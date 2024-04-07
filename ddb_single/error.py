class DDBSingleError(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ValidationError(DDBSingleError):

    def __str__(self):
        return f"Falied to validate: {self.message}"


class InvalidParameterError(DDBSingleError):

    def __str__(self):
        return f"Invalid parameter: {self.message}"


class NotFoundError(DDBSingleError):

    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Item not found: {self.message}"
