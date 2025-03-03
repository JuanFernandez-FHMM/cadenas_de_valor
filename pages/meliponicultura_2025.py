import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import time
import folium
from streamlit_folium import folium_static
import numpy as np

def plot_tipo1(dataset, columna, titulo, textposition='auto'):
    plot = px.pie(dataset, names=columna, title=titulo)
    plot.update_traces(
        textposition=textposition,
        textinfo='percent+label+value',
        hole=0.3,
        marker=dict(line=dict(color='#000000', width=2))
    )
    return plot

def plot_tipo2(dataframe, lista_categorias, columna, titulo, textposition='auto'):
    df_temp = dataframe[columna]
    df = []
    for i in df_temp:
        found_categories = [categoria for categoria in lista_categorias if categoria.lower() in str(i).lower()]
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

def clean_data(tablename, secondtable):
    # Load flattened data and helper table
    flat_data, second_table = utils.start_(tablename, secondtable)
    
    # Create value replacement dictionary
    replace_dict = {item['name']: item['label'] for item in second_table} if second_table else {}
    
    # Normalize main data structure
    df = pd.json_normalize(
        flat_data,
        meta=[
            '_id', 'estado', 'municipio', 'localidad', 'grupo',
            '_submission_time', 'ing_prom_grupo', 'ciclo', 'image', 'geo'
        ],
        sep='/',
        errors='ignore'
    )
    
    # Process nested abeja data
    abejas = pd.json_normalize(
        flat_data,
        record_path='repeat_abejas',
        meta=['_id'],
        sep='/',
        errors='ignore'
    )
    
    # Explode and normalize productos within abejas
    if 'repeat_abejas/com_x_productos' in abejas.columns:
        abejas = abejas.explode('repeat_abejas/com_x_productos')
        productos = pd.json_normalize(
            abejas['repeat_abejas/com_x_productos'],
            sep='/'
        ).add_prefix('producto_')
        abejas = pd.concat([abejas.drop(columns=['repeat_abejas/com_x_productos']), productos], axis=1)
    
    # Process nested convenios data
    if 'repeat_convenios' in df.columns:
        convenios = pd.json_normalize(
            flat_data,
            record_path='repeat_convenios',
            meta=['_id'],
            sep='/',
            errors='ignore'
        )
        # Merge convenios data as separate columns
        if not convenios.empty:
            #convenios = convenios.add_prefix('convenio_')
            #print(convenios.columns)
            #print("hi")
            df = df.merge(convenios, on='_id', how='left')
    
    # Merge abejas data
    merged = df.merge(abejas, on='_id', how='left')
    
    # Value replacement function
    
    
    # Process geo coordinates
    if 'geo' in merged.columns:
        geo_split = merged['geo'].str.split(' ', expand=True)
        merged['latitud'] = pd.to_numeric(geo_split[0], errors='coerce')
        merged['longitud'] = pd.to_numeric(geo_split[1], errors='coerce')
    
    # Handle image URL
    if '_attachments' in merged.columns:
        merged['imagen_url'] = merged['_attachments'].apply(
            lambda x: x[0]['download_url'] if x and isinstance(x, list) else None
        )
    
    # Select and rename final columns

    def replace_values(column):
        replace_columns = [
            'estado', 'municipio', 'localidad', 'grupo', 'persona',
            'abejas', 'factura', 'ciclo', 'pract_conserv', 'convenios',
            'alimentacion', 'acces_ubi', 'infra', 'acom', 'lim', 'herr',
            'agro', 'herr_equipo', 'trab', 'auto', 'repeat_abejas/productos', 'producto_repeat_abejas/com_x_productos/compradores', 'repeat_convenios/conv_prov'
        ]
        if column.name in replace_columns:
            return column.apply(
                lambda x: ' '.join([replace_dict.get(part, part) for part in str(x).split()])
            )
        return column
    
    # Apply value replacements
    merged = merged.apply(replace_values)
    #print(merged.columns)
    
    merged.drop(columns=['_id', 'formhub/uuid', 'start', 'end', 'repeat_persona_edadsexo_count','repeat_persona_edadsexo',
                          'count_abejas', 'repeat_abejas_count', 'repeat_abejas', 'count_practicas', 'repeat_practicas_count', 'repeat_practicas',
                          'count_convenios', 'repeat_convenios_count',
       'repeat_convenios', 'image', 'geo', '__version__', 'meta/instanceID',
       '_xform_id_string', '_uuid', '_attachments', '_status', '_geolocation',
       '_submission_time', '_tags', '_notes', '_submitted_by', 'repeat_abejas/count_prod_vendidos',
       'repeat_abejas/com_x_productos_count',], inplace=True)
    

    return merged#[[col for col in final_columns if col in merged.columns]]


st.set_page_config(page_title="Meliponario Comercialización 2025", page_icon=":honeybee:", layout="wide", initial_sidebar_state="collapsed")

st.title("Meliponario Comercialización 2025 :honeybee:")
if st.button("Página principal"):
    st.switch_page("pagina_principal.py")

