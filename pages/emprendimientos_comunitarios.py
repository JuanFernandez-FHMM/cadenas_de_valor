import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils as utils
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import folium_static


######################################################
### SPECIFIC CLEANNING DATA FUNCTION FOR EACH PAGE ###
######################################################

def clean_data(tablename,secondtable):
    
    # Read data using utils
    flat_data, second_table = utils.start_(tablename, secondtable)

    # create table for second dict only if exists
    if second_table:
        secondtable_dict = dict(second_table)
    else:
        secondtable_dict = {}

    # columns with values to be replaced with second table
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

def plot_tipo1(dataset,columna,titulo, textposition='auto'):
        plot = px.pie(dataset, names=columna, title=titulo)
        plot.update_traces(
            textposition=textposition,
            textinfo='percent+label+value',
            hole=0.3,
            marker=dict(line=dict(color='#000000', width=2))
            )
        return plot

def plot_tipo2(dataframe,lista_categorias, columna,titulo, textposition='auto'):
    df_temp = dataframe[columna]
    df = []

    for i in df_temp:
        found_categories = []
        for categoria in lista_categorias:
            if categoria.lower() in str(i).lower():  
                found_categories.append(categoria)
        df.append(found_categories)
    df = pd.DataFrame({'categorias': [cat for cats in df for cat in (cats if cats else [None])]})

    plot = px.pie(df, names="categorias", title=titulo)
    plot.update_traces(
        textposition=textposition,
        textinfo='percent+label+value',
        hole=0.3,
        marker=dict(line=dict(color='#000000', width=2))
    )

    return plot

st.set_page_config(page_title="Emprendimientos Comunitarios Naat-Ha", page_icon=":earth_americas:", layout="wide", initial_sidebar_state="collapsed")

st.title("Mapeo de emprendimientos comunitarios Naat-Ha :earth_americas:")

if st.button("Página principal"):
    st.switch_page("pagina_principal.py")

if st.button("Mapa de fichas"):
    st.switch_page("pages/fichas_comunidades.py")

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

