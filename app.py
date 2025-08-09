import streamlit as st
import pandas as pd
import io
import time
import logging
from datetime import datetime
import hashlib
import json

# Import our custom modules
from ai_analysis import analyze_single_candidate, analyze_batch_candidates
from file_utils import extract_text_from_file, save_uploaded_file
from name_extraction import extract_name_from_text, extract_name_from_filename
from pdf_generator import generate_comparison_pdf
from ui_components import apply_custom_css, render_header, render_sidebar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables"""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'candidate_cache' not in st.session_state:
        st.session_state.candidate_cache = {}

def generate_candidate_hash(text_content, filename):
    """Generate a hash for candidate data to enable caching"""
    content_str = f"{filename}_{text_content[:500]}"  # Use first 500 chars for hash
    return hashlib.md5(content_str.encode()).hexdigest()

def clear_session():
    """Clear all session state data"""
    keys_to_clear = [
        'analysis_results', 'job_description', 'analysis_history', 
        'candidate_cache', 'batch_results'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def display_analysis_results(results, job_description):
    """Display analysis results with improved formatting"""
    if not results:
        st.warning("No analysis results to display.")
        return
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Rankings", "📋 Detailed Analysis", "📄 Export"])
    
    with tab1:
        # Sort candidates by overall score
        sorted_results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # Display top candidates
        st.subheader("🏆 Candidate Rankings")
        
        for i, result in enumerate(sorted_results, 1):
            score = result.get('overall_score', 0)
            name = result.get('candidate_name', 'Unknown Candidate')
            
            # Color code based on score
            if score >= 80:
                color = "#2E8B57"  # Sea Green
                emoji = "🌟"
            elif score >= 60:
                color = "#DAA520"  # Golden Rod
                emoji = "⭐"
            else:
                color = "#CD5C5C"  # Indian Red
                emoji = "📋"
            
            with st.container():
                st.markdown(f"""
                <div style="
                    background: linear-gradient(90deg, {color}20 0%, transparent 100%);
                    border-left: 4px solid {color};
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                ">
                    <h4 style="color: {color}; margin: 0;">{emoji} #{i} {name}</h4>
                    <p style="font-size: 18px; font-weight: bold; margin: 5px 0;">
                        Overall Score: {score}%
                    </p>
                    <p style="margin: 0; opacity: 0.8;">
                        Skills: {result.get('skills_score', 0)}% | 
                        Experience: {result.get('experience_score', 0)}% | 
                        Education: {result.get('education_score', 0)}%
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        # Detailed analysis for each candidate
        st.subheader("📋 Detailed Candidate Analysis")
        
        for result in sorted_results:
            name = result.get('candidate_name', 'Unknown Candidate')
            with st.expander(f"📄 {name} - {result.get('overall_score', 0)}%"):
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Scores Breakdown:**")
                    scores = {
                        "Skills Match": result.get('skills_score', 0),
                        "Experience": result.get('experience_score', 0),
                        "Education": result.get('education_score', 0)
                    }
                    
                    for category, score in scores.items():
                        st.metric(category, f"{score}%")
                
                with col2:
                    st.markdown("**Detailed Analysis:**")
                    
                    # Skills analysis
                    if 'skills_analysis' in result:
                        st.markdown("**🔧 Skills Analysis:**")
                        st.write(result['skills_analysis'])
                    
                    # Experience analysis
                    if 'experience_analysis' in result:
                        st.markdown("**💼 Experience Analysis:**")
                        st.write(result['experience_analysis'])
                    
                    # Recommendations
                    if 'recommendations' in result:
                        st.markdown("**💡 Recommendations:**")
                        st.write(result['recommendations'])
    
    with tab3:
        # Export options
        st.subheader("📄 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Excel Report", use_container_width=True):
                excel_data = create_excel_report(results)
                st.download_button(
                    label="⬇️ Download Excel Report",
                    data=excel_data,
                    file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col2:
            if st.button("📑 Generate PDF Report", use_container_width=True):
                pdf_data = generate_comparison_pdf(results, job_description)
                if pdf_data:
                    st.download_button(
                        label="⬇️ Download PDF Report",
                        data=pdf_data,
                        file_name=f"resume_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

def create_excel_report(results):
    """Create an Excel report with analysis results"""
    # Create DataFrame
    data = []
    for result in results:
        data.append({
            'Candidate Name': result.get('candidate_name', 'Unknown'),
            'Overall Score': result.get('overall_score', 0),
            'Skills Score': result.get('skills_score', 0),
            'Experience Score': result.get('experience_score', 0),
            'Education Score': result.get('education_score', 0),
            'Skills Analysis': result.get('skills_analysis', ''),
            'Experience Analysis': result.get('experience_analysis', ''),
            'Recommendations': result.get('recommendations', '')
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Analysis Results', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Analysis Results']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return output.getvalue()

def main():
    # Configure page
    st.set_page_config(
        page_title="ResumeAlign - AI-Powered Resume Analysis",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Apply custom CSS
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Render header
    render_header()
    
    # Sidebar
    with st.sidebar:
        render_sidebar()
        
        # Clear session button with improved styling
        if st.button("🗑️ Clear Session", 
                    use_container_width=True, 
                    help="Clear all analysis results and start fresh"):
            clear_session()
        
        # Show analysis history count
        if st.session_state.analysis_results:
            st.info(f"📊 {len(st.session_state.analysis_results)} candidates analyzed")
    
    # Main content area
    st.markdown("## 🎯 Smart Resume Analysis")
    
    # Job description input
    with st.container():
        st.markdown("### 📋 Job Description")
        job_desc = st.text_area(
            "Enter the job description to analyze resumes against:",
            value=st.session_state.get('job_description', ''),
            height=200,
            placeholder="Paste the job description here including required skills, experience, and qualifications...",
            key="job_desc_input"
        )
        
        if job_desc != st.session_state.job_description:
            st.session_state.job_description = job_desc
    
    # Analysis tabs
    tab1, tab2 = st.tabs(["📄 Single Resume Analysis", "📁 Batch Analysis"])
    
    with tab1:
        st.markdown("### 📄 Analyze Single Resume")
        
        uploaded_file = st.file_uploader(
            "Upload resume (PDF, DOCX, or TXT)",
            type=['pdf', 'docx', 'txt'],
            key="single_file",
            help="Select a resume file to analyze against the job description"
        )
        
        if uploaded_file and st.session_state.job_description:
            col1, col2 = st.columns([3, 1])
            
            with col2:
                analyze_button = st.button(
                    "🔍 Analyze Resume",
                    use_container_width=True,
                    type="primary"
                )
            
            if analyze_button:
                with st.spinner("🔄 Analyzing resume..."):
                    try:
                        # Extract text from file
                        file_text = extract_text_from_file(uploaded_file)
                        
                        if file_text:
                            # Generate candidate hash for caching
                            candidate_hash = generate_candidate_hash(file_text, uploaded_file.name)
                            
                            # Check cache first
                            cache_key = f"{candidate_hash}_{hashlib.md5(st.session_state.job_description.encode()).hexdigest()}"
                            
                            if cache_key in st.session_state.candidate_cache:
                                st.info("📋 Using cached analysis results")
                                result = st.session_state.candidate_cache[cache_key]
                            else:
                                # Analyze resume
                                result = analyze_single_candidate(
                                    file_text, 
                                    st.session_state.job_description, 
                                    uploaded_file.name
                                )
                                
                                # Cache the result
                                st.session_state.candidate_cache[cache_key] = result
                            
                            if result:
                                # Add to results
                                result['timestamp'] = datetime.now()
                                st.session_state.analysis_results.append(result)
                                
                                st.success("✅ Analysis completed!")
                                
                                # Display immediate results
                                display_analysis_results([result], st.session_state.job_description)
                            else:
                                st.error("❌ Analysis failed. Please try again.")
                        else:
                            st.error("❌ Could not extract text from the uploaded file.")
                    
                    except Exception as e:
                        logger.error(f"Single analysis error: {str(e)}")
                        st.error(f"❌ Analysis failed: {str(e)}")
    
    with tab2:
        st.markdown("### 📁 Batch Resume Analysis")
        
        uploaded_files = st.file_uploader(
            "Upload multiple resumes",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            key="batch_files",
            help="Select multiple resume files for batch analysis"
        )
        
        if uploaded_files and st.session_state.job_description:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"📁 {len(uploaded_files)} files selected")
            
            with col3:
                analyze_batch_button = st.button(
                    "🔍 Analyze All",
                    use_container_width=True,
                    type="primary"
                )
            
            if analyze_batch_button:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    batch_results = []
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"🔄 Analyzing {uploaded_file.name}...")
                        progress_bar.progress((i + 1) / len(uploaded_files))
                        
                        # Extract text
                        file_text = extract_text_from_file(uploaded_file)
                        
                        if file_text:
                            # Generate candidate hash for caching
                            candidate_hash = generate_candidate_hash(file_text, uploaded_file.name)
                            cache_key = f"{candidate_hash}_{hashlib.md5(st.session_state.job_description.encode()).hexdigest()}"
                            
                            # Check cache first
                            if cache_key in st.session_state.candidate_cache:
                                result = st.session_state.candidate_cache[cache_key]
                                status_text.text(f"📋 Using cached result for {uploaded_file.name}")
                            else:
                                # Analyze with consistent settings
                                result = analyze_single_candidate(
                                    file_text, 
                                    st.session_state.job_description, 
                                    uploaded_file.name,
                                    batch_mode=True  # Use consistent settings for batch
                                )
                                
                                # Cache the result
                                if result:
                                    st.session_state.candidate_cache[cache_key] = result
                            
                            if result:
                                result['timestamp'] = datetime.now()
                                batch_results.append(result)
                        
                        # Small delay to prevent rate limiting
                        time.sleep(0.5)
                    
                    progress_bar.progress(1.0)
                    status_text.text("✅ Batch analysis completed!")
                    
                    if batch_results:
                        # Add to session state
                        st.session_state.analysis_results.extend(batch_results)
                        
                        st.success(f"✅ Successfully analyzed {len(batch_results)} resumes!")
                        
                        # Display results
                        display_analysis_results(batch_results, st.session_state.job_description)
                    else:
                        st.error("❌ No resumes could be analyzed.")
                
                except Exception as e:
                    logger.error(f"Batch analysis error: {str(e)}")
                    st.error(f"❌ Batch analysis failed: {str(e)}")
                
                finally:
                    progress_bar.empty()
                    status_text.empty()
    
    # Display existing results if any
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        display_analysis_results(st.session_state.analysis_results, st.session_state.job_description)

if __name__ == "__main__":
    main()
