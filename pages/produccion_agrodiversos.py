import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils
import pandas as pd


def clean_data(tablename):
    flat_data = utils.start_(tablename)
    df_products = pd.json_normalize(
        flat_data,
        record_path='producto_repeat',
        meta=['comunidad', 'productor', '_submission_time'],
        sep='/'
    )

    # Explode the cosecha_repeat entries
    df_cosecha = df_products.explode('producto_repeat/cosecha_repeat').reset_index(drop=True)

    # Normalize the cosecha_repeat data
    cosecha_data = pd.json_normalize(df_cosecha['producto_repeat/cosecha_repeat'])

    # Combine everything
    df = pd.concat([
        df_cosecha.drop('producto_repeat/cosecha_repeat', axis=1).reset_index(drop=True),
        cosecha_data
    ], axis=1)

    # Clean column names
    df.columns = df.columns.str.replace('producto_repeat/cosecha_repeat/', '', regex=False)
    df.rename(columns={
        'producto_repeat/current_producto': 'producto',
        'cantidad_cosecha_2': 'cantidad_cosecha',
        'cantidad_comercializar_2': 'cantidad_comercializar',
        '_submission_time': 'fecha_submision'
    }, inplace=True)

    # Convert data types
    df['fecha_submision'] = pd.to_datetime(df['fecha_submision'])
    df['fecha_cosecha'] = pd.to_datetime(df['fecha_cosecha'])
    numeric_cols = ['periodo_num', 'cantidad_cosecha', 'cantidad_comercializar']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

    # Final cleanup
    df = df[['producto', 'cantidad_cosecha', 
            'cantidad_comercializar', 'fecha_cosecha', 
            'comunidad', 'productor']]
    cleaning_dict = {
        'Limón país (Indio) (kg)': 'Limón indio (kg)'
    }

    # Apply cleaning dictionary
    df['producto'] = df['producto'].replace(cleaning_dict)

    #change date to d m Y
    df['fecha_cosecha'] = df['fecha_cosecha'].dt.strftime('%d-%m-%Y')

    return df


st.set_page_config(page_title="Seguimiento de la producción de agrodiversos 2025", page_icon=":corn:", layout="wide", initial_sidebar_state="collapsed")

st.title("Seguimiento de la producción de agrodiversos 2025 :corn:")
if st.button("Página principal"):
    st.switch_page("pagina_principal.py")

df = clean_data("seguimiento_prod_agrodiversos_2025")

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(
    groupable=True,
    value=True,
    enableRowGroup=True,
    aggFunc='sum',
    filter='agTextColumnFilter'
)

columns = {
    'producto': "Producto",
    'cantidad_cosecha': "Cantidad cosecha",
    'cantidad_comercializar': "Cantidad a comercializar",
    'fecha_cosecha': "Fecha de la cosecha (dd-mm-YYYY)",
    'comunidad': "Comunidad",
    'productor': "Productor"
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
    
    total_cosecha = selected_df['cantidad_cosecha'].sum()
    total_comercio = selected_df['cantidad_comercializar'].sum()
    st.write(f"Total Cosecha: {total_cosecha} \t|\t Total Comercializar: {total_comercio}")
    
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