if not selected_df.empty:
    geo_df = selected_df.dropna(subset=['geo_lat', 'geo_lon'])
    map_center = [geo_df['geo_lat'].mean(), geo_df['geo_lon'].mean()]
    m = folium.Map(location=map_center, zoom_start=12, tiles="OpenStreetMap")

    for _, row in geo_df.iterrows():
        # Create a small DataFrame for the popup
        popup_df = pd.DataFrame({
            "Nombre del emprendimiento": [row["emprendimiento"]],
            "Tipo de emprendimiento": [row["tipo_emprendimiento"]],
            "Persona": [row["persona"]],
            "¿Necesita Capacitación?": [row["necesita_cap"]],
            "¿En qué?": [row["enque"]],
            "Modalidad preferida": [row["forma_capacitacion"]],
            "Horario preferido": [row["horario"]]
        })

        html_table = popup_df.to_html(classes="table table-striped table-hover table-condensed table-responsive")
        # Create a folium Popup with the HTML table
        popup = folium.Popup(html_table, max_width=800)
        # Add marker with popup & tooltip
        folium.Marker(
            location=[row['geo_lat'], row['geo_lon']],
            popup=popup,  # Show table on click
            tooltip=row['emprendimiento']  # Show name on hover
        ).add_to(m)


    try:

        selected_df["solo_o_grupo"] = selected_df["solo_o_grupo"].replace({"si": "En grupo", "no": "Individual"})
        selected_df["emp_colab"] = selected_df["emp_colab"].replace({"si":"Sí", "no":"No"})
        
        localidades = plot_tipo1(selected_df, "localidad", "Localidades")
        tipo_emprendimiento = plot_tipo1(selected_df, "tipo_emprendimiento", "Tipos de emprendimiento")
        grupos = plot_tipo1(selected_df, "solo_o_grupo", "Distribución de tipo de trabajo por emprendimiento (individual/grupal)")
        
        espaciodetrabajodf = selected_df.dropna(subset="esp_trabajo")
        espaciodetrabajo = plot_tipo1(espaciodetrabajodf,"esp_trabajo", "Estado de los espacios de trabajo por emprendimiento")

        herramientadf = selected_df.dropna(subset="herramienta")
        herramienta = plot_tipo1(herramientadf, "herramienta", "Estado de las herramientas por emprendimiento")

        maquinariaequipodf = selected_df.dropna(subset="maq_equipo")
        maquinariaequipo = plot_tipo1(maquinariaequipodf, "maq_equipo", "Estado de la maquinaria y del equipo por emprendimiento")

        empleados = plot_tipo1(selected_df, "emp_colab", "Porcentaje de emprendimientos que cuenta con empleados")

        desafios_pie = plot_tipo2(selected_df,[
                        "Costos de materia prima",
                        "Logistica",
                        "Acceso a clientes",
                        "Competencia",
                        "Otro",
                        "Precio del producto"
                        ],
                        'desafios',
                        'Desafíos que detectaron los emprendimientos'
                        )
        
        comunicacion_pie = plot_tipo2(selected_df,[
                        "Redes sociales",
                        "Publicidad impresa",
                        "Voceo",
                        "De boca en boca"
                        ],
                        'comunicacion',
                        'Métodos de promoción de los emprendimientos dentro de la comunidad' 
                        )
        
        acompa_pie = plot_tipo2(selected_df,[
                        "Capacitación",
                        "Capital de trabajo",
                        "Maquinaria y equipo",
                        "Herramientas",
                        "Espacio de trabajo",
                        "Asesoría",
                        ],
                        'tipo_acompa', 
                        'Tipos de acompañamiento que necesitan los emprendimientos'   
                        )
        
        acceso_internet = plot_tipo1(selected_df,'acc_int','Porcentaje de acceso a internet en los emprendimientos')

        conex_pie = plot_tipo2(selected_df,[
                        "Casa propia",
                        "Biblioteca",
                        "Comisaría",
                        "Escuela",
                        "Cabecera municipal",
                        "Red pública (Ejemplo: CFE)",
                        "Otro",
                        ],
                        'donde_conex',
                        'Lugar donde se conectan a internet los representantes de los emprendimientos'    
                        )
        
        calidad_conex_df = selected_df.dropna(subset="tipo_conexion")
        calidad_conexion = plot_tipo1(calidad_conex_df,'tipo_conexion','Calidad de la conexión a internet de los representantes')

        equipo_conex_pie = plot_tipo2(selected_df,[
                        "Celular",
                        "Computadora Escritorio",
                        "Laptop",
                        "Tablet",
                        ],
                        'equipo',
                        'Equipo que usan para conectarse a internet'
                        )
        
        capacitacion = plot_tipo1(selected_df,'capacitacion','Emprendimientos que han recibido capacitación')

        tipos_capacitacion_pie = plot_tipo2(selected_df,[
                        "Emprenimiento",
                        "Marketing",
                        "Finanzas",
                        "Otro",
                        ],
                        'tipo_capacitacion',
                        'Tipos de capacitación recibida'
                        )

        donde_capacitacion = plot_tipo1(selected_df,'donde_capacitacion','Dónde se ha recibido la capacitación')

        quien_cap_pie = plot_tipo2(selected_df,[
                        "Sembrando vida",
                        "Ayuntamiento municipal",
                        "DIF",
                        "IYEM",
                        "Misiones culturales",
                        "Fundación Soriana",
                        "Ko'ox Taani",
                        "EDUCE",
                        "El hombre sobre la tierra",
                        "Heifer",
                        "INPI",
                        "Una ONG",
                        "Un particular",
                        "Otro",
                        ],
                        'quien_cap',
                        'Quiénes otorgaron las capacitaciones'
                        )

        necesita_cap = plot_tipo1(selected_df, 'necesita_cap', 'Porcentaje que considera necesitar capacitación para su emprendimiento')

        forma_cap_df = selected_df.dropna(subset="forma_capacitacion")
        forma_cap = plot_tipo1(forma_cap_df,'forma_capacitacion','Modalidad preferida para las capacitaciones')

        horario_df = selected_df.dropna(subset="horario")
        horario = plot_tipo1(horario_df, 'horario', 'Horario preferido para las capacitaciones')

    except:
        st.info("Hay un problema al generar algunas gráficas. Por favor selecciona otros datos.\nSi el error persiste comuníquelo a david.contreras@fhmm.org o a juan.fernandez@fhmm.org")

    col1, col2 = st.columns(2)
    c1,c2,c3 = st.columns(3)

    try:

        with col1:

            st.plotly_chart(tipo_emprendimiento, use_container_width=True)
            st.plotly_chart(grupos, use_container_width=True)
            st.plotly_chart(empleados, use_container_width=True)
            st.plotly_chart(comunicacion_pie, use_container_width=True)
            st.plotly_chart(acceso_internet, use_container_width=True)
            
            
        with col2:

            st.plotly_chart(localidades, use_container_width=True)
            st.plotly_chart(desafios_pie, use_container_width=True)
            st.plotly_chart(acompa_pie, use_container_width=True)
            st.plotly_chart(calidad_conexion, use_container_width=True)
            st.plotly_chart(equipo_conex_pie, use_container_width=True)
            
            
        with c1:

            st.plotly_chart(espaciodetrabajo, use_container_width=True)


        with c2:

            st.plotly_chart(herramienta, use_container_width=True)


        with c3:

            st.plotly_chart(maquinariaequipo, use_container_width=True)
        


        st.plotly_chart(capacitacion, use_container_width=True)

        co1, co2, co3,  = st.columns(3)
        
        with co1:

            st.plotly_chart(donde_capacitacion, use_container_width=True)


        with co2:

            st.plotly_chart(tipos_capacitacion_pie, use_container_width=True)


        with co3:

            st.plotly_chart(quien_cap_pie, use_container_width=True)


        co4, co5, co6 = st.columns(3)

        with co4:

            st.plotly_chart(necesita_cap, use_container_width=True)


        with co5:

            st.plotly_chart(forma_cap, use_container_width=True)


        with co6:

            st.plotly_chart(horario, use_container_width=True)


        folium_static(m, width=1000, height=1000)
        
        m.save("mapa.html")

        with open("mapa.html", "rb") as file:

            st.download_button(label="Descargar mapa", data=file, file_name="mapa.html", mime="text/html")

    except:

        st.error("Hubo un problema al renderizar las gráficas, por favor comuníqueselo a david.contreras@fhmm.org o a juan.fernandez@fhmm.org")
        
else:

    st.write("Selecciona filas para cargas las gráficas.")