
import os
import django
import json
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tau.settings')
django.setup()

from users.schema import schema
from django.conf import settings
from users.models import CustomUser
from gqlauth.jwt.types_ import TokenType

def test_refresh_mutation():
    # 1. Create a dummy user
    email = "test_refresh@example.com"
    password = "testpassword123"
    username = "test_refresh"
    
    try:
        user = CustomUser.objects.get(email=email)
        user.delete()
    except CustomUser.DoesNotExist:
        pass
        
    user = CustomUser.objects.create_user(username=username, email=email, password=password)
    print(f"Created user: {user.email}")

    # 2. Generate a refresh token manually (or via login)
    # We'll use the login mutation to get a valid refresh token
    login_query = """
    mutation Login($username: String!, $password: String!) {
        tokenAuth(username: $username, password: $password) {
            token {
                token
            }
            refreshToken {
                token
            }
        }
    }
    """
    
    rf = RequestFactory()
    login_request = rf.post("/graphql/")
    
    # We need MockContext definition earlier
    class MockResponse:
        def __init__(self):
            self.cookies = {}
        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

    class MockContext:
        def __init__(self, request, response):
            self.request = request
            self.response = response

    mock_response = MockResponse()

    result = schema.execute_sync(
        login_query, 
        variable_values={"username": email, "password": password},
        context_value=MockContext(login_request, mock_response)
    )
    
    if result.errors:
        print("Login failed:", result.errors)
        return

    refresh_token = result.data['tokenAuth']['refreshToken']['token']
    print(f"Got refresh token: {refresh_token[:20]}...")

    # 3. Test Refresh Mutation with Cookie
    refresh_query = """
    mutation Refresh {
        refreshToken {
            token
            refreshToken
        }
    }
    """
    
    # Create a request with the cookie
    refresh_request = rf.post("/graphql/")
    refresh_request.COOKIES[settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE']] = refresh_token
    
    # Mock a response object to capture set_cookie calls
    class MockResponse:
        def __init__(self):
            self.cookies = {}
        def set_cookie(self, key, value, **kwargs):
            self.cookies[key] = value

    class MockContext:
        def __init__(self, request, response):
            self.request = request
            self.response = response

    mock_response = MockResponse()
    
    # Use MockContext for login too, though response is None
    print("Executing login...")
    result = schema.execute_sync(
        login_query, 
        variable_values={"username": email, "password": password},
        context_value=MockContext(login_request, mock_response) 
    )
    
    if result.errors:
        print("Login failed:", result.errors)
        return

    refresh_token = result.data['tokenAuth']['refreshToken']['token']
    print(f"Got refresh token: {refresh_token[:20]}...")

    # 3. Test Refresh Mutation with Cookie
    refresh_query = """
    mutation Refresh {
        refreshToken {
            token
            refreshToken
        }
    }
    """
    
    # Create a request with the cookie
    refresh_request = rf.post("/graphql/")
    refresh_request.COOKIES[settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE']] = refresh_token
    
    print("Executing refresh mutation with cookie...")
    refresh_result = schema.execute_sync(
        refresh_query,
        context_value=MockContext(refresh_request, mock_response)
    )
    
    if refresh_result.errors:
        print("Refresh failed:", refresh_result.errors)
    else:
        data = refresh_result.data['refreshToken']
        if data and data['token']:
            print("Refresh SUCCESS!")
            print(f"New Access Token: {data['token'][:20]}...")
            if settings.GRAPHQL_JWT['JWT_AUTH_COOKIE'] in mock_response.cookies:
                 print("Access Token Cookie SET correctly.")
            else:
                 print("Access Token Cookie NOT SET.")
        else:
            print("Refresh returned no token:", data)

if __name__ == "__main__":
    test_refresh_mutation()
