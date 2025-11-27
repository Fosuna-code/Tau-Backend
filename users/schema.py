import strawberry
import strawberry_django
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from gqlauth.user import arg_mutations as mutations
from gqlauth.user.queries import UserQueries
from gqlauth.core.middlewares import JwtSchema
from gqlauth.jwt.types_ import TokenType, ObtainJSONWebTokenInput, ObtainJSONWebTokenType
from .models import CustomUser

# 1. Define Custom User Type
# We use this instead of the library's default so we can control exactly
# what data is visible to the frontend (e.g. we want to see 'username').
@strawberry_django.type(CustomUser)
class AccountType:
    username: str
    email: str

# 2. Define Query
# We define our own 'me' query instead of inheriting from UserQueries
# because UserQueries uses a default UserType that doesn't expose username
@strawberry.type
class Query:
    @strawberry.field
    def me(self, info) -> AccountType | None:
        """Return the currently authenticated user."""
        user = info.context.request.user
        
        # Fallback: Manual authentication if middleware failed but cookie is present
        # This handles the case where gqlauth produces a nested JSON payload string
        if not user.is_authenticated:
            import jwt
            import json
            from django.conf import settings
            from django.contrib.auth import get_user_model
            
            token = info.context.request.COOKIES.get(settings.GRAPHQL_JWT['JWT_AUTH_COOKIE'])
            if token:
                try:
                    # Decode the token
                    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                    
                    # Handle nested payload structure from gqlauth
                    if 'payload' in payload and isinstance(payload['payload'], str):
                        inner_payload = json.loads(payload['payload'])
                        username = inner_payload.get('username')
                    else:
                        username = payload.get('username')
                        
                    if username:
                        User = get_user_model()
                        try:
                            user = User.objects.get(username=username)
                            # Manually set the user on the request for subsequent resolvers
                            info.context.request.user = user
                        except User.DoesNotExist:
                            pass
                except Exception:
                    # Token invalid or expired
                    pass

        if user.is_authenticated:
            return user
        return None

# 3. Define Mutation
#This is to fix the error that occurs when you try to login with email
class CustomObtainJSONWebToken(mutations.ObtainJSONWebToken):
    @classmethod
    def resolve_mutation(cls, info, input_: ObtainJSONWebTokenInput) -> ObtainJSONWebTokenType:
        # Fix for "ObtainJSONWebTokenInput object has no attribute 'email'"
        # gqlauth expects 'email' attribute because USERNAME_FIELD='email',
        # but the input object only has 'username'.
        if not hasattr(input_, 'email') and hasattr(input_, 'username'):
            # We can't easily set attribute on frozen dataclass, so we might need to rely on
            # the fact that it's a standard class or use a workaround.
            # Strawberry inputs are often simple objects.
            try:
                setattr(input_, 'email', input_.username)
            except AttributeError:
                pass
        
        result = super().resolve_mutation(info, input_)
        
        # Explicitly ensure cookies are set (redundant check/enforcement)
        # This is to address the reported issue where cookies might not be set correctly
        from django.conf import settings
        
        if result.token:
            info.context.response.set_cookie(
                settings.GRAPHQL_JWT['JWT_AUTH_COOKIE'],
                result.token.token,
                httponly=settings.GRAPHQL_JWT['JWT_COOKIE_HTTPONLY'],
                samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
                secure=settings.GRAPHQL_JWT['JWT_COOKIE_SECURE'],
                max_age=settings.GRAPHQL_JWT['JWT_EXPIRATION_DELTA'].total_seconds(),
            )
            
        if result.refresh_token:
            info.context.response.set_cookie(
                settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE'],
                result.refresh_token.token,
                httponly=settings.GRAPHQL_JWT['JWT_COOKIE_HTTPONLY'],
                samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
                secure=settings.GRAPHQL_JWT['JWT_COOKIE_SECURE'],
                max_age=settings.GRAPHQL_JWT['JWT_REFRESH_EXPIRATION_DELTA'].total_seconds(),
            )

        return result

from gqlauth.jwt.types_ import RefreshTokenType, RevokeRefreshTokenType
from gqlauth.user import resolvers

class CustomRefreshToken(mutations.RefreshToken):
    @classmethod
    def resolve_mutation(cls, info, input_: resolvers.RefreshTokenMixin.RefreshTokenInput) -> ObtainJSONWebTokenType:
        from django.conf import settings
        import dataclasses

        # 1. LOGIC UPDATE: Check for empty OR dummy placeholder
        # The schema requires a string, so the frontend sends "cookie-mode"
        print(f"DEBUG: CustomRefreshToken called with {input_.refresh_token}")
        if not input_.refresh_token or input_.refresh_token == "cookie-mode":
            cookie_name = settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE']
            refresh_token = info.context.request.COOKIES.get(cookie_name)
            print(f"DEBUG: Found cookie refresh token: {refresh_token}")
            
            if refresh_token:
                # Use dataclasses.replace to modify the frozen input object
                try:
                    input_ = dataclasses.replace(input_, refresh_token=refresh_token)
                    print("DEBUG: Replaced input refresh token")
                except Exception as e:
                    print(f"DEBUG: Failed to replace input: {e}")
                    pass
        
        # 2. Call the parent resolver
        print("DEBUG: Calling super().resolve_mutation")
        result = super().resolve_mutation(info, input_)
        print(f"DEBUG: super() returned {type(result)}")

        # 3. Set the new cookies (Same as before)
        # Note: We access result.payload, result.refresh_token carefully
        if result.token:
             token = result.token.token
             if token:
                info.context.response.set_cookie(
                    settings.GRAPHQL_JWT['JWT_AUTH_COOKIE'],
                    token,
                    httponly=settings.GRAPHQL_JWT['JWT_COOKIE_HTTPONLY'],
                    samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
                    secure=settings.GRAPHQL_JWT['JWT_COOKIE_SECURE'],
                    max_age=settings.GRAPHQL_JWT['JWT_EXPIRATION_DELTA'].total_seconds(),
                )

        if result.refresh_token:
             # IMPORTANT: result.refresh_token is likely an OBJECT, not a string
             # We need to extract the .token string from it
             rt_token_str = result.refresh_token.token 
             
             info.context.response.set_cookie(
                settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE'],
                rt_token_str,
                httponly=settings.GRAPHQL_JWT['JWT_COOKIE_HTTPONLY'],
                samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
                secure=settings.GRAPHQL_JWT['JWT_COOKIE_SECURE'],
                max_age=settings.GRAPHQL_JWT['JWT_REFRESH_EXPIRATION_DELTA'].total_seconds(),
            )
            
        return result

