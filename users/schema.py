import strawberry
from strawberry_django_jwt.middleware import JSONWebTokenMiddleware
from strawberry_django_jwt.decorators import login_required
import strawberry_django_jwt.mutations as jwt_mutations
from .models import CustomUser

# 1. Define the User Type
@strawberry.type
class UserType:
    id: strawberry.ID
    email: str
    username: str
    is_premium: bool

# 2. Create the Register Mutation (Custom Logic)
@strawberry.type
class Mutation:
    # Default JWT mutations (Login, Verify, Refresh)
    token_auth = jwt_mutations.ObtainJSONWebToken.field
    verify_token = jwt_mutations.Verify.field
    refresh_token = jwt_mutations.Refresh.field

    # Custom Register logic
    @strawberry.mutation
    def register(self, email: str, password: str, username: str) -> UserType:
        if CustomUser.objects.filter(email=email).exists():
            raise Exception("Email already exists")
        
        user = CustomUser.objects.create_user(
            username=username, 
            email=email, 
            password=password
        )
        return user