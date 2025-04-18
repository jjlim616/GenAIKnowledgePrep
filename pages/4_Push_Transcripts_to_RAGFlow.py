# pages/4_Push_Transcripts_to_RAGFlow.py
# Standard libraries
import os

# Third-party libraries
import streamlit as st

# Local application imports
from config import RAGFLOW_BASE_URL
from src.ragflow_utils import (
    init_db,
    save_project_config,
    get_project_config,
    get_all_projects,
    fetch_knowledge_bases,
    push_to_ragflow,
    parse_document,
    list_transcript_files,
    delete_project_config,
)
from src.utils import (
    initialize_session,
    update_activity_timestamp,
    check_session_expiry,
)

# Initialize session and check for expiry
initialize_session()
if not check_session_expiry(max_inactivity_days=1):
    st.warning("Session has expired due to inactivity. Starting a new session.")
    initialize_session()
update_activity_timestamp()

init_db()

st.title("Push Transcripts to RAGFlow")

# Step 1: Project Setup
with st.container(border=True):
    st.subheader("Step 1: Set Up a Project")
    project_name_input = st.text_input("Enter a project name")
    api_key_input = st.text_input("Enter your RAGFlow API key", type="password")

    if st.button("Save Project"):
        update_activity_timestamp()
        if project_name_input and api_key_input:
            # Verify API key by attempting to fetch knowledge bases
            knowledge_bases = fetch_knowledge_bases(api_key_input, RAGFLOW_BASE_URL)
            if knowledge_bases:
                save_project_config(project_name_input, api_key_input)
                st.success(f"Project '{project_name_input}' saved successfully!")
            else:
                st.error("Invalid API key. Please check your RAGFlow API key and try again.")
        else:
            st.error("Please provide both a project name and an API key.")

# # Step 1.5: Delete a Project
# st.subheader("Step 1.5: Delete a Project")
# projects = get_all_projects()
# if projects:
#     project_to_delete = st.selectbox("Select a project to delete", projects, key="delete_project")
#     if st.button("Delete Selected Project"):
#         update_activity_timestamp()
#         delete_project_config(project_to_delete)
#         st.success(f"Project '{project_to_delete}' and its API key deleted successfully!")
# else:
#     st.warning("No projects available to delete.")

# Step 2: Select Project and Knowledge Base
with st.container(border=True):
    st.subheader("Step 2: Select Project and Knowledge Base")
    projects = get_all_projects()  # Refresh projects list after potential deletion
    if projects:
        selected_project = st.selectbox("Select a project", projects, key="select_project")
        api_key, kb_id = get_project_config(selected_project)

        if api_key:
            # Fetch knowledge bases
            knowledge_bases = fetch_knowledge_bases(api_key, RAGFLOW_BASE_URL)
            if knowledge_bases:
                kb_options = {kb["name"]: kb["id"] for kb in knowledge_bases}
                selected_kb_name = st.selectbox("Select Knowledge Base", list(kb_options.keys()), index=list(kb_options.keys()).index(next((name for name, id in kb_options.items() if id == kb_id), None)) if kb_id else 0)
                selected_kb_id = kb_options[selected_kb_name]

                # Save the selected knowledge base ID
                if selected_kb_id != kb_id:
                    save_project_config(selected_project, api_key, selected_kb_id)
                    st.success(f"Knowledge base '{selected_kb_name}' selected for project '{selected_project}'.")
            else:
                st.warning("No knowledge bases found. Please check your API key or create a knowledge base in RAGFlow.")
    else:
        st.warning("No projects found. Please set up a project first.")
        selected_project = None
        selected_kb_id = None

# Step 3: Select Files and Push to RAGFlow
with st.container(border=True):
    if selected_project and selected_kb_id:
        st.subheader("Step 3: Select Files to Push")
        transcript_folder = "transcripts"  # Path to the transcripts folder
        if not os.path.exists(transcript_folder):
            st.error(f"Transcripts folder '{transcript_folder}' not found.")
        else:
            # List all DOCX files in the transcripts folder
            files = list_transcript_files(transcript_folder)
            if not files:
                st.warning("No DOCX files found in the transcripts folder or its subfolders.")
            else:
                selected_files = st.multiselect("Select files to push (path includes subfolder)", files)
                if st.button("Push Selected Files"):
                    update_activity_timestamp()
                    if selected_files:
                        for relative_file_path in selected_files:
                            # Convert relative path to absolute path for file access
                            file_path = os.path.join(transcript_folder, relative_file_path)
                            success, document_id = push_to_ragflow(api_key, selected_kb_id, file_path, RAGFLOW_BASE_URL)
                            if success:
                                st.success(f"File '{relative_file_path}' pushed to RAGFlow successfully!")
                                # Optionally parse the document
                                if parse_document(api_key, selected_kb_id, document_id, RAGFLOW_BASE_URL):
                                    st.info(f"File '{relative_file_path}' parsed successfully.")
                                else:
                                    st.warning(f"File '{relative_file_path}' uploaded but parsing failed.")
                    else:
                        st.error("Please select at least one file to push.")