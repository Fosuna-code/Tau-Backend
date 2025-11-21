import strawberry
from gqlauth.core.middlewares import JwtSchema

# 1. Import the schema classes from your apps
# We alias them (as ...Query) to avoid name collisions
from users.schema import Query as UserQuery, Mutation as UserMutation
from streaming.schema import Query as StreamingQuery, Mutation as StreamingMutation

# 2. Merge the Queries
# We inherit from both classes so the API can read Users AND Movies
@strawberry.type
class Query(UserQuery, StreamingQuery):
    pass

# 3. Merge the Mutations
# We inherit from both so the API can Login/Register AND Create Movies
@strawberry.type
class Mutation(UserMutation, StreamingMutation):
    pass

# 4. Create the Final Schema
# We use JwtSchema to ensure the Authentication Middleware works for everything
schema = JwtSchema(query=Query, mutation=Mutation)