import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils as utils
import pandas as pd
import numpy as np


import pandas as pd

import pandas as pd
import numpy as np

def clean_data(tablename, personas_csv_path):
    # Load the CSV file that maps IDs to names
    personas_df = pd.read_csv(personas_csv_path)
    # Convert the CSV into a dictionary for quick lookup
    localidades_df = pd.read_csv("data\\localidades.csv")
    personas_dict = dict(zip(personas_df['id'], personas_df['name']))
    localidades_dict = dict(zip(localidades_df['id'], localidades_df['name']))
    
    flat_data = utils.start_(tablename)
    
    # Normalize the main repeat_inicio entries
    df_inicio = pd.json_normalize(
        flat_data,
        record_path='repeat_inicio',
        meta=[
            '_id', 'localidad', 'persona', 'solo_o_grupo', 'grupo', 'num_personas',
            'inf', 'asp_social_comun', 'tec_com', 'fort', '_submission_time',
            'ubi', '_geolocation', 'observaciones', 'repeat_personas',
            'nombre_persona', 'apellidos_persona', 'sexo_persona', 'edad_persona'
        ],
        sep='/',
        errors='ignore'  # Skip missing keys instead of raising an error
    )
    
    # Ensure all expected columns are present, even if missing in the data
    expected_columns = [
        'repeat_inicio/nombre_emprendimiento', 'repeat_inicio/tipo_emprendimiento',
        'repeat_inicio/artesania', 'repeat_inicio/productos', 'repeat_inicio/image_prod',
        'repeat_inicio/costeo', 'repeat_inicio/factura', 'repeat_inicio/client_potenciales',
        '_id', 'localidad', 'persona', 'solo_o_grupo', 'grupo', 'num_personas',
        'inf', 'asp_social_comun', 'tec_com', 'fort', '_submission_time',
        'ubi', '_geolocation', 'observaciones', 'repeat_personas',
        'nombre_persona', 'apellidos_persona', 'sexo_persona', 'edad_persona'
    ]
    
    # Add missing columns with default NaN values
    for col in expected_columns:
        if col not in df_inicio.columns:
            df_inicio[col] = np.nan
    
    # Process 'inf' and nested 'estado_infra'
    df_inicio_exploded_inf = df_inicio.explode('inf').reset_index(drop=True)
    inf_data = pd.json_normalize(df_inicio_exploded_inf['inf'], sep='/', errors='ignore')
    
    # Ensure 'inf/estado_infra' exists in the data
    if 'inf/estado_infra' in inf_data.columns:
        inf_data_exploded_estado = inf_data.explode('inf/estado_infra').reset_index(drop=True)
        estado_infra = pd.json_normalize(inf_data_exploded_estado['inf/estado_infra'], sep='/', errors='ignore')
        
        # Ensure 'esp_trabajo', 'herramienta', and 'maq_equipo' exist in estado_infra
        for col in ['esp_trabajo', 'herramienta', 'maq_equipo']:
            if col not in estado_infra.columns:
                estado_infra[col] = np.nan
        
        inf_combined = pd.concat([
            inf_data_exploded_estado.drop(['inf/estado_infra', 'inf/estado_infra_count'], axis=1),
            estado_infra
        ], axis=1)
    else:
        # If 'inf/estado_infra' is missing, create empty columns for 'esp_trabajo', 'herramienta', and 'maq_equipo'
        inf_combined = inf_data.copy()
        for col in ['esp_trabajo', 'herramienta', 'maq_equipo']:
            inf_combined[col] = np.nan
    
    inf_combined.columns = inf_combined.columns.str.replace('inf/', '')
    df_inicio_with_inf = pd.concat([
        df_inicio_exploded_inf.drop('inf', axis=1).reset_index(drop=True),
        inf_combined
    ], axis=1)
    
    # Process 'asp_social_comun'
    df_inicio_with_inf_exploded_asp = df_inicio_with_inf.explode('asp_social_comun').reset_index(drop=True)
    asp_data = pd.json_normalize(df_inicio_with_inf_exploded_asp['asp_social_comun'], sep='/', errors='ignore')
    asp_data.columns = asp_data.columns.str.replace('asp_social_comun/', '')
    df_inicio_with_inf_asp = pd.concat([
        df_inicio_with_inf_exploded_asp.drop('asp_social_comun', axis=1),
        asp_data
    ], axis=1)
    
    # Process 'tec_com'
    df_inicio_with_inf_asp_exploded_tec = df_inicio_with_inf_asp.explode('tec_com').reset_index(drop=True)
    tec_data = pd.json_normalize(df_inicio_with_inf_asp_exploded_tec['tec_com'], sep='/', errors='ignore')
    tec_data.columns = tec_data.columns.str.replace('tec_com/', '')
    df_inicio_with_inf_asp_tec = pd.concat([
        df_inicio_with_inf_asp_exploded_tec.drop('tec_com', axis=1),
        tec_data
    ], axis=1)
    
    # Process 'fort'
    df_inicio_with_inf_asp_tec_exploded_fort = df_inicio_with_inf_asp_tec.explode('fort').reset_index(drop=True)
    fort_data = pd.json_normalize(df_inicio_with_inf_asp_tec_exploded_fort['fort'], sep='/', errors='ignore')
    fort_data.columns = fort_data.columns.str.replace('fort/', '')
    df_final = pd.concat([
        df_inicio_with_inf_asp_tec_exploded_fort.drop('fort', axis=1),
        fort_data
    ], axis=1)
    
    # Process 'repeat_personas'
    df_final_exploded_personas = df_final.explode('repeat_personas').reset_index(drop=True)
    personas_data = pd.json_normalize(df_final_exploded_personas['repeat_personas'], sep='/', errors='ignore')
    personas_data.columns = personas_data.columns.str.replace('repeat_personas/', '')
    df_final_with_personas = pd.concat([
        df_final_exploded_personas.drop('repeat_personas', axis=1),
        personas_data
    ], axis=1)
    
    # Clean column names
    df_final_with_personas.columns = df_final_with_personas.columns.str.replace('/', '_')
    
    # Convert dates
    df_final_with_personas['_submission_time'] = pd.to_datetime(df_final_with_personas['_submission_time'])
    
    # Split geolocation
    ubi_split = df_final_with_personas['ubi'].str.split(' ', expand=True)
    df_final_with_personas['geo_lat'] = pd.to_numeric(ubi_split[0], errors='coerce')
    df_final_with_personas['geo_lon'] = pd.to_numeric(ubi_split[1], errors='coerce')
    df_final_with_personas['geo_alt'] = pd.to_numeric(ubi_split[2], errors='coerce')
    df_final_with_personas['geo_acc'] = pd.to_numeric(ubi_split[3], errors='coerce')
    
    # Extract coordinates from _geolocation
    df_final_with_personas['_geolocation_lat'] = df_final_with_personas['_geolocation'].apply(
        lambda x: x[0] if isinstance(x, list) and len(x) >= 2 else None
    )
    df_final_with_personas['_geolocation_lon'] = df_final_with_personas['_geolocation'].apply(
        lambda x: x[1] if isinstance(x, list) and len(x) >= 2 else None
    )
    
    # Convert numeric columns
    numeric_cols = ['edad_persona', 'num_personas', 'edad']
    for col in numeric_cols:
        df_final_with_personas[col] = pd.to_numeric(df_final_with_personas[col], errors='coerce')
    
    # Replace IDs with names from the CSV file
    df_final_with_personas['persona'] = df_final_with_personas['persona'].map(personas_dict).fillna(df_final_with_personas['persona'])
    df_final_with_personas['persona_grupo'] = df_final_with_personas['persona_grupo'].map(personas_dict).fillna(df_final_with_personas['persona_grupo'])
    
    # replace localidades
    df_final_with_personas['localidad'] = df_final_with_personas['localidad'].map(localidades_dict).fillna(df_final_with_personas['localidad'])
    df_final_with_personas['temp_nom'] = df_final_with_personas['nombre_persona'] + " " + df_final_with_personas["apellidos_persona"]
    df_final_with_personas['temp_nom'] = df_final_with_personas['temp_nom'].str.strip()
    df_final_with_personas.loc[df_final_with_personas['persona']=="otro", "persona"] = df_final_with_personas['temp_nom']
    df_final_with_personas.drop(columns=["temp_nom"], inplace=True)

    df_final_with_personas['temp_nom'] = df_final_with_personas['nombre'] + " " + df_final_with_personas["apellidos"]
    df_final_with_personas['temp_nom'] = df_final_with_personas['temp_nom'].str.strip()
    df_final_with_personas.loc[df_final_with_personas['persona_grupo']=="otro", "persona_grupo"] = df_final_with_personas['temp_nom']
    df_final_with_personas.drop(columns=["temp_nom"], inplace=True)
    # Select and rename key columns
    df_final_with_personas.rename(columns={
        '_submission_time': 'fecha_submision',
        'repeat_inicio_nombre_emprendimiento': 'emprendimiento',
        'repeat_inicio_tipo_emprendimiento': 'tipo_emprendimiento',
        'repeat_inicio_productos': 'productos_servicios',
        'repeat_inicio_image_prod': 'imagen_producto'
    }, inplace=True)
    
    # Final column selection (adjust based on needs)
    final_cols = [
        'emprendimiento', 'tipo_emprendimiento', 'productos_servicios', 'imagen_producto',
        'localidad', 'persona', 'nombre_persona', 'apellidos_persona', 'sexo_persona', 'edad_persona',
        'solo_o_grupo', 'grupo', 'num_personas', 'persona_grupo', 'nombre', 'apellidos', 'sexo', 'edad',
        'esp_trabajo', 'herramienta', 'maq_equipo', 'acc_bas', 'acc_lu', 'emp_colab',
        'desafios', 'comunicacion', 'tipo_acompa', 'acc_int', 'donde_conex', 'tipo_conexion', 'equipo',
        'capacitacion', 'necesita_cap', 'enque', 'forma_capacitacion', 'horario', 'desfios_nuevos',
        'fecha_submision', 'geo_lat', 'geo_lon', 'observaciones'
    ]
    
    # Ensure all final columns exist in the DataFrame
    for col in final_cols:
        if col not in df_final_with_personas.columns:
            df_final_with_personas[col] = np.nan
    
    # Filter and return
    return df_final_with_personas[final_cols].copy()


