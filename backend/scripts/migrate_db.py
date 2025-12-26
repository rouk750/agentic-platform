import sqlite3

def migrate():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE flow ADD COLUMN is_archived BOOLEAN DEFAULT 0")
        conn.commit()
        print("Migration successful: Added is_archived column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column is_archived already exists.")
        else:
            print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
