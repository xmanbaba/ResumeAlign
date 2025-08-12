import streamlit as st
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_custom_css():
    """Apply custom CSS styling with COMPACT file upload area"""
    st.markdown("""
    <style>
    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling with correct branding colors */
    .header-container {
        background: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .logo-placeholder {
        width: 50px;
        height: 50px;
        background: #E53E3E;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 18px;
    }
    
    .header-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        color: black !important;
    }
    
    .header-subtitle {
        font-size: 0.9rem;
        margin: 0.2rem 0 0 0;
        color: #E53E3E !important;
        font-weight: 500;
    }
    
    /* Button styling with brand colors */
    .stButton > button {
        background: #E53E3E !important;
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(229, 62, 62, 0.2);
    }
    
    .stButton > button:hover {
        background: #C53030 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(229, 62, 62, 0.3);
    }
    
    /* COMPACT file uploader - REDUCED HEIGHT by 75% as requested */
    .stFileUploader > div > div {
        background-color: #f8fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 8px;
        padding: 1rem !important;  /* Much smaller padding */
        min-height: 60px !important;  /* Reduced from 200px to 60px */
        text-align: center;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    .stFileUploader > div > div:hover {
        border-color: #E53E3E;
        background-color: #fef2f2;
    }
    
    /* Make upload text smaller to fit compact area */
    .stFileUploader > div > div > div {
        font-size: 0.9rem;
    }
    
    /* Text area improvements */
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #E53E3E;
        box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.1);
    }
    
    /* Tab styling with brand colors */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8fafc;
        padding: 4px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 8px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: transparent;
        border: 1px solid transparent;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: #E53E3E !important;
        color: white;
        font-weight: 600;
    }
    
    /* Progress bar styling with brand color */
    .stProgress .st-bo {
        background: #E53E3E !important;
    }
    
    /* Alert styling - PERSISTENT ERRORS */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin: 1rem 0 !important;
    }
    
    /* Make error messages more prominent and persistent */
    .stError {
        background-color: #fef2f2 !important;
        border-left: 4px solid #ef4444 !important;
        color: #991b1b !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 600;
    }
    
    .stSuccess {
        background-color: #f0fff4 !important;
        border-left: 4px solid #22c55e !important;
        color: #166534 !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 600;
    }
    
    .stWarning {
        background-color: #fffbf0 !important;
        border-left: 4px solid #f59e0b !important;
        color: #92400e !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 600;
    }
    
    .stInfo {
        background-color: #eff6ff !important;
        border-left: 4px solid #3b82f6 !important;
        color: #1e40af !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        font-weight: 600;
    }
    
    /* Sidebar improvements */
    .sidebar .block-container {
        padding-top: 1rem;
    }
    
    /* Clear Session button styling */
    .stButton:has(button:contains("Clear Session")) > button {
        background: #dc2626 !important;
        color: white !important;
    }
    
    .stButton:has(button:contains("Clear Session")) > button:hover {
        background: #b91c1c !important;
    }
    
    /* RIGHT-ALIGNED ANALYZE BUTTON - NEW STYLING */
    .analyze-button-right {
        display: flex;
        justify-content: flex-end;
        margin: 1rem 0;
    }
    
    .analyze-button-right .stButton {
        margin-left: auto;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 6px;
        font-weight: 600;
        border-left: 3px solid #E53E3E;
        padding: 0.5rem 1rem;
    }
    
    /* Score display styling */
    .score-high { 
        color: white; 
        background: #22c55e;
        padding: 4px 12px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    .score-medium { 
        color: white; 
        background: #f59e0b;
        padding: 4px 12px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    .score-low { 
        color: white; 
        background: #ef4444;
        padding: 4px 12px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    /* File info styling */
    .file-info {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        color: #4a5568;
    }
    
    /* Compact metric containers */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #E53E3E;
        margin: 0.5rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .header-title {
            font-size: 1.8rem;
        }
        
        .header-subtitle {
            font-size: 0.8rem;
        }
        
        .stFileUploader > div > div {
            padding: 0.8rem !important;
            min-height: 50px !important;
        }
        
        .analyze-button-right {
            justify-content: center;
        }
    }
    
    /* Custom animations */
    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateY(10px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    .slide-in {
        animation: slideIn 0.3s ease-out;
    }
    
    /* Spinner for loading states */
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .spinner {
        animation: spin 1s linear infinite;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header with correct branding"""
    st.markdown("""
    <div class="header-container">
        <div class="logo-container">
            <div class="logo-placeholder">RA</div>
            <div>
                <h1 class="header-title">ResumeAlign</h1>
                <p class="header-subtitle">AI-Powered Resume Analysis and Candidate Matching</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render enhanced sidebar with navigation and info - REMOVED GEMINI REFERENCE"""
    st.markdown("### 🎯 ResumeAlign")
    st.markdown("---")
    
    # App info
    with st.expander("ℹ️ About ResumeAlign"):
        st.markdown("""
        **ResumeAlign** helps you find the perfect candidates by:
        
        ✅ **Smart Analysis** - AI-powered resume evaluation  
        ✅ **Batch Processing** - Analyze up to 5 resumes at once
        ✅ **Detailed Scoring** - Skills, experience, and education breakdown  
        ✅ **Export Options** - PDF, Excel, and JSON reports  
        ✅ **Interview Questions** - AI-generated relevant questions
        ✅ **Candidate Ranking** - Automatic ranking by fit score
        """)
    
    # Usage tips - comprehensive
    with st.expander("💡 Usage Tips"):
        st.markdown("""
        **For Best Results:**
        
        1️⃣ **Detailed Job Description** - Include specific skills, experience levels, and requirements. More detail = better matching.
        
        2️⃣ **Clear Resume Format** - PDF and DOCX files work best. Ensure text is selectable, not scanned images.
        
        3️⃣ **Batch Limits** - Maximum 5 resumes per batch analysis. Plan accordingly.
        
        4️⃣ **File Upload** - Use the compact upload area. Click or drag files directly.
        
        5️⃣ **Review Detailed Analysis** - Check expanded reports for insights beyond scores.
        
        6️⃣ **Clear Session** - Use Clear Session button between different job analyses.
        
        7️⃣ **Export Results** - Generate PDF/Excel/JSON reports for team sharing.
        
        **Supported Files:** PDF, DOCX, TXT (max 10MB each)  
        **Best Practices:** Quality over quantity - detailed JD gets better results
        """)
    
    # REMOVED: st.markdown("---")
    # REMOVED: st.markdown("*Powered by Google Gemini 2.5 Flash*")

def render_compact_file_info(uploaded_files):
    """Render compact file information - FIXED to handle Streamlit file objects"""
    if not uploaded_files:
        return
        
    # Handle both single file and multiple files
    files = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
    
    for i, file in enumerate(files, 1):
        try:
            # FIXED: Use len(getvalue()) for Streamlit uploaded files
            file_content = file.getvalue()
            file_size = len(file_content)
            
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.1f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.1f} MB"
        except Exception as e:
            size_str = "Unknown size"
            logger.warning(f"Could not get size for file {file.name}: {str(e)}")
        
        st.markdown(f"""
        <div class="file-info">
            📄 {i}. {file.name} ({size_str})
        </div>
        """, unsafe_allow_html=True)

def render_persistent_error(message, key=None):
    """Render persistent error message that doesn't disappear"""
    if key and key not in st.session_state:
        st.session_state[key] = message
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #ef444420 0%, transparent 100%);
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        color: #991b1b;
        font-weight: 600;
    ">
        ❌ {message}
    </div>
    """, unsafe_allow_html=True)

def render_persistent_success(message):
    """Render persistent success message"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #22c55e20 0%, transparent 100%);
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        color: #166534;
        font-weight: 600;
    ">
        ✅ {message}
    </div>
    """, unsafe_allow_html=True)

def render_file_limit_warning():
    """Render warning about file limits"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #f59e0b20 0%, transparent 100%);
        border-left: 4px solid #f59e0b;
        padding: 0.8rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        color: #92400e;
        font-size: 0.9rem;
    ">
        ⚠️ <strong>Batch Limit:</strong> Maximum 5 files per batch analysis
    </div>
    """, unsafe_allow_html=True)

def render_right_aligned_analyze_button(button_text, button_key, disabled=False):
    """Render analyze button aligned to the right"""
    st.markdown('<div class="analyze-button-right">', unsafe_allow_html=True)
    
    result = st.button(
        button_text, 
        key=button_key, 
        type="primary", 
        disabled=disabled,
        use_container_width=False
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return result

def render_analysis_card(result, rank=None):
    """Render a single analysis result card"""
    name = result.get('candidate_name', 'Unknown Candidate')
    overall_score = result.get('overall_score', 0)
    skills_score = result.get('skills_score', 0)
    experience_score = result.get('experience_score', 0)
    education_score = result.get('education_score', 0)
    
    # Determine score color and emoji
    if overall_score >= 80:
        score_class = "score-high"
        score_emoji = "🌟"
    elif overall_score >= 60:
        score_class = "score-medium"
        score_emoji = "⭐"
    else:
        score_class = "score-low"
        score_emoji = "📋"
    
    rank_display = f"#{rank} " if rank else ""
    
    card_html = f"""
    <div class="metric-container slide-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h4 style="margin: 0; color: #2D3748;">{score_emoji} {rank_display}{name}</h4>
            <div class="{score_class}">
                {overall_score}%
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">
            <div style="text-align: center;">
                <div style="font-size: 1.2em; font-weight: bold; color: #2D3748;">{skills_score}%</div>
                <div style="font-size: 0.8em; color: #718096;">Skills</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.2em; font-weight: bold; color: #2D3748;">{experience_score}%</div>
                <div style="font-size: 0.8em; color: #718096;">Experience</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.2em; font-weight: bold; color: #2D3748;">{education_score}%</div>
                <div style="font-size: 0.8em; color: #718096;">Education</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_loading_spinner(text="Processing..."):
    """Render loading spinner with brand colors"""
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div class="spinner" style="display: inline-block; width: 40px; height: 40px; border: 3px solid #f3f3f3; border-radius: 50%; border-top: 3px solid #E53E3E;"></div>
        <p style="margin-top: 15px; color: #E53E3E; font-weight: 500;">{text}</p>
    </div>
    """, unsafe_allow_html=True)

def get_timestamp():
    """Get formatted timestamp for display"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
