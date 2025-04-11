import streamlit as st
from supabase import create_client, Client
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from utils import logged_in

logged_in(st.session_state)



# Initialize connection to Supabase
url: str = st.secrets.supabase["url"]
key: str = st.secrets.supabase["key"]

supabase: Client = create_client(url, key)

# get data from supabase
milpa_sustentable = supabase.table("milpa_sustentable").select("*").execute()
transacciones = supabase.table("transacciones_milpa_traspatiomaya").select("*").execute()
transacciones_data = supabase.table("transacciones_milpa_traspatiomaya_data").select("*").execute()
actualizaciones_prod_maiz = supabase.table("registro_actualizaciones_produccion_maiz").select("data").execute()
actualizaciones_prod_maiz_data = supabase.table("registro_actualizaciones_produccion_maiz_data").select("*").execute()

milpa_sustentable_df = pd.DataFrame(milpa_sustentable.data)

actualizaciones_prod_maiz_data_df = pd.DataFrame(actualizaciones_prod_maiz_data.data)

# actualizaciones_prod_maiz_df es contiene jsons en la columna data que se extrajo, así que se debe convertir a un dataframe
actualizaciones_prod_maiz_df = pd.json_normalize(actualizaciones_prod_maiz.data)
actualizaciones_prod_maiz_df = actualizaciones_prod_maiz_df.explode("data.repeat_variedades")

# replace on actualizaciones_prod_maiz_df "data.productor" where actualizaciones_prod_maiz_data_df "name" == "productor" get "label"
actualizaciones_prod_maiz_df["data.productor"] = actualizaciones_prod_maiz_df["data.productor"].replace(
    actualizaciones_prod_maiz_data_df.set_index("name")["label"].to_dict()
)

# remove cols not useful
actualizaciones_prod_maiz_df = actualizaciones_prod_maiz_df.drop(
    columns=[
        "data.formhub/uuid",
        "data.start",
        "data.end",
        "data.variedad",
        "data.num_selected",
        "data.repeat_variedades_count",
        "data.__version__",
        "data.meta/instanceID",
        "data._xform_id_string",
        "data._uuid",
        "data._attachments",
        "data._status",
        "data._geolocation",
        "data._submission_time",
        "data._tags",
        "data._notes",
        "data._submitted_by",
    ]
)

# now copying milpa_sustentable_df into new_data, then for data.productor on actualizaciones_prod_maiz_df that coincide with productor on milpa_sustentable_df, check on data.repeat_variedades containing a json, find key "repeat_variedades/current_variedad_name", use that to join on milpa_sustentable_df["variedad"], if found, replace "data.repeat_variedades"."repeat_variedades/cosecha" on milpa_sustentable_df.cosecha and "data.repeat_variedades"."repeat_variedades/excedente" on milpa_sustentable_df.venta, if not found, insert new line on milpa_sustentable_df with data.productor, data.repeat_variedades."repeat_variedades/cosecha" and data.repeat_variedades."repeat_variedades/excedente" on milpa_sustentable_df.cosecha and milpa_sustentable_df.venta respectively everything else set to null. if data.productor not found on productor on milpa_sustentable_df, insert new line on milpa_sustentable_df with data.productor, data.repeat_variedades."repeat_variedades/cosecha" and data.repeat_variedades."repeat_variedades/excedente" on milpa_sustentable_df.cosecha and milpa_sustentable_df.venta respectively everything else set to null.
new_data = milpa_sustentable_df.copy()

# Create a mapping for productor names using actualizaciones_prod_maiz_data_df
productor_map = actualizaciones_prod_maiz_data_df.set_index("name")["label"].to_dict()

# Ensure productor column in new_data is a string for consistency
new_data['productor'] = new_data['productor'].astype(str)




# Ensure productor mapping is correct
productor_map = actualizaciones_prod_maiz_data_df.set_index("name")["label"].to_dict()
new_data['productor'] = new_data['productor'].astype(str)  # Standardize type

# Add new columns if they don't exist
for col in ["nueva cosecha", "diferencia cosecha", "nueva venta", "diferencia venta"]:
    if col not in new_data.columns:
        new_data[col] = None

