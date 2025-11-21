import strawberry
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from gqlauth.user import arg_mutations as mutations
from gqlauth.user.queries import UserQueries
from gqlauth.core.middlewares import JwtSchema
from .models import CustomUser

# 1. Define Custom User Type
# We use this instead of the library's default so we can control exactly
# what data is visible to the frontend (e.g. we want to see 'username').
@strawberry.django.type(CustomUser)
class AccountType:
    username: str
    email: str
    full_name: str | None
    date_of_birth: strawberry.auto # 'auto' automatically maps the Date type

# 2. Define Query
# We inherit the library's queries (like 'me', 'public_user')
@strawberry.type
class Query(UserQueries):
    pass 

# 3. Define Mutation
@strawberry.type
class Mutation:
    # --- Standard Auth Tools (Login/Tokens) ---
    token_auth = mutations.ObtainJSONWebToken.field
    verify_token = mutations.VerifyToken.field
    refresh_token = mutations.RefreshToken.field
    revoke_token = mutations.RevokeToken.field

    # --- Account Management Helpers ---
    verify_account = mutations.VerifyAccount.field
    update_account = mutations.UpdateAccount.field
    delete_account = mutations.DeleteAccount.field
    password_change = mutations.PasswordChange.field
    password_reset = mutations.PasswordReset.field
    password_set = mutations.PasswordSet.field
    
    # --- CUSTOM REGISTRATION LOGIC ---
    @strawberry.mutation
    def register(
        self, 
        username: str, 
        email: str, 
        password: str, 
        full_name: str | None = None,
        date_of_birth: str | None = None
    ) -> AccountType:
        
        # Step A: Security - Check Password Strength
        # This runs against the validators in your settings.py
        try:
            validate_password(password)
        except ValidationError as e:
            # Return the specific reason (e.g., "Password too short")
            raise Exception(f"Weak Password: {e.messages[0]}")

        # Step B: Check duplicates
        if CustomUser.objects.filter(email=email).exists():
             raise Exception("Email already exists")
        
        if CustomUser.objects.filter(username=username).exists():
             raise Exception("Username already exists")

        # Step C: Create the user safely
        # .create_user() handles the password hashing for us.
        user = CustomUser.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            full_name=full_name,
            date_of_birth=date_of_birth
        )
        
        return user

# 4. Schema Wrapper
# We keep this here so this file can be tested in isolation if needed.
schema = JwtSchema(query=Query, mutation=Mutation)