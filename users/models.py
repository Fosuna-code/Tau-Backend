from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # We make email unique and required for a modern auth system
    email = models.EmailField(unique=True, verbose_name="email address")
    


    # Standard Django configurations
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    # Fields required when running 'python manage.py createsuperuser'
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username