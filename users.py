import re
import hashlib


def validate_password(password):
    """
    Validate a password against the following criteria:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one number
    - Contains at least one special character
    
    Args:
        password: The password string to validate
        
    Returns:
        True if the password meets all criteria, False otherwise
    """
    if not password or len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[^A-Za-z0-9]', password):
        return False
    
    return True


class User:
    def __init__(self, user_id, full_name, email, phone, password=None):
        self.user_id = user_id
        self.full_name = full_name
        self.email = email
        self.phone = phone
        if password is None:
            self.password = hashlib.sha256(b"").hexdigest()
        else:
            self.password = password

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone
        }

    def __repr__(self):
        return f"User(user_id={self.user_id!r}, full_name={self.full_name!r}, email={self.email!r}, phone={self.phone!r})"
    def __repr__(self):
        return f"User(user_id={self.user_id!r}, full_name={self.full_name!r}, email={self.email!r}, phone={self.phone!r})"

    def login(self, provided_password):
        """
        Attempt to login with the provided password.
        
        Args:
            provided_password: The password provided by the user
            
        Returns:
            True if login succeeds (password is valid and matches), False otherwise
        """
        if not validate_password(provided_password):
            return False
        return provided_password == self.password
