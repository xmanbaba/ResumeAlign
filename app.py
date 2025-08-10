import streamlit as st
import pandas as pd
import io
import time
import logging
from datetime import datetime
import hashlib
import json
import uuid

# Import our custom modules
from ai_analysis import analyze_single_candidate, analyze_batch_candidates
from file_utils import extract_text_from_file, save_uploaded_file
from name_extraction import extract_name_from_text, extract_name_from_filename
from pdf_generator import generate_comparison_pdf, generate_single_candidate_pdf, generate_batch_zip_reports
from ui_components import (
    apply_custom_css, render_header, render_sidebar, render_compact_file_info,
    render_persistent_error, render_persistent_success, render_file_limit_warning
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BATCH_LIMIT = 5
MAX_FILE_SIZE_MB = 10

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
    if 'error_messages' not in st.session_state:
        st.session_state.error_messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]

def clear_session():
    """Clear ALL session state data completely"""
    logger.info("Clearing all session state data...")
    
    # List of ALL keys to clear
    keys_to_clear = [
        'analysis_results', 
        'job_description', 
        'analysis_history', 
        'candidate_cache', 
        'batch_results',
        'uploaded_files_info',
        'error_messages',
        'single_file',
        'batch_files',
        'job_desc_input'
    ]
    
    # Clear each key
    for key in keys_to_clear:
        if key in st.session_state:
            logger.info(f"Clearing session key: {key}")
            del st.session_state[key]
    
    # Generate new session ID and clear trigger
    st.session_state.session_id = str(uuid.uuid4())[:8]
    st.session_state['clear_trigger'] = datetime.now().timestamp()
    
    logger.info("Session cleared successfully")
    render_persistent_success("Session cleared successfully! All data removed.")
    time.sleep(1)
    st.rerun()

def validate_uploaded_files(uploaded_files, is_batch=False):
    """Validate uploaded files with proper error handling"""
    if not uploaded_files:
        return [], ["No files uploaded"]
    
    files = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
    valid_files = []
    errors = []
    
    # Check batch limit
    if is_batch and len(files) > BATCH_LIMIT:
        errors.append(f"Maximum {BATCH_LIMIT} files per batch. You uploaded {len(files)} files.")
        return [], errors
    
    for file in files:
        # Check file type
        if not file.name.lower().endswith(('.pdf', '.docx', '.txt')):
            errors.append(f"Unsupported file type: {file.name}")
            continue
        
        # Check file size
        file_size_mb = len(file.getvalue()) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            errors.append(f"File too large: {file.name} ({file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB limit)")
            continue
        
        valid_files.append(file)
    
    return valid_files, errors

def display_persistent_errors(errors):
    """Display persistent error messages"""
    if not errors:
        return
    
    for error in errors:
        render_persistent_error(error)

def generate_candidate_hash(text_content, filename):
    """Generate hash for caching"""
    content_str = f"{filename}_{text_content[:500]}"
    return hashlib.md5(content_str.encode()).hexdigest()

def create_excel_report(results):
    """Create Excel report with error handling"""
    try:
        data = []
        for result in results:
            # Include interview questions in Excel
            interview_questions = result.get('interview_questions', [])
            questions_text = '\n'.join([f"{i+1}. {q}" for i, q in enumerate(interview_questions)])
            
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
                'Areas for Improvement': '; '.join(result.get('weaknesses', [])),
                'Interview Questions': questions_text
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Analysis Results', index=False)
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
        logger.error(f"Excel generation error: {str(e)}")
        return None

def create_json_report(results):
    """Create JSON report"""
    try:
        report_data = {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_candidates': len(results),
            'candidates': results
        }
        return json.dumps(report_data, indent=2)
    except Exception as e:
        logger.error(f"JSON generation error: {str(e)}")
        return None

