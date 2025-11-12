import os
import psycopg2

def get_db_connection():
    """Get a database connection using DATABASE_URL from environment"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(database_url)

def simple_chunk(text, size=1200, overlap=200):
    words = text.split()
    step = max(1, size - overlap)
    return [" ".join(words[i:i+size]) for i in range(0, len(words), step)]
