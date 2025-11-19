from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True) # Force unique emails
    is_premium = models.BooleanField(default=False) # For your subscription logic
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # Fix the "reverse accessor" conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    USERNAME_FIELD = 'email' # Log in with Email, not Username
    REQUIRED_FIELDS = ['username']