import hashlib


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
