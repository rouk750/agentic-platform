"""
Centralized Configuration Management for Agentic Platform Backend.

Uses Pydantic Settings for validation and environment variable support.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    All settings have sensible defaults for local development.
    """
    
    # Database
    database_url: str = Field(
        default="sqlite:///./database.db",
        description="SQLAlchemy database URL"
    )
    checkpoints_db_path: str = Field(
        default="checkpoints.sqlite",
        description="Path to LangGraph checkpoints database"
    )
    db_pool_size: int = Field(
        default=5,
        ge=1,
        description="SQLAlchemy pool size (number of connections to keep open)"
    )
    db_max_overflow: int = Field(
        default=10,
        ge=0,
        description="SQLAlchemy max overflow (connections above pool size)"
    )
    db_pool_timeout: int = Field(
        default=30,
        ge=1,
        description="SQLAlchemy pool timeout in seconds"
    )
    db_pool_recycle: int = Field(
        default=1800,
        ge=60,
        description="SQLAlchemy pool recycle time in seconds"
    )
    
    # LangGraph Execution
    langgraph_recursion_limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum recursion depth for graph execution"
    )
    max_subgraph_depth: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum nesting depth for subgraphs"
    )
    
    # MCP (Model Context Protocol)
    mcp_config_path: str = Field(
        default="mcp_config.json",
        description="Path to MCP servers configuration file"
    )
    
    # Tool Execution
    max_tool_output_length: int = Field(
        default=50000,
        ge=1000,
        description="Maximum characters for tool output (prevents context explosion)"
    )
    
    # LLM Settings
    llm_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts for LLM calls"
    )
    llm_retry_min_wait: float = Field(
        default=2.0,
        ge=0.5,
        description="Minimum wait time (seconds) between retries"
    )
    llm_retry_max_wait: float = Field(
        default=10.0,
        ge=1.0,
        description="Maximum wait time (seconds) between retries"
    )
    
    # Cache Settings
    llm_profile_cache_size: int = Field(
        default=50,
        ge=10,
        description="Maximum number of LLM profiles to cache"
    )
    llm_profile_cache_ttl: int = Field(
        default=300,
        ge=60,
        description="TTL in seconds for cached LLM profiles"
    )
    
    # Security
    allow_path_traversal: bool = Field(
        default=False,
        description="Allow file operations outside working directory (DANGEROUS)"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        pattern="^(json|console)$",
        description="Log output format"
    )
    
    # API Settings
    api_prefix: str = Field(
        default="/api",
        description="API route prefix"
    )
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins"
    )
    
    # Feature Flags
    enable_json_api: bool = Field(
        default=False,
        description="Enable JSON:API format for responses"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns a cached singleton instance of Settings.
    The cache is invalidated only on application restart.
    """
    return Settings()


# Convenience alias for direct import
settings = get_settings()
