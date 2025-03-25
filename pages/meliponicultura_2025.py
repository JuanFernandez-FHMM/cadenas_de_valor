import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import utils
import pandas as pd
import plotly.express as px
import io
import re
import numpy as np



utils.logged_in(st.session_state)

def plot_tipo1(dataset, columna, titulo, textposition='auto'):
    plot = px.pie(dataset, names=columna, title=titulo)
    plot.update_traces(
        textposition=textposition,
        textinfo='percent+label+value',
        hole=0.3,
        marker=dict(line=dict(color='#000000', width=2))
    )
    plot.update_traces(hovertemplate='Especie: %{label}<br>Percent: %{percent}<br>Value: %{value}')
    return plot
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
    'estado','municipio','localidad','grupo', 'repeat_persona_edadsexo.repeat_persona_edadsexo/sexo_persona', 'repeat_otros.repeat_otros/sexo',
    'abejas', 'repeat_abejas.repeat_abejas/productos', 'factura','ciclo','pract_conserv', 'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores',
    'repeat_practicas.repeat_practicas/capacitador','convenios', 'repeat_convenios.repeat_convenios/conv_prov','conserv_abejas','alimentacion',
    'acces_ubi', 'infra', 'acom', 'lim', 'herr', 'agro','herr_equipo','trab','auto',
    ]
df2 = df.copy()
columns_to_replace.append('persona')

for col in columns_to_replace:
        
        df[col] = df[col].apply(replace_values)


df.drop(columns=["repeat_persona_edadsexo_count", "repeat_abejas_count",'repeat_practicas_count',
                 'repeat_abejas','repeat_practicas','repeat_convenios_count','repeat_convenios',
                 'repeat_otros_count', 'repeat_otros','repeat_persona_edadsexo','repeat_otros.repeat_otros/curr_persona_nueva',
                 'repeat_abejas.repeat_abejas/com_x_productos'],
                inplace=True)



for col in columns_to_replace:
    if col == 'persona':
        # Split into keys, replace each, and return a list of full names
        df2[col] = df2[col].apply(
            lambda x: [secondtable_dict.get(part, part) for part in str(x).split()] 
            if pd.notnull(x) and isinstance(x, str) 
            else []
        )
    else:
        df2[col] = df2[col].apply(replace_values)

# Explode the persona column to create individual rows per person
df2 = df2.explode('persona')

# Create final personas table
personas_df = df2[['_id', 'localidad', 'grupo','otro_grupo', 'persona']].drop_duplicates().reset_index(drop=True)
#st.write(personas_df)
#st.table(personas_df)

#######################
###### STREAMLIT ######
#######################



st.set_page_config(page_title="Meliponicultura Comercialización 2025", page_icon="data/favicon.ico", layout="wide", initial_sidebar_state="collapsed")
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



st.title("Meliponicultura Comercialización 2025 :honeybee:")

if st.button("Página principal"):
    
    st.switch_page("pagina_principal.py")




########################
##### FIRST TABLE ######
########################
#st.write(secondtable_dict)
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



#########################
##### SECOND TABLE ######
#########################


st.subheader("Filtros")

st.write("Seleccione los filtros que desea aplicar a la tabla principal")

