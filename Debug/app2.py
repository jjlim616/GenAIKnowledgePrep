# app2.py
import streamlit as st
import pandas as pd
import os
import io
from utils import get_image_mime_type, encode_image_to_base64, split_tables, clean_non_csv_content
from src.table_generator import generate_tables, refine_tables

# Default system prompt (same as originally in table_generator.py)
DEFAULT_SYSTEM_PROMPT = """You are an assistant that analyzes hierarchical diagrams and generates tables in CSV format.  
                The diagram represents a hierarchy where Level 1 is the root node, and Level 2 items are the direct children of the root.  
                Each Level 2 item has its own sub-items (Level 3 and below).  

                **Traversal Order:**  
                When processing the hierarchy, traverse the diagram strictly in a **left-to-right, top-to-bottom** order at each level.  
                - At Level 2, process the direct children of the root from left to right, top to bottom, as they appear in the diagram.  
                - For each Level 2 item, process its sub-items (Level 3 and below) in a left-to-right, top-to-bottom order, recursively applying this rule to all sub-levels.  
                - Ensure that the order of items in the generated tables reflects this traversal sequence.  

                **Table Generation Rules:**  
                By default, generate a single table with the following columns: Bil, ID, Nama Kes Gunaan/ID (column names must be in Malay).  
                - 'Bil' is a sequential number starting from 1 for each table.  
                - 'ID' is the identifier of the item (e.g., SF-MP-PD-01).  
                - 'Nama Kes Gunaan/ID' is the name or description of the item (e.g., Memilih Data - Carian Terperinci).  
                If the user requests 'one table per level 2 item,' identify all Level 2 items in the hierarchy and generate one table for each Level 2 item.  
                Each table must include only the sub-items directly under that specific Level 2 item (including all sub-levels under it), with the columns: Bil, ID, Nama Kes Gunaan/ID.  
                Do not mix sub-items from different Level 2 items in the same table.  

                **Output Format:**  
                Output each table in strict CSV format using the pipe character '|' as the delimiter (instead of commas).  
                The CSV content must start with the header 'Bil|ID|Nama Kes Gunaan/ID' followed by the data rows.  
                Do not include any additional text, explanations, labels (such as '**Table 1: Prosesan Data**'), or markdown before, after, or between the CSV data, except for the separator between tables.  
                Separate multiple tables with '---TABLE_SEPARATOR---' on its own line.  
                If only one table is generated, output a single CSV with no separator.  

                Follow any additional user instructions provided.  
                """

# Initialize session state for the system prompt if not already set
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT

st.title("Diagram Analysis and Table Generation")

# Create tabs
tab1, tab2 = st.tabs(["Generate Tables", "Edit System Prompt"])

# Tab 1: Table Generation
with tab1:
    st.write("Upload an image of a diagram (e.g., use case or hierarchy diagram), provide an optional prompt, and click 'Generate Tables' to analyze it and generate tables in Malay.")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"], key="uploader_tab1")
    
    # User prompt
    user_prompt = st.text_input(
        "Enter a custom prompt (optional)",
        placeholder="E.g., 'Generate 1 table each for item in level 2, so total of 3 tables (prosesan data, scheduling data prosesan and paparan audit log)'",
        key="prompt_tab1"
    )
    
    # Generate tables button
    if st.button("Generate Tables"):
        if uploaded_file:
            image_bytes = uploaded_file.read()
            try:
                mime_type = get_image_mime_type(image_bytes)
                base64_image = encode_image_to_base64(image_bytes)
                file_name = os.path.splitext(uploaded_file.name)[0]
                st.session_state.file_name = file_name
                
                generated_tables, messages = generate_tables(st.session_state.system_prompt, base64_image, mime_type, user_prompt)
                st.session_state.messages = messages
                st.session_state.current_tables = split_tables(generated_tables)
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please upload an image first.")
    
    # Display and refine tables
    if "current_tables" in st.session_state:
        st.subheader("Generated Tables")
        
        # Refinement section
        feedback = st.text_input("Feedback for refinement", placeholder="E.g., 'Correct Table 2, ID 1 Nama Kes Gunaan to Proses log masuk'", key="feedback_tab1")
        if st.button("Refine Tables"):
            if feedback:
                try:
                    refined_tables, messages = refine_tables(st.session_state.messages, feedback)
                    st.session_state.messages = messages
                    st.session_state.current_tables = split_tables(refined_tables)
                except Exception as e:
                    st.error(f"Error refining tables: {e}")
            else:
                st.warning("Please enter feedback to refine the tables.")
        
        # Display tables
        for i, table_content in enumerate(st.session_state.current_tables, 1):
            st.write(f"**Table {i}**")
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
                
                csv_filename = f"{st.session_state.file_name}_table_{i}.csv"
                download_content = "\n".join(
                    ','.join(field for field in line.split('|'))
                    for line in cleaned_content.splitlines()
                )
                st.download_button(
                    label=f"Download Table {i} CSV",
                    data=download_content,
                    file_name=csv_filename,
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error displaying Table {i}: {e}")

# Tab 2: Edit System Prompt
with tab2:
    st.write("View and edit the system prompt used for table generation below. Changes will apply to subsequent table generations.")
    
    # Text area for editing the system prompt
    edited_prompt = st.text_area(
        "System Prompt",
        value=st.session_state.system_prompt,
        height=400,
        key="system_prompt_editor"
    )
    
    # Button to save changes
    if st.button("Save Changes"):
        st.session_state.system_prompt = edited_prompt
        st.success("System prompt updated successfully!")
    
    # Button to reset to default
    if st.button("Reset to Default"):
        st.session_state.system_prompt = DEFAULT_SYSTEM_PROMPT
        st.success("System prompt reset to default!")