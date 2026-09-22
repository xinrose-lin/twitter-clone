import os

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"],
    kwargs={"row_factory": dict_row},
    min_size=4,
    max_size=20,
    open=False,
)