with st.container(border=True):

    useful = df.dropna(subset=['repeat_abejas.repeat_abejas/current_abeja'])

    cols_to_keep = ['_id','localidad', 'grupo', 'otro_grupo', 'persona', 'factura','ciclo', ]

    useful_first_filter = useful.loc[:, cols_to_keep]

    useful_first_filter = useful_first_filter.drop_duplicates(subset=['_id', 'grupo',])

    cols1 = {
        '_id': 'ID',
        'localidad': 'Localidad',
        'grupo': 'Grupo',
        'otro_grupo': 'Otro grupo',
        'persona': 'Persona',
        'factura': 'Factura',
        'ciclo': 'Ciclo de comercialización con TRM',
    }

    # Now rename the columns using the columns1 dictionary
    useful_first_filter = useful_first_filter.rename(columns=cols1)


    ### FIRST AGGRID TABLE ###

    gb = GridOptionsBuilder.from_dataframe(useful_first_filter)

    gb.configure_side_bar(filters_panel=True)

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

    gb.configure_grid_options(columnSize="sizeToFit")

    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=True,
        pre_selected_rows=[],
        header_checkbox=True,
        suppressRowDeselection=False
    )

    grid_options = gb.build()

    grid_response = AgGrid(
        useful_first_filter,
        gridOptions=grid_options,
        fit_columns_on_grid_load=True,  # This is important
        allow_unsafe_jscode=True,
        update_mode='SELECTION_CHANGED',
        theme='fresh'
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


        ### SECOND AGGRID TABLE ###

        useful2_2 = df.dropna(subset=['repeat_practicas.repeat_practicas/current_practica'])

        selected2_2 = useful2_2[useful2_2['_id'].isin(selected_df['ID'])]


        cols_2_keep_second = ['_id','grupo', 'otro_grupo', 'localidad', 'repeat_practicas.repeat_practicas/current_practica','repeat_practicas.repeat_practicas/capacitador','repeat_practicas.repeat_practicas/capacitador_otro']

        useful2 = selected2_2.loc[:, cols_2_keep_second]

        useful2 = useful2.drop_duplicates(subset=['_id', 'grupo', 'repeat_practicas.repeat_practicas/current_practica'])

        cols2_2 = {
            '_id': 'ID',
            'grupo': 'Grupo',
            'localidad': 'Localidad',
            'repeat_practicas.repeat_practicas/current_practica': 'Práctica',
            'repeat_practicas.repeat_practicas/capacitador': 'Capacitador',
            'repeat_practicas.repeat_practicas/capacitador_otro': 'Otro capacitador'
        }

        useful2 = useful2.rename(columns=cols2_2)

        gb2_2 = GridOptionsBuilder.from_dataframe(useful2)

        gb2_2.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            aggFunc='sum',
            filter='agTextColumnFilter',
            resizable=True,
            autoHeight=True,
            wrapText=True,
            autoSizeColumns=True
        )

        gb2_2.configure_grid_options(columnSize="sizeToFit")
        
        gb2_2.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            header_checkbox=True,
            pre_selected_rows=[],
            suppressRowDeselection=False
        )

        gb2_2.configure_side_bar(filters_panel=True)

        grid_options = gb2_2.build()

        grid_response = AgGrid(
            useful2,
            gridOptions=grid_options,
            fit_columns_on_grid_load=True,  # This is important
            allow_unsafe_jscode=True,
            update_mode='SELECTION_CHANGED',
            theme='fresh'
        )

        selected_rows2_2 = grid_response['selected_rows']
        
        selected_df2_2 = pd.DataFrame(selected_rows2_2)

        if not selected_df2_2.empty:

            csv_data2_2 = convert_df_to_csv(selected_df2_2)

            st.download_button(
                label="Descargar CSV",
                data=csv_data2_2,
                file_name="data.csv",
                mime="text/csv",
                key="third2_2"
            )
        


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

        secondary = secondary.rename(columns=cols2)

        gb2 = GridOptionsBuilder.from_dataframe(secondary)

        gb2.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            aggFunc='sum',
            filter='agTextColumnFilter',
            resizable=True,
            autoHeight=True,
            wrapText=True,
            autoSizeColumns=True
        )

        gb2.configure_grid_options(columnSize="sizeToFit")

        gb2.configure_selection(
            selection_mode="multiple",
            use_checkbox=True,
            header_checkbox=True,
            pre_selected_rows=[],
            suppressRowDeselection=False
        )

        gb2.configure_side_bar(filters_panel=True)

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

            
            ### THIRD AGGRID TABLE ###

            selected = useful[useful['_id'].isin(secondary_response_df['ID'])]

            cols_to_keep3 = ['_id','repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod',
                            'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_com_prod',
                            'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores', 
                            'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025',
                            'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/quien_otro']
            
            selected = selected.loc[:, cols_to_keep3]

            selected = selected.drop_duplicates()

            selected = selected.dropna(subset=['repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod'])

            selected = selected[['_id','repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod',
                                 'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_com_prod',
                                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores',
                                  'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/quien_otro',
                                  'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025',
                                ]]
            columns3 = {
                '_id': 'ID',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod': 'Producto',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_com_prod': 'Cantidad comercializada el año anterior',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/compradores': 'Compradores',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/quien_otro': 'Otro comprador',
                'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025': 'Cantidad a producir en el 2025'
            }
            
            
            selected = selected.rename(columns=columns3)

            gb3 = GridOptionsBuilder.from_dataframe(selected)

            gb3.configure_default_column(
                groupable=True,
                value=True,
                enableRowGroup=True,
                aggFunc='sum',
                filter='agTextColumnFilter',
                resizable=True,
                autoHeight=True,
                wrapText=True,
                autoSizeColumns=True
            )

            gb3.configure_grid_options(columnSize="sizeToFit")


            gb3.configure_selection(
                selection_mode="multiple",
                use_checkbox=True,
                header_checkbox=True,
                pre_selected_rows=[],
                suppressRowDeselection=False
            )
            
            gb3.configure_side_bar(filters_panel=True)

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

