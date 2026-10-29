import os
import psycopg

from pathlib import Path
from dotenv import load_dotenv
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def connect():
    return psycopg.connect(os.getenv("DATABASE_URL"), row_factory=dict_row)
