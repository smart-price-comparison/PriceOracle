# filename: db_utils_sqlite.py
import sqlite3
from contextlib import closing

DB_PATH = "priceoracle.db"

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price TEXT,
            url TEXT,
            image TEXT,
            source TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def insert_product(name, price, url, image, source="amazon"):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO products (name, price, url, image, source) VALUES (?, ?, ?, ?, ?)",
            (name, price, url, image, source)
        )
        conn.commit()

def fetch_recent(limit=10):
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, price, url, image, scraped_at FROM products ORDER BY scraped_at DESC LIMIT ?", (limit,))
        return c.fetchall()

if __name__ == "__main__":
    init_db()
    print("DB initialized at", DB_PATH)
