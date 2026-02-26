from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------

class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, detail: str = "Resource not found"):
        self.detail = detail
        super().__init__(self.detail)


class ConflictError(Exception):
    """Raised on duplicate or conflicting state."""

    def __init__(self, detail: str = "Conflict"):
        self.detail = detail
        super().__init__(self.detail)


class ValidationError(Exception):
    """Raised when business-rule validation fails (distinct from Pydantic validation)."""

    def __init__(self, detail: str = "Validation error"):
        self.detail = detail
        super().__init__(self.detail)


class AuthenticationError(Exception):
    """Raised when authentication credentials are missing or invalid."""

    def __init__(self, detail: str = "Not authenticated"):
        self.detail = detail
        super().__init__(self.detail)


class AuthorizationError(Exception):
    """Raised when the user lacks permission for the requested action."""

    def __init__(self, detail: str = "Forbidden"):
        self.detail = detail
        super().__init__(self.detail)


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """Attach custom exception handlers to the FastAPI application."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_request: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content={"detail": exc.detail})

    @app.exception_handler(ValidationError)
    async def validation_handler(_request: Request, exc: ValidationError):
        return JSONResponse(status_code=422, content={"detail": exc.detail})

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(_request: Request, exc: AuthenticationError):
        return JSONResponse(status_code=401, content={"detail": exc.detail})

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(_request: Request, exc: AuthorizationError):
        return JSONResponse(status_code=403, content={"detail": exc.detail})
