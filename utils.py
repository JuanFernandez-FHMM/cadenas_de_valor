from psycopg2.extras import DictCursor, Json
import psycopg2
import pandas as pd
import re
from streamlit import secrets


db_credentials = {
    "host": secrets["database"]["host"],
    "port": secrets["database"]["port"],
    "database": secrets["database"]["database"],
    "user": secrets["database"]["user"],
    "password": secrets["database"]["password"],
    "cursor_factory": DictCursor  # Keep this directly in the script
}

def connect_to_db():
    conn = psycopg2.connect(**db_credentials)
    return conn

def read_data(tablename):
    conn = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        
        cur.execute(f"SELECT data FROM {tablename}")
        data = cur.fetchall()
        
        return data
        
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()


def start_(tablename):
    og_data = read_data(tablename=tablename)

    flat_data = [item for sublist in og_data for item in sublist]

    return flat_data

def extract_type(product):
        match = re.search(r'\(([^()]*)\)$', product)  # Extract last parentheses content
        return match.group(1) if match else 'Unknown'