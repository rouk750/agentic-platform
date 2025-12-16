from sqlmodel import text, create_engine
import os

# Adjust path to find database.db in backend root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sqlite_file_name = os.path.join(BASE_DIR, "database.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

def migrate():
    print(f"Migrating database at {sqlite_file_name}...")
    with engine.connect() as connection:
        # Check FlowVersion
        try:
            connection.execute(text("ALTER TABLE flowversion ADD COLUMN is_locked BOOLEAN DEFAULT 0"))
            print("Added is_locked to flowversion")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("is_locked already exists in flowversion")
            else:
                print(f"Error updating flowversion: {e}")

        # Check AgentTemplateVersion
        try:
            connection.execute(text("ALTER TABLE agenttemplateversion ADD COLUMN is_locked BOOLEAN DEFAULT 0"))
            print("Added is_locked to agenttemplateversion")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("is_locked already exists in agenttemplateversion")
            else:
                print(f"Error updating agenttemplateversion: {e}")
        
        connection.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
