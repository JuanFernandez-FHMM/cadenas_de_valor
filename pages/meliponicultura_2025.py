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
import io


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

def concatenate_values(series):
    return ','.join(str(v) for v in series if pd.notna(v)) if  (v for v in series) is int else lambda x: ','.join(sorted(set(str(v) for v in x if pd.notna(v))))
def replace_values(value):
    if isinstance(value, str):  # Ensure it's a string
        parts = value.split(" ")  # Split by spaces
        replaced_parts = [secondtable_dict.get(part, part) for part in parts]  # Replace each part
        return " ".join(replaced_parts)  # Join back with spaces
    return value  # Return unchanged if not a string
def convert_df_to_csv(df):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()



tablename = 'meliponicultura_comercializacion_2025'
secondtable = 'meliponicultura_2024_data'

flat_data, second_table = utils.start_(tablename, secondtable=secondtable)
df = pd.json_normalize(flat_data)

# Drop unnecessary metadata columns
drop_cols = ['formhub/uuid', 'start', 'end', '__version__', 'meta/instanceID', '_xform_id_string', '_uuid',
             '_attachments', '_status', '_geolocation', '_submission_time', '_tags', '_notes', '_submitted_by']
df.drop(columns=[col for col in drop_cols if col in df.columns], inplace=True)

# List of nested columns (repeat groups) that need to be exploded
repeat_groups = [
    "repeat_persona_edadsexo",
    "repeat_otros",
    "repeat_personas_otro",
    "repeat_abejas",
    "com_x_productos",
    "repeat_practicas",
    "repeat_convenios"
]

# Fully expand all repeat groups
expanded_dfs = []
for group in repeat_groups:

    if group in df.columns:
        


        expanded_df = df.explode(group)
        expanded_df = pd.json_normalize(expanded_df.to_dict(orient="records"))
        expanded_dfs.append(expanded_df)
        if group == "repeat_abejas":
            #print(expanded_df.columns)
            #com = expanded_df
            # expand com_x_productos inside abejas named "repeat_abejas/com_x_productos"
            if "repeat_abejas.repeat_abejas/com_x_productos" in expanded_df.columns:
                expand_df = expanded_df.explode("repeat_abejas.repeat_abejas/com_x_productos")
                expand_df = pd.json_normalize(expand_df.to_dict(orient="records"))
                expanded_dfs.append(expand_df)


# Merge back all expanded data
if expanded_dfs:
    df = pd.concat(expanded_dfs, ignore_index=True)

if second_table:
    secondtable_dict = dict(second_table)
else:
    secondtable_dict = {}

columns_to_replace = [
    'estado','municipio','localidad','grupo','persona', 'repeat_persona_edadsexo.repeat_persona_edadsexo/sexo_persona', 'repeat_otros.repeat_otros/sexo',
     'abejas', 'repeat_abejas.repeat_abejas/productos', 'factura','ciclo','pract_conserv', 'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores',
    'repeat_practicas.repeat_practicas/capacitador','convenios', 'repeat_convenios.repeat_convenios/conv_prov','conserv_abejas','alimentacion',
    'acces_ubi', 'infra', 'acom', 'lim', 'herr', 'agro','herr_equipo','trab','auto',
]


for col in columns_to_replace:
        df[col] = df[col].apply(replace_values)

df.drop(columns=["repeat_persona_edadsexo_count", "repeat_abejas_count",'repeat_practicas_count',
                 'repeat_abejas','repeat_practicas','repeat_convenios_count','repeat_convenios',
                 'repeat_otros_count', 'repeat_otros','repeat_persona_edadsexo','repeat_otros.repeat_otros/curr_persona_nueva',
                 'repeat_abejas.repeat_abejas/com_x_productos'], inplace=True)

st.set_page_config(page_title="Meliponicultura Comercialización 2025", page_icon=":honeybee:", layout="wide", initial_sidebar_state="collapsed")

st.title("Meliponicultura Comercialización 2025 :honeybee:")
if st.button("Página principal"):
    st.switch_page("pagina_principal.py")




# use dropdown to show table
tb_principal = st.expander("Tabla principal", icon=":material/table_view:")
with tb_principal:
    st.write(df)
    csv_data = convert_df_to_csv(df)
    st.download_button(
        label="Descargar CSV",
        data=csv_data,
        file_name="data.csv",
        mime="text/csv",
        key="main"
    )



useful = df.dropna(subset=['repeat_abejas.repeat_abejas/current_abeja'])
#fill every null with 0

# Group by _id and the main identifier, then concatenate other columns
#merged_abejas = useful.groupby(["_id", "repeat_abejas.repeat_abejas/current_abeja", 'grupo']).agg(concatenate_values).reset_index()

cols_to_keep = ['_id','grupo',  ]
useful_first_filter = useful.loc[:, cols_to_keep]

useful_first_filter = useful_first_filter.drop_duplicates(subset=['_id', 'grupo',])
#st.write(useful_first_filter)
cols1 = {
    '_id': 'ID',
    'grupo': 'Grupo',
}
# Now rename the columns using the columns1 dictionary
useful_first_filter = useful_first_filter.rename(columns=cols1)


