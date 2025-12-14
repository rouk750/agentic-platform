import argparse
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.database import engine
from app.api import settings
from app.api import run
from app.api import tools
from app.api import flows
from app.api import smart_nodes
from app.api import guardrails
from app.api import agent_templates

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load all models so that SQLModel knows about them
    from app.models import settings as settings_model
    from app.models import flow as flow_model
    from app.models import agent_template as agent_template_model
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(title="AgentArchitect API", lifespan=lifespan)

# CORS Configuration
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(run.router, prefix="/api", tags=["run"])
app.include_router(tools.router, prefix="/api", tags=["tools"])
app.include_router(flows.router, prefix="/api", tags=["flows"])
app.include_router(smart_nodes.router, prefix="/api", tags=["smart-nodes"])
app.include_router(guardrails.router, prefix="/api", tags=["guardrails"])
app.include_router(agent_templates.router, prefix="/api", tags=["agent-templates"])

@app.get("/")
def read_root():
    return {"Hello": "World", "version": "0.1.0"}

def start():
    """Entry point for poetry run start"""
    parser = argparse.ArgumentParser(description="Start the FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    
    # Parse args. Note: when running via poetry run start, args are passed.
    # We use parse_known_args to avoid issues if other args are passed, though not expected.
    args, unknown = parser.parse_known_args()
    
    print(f"Starting server on port {args.port}")
    uvicorn.run(app, host="127.0.0.1", port=args.port)

if __name__ == "__main__":
    start()
