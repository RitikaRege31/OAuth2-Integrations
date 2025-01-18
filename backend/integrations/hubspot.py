import json
import secrets
import base64
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

from fastapi import APIRouter

router = APIRouter()
# HubSpot credentials
HUBSPOT_CLIENT_ID = '0252423f-9a2d-4434-b622-3b2129f9c46d'
HUBSPOT_CLIENT_SECRET = '1c56c413-6cb7-4942-ba51-06450cb65580'
HUBSPOT_REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'

# Base64 encoding for client ID and secret
encoded_client_id_secret = base64.b64encode(f"{HUBSPOT_CLIENT_ID}:{HUBSPOT_CLIENT_SECRET}".encode()).decode()

# Authorization URL
AUTHORIZATION_URL = f"https://app.hubspot.com/oauth/authorize?client_id={HUBSPOT_CLIENT_ID}&redirect_uri={HUBSPOT_REDIRECT_URI}&scope=crm.objects.contacts.write%20oauth%20crm.objects.companies.write%20crm.lists.write%20crm.objects.companies.read%20crm.lists.read%20crm.objects.contacts.read"

# Token URL
TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"


async def authorize_hubspot(user_id, org_id):
    """Generate the authorization URL with a state parameter."""
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = json.dumps(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', encoded_state, expire=600)

    return f"{AUTHORIZATION_URL}&state={encoded_state}"


async def oauth2callback_hubspot(request: Request):
    """Handle OAuth2 callback for HubSpot."""
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error'))

    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(encoded_state)

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    # Validate state
    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    # Exchange authorization code for tokens

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            # client.post(TOKEN_URL, data=payload, headers=headers),
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                   'grant_type': 'authorization_code',
                   'client_id': HUBSPOT_CLIENT_ID,
                   'client_secret': HUBSPOT_CLIENT_SECRET,
                   'redirect_uri': HUBSPOT_REDIRECT_URI,
                   'code': code,
                },
                headers={
                   'Content-Type': 'application/x-www-form-urlencoded'
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}')
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange token: {response.text}"
        )

    tokens = response.json()
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(tokens), expire=600)

    # Close the OAuth popup window
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

@router.get("/credentials")
async def get_hubspot_credentials(user_id, org_id):
    """Retrieve stored HubSpot credentials."""
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    return credentials


# # Step 4: Get Items from HubSpot
# @router.post("/load")
# def create_integration_item_metadata_object(response_json: dict) -> IntegrationItem:
#     """
#     Create an IntegrationItem object from HubSpot API response data.
#     """
#     name = response_json.get('properties', {}).get('name', {}).get('value', 'Unnamed Item')
#     created_time = response_json.get('createdAt')
#     last_modified_time = response_json.get('updatedAt')
#     parent_id = response_json.get('associations', {}).get('companyIds', [None])[0]
#     item_type = response_json.get('objectType', 'Unknown')

#     integration_item_metadata = IntegrationItem(
#         id=response_json['id'],
#         type=item_type,
#         name=name,
#         creation_time=created_time,
#         last_modified_time=last_modified_time,
#         parent_id=parent_id,
#     )
#     return integration_item_metadata


# async def get_items_hubspot(credentials: dict) -> list[IntegrationItem]:
#     """
#     Fetch items from HubSpot and convert them into IntegrationItem objects.
#     """
#     credentials = json.loads(credentials)
#     access_token = credentials.get('access_token')
#     if not access_token:
#         raise HTTPException(status_code=400, detail="Missing access token in credentials.")

#     # HubSpot API URL for fetching objects (e.g., contacts)
#     api_url = "https://api.hubapi.com/crm/v3/objects/contacts"

#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             api_url,
#             headers={
#                 "Authorization": f"Bearer {access_token}",
#                 "Content-Type": "application/json",
#             },
#         )

#     if response.status_code != 200:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Failed to fetch items from HubSpot: {response.text}",
#         )

#     # Parse response data
#     items_data = response.json().get("results", [])
#     list_of_integration_item_metadata = []

#     for item in items_data:
#         integration_item = create_integration_item_metadata_object(item)
#         list_of_integration_item_metadata.append(integration_item)

#     # Print the items for testing purposes
#     print(list_of_integration_item_metadata)

#     return list_of_integration_item_metadata


def create_integration_item_metadata_object(
    response_json: dict, item_type: str, parent_id=None, parent_name=None
) -> IntegrationItem:
    """
    Create an IntegrationItem object from the HubSpot API response.
    """
    parent_id = None if parent_id is None else f"{parent_id}_HubSpot"
    integration_item_metadata = IntegrationItem(
        id=response_json.get('id', None) + f"_{item_type}",
        name=response_json.get('properties', {}).get('name', 'Unnamed Item'),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
    )
    return integration_item_metadata


def fetch_items(
    access_token: str, url: str, aggregated_response: list, after=None
):
    """
    Recursively fetch data from HubSpot API and handle pagination.
    """
    params = {'after': after} if after else {}
    headers = {'Authorization': f'Bearer {access_token}'}
    response = httpx.get(url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json().get('results', [])
        next_page = response.json().get('paging', {}).get('next', {}).get('after', None)

        aggregated_response.extend(results)

        if next_page:
            fetch_items(access_token, url, aggregated_response, next_page)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch items: {response.text}"
        )


async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """
    Fetch items from HubSpot and convert them into IntegrationItem objects.
    """
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail="Missing access token in credentials.")

    base_url = "https://api.hubapi.com/crm/v3/objects"
    endpoints = {
        "contacts": f"{base_url}/contacts",
        "companies": f"{base_url}/companies",
        # Add more endpoints as needed
    }

    list_of_integration_item_metadata = []

    for item_type, url in endpoints.items():
        aggregated_response = []
        fetch_items(access_token, url, aggregated_response)

        for response in aggregated_response:
            integration_item = create_integration_item_metadata_object(response, item_type)
            list_of_integration_item_metadata.append(integration_item)

    print(f"list_of_integration_item_metadata: {list_of_integration_item_metadata}")
    return list_of_integration_item_metadata


# @router.get("/credentials")
# async def get_hubspot_credentials_endpoint(user_id: str, org_id: str):
#     """
#     API endpoint to retrieve stored HubSpot credentials.
#     """
#     return await get_hubspot_credentials(user_id, org_id)


@router.post("/load")
async def load_hubspot_items(user_id: str, org_id: str):
    """
    API endpoint to load and return HubSpot items as IntegrationItems.
    """
    credentials = await get_hubspot_credentials(user_id, org_id)
    return await get_items_hubspot(credentials)


