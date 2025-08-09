import streamlit as st
from datetime import datetime

def apply_custom_css():
    """Apply custom CSS styling with correct branding colors"""
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
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .logo-placeholder {
        width: 60px;
        height: 60px;
        background: #E53E3E;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 24px;
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        color: black !important;  /* Black text as requested */
    }
    
    .header-subtitle {
        font-size: 1rem;
        margin: 0.3rem 0 0 0;
        color: #E53E3E !important;  /* Red subtitle as requested */
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
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(229, 62, 62, 0.3);
    }
    
    /* Primary button (Analyze buttons) */
    .stButton[data-testid="baseButton-primary"] > button {
        background: #E53E3E !important;
        border: 2px solid #E53E3E;
    }
    
    /* File uploader styling - make it much taller */
    .stFileUploader > div > div {
        background-color: #f8fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 10px;
        padding: 4rem 2rem !important;  /* Tripled the height as requested */
        min-height: 200px !important;  /* Minimum height to ensure good drag area */
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
    
    /* Upload area text */
    .stFileUploader > div > div > div {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
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
        height: 50px;
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
    
    /* Alert styling */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: #f0fff4 !important;
        border-left: 4px solid #22c55e !important;
        color: #166534 !important;
    }
    
    /* Error message styling */
    .stError {
        background-color: #fef2f2 !important;
        border-left: 4px solid #ef4444 !important;
        color: #991b1b !important;
    }
    
    /* Warning message styling */
    .stWarning {
        background-color: #fffbf0 !important;
        border-left: 4px solid #f59e0b !important;
        color: #92400e !important;
    }
    
    /* Info message styling */
    .stInfo {
        background-color: #eff6ff !important;
        border-left: 4px solid #3b82f6 !important;
        color: #1e40af !important;
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
    
    /* Expander styling with brand colors */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 8px;
        font-weight: 600;
        border-left: 4px solid #E53E3E;
    }
    
    /* Metric container styling */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #E53E3E;
        margin: 0.5rem 0;
    }
    
    /* Score display styling with brand colors */
    .score-high { 
        color: white; 
        background: #22c55e;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    .score-medium { 
        color: white; 
        background: #f59e0b;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    .score-low { 
        color: white; 
        background: #ef4444;
        padding: 6px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
    }
    
    /* LinkedIn blue for future LinkedIn features */
    .linkedin-blue {
        color: #0077b5;
    }
    
    /* Navy blue for secondary text */
    .navy-text {
        color: #2D3748;
    }
    
    /* Hide Streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2rem;
        }
        
        .header-subtitle {
            font-size: 0.9rem;
        }
        
        .stFileUploader > div > div {
            padding: 3rem 1rem !important;
        }
    }
    
    /* Custom animations */
    @keyframes slideIn {
        from { 
            opacity: 0; 
            transform: translateY(20px); 
        }
        to { 
            opacity: 1; 
            transform: translateY(0); 
        }
    }
    
    .slide-in {
        animation: slideIn 0.5s ease-out;
    }
    
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
    """Render enhanced sidebar with navigation and info"""
    st.markdown("### 🎯 ResumeAlign")
    st.markdown("---")
    
    # App info
    with st.expander("ℹ️ About ResumeAlign"):
        st.markdown("""
        **ResumeAlign** helps you find the perfect candidates by:
        
        ✅ **Smart Analysis** - AI-powered resume evaluation  
        ✅ **Batch Processing** - Analyze multiple resumes at once  
        ✅ **Detailed Scoring** - Skills, experience, and education breakdown  
        ✅ **Export Options** - PDF and Excel reports  
        ✅ **Consistent Results** - Reliable scoring across analyses  
        ✅ **Candidate Ranking** - Automatic ranking by fit score
        """)
    
    # Quick stats
    if 'analysis_results' in st.session_state and st.session_state.analysis_results:
        with st.expander("📊 Current Session Stats"):
            results = st.session_state.analysis_results
            total_candidates = len(results)
            avg_score = sum(r.get('overall_score', 0) for r in results) / total_candidates if total_candidates > 0 else 0
            
            st.metric("Candidates Analyzed", total_candidates)
            st.metric("Average Score", f"{avg_score:.1f}%")
            
            # Top candidate
            if results:
                top_candidate = max(results, key=lambda x: x.get('overall_score', 0))
                st.metric("Top Candidate", 
                         top_candidate.get('candidate_name', 'Unknown'),
                         f"{top_candidate.get('overall_score', 0)}%")
    
    # Usage tips - expanded as requested
    with st.expander("💡 Usage Tips"):
        st.markdown("""
        **For Best Results:**
        
        1️⃣ **Detailed Job Description** - Include specific skills, experience levels, and requirements. The more specific, the better the matching.
        
        2️⃣ **Clear Resume Format** - PDF and DOCX files work best. Ensure text is selectable, not scanned images.
        
        3️⃣ **Batch Analysis** - Use batch mode for consistent scoring when analyzing multiple candidates for the same position.
        
        4️⃣ **Review Detailed Analysis** - Check the expanded reports for insights beyond just scores.
        
        5️⃣ **File Upload Tips** - Drag files directly to the upload area. If it doesn't work the first time, try again or click to browse.
        
        6️⃣ **Clear Session** - Use the Clear Session button to start fresh when analyzing for a different position.
        
        7️⃣ **Export Results** - Generate PDF or Excel reports for sharing with your team.
        
        **Supported File Types:** PDF, DOCX, TXT
        **Maximum File Size:** 10MB per file
        **Best Practices:** Use clear, professional resume formats with standard headings.
        """)
    
    st.markdown("---")
    st.markdown("*Powered by Google Gemini AI*")

def render_analysis_card(result, rank=None):
    """Render a single analysis result card with improved styling"""
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
    """Render a custom loading spinner with brand colors"""
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div class="spinner" style="display: inline-block; width: 40px; height: 40px; border: 3px solid #f3f3f3; border-radius: 50%; border-top: 3px solid #E53E3E;"></div>
        <p style="margin-top: 15px; color: #E53E3E; font-weight: 500;">{text}</p>
    </div>
    """, unsafe_allow_html=True)

def render_success_message(message, icon="✅"):
    """Render a custom success message"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #22c55e20 0%, transparent 100%);
        border-left: 4px solid #22c55e;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        animation: slideIn 0.5s ease-out;
    ">
        <p style="margin: 0; color: #166534; font-weight: 600;">
            {icon} {message}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_warning_message(message, icon="⚠️"):
    """Render a custom warning message"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #f59e0b20 0%, transparent 100%);
        border-left: 4px solid #f59e0b;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        animation: slideIn 0.5s ease-out;
    ">
        <p style="margin: 0; color: #92400e; font-weight: 600;">
            {icon} {message}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_error_message(message, icon="❌"):
    """Render a custom error message"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #ef444420 0%, transparent 100%);
        border-left: 4px solid #ef4444;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        animation: slideIn 0.5s ease-out;
    ">
        <p style="margin: 0; color: #991b1b; font-weight: 600;">
            {icon} {message}
        </p>
    </div>
    """, unsafe_allow_html=True)

def get_timestamp():
    """Get formatted timestamp for display"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
