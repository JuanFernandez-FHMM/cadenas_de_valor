from flask import Flask, request, jsonify
from psycopg2.extras import DictCursor, Json
import psycopg2
import logging
import time
import toml


logging.basicConfig(level=logging.INFO)

def connect_to_db():
    conn = psycopg2.connect(**db_credentials, cursor_factory=DictCursor)
    return conn

def handle_webhook(tablename):
    
    data = request.get_json(silent=True) or {}

    try:
        with connect_to_db() as conn, conn.cursor() as cur:
            cur.execute(f"INSERT INTO \"{tablename}\" (data) VALUES (%s)", (Json(data),))
            conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def store_milpa_transactions():
    data = request.get_json(silent=True) or {}
    tablename = "transacciones_milpa_traspatiomaya"
    
    try:
        productor = data.get("productor")
        variedades = data.get("variedad_repeat", [])
        
        transactions = []
        for variedad in variedades:
            variedad_name = variedad.get("variedad_repeat/current_variedad")
            bolsas_cantidad = int(variedad.get("variedad_repeat/bolsas_cantidad", 0))
            cantidad_kg = bolsas_cantidad * 25
            transactions.append((productor, variedad_name, cantidad_kg))
        
        if transactions:
            with connect_to_db() as conn, conn.cursor() as cur:
                cur.executemany(
                    f"INSERT INTO \"{tablename}\" (productor, variedad, cantidad) VALUES (%s, %s, %s)",
                    transactions
                )
                conn.commit()
                print("Sent to DB", time.time())
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


config = toml.load('.streamlit/secrets.toml')
db_credentials = config['database']


allowed_tables = {
    "preregistro-becas-integrales-FHMMIU": "preregistro_becas_integrales_FHMMIU",
    "compra-maiz-traspatiomaya": "compra_maiz_traspatiomaya",
    "seguimiento-produccion-agrodiversos-2025": "seguimiento_prod_agrodiversos_2025",
    "mapeo-produccion-pujol": "mapeo_prod_pujol",
    "muestreo-calidad-maiz": "muestreo_calidad_maiz",
    "meliponicultura-comercializacion-2025": "meliponicultura_comercializacion_2025",
    "mapeo-emprendimientos-comunitarios-naatha": "mapeo_emprend_comunitarios_naatha",
    "convocatoria-comite-comunitario-2025": "convocatoria_comite_comunitario_2025",
    "lista-asistencia-naatha":"lista_asistencia_naatha",
    "registro-de-actualizaciones-de-produccion-de-maiz": "registro_actualizaciones_produccion_maiz",
}


app = Flask(__name__)

@app.route('/<path:route>', methods=['POST'])
def webhook_handler(route):
    if route in allowed_tables:
        if route == 'compra-maiz-traspatiomaya':
            #data = request.get_json(silent=True)
            store_milpa_transactions()
        return handle_webhook(allowed_tables[route])
    return jsonify({"status": "error", "message": "Invalid webhook route"}), 400


if __name__ == '__main__':
    app.run(port=5000)
    