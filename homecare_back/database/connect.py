import psycopg
import os
from psycopg.rows import dict_row

def connect():
    connection = psycopg.connect(
        os.getenv("DATABASE_URL"),
        row_factory = dict_row
    )

    return connection
