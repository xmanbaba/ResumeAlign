"""
UI Components and CSS styling for ResumeAlign
Contains all styling and reusable UI components - FIXED VERSION
"""

import streamlit as st


def apply_custom_css():
    """Apply modern CSS styling with ResumeAlign brand colors and requested improvements"""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: #ffffff;
        min-height: 100vh;
    }
    
    /* Logo Header Container */
    .logo-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        padding: 1rem 2rem;
        border-bottom: 2px solid #E53E3E;
        margin-bottom: 2rem;
        box-shadow: 0 2px 10px rgba(229, 62, 62, 0.1);
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .logo-image {
        height: 50px;
        width: auto;
    }
    
    .logo-text {
        font-size: 1.8rem;
        font-weight: 700;
        color: #E53E3E;
        margin: 0;
    }
    
    /* Main Container */
    .main > div {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: #ffffff;
    }
    
    /* Header Styling - Reduced height */
    .main-header {
        background: #ffffff;
        border: 2px solid #000000;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .main-title {
        background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-subtitle {
        text-align: center;
        color: #2D3748;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Feature Button Cards - Black borders and properly aligned headers */
    .feature-card {
        background: #ffffff;
        border: 2px solid #000000;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 15px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        min-height: auto;
        height: auto;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12);
        border-color: #E53E3E;
    }
    
    .feature-card h3 {
        color: #1e293b;
        margin-bottom: 0.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        text-align: center;
        padding: 0.5rem;
        background: rgba(229, 62, 62, 0.05);
        border-radius: 8px;
        border: 1px solid rgba(229, 62, 62, 0.2);
    }
    
    /* Analysis Cards - Black borders and properly aligned headers */
    .analysis-card {
        background: #ffffff;
        border: 2px solid #000000;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 15px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
    }
    
    .analysis-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
        border-color: #E53E3E;
    }
    
    /* Ensure all section headers are properly aligned in their button boxes */
    .analysis-card h3 {
        color: #059669;
        margin-bottom: 1rem;
        font-weight: 600;
        text-align: center;
        padding: 0.8rem;
        background: rgba(5, 150, 105, 0.05);
        border-radius: 8px;
        border: 1px solid rgba(5, 150, 105, 0.2);
    }
    
    /* Mode Selector - Black borders */
    .stRadio > label {
        background: #ffffff;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        margin: 0.3rem 0;
        border: 2px solid #000000;
        transition: all 0.3s ease;
        min-height: auto;
    }
    
    .stRadio > label:hover {
        border-color: #E53E3E;
        background: rgba(229, 62, 62, 0.05);
    }
    
    /* Form Elements - Black borders */
    .stTextArea textarea, .stTextInput input {
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        padding: 0.8rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        background: #ffffff !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #E53E3E !important;
        box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.1) !important;
    }
    
    /* Compact text areas */
    .stTextArea textarea {
        min-height: 120px !important;
    }
    
    /* Buttons - Properly aligned and reduced height */
    .stButton > button {
        background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%) !important;
        color: white !important;
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 10px rgba(229, 62, 62, 0.3) !important;
        min-height: auto !important;
        height: auto !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(229, 62, 62, 0.4) !important;
        background: linear-gradient(135deg, #C53030 0%, #E53E3E 100%) !important;
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2D3748 0%, #1A202C 100%) !important;
        color: white !important;
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 10px rgba(45, 55, 72, 0.3) !important;
        min-height: auto !important;
        width: 100% !important;
        text-align: center !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(45, 55, 72, 0.4) !important;
        background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%) !important;
    }
    
    /* File Uploader - Black border */
    .stFileUploader {
        background: #ffffff;
        border: 2px solid #000000;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #E53E3E;
        background: rgba(229, 62, 62, 0.02);
    }
    
    /* Metrics - Black borders and compact */
    .stMetric {
        background: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #000000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    
    /* Progress Bar */
    .stProgress .css-1cpxqw2 {
        background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%);
        border-radius: 6px;
    }
    
    /* Info/Success/Error Messages - Black borders */
    .stAlert {
        border-radius: 8px;
        border: 2px solid #000000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    /* Tables - Black borders */
    .stTable {
        background: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        border: 2px solid #000000;
    }
    
    /* Expander - Black borders and compact */
    .streamlit-expanderHeader {
        background: #ffffff;
        border-radius: 8px;
        border: 2px solid #000000;
        font-weight: 600;
        color: #2D3748;
        padding: 0.8rem 1rem;
        min-height: auto;
        text-align: center;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #E53E3E;
        background: rgba(229, 62, 62, 0.02);
    }
    
    /* LinkedIn Helper Section - Black border */
    .linkedin-section {
        background: rgba(0, 119, 181, 0.05);
        border: 2px solid #000000;
        border-radius: 12px;
        padding: 1.2rem;
        margin: 1rem 0;
    }
    
    /* Link Button Styling - Black border */
    .stLinkButton > a {
        background: linear-gradient(135deg, #0077b5 0%, #005582 100%) !important;
        color: white !important;
        text-decoration: none !important;
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        display: block !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 10px rgba(0, 119, 181, 0.3) !important;
        min-height: auto !important;
        width: 100% !important;
    }
    
    .stLinkButton > a:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(0, 119, 181, 0.4) !important;
    }
    
    /* Popover Styling - Black borders */
    .stPopover {
        border-radius: 8px;
        box-shadow: 0 2px 15px rgba(0, 0, 0, 0.15);
        border: 2px solid #000000;
        background: #ffffff;
    }
    
    /* Clear Button Styling */
    .clear-button {
        background: linear-gradient(135deg, #718096 0%, #4A5568 100%) !important;
        border: 2px solid #000000 !important;
    }
    
    .clear-button:hover {
        background: linear-gradient(135deg, #4A5568 0%, #718096 100%) !important;
    }
    
    /* Success/Error Styling - Black borders */
    .stSuccess {
        background: rgba(72, 187, 120, 0.1);
        border: 2px solid #000000;
        border-left: 4px solid #48bb78;
        color: #22543d;
    }
    
    .stError {
        background: rgba(229, 62, 62, 0.1);
        border: 2px solid #000000;
        border-left: 4px solid #E53E3E;
        color: #742a2a;
    }
    
    .stInfo {
        background: rgba(49, 130, 206, 0.1);
        border: 2px solid #000000;
        border-left: 4px solid #3182ce;
        color: #2c5aa0;
    }
    
    .stWarning {
        background: rgba(237, 137, 54, 0.1);
        border: 2px solid #000000;
        border-left: 4px solid #ed8936;
        color: #9c4221;
    }
    
    /* Form containers - Black borders */
    .stForm {
        border: 2px solid #000000;
        border-radius: 12px;
        padding: 1.5rem;
        background: #ffffff;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Compact spacing */
    .element-container {
        margin-bottom: 0.8rem;
    }
    
    /* Reduce column gaps */
    .row-widget {
        gap: 0.5rem;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .stSpinner {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Remove default Streamlit branding adjustments */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


def render_logo_header():
    """Render the ResumeAlign logo header"""
    st.markdown("""
    <div class="logo-header">
        <div class="logo-container">
            <svg width="50" height="35" viewBox="0 0 430 300" fill="none" xmlns="http://www.w3.org/2000/svg" class="logo-image">
                <rect width="430" height="300" fill="white"/>
                <path d="M82.5 267.5L172 187.5H102L82.5 267.5Z" fill="#E53E3E"/>
                <path d="M82.5 267.5V187.5H172C172 187.5 172 154.167 172 137.5C172 120.833 155.167 104 144.5 104C133.833 104 82.5 104 82.5 104V267.5Z" fill="#E53E3E"/>
                <path d="M102 167H154C154 167 162 154 162 148C162 142 154 129 154 129H102V167Z" fill="white"/>
                <path d="M117.5 157L126.5 148L141 162.5L134 169.5L117.5 157Z" fill="#233A54"/>
                <text x="185" y="175" font-family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif" font-size="42" font-weight="600" fill="#2D3748">ResumeAlign</text>
            </svg>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_main_header():
    """Render the main header section"""
    st.markdown("""
    <div class="main-header">
        <p class="main-subtitle">AI-Powered Resume & CV Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)


def render_feature_card(title, content=""):
    """Render a feature card with title"""
    st.markdown(f"""
    <div class="feature-card">
        <h3>{title}</h3>
        {content}
    </div>
    """, unsafe_allow_html=True)


def render_analysis_card(title, content=""):
    """Render an analysis results card"""
    st.markdown(f"""
    <div class="analysis-card">
        <h3>{title}</h3>
        {content}
    </div>
    """, unsafe_allow_html=True)


def render_linkedin_helper():
    """Render the LinkedIn profile helper section"""
    st.markdown('<div class="linkedin-section">', unsafe_allow_html=True)
    
    with st.popover("ℹ️ How to use LinkedIn URL", use_container_width=False):
        st.markdown("""
        **Step-by-step Guide:**
        
        1. **Paste LinkedIn URL** - The URL is automatically detected
        2. **Click 'Save to PDF'** - Opens the exact profile page  
        3. **On LinkedIn page** - Click **More → Save to PDF**
        4. **Upload PDF** - Upload the downloaded PDF file
        
        💡 **Tip:** This method provides the most accurate analysis!
        """)
    
    col1, col2 = st.columns([4, 2])
    with col1:
        profile_url = st.text_input(
            "LinkedIn Profile URL", 
            placeholder="https://linkedin.com/in/candidate-name",
            help="Paste the candidate's LinkedIn profile URL here"
        )
    
    with col2:
        target = profile_url.strip() if profile_url.strip() else "https://linkedin.com"
        st.link_button("📱 Open LinkedIn Profile", target, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    return profile_url


def render_copy_paste_guide():
    """Render the manual copy-paste guide"""
    with st.popover("📋 Manual Copy-Paste Guide", use_container_width=False):
        st.markdown("""
        **Essential LinkedIn Sections to Copy:**
        
        ✅ **Name & Professional Headline**  
        ✅ **About Section** (complete summary)  
        ✅ **Experience** (all positions with descriptions)  
        ✅ **Skills & Endorsements**  
        ✅ **Education** (degrees, institutions, dates)  
        ✅ **Certifications & Licenses**  
        
        **Pro Tips:**
        - Copy each section completely for better analysis
        - Include job descriptions and achievements
        - Don't forget skills and endorsements
        """)


def render_app_footer():
    """Render the application footer - FIXED: Removed "Built with love" message"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #64748b; font-size: 0.9rem; border-top: 2px solid #000000; margin-top: 2rem;">
        <p>© 2025 ResumeAlign - AI-Powered Resume Analysis Platform</p>
    </div>
    """, unsafe_allow_html=True)


def clear_session():
    """Clear all session state data"""
    keys_to_clear = ["last_report", "linkedin_url", "batch_reports", "batch_job_desc"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
