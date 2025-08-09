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
    if 'uploaded_files_info' not in st.session_state:
        st.session_state.uploaded_files_info = []

def clear_session():
    """Clear ALL session state data completely - FIXED VERSION"""
    logger.info("Clearing all session state data...")
    
    # List of ALL keys to clear
    keys_to_clear = [
        'analysis_results', 
        'job_description', 
        'analysis_history', 
        'candidate_cache', 
        'batch_results',
        'uploaded_files_info',
        'single_file',
        'batch_files',
        'job_desc_input'
    ]
    
    # Clear each key
    for key in keys_to_clear:
        if key in st.session_state:
            logger.info(f"Clearing session key: {key}")
            del st.session_state[key]
    
    # Also clear file uploader widgets by setting their keys to None
    # This forces a complete refresh of the file uploaders
    st.session_state['clear_trigger'] = datetime.now().timestamp()
    
    logger.info("Session cleared successfully")
    st.success("🗑️ Session cleared successfully!")
    st.rerun()

def generate_candidate_hash(text_content, filename):
    """Generate a hash for candidate data to enable caching"""
    content_str = f"{filename}_{text_content[:500]}"  # Use first 500 chars for hash
    return hashlib.md5(content_str.encode()).hexdigest()

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
                color = "#22c55e"  # Green
                emoji = "🌟"
            elif score >= 60:
                color = "#f59e0b"  # Yellow
                emoji = "⭐"
            else:
                color = "#ef4444"  # Red
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
        
        for i, result in enumerate(sorted_results, 1):
            name = result.get('candidate_name', 'Unknown Candidate')
            overall_score = result.get('overall_score', 0)
            
            with st.expander(f"📄 {name} - {overall_score}%", expanded=(i == 1)):
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Scores Breakdown:**")
                    
                    # Display metrics with proper values
                    st.metric("Skills Match", f"{result.get('skills_score', 0)}%")
                    st.metric("Experience", f"{result.get('experience_score', 0)}%")
                    st.metric("Education", f"{result.get('education_score', 0)}%")
                    st.metric("Overall", f"{overall_score}%")
                
                with col2:
                    st.markdown("**📝 Detailed Analysis:**")
                    
                    # Skills analysis
                    skills_analysis = result.get('skills_analysis', 'No analysis available')
                    if skills_analysis and skills_analysis != 'Analysis not available':
                        st.markdown("**🔧 Skills Analysis:**")
                        st.write(skills_analysis)
                    else:
                        st.warning("Skills analysis not available")
                    
                    # Experience analysis
                    experience_analysis = result.get('experience_analysis', 'No analysis available')
                    if experience_analysis and experience_analysis != 'Analysis not available':
                        st.markdown("**💼 Experience Analysis:**")
                        st.write(experience_analysis)
                    else:
                        st.warning("Experience analysis not available")
                    
                    # Education analysis
                    education_analysis = result.get('education_analysis', 'No analysis available')
                    if education_analysis and education_analysis != 'Analysis not available':
                        st.markdown("**🎓 Education Analysis:**")
                        st.write(education_analysis)
                    else:
                        st.warning("Education analysis not available")
                    
                    # Fit assessment
                    fit_assessment = result.get('fit_assessment', '')
                    if fit_assessment and fit_assessment != 'Assessment not available':
                        st.markdown("**🎯 Overall Fit Assessment:**")
                        st.info(fit_assessment)
                    
                    # Strengths and weaknesses
                    strengths = result.get('strengths', [])
                    weaknesses = result.get('weaknesses', [])
                    
                    if strengths:
                        st.markdown("**✅ Key Strengths:**")
                        for strength in strengths[:3]:  # Show top 3
                            st.write(f"• {strength}")
                    
                    if weaknesses:
                        st.markdown("**⚠️ Areas for Improvement:**")
                        for weakness in weaknesses[:3]:  # Show top 3
                            st.write(f"• {weakness}")
                    
                    # Recommendations
                    recommendations = result.get('recommendations', '')
                    if recommendations and recommendations != 'No specific recommendations':
                        st.markdown("**💡 Recommendations:**")
                        st.info(recommendations)
    
    with tab3:
        # Export options
        st.subheader("📄 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Generate Excel Report", use_container_width=True):
                try:
                    excel_data = create_excel_report(results)
                    if excel_data:
                        st.download_button(
                            label="⬇️ Download Excel Report",
                            data=excel_data,
                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success("Excel report generated successfully!")
                    else:
                        st.error("Failed to generate Excel report")
                except Exception as e:
                    st.error(f"Error generating Excel report: {str(e)}")
        
        with col2:
            if st.button("📑 Generate PDF Report", use_container_width=True):
                try:
                    with st.spinner("Generating PDF report..."):
                        pdf_data = generate_comparison_pdf(results, job_description)
                        if pdf_data:
                            st.download_button(
                                label="⬇️ Download PDF Report",
                                data=pdf_data,
                                file_name=f"resume_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            st.success("PDF report generated successfully!")
                        else:
                            st.error("Failed to generate PDF report")
                except Exception as e:
                    st.error(f"Error generating PDF report: {str(e)}")

def create_excel_report(results):
    """Create an Excel report with analysis results"""
    try:
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
                'Education Analysis': result.get('education_analysis', ''),
                'Fit Assessment': result.get('fit_assessment', ''),
                'Recommendations': result.get('recommendations', ''),
                'Strengths': '; '.join(result.get('strengths', [])),
                'Areas for Improvement': '; '.join(result.get('weaknesses', []))
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
    except Exception as e:
        logger.error(f"Error creating Excel report: {str(e)}")
        return None

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
    
    # Render header with correct branding
    render_header()
    
    # Sidebar
    with st.sidebar:
        render_sidebar()
        
        # Clear session button with improved functionality
        st.markdown("---")
        if st.button("🗑️ Clear Session", 
                    use_container_width=True, 
                    help="Clear all analysis results, job description, and uploaded files"):
            clear_session()
        
        # Show analysis history count
        if st.session_state.analysis_results:
            st.info(f"📊 {len(st.session_state.analysis_results)} candidates analyzed")
    
    # Main content area
    st.markdown("## 🎯 Smart Resume Analysis")
    
    # Job description input with proper session state management
    with st.container():
        st.markdown("### 📋 Job Description")
        
        # Use a unique key for job description
        job_desc_key = "job_desc_input"
        if 'clear_trigger' in st.session_state:
            job_desc_key = f"job_desc_input_{st.session_state.clear_trigger}"
        
        job_desc = st.text_area(
            "Enter the job description to analyze resumes against:",
            value=st.session_state.get('job_description', ''),
            height=200,
            placeholder="Paste the job description here including required skills, experience, and qualifications...",
            key=job_desc_key,
            help="Provide detailed job requirements for better matching accuracy"
        )
        
        # Update session state when job description changes
        if job_desc != st.session_state.get('job_description', ''):
            st.session_state.job_description = job_desc
    
    # Analysis tabs
    tab1, tab2 = st.tabs(["📄 Single Resume Analysis", "📁 Batch Analysis"])
    
    with tab1:
        st.markdown("### 📄 Analyze Single Resume")
        st.markdown("Upload a resume to get detailed analysis and scoring against your job description.")
        
        # File uploader with unique key to handle clearing
        single_file_key = "single_file"
        if 'clear_trigger' in st.session_state:
            single_file_key = f"single_file_{st.session_state.clear_trigger}"
        
        uploaded_file = st.file_uploader(
            "Upload resume (PDF, DOCX, or TXT)",
            type=['pdf', 'docx', 'txt'],
            key=single_file_key,
            help="Select a resume file to analyze against the job description. Drag and drop or click to browse."
        )
        
        if uploaded_file and st.session_state.job_description.strip():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.info(f"📁 File selected: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            with col2:
                analyze_button = st.button(
                    "🔍 Analyze Resume",
                    use_container_width=True,
                    type="primary",
                    help="Start AI analysis of the resume"
                )
            
            if analyze_button:
                with st.spinner("🔄 Analyzing resume... This may take a few moments."):
                    try:
                        # Extract text from file
                        file_text = extract_text_from_file(uploaded_file)
                        
                        if file_text and file_text.strip():
                            logger.info(f"Extracted {len(file_text)} characters from {uploaded_file.name}")
                            
                            # Generate candidate hash for caching
                            candidate_hash = generate_candidate_hash(file_text, uploaded_file.name)
                            cache_key = f"{candidate_hash}_{hashlib.md5(st.session_state.job_description.encode()).hexdigest()}"
                            
                            # Check cache first
                            if cache_key in st.session_state.candidate_cache:
                                st.info("📋 Using cached analysis results")
                                result = st.session_state.candidate_cache[cache_key]
                            else:
                                # Analyze resume with proper error handling
                                result = analyze_single_candidate(
                                    file_text, 
                                    st.session_state.job_description, 
                                    uploaded_file.name,
                                    batch_mode=False
                                )
                                
                                # Cache the result if successful
                                if result and result.get('overall_score', 0) > 0:
                                    st.session_state.candidate_cache[cache_key] = result
                            
                            if result and result.get('overall_score', 0) > 0:
                                # Add to results with timestamp
                                result['timestamp'] = datetime.now()
                                result['analysis_type'] = 'single'
                                
                                # Add to session results
                                st.session_state.analysis_results.append(result)
                                
                                st.success("✅ Analysis completed successfully!")
                                
                                # Display immediate results
                                st.markdown("#### 📊 Analysis Results")
                                display_analysis_results([result], st.session_state.job_description)
                            else:
                                st.error("❌ Analysis failed. The AI could not process this resume. Please check if the file contains readable text and try again.")
                                logger.error(f"Analysis returned invalid result: {result}")
                        else:
                            st.error("❌ Could not extract text from the uploaded file. Please ensure the file contains readable text and is not corrupted.")
                    
                    except Exception as e:
                        logger.error(f"Single analysis error: {str(e)}")
                        st.error(f"❌ Analysis failed: {str(e)}")
        elif uploaded_file and not st.session_state.job_description.strip():
            st.warning("⚠️ Please enter a job description first before analyzing resumes.")
        elif not uploaded_file and st.session_state.job_description.strip():
            st.info("👆 Please upload a resume file to begin analysis.")
    
    with tab2:
        st.markdown("### 📁 Batch Resume Analysis")
        st.markdown("Upload multiple resumes for consistent analysis and automatic ranking.")
        
        # File uploader for batch with unique key
        batch_files_key = "batch_files"
        if 'clear_trigger' in st.session_state:
            batch_files_key = f"batch_files_{st.session_state.clear_trigger}"
        
        uploaded_files = st.file_uploader(
            "Upload multiple resumes",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            key=batch_files_key,
            help="Select multiple resume files for batch analysis. All files will be analyzed against the same job description."
        )
        
        if uploaded_files and st.session_state.job_description.strip():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.info(f"📁 {len(uploaded_files)} files selected for batch analysis")
                # Show file names
                with st.expander("View selected files"):
                    for i, file in enumerate(uploaded_files, 1):
                        st.write(f"{i}. {file.name} ({file.size} bytes)")
            
            with col3:
                analyze_batch_button = st.button(
                    "🔍 Analyze All",
                    use_container_width=True,
                    type="primary",
                    help="Start batch analysis of all uploaded resumes"
                )
            
            if analyze_batch_button:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    batch_results = []
                    total_files = len(uploaded_files)
                    
                    status_text.info("🚀 Starting batch analysis...")
                    
                    for i, uploaded_file in enumerate(uploaded_files):
                        # Update progress
                        progress = (i) / total_files
                        progress_bar.progress(progress)
                        status_text.info(f"🔄 Analyzing {uploaded_file.name}... ({i+1}/{total_files})")
                        
                        try:
                            # Extract text
                            file_text = extract_text_from_file(uploaded_file)
                            
                            if file_text and file_text.strip():
                                logger.info(f"Processing {uploaded_file.name} - {len(file_text)} characters")
                                
                                # Generate candidate hash for caching
                                candidate_hash = generate_candidate_hash(file_text, uploaded_file.name)
                                cache_key = f"{candidate_hash}_{hashlib.md5(st.session_state.job_description.encode()).hexdigest()}"
                                
                                # Check cache first
                                if cache_key in st.session_state.candidate_cache:
                                    result = st.session_state.candidate_cache[cache_key]
                                    status_text.info(f"📋 Using cached result for {uploaded_file.name}")
                                else:
                                    # Analyze with consistent batch settings
                                    result = analyze_single_candidate(
                                        file_text, 
                                        st.session_state.job_description, 
                                        uploaded_file.name,
                                        batch_mode=True  # Use consistent settings for batch
                                    )
                                    
                                    # Cache the result if successful
                                    if result and result.get('overall_score', 0) > 0:
                                        st.session_state.candidate_cache[cache_key] = result
                                
                                if result and result.get('overall_score', 0) > 0:
                                    result['timestamp'] = datetime.now()
                                    result['analysis_type'] = 'batch'
                                    batch_results.append(result)
                                    logger.info(f"Successfully analyzed {uploaded_file.name} - Score: {result.get('overall_score', 0)}%")
                                else:
                                    logger.warning(f"Failed to analyze {uploaded_file.name} - Invalid result")
                                    status_text.warning(f"⚠️ Could not analyze {uploaded_file.name}")
                            else:
                                logger.warning(f"Could not extract text from {uploaded_file.name}")
                                status_text.warning(f"⚠️ Could not extract text from {uploaded_file.name}")
                        
                        except Exception as e:
                            logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
                            status_text.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                        
                        # Small delay to prevent rate limiting and show progress
                        time.sleep(0.5)
                    
                    # Final progress update
                    progress_bar.progress(1.0)
                    
                    if batch_results:
                        # Add to session state
                        st.session_state.analysis_results.extend(batch_results)
                        
                        status_text.success(f"✅ Successfully analyzed {len(batch_results)} out of {total_files} resumes!")
                        
                        # Display results
                        st.markdown("#### 📊 Batch Analysis Results")
                        display_analysis_results(batch_results, st.session_state.job_description)
                    else:
                        status_text.error("❌ No resumes could be analyzed successfully. Please check the file formats and try again.")
                
                except Exception as e:
                    logger.error(f"Batch analysis error: {str(e)}")
                    status_text.error(f"❌ Batch analysis failed: {str(e)}")
                
                finally:
                    # Clean up progress indicators after 3 seconds
                    time.sleep(3)
                    progress_bar.empty()
                    if status_text:
                        status_text.empty()
        
        elif uploaded_files and not st.session_state.job_description.strip():
            st.warning("⚠️ Please enter a job description first before analyzing resumes.")
        elif not uploaded_files and st.session_state.job_description.strip():
            st.info("👆 Please upload resume files to begin batch analysis.")
    
    # Display existing results if any
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("## 📊 Previous Analysis Results")
        st.markdown(f"Showing results from your current session ({len(st.session_state.analysis_results)} candidates analyzed)")
        display_analysis_results(st.session_state.analysis_results, st.session_state.job_description)

if __name__ == "__main__":
    main()
