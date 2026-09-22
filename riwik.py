def is_palindrome(s):
    """
    Check whether a given string is a palindrome.
    
    Ignores spaces and is case-insensitive.
    An empty string or a string containing only non-alphanumeric characters
    is considered a palindrome.
    
    Args:
        s (str): The string to check.
        
    Returns:
        bool: True if the string is a palindrome, False otherwise.
    """
    if not s:
        return True
    
    # Normalize: remove spaces and convert to lowercase
    cleaned = "".join(char.lower() for char in s if char != " ")
    
    # If no alphanumeric characters, it's a palindrome
    if not any(c.isalnum() for c in cleaned):
        return True
    
    # Compare with reverse
    return cleaned == cleaned[::-1]
