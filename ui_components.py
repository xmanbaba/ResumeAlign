import streamlit as st
from datetime import datetime

def apply_custom_css():
    """Apply custom CSS styling to the application"""
    st.markdown("""
    <style>
    /* Main app styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
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
    
    /* Button styling improvements */
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
    
    /* File uploader styling */
    .stFileUploader > div > div {
        background-color: #f8fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div > div:hover {
        border-color: #667eea;
        background-color: #f0f4ff;
    }
    
    /* Text area improvements */
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Tab styling */
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
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
    }
    
    /* Metric styling */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    
    /* Progress bar styling */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar improvements */
    .sidebar .block-container {
        padding-top: 1rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #f8fafc;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Success/Error message styling */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 8px;
        border: none;
        font-weight: 500;
    }
    
    /* Container improvements */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Score display styling */
    .score-high { 
        color: #2d5a27; 
        background: #c6f6d5; 
    }
    
    .score-medium { 
        color: #744210; 
        background: #fef5e7; 
    }
    
    .score-low { 
        color: #742a2a; 
        background: #fed7d7; 
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .header-title {
            font-size: 2rem;
        }
        
        .header-subtitle {
            font-size: 1rem;
        }
        
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    
    /* Hide Streamlit style */
    #MainMenu {
        visibility: hidden;
    }
    
    footer {
        visibility: hidden;
    }
    
    .stDeployButton {
        display: none;
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
        from { 
            transform: rotate(0deg); 
        }
        to { 
            transform: rotate(360deg); 
        }
    }
    
    /* Improved spacing */
    .block-container > div > div > div > div {
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header with improved styling"""
    st.markdown("""
    <div class="header-container slide-in">
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

def render_analysis_card(result, rank=None):
    """Render a single analysis result card with improved styling"""
    name = result.get('candidate_name', 'Unknown Candidate')
    overall_score = result.get('overall_score', 0)
    skills_score = result.get('skills_score', 0)
    experience_score = result.get('experience_score', 0)
    education_score = result.get('education_score', 0)
    
    # Determine score color
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
            <h4 style="margin: 0; color: #2d3748;">{score_emoji} {rank_display}{name}</h4>
            <div class="{score_class}" style="padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                {overall_score}%
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">
            <div style="text-align: center;">
                <div style="font-size: 1.2em; font-weight: bold; color: #4a5568;">{skills_score}%</div>
                <div style="font-size: 0.8em; color: #718096;">Skills</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.2em; font-weight: bold; color: #4a5568;">{experience_score}%</div>
                <div style="font-size: 0.8em; color: #718096;">Experience</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 1.2em; font-weight: bold; color: #4a5568;">{education_score}%</div>
                <div style="font-size: 0.8em; color: #718096;">Education</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def render_loading_spinner(text="Processing..."):
    """Render a custom loading spinner"""
    st.markdown(f"""
    <div style="text-align: center; padding: 20px;">
        <div style="display: inline-block; width: 40px; height: 40px; border: 3px solid #f3f3f3; border-radius: 50%; border-top: 3px solid #667eea; animation: spin 1s linear infinite;"></div>
        <p style="margin-top: 15px; color: #667eea; font-weight: 500;">{text}</p>
    </div>
    """, unsafe_allow_html=True)

def render_score_gauge(score, label):
    """Render a visual score gauge"""
    # Determine color based on score
    if score >= 80:
        color = "#22c55e"  # Green
    elif score >= 60:
        color = "#f59e0b"  # Yellow
    else:
        color = "#ef4444"  # Red
    
    # Calculate the circumference and dash offset
    radius = 54
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference * (1 - score/100)
    
    gauge_html = f"""
    <div style="text-align: center; margin: 10px;">
        <div style="position: relative; width: 120px; height: 120px; margin: 0 auto;">
            <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="{radius}" fill="none" stroke="#e5e7eb" stroke-width="8"/>
                <circle cx="60" cy="60" r="{radius}" fill="none" stroke="{color}" stroke-width="8"
                        stroke-dasharray="{circumference}" 
                        stroke-dashoffset="{dash_offset}"
                        transform="rotate(-90 60 60)"/>
                <text x="60" y="65" text-anchor="middle" font-size="18" font-weight="bold" fill="{color}">
                    {score}%
                </text>
            </svg>
        </div>
        <div style="font-weight: 600; color: #4a5568; margin-top: 5px;">{label}</div>
    </div>
    """
    
    return gauge_html

def render_comparison_table(results):
    """Render a comparison table for multiple candidates"""
    if not results:
        return
    
    # Sort by overall score
    sorted_results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
    
    table_html = """
    <div style="overflow-x: auto; margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
            <thead style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                <tr>
                    <th style="padding: 15px; text-align: left;">Rank</th>
                    <th style="padding: 15px; text-align: left;">Candidate</th>
                    <th style="padding: 15px; text-align: center;">Overall</th>
                    <th style="padding: 15px; text-align: center;">Skills</th>
                    <th style="padding: 15px; text-align: center;">Experience</th>
                    <th style="padding: 15px; text-align: center;">Education</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for i, result in enumerate(sorted_results, 1):
        name = result.get('candidate_name', 'Unknown')
        overall = result.get('overall_score', 0)
        skills = result.get('skills_score', 0)
        experience = result.get('experience_score', 0)
        education = result.get('education_score', 0)
        
        # Row styling based on rank
        if i == 1:
            row_style = "background-color: #f0fff4; border-left: 4px solid #22c55e;"
        elif i == 2:
            row_style = "background-color: #fffbf0; border-left: 4px solid #f59e0b;"
        elif i == 3:
            row_style = "background-color: #fef2f2; border-left: 4px solid #ef4444;"
        else:
            row_style = "background-color: #f8fafc;"
        
        table_html += f"""
                <tr style="{row_style}">
                    <td style="padding: 12px; font-weight: bold;">#{i}</td>
                    <td style="padding: 12px; font-weight: 600;">{name}</td>
                    <td style="padding: 12px; text-align: center; font-weight: bold; color: #2d3748;">{overall}%</td>
                    <td style="padding: 12px; text-align: center;">{skills}%</td>
                    <td style="padding: 12px; text-align: center;">{experience}%</td>
                    <td style="padding: 12px; text-align: center;">{education}%</td>
                </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)

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

def render_info_message(message, icon="ℹ️"):
    """Render a custom info message"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #3b82f620 0%, transparent 100%);
        border-left: 4px solid #3b82f6;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        animation: slideIn 0.5s ease-out;
    ">
        <p style="margin: 0; color: #1e40af; font-weight: 600;">
            {icon} {message}
        </p>
    </div>
    """, unsafe_allow_html=True)

def get_timestamp():
    """Get formatted timestamp for display"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
