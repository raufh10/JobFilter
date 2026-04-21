import sqlite3
from pathlib import Path

DB_PATH = Path("data/cli/data.db")

def get_connection():
  """Provides a connection to the SQLite database."""
  DB_PATH.parent.mkdir(parents=True, exist_ok=True)
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn

def init_db():
  """Initialize the tables if it doesn't exist."""
  with get_connection() as conn:
    conn.execute("""
      CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        site_name TEXT NOT NULL,
        search_term TEXT NOT NULL,
        location TEXT NOT NULL,
        results_wanted INTEGER NOT NULL,
        hours_old INTEGER,
        country_indeed TEXT NOT NULL,
        remote_only BOOLEAN NOT NULL,
        strictness TEXT NOT NULL
      )
    """)

    conn.execute("""
      CREATE TABLE IF NOT EXISTS jobs (
        job_url TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        score INTEGER,
        explanation TEXT,
        matched_skills TEXT,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    """)

