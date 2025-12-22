"""
JSON:API Serializers

Transforms domain objects to JSON:API format responses.
Reference: https://jsonapi.org/format/
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any, Callable
from abc import ABC, abstractmethod

T = TypeVar('T')


class JSONAPISerializer(ABC, Generic[T]):
    """
    Abstract base serializer for JSON:API format.
    
    Subclasses must define:
    - resource_type: The JSON:API type (e.g., "flows")
    - _get_id: Extract ID from object
    - _get_attributes: Extract attributes from object
    """
    
    resource_type: str
    
    @abstractmethod
    def _get_id(self, obj: T) -> str:
        """Get string ID from object."""
        pass
    
    @abstractmethod
    def _get_attributes(self, obj: T) -> Dict[str, Any]:
        """Get attributes dictionary from object."""
        pass
    
    def _get_relationships(self, obj: T) -> Optional[Dict[str, Any]]:
        """Get relationships (override in subclass if needed)."""
        return None
    
    def _get_links(self, obj: T, base_url: str = "") -> Dict[str, str]:
        """Get resource links."""
        obj_id = self._get_id(obj)
        return {"self": f"{base_url}/{self.resource_type}/{obj_id}"}
    
    def serialize_resource(self, obj: T) -> Dict[str, Any]:
        """Serialize single object to JSON:API resource object."""
        resource = {
            "type": self.resource_type,
            "id": self._get_id(obj),
            "attributes": self._get_attributes(obj)
        }
        
        relationships = self._get_relationships(obj)
        if relationships:
            resource["relationships"] = relationships
        
        return resource
    
    def serialize_one(
        self, 
        obj: T, 
        base_url: str = "/api",
        include_links: bool = True
    ) -> Dict[str, Any]:
        """
        Serialize single object to complete JSON:API document.
        
        Returns:
            {
                "data": { resource object },
                "links": { "self": "..." }
            }
        """
        result = {"data": self.serialize_resource(obj)}
        
        if include_links:
            result["links"] = self._get_links(obj, base_url)
        
        return result
    
    def serialize_many(
        self,
        objects: List[T],
        base_url: str = "/api",
        total: Optional[int] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Serialize list of objects to JSON:API collection document.
        
        Returns:
            {
                "data": [ ... resource objects ... ],
                "meta": { "total": N, "page": M, "per_page": P },
                "links": { "self": "...", "next": "...", "prev": "..." }
            }
        """
        result = {
            "data": [self.serialize_resource(obj) for obj in objects],
            "meta": {
                "total": total if total is not None else len(objects),
                "page": page,
                "per_page": per_page
            }
        }
        
        # Pagination links
        total_count = total if total is not None else len(objects)
        total_pages = (total_count + per_page - 1) // per_page if per_page > 0 else 1
        
        links = {"self": f"{base_url}/{self.resource_type}?page={page}&per_page={per_page}"}
        
        if page < total_pages:
            links["next"] = f"{base_url}/{self.resource_type}?page={page + 1}&per_page={per_page}"
        if page > 1:
            links["prev"] = f"{base_url}/{self.resource_type}?page={page - 1}&per_page={per_page}"
        
        links["first"] = f"{base_url}/{self.resource_type}?page=1&per_page={per_page}"
        links["last"] = f"{base_url}/{self.resource_type}?page={total_pages}&per_page={per_page}"
        
        result["links"] = links
        
        return result


# Concrete Serializers

class FlowSerializer(JSONAPISerializer):
    """Serializer for Flow entities."""
    
    resource_type = "flows"
    
    def _get_id(self, obj) -> str:
        return str(obj.id)
    
    def _get_attributes(self, obj) -> Dict[str, Any]:
        return {
            "name": obj.name,
            "description": obj.description,
            "is_archived": obj.is_archived,
            "data": obj.data,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None
        }
    
    def _get_relationships(self, obj) -> Dict[str, Any]:
        return {
            "versions": {
                "links": {"related": f"/api/flows/{obj.id}/versions"}
            }
        }


class FlowVersionSerializer(JSONAPISerializer):
    """Serializer for FlowVersion entities."""
    
    resource_type = "flow-versions"
    
    def _get_id(self, obj) -> str:
        return str(obj.id)
    
    def _get_attributes(self, obj) -> Dict[str, Any]:
        return {
            "flow_id": obj.flow_id,
            "data": obj.data,
            "is_locked": obj.is_locked,
            "created_at": obj.created_at.isoformat() if obj.created_at else None
        }


class LLMProfileSerializer(JSONAPISerializer):
    """Serializer for LLMProfile entities."""
    
    resource_type = "llm-profiles"
    
    def _get_id(self, obj) -> str:
        return str(obj.id)
    
    def _get_attributes(self, obj) -> Dict[str, Any]:
        return {
            "name": obj.name,
            "provider": obj.provider.value if hasattr(obj.provider, 'value') else str(obj.provider),
            "model_id": obj.model_id,
            "base_url": obj.base_url,
            "temperature": obj.temperature,
            "has_api_key": bool(obj.api_key_ref)
        }


class AgentTemplateSerializer(JSONAPISerializer):
    """Serializer for AgentTemplate entities."""
    
    resource_type = "agent-templates"
    
    def _get_id(self, obj) -> str:
        return str(obj.id)
    
    def _get_attributes(self, obj) -> Dict[str, Any]:
        return {
            "name": obj.name,
            "description": obj.description,
            "type": obj.type,
            "config": obj.config,
            "is_archived": obj.is_archived,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None
        }
