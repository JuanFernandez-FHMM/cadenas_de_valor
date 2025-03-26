from streamlit import secrets, warning, switch_page, stop
from psycopg2.extras import DictCursor
import psycopg2
import time
import re


# Leer las credenciales de supabase (es un servidor de Postgres así que la conexión funciona aunque no sea supabase)
# Toda la información la puedes encontrar en Supabase https://supabase.com/docs/reference/python/ 
# Hay una forma más directa de conectarse al servidor por medio de la libreria supabase en python
# Es preferible usar ese tipo de conexión, sin embargo, en el comienzo del desarrollo se utilizaron otros métodos como esta conexión directa al servido de postgres
# La conexión con este método hace que se llame la función connect_to_db() varias veces, siendo menos óptima.
db_credentials = {
    "host": secrets["database"]["host"],
    "port": secrets["database"]["port"],
    "database": secrets["database"]["database"],
    "user": secrets["database"]["user"],
    "password": secrets["database"]["password"],
    "cursor_factory": DictCursor
}
# Función para conectarse a la base de datos
def connect_to_db():
    conn = psycopg2.connect(**db_credentials)
    return conn

# Lee las tablas que contienen los jsons de las respuestas de los formularios sin limpiar, esas tablas tienen una estructura de id, timestamp, data. siendo data un json object
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

# Esta funcion lee una tabla específica en calidad de maíz con un formato diferente, viene de la anterior base de datos (en Google Sheets)
def read_data_1(tablename):
    conn = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        
        cur.execute(f"SELECT productor,variedad, venta FROM \"{tablename}\"")
        data = cur.fetchall()
        
        return data
        
    except Exception as e:
        print(f"Database error: {e}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()

# Función para leer los datos de las tablas secundarias de los formularios, estas tablas contienen id, name, label. siendo name y label dos columnas con las 'choices' dentro de los formularios 
# sirve para cambiar las respuestas donde se guardó su name, por el label
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

# Función para leer la información de las dos tablas, la principal y su secundaria, que puede ser None en ciertos casos
def start_(tablename, secondtable=None):
    og_data = read_data(tablename=tablename)

    flat_data = [item for sublist in og_data for item in sublist]
    if secondtable is not None:
        data_data = read_data_helper_table(secondtable)

        return flat_data, data_data
    else: 
        return flat_data

# Función para extraer los tipos de productos (kg, pieza, atado, etc) de una lista de valores
def extract_type(product):
        match = re.search(r'\(([^()]*)\)$', product)  # Extract last parentheses content
        return match.group(1) if match else 'Unknown'

# Función que bloquea acceso a cualquier panel si no se ha iniciado sesión
def logged_in(session_state):
    if 'logged_in' not in session_state or not session_state.logged_in:
        warning("Debe iniciar sesión para acceder a esta página.\nRedireccionando...")
        time.sleep(3)
        switch_page("pagina_principal.py")  # Adjust the main page filename if needed
        stop()

    return 