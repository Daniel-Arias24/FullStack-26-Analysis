import sqlite3

DB_PATH = "esprit.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor  TEXT NOT NULL,
            fecha     TEXT NOT NULL,
            local     TEXT,
            producto  TEXT NOT NULL,
            canal     TEXT NOT NULL DEFAULT 'fisica',
            costo     REAL NOT NULL,
            creado_en TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()