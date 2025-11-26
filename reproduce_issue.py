import requests
import json

URL = "http://localhost:8000/graphql/"

def run_query(query, variables=None, cookies=None):
    response = requests.post(URL, json={'query': query, 'variables': variables}, cookies=cookies)
    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {query}")
    return response

def register_user(email, username, password):
    mutation = """
    mutation Register($email: String!, $username: String!, $password: String!) {
        register(email: $email, username: $username, password: $password) {
            username
            email
        }
    }
    """
    variables = {"email": email, "username": username, "password": password}
    # We expect this might fail if user exists, which is fine
    try:
        response = run_query(mutation, variables)
        return response
    except Exception as e:
        print(f"Registration might have failed (user exists?): {e}")
        return None

def login_user(username, password):
    mutation = """
    mutation Login($username: String!, $password: String!) {
        tokenAuth(username: $username, password: $password) {
            token {
                token
                payload {
                    username
                    exp
                    origIat
                }
            }
            refreshToken {
                token
            }
        }
    }
    """
    variables = {"username": username, "password": password}
    response = run_query(mutation, variables)
    return response

def main():
    email = "test@example.com"
    username = "testuser"
    password = "TestPassword123!"

    print("Attempting to register...")
    register_user(email, username, password)

    print("Attempting to login...")
    response = login_user(username, password)
    
    data = response.json()
    if 'errors' in data:
        print("Login Errors:", data['errors'])
    else:
        print("Login Success!")
        print("Cookies received:", response.cookies.get_dict())
        
        # Check for specific cookies
        auth_cookie = response.cookies.get('tau_auth_token')
        refresh_cookie = response.cookies.get('tau_refresh_token')
        
        if auth_cookie:
            print(f"Found tau_auth_token: {auth_cookie[:10]}...")
            # Check cookie attributes
            for cookie in response.cookies:
                if cookie.name == 'tau_auth_token':
                    print(f"tau_auth_token HttpOnly: {cookie.has_nonstandard_attr('HttpOnly') or cookie.rest.get('HttpOnly') is not None}")
        else:
            print("MISSING tau_auth_token cookie")
            
        if refresh_cookie:
            print(f"Found tau_refresh_token: {refresh_cookie[:10]}...")
            for cookie in response.cookies:
                if cookie.name == 'tau_refresh_token':
                    print(f"tau_refresh_token HttpOnly: {cookie.has_nonstandard_attr('HttpOnly') or cookie.rest.get('HttpOnly') is not None}")
        else:
            print("MISSING tau_refresh_token cookie")

        # Verify session with cookies
        print("\nVerifying session with cookies...")
        me_query = """
        query {
            me {
                username
                email
            }
        }
        """
        me_response = run_query(me_query, cookies=response.cookies)
        me_data = me_response.json()
        print("Me Query Result:", me_data)

if __name__ == "__main__":
    main()