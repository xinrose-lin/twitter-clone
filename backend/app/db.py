import os
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

pool = ConnectionPool(
    conninfo=os.environ["DATABASE_URL"], 
    kwargs={"row_factory": dict_row},
    open=False,
)