from psycopg2.extras import DictCursor, Json
import psycopg2
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
def db_url_conn():
    db_url = (
        f"postgresql+psycopg2://{db_credentials['user']}:{db_credentials['password']}"
        f"@{db_credentials['host']}:{db_credentials['port']}/{db_credentials['database']}?client_encoding=utf8"
    )
    return db_url
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

def read_data_secondtable(secondtable):
    conn = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        
        cur.execute(f"SELECT name, label FROM {secondtable}")
        data = cur.fetchall()
        
        return data
        
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

def start_(tablename, secondtable=None):
    og_data = read_data(tablename=tablename)

    flat_data = [item for sublist in og_data for item in sublist]
    if secondtable is not None:
        data_data = read_data_secondtable(secondtable)

        return flat_data, data_data
    else: 
        return flat_data
    
def extract_type(product):
        match = re.search(r'\(([^()]*)\)$', product)  # Extract last parentheses content
        return match.group(1) if match else 'Unknown'