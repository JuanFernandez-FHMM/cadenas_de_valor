from psycopg2.extras import DictCursor, Json
import psycopg2
import re
from streamlit import secrets


# Read database credentials for Streamlit
db_credentials = {
    "host": secrets["database"]["host"],
    "port": secrets["database"]["port"],
    "database": secrets["database"]["database"],
    "user": secrets["database"]["user"],
    "password": secrets["database"]["password"],
    "cursor_factory": DictCursor  
}

# Function to tranform the database credentials into a url to connect
def db_url_conn():
    db_url = (
        f"postgresql+psycopg2://{db_credentials['user']}:{db_credentials['password']}"
        f"@{db_credentials['host']}:{db_credentials['port']}/{db_credentials['database']}?client_encoding=utf8"
    )
    return db_url

# Function to connect to the database with credentials
def connect_to_db():
    conn = psycopg2.connect(**db_credentials)
    return conn

# Function to run SELECT * from a specified table
def read_data(tablename):
    conn = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        
        cur.execute(f"SELECT data FROM \"{tablename}\"")
        data = cur.fetchall()
        
        return data
        
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()


# Function to read data from secondary table (Structure is always name | label)
def read_data_helper_table(secondtable):
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

# Read data from both tables
def start_(tablename, secondtable=None):
    og_data = read_data(tablename=tablename)

    flat_data = [item for sublist in og_data for item in sublist]
    if secondtable is not None:
        data_data = read_data_helper_table(secondtable)

        return flat_data, data_data
    else: 
        return flat_data

# Function to get product type (specific for the ones including kg or pza etc)
def extract_type(product):
        match = re.search(r'\(([^()]*)\)$', product)  # Extract last parentheses content
        return match.group(1) if match else 'Unknown'
        