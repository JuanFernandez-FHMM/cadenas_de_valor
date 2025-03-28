import streamlit as st 
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd
import utils
import plotly.express as px
import re
import io
import json

utils.logged_in(st.session_state)

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

def parse_grain_data(data):
    """
    Parse JSON data into a normalized structure with main records and detail records
    """
    # Extract main record information
    main_record = {
        'ID': data.get('_id'),
        'Fecha_registro': data.get('start', '').split('T')[0] if 'start' in data else None,
        'Momento_registro': data.get('momento_registro'),
        'Productor': data.get('productor'),
        'Aval': data.get('aval'),
    }
    
    # Create a list to hold variety details
    variety_details = []
    
    # Get the list of varieties
    variety_list = data.get('variedad', '').split()
    
    # Process each variety entry in the repeated group
    for idx, var_entry in enumerate(data.get('variedad_repeat', [])):
        # Get the bag tests for this variety
        for bag_test in var_entry.get('variedad_repeat/bolsas_test', []):
            # Create a record for this variety test
            detail = {
                'ID': data.get('_id'),
                'Variedad_code': variety_list[idx] if idx < len(variety_list) else None,
                'Folio': bag_test.get('variedad_repeat/bolsas_test/bolsa_folio', ''),
                'Folio_input': bag_test.get('variedad_repeat/bolsas_test/folio_input', ''),
                'Humedad': bag_test.get('variedad_repeat/bolsas_test/humedad', ''),
                'Granos_quebrados': bag_test.get('variedad_repeat/bolsas_test/granos_quebrados', ''),
                'Impurezas': bag_test.get('variedad_repeat/bolsas_test/impurezas', ''),
                'Color_uniforme': bag_test.get('variedad_repeat/bolsas_test/color_uniforme', ''),
                'Olor': bag_test.get('variedad_repeat/bolsas_test/olor', ''),
                'Peso_bruto': bag_test.get('variedad_repeat/bolsas_test/peso_bruto', ''),
                'Comentarios': bag_test.get('variedad_repeat/bolsas_test/comentarios', '')
            }
            variety_details.append(detail)
    
    return main_record, variety_details

def reconstruct_original_format(main_df, detail_df):
    """
    Reconstruct the original format with comma-separated values from the normalized structure
    """
    # Group by ID
    grouped = main_df.copy()
    
    # For each ID, collect the detail records and format them as comma-separated values
    for id_val in grouped['ID'].unique():
        details = detail_df[detail_df['ID'] == id_val]
        
        if not details.empty:
            # Collect comma-separated values for each column
            for col in ['Folio_input', 'Humedad', 'Granos_quebrados', 'Impurezas', 
                       'Color_uniforme', 'Olor', 'Peso_bruto', 'Comentarios']:
                detail_col = col
                main_col = col if col != 'Folio_input' else 'Folio de las bolsas'
                
                values = details[detail_col].dropna().astype(str).tolist()
                grouped.loc[grouped['ID'] == id_val, main_col] = ', '.join(values)
            
            # Correctly reconstruct 'Variedad' by collecting all codes from details
            variedad_codes_in_details = details['Variedad_code'].tolist()
            variedad_names_in_details = [secondtable_dict.get(code, code) for code in variedad_codes_in_details]
            variedad_str = ' '.join(variedad_names_in_details)
            grouped.loc[grouped['ID'] == id_val, 'Variedad'] = variedad_str
    
    return grouped

# Main code
tablename = 'muestreo_calidad_maiz'
secondtable = 'muestreo_calidad_maiz_data'

flat_data, second_table = utils.start_(tablename, secondtable=secondtable)

if second_table:
    secondtable_dict = dict(second_table)
else:
    secondtable_dict = {}

# Process data into normalized structure
main_records = []
detail_records = []

for record in flat_data:
    main_record, variety_details = parse_grain_data(record)
    main_records.append(main_record)
    detail_records.extend(variety_details)

# Create DataFrames
main_df = pd.DataFrame(main_records)
detail_df = pd.DataFrame(detail_records)

# Apply replacements to main_df values
columns_to_replace = ['Momento_registro', 'Productor']
for col in columns_to_replace:
    if col in main_df.columns:
        main_df[col] = main_df[col].apply(replace_values)

# Apply replacements to variety codes in detail_df
if 'Variedad_code' in detail_df.columns:
    detail_df['Variedad_name'] = detail_df['Variedad_code'].apply(replace_values)