def display_analysis_results(results, job_description):
    """Display analysis results with improved formatting and FIXED button IDs"""
    if not results:
        st.warning("No analysis results to display.")
        return
    
    # Create unique session identifier for all buttons
    session_id = st.session_state.get('session_id', 'default')
    timestamp = str(int(datetime.now().timestamp() * 1000))  # Millisecond timestamp
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Rankings", "📋 Detailed Analysis", "📄 Export"])
    
    with tab1:
        # Sort candidates by overall score
        sorted_results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
        
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
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(90deg, {color}20 0%, transparent 100%);
                border-left: 4px solid {color};
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
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
        st.subheader("📋 Detailed Candidate Analysis")
        
        for i, result in enumerate(sorted_results, 1):
            name = result.get('candidate_name', 'Unknown Candidate')
            overall_score = result.get('overall_score', 0)
            
            with st.expander(f"📄 {name} - {overall_score}%", expanded=(i == 1)):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**Scores:**")
                    st.metric("Skills", f"{result.get('skills_score', 0)}%")
                    st.metric("Experience", f"{result.get('experience_score', 0)}%")
                    st.metric("Education", f"{result.get('education_score', 0)}%")
                    st.metric("Overall", f"{overall_score}%")
                
                with col2:
                    st.markdown("**Analysis:**")
                    
                    # Display analyses with validation
                    skills_analysis = result.get('skills_analysis', '')
                    if skills_analysis and skills_analysis != 'Analysis not available':
                        st.markdown("**🔧 Skills:**")
                        st.write(skills_analysis)
                    
                    experience_analysis = result.get('experience_analysis', '')
                    if experience_analysis and experience_analysis != 'Analysis not available':
                        st.markdown("**💼 Experience:**")
                        st.write(experience_analysis)
                    
                    education_analysis = result.get('education_analysis', '')
                    if education_analysis and education_analysis != 'Analysis not available':
                        st.markdown("**🎓 Education:**")
                        st.write(education_analysis)
                    
                    # Strengths and weaknesses
                    strengths = result.get('strengths', [])
                    weaknesses = result.get('weaknesses', [])
                    
                    if strengths:
                        st.markdown("**✅ Strengths:**")
                        for strength in strengths:
                            if strength and len(strength.strip()) > 5:
                                st.write(f"• {strength}")
                    
                    if weaknesses:
                        st.markdown("**⚠️ Areas for Improvement:**")
                        for weakness in weaknesses:
                            if weakness and len(weakness.strip()) > 5:
                                st.write(f"• {weakness}")
                    
                    # Interview Questions - FIXED SECTION
                    interview_questions = result.get('interview_questions', [])
                    if interview_questions:
                        st.markdown("**❓ Interview Questions:**")
                        for j, question in enumerate(interview_questions, 1):
                            if question and len(question.strip()) > 10:
                                st.write(f"{j}. {question}")
                    
                    # Recommendations
                    recommendations = result.get('recommendations', '')
                    if recommendations and recommendations != 'Please try the analysis again':
                        st.markdown("**💡 Recommendations:**")
                        st.info(recommendations)
    
    with tab3:
        st.subheader("📄 Export Results")
        
        # FIXED: Reordered buttons - PDF first, Excel second, JSON third
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # PDF Download - FIXED unique keys
            pdf_button_key = f"pdf_btn_{session_id}_{timestamp}_{len(results)}"
            if st.button("📑 Download PDF", key=pdf_button_key, use_container_width=True):
                try:
                    with st.spinner("Generating PDF/ZIP..."):
                        if len(results) == 1:
                            # Single candidate PDF
                            pdf_data = generate_single_candidate_pdf(results[0], job_description)
                            if pdf_data:
                                candidate_name = results[0].get('candidate_name', 'Unknown')
                                safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
                                
                                st.download_button(
                                    label="⬇️ Download PDF Report",
                                    data=pdf_data,
                                    file_name=f"Resume_Analysis_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                    mime="application/pdf",
                                    key=f"pdf_download_{session_id}_{timestamp}",
                                    use_container_width=True
                                )
                                render_persistent_success("PDF report ready for download!")
                        else:
                            # Multiple candidates ZIP
                            zip_data = generate_batch_zip_reports(results, job_description)
                            if zip_data:
                                st.download_button(
                                    label="⬇️ Download ZIP Reports",
                                    data=zip_data,
                                    file_name=f"Resume_Analysis_Batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                                    mime="application/zip",
                                    key=f"zip_download_{session_id}_{timestamp}",
                                    use_container_width=True
                                )
                                render_persistent_success("ZIP file with individual reports ready for download!")
                except Exception as e:
                    render_persistent_error(f"Failed to generate PDF: {str(e)}")
        
        with col2:
            # Excel Download - FIXED unique keys
            excel_button_key = f"excel_btn_{session_id}_{timestamp}_{len(results)}"
            if st.button("📊 Download Excel", key=excel_button_key, use_container_width=True):
                try:
                    excel_data = create_excel_report(results)
                    if excel_data:
                        st.download_button(
                            label="⬇️ Download Excel Report",
                            data=excel_data,
                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"excel_download_{session_id}_{timestamp}",
                            use_container_width=True
                        )
                        render_persistent_success("Excel report ready for download!")
                except Exception as e:
                    render_persistent_error(f"Failed to generate Excel report: {str(e)}")
        
        with col3:
            # JSON Download - FIXED unique keys
            json_button_key = f"json_btn_{session_id}_{timestamp}_{len(results)}"
            if st.button("📋 Download JSON", key=json_button_key, use_container_width=True):
                try:
                    json_data = create_json_report(results)
                    if json_data:
                        st.download_button(
                            label="⬇️ Download JSON Report",
                            data=json_data,
                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key=f"json_download_{session_id}_{timestamp}",
                            use_container_width=True
                        )
                        render_persistent_success("JSON report ready for download!")
                except Exception as e:
                    render_persistent_error(f"Failed to generate JSON report: {str(e)}")