st.set_page_config(page_title="Emprendimientos Comunitarios Naat-Ha", page_icon=":earth_americas:", layout="wide", initial_sidebar_state="collapsed")

st.title("Mapeo de emprendimientos comunitarios Naat-Ha :earth_americas:")
if st.button("Página principal"):
    st.switch_page("pagina_principal.py")


df = clean_data("mapeo_emprend_comunitarios_naatha","data\\personas.csv")
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(
    groupable=True,
    value=True,
    enableRowGroup=True,
    aggFunc='sum',
    filter='agTextColumnFilter'
)

# Updated columns dictionary
columns = {
    'emprendimiento': "Nombre del emprendimiento",
    'tipo_emprendimiento': "Tipo de emprendimiento",
    'productos_servicios': "Productos o servicios ofrecidos",
    'imagen_producto': "Imagen del producto",
    'localidad': "Localidad",
    'persona': "Persona encuestada",
    'nombre_persona': "Nombre de la persona",
    'apellidos_persona': "Apellidos de la persona",
    'sexo_persona': "Sexo de la persona",
    'edad_persona': "Edad de la persona",
    'solo_o_grupo': "¿Trabaja solo o en grupo?",
    'grupo': "Nombre del grupo",
    'num_personas': "Número de personas en el grupo",
    'persona_grupo': "Miembro del grupo",
    'nombre': "Nombre del miembro (si no está registrado)",
    'apellidos': "Apellidos del miembro (si no está registrado)",
    'sexo': "Sexo del miembro (si no está registrado)",
    'edad': "Edad del miembro (si no está registrado)",
    'esp_trabajo': "Estado del espacio de trabajo",
    'herramienta': "Estado de las herramientas",
    'maq_equipo': "Estado de la maquinaria y equipo",
    'acc_bas': "Acceso a servicio de agua",
    'acc_lu': "Acceso a servicio de luz",
    'emp_colab': "¿Cuenta con empleados?",
    'desafios': "Desafíos empresariales",
    'comunicacion': "Formas de promoción",
    'tipo_acompa': "Tipo de acompañamiento necesario",
    'acc_int': "Acceso a internet",
    'donde_conex': "Lugar de conexión a internet",
    'tipo_conexion': "Tipo de conexión a internet",
    'equipo': "Equipo utilizado para internet",
    'capacitacion': "¿Ha recibido capacitación?",
    'necesita_cap': "¿Necesita capacitación?",
    'enque': "¿En qué necesita capacitación?",
    'forma_capacitacion': "Forma preferida de capacitación",
    'horario': "Horario preferido para capacitación",
    'desfios_nuevos': "Desafíos al participar en el programa",
    'fecha_submision': "Fecha de envío del formulario",
    'geo_lat': "Latitud",
    'geo_lon': "Longitud",
    'observaciones': "Observaciones"
}

# Configure columns with Spanish headers
for col, header in columns.items():
    gb.configure_column(col, header_name=header)

# Configure selection and side bar
gb.configure_selection(
    selection_mode="multiple",
    use_checkbox=True,
    pre_selected_rows=[],
    suppressRowDeselection=False
)
gb.configure_side_bar(filters_panel=True, defaultToolPanel='filters')
grid_options = gb.build()

# Display the AgGrid
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    height=800,
    width='100%',
    allow_unsafe_jscode=True,
    update_mode='SELECTION_CHANGED'
)

# Extract selected rows
selected_rows = grid_response['selected_rows']
selected_df = pd.DataFrame(selected_rows)

if not selected_df.empty:
    st.subheader("Filas Seleccionadas")
    st.dataframe(selected_df[list(columns.keys())])
    
#    total_cosecha = selected_df['cantidad_cosecha'].sum()
#    total_comercio = selected_df['cantidad_comercializar'].sum()
#    st.write(f"Total Cosecha: {total_cosecha} \t|\t Total Comercializar: {total_comercio}")
    
    csv = selected_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Descargar",
        csv,
        "selected_data.csv",
        "text/csv",
        key='download-selected'
    )
else:
    st.write("No hay filas seleccionadas")

