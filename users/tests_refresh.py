from django.test import TestCase, Client
import json
from .models import CustomUser
from django.conf import settings

class RefreshTokenTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testuser", 
            email="test@example.com", 
            password="Str0ng!Passw0rd123"
        )
        
    def test_refresh_token_cookie_mode(self):
        # 1. Login to get tokens
        login_query = """
            mutation {
                tokenAuth(username: "testuser", password: "Str0ng!Passw0rd123") {
                    token {
                        token
                    }
                    refreshToken {
                        token
                    }
                }
            }
        """
        response = self.client.post(
            "/graphql/", 
            data=json.dumps({"query": login_query}), 
            content_type="application/json"
        )
        content = json.loads(response.content)
        if "errors" in content:
            self.fail(f"Login Errors: {content['errors']}")
        
        # Check if cookies are set
        cookie_name = settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE']
        self.assertIn(cookie_name, response.cookies)
        
        # 2. Call Refresh Token with "cookie-mode"
        refresh_query = """
            mutation {
                refreshToken(refreshToken: "cookie-mode", revokeRefreshToken: true) {
                    token {
                        token
                    }
                }
            }
        """
        
        # The client should persist cookies
        response_refresh = self.client.post(
            "/graphql/", 
            data=json.dumps({"query": refresh_query}), 
            content_type="application/json"
        )
        
        content_refresh = json.loads(response_refresh.content)
        if "errors" in content_refresh:
            self.fail(f"Refresh Errors: {content_refresh['errors']}")
            
        self.assertIsNotNone(content_refresh['data']['refreshToken']['token']['token'])
        print("Refresh Token Success:", content_refresh['data']['refreshToken']['token']['token'][:10] + "...")