def main():
    # Configure page
    st.set_page_config(
        page_title="ResumeAlign - AI Resume Analysis",
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
        
        st.markdown("---")
        if st.button("🗑️ Clear Session", 
                    use_container_width=True,
                    help="Clear all data and start fresh"):
            clear_session()
    
    # Main content
    st.markdown("## 🎯 Smart Resume Analysis")
    
    # Job description input
    with st.container():
        st.markdown("### 📋 Job Description")
        
        job_desc_key = f"job_desc_input_{st.session_state.session_id}"
        if 'clear_trigger' in st.session_state:
            job_desc_key = f"job_desc_input_{st.session_state.session_id}_{int(st.session_state.clear_trigger)}"
        
        job_desc = st.text_area(
            "Enter detailed job description for accurate matching:",
            value=st.session_state.get('job_description', ''),
            height=180,
            placeholder="Include required skills, experience, qualifications, responsibilities...",
            key=job_desc_key,
            help="More detailed job descriptions produce better analysis results"
        )
        
        if job_desc != st.session_state.get('job_description', ''):
            st.session_state.job_description = job_desc
    
    # Analysis tabs
    tab1, tab2 = st.tabs(["📄 Single Resume Analysis", f"📁 Batch Analysis (Max {BATCH_LIMIT} files)"])
    
    with tab1:
        st.markdown("### 📄 Single Resume Analysis")
        st.markdown("Upload one resume for detailed individual analysis.")
        
        single_file_key = f"single_file_{st.session_state.session_id}"
        if 'clear_trigger' in st.session_state:
            single_file_key = f"single_file_{st.session_state.session_id}_{int(st.session_state.clear_trigger)}"
        
        uploaded_file = st.file_uploader(
            "Choose resume file (PDF, DOCX, TXT - Max 10MB)",
            type=['pdf', 'docx', 'txt'],
            key=single_file_key,
            help="Select a resume file for AI analysis"
        )
        
        # DEBUG: Show current state
        if uploaded_file:
            st.info(f"📄 File uploaded: {uploaded_file.name}")
            
        if st.session_state.job_description.strip():
            st.info(f"📋 Job description ready ({len(st.session_state.job_description)} characters)")
        else:
            st.warning("⚠️ Job description needed")
        
        if uploaded_file and st.session_state.job_description.strip():
            # Validate file
            valid_files, errors = validate_uploaded_files(uploaded_file, is_batch=False)
            
            if errors:
                display_persistent_errors(errors)
                st.stop()  # Don't proceed if validation failed
            
            if valid_files:
                render_compact_file_info(uploaded_file)
                
                col1, col2 = st.columns([3, 1])
                with col2:
                    # FIXED: Simple, unique analyze button key
                    current_timestamp = int(time.time() * 1000)
                    analyze_button_key = f"analyze_btn_{current_timestamp}"
                    
                    analyze_button = st.button(
                        "🔍 Analyze Resume",
                        key=analyze_button_key,
                        use_container_width=True,
                        type="primary",
                        help="Click to start AI analysis"
                    )
                
                # DEBUG: Show button state
                if analyze_button:
                    st.success("✅ Button clicked! Starting analysis...")
                
                if analyze_button:
                    # Create a placeholder for status updates
                    status_placeholder = st.empty()
                    
                    try:
                        status_placeholder.info("🔄 Step 1: Extracting text from file...")
                        
                        # Extract text - FIXED: Now using proper file_utils with better error handling
                        logger.info(f"Extracting text from {uploaded_file.name}")
                        file_text = extract_text_from_file(uploaded_file)
                        
                        # DEBUG: Check text extraction result
                        if file_text:
                            status_placeholder.info(f"✅ Step 1 Complete: Extracted {len(file_text)} characters")
                            logger.info(f"Successfully extracted {len(file_text)} characters")
                        else:
                            status_placeholder.error("❌ Step 1 Failed: Could not extract text from file")
                            st.error("Could not extract text from the file. Please ensure it's not corrupted or password-protected.")
                            st.stop()
                        
                        if file_text and file_text.strip():
                            status_placeholder.info("🔄 Step 2: Generating analysis with AI...")
                            
                            # Generate hash for caching
                            import hashlib
                            candidate_hash = generate_candidate_hash(file_text, uploaded_file.name)
                            cache_key = f"{candidate_hash}_{hashlib.md5(st.session_state.job_description.encode()).hexdigest()}"
                            
                            # Check cache
                            if cache_key in st.session_state.candidate_cache:
                                result = st.session_state.candidate_cache[cache_key]
                                status_placeholder.success("📋 Using cached result")
                            else:
                                # Analyze
                                result = analyze_single_candidate(
                                    file_text,
                                    st.session_state.job_description,
                                    uploaded_file.name,
                                    batch_mode=False
                                )
                                
                                if result and result.get('overall_score', 0) >= 0:
                                    st.session_state.candidate_cache[cache_key] = result
                                    status_placeholder.success("✅ Step 2 Complete: Analysis finished")
                            
                            if result and result.get('overall_score', 0) >= 0:
                                result['timestamp'] = datetime.now()
                                st.session_state.analysis_results = [result]  # Replace for single analysis
                                
                                status_placeholder.success("🎉 Analysis completed successfully!")
                                
                                # Clear the status after a moment
                                time.sleep(2)
                                status_placeholder.empty()
                                
                                # Force a rerun to show results
                                st.rerun()
                            else:
                                status_placeholder.error("❌ Step 2 Failed: Analysis returned invalid results")
                                st.error("Analysis failed. Please check the file and try again.")
                        else:
                            status_placeholder.error("❌ Step 1 Failed: No text content found")
                            st.error("Could not extract text from the file. Please ensure it's not corrupted or password-protected.")
                    
                    except Exception as e:
                        logger.error(f"Single analysis error: {str(e)}")
                        status_placeholder.error(f"❌ Analysis failed: {str(e)}")
                        st.error(f"Analysis failed: {str(e)}")
        
        elif uploaded_file and not st.session_state.job_description.strip():
            st.warning("⚠️ Please enter a job description first.")
        elif not uploaded_file and st.session_state.job_description.strip():
            st.info("👆 Upload a resume file to begin analysis.")
    
    with tab2:
        st.markdown("### 📁 Batch Resume Analysis")
        render_file_limit_warning()
        
        batch_files_key = f"batch_files_{st.session_state.session_id}"
        if 'clear_trigger' in st.session_state:
            batch_files_key = f"batch_files_{st.session_state.session_id}_{int(st.session_state.clear_trigger)}"
        
        uploaded_files = st.file_uploader(
            f"Choose up to {BATCH_LIMIT} resume files (PDF, DOCX, TXT)",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            key=batch_files_key,
            help=f"Maximum {BATCH_LIMIT} files per batch"
        )
        
        # Show uploaded files info
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} files uploaded")
            for file in uploaded_files:
                st.write(f"• {file.name} ({len(file.getvalue()) / 1024:.1f} KB)")
        
        # Show job description status
        if st.session_state.job_description.strip():
            st.info(f"📋 Job description ready ({len(st.session_state.job_description)} characters)")
        else:
            st.warning("⚠️ Job description needed for batch analysis")
        
        # Batch analysis logic
        if uploaded_files and st.session_state.job_description.strip():
            # Validate files
            valid_files, errors = validate_uploaded_files(uploaded_files, is_batch=True)
            
            if errors:
                display_persistent_errors(errors)
            
            if valid_files:
                st.success(f"✅ {len(valid_files)} valid files ready for batch analysis")
                
                # Show files to be processed
                with st.expander("📋 Files to Process", expanded=False):
                    for i, file in enumerate(valid_files, 1):
                        file_size_mb = len(file.getvalue()) / (1024 * 1024)
                        st.write(f"{i}. **{file.name}** ({file_size_mb:.1f} MB)")
                
                # Batch analysis button
                col1, col2 = st.columns([3, 1])
                with col2:
                    batch_timestamp = int(time.time() * 1000)
                    batch_button_key = f"batch_analyze_btn_{batch_timestamp}"
                    
                    batch_analyze = st.button(
                        "🔍 Analyze All Resumes",
                        key=batch_button_key,
                        use_container_width=True,
                        type="primary",
                        help="Process all uploaded resumes"
                    )
                
                if batch_analyze:
                    st.success("🎉 Starting batch analysis...")
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_container = st.empty()
                    
                    batch_results = []
                    
                    try:
                        for i, file in enumerate(valid_files):
                            # Update progress
                            progress = (i + 1) / len(valid_files)
                            progress_bar.progress(progress)
                            status_text.info(f"🔄 Processing {file.name} ({i+1}/{len(valid_files)})")
                            
                            # Extract text
                            file_text = extract_text_from_file(file)
                            
                            if file_text and file_text.strip():
                                # Generate cache key
                                candidate_hash = generate_candidate_hash(file_text, file.name)
                                cache_key = f"{candidate_hash}_{hashlib.md5(st.session_state.job_description.encode()).hexdigest()}"
                                
                                # Check cache first
                                if cache_key in st.session_state.candidate_cache:
                                    result = st.session_state.candidate_cache[cache_key]
                                    status_text.info(f"📋 Using cached result for {file.name}")
                                else:
                                    # Analyze with AI
                                    result = analyze_single_candidate(
                                        file_text,
                                        st.session_state.job_description,
                                        file.name,
                                        batch_mode=True
                                    )
                                    
                                    if result and result.get('overall_score', 0) >= 0:
                                        st.session_state.candidate_cache[cache_key] = result
                                
                                if result and result.get('overall_score', 0) >= 0:
                                    result['timestamp'] = datetime.now()
                                    batch_results.append(result)
                                    
                                    # Show intermediate result
                                    score = result.get('overall_score', 0)
                                    name = result.get('candidate_name', 'Unknown')
                                    status_text.success(f"✅ {file.name}: {name} - {score}%")
                                else:
                                    status_text.error(f"❌ Failed to analyze {file.name}")
                                    batch_results.append({
                                        'candidate_name': f"Error - {file.name}",
                                        'overall_score': 0,
                                        'skills_score': 0,
                                        'experience_score': 0,
                                        'education_score': 0,
                                        'error': 'Analysis failed'
                                    })
                            else:
                                status_text.error(f"❌ Could not extract text from {file.name}")
                                batch_results.append({
                                    'candidate_name': f"Error - {file.name}",
                                    'overall_score': 0,
                                    'skills_score': 0,
                                    'experience_score': 0,
                                    'education_score': 0,
                                    'error': 'Text extraction failed'
                                })
                            
                            # Small delay to prevent overwhelming the API
                            time.sleep(0.5)
                        
                        # Batch complete
                        progress_bar.progress(1.0)
                        status_text.success(f"🎉 Batch analysis complete! Processed {len(batch_results)} files.")
                        
                        # Store results
                        st.session_state.analysis_results = batch_results
                        
                        # Clear progress indicators after a moment
                        time.sleep(2)
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Force rerun to show results
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"Batch analysis error: {str(e)}")
                        status_text.error(f"❌ Batch analysis failed: {str(e)}")
                        st.error(f"Batch analysis failed: {str(e)}")
        
        elif uploaded_files and not st.session_state.job_description.strip():
            st.warning("⚠️ Please enter a job description first.")
        elif not uploaded_files and st.session_state.job_description.strip():
            st.info("👆 Upload resume files to begin batch analysis.")

    # Display results section - outside of tabs
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("## 📊 Analysis Results")
        st.markdown(f"**Session Results:** {len(st.session_state.analysis_results)} candidate(s) analyzed")
        display_analysis_results(st.session_state.analysis_results, st.session_state.job_description)
    
    # DEBUGGING SECTION - Keep the comprehensive debugging from your original code
    # This section can be removed once everything is working properly
    
    # Debug information - can be removed in production
    if st.checkbox("🔧 Show Debug Info", help="Toggle debug information"):
        st.markdown("### 🔍 Debug Information")
        
        with st.expander("Session State", expanded=False):
            st.json({
                'session_id': st.session_state.get('session_id'),
                'job_description_length': len(st.session_state.get('job_description', '')),
                'analysis_results_count': len(st.session_state.get('analysis_results', [])),
                'cache_size': len(st.session_state.get('candidate_cache', {})),
                'has_clear_trigger': 'clear_trigger' in st.session_state
            })
        
        with st.expander("Current Analysis Results", expanded=False):
            if st.session_state.analysis_results:
                for i, result in enumerate(st.session_state.analysis_results):
                    st.write(f"**Result {i+1}:**")
                    st.json({
                        'candidate_name': result.get('candidate_name'),
                        'overall_score': result.get('overall_score'),
                        'has_skills_analysis': bool(result.get('skills_analysis')),
                        'has_experience_analysis': bool(result.get('experience_analysis')),
                        'has_education_analysis': bool(result.get('education_analysis')),
                        'has_interview_questions': bool(result.get('interview_questions')),
                        'strengths_count': len(result.get('strengths', [])),
                        'weaknesses_count': len(result.get('weaknesses', [])),
                        'timestamp': str(result.get('timestamp', 'Not set'))
                    })
            else:
                st.info("No analysis results available")

if __name__ == "__main__":
    main()
