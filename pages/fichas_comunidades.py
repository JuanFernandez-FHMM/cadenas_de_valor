import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils as utils
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import branca

utils.logged_in(st.session_state)

def clean_data(tablename,secondtable):
    
    
    flat_data, second_table = utils.start_(tablename, secondtable)
    if second_table:
        secondtable_dict = dict(second_table)
    else:
        secondtable_dict = {}

    columns_to_replace = [
    'desafios', 'comunicacion', 'tipo_acompa', 'acc_int', 'persona', 'localidad',
    'donde_conex', 'tipo_conexion', 'equipo', 
    'capacitacion', 'necesita_cap', 'forma_capacitacion',
    'horario','repeat_inicio_tipo_emprendimiento', 'tipo_capacitacion', 'otro_tipo_capacitacion', 'donde_capacitacion', 'quien_cap',
]

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
        errors='ignore'
    )
    
    # Ensure all expected columns are present, even if missing in the data
    expected_columns = [
        'repeat_inicio/nombre_emprendimiento', 'repeat_inicio/tipo_emprendimiento',
        'repeat_inicio/artesania', 'repeat_inicio/productos', 'repeat_inicio/image_prod',
        'repeat_inicio/costeo', 'repeat_inicio/factura', 'repeat_inicio/client_potenciales',
        '_id', 'localidad', 'persona', 'solo_o_grupo', 'grupo', 'num_personas',
        'inf', 'asp_social_comun', 'tec_com', 'fort', '_submission_time',
        'ubi', '_geolocation', 'observaciones', 'repeat_personas',
        'nombre_persona', 'apellidos_persona', 'sexo_persona', 'edad_persona',# 'esp_trabajo', 'herramienta','maq_equipo',
    ]
    
    # Add missing columns with default NaN values
    for col in expected_columns:
        if col not in df_inicio.columns:
            df_inicio[col] = np.nan
    
    # Process 'inf' and nested 'estado_infra'
    df_inicio_exploded_inf = df_inicio.explode('inf').reset_index(drop=True)
    inf_data = pd.json_normalize(df_inicio_exploded_inf['inf'], sep='/', errors='ignore')
    
    # Ensure 'inf/estado_infra' exists in the data
    df_inicio_exploded_inf = df_inicio.explode('inf').reset_index(drop=True)
    inf_data = pd.json_normalize(df_inicio_exploded_inf['inf'], sep='/', errors='ignore')
    
    # Handle the nested estado_infra structure
    if 'inf/estado_infra' in inf_data.columns:
        # Explode the estado_infra array
        inf_data_exploded_estado = inf_data.explode('inf/estado_infra').reset_index(drop=True)
        
        # Normalize the estado_infra objects
        estado_infra = pd.json_normalize(
            inf_data_exploded_estado['inf/estado_infra'],
            errors='ignore'
        )
        
        # Rename the columns to remove the nested prefix
        estado_infra.columns = estado_infra.columns.str.replace('inf/estado_infra/', '')
        
        # Create missing columns if they don't exist
        for col in ['esp_trabajo', 'herramienta', 'maq_equipo']:
            if col not in estado_infra.columns:
                estado_infra[col] = np.nan
        
        # Combine the data
        inf_combined = pd.concat([
            inf_data_exploded_estado.drop(['inf/estado_infra', 'inf/estado_infra_count'], axis=1),
            estado_infra
        ], axis=1)
    else:
        # If estado_infra is missing, create empty columns
        inf_combined = inf_data.copy()
        for col in ['esp_trabajo', 'herramienta', 'maq_equipo']:
            inf_combined[col] = np.nan
    
    # Rest of the function remains the same...
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
    
    df_final_exploded_personas = df_final.copy()
    
    # Create a temporary DataFrame to process repeat_personas
    temp_personas = df_final.explode('repeat_personas').reset_index()
    personas_data = pd.json_normalize(temp_personas['repeat_personas'], sep='/', errors='ignore')
    personas_data.columns = personas_data.columns.str.replace('repeat_personas/', '')
    
    # Group by index to collect all persona_grupo values into lists
    grouped_personas = personas_data.groupby(temp_personas['index']).agg({
        'persona_grupo': lambda x: list(x) if not x.isna().all() else None,
        'nombre': 'first',
        'apellidos': 'first',
        'sexo': 'first',
        'edad': 'first'
    }).reset_index()
    
    # Merge back with the main DataFrame
    df_final_with_personas = pd.merge(
        df_final_exploded_personas,
        grouped_personas,
        left_index=True,
        right_on='index',
        how='left'
    ).drop('index', axis=1)
    
    # Clean column names
    df_final_with_personas.columns = df_final_with_personas.columns.str.replace('/', '_')
    
    # Convert dates and process geolocation (same as before)
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
    
    # Replace IDs with names
    #df_final_with_personas['persona'] = df_final_with_personas['persona'].map(personas_dict).fillna(df_final_with_personas['persona'])
    # Map persona_grupo names for each item in the list
    #df_final_with_personas['persona_grupo'] = df_final_with_personas['persona_grupo'].apply(
    #    lambda x: [personas_dict.get(i, i) for i in x] if isinstance(x, list) else x
    #)
    
    # Replace localidades
    #df_final_with_personas['localidad'] = df_final_with_personas['localidad'].map(localidades_dict).fillna(df_final_with_personas['localidad'])
    
    # Handle 'otro' cases for persona
    df_final_with_personas['temp_nom'] = df_final_with_personas['nombre_persona'] + " " + df_final_with_personas["apellidos_persona"]
    df_final_with_personas['temp_nom'] = df_final_with_personas['temp_nom'].str.strip()
    df_final_with_personas.loc[df_final_with_personas['persona']=="otro", "persona"] = df_final_with_personas['temp_nom']
    df_final_with_personas.drop(columns=["temp_nom"], inplace=True)

    # Handle 'otro' cases for persona_grupo list
    df_final_with_personas['temp_nom'] = df_final_with_personas['nombre'] + " " + df_final_with_personas["apellidos"]
    df_final_with_personas['temp_nom'] = df_final_with_personas['temp_nom'].str.strip()
    df_final_with_personas['persona_grupo'] = df_final_with_personas.apply(
        lambda row: [row['temp_nom'] if x == "otro" else x for x in row['persona_grupo']]
        if isinstance(row['persona_grupo'], list) else row['persona_grupo'],
        axis=1
    )
    df_final_with_personas.drop(columns=["temp_nom"], inplace=True)

    def replace_values(value):
        if isinstance(value, str):  # Ensure it's a string
            parts = value.split(" ")  # Split by spaces
            replaced_parts = [secondtable_dict.get(part, part) for part in parts]  # Replace each part
            return " ".join(replaced_parts)  # Join back with spaces
        return value  # Return unchanged if not a string

    # Apply the transformation to each column
    for col in columns_to_replace:
        df_final_with_personas[col] = df_final_with_personas[col].apply(replace_values)
    
    # Rename columns and select final columns (same as before)
    df_final_with_personas.rename(columns={
        '_submission_time': 'fecha_submision',
        'repeat_inicio_nombre_emprendimiento': 'emprendimiento',
        'repeat_inicio_tipo_emprendimiento': 'tipo_emprendimiento',
        'repeat_inicio_productos': 'productos_servicios',
        'repeat_inicio_image_prod': 'imagen_producto'
    }, inplace=True)
    
    final_cols = [
        'emprendimiento', 'tipo_emprendimiento', 'productos_servicios', 'imagen_producto',
        'localidad', 'persona', 'nombre_persona', 'apellidos_persona', 'sexo_persona', 'edad_persona',
        'solo_o_grupo', 'grupo', 'num_personas', 'persona_grupo', 'nombre', 'apellidos', 'sexo', 'edad',
        'esp_trabajo', 'herramienta', 'maq_equipo', 'acc_bas', 'acc_lu', 'emp_colab',
        'desafios', 'comunicacion', 'tipo_acompa', 'acc_int', 'donde_conex', 'tipo_conexion', 'equipo',
        'capacitacion', 'tipo_capacitacion', 'otro_tipo_capacitacion', 'donde_capacitacion', 'otro_donde_capacitacion','quien_cap', 'necesita_cap', 'enque', 'forma_capacitacion', 'horario', 'desfios_nuevos',
        'fecha_submision', 'geo_lat', 'geo_lon', 'observaciones'
    ]
    
    # Ensure all final columns exist
    for col in final_cols:
        if col not in df_final_with_personas.columns:
            df_final_with_personas[col] = np.nan
    
    return df_final_with_personas[final_cols].copy()


