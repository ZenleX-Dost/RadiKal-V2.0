"""
Security headers middleware for production hardening.

Adds security headers to all responses:
- X-Content-Type-Options: Prevents MIME sniffing
- X-Frame-Options: Prevents clickjacking
- X-XSS-Protection: XSS filter (legacy browsers)
- Strict-Transport-Security: Forces HTTPS
- Content-Security-Policy: Restricts resource loading
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Controls browser features
"""

from typing import Optional
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    def __init__(
        self,
        app,
        content_security_policy: Optional[str] = None,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        enable_xss_protection: bool = True,
        frame_options: str = "DENY",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[str] = None,
    ):
        """
        Initialize security headers middleware.
        
        Args:
            app: FastAPI application
            content_security_policy: CSP header value
            enable_hsts: Enable HSTS header
            hsts_max_age: HSTS max-age in seconds
            enable_xss_protection: Enable X-XSS-Protection
            frame_options: X-Frame-Options value
            referrer_policy: Referrer-Policy value
            permissions_policy: Permissions-Policy value
        """
        super().__init__(app)
        self.content_security_policy = content_security_policy or self._default_csp()
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.enable_xss_protection = enable_xss_protection
        self.frame_options = frame_options
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy or self._default_permissions_policy()
    
    def _default_csp(self) -> str:
        """Get default Content Security Policy."""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow for API docs
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.supabase.co wss://*.supabase.co; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
    
    def _default_permissions_policy(self) -> str:
        """Get default Permissions Policy."""
        return (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = self.frame_options
        
        # XSS Protection (for older browsers)
        if self.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict Transport Security (HTTPS only)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={self.hsts_max_age}; includeSubDomains"
            )
        
        # Content Security Policy
        if self.content_security_policy:
            response.headers["Content-Security-Policy"] = self.content_security_policy
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy
        
        # Permissions Policy (previously Feature-Policy)
        if self.permissions_policy:
            response.headers["Permissions-Policy"] = self.permissions_policy
        
        # Cache Control for sensitive endpoints
        if "/api/" in str(request.url.path):
            # Don't cache API responses by default
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                response.headers["Pragma"] = "no-cache"
        
        return response


async def security_headers_middleware(request: Request, call_next) -> Response:
    """
    Simple function-based security headers middleware.
    
    Use this if you prefer not to use the class-based middleware.
    """
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    
    # HSTS (only if HTTPS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
