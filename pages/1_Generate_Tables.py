# pages/1_Generate_Tables.py
# Standard libraries
import os
import io

# Third-party libraries
import pandas as pd
import streamlit as st

# Local application imports
from src.utils import (
    get_image_mime_type,
    encode_image_to_base64,
    split_tables,
    clean_non_csv_content,
    initialize_session,
    update_activity_timestamp,
    check_session_expiry,
)
from src.table_generator import generate_tables, refine_tables
from src.prompts import TABLES_DEFAULT_SYSTEM_PROMPT

# Initialize session and check for expiry
initialize_session()
if not check_session_expiry(max_inactivity_days=1):
    st.warning("Session has expired due to inactivity. Starting a new session.")
    initialize_session()
update_activity_timestamp()

# Initialize session state for system prompts
if 'system_prompts' not in st.session_state:
    st.session_state.system_prompts = {
        "Hierarchy Diagrams": TABLES_DEFAULT_SYSTEM_PROMPT,
        "ERD": TABLES_DEFAULT_SYSTEM_PROMPT,
        "Use Case Diagrams": TABLES_DEFAULT_SYSTEM_PROMPT,
    }

st.title("Diagram Analysis and Table Generation")

# Define tabs
tab_names = ["Hierarchy Diagrams", "ERD", "Use Case Diagrams"]
tabs = st.tabs(tab_names)

# Process each tab
for i, tab_name in enumerate(tab_names):
    with tabs[i]:
        # Two-column layout for input and prompt editing
        col1, col2 = st.columns(2)

        # Column 1: Upload and Prompt
        with col1:
            st.write(f"Upload an image of a {tab_name.lower()} and provide an optional prompt to generate tables in Malay.")
            
            uploaded_file = st.file_uploader(f"Upload an image ({tab_name})", type=["jpg", "jpeg", "png"], key=f"uploader_{tab_name}")
            
            user_prompt = st.text_input(
                f"Enter a custom prompt (optional) for {tab_name}",
                placeholder="E.g., 'Generate 1 table each for item in level 2'",
                key=f"prompt_{tab_name}"
            )
            
            if st.button(f"Generate Tables ({tab_name})", key=f"generate_{tab_name}"):
                update_activity_timestamp()  # Update timestamp on user interaction
                if uploaded_file:
                    image_bytes = uploaded_file.read()
                    try:
                        mime_type = get_image_mime_type(image_bytes)
                        base64_image = encode_image_to_base64(image_bytes)
                        file_name = os.path.splitext(uploaded_file.name)[0]
                        st.session_state.file_name = file_name
                        
                        generated_tables, messages = generate_tables(
                            st.session_state.system_prompts[tab_name], 
                            base64_image, 
                            mime_type, 
                            user_prompt
                        )
                        st.session_state[f"messages_{tab_name}"] = messages
                        st.session_state[f"current_tables_{tab_name}"] = split_tables(generated_tables)
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please upload an image first.")

        # Column 2: Edit System Prompt
        with col2:
            st.write(f"Edit the system prompt for {tab_name} below.")
            
            edited_prompt = st.text_area(
                f"System Prompt ({tab_name})",
                value=st.session_state.system_prompts[tab_name],
                height=300,
                key=f"system_prompt_{tab_name}"
            )
            
            if st.button(f"Save Changes ({tab_name})", key=f"save_{tab_name}"):
                update_activity_timestamp()  # Update timestamp on user interaction
                st.session_state.system_prompts[tab_name] = edited_prompt
                st.success(f"System prompt for {tab_name} updated successfully!")
            
            if st.button(f"Reset to Default ({tab_name})", key=f"reset_{tab_name}"):
                update_activity_timestamp()  # Update timestamp on user interaction
                st.session_state.system_prompts[tab_name] = TABLES_DEFAULT_SYSTEM_PROMPT
                st.success(f"System prompt for {tab_name} reset to default!")

        # Output Section (below columns)
        if f"current_tables_{tab_name}" in st.session_state:
            st.subheader(f"Generated Tables ({tab_name})")
            
            feedback = st.text_input(
                f"Feedback for refinement ({tab_name})", 
                placeholder="E.g., 'Correct Table 2, ID 1 Nama Kes Gunaan to Proses log masuk'",
                key=f"feedback_{tab_name}"
            )
            if st.button(f"Refine Tables ({tab_name})", key=f"refine_{tab_name}"):
                update_activity_timestamp()  # Update timestamp on user interaction
                if feedback:
                    try:
                        refined_tables, messages = refine_tables(
                            st.session_state[f"messages_{tab_name}"], 
                            feedback
                        )
                        st.session_state[f"messages_{tab_name}"] = messages
                        st.session_state[f"current_tables_{tab_name}"] = split_tables(refined_tables)
                    except Exception as e:
                        st.error(f"Error refining tables: {e}")
                else:
                    st.warning("Please enter feedback to refine the tables.")
            
            for j, table_content in enumerate(st.session_state[f"current_tables_{tab_name}"], 1):
                st.write(f"**Table {j}**")
                cleaned_content = clean_non_csv_content(table_content)
                
                try:
                    df = pd.read_csv(
                        io.StringIO(cleaned_content),
                        sep='|',
                        encoding='utf-8',
                        on_bad_lines='warn',
                        skip_blank_lines=True
                    )
                    st.dataframe(df)
                    
                    csv_filename = f"{st.session_state.file_name}_table_{j}.csv"
                    download_content = "\n".join(
                        ','.join(field for field in line.split('|'))
                        for line in cleaned_content.splitlines()
                    )
                    st.download_button(
                        label=f"Download Table {j} CSV",
                        data=download_content,
                        file_name=csv_filename,
                        mime="text/csv",
                        key=f"download_{tab_name}_{j}"
                    )
                except Exception as e:
                    st.error(f"Error displaying Table {j}: {e}")