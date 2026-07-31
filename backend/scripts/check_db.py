# scripts/check_db.py
from dotenv import load_dotenv

load_dotenv()

from app.db import pool

pool.open()

# connection pool is like a cache of db connections
# context manager - auto close the connection after code ends this cnotext
# allow capture release (cheaper than open/close)
with pool.connection() as conn:
    # executes query
    with conn.cursor() as cur:
        cur.execute("SELECT 1 AS ok")
        print(cur.fetchone())

pool.close()
