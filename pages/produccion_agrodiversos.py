import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils
import pandas as pd
import plotly.express as px

utils.logged_in(st.session_state)


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


st.set_page_config(page_title="Seguimiento de la producción de agrodiversos 2025", page_icon="data/favicon.ico", layout="wide", initial_sidebar_state="collapsed")
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
st.write("#### Selecciona todos los datos para tener una mejor visualización de las gráficas")

if not selected_df.empty:
    st.subheader("Filas Seleccionadas")
    st.dataframe(selected_df[list(columns.keys())])

    total_cosecha = selected_df['cantidad_cosecha'].sum()
    total_comercio = selected_df['cantidad_comercializar'].sum()
    st.write(f"Total Cosecha: {total_cosecha} \t|\t Total Comercializar: {total_comercio}")

    csv = selected_df.to_csv(index=False).encode('utf-8')
    if st.button("Guardar CSV"):
        csv_data = selected_df.to_csv(index=False)
        with open("selected_data.csv", "w", encoding="utf-8") as file:
            file.write(csv_data)
        st.success("Archivo guardado exitosamente")
else:
    st.write("No hay filas seleccionadas")


def create_plots(selected_df, selected_product):
    """
    Creates the required plots for a selected product.  Modified to work with Streamlit.

    Args:
        selected_df: The pandas DataFrame containing the *selected* data.
        selected_product: The product for which to generate the plots.
    """

    # Filter data for the selected product
    product_df = selected_df[selected_df['producto'] == selected_product]

    if product_df.empty:
        st.warning(f"No data found for product: {selected_product}")
        return  # Use st.warning and return

    # --- Plot 1: Line chart of harvest and commercialization over time ---
    # Group by date and sum the quantities
    grouped_df = product_df.groupby('fecha_cosecha').agg({
        'cantidad_cosecha': 'sum',
        'cantidad_comercializar': 'sum'
    }).reset_index()

    # Sort the grouped data by date *after* grouping
    grouped_df['fecha_cosecha'] = pd.to_datetime(grouped_df['fecha_cosecha'], format='%d-%m-%Y')
    grouped_df = grouped_df.sort_values('fecha_cosecha')
    grouped_df['fecha_cosecha'] = grouped_df['fecha_cosecha'].dt.strftime('%d-%m-%Y')

    # Create the line chart using Plotly Express
    fig1 = px.line(
        grouped_df,
        x='fecha_cosecha',
        y=['cantidad_cosecha', 'cantidad_comercializar'],
        title=f'Cantidad de Cosecha y Comercialización de {selected_product} a lo Largo del Tiempo',
        labels={'value': 'Cantidad', 'variable': 'Tipo', 'fecha_cosecha': 'Fecha de Cosecha'},
        template='plotly'
    )
    fig1.update_traces(
        line=dict(width=2.5),
    )
    fig1.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        title_x=0.5
    )
    # Format x-axis to show dates as dd-mm-yyyy
    fig1.update_xaxes(
        tickformat="%d-%m-%Y",
        dtick="M1"  # Show ticks monthly; adjust as needed (e.g., "M3" for quarterly)
    )

    st.plotly_chart(fig1, use_container_width=True)  # Display in Streamlit


    # --- Plot 2: Histogram of harvest quantity distribution by Producer ---

    fig2 = px.histogram(
        product_df,
        x='productor',
        y='cantidad_cosecha',
        color='comunidad',  # Add color based on 'comunidad'
        title=f'Distribución de Cantidad de Cosecha de {selected_product} por Productor',
        labels={'cantidad_cosecha': 'Cantidad de Cosecha', 'productor': 'Productor', 'comunidad': 'Comunidad'},
        template='plotly',
        histfunc='sum'
    )
    fig2.update_layout(
        title_x=0.5,
        bargap=0.1
    )
    st.plotly_chart(fig2, use_container_width=True)


    # --- Plot 3: Distribution of harvest by community ---
    fig3 = px.histogram(
        product_df,
        x='comunidad',
        y='cantidad_cosecha',
        color='comunidad',
        title=f'Distribución de la Cantidad Cosechada de {selected_product} por Comunidad',
        labels={'cantidad_cosecha': 'Cantidad Cosechada', 'comunidad': 'Comunidad'},
        template='plotly',
        histfunc='sum'
    )
    fig3.update_layout(title_x=0.5)
    st.plotly_chart(fig3, use_container_width=True)



if not selected_df.empty:
    # --- Plot selection logic (added) ---
    product_list = selected_df['producto'].unique().tolist()
    selected_product = st.selectbox("Seleccione un producto para análisis:", product_list, key="product_select")
    hide_outliers = st.checkbox("Ocultar valores atipicos", value=False, key="hide_outliers", help='Esto no borra los datos de la base de datos, solo los oculta.')
    if hide_outliers:
        def remove_outliers(df):
            df_filtered = df.copy()
            for col in ['cantidad_cosecha', 'cantidad_comercializar']:
                Q1 = df_filtered[col].quantile(0.25)
                Q3 = df_filtered[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 3 * IQR
                upper_bound = Q3 + 3 * IQR
                df_filtered = df_filtered[(df_filtered[col] >= lower_bound) & (df_filtered[col] <= upper_bound)]
            return df_filtered
        df_plots = remove_outliers(selected_df)
    else:
        df_plots = selected_df.copy()

    if selected_product:  # Only create plots if a product is selected
        create_plots(df_plots, selected_product)
    selected_df = df_plots  # Use filtered data for subsequent plots (e.g., the original bar chart)
    #if selected_product:  # Only create plots if a product is selected
    #    create_plots(selected_df, selected_product)

