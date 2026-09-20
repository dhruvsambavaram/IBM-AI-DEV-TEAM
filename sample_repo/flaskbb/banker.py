class InsufficientFundsError(Exception):
    """Exception raised when a withdrawal exceeds the account balance."""
    pass

class InvalidAmountError(Exception):
    """Exception raised when an invalid amount (non-positive, non-numeric) is provided."""
    pass

class Bank:
    """
    Banking system that manages bank accounts.
    Provides account creation, deposits, withdrawals, and secured transfers.
    """

    def __init__(self):
        self.accounts = {}  # Dict mapping account IDs to BankAccount objects
