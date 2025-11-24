from django.test import TestCase
import json
from django.test import TestCase, Client
from .models import CustomUser

class RegisterMutationTest(TestCase):
    def setUp(self):
        # We use the Client to simulate a real browser request
        self.client = Client()

    def test_register_mutation(self):
        # 1. Define the Query
        # We ask for 'username' and 'email' to verify the return type works
        query = """
            mutation {
                register(
                    username: "testuser",
                    email: "test@example.com",
                    password: "Str0ng!Passw0rd123"
                ) {
                    username
                    email
                }
            }
        """

        # 2. Send the Request
        # IMPORTANT: We must use "/graphql/" (with the trailing slash) 
        # to prevent a 301 Redirect error.
        response = self.client.post(
            "/graphql/", 
            data=json.dumps({"query": query}), 
            content_type="application/json"
        )

        # 3. check for HTTP 200 OK
        self.assertEqual(response.status_code, 200, f"Server failed: {response.content}")

        # 4. Parse Response
        content = json.loads(response.content)

        # 5. Check for GraphQL Errors
        # If password validation fails or schema is wrong, it prints here.
        if "errors" in content:
            self.fail(f"GraphQL Errors Found: {content['errors']}")

        # 6. Verify Return Data
        data = content['data']['register']
        self.assertEqual(data['email'], "test@example.com")
        self.assertEqual(data['username'], "testuser")
        
        # 7. Verify Database
        # Ensure the data actually saved to the DB
        user = CustomUser.objects.get(email="test@example.com")
        
        # Verify password was hashed (not plain text)
        self.assertTrue(user.check_password("Str0ng!Passw0rd123"))