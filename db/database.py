from pathlib import Path
import sqlite3

# --- DB path define ---
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "entries.db"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Return a SQLite connection"""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create entries table if it doesn't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        journal TEXT,
        intention TEXT,
        dream TEXT,
        priorities TEXT,
        reflection TEXT,
        strategy TEXT,
        dream_summary TEXT,
        mindset TEXT
    )
    """)
    conn.commit()
    conn.close()


def save_entry(date, journal, intention, dream, priorities, reflection, strategy, dream_summary="", mindset=""):
    """Save a new entry in the DB"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entries (date, journal, intention, dream, priorities, reflection, strategy, dream_summary, mindset)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date, journal, intention, dream, priorities, reflection, strategy, dream_summary, mindset))
    conn.commit()
    conn.close()


def get_entry_by_date(date):
    """Fetch entries by a specific date"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries WHERE date = ?", (date,))
    rows = cursor.fetchall()
    conn.close()
    return rows
