import pytest
from riwik import is_palindrome


def test_valid_palindromes():
    assert is_palindrome("racecar") is True
    assert is_palindrome("A man a plan a canal Panama") is True
    assert is_palindrome("Was it a car or a cat I saw") is True
    assert is_palindrome("No lemon, no melon") is True
    assert is_palindrome("hello") is False
    assert is_palindrome("world") is False


def test_case_insensitive():
    assert is_palindrome("RaceCar") is True
    assert is_palindrome("RaCeCaR") is True
    assert is_palindrome("aA") is True
    assert is_palindrome("Ab") is False


def test_single_character():
    assert is_palindrome("a") is True
    assert is_palindrome("Z") is True


def test_empty_string():
    assert is_palindrome("") is True


def test_whitespace_only():
    assert is_palindrome(" ") is True
    assert is_palindrome("   ") is True
    assert is_palindrome("\t") is True


def test_mixed_case_with_spaces():
    assert is_palindrome("A Santa at NASA") is True
    assert is_palindrome("Never odd or even") is True


def test_non_palindromes():
    assert is_palindrome("hello world") is False
    assert is_palindrome("python") is False


def test_special_characters_and_digits():
    assert is_palindrome("12321") is True
    assert is_palindrome("12345") is False
    assert is_palindrome("A, a") is True
    assert is_palindrome("A, b") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
