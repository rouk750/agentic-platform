import argparse
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from app.database import engine
from app.config import settings
from app.logging import configure_logging, get_logger
from app.exceptions import AgenticPlatformError

# Configure structured logging before anything else
configure_logging()
logger = get_logger(__name__)

# Import routers
from app.api import settings as settings_router
from app.api import run
from app.api import tools
from app.api import flows
from app.api import smart_nodes
from app.api import guardrails
from app.api import agent_templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    logger.info("application_starting", version="0.2.0")
    
    # Load all models so that SQLModel knows about them
    from app.models import settings as settings_model
    from app.models import flow as flow_model
    from app.models import agent_template as agent_template_model
    SQLModel.metadata.create_all(engine)
    
    logger.info("database_initialized")
    yield
    
    logger.info("application_shutting_down")


app = FastAPI(
    title="Agentic Platform API",
    version="0.2.0",
    lifespan=lifespan
)


# Exception Handlers
@app.exception_handler(AgenticPlatformError)
async def agentic_platform_exception_handler(
    request: Request, 
    exc: AgenticPlatformError
) -> JSONResponse:
    """Handle all custom platform exceptions with JSON:API format."""
    logger.error(
        "platform_error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"errors": [exc.to_dict()]}
    )


# CORS Configuration
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
if "*" in cors_origins:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(settings_router.router, prefix=settings.api_prefix, tags=["settings"])
app.include_router(run.router, prefix=settings.api_prefix, tags=["run"])
app.include_router(tools.router, prefix=settings.api_prefix, tags=["tools"])
app.include_router(flows.router, prefix=settings.api_prefix, tags=["flows"])
app.include_router(smart_nodes.router, prefix=settings.api_prefix, tags=["smart-nodes"])
app.include_router(guardrails.router, prefix=settings.api_prefix, tags=["guardrails"])
app.include_router(agent_templates.router, prefix=settings.api_prefix, tags=["agent-templates"])


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "service": "Agentic Platform API", 
        "version": "0.2.0",
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "log_level": settings.log_level,
        "json_api_enabled": settings.enable_json_api
    }


def start():
    """Entry point for poetry run start"""
    parser = argparse.ArgumentParser(description="Start the FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    
    args, unknown = parser.parse_known_args()
    
    logger.info("server_starting", port=args.port, host="127.0.0.1")
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    start()

