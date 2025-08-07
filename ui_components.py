import streamlit as st

def load_custom_css():
    """Load custom CSS for the application"""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .upload-section {
        background-color: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .analysis-section {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .score-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .score-item {
        text-align: center;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #2E86AB;
    }
    
    .score-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2E86AB;
    }
    
    .score-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .recommendation-box {
        background-color: #e8f4fd;
        border-left: 4px solid #2E86AB;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .stProgress > div > div > div > div {
        background-color: #2E86AB;
    }
    
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

def display_header():
    """Display application header"""
    st.markdown('<h1 class="main-header">🎯 ResumeAlign</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Resume Analysis & Job Matching</p>', unsafe_allow_html=True)

def display_score_metrics(scores: dict):
    """Display score metrics in a formatted layout"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="score-item">
            <div class="score-number">{scores.get('overall', 0)}%</div>
            <div class="score-label">Overall Match</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="score-item">
            <div class="score-number">{scores.get('skills', 0)}%</div>
            <div class="score-label">Skills Match</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="score-item">
            <div class="score-number">{scores.get('experience', 0)}%</div>
            <div class="score-label">Experience</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="score-item">
            <div class="score-number">{scores.get('education', 0)}%</div>
            <div class="score-label">Education</div>
        </div>
        """, unsafe_allow_html=True)

def display_recommendation_box(content: str, box_type: str = "info"):
    """Display recommendation in styled box"""
    css_class = {
        "info": "recommendation-box",
        "warning": "warning-box", 
        "success": "success-box"
    }.get(box_type, "recommendation-box")
    
    st.markdown(f"""
    <div class="{css_class}">
        {content}
    </div>
    """, unsafe_allow_html=True)

def display_footer():
    """Display application footer"""
    st.markdown("""
    <div class="footer">
        Built with ❤️ using Streamlit & Google Gemini AI
    </div>
    """, unsafe_allow_html=True)
