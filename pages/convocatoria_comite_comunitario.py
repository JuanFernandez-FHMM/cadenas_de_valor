import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils
import pandas as pd

utils.logged_in(st.session_state)

tablename = 'convocatoria_comite_comunitario_2025'
secondtable = 'convocatoria_comite_comunitario_data'

def clean_data(tablename,secondtable):

    columns_to_replace = [
    'localidad','tematica','opcion','dias','horarios','encuentros','grupo_trabajo','sexo', 'rol'
    ]

    flat_data, second_table = utils.start_(tablename,secondtable)

    df = pd.json_normalize(flat_data)

    df.drop(columns=['_id', 'formhub/uuid', 'start', 'end','__version__', 'meta/instanceID', '_xform_id_string', '_uuid',
       '_attachments', '_status', '_geolocation', '_submission_time', '_tags',
       '_notes', '_submitted_by'], inplace=True)
    
    if second_table:
        secondtable_dict = dict(second_table)
    else:
        secondtable_dict = {}

    def replace_values(value):
        if isinstance(value, str):  # Ensure it's a string
            parts = value.split(" ")  # Split by spaces
            # Replace each part only if it exists in the dictionary
            replaced_parts = [secondtable_dict.get(part, part) for part in parts]
            return " ".join(replaced_parts)  # Join back with spaces
        return value  # Return unchanged if not a string

    # Ensure the columns exist in the DataFrame before applying the function
    for col in columns_to_replace:
        if col in df.columns:  # Check if the column exists in the DataFrame
            df[col] = df[col].apply(replace_values)
        else:
            print(f"Column '{col}' not found in DataFrame. Skipping...")

    return df


st.set_page_config(page_title="Convocatoria Comité comunitario 2025", page_icon=":page_with_curl:", layout="wide", initial_sidebar_state="collapsed")

st.title("Convocatoria Comité comunitario 2025 :page_with_curl:")

if st.button("Página principal"):
    st.switch_page("pagina_principal.py")

df = clean_data(tablename,secondtable)


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
    'localidad': "Localidad",
    'nombre': "Nombre o nombres",
    'apellidos': "Apellidos",
    'edad': "Edad",
    'sexo': "Sexo",
    'celular': "Teléfono celular",
    'correo': "Correo electrónico",
    'atencion': "¿Qué te llamó la atención de la convocatoria?",
    'tematica': "Temáticas de interés",
    'opcion': "¿Que te gustaría hacer?",
    'dias': "Días disponibles",
    'horarios': "Horario preferido",
    'encuentros': '¿Te gustaría asistir a encuentros presenciales en otras comunidades?',
    'grupo_trabajo': "¿Has formado parte de un grupo de trabajo?",
    'rol': "En el grupo de trabajo, ¿has tenido algún rol específico?",
    'rol_cual': "¿Cuál?",
    
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
    height=600,
    width='100%',
    allow_unsafe_jscode=True,
    update_mode='SELECTION_CHANGED'
)

# Extract selected rows
selected_rows = grid_response['selected_rows']
selected_df = pd.DataFrame(selected_rows)

if not selected_df.empty:
    st.subheader("Filas Seleccionadas")
    st.dataframe(selected_df)
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