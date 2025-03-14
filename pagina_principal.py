import streamlit as st
import os
from supabase import create_client, Client
from streamlit_extras.switch_page_button import switch_page



st.set_page_config(
    page_title="Sistema de Proyectos Comunitarios",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

url: str = st.secrets.supabase.url
key: str = st.secrets.supabase.key
supabase: Client = create_client(url, key)

# --- FUNCIONALIDAD DE LOGIN ---
def login_section():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.title("Acceso al Sistema 🔒")
        
        with st.form("login_form"):
            password = st.text_input("Contraseña de acceso:", type="password")
            submit = st.form_submit_button("Ingresar")
            
            if submit:
                if password == st.secrets.login_credentials.psswrd:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta. Intente nuevamente.")
        return True
    return False

if login_section():
    st.stop()

st.markdown("## Proyectos disponibles :floppy_disk:")
st.info("Has click en una página para ver los datos.")
st.markdown("---")

# Create a container for the navigation section
with st.container():
    # Add a header
    st.header("Application Navigation")
    
    # Add a divider for better visual separation
    st.divider()
    
    pages_dir = "pages"
    if not os.path.exists(pages_dir):
        st.error("No se encontró el directorio 'pages'. Favor de notificar al administrador.")
    else:
        page_files = [f for f in os.listdir(pages_dir) if f.endswith(".py")]
        
        if not page_files:
            st.warning("No pages found inside 'pages' directory.")
        else:
            # Create the navigation section with a card
            with st.container():
                # Use 3 columns for the buttons
                cols = st.columns(3)
                
                # Distribute buttons across columns
                for idx, file in enumerate(sorted(page_files)):
                    page_name = file.replace(".py", "").replace("_", " ").title()
                    col_idx = idx % 3
                    
                    # Place button in the appropriate column
                    with cols[col_idx]:
                        # Use st.button with custom key and styling options
                        button_key = f"nav_button_{idx}"
                        
                        # Streamlit's button with native styling
                        if st.button(
                            page_name, 
                            key=button_key,
                            use_container_width=True  # Makes button fill the column width
                        ):
                            target_page = f"pages/{file}"
                            try:
                                st.switch_page(target_page)
                            except Exception as e:
                                st.error(f"Error navigating to {page_name}: {str(e)}")
                                st.info("Please try again or reload the page.")
    
    # Add some spacing at the bottom
    st.write("")


video_url = f"https://www.youtube.com/watch?v=Ukre4MMCQfo"

with st.expander("Guía para el uso de la página"):	
    container = st.container(border=True,)
    container.video(video_url)