for _, row in actualizaciones_prod_maiz_df.iterrows():
    # Get productor name from mapping
    productor_id = str(row['data.productor'])
    productor_name = productor_map.get(productor_id, productor_id)

    # Extract repeat_variedades
    variedades_list = row.get("data.repeat_variedades", [])

    # If not a list, wrap in a list
    if not isinstance(variedades_list, list):
        variedades_list = [variedades_list] if isinstance(variedades_list, dict) else []
    
    for variedad in variedades_list:
        try:
            variedad_name = variedad.get("repeat_variedades/current_variedad_name")
            cosecha = variedad.get("repeat_variedades/cosecha")
            excedente = variedad.get("repeat_variedades/excedente")

            if not variedad_name:
                print(f"Skipping due to missing variety name: {variedad}")
                continue

            # Convert numeric values if needed
            cosecha = int(cosecha) if isinstance(cosecha, str) and cosecha.isdigit() else cosecha
            excedente = int(excedente) if isinstance(excedente, str) and excedente.isdigit() else excedente

            # Match existing row
            match = (new_data['productor'] == productor_name) & (new_data['variedad'] == variedad_name)

            if match.any():
                # Get the current values
                current_cosecha = new_data.loc[match, 'cosecha'].values[0]
                current_venta = new_data.loc[match, 'venta'].values[0]

                # Compute differences
                diferencia_cosecha = (cosecha - current_cosecha) if current_cosecha is not None else None
                diferencia_venta = (excedente - current_venta) if current_venta is not None else None

                # Update new columns
                new_data.loc[match, 'nueva cosecha'] = cosecha
                new_data.loc[match, 'diferencia cosecha'] = diferencia_cosecha
                new_data.loc[match, 'nueva venta'] = excedente
                new_data.loc[match, 'diferencia venta'] = diferencia_venta
            else:
                # Insert new row with all other columns set to None
                new_row = pd.DataFrame([{col: None for col in new_data.columns}])
                new_row.update({
                    'productor': productor_name,
                    'variedad': variedad_name,
                    'nueva cosecha': cosecha,
                    'diferencia cosecha': None,  # No previous value, so difference is None
                    'nueva venta': excedente,
                    'diferencia venta': None  # No previous value
                })

                new_data = pd.concat([new_data, new_row], ignore_index=True)
        except Exception as e:
            print(f"Skipping due to unexpected data format: {variedad}, Error: {e}")

# add columns "cosecha total" and "venta total" as new columns to new_data it should include "nueva cosecha" and "nueva venta" respectively unless they are null, if they are null, use "cosecha" and "venta" respectively
new_data["cosecha total"] = new_data.apply(
    lambda row: row["nueva cosecha"] if pd.notnull(row["nueva cosecha"]) else row["cosecha"], axis=1
)
new_data["venta total"] = new_data.apply(
    lambda row: row["nueva venta"] if pd.notnull(row["nueva venta"]) else row["venta"], axis=1
)
new_data["venta total sin compras"] = new_data["venta total"].copy()


# reorder columns based on list
column_order = [
    "productor",
    "variedad",
    "color",
    "cosecha total",
    "venta total",
    "venta total sin compras",
    "cosecha",
    "nueva cosecha",
    "diferencia cosecha",
    "venta",
    "nueva venta",
    "diferencia venta",
    "estado",
    "municipio",
    "comunidad",
    "padron"

]

new_data = new_data[column_order]
#copy "venta total" to "venta total sin compras" in new_data

# transform transacciones["productor"] using transacciones_data["name"] and transacciones_data["label"]
# Create DataFrame from transacciones and transform productor column
transacciones_df = pd.DataFrame(transacciones.data)
transacciones_data_df = pd.DataFrame(transacciones_data.data)
productor_mapping = transacciones_data_df.set_index('name')['label'].to_dict()
transacciones_df['productor'] = transacciones_df['productor'].map(productor_mapping)

#match transacciones_df "productor" and "variedad" with new_data "productor" and "variedad" and substract transacciones_df["cantidad"] from new_data["venta total"]
for _, row in transacciones_df.iterrows():
    productor = row['productor']
    variedad = row['variedad']
    cantidad = row['cantidad']

    # Find matching rows in new_data
    match = (new_data['productor'] == productor) & (new_data['variedad'] == variedad)

    if match.any():
        # Subtract cantidad from venta total
        new_data.loc[match, 'venta total'] -= cantidad
    else:
        # If no match found, you might want to handle this case (e.g., log it, raise an error, etc.)
        print(f"No match found for productor: {productor}, variedad: {variedad}")

