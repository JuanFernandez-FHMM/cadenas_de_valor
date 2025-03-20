import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
import time
import folium
from streamlit_folium import folium_static

utils.logged_in(st.session_state)

def clean_data(tablename, secondtable):
    # Read data using utils, now fetching both flat_data and second_table
    flat_data, second_table = utils.start_(tablename, secondtable)
    df = pd.json_normalize(flat_data)
    
    # Ensure required columns exist, filling missing ones with NaN
    required_columns = [
        'estado', 'municipio', 'localidad', 'persona', 'nombres', 'apellidos',
        'edad', 'sexo', 'celular', 'correo', 'estudios', 'universidad',
        'beca_interes', 'labor', 'resena', '_submission_time'
    ]
    
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    
    # Create a dictionary from the second table for value replacement
    secondtable_dict = {}
    if second_table:
        secondtable_dict = {item['name']: item['label'] for item in second_table}
    
    # Columns where values should be replaced using secondtable_dict
    columns_to_replace = [
        'estado', 'municipio', 'localidad', 'persona', 'sexo', 'estudios', 'universidad',
        'beca_interes', 'labor', 
    ]
    
    # Function to replace values using the secondtable_dict
    def replace_values(value):
        if isinstance(value, str):
            parts = value.split()
            replaced_parts = [secondtable_dict.get(part, part) for part in parts]
            return ' '.join(replaced_parts)
        return value
    
    # Apply replacement to each column if it exists in df
    for col in columns_to_replace:
        if col in df.columns:
            df[col] = df[col].apply(replace_values)
    
    # Handling persona logic
    df['persona_present'] = df['persona'].notna()
    
    df['final_nombres'] = df.apply(lambda x: x['persona'] if x['persona_present'] else x['nombres'], axis=1)
    df['final_apellidos'] = df.apply(lambda x: None if x['persona_present'] else x['apellidos'], axis=1)
    df['final_edad'] = df.apply(lambda x: None if x['persona_present'] else x['edad'], axis=1)
    df['final_sexo'] = df.apply(lambda x: None if x['persona_present'] else x['sexo'], axis=1)
    
    # Convert data types
    df['_submission_time'] = pd.to_datetime(df['_submission_time'], errors='coerce')
    df['edad'] = pd.to_numeric(df['edad'], errors='coerce')
    
    # Format dates
    df['_submission_time'] = df['_submission_time'].dt.strftime('%d-%m-%Y')
    
    # Select relevant columns for output
    df = df[[
        'estado', 'municipio', 'localidad', 'final_nombres', 'final_apellidos', 
        'final_edad', 'final_sexo', 'celular', 'correo', 'estudios', 'universidad', 
        'beca_interes', 'labor', 'resena', '_submission_time'
    ]]
    
    df.rename(columns={
        'final_nombres': 'nombres',
        'final_apellidos': 'apellidos',
        'final_edad': 'edad',
        'final_sexo': 'sexo',
        '_submission_time': 'fecha_submision'
    }, inplace=True)
    
    return df

st.set_page_config(page_title="Preregistro para las Becas Integrales FHMM-IU", page_icon="data/favicon.ico", layout="wide", initial_sidebar_state="collapsed")
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


st.title("Preregistro para las Becas Integrales FHMM-IU :school:")
if st.button("Página principal"):
    st.switch_page("pagina_principal.py")

df = clean_data("preregistro_becas_integrales_FHMMIU", "preregistro_becas_data")

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
    'nombres': "Nombres",
    'apellidos': "Apellidos",
    'edad': "Edad",
    'sexo': "Sexo",
    'celular': "Número de celular",
    'correo': "Correo electrónico",
    'estudios': "Nivel de estudios",
    'universidad': "Universidad",
    'beca_interes': "Beca de interés",
    'labor': "Situación laboral",
    'resena': "Reseña personal",
    'fecha_submision': "Fecha de envío (dd-mm-YYYY)"
}

  
for col, header in columns.items():
    gb.configure_column(col, header_name=header)

