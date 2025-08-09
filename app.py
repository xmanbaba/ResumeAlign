import streamlit as st
import sys
import os

# Add debugging
st.write("Python version:", sys.version)
st.write("Current working directory:", os.getcwd())
st.write("Python path:", sys.path)

# List files in current directory
try:
    files = os.listdir('.')
    st.write("Files in current directory:", files)
except Exception as e:
    st.error(f"Error listing files: {e}")

# Test each import individually
st.write("Testing imports...")

try:
    st.write("✅ Streamlit imported successfully")
except Exception as e:
    st.error(f"❌ Streamlit import failed: {e}")

try:
    import pandas as pd
    st.write("✅ Pandas imported successfully")
except Exception as e:
    st.error(f"❌ Pandas import failed: {e}")

try:
    import io
    st.write("✅ IO imported successfully")
except Exception as e:
    st.error(f"❌ IO import failed: {e}")

try:
    from datetime import datetime
    st.write("✅ Datetime imported successfully")
except Exception as e:
    st.error(f"❌ Datetime import failed: {e}")

# Test ui_components import
try:
    from ui_components import apply_custom_css, render_header, render_sidebar
    st.write("✅ ui_components imported successfully")
    
    # Test calling functions
    apply_custom_css()
    render_header()
    
    with st.sidebar:
        render_sidebar()
        
except Exception as e:
    st.error(f"❌ ui_components import failed: {e}")
    st.error(f"Error type: {type(e)}")
    import traceback
    st.error(f"Traceback: {traceback.format_exc()}")

# Test other imports
try:
    from ai_analysis import analyze_single_candidate, analyze_batch_candidates
    st.write("✅ ai_analysis imported successfully")
except Exception as e:
    st.error(f"❌ ai_analysis import failed: {e}")

try:
    from file_utils import extract_text_from_file, save_uploaded_file
    st.write("✅ file_utils imported successfully")
except Exception as e:
    st.error(f"❌ file_utils import failed: {e}")

try:
    from name_extraction import extract_name_from_text, extract_name_from_filename
    st.write("✅ name_extraction imported successfully")
except Exception as e:
    st.error(f"❌ name_extraction import failed: {e}")

try:
    from pdf_generator import generate_comparison_pdf
    st.write("✅ pdf_generator imported successfully")
except Exception as e:
    st.error(f"❌ pdf_generator import failed: {e}")

st.write("Import testing completed!")
