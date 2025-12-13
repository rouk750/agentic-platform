import sqlite3

def migrate():
    # This migration is handled automatically by SQLModel.metadata.create_all(engine) 
    # in the lifespan function of main.py because these are new tables.
    # We only need explicit migration if we are modifying EXISTING tables.
    # Since AgentTemplate and AgentTemplateVersion are new, create_all will create them.
    # However, to be safe and verify, we can run this.
    try:
        from app.database import engine
        from sqlmodel import SQLModel
        # Import models to register them
        from app.models import agent_template
        
        print("Creating new tables for Agent Templates...")
        SQLModel.metadata.create_all(engine)
        print("Tables created successfully (if they didn't exist).")
        
    except Exception as e:
        print(f"Migration failed or tables already exist: {e}")

if __name__ == "__main__":
    migrate()
