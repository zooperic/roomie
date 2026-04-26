"""
OAuth server for Swiggy authentication
Runs on port 8765 to handle OAuth callback
"""

import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

app = FastAPI()

# Store tokens temporarily
TOKEN_FILE = ".swiggy_tokens.json"
OAUTH_STATE = {}

SWIGGY_OAUTH_URL = "https://www.swiggy.com/mcp/oauth/authorize"
SWIGGY_TOKEN_URL = "https://www.swiggy.com/mcp/oauth/token"
REDIRECT_URI = "http://localhost:8765/callback"


@app.get("/auth")
async def start_auth():
    """Initiate OAuth flow"""
    import secrets
    state = secrets.token_urlsafe(32)
    OAUTH_STATE['state'] = state
    
    # Build authorization URL
    auth_url = (
        f"{SWIGGY_OAUTH_URL}"
        f"?response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
        f"&scope=cart.write orders.write"
    )
    
    return RedirectResponse(url=auth_url)


@app.get("/callback")
async def oauth_callback(request: Request):
    """Handle OAuth callback from Swiggy"""
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')
    
    if error:
        return HTMLResponse(f"""
        <html><body>
        <h1>❌ Authentication Failed</h1>
        <p>Error: {error}</p>
        <p>{request.query_params.get('error_description', '')}</p>
        </body></html>
        """)
    
    if state != OAUTH_STATE.get('state'):
        return HTMLResponse("<html><body><h1>Invalid state</h1></body></html>")
    
    # Exchange code for tokens
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SWIGGY_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                }
            )
            
            if response.status_code == 200:
                tokens = response.json()
                
                # Save tokens
                with open(TOKEN_FILE, 'w') as f:
                    json.dump({
                        **tokens,
                        'timestamp': datetime.utcnow().isoformat()
                    }, f, indent=2)
                
                return HTMLResponse("""
                <html><body>
                <h1>✅ Authentication Successful!</h1>
                <p>You can close this window and return to ROOMIE.</p>
                <p>Your Swiggy account is now connected.</p>
                </body></html>
                """)
            else:
                return HTMLResponse(f"""
                <html><body>
                <h1>❌ Token Exchange Failed</h1>
                <p>Status: {response.status_code}</p>
                <p>Response: {response.text}</p>
                </body></html>
                """)
                
        except Exception as e:
            return HTMLResponse(f"""
            <html><body>
            <h1>❌ Error</h1>
            <p>{str(e)}</p>
            </body></html>
            """)


@app.get("/")
async def root():
    """Show status"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)
        return {
            "status": "authenticated",
            "timestamp": tokens.get('timestamp'),
            "has_access_token": bool(tokens.get('access_token'))
        }
    return {"status": "not_authenticated"}


def start_oauth_server():
    """Start the OAuth server"""
    print("[OAuth] Starting OAuth server on http://localhost:8765")
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="info")


if __name__ == "__main__":
    start_oauth_server()