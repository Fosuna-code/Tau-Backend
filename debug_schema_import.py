
import os
import django
from django.conf import settings

# Configure Django settings manually if needed, or set env var
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tau.settings')
django.setup()

try:
    from users.schema import schema
    print("Schema imported successfully")
except Exception as e:
    print(f"Error importing schema: {e}")
    import traceback
    traceback.print_exc()
