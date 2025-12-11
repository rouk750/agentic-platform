try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
except ImportError:
    # Fallback or debug
    try:
        from langgraph_checkpoint_sqlite.aio import AsyncSqliteSaver
    except ImportError:
         raise ImportError("Could not import AsyncSqliteSaver. Please ensure langgraph-checkpoint-sqlite is installed.")

# Singleton or factory for checkpointer
# We use a separate DB file for checkpoints to avoid locking issues with main DB, 
# or we can use the same matching the setup. Start with separate to be safe/simple.
CHECKPOINT_DB = "checkpoints.sqlite"

async def get_graph_checkpointer():
    # Return a new context manager for each request
    return AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB)