# Reconstruct the original format for display and visualization
grouped = reconstruct_original_format(main_df, detail_df)

# Rename columns
cols = {
    "ID": "ID",
    'Fecha_registro': 'Fecha del registro',
    "Momento_registro": "Momento del registro",
    "Productor": "Productor",
    "Variedad_code": "Variedad",
    "Firma_productor": "Firma del productor",
    "Aval": "Aval",
    "Firma_aval": "Firma del aval",
    "Folio_input": "Folio de las bolsas",
    "Humedad": "Humedad",
    "Granos_quebrados": "Granos quebrados",
    "Impurezas": "Impurezas",
    "Color_uniforme": "Color uniforme",
    "Olor": "Olor",
    "Peso_bruto": "Peso bruto",
    "Comentarios": "Comentarios",
}

# Apply renaming to both DataFrames
main_df.rename(columns={k: v for k, v in cols.items() if k in main_df.columns}, inplace=True)
detail_df.rename(columns={k: v for k, v in cols.items() if k in detail_df.columns}, inplace=True)
grouped.rename(columns={k: v for k, v in cols.items() if k in grouped.columns}, inplace=True)


# Add this column reordering logic:
desired_column_order = [
    "ID",
    "Fecha del registro",
    "Momento del registro",
    "Productor",
    "Variedad",  # Now placed after Productor
    "Firma del productor",
    "Aval",
    "Firma del aval",
    "Folio de las bolsas",
    "Humedad",
    "Granos quebrados",
    "Impurezas",
    "Color uniforme",
    "Olor",
    "Peso bruto",
    "Comentarios",
    "Submission_time"  # Include if present
]

# Filter only columns that actually exist in the DataFrame
existing_columns = [col for col in desired_column_order if col in grouped.columns]
additional_columns = [col for col in grouped.columns if col not in existing_columns]

# Create final ordered column list
final_columns = existing_columns + additional_columns

# Reindex the DataFrame
grouped = grouped[final_columns]

# Format date and other fields
if 'Fecha del registro' in grouped.columns:
    grouped["Fecha del registro"] = pd.to_datetime(grouped["Fecha del registro"], errors="coerce").dt.strftime("%d-%m-%Y")

# Fix spaces in Folio column if needed
if 'Folio de las bolsas' in grouped.columns:
    grouped["Folio de las bolsas"] = grouped["Folio de las bolsas"].apply(lambda x: " ".join(str(x).split(" ")) if isinstance(x, str) else x)

# Streamlit UI
st.set_page_config(page_title="Muestreo de calidad de maiz", page_icon="data/favicon.ico", layout="wide", initial_sidebar_state="collapsed")
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



st.title("Muestreo de calidad de maiz :corn:")

if st.button("Página principal"):
    st.switch_page("pagina_principal.py")

# Configure AgGrid
gb = GridOptionsBuilder.from_dataframe(grouped)

gb.configure_side_bar(filters_panel=True)

gb.configure_default_column(
    groupable=True,
    value=True,
    enableRowGroup=True,
    aggFunc='sum',
    filter='agTextColumnFilter',
    resizable=True,
    autoHeight=True,
    wrapText=True,
    autoSizeColumns=True,
    suppressSizeToFit=True
)

gb.configure_selection(
    selection_mode="multiple",
    use_checkbox=True,
    pre_selected_rows=[],
    header_checkbox=True,
    suppressRowDeselection=False
)

grid_options = gb.build()