#useful_first_filter.dropna(subset=['repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod'], inplace=True)
#st.write(abejas)
tb_ventas = st.expander("Tabla con filtro de productos", icon=":material/inventory_2:")
with tb_ventas:
    #st.write(useful_first_filter)
    gb = GridOptionsBuilder.from_dataframe(useful_first_filter)
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        aggFunc='sum',
        filter='agTextColumnFilter',
        # Add these options for better auto-sizing
        resizable=True,
        autoHeight=True,
        wrapText=True,
        # This will make columns fit their content
        autoSizeColumns=True
    )

    # You can also set a minimum width for all columns
    gb.configure_grid_options(columnSize="sizeToFit")

    # For specific columns that need custom width
    # gb.configure_column("column_name", minWidth=200)

    # Rest of your code remains the same
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
        useful_first_filter,
        gridOptions=grid_options,
        fit_columns_on_grid_load=True,  # This is important
        allow_unsafe_jscode=True,
        update_mode='SELECTION_CHANGED'
    )

    selected_rows = grid_response['selected_rows']
    selected_df = pd.DataFrame(selected_rows)
    if not selected_df.empty:
        csv_data = convert_df_to_csv(selected_df)
        st.download_button(
            label="Descargar CSV",
            data=csv_data,
            file_name="data.csv",
            mime="text/csv",
            key="second"
        )

        #second_filter = st.expander("Abejas", icon=":material/emoji_nature:")
        #find selected in df and make new df
        selected = useful[useful['_id'].isin(selected_df['ID'])]
        cols_to_keep2 = ['_id','repeat_abejas.repeat_abejas/current_abeja','repeat_abejas.repeat_abejas/num_colmenas_fuertes',
                          'repeat_abejas.repeat_abejas/num_colmenas_estables','repeat_abejas.repeat_abejas/num_colmenas_pequenas',]
        selected = selected.loc[:, cols_to_keep2]
        selected = selected.drop_duplicates()
        secondary = selected.copy()
        cols2 = {
            '_id': 'ID',    
            'repeat_abejas.repeat_abejas/current_abeja': 'Abeja',
            'repeat_abejas.repeat_abejas/num_colmenas_fuertes': 'Número de colmenas fuertes',
            'repeat_abejas.repeat_abejas/num_colmenas_estables': 'Número de colmenas estables',
            'repeat_abejas.repeat_abejas/num_colmenas_pequenas': 'Número de colmenas pequeñas',}
        # Now rename the columns using the columns2 dictionary}
        secondary = secondary.rename(columns=cols2)
        #st.write(selected)
        gb2 = GridOptionsBuilder.from_dataframe(secondary)
        gb2.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            aggFunc='sum',
            filter='agTextColumnFilter',
            # Add these options for better auto-sizing
            resizable=True,
            autoHeight=True,
            wrapText=True,
            # This will make columns fit their content
            autoSizeColumns=True
        )

        # You can also set a minimum width for all columns
        gb2.configure_grid_options(columnSize="sizeToFit")

        # For specific columns that need custom width
        # gb.configure_column("column_name", minWidth=200)

        # Rest of your code remains the same
        gb2.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            header_checkbox=True,
            pre_selected_rows=[],
            suppressRowDeselection=False
        )
        gb2.configure_side_bar(filters_panel=True, defaultToolPanel='filters')
        grid_options = gb2.build()

        grid_response = AgGrid(
            secondary,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,  # This is important
            allow_unsafe_jscode=True,
            update_mode='SELECTION_CHANGED',
            theme='fresh'
        )
        
        secondary_response = grid_response['selected_rows']
        secondary_response_df = pd.DataFrame(secondary_response)
        if not secondary_response_df.empty:
            csv = secondary_response_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name="data.csv",
                mime="text/csv",
                key="thrd"
            )

            # get only where current_abeja is in selected based on id
            selected = useful[useful['_id'].isin(secondary_response_df['ID'])]
            cols_to_keep3 = ['_id','repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod','repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_com_prod',
                             'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores', 'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025',
                             'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/quien_otro']
            selected = selected.loc[:, cols_to_keep3]
            selected = selected.drop_duplicates()
            selected = selected.dropna(subset=['repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod'])
            selected = selected[['_id','repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod','repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_com_prod',
                             'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores', 'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/quien_otro','repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025',
                             ]]
            columns3 = {
                '_id': 'ID',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod': 'Producto',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_com_prod': 'Cantidad comercializada el año anterior',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores': 'Compradores',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/quien_otro': 'Otro comprador',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025': 'Cantidad a producir en el 2025'
            }
            # Now rename the columns using the columns3 dictionary
            selected = selected.rename(columns=columns3)
            #st.write(selected)
            gb3 = GridOptionsBuilder.from_dataframe(selected)
            gb3.configure_default_column(
                groupable=True,
                value=True,
                enableRowGroup=True,
                aggFunc='sum',
                filter='agTextColumnFilter',
                # Add these options for better auto-sizing
                resizable=True,
                autoHeight=True,
                wrapText=True,
                # This will make columns fit their content
                autoSizeColumns=True
            )

            # You can also set a minimum width for all columns
            gb3.configure_grid_options(columnSize="sizeToFit")

            # For specific columns that need custom width
            # gb.configure_column("column_name", minWidth=200)

            # Rest of your code remains the same
            gb3.configure_selection(
                selection_mode="multiple",
                use_checkbox=True,
                header_checkbox=True,
                pre_selected_rows=[],
                suppressRowDeselection=False
            )
            gb3.configure_side_bar(filters_panel=True, defaultToolPanel='filters')
            grid_options = gb3.build()

            grid_response = AgGrid(
                selected,
                gridOptions=grid_options,
                fit_columns_on_grid_load=True,  # This is important
                allow_unsafe_jscode=True,
                update_mode='SELECTION_CHANGED',
                theme='dark'
            )
            
                #gb3.configure_column()
            
            selected_response = grid_response['selected_rows']
            selected3 = pd.DataFrame(selected_response)
            if not selected3.empty:
                csv = selected3.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name="data.csv",
                    mime="text/csv",
                    key="fourth"
                )



        else:
            st.write("No hay filas seleccionadas")

            

    else:
        st.write("No hay filas seleccionadas")

