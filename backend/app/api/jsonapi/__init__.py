"""
JSON:API Package

Utilities for JSON:API compliant API responses.
Reference: https://jsonapi.org/format/
"""

from app.api.jsonapi.serializers import (
    JSONAPISerializer,
    FlowSerializer,
    FlowVersionSerializer,
    LLMProfileSerializer,
    AgentTemplateSerializer,
)
from app.api.jsonapi.errors import (
    JSONAPIError,
    JSONAPIErrorResponse,
    from_platform_error,
    validation_error,
    not_found_error,
    internal_error,
)
from app.api.jsonapi.pagination import (
    Paginator,
    PaginationMeta,
    CursorPaginator,
)

__all__ = [
    # Serializers
    "JSONAPISerializer",
    "FlowSerializer",
    "FlowVersionSerializer",
    "LLMProfileSerializer",
    "AgentTemplateSerializer",
    # Errors
    "JSONAPIError",
    "JSONAPIErrorResponse",
    "from_platform_error",
    "validation_error",
    "not_found_error",
    "internal_error",
    # Pagination
    "Paginator",
    "PaginationMeta",
    "CursorPaginator",
]
