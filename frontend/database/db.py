import os
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    # psycopg 3 uses psycopg.connect
    return psycopg.connect(DATABASE_URL)