###########################
#### TABLA DE PERSONAS ####
###########################

# make new df with columns 'id', 'localidad', 'grupo' and 'persona'
# persona will count every different person on the actual df'Persona', they are separated by spaces but names contain spaces in them, so use secondary to extract all different people
# we will have a table for all 'persona' by group, localidad and id

#st.subheader('Productores')
productores = st.expander('Productores',expanded=False,icon=':material/group:')
with productores:
    #st.write('s')
    gb_df = personas_df.copy()
    gb_df.dropna(subset=['persona'],inplace=True)
    gb = GridOptionsBuilder.from_dataframe(gb_df)

    gb.configure_side_bar(filters_panel=True)

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

    gb.configure_grid_options(columnSize="sizeToFit")

    gb.configure_selection(
        selection_mode="multiple",
        use_checkbox=True,
        pre_selected_rows=[],
        header_checkbox=True,
        suppressRowDeselection=False
    )

    grid_options = gb.build()

    grid_response = AgGrid(
        gb_df,
        gridOptions=grid_options,
        fit_columns_on_grid_load=True,  # This is important
        allow_unsafe_jscode=True,
        update_mode='SELECTION_CHANGED',
        theme='fresh'
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

    try:
            # plots
        personas_df['grupo_id'] = personas_df['_id'].astype(str).str[-4:] + ' - ' + personas_df['grupo']

        # Contamos el número de productores por grupo
        conteo_por_grupo = personas_df.groupby(['grupo_id', 'localidad', 'grupo']).size().reset_index(name='cantidad_productores')

        # Ordenamos por cantidad de productores (descendente)
        conteo_por_grupo = conteo_por_grupo.sort_values('cantidad_productores', ascending=False)

        # Gráfico de barras: Número de productores por grupo
        fig1 = px.bar(
            conteo_por_grupo,
            x='grupo_id',
            y='cantidad_productores',
            color='localidad',
            text='cantidad_productores',
            title='Número de Productores por Grupo',
            labels={
                'grupo_id': 'Grupo (ID - Nombre)',
                'cantidad_productores': 'Número de Productores',
                'localidad': 'Localidad'
            },
            color_discrete_sequence=px.colors.qualitative.Vivid,
            height=600
        )

        fig1.update_layout(
            xaxis_tickangle=-45,
            font=dict(size=12)
        )

        # Gráfico de pastel: Distribución de productores por localidad
        conteo_por_localidad = personas_df.groupby('localidad').size().reset_index(name='cantidad_productores')
        fig2 = px.pie(
            conteo_por_localidad,
            values='cantidad_productores',
            names='localidad',
            title='Distribución de Productores por Localidad',
            color_discrete_sequence=px.colors.qualitative.Bold,
            hole=0.3
        )
        fig2.update_traces(textinfo='percent+value')

        # Gráfico de treemap: Jerarquía de localidad -> grupo -> número de productores (valor agregado por slice)
        fig3 = px.treemap(
            personas_df.assign(value=1),  # Asigna el valor '1' a cada productor
            path=['localidad', 'grupo_id'],
            values='value',
            title='Distribución Jerárquica de Productores por Localidad y Grupo',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )

        conteo_grupo_localidad = personas_df.groupby(['localidad', 'grupo_id', 'grupo']).size().reset_index(name='cantidad_productores')

        # Conteo de personas solo por localidad (para el mapa de burbujas)
        conteo_por_localidad = personas_df.groupby('localidad').size().reset_index(name='cantidad_productores')

        # Coordenadas aproximadas para las localidades en la Península de Yucatán (esto debería ser reemplazado con coordenadas reales)
        # Estas son coordenadas ficticias para demostración - necesitarás coordenadas reales para un uso práctico
        coordenadas = {
            "Temozón": {"lat": 20.8046396, "lon": -88.2220431},
            "Granada (Chican Granada)": {"lat": 20.5791081, "lon": -90.0531311},
            "Pakchén": {"lat": 19.5281067, "lon": -89.7985086},
            "Quetzal Edzná": {"lat": 19.459534, "lon":-90.1082347},
            "X-Kanchakán": {"lat": 20.6244424, "lon": -89.5116471},
            "Tixcacaltuyub": {"lat": 20.4920897, "lon": -88.9257571},
            "Tankuché": {'lat':20.5078621, "lon":-90.2484375}
        }

        # Añadir coordenadas al DataFrame
        conteo_por_localidad['lat'] = conteo_por_localidad['localidad'].map(lambda x: coordenadas[x]['lat'])
        conteo_por_localidad['lon'] = conteo_por_localidad['localidad'].map(lambda x: coordenadas[x]['lon'])

        # Crear un mapa de burbujas
        fig = px.scatter_mapbox(
            conteo_por_localidad,
            lat="lat",
            lon="lon",
            size="cantidad_productores",
            color="localidad",
            hover_name="localidad",
            hover_data=["cantidad_productores"],
            title="Distribución de Productores por Localidad",
            mapbox_style="carto-positron",
            zoom=7,
            size_max=30,
            color_discrete_sequence=px.colors.qualitative.Vivid
        )

        # Añadir información sobre los grupos en cada localidad como texto en el hover
        grupos_por_localidad = personas_df.groupby(['localidad', 'grupo_id']).size().reset_index(name='conteo')
        grupos_info = {}

        grupos_por_localidad['localidad_normalized'] = grupos_por_localidad['localidad'].str.strip().str.lower()
        conteo_por_localidad['localidad_normalized'] = conteo_por_localidad['localidad'].str.strip().str.lower()

        # Generate grupos_info with normalized keys
        grupos_info = {}
        for localidad in grupos_por_localidad['localidad_normalized'].unique():
            grupos_localidad = grupos_por_localidad[grupos_por_localidad['localidad_normalized'] == localidad]
            grupos_info[localidad] = "<br>".join([
                f"{row['grupo_id']}: {row['conteo']} productores" 
                for _, row in grupos_localidad.iterrows()
            ])

        fig.update_traces(
            hovertemplate=(
                "<b>%{hovertext}</b><br><br>"
                "Localidad: %{customdata[0]}<br>"
                "Total productores: %{marker.size}<br><br>"
                
            ),
            customdata=[
                [
                    row['localidad'],  # Original localidad name for display
                    grupos_info.get(row['localidad_normalized'], "No hay grupos")
                ] 
                for _, row in conteo_por_localidad.iterrows()
            ]
        )

        fig.update_layout(
            font=dict(family="Arial", size=14),
            title=dict(font=dict(size=20)),
            margin=dict(l=0, r=0, t=40, b=0),
            height=600,
            width=800
        )

        #fig.show()


        columns = st.columns(2)
        with columns[0]:
            st.plotly_chart(fig1)
            st.plotly_chart(fig3)
        with columns[1]:
            st.plotly_chart(fig2)
            st.plotly_chart(fig)
    except:
        st.write('Hubo un error al tratar de generar las gráficas.')


########################
##### PLOTS ###########
########################

#st.subheader("Gráficos")

plots = st.expander("Gráficos", expanded=False,icon=':material/bar_chart:')

with plots:
    try:
        if not df.empty:

            # get data grouped by _id and grupo where repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod is not null
            df_plots = df.dropna(subset=['repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod'])

            plot1df = df_plots.drop_duplicates(subset=['_id', 'grupo'])

            plot1 = plot_tipo1(plot1df, 'localidad', 'Distribución de respuestas por Localidad')
            
            

            bees = df_plots.dropna(subset=['repeat_abejas.repeat_abejas/current_abeja'])

            #bees.drop_duplicates(subset=['_id', 'grupo'], inplace=True)

            plot2 = plot_tipo1(bees,'repeat_abejas.repeat_abejas/current_abeja', 'Distribución de las abejas por tipo')

            
            
            col1,col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot1)
            with col2:
                st.plotly_chart(plot2)

            # Define the KPIs that must always be shown
            required_kpis = ["Miel (l)", "Polen (g)", "Propóleos (g)", "Colmenas (pieza)"]

            # Convert values to integers and sum them
            df_plots["repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025"] = (
                df_plots["repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025"]
                .astype(float)
            )

            # Group by 'current_prod' and sum values
            prod_dict = df_plots.groupby(
                "repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod"
            )["repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025"].sum().to_dict()

            # Function to display a metric
            def make_metric(label, value):
                st.metric(label=label, value=value)

                # Layout columns for KPIs
            cols = st.columns(len(required_kpis))

            for i, kpi in enumerate(required_kpis):
                value = prod_dict.get(kpi, 0)  # Get sum from grouped dict, or default to 0
                with cols[i]:
                    make_metric(kpi, value)
            # histogram for prods based on df_plots with repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025 on y and repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod on x
            #transform _id to string to avoid error
            df_plots['_id'] = df_plots['_id'].astype(str)
            # extract what is inside parenthesis in current_prod as new col called type
            

            regex = r"\((.*?)\)"

            df_plots['type'] = df_plots['repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod'].apply(lambda x: re.search(regex, x).group(1) if re.search(regex, x) else None)
            

            # plot where prod is = 'Polen (g)'

            plot3df = df_plots[df_plots['type'] == 'g']
            # drop where prod_2025 is null
            plot3df = plot3df.dropna(subset=['repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025'])
            # drop where cant_prod_2025 is 0
            plot3df = plot3df[plot3df['repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025'] != '0']

            # First, create a mapping from _id to grupo name
            id_to_group = dict(zip(plot3df['_id'], plot3df['grupo']))

            # Create the plot using _id for color
            plot3 = px.histogram(
                plot3df,
                hover_data='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025',
                x='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod',
                y='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025', 
                title='Cantidad de polen y propóleos a cosechar en 2025', 
                color='_id',  # Use _id for color
                labels={
                    'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025': 'Cantidad a cosechar en 2025',
                    'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod': 'Producto'
                },
                facet_col='grupo'
            )

            # Update the color legend labels
            for i, id_val in enumerate(plot3.data):
                if hasattr(id_val, 'name') and id_val.name in id_to_group:
                    id_val.name = id_to_group[id_val.name]  # Replace ID with group name in legend

            # Or alternatively, you can update the entire legend
            plot3.update_layout(
                legend_title_text='Grupo',
                legend=dict(
                    itemsizing='constant',
                    title_font=dict(size=12),
                    font=dict(size=10)
                )
            )

            st.plotly_chart(plot3)

            # plot where prod is = 'Miel (L)'
            plot4df = df_plots[df_plots['type'] == 'l']
            id_to_group_4 = dict(zip(plot4df['_id'], plot4df['grupo']))

            # Create the plot using _id for color
            plot4 = px.histogram(
                plot4df,
                hover_data='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025',
                x='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod',
                y='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025', 
                title='Cantidad de miel a cosechar en 2025', 
                color='_id',  # Use _id for color
                labels={
                    'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025': 'Cantidad a cosechar en 2025',
                    'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod': 'Producto'
                },
                facet_col='grupo'
            )

            # Update the color legend labels
            for i, id_val in enumerate(plot4.data):
                if hasattr(id_val, 'name') and id_val.name in id_to_group_4:
                    id_val.name = id_to_group_4[id_val.name]

            # Update legend layout
            plot4.update_layout(
                legend_title_text='Grupo',
                legend=dict(
                    itemsizing='constant',
                    title_font=dict(size=12),
                    font=dict(size=10)
                )
            )

            st.plotly_chart(plot4)

            #plot where type is pieza
            plot5df = df_plots[df_plots['type'] == 'pieza']
            id_to_group_5 = dict(zip(plot5df['_id'], plot5df['grupo']))

            # Create the plot using _id for color
            plot5 = px.histogram(
                plot5df,
                hover_data='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025',
                x='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod',
                y='repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025', 
                title='Cantidad de colmenas a cosechar en 2025', 
                color='_id',  # Use _id for color
                labels={
                    'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/cant_prod_2025': 'Cantidad a cosechar en 2025',
                    'repeat_abejas.repeat_abejas/com_x_productos.repeat_abejas/com_x_productos/current_prod': 'Producto'
                },
                facet_col='grupo'
            )

            # Update the color legend labels
            for i, id_val in enumerate(plot5.data):
                if hasattr(id_val, 'name') and id_val.name in id_to_group_5:
                    id_val.name = id_to_group_5[id_val.name]

            # Update legend layout
            plot5.update_layout(
                legend_title_text='Grupo',
                legend=dict(
                    itemsizing='constant',
                    title_font=dict(size=12),
                    font=dict(size=10)
                )
            )

            st.plotly_chart(plot5)



        else:
            st.write("No hay datos para mostrar")

    except Exception as e:
        st.write(f"Ocurrió un error: {e}")