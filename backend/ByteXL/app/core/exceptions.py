from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.logging import get_logger

logger = get_logger("app.exceptions")


class AppException(Exception):
    """Base exception for application-level errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class DatabaseConnectionError(AppException):
    """Raised when database connectivity fails."""

    def __init__(
        self,
        message: str = "Failed to establish database connection.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
            details=details,
        )


class ConfigurationError(AppException):
    """Raised when runtime or startup configuration is invalid."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


class ResourceNotFoundError(AppException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Requested resource not found.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


# Aliases and additional domain exceptions
AppError = AppException
NotFoundError = ResourceNotFoundError


class ValidationError(AppException):
    """Raised when business validation or domain rules fail."""

    def __init__(
        self,
        message: str = "Validation failed.",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(AppException):
    """Raised when authentication credentials are missing, invalid, or expired."""

    def __init__(
        self,
        message: str = "Authentication failed. Valid credentials required.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_FAILED",
            details=details,
        )


class AuthorizationError(AppException):
    """Raised when authenticated user lacks permissions for a role or resource."""

    def __init__(
        self,
        message: str = "Access forbidden. Insufficient permissions.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="ACCESS_FORBIDDEN",
            details=details,
        )


BadRequestError = ValidationError
ForbiddenError = AuthorizationError


class AccountSuspendedError(AppException):
    """Raised when accessing services with a suspended account."""

    def __init__(
        self,
        message: str = "Account is suspended. Access denied.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="ACCOUNT_SUSPENDED",
            details=details,
        )


class RateLimitExceededError(AppException):
    """Raised when an operation exceeds allowed rate limits."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please wait before trying again.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
        )


class OTPVerificationError(AppException):
    """Raised when OTP is invalid, expired, or maximum attempts reached."""

    def __init__(
        self,
        message: str = "Invalid or expired verification code.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_OTP",
            details=details,
        )


class OTPDeliveryError(AppException):
    """Raised when SMS delivery or provider communication fails."""

    def __init__(
        self,
        message: str = "Failed to dispatch verification code.",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="OTP_DELIVERY_FAILED",
            details=details,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register centralized exception handlers on the FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            f"Handled application exception on {request.method} {request.url.path}: {exc.message}",
            extra={"error_code": exc.error_code, "status_code": exc.status_code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        safe_errors = [
            {
                "loc": [str(item) for item in err.get("loc", [])],
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", "")),
            }
            for err in exc.errors()
        ]
        logger.warning(
            f"Validation error on {request.method} {request.url.path}: {safe_errors}"
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed.",
                    "details": {"errors": safe_errors},
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact system administrator.",
                    "details": {},
                }
            },
        )

    @app.middleware("http")
    async def global_exception_middleware(request: Request, call_next: Any) -> JSONResponse:
        try:
            return await call_next(request)
        except AppException as exc:
            return await app_exception_handler(request, exc)
        except Exception as exc:
            return await unhandled_exception_handler(request, exc)

