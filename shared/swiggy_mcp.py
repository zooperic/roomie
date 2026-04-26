"""
Swiggy MCP Client with OAuth 2.0 PKCE Flow
Based on: github.com/DeepBhupatkar/swiggy-voice-ai-agent-videosdk-mcp
"""
import os
import json
import httpx
import hashlib
import secrets
import webbrowser
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Optional, Dict, Any

TOKEN_FILE = ".swiggy_tokens.json"
OAUTH_PORT = 8765

# Swiggy MCP endpoints
SWIGGY_AUTH_URL = "https://mcp.swiggy.com/oauth/authorize"
SWIGGY_TOKEN_URL = "https://mcp.swiggy.com/oauth/token"
SWIGGY_INSTAMART_BASE = "https://mcp.swiggy.com/im"


class TokenStorage:
    """Handle token persistence"""
    
    @staticmethod
    def save(tokens: Dict[str, Any]):
        with open(TOKEN_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
        print(f"[SwiggyMCP] Tokens saved to {TOKEN_FILE}")
    
    @staticmethod
    def load() -> Optional[Dict[str, Any]]:
        if not os.path.exists(TOKEN_FILE):
            return None
        try:
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[SwiggyMCP] Error loading tokens: {e}")
            return None
    
    @staticmethod
    def clear():
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
            print(f"[SwiggyMCP] Tokens cleared")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback"""
    
    auth_code = None
    state = None
    
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        
        if 'code' in query and 'state' in query:
            OAuthCallbackHandler.auth_code = query['code'][0]
            OAuthCallbackHandler.state = query['state'][0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: monospace; padding: 40px; text-align: center;">
                    <h2>Swiggy Authentication Successful!</h2>
                    <p>You can close this window and return to the terminal.</p>
                    <script>window.close();</script>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Error: Invalid callback</h2></body></html>")
    
    def log_message(self, format, *args):
        pass  # Suppress server logs


class SwiggyMCPClient:
    """Swiggy MCP Client with OAuth 2.0 PKCE"""
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.expires_at: Optional[datetime] = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    def _generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge"""
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge_b64 = secrets.token_urlsafe(43).replace('=', '')
        return code_verifier, code_challenge_b64
    
    async def _exchange_code_for_token(self, code: str, code_verifier: str):
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': f'http://localhost:{OAUTH_PORT}/callback',
            'code_verifier': code_verifier,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(SWIGGY_TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
    
    async def _refresh_access_token(self):
        """Refresh expired access token"""
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(SWIGGY_TOKEN_URL, data=data)
            response.raise_for_status()
            tokens = response.json()
        
        self._store_tokens(tokens)
        print("[SwiggyMCP] Access token refreshed")
    
    def _store_tokens(self, tokens: Dict[str, Any]):
        """Store tokens and set expiry"""
        self.access_token = tokens['access_token']
        self.refresh_token = tokens.get('refresh_token', self.refresh_token)
        
        # Calculate expiry (default 1 hour if not specified)
        expires_in = tokens.get('expires_in', 3600)
        self.expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # Save to file
        TokenStorage.save({
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at.isoformat(),
        })
    
    def _load_tokens(self) -> bool:
        """Load tokens from file"""
        tokens = TokenStorage.load()
        if not tokens:
            return False
        
        self.access_token = tokens.get('access_token')
        self.refresh_token = tokens.get('refresh_token')
        expires_at_str = tokens.get('expires_at')
        
        if expires_at_str:
            self.expires_at = datetime.fromisoformat(expires_at_str)
        
        return True
    
    def _is_token_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.expires_at:
            return True
        return datetime.now() >= self.expires_at
    
    async def authenticate(self):
        """Run OAuth flow or load existing tokens"""
        # Try loading existing tokens
        if self._load_tokens():
            print("[SwiggyMCP] Loaded existing tokens")
            
            # Refresh if expired
            if self._is_token_expired():
                print("[SwiggyMCP] Token expired, refreshing...")
                try:
                    await self._refresh_access_token()
                    return
                except Exception as e:
                    print(f"[SwiggyMCP] Refresh failed: {e}, re-authenticating...")
                    TokenStorage.clear()
            else:
                print("[SwiggyMCP] Token still valid")
                return
        
        # Start OAuth flow
        print("[SwiggyMCP] Starting OAuth flow...")
        
        code_verifier, code_challenge = self._generate_pkce_pair()
        state = secrets.token_urlsafe(16)
        
        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'redirect_uri': f'http://localhost:{OAUTH_PORT}/callback',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        auth_url = f"{SWIGGY_AUTH_URL}?{urlencode(auth_params)}"
        
        # Start local HTTP server for callback
        server = HTTPServer(('localhost', OAUTH_PORT), OAuthCallbackHandler)
        
        print(f"[SwiggyMCP] Opening browser for Swiggy login...")
        print(f"[SwiggyMCP] Callback server started on http://localhost:{OAUTH_PORT}")
        webbrowser.open(auth_url)
        
        # Wait for callback
        print("[SwiggyMCP] Waiting for authorization...")
        server.handle_request()
        
        # Verify state
        if OAuthCallbackHandler.state != state:
            raise Exception("OAuth state mismatch - potential CSRF attack")
        
        # Exchange code for token
        print("[SwiggyMCP] Exchanging code for access token...")
        tokens = await self._exchange_code_for_token(
            OAuthCallbackHandler.auth_code,
            code_verifier
        )
        
        self._store_tokens(tokens)
        print("[SwiggyMCP] Authentication successful!")
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid access token"""
        if not self.access_token or self._is_token_expired():
            if self.refresh_token and self._is_token_expired():
                await self._refresh_access_token()
            else:
                raise Exception("Not authenticated - call authenticate() first")
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Swiggy MCP"""
        await self._ensure_authenticated()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }
        
        url = f"{SWIGGY_INSTAMART_BASE}/{endpoint}"
        response = await self.client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # === Swiggy Instamart API Methods ===
    
    async def search_products(self, query: str, location: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for products on Swiggy Instamart"""
        params = {'query': query}
        if location:
            params['lat'] = location.get('latitude')
            params['lng'] = location.get('longitude')
        return await self._request('GET', 'search', params=params)
    
    async def get_cart(self) -> Dict[str, Any]:
        """Get current cart"""
        return await self._request('GET', 'cart')
    
    async def add_to_cart(self, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add product to cart"""
        data = {'product_id': product_id, 'quantity': quantity}
        return await self._request('POST', 'cart/add', json=data)
    
    async def update_cart(self, product_id: str, quantity: int) -> Dict[str, Any]:
        """Update cart item quantity"""
        data = {'product_id': product_id, 'quantity': quantity}
        return await self._request('PUT', 'cart/update', json=data)
    
    async def remove_from_cart(self, product_id: str) -> Dict[str, Any]:
        """Remove product from cart"""
        return await self._request('DELETE', f'cart/remove/{product_id}')
    
    async def checkout(self, payment_method: str = 'COD') -> Dict[str, Any]:
        """Place order (COD only supported)"""
        data = {'payment_method': payment_method}
        return await self._request('POST', 'checkout', json=data)
    
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status and tracking"""
        return await self._request('GET', f'orders/{order_id}')
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# === Standalone Usage ===

async def main():
    """Test OAuth flow"""
    client = SwiggyMCPClient()
    
    try:
        await client.authenticate()
        print("\n[SwiggyMCP] Authentication complete! Testing API...")
        
        # Test search
        results = await client.search_products("milk")
        print(f"\n[SwiggyMCP] Found {len(results.get('products', []))} milk products")
        
    except Exception as e:
        print(f"[SwiggyMCP] Error: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
