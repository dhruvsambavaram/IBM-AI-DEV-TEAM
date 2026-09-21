import users


def main():
    print("hi")


def test__mine_minesweeper_():
    import minesweeper
    b = minesweeper.Board(5, 5, 3)
    b2 = b.generate_gameboard(b.grid, 3, 42)
    assert sum(sum(r) for r in b2) == 3


def test_health_endpoint():
    import health_endpoint
    status, body = health_endpoint.health()
    assert status == 200
    assert body == {"status": "ok"}


def test_valid_password():
    """Test that valid passwords are accepted."""
    assert users.validate_password("Pass123!") is True
    assert users.validate_password("MyP@ssw0rd") is True
    assert users.validate_password("Str0ng#Pass") is True
    assert users.validate_password("Valid1Pass!") is True


def test_password_too_short():
    """Test that passwords shorter than 8 characters are rejected."""
    assert users.validate_password("Pass1!") is False
    assert users.validate_password("A1!") is False
    assert users.validate_password("") is False
    assert users.validate_password(None) is False


def test_password_no_uppercase():
    """Test that passwords without uppercase letters are rejected."""
    assert users.validate_password("password1!") is False
    assert users.validate_password("pass123@word") is False


def test_password_no_number():
    """Test that passwords without numbers are rejected."""
    assert users.validate_password("Password!") is False
    assert users.validate_password("Password@") is False


def test_password_no_special():
    """Test that passwords without special characters are rejected."""
    assert users.validate_password("Password1") is False
    assert users.validate_password("MyPassword") is False


def test_password_multiple_invalid():
    """Test that passwords missing multiple criteria are rejected."""
    assert users.validate_password("password") is False  # no uppercase, no number, no special
    assert users.validate_password("12345678") is False  # no uppercase, no special
    assert users.validate_password("PASSWORD") is False  # no number, no special


def main():
    print("hi")
if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