st.set_page_config(page_title="Mapa de fichas de Emprendimientos Comunitarios Naat-Ha", page_icon="data/favicon.ico", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
<style>
    [data-testid="stSidebarNavItems"] {
        display: none
    }

    [data-testid="stSidebarNavSeparator"]{
    display:none}
</style>
""",
    unsafe_allow_html=True,
)



if st.button("Página principal"):
    st.switch_page("pagina_principal.py")
if st.button("Emprendimiento Comunidades NaatHa"):
    st.switch_page("pages/emprendimientos_comunitarios.py")

def get_data():
    df = clean_data("mapeo_emprend_comunitarios_naatha","mapeo_emprend_naatha_data")
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
        'solo_o_grupo': "¿Trabaja en grupo?",
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
        'tipo_capacitacion': "¿Qué tipo de capacitación recibió?",
        'otro_tipo_capacitacion':"¿Qué otro tipo de capacitación?",
        'donde_capacitacion': "¿Dónde recibió la capacitación?", 
        'otro_donde_capacitacion': "¿En qué otro lugar recibió la capacitación?",
        'quien_cap':"¿Quién otorgó la capacitación?",
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
        pre_selected_rows=[],
        selection_mode="multiple",
        use_checkbox=True,
        header_checkbox=True,
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
    selected_rows = grid_response['selected_rows']
    selected_df = pd.DataFrame(selected_rows)
    return selected_df

selected_df = get_data()

if not selected_df.empty:
    try:
        geo_df = selected_df.dropna(subset=['geo_lat', 'geo_lon'])

        # Calculate the center of the points
        map_center = [geo_df['geo_lat'].mean(), geo_df['geo_lon'].mean()]

        # Create Folium map
        m = folium.Map(location=map_center, zoom_start=16)

        for _, row in geo_df.iterrows():
            filtered_geo = geo_df[geo_df['emprendimiento'] == row['emprendimiento']]
            # Create a scrollable HTML table for the popup
            filtered_geo = filtered_geo.drop(columns=['imagen_producto','localidad', 'nombre_persona', 'apellidos_persona', 'sexo_persona', 'edad_persona', 'persona_grupo','nombre','apellidos','sexo','edad','esp_trabajo','herramienta','maq_equipo','acc_bas', 'acc_lu', 'emp_colab', 'desafios', 'tipo_acompa', 'capacitacion', 'tipo_capacitacion', 'otro_tipo_capacitacion', 'donde_capacitacion', 'otro_donde_capacitacion', 'quien_cap', 'necesita_cap', 'enque', 'forma_capacitacion', 'horario','desfios_nuevos', 'fecha_submision', 'geo_lat', 'geo_lon'])
            html_table = filtered_geo.to_html(
                classes="table table-striped table-hover table-condensed table-responsive",
                index=False
            )
            
            # Wrap the table in a scrollable div for better mobile experience
            scrollable_html = f"""
            <div style="overflow-x: auto; max-width: 300px; max-height: 400px;">
                {html_table}
            </div>
            """
            
            # Create an iframe with the scrollable table
            iframe = branca.element.IFrame(html=scrollable_html, width=320, height=420)
            
            # Create a folium Popup with the iframe
            popup = folium.Popup(iframe, max_width=500)
            
            # Add marker with popup & tooltip
            folium.Marker(
                location=[row['geo_lat'], row['geo_lon']],
                popup=popup,  # Show scrollable table on click
                tooltip=row['emprendimiento']  # Show name on hover
            ).add_to(m)

        # Add points with popups
        

        folium_static(m, width=1400, height=700)
        
        m.save("mapa_fichas.html")
        with open("mapa_fichas.html", "rb") as file:
            st.download_button(label="Descargar mapa", data=file, file_name="mapa_fichas.html", mime="text/html")
    except:
        st.write("Selecciona otros datos, hubo un error con los seleccionados.\nDe ser posible, comparte la selección que causa problemas con el administrador de la página.")