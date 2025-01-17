from fastapi import APIRouter, Form, Request, HTTPException
import httpx
import os

router = APIRouter()
# Define your HubSpot credentials
HUBSPOT_CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID", "0252423f-9a2d-4434-b622-3b2129f9c46d")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET", "1c56c413-6cb7-4942-ba51-06450cb65580")
HUBSPOT_REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI", "localhost:8000/integrations/hubspot/oauth2callback")
authorization_url = "https://app.hubspot.com/oauth/authorize?client_id=0252423f-9a2d-4434-b622-3b2129f9c46d&redirect_uri=http://localhost:8000/integrations/hubspot/oauth2callback&scope=crm.schemas.companies.write%20crm.schemas.quotes.read%20crm.schemas.contacts.write%20crm.objects.line_items.read%20crm.objects.carts.write%20content%20crm.schemas.deals.read%20crm.objects.line_items.write%20crm.objects.carts.read%20crm.schemas.deals.write%20crm.schemas.line_items.read%20crm.pipelines.orders.write%20crm.dealsplits.read_write%20crm.pipelines.orders.read%20crm.objects.subscriptions.read%20crm.schemas.orders.write%20crm.import%20crm.schemas.subscriptions.read%20crm.schemas.orders.read%20crm.schemas.commercepayments.read%20crm.objects.orders.write%20oauth%20crm.objects.owners.read%20crm.objects.commercepayments.read%20crm.objects.orders.read%20crm.objects.invoices.read%20crm.schemas.invoices.read%20crm.objects.courses.read%20crm.objects.courses.write%20crm.objects.listings.read%20crm.objects.leads.read%20crm.objects.listings.write%20crm.objects.leads.write%20crm.objects.services.read%20crm.export%20crm.objects.users.read%20crm.objects.partner-clients.read%20crm.objects.services.write%20crm.objects.contacts.write%20crm.objects.users.write%20crm.objects.partner-clients.write%20crm.objects.appointments.read%20crm.objects.appointments.write%20crm.objects.marketing_events.read%20crm.objects.marketing_events.write%20crm.schemas.custom.read%20crm.objects.custom.read%20crm.objects.feedback_submissions.read%20crm.objects.custom.write%20crm.schemas.services.read%20crm.schemas.services.write%20crm.objects.companies.write%20crm.schemas.courses.read%20crm.lists.write%20crm.objects.goals.read%20crm.schemas.courses.write%20crm.objects.companies.read%20crm.schemas.listings.read%20crm.lists.read%20crm.objects.deals.read%20crm.schemas.listings.write%20crm.schemas.contacts.read%20crm.objects.deals.write%20crm.objects.quotes.write%20crm.schemas.carts.write%20crm.schemas.appointments.read%20crm.objects.contacts.read%20crm.schemas.companies.read%20crm.objects.quotes.read%20crm.schemas.carts.read%20crm.schemas.appointments.write"
TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"

# Step 1: Authorize HubSpot
@router.post("/authorize")
async def authorize_hubspot(user_id: str = Form(...), org_id: str = Form(...)):
    authorization_url = (
        f"https://app.hubspot.com/oauth/authorize?"
        f"client_id={HUBSPOT_CLIENT_ID}&redirect_uri={HUBSPOT_REDIRECT_URI}&"
        f"scope=contacts%20crm.objects.deals.read%20crm.objects.companies.read"
    )
    return {"url": authorization_url}


# Step 2: OAuth2 Callback
@router.get("/oauth2callback")
async def oauth2callback_hubspot(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    token_url = "https://api.hubapi.com/oauth/v1/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": HUBSPOT_CLIENT_ID,
        "client_secret": HUBSPOT_CLIENT_SECRET,
        "redirect_uri": HUBSPOT_REDIRECT_URI,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange token.")

    tokens = response.json()
    # Save the access and refresh tokens to the database
    return {"tokens": tokens}


# Step 3: Get HubSpot Credentials
async def get_hubspot_credentials(user_id: str, org_id: str):
    # Fetch credentials from your database or storage
    # Example:
    # credentials = db.fetch_credentials(user_id, org_id, "hubspot")
    credentials = {
        "access_token": "your_access_token",  # Replace with stored token
    }
    return credentials


# Step 4: Get Items from HubSpot
@router.get("/items")
async def get_items_hubspot(user_id: str, org_id: str):
    credentials = await get_hubspot_credentials(user_id, org_id)
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