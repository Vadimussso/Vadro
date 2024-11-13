class UserRequiredError(ValueError):
    def __init__(self, message="User is required"):
        super().__init__(message)


class UserCredentialsError(ValueError):

    def __init__(self, message="Wrong credentials"):
        super().__init__(message)


class ItemRequiredError(ValueError):
    def __init__(self, message="Item is not represented"):
        super().__init__(message)