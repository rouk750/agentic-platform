"""
JSON:API Pagination

Provides pagination utilities for JSON:API responses.
"""

from typing import TypeVar, Generic, List, Optional
from dataclasses import dataclass
from fastapi import Query

T = TypeVar('T')


@dataclass
class PaginationMeta:
    """Pagination metadata for responses."""
    total: int
    page: int
    per_page: int
    total_pages: int
    
    def to_dict(self):
        return {
            "total": self.total,
            "page": self.page,
            "per_page": self.per_page,
            "total_pages": self.total_pages
        }


class Paginator:
    """
    Pagination helper for API endpoints.
    
    Usage in FastAPI route:
        @app.get("/items")
        def list_items(paginator: Paginator = Depends()):
            items = get_items(skip=paginator.offset, limit=paginator.per_page)
            total = count_items()
            return paginator.paginate(items, total)
    """
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.per_page = per_page
    
    @property
    def offset(self) -> int:
        """Calculate database offset."""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Alias for per_page (for database queries)."""
        return self.per_page
    
    def get_meta(self, total: int) -> PaginationMeta:
        """Get pagination metadata."""
        total_pages = (total + self.per_page - 1) // self.per_page if self.per_page > 0 else 1
        return PaginationMeta(
            total=total,
            page=self.page,
            per_page=self.per_page,
            total_pages=total_pages
        )
    
    def get_links(self, base_url: str, total: int) -> dict:
        """Generate pagination links."""
        meta = self.get_meta(total)
        links = {
            "self": f"{base_url}?page={self.page}&per_page={self.per_page}",
            "first": f"{base_url}?page=1&per_page={self.per_page}",
            "last": f"{base_url}?page={meta.total_pages}&per_page={self.per_page}"
        }
        
        if self.page < meta.total_pages:
            links["next"] = f"{base_url}?page={self.page + 1}&per_page={self.per_page}"
        if self.page > 1:
            links["prev"] = f"{base_url}?page={self.page - 1}&per_page={self.per_page}"
        
        return links


class CursorPaginator:
    """
    Cursor-based pagination for large datasets.
    
    More efficient than offset-based for large tables.
    """
    
    def __init__(
        self,
        cursor: Optional[str] = Query(None, description="Cursor for next page"),
        limit: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.cursor = cursor
        self.limit = limit
    
    def decode_cursor(self) -> Optional[int]:
        """Decode cursor to last seen ID."""
        if self.cursor:
            try:
                import base64
                decoded = base64.b64decode(self.cursor.encode()).decode()
                return int(decoded)
            except Exception:
                return None
        return None
    
    @staticmethod
    def encode_cursor(last_id: int) -> str:
        """Encode ID to cursor string."""
        import base64
        return base64.b64encode(str(last_id).encode()).decode()
