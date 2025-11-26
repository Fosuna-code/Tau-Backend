import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tau.settings')
django.setup()

from gqlauth.user import arg_mutations as mutations
from gqlauth.user import resolvers

print("Attributes of gqlauth.user.arg_mutations:")
for attr in dir(mutations):
    if not attr.startswith("__"):
        print(attr)

print("\nAttributes of gqlauth.user.resolvers:")
for attr in dir(resolvers):
    if not attr.startswith("__"):
        print(attr)

try:
    print("\nChecking RevokeTokenMixin in resolvers:")
    if hasattr(resolvers, 'RevokeTokenMixin'):
        print("RevokeTokenMixin found")
        mixin = resolvers.RevokeTokenMixin
        if hasattr(mixin, 'RevokeTokenInput'):
             print("RevokeTokenMixin.RevokeTokenInput found")
        else:
             print("RevokeTokenMixin.RevokeTokenInput NOT found")
    else:
        print("RevokeTokenMixin NOT found")

    from gqlauth.jwt import types_
    print("\nAttributes of gqlauth.jwt.types_:")
    for attr in dir(types_):
        if not attr.startswith("__"):
            print(attr)
except Exception as e:
    print(f"Error checking mixin: {e}")
