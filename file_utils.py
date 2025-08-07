import os
import tempfile
import streamlit as st
from typing import Optional

def save_uploaded_file(uploaded_file) -> Optional[str]:
    """Save uploaded file to temp directory and return file path"""
    if uploaded_file is not None:
        try:
            # Create temp directory if it doesn't exist
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, uploaded_file.name)
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            return file_path
        except Exception as e:
            st.error(f"Error saving file: {str(e)}")
            return None
    return None

def cleanup_temp_files(file_paths: list):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            st.warning(f"Could not clean up file {file_path}: {str(e)}")

def validate_file_type(uploaded_file, allowed_types: list) -> bool:
    """Validate uploaded file type"""
    if uploaded_file is not None:
        file_type = uploaded_file.type
        return file_type in allowed_types
    return False