# add column on new_data "cantidad comprada" including sum of "cantidad" from "productor" and "variedad" on transacciones_df
new_data["cantidad comprada"] = 0
for _, row in transacciones_df.iterrows():
    productor = row['productor']
    variedad = row['variedad']
    cantidad = row['cantidad']

    # Find matching rows in new_data
    match = (new_data['productor'] == productor) & (new_data['variedad'] == variedad)

    if match.any():
        # Add cantidad to cantidad comprada
        new_data.loc[match, 'cantidad comprada'] += cantidad
    else:
        # If no match found, you might want to handle this case (e.g., log it, raise an error, etc.)
        print(f"No match found for productor: {productor}, variedad: {variedad}")


# reorder columns based on list
column_order = [
    "productor",
    "variedad",
    "color",
    "cosecha total",
    "venta total",
    "cantidad comprada",
    "venta total sin compras",
    "cosecha",
    "nueva cosecha",
    "diferencia cosecha",
    "venta",
    "nueva venta",
    "diferencia venta",
    "estado",
    "municipio",
    "comunidad",
    "padron"

]

new_data = new_data[column_order]

st.set_page_config(page_title="Disponibilidad de maíz 2025", page_icon="data/favicon.ico", layout="wide", initial_sidebar_state="collapsed")

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

st.title("Disponibilidad de maíz 2025 :material/spa:")
if st.button("Página principal"):
    st.switch_page("pagina_principal.py")


gb = GridOptionsBuilder.from_dataframe(new_data)

gb.configure_default_column(
    groupable=True,
    value=True,
    enableRowGroup=True,
    aggFunc='sum',
    filter='agTextColumnFilter',
    fit_columns_on_grid_load=True,
    
)

columns = {
    "productor":"Productor",
    "variedad":"Variedad",
    "color":"Color",
    "cosecha total":"Cosecha total",
    "venta total":"Venta total",
    "cantidad comprada":"Cantidad comprada",
    "venta total sin compras":"Venta total sin compras",
    "cosecha": "Cosecha original",
    "nueva cosecha": "Nuevo registro de cosecha",
    "diferencia cosecha": "Diferencia de cosecha",
    "venta":"Venta original",
    "nueva venta":"Nuevo registro de venta",
    "diferencia venta":"Diferencia de venta",
    "estado":"Estado",
    "municipio":"Municipio",
    "comunidad":"Localidad",
    "padron":"Padron"
}

important_columns = ["Cosecha total", "Venta total"]

for col, header in columns.items():
    if header in important_columns:
        gb.configure_column(
            col,
            header_name=header,
            cellStyle={"backgroundColor": "#F0E965", "fontWeight": "bold"},  # Gold background, bold text
            width=390
        )
    else:
        gb.configure_column(col, header_name=header)

gb.configure_column(
    "padron",
    header_name="Padrón",
    rowGroup=True,  # Enables grouping
    enableRowGroup=True,  # Allows row grouping
    hide=True,  # Hides the column in the grid


)


gb.configure_selection(
    selection_mode="multiple",
    use_checkbox=True,
    pre_selected_rows=[],
    header_checkbox=True,
    suppressRowDeselection=False
)
gb.configure_side_bar(filters_panel=True,)
gb.configure_grid_options(suppressAutoSize=False, suppressSizeToFit=False)


grid_options = gb.build()


grid_response = AgGrid(
    new_data,
    gridOptions=grid_options,
    allow_unsafe_jscode=True,
    update_mode="MODEL_CHANGED",
    enable_enterprise_modules=True,
    theme="streamlit",
    fit_columns_on_grid_load=True,
    height=700,
)
selected_rows = grid_response['selected_rows']
selected_df = pd.DataFrame(selected_rows)

# add download button
st.download_button(
    label="Descargar datos seleccionados",
    data=selected_df.to_csv(index=False).encode('utf-8'),
    file_name='disponibilidad_maiz_2025.csv',
    mime='text/csv',
)

# use st.metric to show total of selected rows in cosecha total and venta total
if not selected_df.empty:
    cosecha_total = selected_df["cosecha total"].sum()
    venta_total = selected_df["venta total"].sum()
    cols = st.columns([1,1,6])
    with cols[0]:
        st.metric(label="Cosecha total seleccionada", value=cosecha_total, delta=None)
    with cols[1]:
        st.metric(label="Venta total seleccionada", value=venta_total, delta=None)

st.write(transacciones_df)