class CustomRevokeToken(mutations.RevokeToken):
    @classmethod
    def resolve_mutation(cls, info, input_: resolvers.RevokeTokenMixin.RevokeTokenInput) -> RevokeRefreshTokenType:
        from django.conf import settings
        import dataclasses
        
        # If refresh token is not provided, try to get it from cookie
        if not input_.refresh_token:
            cookie_name = settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE']
            refresh_token = info.context.request.COOKIES.get(cookie_name)
            if refresh_token:
                try:
                    input_ = dataclasses.replace(input_, refresh_token=refresh_token)
                except Exception:
                    pass

        result = super().resolve_mutation(info, input_)

        # Debug: Log the deletion attempt
        print(f"DEBUG: Attempting to delete cookies")
        print(f"DEBUG: Cookie names: {settings.GRAPHQL_JWT['JWT_AUTH_COOKIE']}, {settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE']}")
        
        # Delete cookies with ALL matching parameters
        # Method 1: Use delete_cookie with all parameters
        info.context.response.delete_cookie(
            settings.GRAPHQL_JWT['JWT_AUTH_COOKIE'],
            path='/',
            samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
        )
        info.context.response.delete_cookie(
            settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE'],
            path='/',
            samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
        )
        
        # Method 2: Also set expired cookies as a fallback
        # This approach sets the cookie with max_age=0 which forces immediate expiration
        info.context.response.set_cookie(
            settings.GRAPHQL_JWT['JWT_AUTH_COOKIE'],
            '',
            max_age=0,
            httponly=settings.GRAPHQL_JWT['JWT_COOKIE_HTTPONLY'],
            samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
            secure=settings.GRAPHQL_JWT['JWT_COOKIE_SECURE'],
            path='/',
        )
        info.context.response.set_cookie(
            settings.GRAPHQL_JWT['JWT_AUTH_REFRESH_COOKIE'],
            '',
            max_age=0,
            httponly=settings.GRAPHQL_JWT['JWT_COOKIE_HTTPONLY'],
            samesite=settings.GRAPHQL_JWT['JWT_COOKIE_SAMESITE'],
            secure=settings.GRAPHQL_JWT['JWT_COOKIE_SECURE'],
            path='/',
        )
        
        print("DEBUG: Cookie deletion commands executed")

        return result

class CustomVerifyAccount(mutations.VerifyAccount):
    @classmethod
    def resolve_mutation(cls, info, input_: resolvers.VerifyAccountMixin.VerifyAccountInput) -> resolvers.MutationNormalOutput:
        # Call the parent resolver first
        result = super().resolve_mutation(info, input_)
        
        # If verification was successful, also set is_active=True
        if result.success:
            # The parent resolver already verified the user via UserStatus
            # Now we need to activate the user account
            try:
                # Get the user from the token
                from gqlauth.models import UserStatus
                from django.contrib.auth import get_user_model
                
                User = get_user_model()
                # Find the user that was just verified
                # We can search for recently verified users
                user_status = UserStatus.objects.filter(verified=True).order_by('-id').first()
                if user_status and user_status.user:
                    user = user_status.user
                    user.is_active = True
                    user.save()
            except Exception as e:
                # Log but don't fail the verification
                print(f"Error activating user: {e}")
        
        return result

@strawberry.type
class Mutation:
    # --- Standard Auth Tools (Login/Tokens) ---
    token_auth = CustomObtainJSONWebToken.field
    verify_token = mutations.VerifyToken.field
    refresh_token = CustomRefreshToken.field
    revoke_token = CustomRevokeToken.field

    # --- Account Management Helpers ---
    verify_account = CustomVerifyAccount.field
    update_account = mutations.UpdateAccount.field
    delete_account = mutations.DeleteAccount.field
    password_change = mutations.PasswordChange.field
    password_reset = mutations.PasswordReset.field
    password_set = mutations.PasswordSet.field
    
    # --- CUSTOM REGISTRATION LOGIC ---
    @strawberry.mutation
    def register(
        self, 
        info,
        username: str, 
        email: str, 
        password: str
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
        # We use transaction.atomic to ensure user creation and email sending (or status update) happen together
        from django.db import transaction

        with transaction.atomic():
            user = CustomUser.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            
            # Force "Unverified" state
            user.is_active = False
            user.save()
            
            # Send Email using Library Utility
            # gqlauth attaches a 'status' OneToOne field to the user (UserStatus model)
            # We call the method on that related object.
            if hasattr(user, 'status'):
                user.status.send_activation_email(info)
        
        return user

    @strawberry.mutation
    def delete_all_users(self) -> str:
        count, _ = CustomUser.objects.all().delete()
        return f"Deleted {count} users"

# 4. Schema Wrapper
# We keep this here so this file can be tested in isolation if needed.
schema = strawberry.Schema(query=Query, mutation=Mutation)