class InstitutionServiceError(Exception):
    """Raised when institution service validation or state transitions fail."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
