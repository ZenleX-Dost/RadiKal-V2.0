"""
Centralized error handling middleware for production.

Features:
- User-friendly error messages
- Detailed logging for debugging
- Error tracking integration
- Automatic error categorization
- Security-safe error responses
"""

from typing import Any, Dict, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging
import traceback
from datetime import datetime
import sys

logger = logging.getLogger(__name__)


class ErrorCategory:
    """Error categories for classification."""
    VALIDATION = "validation_error"
    DATABASE = "database_error"
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    NOT_FOUND = "not_found"
    RATE_LIMIT = "rate_limit_exceeded"
    ML_MODEL = "model_error"
    FILE_PROCESSING = "file_error"
    EXTERNAL_API = "external_api_error"
    SERVER = "server_error"
    UNKNOWN = "unknown_error"


class ApplicationError(Exception):
    """Base application error with context."""
    
    def __init__(
        self,
        message: str,
        category: str = ErrorCategory.UNKNOWN,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        """
        Initialize application error.
        
        Args:
            message: Technical error message (for logs)
            category: Error category
            status_code: HTTP status code
            details: Additional error context
            user_message: User-friendly message (if different from technical)
        """
        super().__init__(message)
        self.message = message
        self.category = category
        self.status_code = status_code
        self.details = details or {}
        self.user_message = user_message or self._get_user_friendly_message()
    
    def _get_user_friendly_message(self) -> str:
        """Generate user-friendly message based on category."""
        friendly_messages = {
            ErrorCategory.VALIDATION: "Invalid input data. Please check your request and try again.",
            ErrorCategory.DATABASE: "Database operation failed. Please try again later.",
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please log in again.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.NOT_FOUND: "The requested resource was not found.",
            ErrorCategory.RATE_LIMIT: "Too many requests. Please slow down and try again.",
            ErrorCategory.ML_MODEL: "Model inference failed. Please try with a different image.",
            ErrorCategory.FILE_PROCESSING: "File processing failed. Please check the file format.",
            ErrorCategory.EXTERNAL_API: "External service unavailable. Please try again later.",
            ErrorCategory.SERVER: "An unexpected error occurred. Our team has been notified.",
        }
        return friendly_messages.get(self.category, self.message)


class ErrorLogger:
    """Enhanced error logging with context."""
    
    @staticmethod
    def log_error(
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        """
        Log error with full context.
        
        Args:
            error: Exception instance
            request: FastAPI request object
            user_id: User identifier
            additional_context: Extra context data
        """
        # Build error context
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }
        
        # Add request context
        if request:
            context.update({
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent"),
            })
        
        # Add user context
        if user_id:
            context["user_id"] = user_id
        
        # Add additional context
        if additional_context:
            context.update(additional_context)
        
        # Log based on severity
        if isinstance(error, ApplicationError):
            if error.status_code >= 500:
                logger.error(f"Server Error: {error.message}", extra=context)
            elif error.status_code >= 400:
                logger.warning(f"Client Error: {error.message}", extra=context)
            else:
                logger.info(f"Error: {error.message}", extra=context)
        else:
            logger.error(f"Unhandled Error: {str(error)}", extra=context)


def create_error_response(
    error: Exception,
    request: Request,
    include_details: bool = False
) -> JSONResponse:
    """
    Create standardized error response.
    
    Args:
        error: Exception instance
        request: FastAPI request
        include_details: Include technical details (dev mode only)
        
    Returns:
        JSONResponse with error details
    """
    # Determine status code and message
    if isinstance(error, ApplicationError):
        status_code = error.status_code
        error_category = error.category
        user_message = error.user_message
        technical_message = error.message
        details = error.details
    elif isinstance(error, HTTPException):
        status_code = error.status_code
        error_category = _categorize_http_exception(error)
        user_message = str(error.detail)
        technical_message = str(error.detail)
        details = {}
    elif isinstance(error, RequestValidationError):
        status_code = 422
        error_category = ErrorCategory.VALIDATION
        user_message = "Invalid input data. Please check your request."
        technical_message = str(error)
        details = {"validation_errors": error.errors()}
    elif isinstance(error, ValidationError):
        status_code = 422
        error_category = ErrorCategory.VALIDATION
        user_message = "Data validation failed."
        technical_message = str(error)
        details = {"validation_errors": error.errors()}
    elif isinstance(error, SQLAlchemyError):
        status_code = 500
        error_category = ErrorCategory.DATABASE
        user_message = "Database operation failed. Please try again."
        technical_message = str(error)
        details = {}
    else:
        status_code = 500
        error_category = ErrorCategory.SERVER
        user_message = "An unexpected error occurred."
        technical_message = str(error)
        details = {}
    
    # Build response
    response_data = {
        "error": True,
        "category": error_category,
        "message": user_message,
        "timestamp": datetime.utcnow().isoformat(),
        "path": request.url.path,
    }
    
    # Add technical details in development mode
    if include_details:
        response_data["technical_message"] = technical_message
        response_data["details"] = details
        response_data["traceback"] = traceback.format_exc().split("\n")
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def _categorize_http_exception(error: HTTPException) -> str:
    """Categorize HTTP exception."""
    if error.status_code == 401:
        return ErrorCategory.AUTHENTICATION
    elif error.status_code == 403:
        return ErrorCategory.AUTHORIZATION
    elif error.status_code == 404:
        return ErrorCategory.NOT_FOUND
    elif error.status_code == 429:
        return ErrorCategory.RATE_LIMIT
    elif error.status_code >= 500:
        return ErrorCategory.SERVER
    else:
        return ErrorCategory.UNKNOWN


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handling middleware.
    
    Usage in main.py:
        from core.middleware.error_handler import error_handler_middleware
        app.middleware("http")(error_handler_middleware)
    """
    try:
        response = await call_next(request)
        return response
    
    except Exception as error:
        # Log error with context
        user_id = getattr(request.state, "user_id", None) if hasattr(request.state, "user_id") else None
        ErrorLogger.log_error(error, request, user_id)
        
        # Check if development mode
        is_dev = sys.argv[0].endswith("uvicorn") and "--reload" in sys.argv
        
        # Create error response
        return create_error_response(error, request, include_details=is_dev)


# Exception handlers for FastAPI
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    ErrorLogger.log_error(exc, request)
    return create_error_response(exc, request)


async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    if exc.status_code >= 500:
        ErrorLogger.log_error(exc, request)
    return create_error_response(exc, request)


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    ErrorLogger.log_error(exc, request)
    return create_error_response(exc, request)


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    ErrorLogger.log_error(exc, request)
    return create_error_response(exc, request, include_details=False)