df = clean_data("meliponicultura_comercializacion_2025", "meliponicultura_2024_data")
#st.write(df.columns)
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(
    groupable=True,
    value=True,
    enableRowGroup=True,
    aggFunc='sum',
    filter='agTextColumnFilter'
)

columns = {
    'estado': "Estado",
    'municipio': "Municipio", 
    'localidad': "Localidad",
    'grupo': "Grupo",
    'persona': "Miembros del grupo",
    'count_personas': "Número de personas en el grupo",
    'abejas': "Especies de abeja del grupo",
    'ing_prom_grupo': "Ingreso promedio del grupo",
    'factura': "Tipo de factura",
    'ciclo': "Ciclos trabajados con FHMM",
    'pract_conserv': "Prácticas de conservación",
    'convenios': "Convenios",
    'alimentacion': "Alimentación",
    'acces_ubi': "Condiciones del meliponario",
    'infra': "Infraestructura",
    'acom': "Acomodo de colmenas",
    'lim': "Limpieza y orden",
    'herr': "Herramientas de monitoreo", 
    'agro': "Manejo de plagas",
    'herr_equipo': "Herramientas y equipo en inventario",
    'trab': 'Trabajo en red',
    'auto': 'Autoconsumo',
    'pract_fortalecer': 'Prácticas a fortalecer',
    'comentarios':'Comentarios',
    'repeat_convenios/current_convenio': 'Convenios',
    'repeat_convenios/conv_prov': 'Proveedores',
    'repeat_abejas/current_abeja': 'Abeja',
    'repeat_abejas/num_colmenas_fuertes': 'Número de colmenas fuertes',
    'repeat_abejas/num_colmenas_estables': 'Número de colmenas estables',
    'repeat_abejas/num_colmenas_pequenas': 'Número de colmenas pequeñas',
    'repeat_abejas/productos': 'Productos',
    'producto_repeat_abejas/com_x_productos/current_prod': 'Producto',
    'producto_repeat_abejas/com_x_productos/cant_com_prod': 'Cantidad de producto',
    'producto_repeat_abejas/com_x_productos/compradores': 'Compradores',
    'producto_repeat_abejas/com_x_productos/cant_prod_2025': 'Cantidad a producir en 2025',
    'latitud': 'Latitud',
    'longitud': 'Longitud',
    'imagen_url': 'Imagen del meliponario'

}
  
for col, header in columns.items():
    gb.configure_column(col, header_name=header)

gb.configure_selection(
    selection_mode="multiple",
    use_checkbox=True,
    pre_selected_rows=[],
    suppressRowDeselection=False
)
gb.configure_side_bar(filters_panel=True, defaultToolPanel='filters')
grid_options = gb.build()

grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    height=600,
    width='100%',
    allow_unsafe_jscode=True,
    update_mode='SELECTION_CHANGED'
)

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
    localidades = plot_tipo1(selected_df, "localidad", "Localidades")
    tipo_factura = plot_tipo1(selected_df, "factura", "Tipos de Factura")
    #ingreso_promedio = plot_tipo1(selected_df, "ing_prom_grupo", "Ingreso Promedio")
    #infraestructura = plot_tipo1(selected_df, "infra", "Infraestructura del Meliponario")
    #acomodo_colmenas = plot_tipo1(selected_df, "acom", "Acomodo de Colmenas")
    #limpieza_orden = plot_tipo1(selected_df, "lim", "Limpieza y Orden")
    #manejo_plagas = plot_tipo1(selected_df, "agro", "Manejo de Plagas")
    #trabajo_red = plot_tipo1(selected_df, "trab", "Trabajo en Red")
    #autoconsumo = plot_tipo1(selected_df, "auto", "Autoconsumo")

    practicas_conservacion = plot_tipo2(selected_df, [
        "Diversidad de tamaños de colmena",
        "Diversidad de plantas melíferas",
        "Limpieza del entorno del meliponario",
        "Manejo agroecológico de plagas",
        "Alimentación con miel melipona a divisiones o población pequeña.",
        "División, fortalecimiento de colmenas",
        "Diversidad de productos de la colmena"
    ], 'pract_fortalecer', 'Prácticas de Conservación')

    productos = plot_tipo2(selected_df, [
        "Miel (l)",
        "Polen",
        "Cera"
    ], 'repeat_abejas/productos', 'Productos Generados')

    # Streamlit UI
    st.title("Análisis de Meliponicultura")
    col1, col2 = st.columns(2)

    with col1:
        st.plotly_chart(tipo_factura, use_container_width=True)
        st.plotly_chart(localidades, use_container_width=True)
        #st.plotly_chart(infraestructura, use_container_width=True)
        #st.plotly_chart(acomodo_colmenas, use_container_width=True)
        #st.plotly_chart(limpieza_orden, use_container_width=True)

    with col2:
        st.plotly_chart(practicas_conservacion, use_container_width=True)
        #st.plotly_chart(ingreso_promedio, use_container_width=True)
        #st.plotly_chart(manejo_plagas, use_container_width=True)
        #st.plotly_chart(trabajo_red, use_container_width=True)
        #st.plotly_chart(autoconsumo, use_container_width=True)
        st.plotly_chart(productos, use_container_width=True)
else:
    st.write("No hay filas seleccionadas")