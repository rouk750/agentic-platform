"""
JSON:API Error Handling

Provides JSON:API compliant error responses.
Reference: https://jsonapi.org/format/#errors
"""

from typing import List, Optional, Dict, Any
from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import AgenticPlatformError


class JSONAPIError:
    """Represents a single JSON:API error object."""
    
    def __init__(
        self,
        status: int,
        code: str,
        title: str,
        detail: Optional[str] = None,
        source: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None
    ):
        self.status = status
        self.code = code
        self.title = title
        self.detail = detail
        self.source = source
        self.meta = meta
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON:API error object."""
        error = {
            "status": str(self.status),
            "code": self.code,
            "title": self.title
        }
        
        if self.detail:
            error["detail"] = self.detail
        if self.source:
            error["source"] = self.source
        if self.meta:
            error["meta"] = self.meta
        
        return error


class JSONAPIErrorResponse:
    """Represents a JSON:API error response document."""
    
    def __init__(self, errors: List[JSONAPIError]):
        self.errors = errors
    
    @property
    def status_code(self) -> int:
        """Get HTTP status code (highest among errors)."""
        if not self.errors:
            return 500
        return max(e.status for e in self.errors)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON:API errors document."""
        return {"errors": [e.to_dict() for e in self.errors]}
    
    def to_response(self) -> JSONResponse:
        """Create FastAPI JSONResponse."""
        return JSONResponse(
            status_code=self.status_code,
            content=self.to_dict(),
            media_type="application/vnd.api+json"
        )


# Factory functions

def from_platform_error(exc: AgenticPlatformError) -> JSONAPIErrorResponse:
    """Create JSON:API error response from platform exception."""
    error = JSONAPIError(
        status=exc.status_code,
        code=exc.error_code,
        title=exc.__class__.__name__,
        detail=exc.message,
        meta=exc.details if exc.details else None
    )
    return JSONAPIErrorResponse([error])


def validation_error(
    message: str,
    field: Optional[str] = None
) -> JSONAPIErrorResponse:
    """Create validation error response."""
    source = {"pointer": f"/data/attributes/{field}"} if field else None
    error = JSONAPIError(
        status=422,
        code="VALIDATION_ERROR",
        title="Validation Error",
        detail=message,
        source=source
    )
    return JSONAPIErrorResponse([error])


def not_found_error(
    resource_type: str,
    resource_id: Any
) -> JSONAPIErrorResponse:
    """Create not found error response."""
    error = JSONAPIError(
        status=404,
        code="RESOURCE_NOT_FOUND",
        title="Resource Not Found",
        detail=f"{resource_type} with ID {resource_id} not found"
    )
    return JSONAPIErrorResponse([error])


def internal_error(message: str = "An unexpected error occurred") -> JSONAPIErrorResponse:
    """Create internal server error response."""
    error = JSONAPIError(
        status=500,
        code="INTERNAL_ERROR",
        title="Internal Server Error",
        detail=message
    )
    return JSONAPIErrorResponse([error])
