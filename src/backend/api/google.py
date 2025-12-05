import requests
from . import config

def get_user_infos_from_google_token_url(code):
    """Exchange OAuth code for access token and fetch user info from Google."""
    if not config.GOOGLE_CLIENT_ID or not config.GOOGLE_CLIENT_SECRET:
        return {
            "status": False,
            "user_infos": None,
            "error": "Google OAuth not configured"
        }
    
    try:
        # Exchange the code for tokens
        token_response = requests.post(
            config.GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": config.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"}
        )
        
        token_response.raise_for_status()
        token_data = token_response.json()
        
        # Get the access token
        access_token = token_data.get("access_token")
        if not access_token:
            return {
                "status": False,
                "user_infos": None,
                "error": "No access token in response"
            }
        
        # Use the access token to get user info
        user_response = requests.get(
            config.GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        user_response.raise_for_status()
        user_info = user_response.json()
        
        return {
            "status": bool(user_info),
            "user_infos": user_info
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": False,
            "user_infos": None,
            "error": f"Request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "status": False,
            "user_infos": None,
            "error": f"Unexpected error: {str(e)}"
        }