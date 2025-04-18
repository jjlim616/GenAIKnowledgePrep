import streamlit as st
import openai
import pandas as pd
import base64
import io
import os
import re
import imghdr
import csv
from config import OPENAI_API_KEY

# Initialize OpenAI client with the API key from config.py
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Define the system prompt with stricter instructions
system_prompt = """You are an assistant that analyzes hierarchical diagrams and generates tables in CSV format.  
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

# Function to determine the image MIME type
def get_image_mime_type(image_bytes):
    image_type = imghdr.what(None, image_bytes)
    if image_type == "jpeg":
        return "image/jpeg"
    elif image_type == "png":
        return "image/png"
    else:
        raise ValueError(f"Unsupported image type: {image_type}. Please upload a JPEG or PNG image.")

# Function to split response into separate tables
def split_tables(response_text):
    tables = re.split(r'---TABLE_SEPARATOR---', response_text.strip())
    return [table.strip() for table in tables if table.strip()]

# Function to capture DataFrame info as a string
def get_df_info(df):
    buffer = io.StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()

# Function to clean non-CSV text from the content
def clean_non_csv_content(content):
    lines = content.replace('\r\n', '\n').splitlines()
    csv_lines = []
    for line in lines:
        # Only include lines that look like CSV data (start with a number or the header)
        if re.match(r'^(Bil|\d+)', line):
            csv_lines.append(line.strip())
    return "\n".join(csv_lines)

# Set up the Streamlit app
st.title("Diagram Analysis and Table Generation")
st.write("Upload an image of a diagram (e.g., use case or hierarchy diagram), provide an optional prompt, and click 'Generate Tables' to analyze it and generate tables in Malay.")

# File uploader for image input
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

# Text input for custom user prompt
user_prompt = st.text_input(
    "Enter a custom prompt (optional)",
    placeholder="E.g., 'Generate 1 table each for item in level 2, so total of 3 tables (prosesan data, "
    "scheduling data prosesan and paparan audit log)'"
)

# Button to generate the tables
if st.button("Generate Tables"):
    if uploaded_file is not None:
        # Read the uploaded image as bytes
        image_bytes = uploaded_file.read()
        # Determine the image MIME type
        try:
            mime_type = get_image_mime_type(image_bytes)
        except ValueError as e:
            st.error(str(e))
            st.stop()
        # Encode the image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        # Get the uploaded file name without extension
        file_name = os.path.splitext(uploaded_file.name)[0]
        # Store the file name in session state for later use
        st.session_state.file_name = file_name
        # Combine system prompt with user prompt if provided
        full_prompt = system_prompt
        if user_prompt:
            full_prompt += f"\n\nAdditional Instructions: {user_prompt}"
        # Initialize the conversation history in session state
        st.session_state.messages = [
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": "Here is the diagram:"},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
            ]}
        ]
        # Make the API call to OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=st.session_state.messages,
                max_tokens=2000
            )
            # Extract the generated tables from the response
            generated_tables = response.choices[0].message.content
            # Display raw response for debugging
            st.write("**Raw API Response (for debugging):**")
            st.text(generated_tables)
            # Append the assistant's response to the conversation history
            st.session_state.messages.append({"role": "assistant", "content": generated_tables})
            # Split the response into separate tables
            table_list = split_tables(generated_tables)
            # Store the tables in session state
            st.session_state.current_tables = table_list
        except Exception as e:
            st.error(f"Error generating tables: {e}")
    else:
        st.warning("Please upload an image first.")

# Display the tables and handle refinement
if "current_tables" in st.session_state:
    st.subheader("Generated Tables")

    # Refinement section (moved before table display to ensure immediate update)
    feedback = st.text_input("Feedback for refinement", placeholder="E.g., 'Correct Table 2, ID 1 Nama Kes Gunaan to Proses log masuk'")
    if st.button("Refine Tables"):
        if feedback:
            # Append the user's feedback to the conversation history
            st.session_state.messages.append({"role": "user", "content": feedback})
            # Make another API call with the updated history
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=st.session_state.messages,
                    max_tokens=2000
                )
                # Extract the refined tables
                refined_tables = response.choices[0].message.content
                # Display raw response for debugging
                st.write("**Raw Refined Response (for debugging):**")
                st.text(refined_tables)
                # Append the assistant's response to the history
                st.session_state.messages.append({"role": "assistant", "content": refined_tables})
                # Split and update the current tables
                table_list = split_tables(refined_tables)
                st.session_state.current_tables = table_list
            except Exception as e:
                st.error(f"Error refining tables: {e}")
        else:
            st.warning("Please enter feedback to refine the tables.")

    # Display the tables (this will re-render with the latest content)
    for i, table_content in enumerate(st.session_state.current_tables, 1):
        st.write(f"**Table {i}**")
        # Clean the table content by removing extra newlines, whitespace, and non-CSV text
        cleaned_content = clean_non_csv_content(table_content)
        # Display raw table content for debugging
        st.write(f"**Raw Table {i} Content (for debugging):**")
        st.text(cleaned_content)
        try:
            # Parse the table using pd.read_csv with pipe delimiter
            df = pd.read_csv(
                io.StringIO(cleaned_content),
                sep='|',  # Use pipe as the delimiter
                encoding='utf-8',
                on_bad_lines='warn',  # Warn instead of skip to see problematic lines
                skip_blank_lines=True  # Skip empty lines
            )
            # Log DataFrame details for debugging
            st.write(f"**DataFrame Info for Table {i}:**")
            st.text(get_df_info(df))
            st.write(f"**DataFrame Shape for Table {i}:** {df.shape}")
            if df.empty:
                st.warning(f"Table {i} is empty after parsing. Check the raw content for issues.")
            else:
                # Try st.dataframe first
                st.dataframe(df)
                # Fallback to st.table if st.dataframe fails to render
                st.write("**Fallback Display (using st.table):**")
                st.table(df)
            # Add a download button for this table, converting back to comma-separated format
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
            st.text(f"Cleaned content of Table {i}:\n{cleaned_content}")


