import streamlit as st
import os
from supabase import create_client, Client
from streamlit_option_menu import option_menu
from time import sleep

st.set_page_config(
    page_title="Sistema de Proyectos Comunitarios",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': 'https://www.example.com/bug',
        'About': 'Sistema de gestión para Proyectos Comunitarios'
    },
    
)

# Custom theme colors
primary_color = "#4CAF50"  # Green shade for community/ecological theme

# Apply custom styles
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    [data-testid="stHeader"] {
        background-color: #f0f8f0;
    }
</style>
""", unsafe_allow_html=True)

url: str = st.secrets.supabase.url
key: str = st.secrets.supabase.key
supabase: Client = create_client(url, key)

# --- FUNCIONALIDAD DE LOGIN ---
def login_section():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        cols = st.columns([1, 2, 1])
        with cols[1]:
            st.title("Sistema de Proyectos Comunitarios 🌱")
            
            # Create a visually appealing login card
            with st.container():
                st.subheader("Acceso al Sistema 🔒")
                
                # Create tabs for login methods (even if we only use password for now)
                tab1, tab2 = st.tabs(["Acceso con Contraseña", "Información"])
                
                with tab1:
                    with st.form("login_form"):
                        password = st.text_input("Contraseña de acceso:", type="password")
                        submit = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
                        
                        if submit:
                            if password == st.secrets.login_credentials.psswrd:
                                st.session_state.logged_in = True
                                st.rerun()
                            else:
                                st.error("Contraseña incorrecta. Intente nuevamente.")
                

                with tab2:
                    st.info("Este sistema permite gestionar y visualizar proyectos comunitarios. Para acceder necesita la contraseña proporcionada por el administrador. Si la necesitas ponte en contacto con juan.fernandez@fhmm.org o david.contreras@fhmm.org")
        return True
    return False

if login_section():
    st.stop()

# Main navigation section after login
st.title("Sistema de Proyectos Comunitarios 🌱")




# Display a status indicator for logged-in user
with st.sidebar:
    st.success("✅ Usuario autenticado")
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.rerun()

# Create top navigation with option_menu
selected = option_menu(
    menu_title=None,
    options=["Proyectos", "Documentación", "Contacto"],
    icons=["folder", "book", "envelope"],
    menu_icon="list",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#f0f8f0"},
        "icon": {"color": primary_color, "font-size": "18px"},
        "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": primary_color},
    }
)

if selected == "Proyectos":

    
    st.info("Seleccione un proyecto para ver sus detalles.")
    st.divider()

    # Create a visually enhanced container for navigation
    with st.container():
        st.subheader("Navegación de Proyectos")
        
        pages_dir = "pages"
        if not os.path.exists(pages_dir):
            st.error("No se encontró el directorio 'pages'. Favor de notificar al administrador.")
        else:
            page_files = [f for f in os.listdir(pages_dir) if f.endswith(".py")]
            
            if not page_files:
                st.warning("No se encontraron páginas en el directorio 'pages'.")
            else:
                # Use simple container with borders for better visual organization
                with st.container(border=True):
                    # Create a grid of 3 columns for buttons
                    cols = st.columns(3)
                    
                    # Distribute buttons across columns
                    for idx, file in enumerate(sorted(page_files)):
                        page_name = file.replace(".py", "").replace("_", " ").capitalize()
                        col_idx = idx % 3
                        
                        # Place button in the appropriate column with improved styling
                        with cols[col_idx]:
                            # Use a container to add padding and spacing around each button
                            with st.container():
                                # Standard streamlit button with use_container_width
                                if st.button(f"📁 {page_name}", 
                                            key=f"btn_{idx}", 
                                            use_container_width=True):
                                    try:
                                        st.switch_page(f"pages/{file}")
                                    except Exception as e:
                                        st.error(f"Error navigating to {page_name}: {str(e)}")
                                        st.info("Please try again or reload the page.")
                            
                            # Add some space between buttons
                            st.write("")

elif selected == "Documentación":
    st.header("Documentación y Ayuda 📚")
    
    # Video tutorial section
    with st.expander("Guía para el uso de la plataforma", expanded=False):
        video_url = "https://www.youtube.com/watch?v=Ukre4MMCQfo"
        st.video(video_url)
    
   

elif selected == "Contacto":
    st.header("Contacto y Soporte 📧")
    
    contact_cols = st.columns([3,1])
    with contact_cols[0]:
        st.subheader("Formulario de Contacto")
        
        with st.form("contact_form"):
            name = st.text_input("Nombre", key="contact_name")
            email = st.text_input("Correo electrónico", key="contact_email")
            inquiry_type = st.selectbox("Tipo de consulta", ["Soporte técnico", "Información general", "Reportar un error"])
            message = st.text_area("Mensaje", height=150)
            submit = st.form_submit_button("Enviar consulta")
            
            if submit:
                # Basic validation
                if not name or not email or not message:
                    st.error("Por favor complete todos los campos obligatorios")
                else:
                    try:
                        # Create data dictionary
                        data = {
                            "name": name.strip(),
                            "email": email.strip(),
                            "inquiry_type": inquiry_type,
                            "message": message.strip()
                        }
                        
                        # Insert into Supabase
                        response = supabase.table('contact_queries').insert(data).execute()
                        
                        if len(response.data) > 0:
                            st.success("Consulta enviada exitosamente! Nos pondremos en contacto pronto.")
                        else:
                            st.error("Error al enviar la consulta. Por favor intente nuevamente.")
                    except Exception as e:
                        st.error(f"Error en el sistema: {str(e)}")
    
    with contact_cols[1]:
        st.subheader("Información de Contacto")
        st.info("""    
        - juan.fernandez@fhmm.org
        - david.contreras@fhmm.org
        """)
        
        st.divider()
        st.subheader("Área de Admin")
        
        admin_pass = st.text_input("Contraseña admin:", type="password")
        
        if 'admin_authenticated' not in st.session_state:
            st.session_state.admin_authenticated = False
            
        if admin_pass or st.session_state.admin_authenticated:
            if admin_pass == st.secrets.admin.password or st.session_state.admin_authenticated:
                st.session_state.admin_authenticated = True
                
                try:
                    response = supabase.table('contact_queries')\
                                        .select('*')\
                                        .eq('status', True)\
                                        .execute()
                    active_queries = response.data
                except Exception as e:
                    st.error(f"Error fetching queries: {str(e)}")
                    active_queries = []
                
                if active_queries:
                    st.success(f"Consultas activas ({len(active_queries)})")
                    
                    for query in active_queries:
                        with st.expander(f"ID: {query['id']} - {query['name'][:20]}..."):
                            st.markdown(f"""
                            **Nombre:** {query['name']}  
                            **Email:** {query['email']}  
                            **Tipo:** {query['inquiry_type']}  
                            **Mensaje:**  
                            {query['message']}
                            """)
                    
                    with st.form("update_status"):
                        st.write("Marcar consulta como resuelta")
                        query_id = st.number_input("ID de consulta",value=0)
                        submit_update = st.form_submit_button("Actualizar estado")
                        
                        if submit_update:
                            try:
                                if not any(q['id'] == query_id for q in active_queries):
                                    st.error("ID no válido o ya resuelto")
                                else:
                                    update_response = supabase.table('contact_queries')\
                                                        .update({'status': False})\
                                                        .eq('id', query_id)\
                                                        .execute()
                                    
                                    if len(update_response.data) > 0:
                                        # ======= NUEVO CÓDIGO CON SENDGRID =======
                                        try:
                                            from sendgrid import SendGridAPIClient
                                            from sendgrid.helpers.mail import Mail
                                            from datetime import datetime
                                            
                                            resolved_query = update_response.data[0]
                                            message_body = resolved_query['message']
                                            first_lines = message_body.split('\n')[0].strip()[:50]
                                            
                                            message_content = f"""
                                            Tu comentario con motivo {resolved_query['inquiry_type']}
                                            y mensaje "{first_lines}" ha sido resuelto con fecha {datetime.now().strftime("%d/%m/%Y")}.
                                            """
                                            
                                            message = Mail(
                                                from_email=st.secrets.sendgrid.sender_email,
                                                to_emails=resolved_query['email'],
                                                subject='Consulta Resuelta - FHMM',
                                                plain_text_content=message_content)
                                            
                                            sg = SendGridAPIClient(st.secrets.sendgrid.api_key)
                                            response = sg.send(message)
                                            
                                            if response.status_code == 202:
                                                st.success("Email de confirmación enviado exitosamente")
                                            else:
                                                st.error(f"Error enviando email: {response.status_code}")
                                        except Exception as email_error:
                                            st.error(f"Error enviando email: {str(email_error)}")
                                        # ======= FIN NUEVO CÓDIGO =======
                                        
                                        st.success(f"Consulta {query_id} marcada como resuelta")
                                        sleep(3)
                                        st.rerun()
                                    else:
                                        st.error("Error al actualizar")
                            except Exception as e:
                                st.error(f"Error de actualización: {str(e)}")
                else:
                    st.info("No hay consultas activas")
                
            else:
                st.error("Contraseña incorrecta")