gb.configure_selection(
    selection_mode="multiple",
    use_checkbox=True,
    pre_selected_rows=[],
    header_checkbox=True,
    suppressRowDeselection=False
)
gb.configure_side_bar(filters_panel=True, defaultToolPanel='filters')
grid_options = gb.build()

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
    col1, col2 = st.columns(2)
    
    with col1:
        sexo = px.pie(selected_df, names='sexo', title='Distribución por sexo')
        st.plotly_chart(sexo)

        estudios = px.pie(selected_df, names='estudios', title='Distribución por nivel de estudios')
        st.plotly_chart(estudios)

        universidad = px.pie(selected_df, names='universidad', title='Distribución por universidad')
        st.plotly_chart(universidad)

    with col2:
        becas_interes = px.pie(selected_df, names='beca_interes', title='Distribución por beca de interés')
        st.plotly_chart(becas_interes)

        labor = px.pie(selected_df, names='labor', title='Distribución por situación laboral')
        st.plotly_chart(labor)

        selected_df = selected_df.dropna(subset=['edad'])  # Drop rows with missing 'edad'
        selected_df['edad'] = pd.to_numeric(selected_df['edad'], errors='coerce')  # Convert to numeric

        # Define the age bins
        age_bins = [0, 11, 14, 18, 29, 100]
        age_labels = ['12-', '12-14', '15-18', '19-29', '30+']

        # Create a new column for the age groups
        selected_df['age_group'] = pd.cut(selected_df['edad'], bins=age_bins, labels=age_labels, right=False)

        # Count the number of occurrences in each age group
        age_group_counts = selected_df['age_group'].value_counts().reindex(age_labels, fill_value=0)

        # Create the histogram using Plotly
        fig = px.bar(
            x=age_group_counts.index,
            y=age_group_counts.values,
            labels={'x': 'Age Group', 'y': 'Count'},
            title='Age Distribution',
            text=age_group_counts.values
        )

        # Customize the layout
        fig.update_traces(marker_line_color='black', marker_line_width=1.5)
        fig.update_layout(
            xaxis_title='Age Group',
            yaxis_title='Count',
            bargap=0.2,  # Adjust the gap between bars
            xaxis={'categoryorder':'array', 'categoryarray': age_labels},  # Ensure x-axis order
            showlegend=False
        )

        # Show the plot
        st.plotly_chart(fig)
# Function to geocode locations
def geocode_location(estado, municipio, localidad):
    try:
        query = f"{localidad}, {municipio}, {estado}, Mexico"
        location = geolocator.geocode(query, exactly_one=True, timeout=10)
        return (location.latitude, location.longitude) if location else (None, None)
    except:
        return (None, None)

try:
    # Geocoding setup
    geolocator = Nominatim(user_agent="mexico_locality_mapper")
    
    # Generate coordinates (if not already present)
    if 'geo_lat' not in selected_df.columns or 'geo_lon' not in selected_df.columns:
        selected_df['geo_lat'] = None
        selected_df['geo_lon'] = None
        
        for index, row in selected_df.iterrows():
            lat, lon = geocode_location(row['estado'], row['municipio'], row['localidad'])
            selected_df.at[index, 'geo_lat'] = lat
            selected_df.at[index, 'geo_lon'] = lon
            time.sleep(1)

    # Clean data
    geo_df = selected_df.dropna(subset=['geo_lat', 'geo_lon']).copy()
    
    if not geo_df.empty:
        # Create Folium map
        map_center = [geo_df['geo_lat'].mean(), geo_df['geo_lon'].mean()]
        m = folium.Map(location=map_center, zoom_start=10, tiles="OpenStreetMap")

        # Add markers with popups
        for _, row in geo_df.iterrows():
            # Create popup table
            popup_df = pd.DataFrame({
                "Campo": ["Estado", "Municipio", "Localidad",],
                "Valor": [
                    row.get("estado", ""),
                    row.get("municipio", ""),
                    row.get("localidad", ""),

                ]
            })
            
            html_table = popup_df.to_html(index=False, classes="table table-striped")
            popup = folium.Popup(html_table, max_width=800)
            
            folium.Marker(
                location=[row['geo_lat'], row['geo_lon']],
                popup=popup,
                tooltip=row.get('emprendimiento', 'Sin nombre')
            ).add_to(m)

        # Display map in Streamlit
        folium_static(m)
        
    else:
        st.warning("No se encontraron coordenadas válidas para mostrar el mapa.")

except Exception as e:
    st.error(f"Error al generar el mapa: {str(e)}")
    st.write("Mapa no disponible")