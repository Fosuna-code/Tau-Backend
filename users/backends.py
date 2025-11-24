"""
Custom Authentication Backend for Email-Based Login

This backend allows users to authenticate using their email address
instead of a username, which aligns with our CustomUser model where
USERNAME_FIELD = "email".
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authenticate using email address instead of username.
    
    This is necessary because our CustomUser model uses email as the
    USERNAME_FIELD, but we want to support both email and username
    for flexibility.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user based on email or username.
        
        Args:
            request: The HTTP request object
            username: Can be either email or username
            password: The user's password
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        try:
            # Try to fetch the user by searching for email first
            # This handles the case where username parameter contains an email
            if '@' in username:
                user = UserModel.objects.get(email=username)
            else:
                # Fall back to username field
                user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            UserModel().set_password(password)
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        
        return None
