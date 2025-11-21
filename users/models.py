from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # We make email unique and required for a modern auth system
    email = models.EmailField(unique=True, verbose_name="email address")
    
    # Custom fields we added in the schema
    full_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Standard Django configurations
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    # Fields required when running 'python manage.py createsuperuser'
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username