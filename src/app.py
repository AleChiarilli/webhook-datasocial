import os
from flask import Flask, request, redirect, url_for, session
from hubspot import HubSpot
from hubspot.auth.oauth import ApiException as OAuthApiException
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException, PublicObjectSearchRequest, Filter, FilterGroup
from requests_oauthlib import OAuth2Session

# Environment variables
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
AUTHORIZATION_BASE_URL = 'https://app.hubspot.com/oauth/authorize'
TOKEN_URL = 'https://api.hubapi.com/oauth/v1/token'
REDIRECT_URI = 'http://localhost:5000/callback'

app = Flask(__name__)
app.secret_key = os.urandom(24)

# OAuth session
def get_hubspot_session(token=None):
    scope = ["contacts"]
    return OAuth2Session(CLIENT_ID, scope=scope, token=token, redirect_uri=REDIRECT_URI, auto_refresh_url=TOKEN_URL, auto_refresh_kwargs={'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET})

@app.route('/')
def index():
    hubspot = get_hubspot_session()
    authorization_url, state = hubspot.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback', methods=['GET'])
def callback():
    hubspot = get_hubspot_session(state=session['oauth_state'])
    try:
        token = hubspot.fetch_token(TOKEN_URL, authorization_response=request.url, client_secret=CLIENT_SECRET)
        session['oauth_token'] = token
        print(f"OAuth token received: {token}")  # Debug statement
        return 'OAuth token received successfully. You can now use the /webhook endpoint.'
    except Exception as e:
        print(f"Error fetching OAuth token: {e}")  # Debug statement
        return f"Error fetching OAuth token: {e}", 500

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    # Get data from the request
    data = request.get_json()

    # Extract email and name
    email = data.get("email")
    name = data.get("name")

    if not email or not name:
        return "Missing required fields: email and name", 400

    hubspot = get_hubspot_session(token=session.get('oauth_token'))
    client = HubSpot(access_token=hubspot.token.get('access_token'))

    try:
        # Search for the contact by email
        filter_ = Filter(property_name="email", operator="EQ", value=email)
        filter_group = FilterGroup(filters=[filter_])
        search_request = PublicObjectSearchRequest(filter_groups=[filter_group], properties=["email", "firstname"])

        search_response = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        results = search_response.results

        if results:
            # Contact exists, update it
            contact_id = results[0].id
            update_properties = {
                "email": email,
                "firstname": name
            }
            client.crm.contacts.basic_api.update(contact_id=contact_id, simple_public_object_input=SimplePublicObjectInput(properties=update_properties))
            return f"Contact with email {email} updated successfully."
        else:
            # Contact does not exist, create a new one
            create_properties = {
                "email": email,
                "firstname": name
            }
            client.crm.contacts.basic_api.create(simple_public_object_input=SimplePublicObjectInput(properties=create_properties))
            return f"Contact with email {email} created successfully."
    
    except ApiException as e:
        return f"HubSpot API exception: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)