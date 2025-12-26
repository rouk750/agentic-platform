from sqlmodel import SQLModel, create_engine, Session
import os
from sqlalchemy import event
from app.config import settings

# Get absolute path to the backend directory (parent of app)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Use database_url from settings for flexibility
# If it's a relative path starting with sqlite:///, make it absolute relative to BASE_DIR
# This handles the default "sqlite:///./database.db" correctly
db_url = settings.database_url
if db_url.startswith("sqlite:///./"):
    sqlite_file_name = os.path.join(BASE_DIR, db_url.replace("sqlite:///./", ""))
    sqlite_url = f"sqlite:///{sqlite_file_name}"
else:
    sqlite_url = db_url

connect_args = {"check_same_thread": False}

# Create engine with pooling configuration
engine = create_engine(
    sqlite_url,
    connect_args=connect_args,
    # SQLite often uses SingletonThreadPool or NullPool by default,
    # but for consistent behavior we configure these.
    # Note: pool_size/max_overflow might be ignored by default SQLite pool
    # unless we explicitly use QueuePool, but QueuePool + SQLite file can cause locking.
    # We stick to default pool behavior for SQLite but add recycle/pre_ping.
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    # echo=settings.log_level == "DEBUG"
)

# Enable WAL mode for SQLite for better concurrency
if "sqlite" in sqlite_url:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

def get_session():
    with Session(engine) as session:
        yield session
