import streamlit as st
from datetime import datetime

def apply_custom_css():
    """Apply custom CSS styling to the application"""
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header with improved styling"""
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🎯 ResumeAlign</h1>
        <p class="header-subtitle">AI-Powered Resume Analysis & Candidate Matching</p>
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
    
    # Usage tips
    with st.expander("💡 Usage Tips"):
        st.markdown("""
        **For Best Results:**
        
        1️⃣ **Detailed Job Description** - Include specific skills, experience levels, and requirements
        
        2️⃣ **Clear Resume Format** - PDF and DOCX files work best
        
        3️⃣ **Batch Analysis** - Use batch mode for consistent scoring when analyzing multiple candidates
        
        4️⃣ **Review Results** - Check the detailed analysis for insights beyond just scores
        """)
    
    st.markdown("---")
    st.markdown("*Powered by Google Gemini AI*")

def get_timestamp():
    """Get formatted timestamp for display"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
