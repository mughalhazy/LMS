class TenantServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400, detail=None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail or {"message": message}