grid_response = AgGrid(
    grouped,
    gridOptions=grid_options,
    fit_columns_on_grid_load=True,
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

# Plots section
plots_exp = st.expander("Gráficas generales", icon=":material/bar_chart:")

variedades = [
    "Chac Chob Rojo",
    "Dzitbacal Amarillo",
    "Dzitbacal Blanco",
    "Eh Hub Morado",
    "Xnuuk Naal Amarillo",
    "Xnuuk Naal Blanco",
    "Xnuuk Naal Mixto O Pinto",
    "Naal Teel Amarillo",
    "Naal Teel Blanco",
    "Naal Xooy Amarillo",
    "Naal Xooy Blanco",
    "Sac Tux Blanco",
    "Santa Rosa Amarillo",
    "Santa Rosa Blanco",
    "Santa Rosa Mixto O Pinto",
    "Xmejen Naal Amarillo",
    "Xmejen Naal Blanco",
    "Chichen Itza Amarillo",
    "Sac-Beh Blanco",
]


table2 = st.expander('Producción', icon=":material/inventory_2:")
sorted_variedades = sorted(variedades, key=lambda x: len(x), reverse=True)

def split_variedad(s):
    s = str(s).strip()
    varieties = []
    remaining = s
    while remaining:
        found = False
        for var in sorted_variedades:
            if remaining.startswith(var):
                varieties.append(var)
                remaining = remaining[len(var):].strip()
                found = True
                break
        if not found:
            # Handle unmatched parts; appends an error indicator for visibility
            varieties.append(f"ERROR:{remaining}")
            break
    return varieties

# Read the dataset


# Columns to split into lists
list_columns = [
    'Folio de las bolsas',
    'Humedad',
    'Granos quebrados',
    'Impurezas',
    'Color uniforme',
    'Olor',
    'Peso bruto',
    'Comentarios'
]



# Process 'Variedad' column
grouped['Variedad'] = grouped['Variedad'].apply(split_variedad)

# Process list columns by splitting comma-separated values and handle NaNs
for col in list_columns:
    # Fill NaN with appropriate defaults before splitting
    if col == 'Comentarios':
        # Replace NaN with 'Sin comentarios' to ensure one entry
        grouped[col] = grouped[col].fillna('Sin comentarios')
    else:
        # For other columns, fill NaN with empty string to split into empty list
        grouped[col] = grouped[col].fillna('')
    # Split into list of items
    grouped[col] = grouped[col].apply(
        lambda x: [item.strip() for item in str(x).split(',')] if x else []
    )

# Adjust each list column to match 'Variedad' length
def adjust_list_length(row, col):
    var_len = len(row['Variedad'])
    current_list = row[col]
    current_len = len(current_list)
    
    if current_len < var_len:
        # Pad with default values
        fill_value = 'Sin comentarios' if col == 'Comentarios' else ''
        return current_list + [fill_value] * (var_len - current_len)
    elif current_len > var_len:
        # Truncate to match 'Variedad' length
        return current_list[:var_len]
    else:
        return current_list

for col in list_columns:
    grouped[col] = grouped.apply(lambda row: adjust_list_length(row, col), axis=1)


# Explode all relevant columns to create individual rows
explode_cols = ['Variedad'] + list_columns
grouped_exploded = grouped.explode(explode_cols)

# Convert numeric columns to appropriate data types
numeric_cols = ['Humedad', 'Granos quebrados', 'Impurezas', 'Color uniforme', 'Peso bruto']
for col in numeric_cols:
    grouped_exploded[col] = pd.to_numeric(grouped_exploded[col], errors='coerce')

# Handle empty strings in 'Comentarios'
grouped_exploded['Comentarios'] = grouped_exploded['Comentarios'].replace('', pd.NA)

# Drop the temporary length columns if they were created
if 'Variedad_length' in grouped_exploded.columns:
    grouped_exploded.drop(columns=['Variedad_length'] + [f'{col}_length' for col in list_columns], errors='ignore', inplace=True)

# Reset index for a clean output
grouped_exploded.reset_index(drop=True, inplace=True)
grouped_exploded.drop(columns=['ID'],inplace=True)

validation_rules = {
    "Humedad": {"max": 11.5},          # Must be ≤ 11.5%
    "Granos quebrados": {"max": 1.0},  # Must be ≤ 1.0%
    "Impurezas": {"max": 1.0},         # Must be ≤ 1.0%
    "Color uniforme": {"min": 98.0},   # Must be ≥ 98.0%
    "Olor": {"valid_values": ["OK"]},  # Must be "OK"
    "Peso bruto": {"min": 25.2}        # Must be ≥ 25.2 kg
}

def colorize_value(val, column_name):
    if pd.isna(val):
        return "background-color: red"  # Missing values fail
    
    rule = validation_rules.get(column_name, {})
    
    # Numeric checks
    if "max" in rule:
        return "background-color: #d0f0ca" if val <= rule["max"] else "background-color: #e97c58"
    elif "min" in rule:
        return "background-color: #d0f0ca" if val >= rule["min"] else "background-color: #e97c58"
    
    # Categorical checks (e.g., "Olor")
    if "valid_values" in rule:
        return "background-color: #d0f0ca" if val in rule["valid_values"] else "background-color: #e97c58"
    
    return ""  # No styling for other columns

# Apply styling to relevant columns
styled_df = (
    grouped_exploded.style
    .applymap(lambda x: colorize_value(x, "Humedad"), subset=["Humedad"])
    .applymap(lambda x: colorize_value(x, "Granos quebrados"), subset=["Granos quebrados"])
    .applymap(lambda x: colorize_value(x, "Impurezas"), subset=["Impurezas"])
    .applymap(lambda x: colorize_value(x, "Color uniforme"), subset=["Color uniforme"])
    .applymap(lambda x: colorize_value(x, "Olor"), subset=["Olor"])
    .applymap(lambda x: colorize_value(x, "Peso bruto"), subset=["Peso bruto"])
    .set_table_styles([{
        "selector": "td",
        "props": [("text-align", "center"), ("padding", "5px")]
    }])
)

to_join = utils.read_data_1('milpa_sustentable')

# Create a DataFrame from to_join with appropriate column names
df_to_join = pd.DataFrame(to_join, columns=["Productor", "Variedad", "A vender"])

# Join the DataFrame on "Productor" and "Variedad" and update grouped_exploded
grouped_exploded = grouped_exploded.merge(df_to_join, on=["Productor", "Variedad"], how="left")
grouped_exploded["A vender"] = grouped_exploded["A vender"].fillna("Sin información")



with table2:
    # Define improved color scheme
    GROUP_COLOR = "#b9d6c7"  # Very pale green for group background
    PASS_COLOR = "#d0f0ca"   # Darker green with better contrast
    FAIL_COLOR = "#f59d7f"   # Light red

    # Custom CSS for better visibility
    st.markdown(f"""
        <style>
            .dataframe td {{
                color: black !important;
                font-weight: 500;
            }}
            .dataframe th {{
                background-color: {GROUP_COLOR} !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    def style_groups_and_validation(df):
        # Initialize style DataFrame
        styles = pd.DataFrame('', index=df.index, columns=df.columns)
        current_producer = None
        
        for idx, row in df.iterrows():
            # Add group background for producer
            if row['Productor'] != current_producer:
                styles.iloc[idx] = f'background-color: {GROUP_COLOR}; border-top: 2px solid white;'
                current_producer = row['Productor']
            
            # Apply validation colors
            for col in validation_rules.keys():
                val = row[col]
                rule = validation_rules[col]
                
                if pd.isna(val):
                    styles.loc[idx, col] = f'background-color: {FAIL_COLOR};'
                    continue
                    
                if col == 'Olor':
                    valid = val in rule['valid_values']
                elif 'max' in rule:
                    valid = val <= rule['max']
                elif 'min' in rule:
                    valid = val >= rule['min']
                    
                color = PASS_COLOR if valid else FAIL_COLOR
                styles.loc[idx, col] = f'background-color: {color}; font-weight: bold;'
                
        return styles

    # Apply styling
    styled_df = (
        grouped_exploded.style
        .apply(style_groups_and_validation, axis=None)
        .format(precision=2)
        .set_properties(**{'text-align': 'center', 'padding': '8px'})
        .set_table_styles([{
            'selector': 'td',
            'props': [('border', '1px solid white')]
        }])
    )

    # Display in Streamlit
    st.title("Control de calidad")


    st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)



plots_exp = st.expander("Gráficas generales", icon=":material/bar_chart:")

try:
    plot_df = grouped.copy()
    
    with plots_exp:
        cols = st.columns(2)
        
        with cols[0]:
            pie1 = px.pie(plot_df, 'Momento del registro', title='Distribución del momento de registro',color='Momento del registro')
            st.plotly_chart(pie1)

        with cols[1]:
            variedad_counts = {}
            for variedad in variedades:
                count_in_detail = detail_df['Variedad_name'].str.contains(variedad, case=False, na=False).sum()
                count_in_grouped = plot_df['Variedad'].str.count(variedad, flags=re.IGNORECASE).sum()
                count = max(count_in_detail, count_in_grouped)
                if count > 0:
                    variedad_counts[variedad] = int(count)
            
            if variedad_counts:
                bar1 = px.bar(
                    x=list(variedad_counts.keys()),
                    y=list(variedad_counts.values()),
                    labels={'x': 'Variedad', 'y': 'Conteo'},
                    title='Conteo de variedades',
                    color=list(variedad_counts.keys())
                )
                st.plotly_chart(bar1)

        st.subheader("Cumplimiento Individual por Productor")
        metrics_info = {
            'Humedad': {'threshold': 11.5, 'condition': '≤', 'unit': '%'},
            'Granos quebrados': {'threshold': 1.0, 'condition': '≤', 'unit': '%'},
            'Impurezas': {'threshold': 1.0, 'condition': '≤', 'unit': '%'},
            'Color uniforme': {'threshold': 98.0, 'condition': '≥', 'unit': '%'},
            'Peso bruto': {'threshold': 25.2, 'condition': '≥', 'unit': 'kg'},
            'Olor': {'threshold': 'OK', 'condition': '=', 'unit': ''}
        }

        compliance_data = []
        productores = main_df['Productor'].unique()
        
        for productor in productores:
            productor_ids = main_df[main_df['Productor'] == productor]['ID'].tolist()
            tests = detail_df[detail_df['ID'].isin(productor_ids)]
            entry = {'Productor': productor}
            
            for metric in ['Humedad', 'Granos quebrados', 'Impurezas', 'Color uniforme', 'Peso bruto']:
                avg = pd.to_numeric(tests[metric], errors='coerce').mean()
                if metric in ['Color uniforme', 'Peso bruto']:
                    compliant = avg >= metrics_info[metric]['threshold'] if not pd.isna(avg) else False
                else:
                    compliant = avg <= metrics_info[metric]['threshold'] if not pd.isna(avg) else False
                entry[f'{metric}_avg'] = avg
                entry[f'{metric}_compliant'] = compliant
            
            olor_compliant = all(prueba == 'OK' for prueba in tests['Olor'].dropna())
            entry['Olor_compliant'] = olor_compliant
            compliance_data.append(entry)

        compliance_df = pd.DataFrame(compliance_data)
        cols_pies = st.columns(3)
        
        for idx, metric in enumerate(metrics_info):
            metric_data = []
            for _, row in compliance_df.iterrows():
                avg_value = row.get(f'{metric}_avg', 'N/A')
                compliant = row.get(f'{metric}_compliant' if metric != 'Olor' else 'Olor_compliant', False)
                #st.write(compliance_df)
                hover_text = (
                    f"Productor: {row['Productor']}<br>"
                    f"Valor: {avg_value}{metrics_info[metric]['unit'] if metric != 'Olor' else compliance_df['Olor_compliant'][_]}<br>"
                    f"Cumple: {'Sí' if compliant else 'No'}"
                )
                metric_data.append({
                    'Productor': row['Productor'],
                    'Cumple': 'Cumple' if compliant else 'No cumple',
                    'Hover': hover_text
                })
            
            df_pie = pd.DataFrame(metric_data)
            title = f"{metric} ({metrics_info[metric]['condition']} {metrics_info[metric]['threshold']}{metrics_info[metric]['unit']})"
            fig = px.pie(
                df_pie,
                names='Productor',
                color='Cumple',
                color_discrete_map={'Cumple': '#00C853', 'No cumple': '#FF1744'},
                title=title,
                hover_name='Hover',
                #hover_data='Hover',
                hole=0.35
            )
            fig.update_traces(
                textposition='auto',
                textinfo='label+value',
                marker=dict(line=dict(color='white', width=1)))
            fig.update_layout(showlegend=False, uniformtext_minsize=10)
            
            with cols_pies[idx % 3]:
                st.plotly_chart(fig, use_container_width=True)
            
            if (idx + 1) % 3 == 0:
                cols_pies = st.columns(3)

except Exception as e:
    st.warning(f"Error generando visualizaciones: {str(e)}")

# KPI section
kpis_personales = st.expander("Métricas personales", icon=':material/person:')

with kpis_personales:
    if not selected_df.empty:
        if len(selected_df['Productor'].unique()) == 1:
            try:
                moment_options = grouped['Momento del registro'].dropna().unique().tolist()
                selected_moment = st.selectbox("Selecciona el momento del registro", ["Selecciona una opción"] + moment_options)

                if selected_moment == "Selecciona una opción":
                    raise ValueError("Momento del registro no seleccionado")

                filtered_moment_df = grouped[grouped['Momento del registro'] == selected_moment]

                try:
                    date_options = filtered_moment_df['Fecha del registro'].dropna().unique().tolist()
                    selected_dates = st.multiselect("Selecciona la(s) fecha(s) de registro", date_options)

                    if not selected_dates:
                        raise ValueError("Fecha del registro no seleccionada")

                    filtered_df = filtered_moment_df[filtered_moment_df['Fecha del registro'].isin(selected_dates)]
                    if filtered_df.empty:
                        st.warning("No hay datos disponibles para los filtros seleccionados.")
                        st.stop()

                    metrics = {}
                    producer_name = selected_df['Productor'].iloc[0]
                    metrics['Nombre'] = producer_name

                    filtered = filtered_df[filtered_df['Productor'] == producer_name]
                    
                    producer_ids = filtered['ID'].unique().tolist()
                    producer_detail_df = detail_df[detail_df['ID'].isin(producer_ids)]
                    
                    # Get unique varieties from both sources
                    detail_variedades = producer_detail_df['Variedad_name'].unique().tolist()
                    main_variedades = filtered['Variedad'].str.split().explode().unique().tolist()
                    unique_variedades = list(set(detail_variedades + main_variedades))
                    
                    variedad_selected = st.multiselect("Selecciona la(s) variedad(es)", detail_variedades)
                    
                    try:
                        if variedad_selected:
                            # Filter both dataframes
                            filtered = filtered[filtered['Variedad'].apply(lambda x: any(v in str(x).split() for v in variedad_selected))]
                            producer_detail_df = producer_detail_df[producer_detail_df['Variedad_name'].isin(variedad_selected)]
                        
                        # Calculate metrics using filtered data
                        metrics['Variedades analizadas'] = {
                            var: producer_detail_df['Variedad_name'].value_counts().get(var, 0) 
                            for var in (variedad_selected if variedad_selected else detail_variedades)
                        }

                        aval_values = filtered['Aval'].dropna().unique().tolist()
                        metrics['Avales'] = aval_values
                        
                        columns_mean = ['Humedad', 'Granos quebrados', 'Impurezas', 'Color uniforme', 'Peso bruto']
                        for col in columns_mean:
                            values = []
                            # Get values from detailed tests
                            if col in producer_detail_df.columns:
                                values.extend(producer_detail_df[col].dropna().astype(float).tolist())
                            # Get values from main entries
                            for cell in filtered[col].dropna():
                                values.extend([float(v.strip()) for v in str(cell).split(',') if v.strip()])
                            
                            if values:
                                metrics[f'Promedio de {col.lower()}'] = sum(values) / len(values)
                            else:
                                metrics[f'Promedio de {col.lower()}'] = None

                        st.subheader(f"Información del productor: {producer_name}")

                        if metrics['Variedades analizadas']:
                            st.markdown("**Variedades analizadas**")
                            st.table(pd.DataFrame(metrics["Variedades analizadas"].items(), columns=["Variedad", "Bolsas analizadas"]))

                        if metrics.get('Avales'):
                            st.markdown("**Avales**")
                            st.table(pd.DataFrame(metrics['Avales'], columns=["Aval"]))

                        thresholds = {
                            'Promedio de humedad': 11.5,
                            'Promedio de granos quebrados': 1.0,
                            'Promedio de impurezas': 1.0,
                            'Promedio de color uniforme': 98.0,
                            'Promedio de peso bruto': 25.2,
                        }
                        
                        metric_keys = [
                            'Promedio de humedad',
                            'Promedio de granos quebrados',
                            'Promedio de impurezas',
                            'Promedio de color uniforme',
                            'Promedio de peso bruto'
                        ]

                        cols = st.columns(3)
                        for idx, key in enumerate(metric_keys):
                            if metrics.get(key) is not None:
                                actual = metrics[key]
                                allowed = thresholds[key]
                                delta = actual - allowed
                                value_str = f"{actual:.2f} kg" if key == 'Promedio de peso bruto' else f"{actual:.2f}%"
                                delta_str = f"{delta:.2f} kg" if key == 'Promedio de peso bruto' else f"{delta:.2f}%"
                                label = key.replace("Promedio de ", "").capitalize()
                                delta_color = "inverse" if key in ['Promedio de humedad', 'Promedio de granos quebrados', 'Promedio de impurezas'] else "normal"
                                cols[idx % 3].metric(label=label, value=value_str, delta=delta_str, delta_color=delta_color)

                        with cols[2]:
                            st.metric('Olor', value='OK', delta='100%')
                                
                    except Exception as e:
                        st.warning('Selecciona la o las variedades.')

                except ValueError as e:
                    st.warning(f"Selecciona un valor en el filtro 'Fecha del registro' para visualizar la información.")

            except ValueError as e:
                st.warning(f"Selecciona un valor en el filtro 'Momento del registro' para visualizar la información.")

        else:
            st.warning('Selecciona solo un productor a la vez para visualizar este tipo de información.')
    else:
        st.warning('Selecciona a un solo productor para obtener sus métricas personales.')