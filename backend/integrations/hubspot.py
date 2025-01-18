from fastapi import APIRouter, Form, Request, HTTPException
import httpx
import os
import redis
import json

# Redis connection setup
redis_host = os.getenv("REDIS_HOST", "localhost")  # Set to your Redis server host
redis_port = os.getenv("REDIS_PORT", 6379)        # Default Redis port
redis_db = os.getenv("REDIS_DB", 0)               # Default Redis database index

redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
try:
    redis_client.ping()  # Test the connection
    print("Connected to Redis successfully.")
except redis.ConnectionError as e:
    print(f"Error connecting to Redis: {e}")

redis_client.set('test_key', 'test_value')
print(redis_client.get('test_key'))
# Function to save tokens securely in Redis
def save_tokens(user_id: str, tokens: dict):
    """
    Save OAuth tokens to Redis for a specific user.

    Args:
        user_id (str): The user's ID.
        tokens (dict): The OAuth tokens (access_token, refresh_token, etc.).
    """
    # try:
    #     redis_key = f"hubspot_tokens:{user_id}"
    #     redis_client.setex(redis_key, 3600, json.dumps(tokens))  # Save for 1 hour
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error saving tokens to Redis: {str(e)}")
    try:
        key = f"hubspot_tokens:{user_id}"
        value = json.dumps(tokens)
        redis_client.setex(key, 3600, value)  # 3600 seconds = 1 hour
        print(f"Tokens saved to Redis: {key} -> {value}")  # Debugging log
    except Exception as e:
        print(f"Error saving tokens: {e}")  # Debugging log
        raise HTTPException(status_code=500, detail=f"Error saving tokens: {str(e)}")
# Function to retrieve tokens from Redis
def get_tokens(user_id: str) -> dict:
    """
    Retrieve OAuth tokens from Redis using the user ID.

    Args:
        user_id (str): The user's ID.

    Returns:
        dict: The OAuth tokens or None if not found.
    """
    try:
        redis_key = f"hubspot_tokens:{user_id}"
        tokens = redis_client.get(redis_key)
        return json.loads(tokens) if tokens else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tokens from Redis: {str(e)}")
    

router = APIRouter()
# Define your HubSpot credentials
HUBSPOT_CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID", "0252423f-9a2d-4434-b622-3b2129f9c46d")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET", "1c56c413-6cb7-4942-ba51-06450cb65580")
HUBSPOT_REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI", "http://localhost:8000/integrations/hubspot/oauth2callback")
authorization_url = "https://app.hubspot.com/oauth/authorize?client_id=0252423f-9a2d-4434-b622-3b2129f9c46d&redirect_uri=http://localhost:8000/integrations/hubspot/oauth2callback&scope=crm.objects.contacts.write%20oauth%20crm.objects.companies.write%20crm.lists.write%20crm.objects.companies.read%20crm.lists.read%20crm.objects.contacts.read&state={user_id}"


TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"

# Step 1: Authorize HubSpot
@router.post("/authorize")
async def authorize_hubspot(user_id: str = Form(...), org_id: str = Form(...)):
    authorization_url = "https://app.hubspot.com/oauth/authorize?client_id=0252423f-9a2d-4434-b622-3b2129f9c46d&redirect_uri=http://localhost:8000/integrations/hubspot/oauth2callback&scope=crm.objects.contacts.write%20oauth%20crm.objects.companies.write%20crm.lists.write%20crm.objects.companies.read%20crm.lists.read%20crm.objects.contacts.read&state={user_id}"
    return {"url": authorization_url}

# Step 2: OAuth Callback
@router.get("/oauth2callback")
async def oauth2callback_hubspot(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")  # Extract state parameter
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")
    if not state:
        raise HTTPException(status_code=400, detail="Missing user ID in state.")
    
    user_id = state  # Assign state value to user_id

    # Continue with token exchange and saving
    payload = {
        "grant_type": "authorization_code",
        "client_id": HUBSPOT_CLIENT_ID,
        "client_secret": HUBSPOT_CLIENT_SECRET,
        "redirect_uri": HUBSPOT_REDIRECT_URI,
        "code": code,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, data=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange token: {response.text}"
        )

    tokens = response.json()
    save_tokens(user_id, tokens)  # Save tokens to Redis
    return {"message": "Authorization successful", "tokens": tokens}
    return RedirectResponse(url=f"/items?user_id={user_id}")


# # Step 3: Get HubSpot Credentials
# async def get_hubspot_credentials(user_id: str):
#     tokens = get_tokens(user_id)  # Retrieve tokens from Redis
#     if not tokens:
#         raise HTTPException(status_code=401, detail="Unauthorized: Tokens not found.")
#     return tokens


# # Step 4: Get Items from HubSpot
# @router.get("/items")
# async def get_items_hubspot(user_id: str, org_id: str):
#     credentials = await get_hubspot_credentials(user_id, org_id)
#     access_token = credentials.get("access_token")

#     if not access_token:
#         raise HTTPException(status_code=401, detail="Unauthorized")

#     items_url = "https://api.hubapi.com/crm/v3/objects/contacts"

#     headers = {"Authorization": f"Bearer {access_token}"}
#     async with httpx.AsyncClient() as client:
#         response = await client.get(items_url, headers=headers)

#     if response.status_code != 200:
#         raise HTTPException(status_code=400, detail="Failed to fetch items.")

#     items = response.json()
#     return {"items": items}

# Step 3: Get HubSpot Credentials
async def get_hubspot_credentials(user_id: str):
    tokens = get_tokens(user_id)  # Retrieve tokens from Redis
    if not tokens:
        raise HTTPException(status_code=401, detail="Unauthorized: Tokens not found.")
    return tokens

# Step 4: Get Items from HubSpot
@router.get("/items")
async def get_items_hubspot(user_id: str):
    credentials = await get_hubspot_credentials(user_id)  # Retrieve credentials for the given user
    access_token = credentials.get("access_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    items_url = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(items_url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch items.")

    items = response.json()
    return {"items": items}
