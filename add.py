def addition(a, b):
    return a + b


if __name__ == "__main__":
    result = addition(3, 5)
    assert result == 8, f"Expected 8, got {result}"
    print(f"Test Passed: addition(3, 5) == {result}")

