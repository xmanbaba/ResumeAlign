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
from ai_analysis import analyze_single_candidate, analyze_batch_candidates, create_excel_report, create_json_report
from file_utils import extract_text_from_file, save_uploaded_file
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
    logger.info("🗑️ Clearing all session state data...")
    
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
    
    logger.info("✅ Session cleared successfully")
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

def render_right_aligned_analyze_button(button_text, button_key, disabled=False):
    """FIXED: Render analyze button aligned to the RIGHT as requested"""
    # Create right-aligned container using columns with more space on left
    col1, col2 = st.columns([3, 1])  # More left space, button on right
    
    with col2:
        return st.button(
            button_text, 
            key=button_key, 
            type="primary", 
            disabled=disabled,
            use_container_width=True,
            help="Click to start STRICT AI analysis"
        )

def create_excel_report_local(results):
    """Create Excel report with error handling - LOCAL VERSION"""
    try:
        if not results:
            logger.error("No results provided for Excel report")
            return None
        
        data = []
        for result in results:
            interview_questions = result.get('interview_questions', [])
            questions_text = '\n'.join([f"{i+1}. {q}" for i, q in enumerate(interview_questions) if q])
            
            data.append({
                'Candidate Name': result.get('candidate_name', 'Unknown'),
                'Overall Score': result.get('overall_score', 0),
                'Skills Score': result.get('skills_score', 0),
                'Experience Score': result.get('experience_score', 0),
                'Education Score': result.get('education_score', 0),
                'Skills Analysis': result.get('skills_analysis', 'Not available'),
                'Experience Analysis': result.get('experience_analysis', 'Not available'),
                'Education Analysis': result.get('education_analysis', 'Not available'),
                'Fit Assessment': result.get('fit_assessment', 'Not available'),
                'Recommendations': result.get('recommendations', 'Not available'),
                'Strengths': '; '.join(result.get('strengths', [])),
                'Areas for Improvement': '; '.join(result.get('weaknesses', [])),
                'Interview Questions': questions_text
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='STRICT Analysis Results', index=False)
            worksheet = writer.sheets['STRICT Analysis Results']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_data = output.getvalue()
        output.close()
        
        logger.info(f"Successfully created Excel report with {len(results)} candidates")
        return excel_data
        
    except Exception as e:
        logger.error(f"Excel generation error: {str(e)}")
        st.error(f"❌ Excel generation failed: {str(e)}")
        return None

def create_json_report_local(results):
    """Create comprehensive JSON report - LOCAL VERSION"""
    try:
        if not results:
            logger.error("No results provided for JSON report")
            return None
            
        from datetime import datetime
        
        report_data = {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_version': 'ResumeAlign STRICT v2.1',
            'model_used': 'Google Gemini 1.5 Flash (FREE)',
            'total_candidates': len(results),
            'scoring_method': 'STRICT (Skills 50% + Experience 30% + Education 20%)',
            'recommendation_thresholds': {
                'Strong Yes': '85-100%',
                'Yes': '75-84%', 
                'Conditional Yes': '65-74%',
                'Maybe': '50-64%',
                'No': '0-49%'
            },
            'candidates': results
        }
        
        json_str = json.dumps(report_data, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully created JSON report with {len(results)} candidates")
        return json_str
        
    except Exception as e:
        logger.error(f"JSON generation error: {str(e)}")
        st.error(f"❌ JSON generation failed: {str(e)}")
        return None

def display_analysis_results(results, job_description):
    """FIXED: Display analysis results with WORKING export buttons"""
    if not results:
        st.warning("No analysis results to display.")
        return
    
    # Create unique session identifier for all buttons
    session_id = st.session_state.get('session_id', 'default')
    timestamp = str(int(datetime.now().timestamp() * 1000))  # Millisecond timestamp
    results_hash = hashlib.md5(str(len(results)).encode()).hexdigest()[:6]
    
    # Create tabs for different views with optional ranking
    if len(results) > 1:
        # Show ranking toggle for multiple candidates
        show_ranking = st.toggle("🏆 Show Candidate Rankings", value=True, help="Toggle candidate ranking view")
        
        if show_ranking:
            tab1, tab2, tab3 = st.tabs(["🏆 Rankings", "📋 Detailed Analysis", "📄 Export"])
        else:
            tab1, tab2 = st.tabs(["📋 Detailed Analysis", "📄 Export"])
            tab3 = tab2  # Export tab reference
    else:
        # Single candidate - no ranking needed
        tab1, tab2 = st.tabs(["📋 Analysis", "📄 Export"])
        tab3 = tab2  # Export tab reference
        show_ranking = False
    
    # Rankings tab (only if multiple candidates and ranking enabled)
    if len(results) > 1 and show_ranking:
        with tab1:
            sorted_results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
            
            st.subheader("🏆 Candidate Rankings")
            
            for i, result in enumerate(sorted_results, 1):
                score = result.get('overall_score', 0)
                name = result.get('candidate_name', 'Unknown Candidate')
                rec = result.get('recommendations', '').split(' -')[0] if ' -' in result.get('recommendations', '') else 'Unknown'
                
                # Color code based on STRICT scoring
                if score >= 80:
                    color = "#22c55e"  # Green
                    emoji = "🌟"
                elif score >= 65:
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
                        Overall Score: {score}% | Recommendation: {rec}
                    </p>
                    <p style="margin: 0; opacity: 0.8;">
                        Skills: {result.get('skills_score', 0)}% | 
                        Experience: {result.get('experience_score', 0)}% | 
                        Education: {result.get('education_score', 0)}%
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # Detailed Analysis tab
    analysis_tab = tab2 if (len(results) > 1 and show_ranking) else tab1
    with analysis_tab:
        st.subheader("📋 Detailed Candidate Analysis")
        
        # Sort by score for display
        sorted_results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
        
        for i, result in enumerate(sorted_results, 1):
            name = result.get('candidate_name', 'Unknown Candidate')
            overall_score = result.get('overall_score', 0)
            
            # FIXED: Enhanced expandable title with score and recommendation
            rec_type = result.get('recommendations', '').split(' -')[0] if ' -' in result.get('recommendations', '') else 'Unknown'
            title = f"📄 {name} Analysis - {overall_score}% ({rec_type})"
            
            with st.expander(title, expanded=(i == 1)):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("**STRICT Scores:**")
                    st.metric("Skills", f"{result.get('skills_score', 0)}%")
                    st.metric("Experience", f"{result.get('experience_score', 0)}%")
                    st.metric("Education", f"{result.get('education_score', 0)}%")
                    st.metric("Overall", f"{overall_score}%")
                    
                    # Show recommendation prominently
                    recommendations = result.get('recommendations', 'No recommendation')
                    if overall_score >= 75:
                        st.success(f"✅ {recommendations}")
                    elif overall_score >= 50:
                        st.warning(f"⚠️ {recommendations}")
                    else:
                        st.error(f"❌ {recommendations}")
                
                with col2:
                    st.markdown("**Detailed Analysis:**")
                    
                    # FIXED: Display analyses with candidate names validated
                    skills_analysis = result.get('skills_analysis', '')
                    if skills_analysis and len(skills_analysis) > 20:
                        st.markdown("**🔧 Skills Analysis:**")
                        st.write(skills_analysis)
                    
                    experience_analysis = result.get('experience_analysis', '')
                    if experience_analysis and len(experience_analysis) > 20:
                        st.markdown("**💼 Experience Analysis:**")
                        st.write(experience_analysis)
                    
                    education_analysis = result.get('education_analysis', '')
                    if education_analysis and len(education_analysis) > 20:
                        st.markdown("**🎓 Education Analysis:**")
                        st.write(education_analysis)
                    
                    fit_assessment = result.get('fit_assessment', '')
                    if fit_assessment and len(fit_assessment) > 20:
                        st.markdown("**🎯 Overall Fit Assessment:**")
                        st.write(fit_assessment)
                    
                    # Strengths and weaknesses
                    strengths = result.get('strengths', [])
                    weaknesses = result.get('weaknesses', [])
                    
                    if strengths:
                        st.markdown("**✅ Key Strengths:**")
                        for strength in strengths:
                            if strength and len(strength.strip()) > 5:
                                st.write(f"• {strength}")
                    
                    if weaknesses:
                        st.markdown("**⚠️ Areas for Improvement:**")
                        for weakness in weaknesses:
                            if weakness and len(weakness.strip()) > 5:
                                st.write(f"• {weakness}")
                    
                    # Interview Questions
                    interview_questions = result.get('interview_questions', [])
                    if interview_questions:
                        st.markdown("**❓ Suggested Interview Questions:**")
                        for j, question in enumerate(interview_questions, 1):
                            if question and len(question.strip()) > 10:
                                st.write(f"{j}. {question}")
    
    # Export tab - FIXED: Working export buttons
    with tab3:
        st.subheader("📄 Export Analysis Results")
        
        if not results:
            st.warning("No results to export")
            return
        
        st.info(f"📊 Ready to export {len(results)} candidate analysis result(s)")
        
        # FIXED: Export buttons with proper unique keys and working functionality
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # FIXED: PDF Download with proper error handling
            pdf_key = f"pdf_export_{session_id}_{timestamp}_{results_hash}"
            if st.button("📑 Generate PDF", key=pdf_key, use_container_width=True):
                try:
                    with st.spinner("📄 Generating PDF report..."):
                        if len(results) == 1:
                            # Single candidate PDF
                            pdf_data = generate_single_candidate_pdf(results[0], job_description)
                            if pdf_data:
                                candidate_name = results[0].get('candidate_name', 'Unknown')
                                safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
                                filename = f"ResumeAlign_Analysis_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                
                                # Create download button with unique key
                                download_key = f"pdf_download_{session_id}_{timestamp}_{results_hash}"
                                st.download_button(
                                    label="⬇️ Download PDF Report",
                                    data=pdf_data,
                                    file_name=filename,
                                    mime="application/pdf",
                                    key=download_key,
                                    use_container_width=True
                                )
                                st.success("✅ PDF report generated successfully!")
                            else:
                                st.error("❌ Failed to generate PDF report")
                        else:
                            # Multiple candidates ZIP
                            zip_data = generate_batch_zip_reports(results, job_description)
                            if zip_data:
                                filename = f"ResumeAlign_Batch_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                                
                                # Create download button with unique key
                                download_key = f"zip_download_{session_id}_{timestamp}_{results_hash}"
                                st.download_button(
                                    label="⬇️ Download ZIP Reports",
                                    data=zip_data,
                                    file_name=filename,
                                    mime="application/zip",
                                    key=download_key,
                                    use_container_width=True
                                )
                                st.success("✅ ZIP file with individual reports generated!")
                            else:
                                st.error("❌ Failed to generate ZIP reports")
                except Exception as e:
                    logger.error(f"PDF generation error: {str(e)}")
                    st.error(f"❌ PDF generation failed: {str(e)}")
        
        with col2:
            # FIXED: Excel Download with proper functionality
            excel_key = f"excel_export_{session_id}_{timestamp}_{results_hash}"
            if st.button("📊 Generate Excel", key=excel_key, use_container_width=True):
                try:
                    with st.spinner("📊 Generating Excel report..."):
                        excel_data = create_excel_report_local(results)
                        if excel_data:
                            filename = f"ResumeAlign_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                            
                            # Create download button with unique key
                            download_key = f"excel_download_{session_id}_{timestamp}_{results_hash}"
                            st.download_button(
                                label="⬇️ Download Excel Report",
                                data=excel_data,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=download_key,
                                use_container_width=True
                            )
                            st.success("✅ Excel report generated successfully!")
                        else:
                            st.error("❌ Failed to generate Excel report")
                except Exception as e:
                    logger.error(f"Excel generation error: {str(e)}")
                    st.error(f"❌ Excel generation failed: {str(e)}")
        
        with col3:
            # FIXED: JSON Download with proper functionality
            json_key = f"json_export_{session_id}_{timestamp}_{results_hash}"
            if st.button("📋 Generate JSON", key=json_key, use_container_width=True):
                try:
                    with st.spinner("📋 Generating JSON report..."):
                        json_data = create_json_report_local(results)
                        if json_data:
                            filename = f"ResumeAlign_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            
                            # Create download button with unique key
                            download_key = f"json_download_{session_id}_{timestamp}_{results_hash}"
                            st.download_button(
                                label="⬇️ Download JSON Report",
                                data=json_data,
                                file_name=filename,
                                mime="application/json",
                                key=download_key,
                                use_container_width=True
                            )
                            st.success("✅ JSON report generated successfully!")
                        else:
                            st.error("❌ Failed to generate JSON report")
                except Exception as e:
                    logger.error(f"JSON generation error: {str(e)}")
                    st.error(f"❌ JSON generation failed: {str(e)}")

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
    st.markdown("## 🎯 STRICT Resume Analysis")
    
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
        st.markdown("Upload one resume for detailed individual analysis with STRICT evaluation.")
        
        single_file_key = f"single_file_{st.session_state.session_id}"
        if 'clear_trigger' in st.session_state:
            single_file_key = f"single_file_{st.session_state.session_id}_{int(st.session_state.clear_trigger)}"
        
        uploaded_file = st.file_uploader(
            "Choose resume file (PDF, DOCX, TXT - Max 10MB)",
            type=['pdf', 'docx', 'txt'],
            key=single_file_key,
            help="Select a resume file for STRICT AI analysis"
        )
        
        # FIXED: Single file analysis with RIGHT-ALIGNED button
        if uploaded_file and st.session_state.job_description.strip():
            # Validate file first
            valid_files, errors = validate_uploaded_files(uploaded_file, is_batch=False)
            
            if errors:
                display_persistent_errors(errors)
            else:
                # Show file info
                render_compact_file_info(uploaded_file)
                
                # FIXED: Right-aligned analyze button as requested
                st.markdown("### 🔍 Analysis")
                
                # Create unique button key
                file_hash = hashlib.md5(uploaded_file.name.encode()).hexdigest()[:6]
                job_hash = hashlib.md5(st.session_state.job_description.encode()).hexdigest()[:6]
                button_key = f"analyze_single_{file_hash}_{job_hash}"
                
                # Use RIGHT-ALIGNED button as requested
                if render_right_aligned_analyze_button("🔍 Analyze Resume", button_key):
                    
                    # Create status container
                    status_container = st.container()
                    
                    with status_container:
                        st.info("🔄 Starting STRICT analysis...")
                        
                        try:
                            # Step 1: Extract text
                            with st.spinner("📄 Extracting text from file..."):
                                file_text = extract_text_from_file(uploaded_file)
                            
                            if not file_text or not file_text.strip():
                                st.error("❌ Could not extract text from file. Please check the file format.")
                                st.stop()
                            
                            st.success(f"✅ Text extracted: {len(file_text)} characters")
                            
                            # Step 2: Check cache
                            candidate_hash = generate_candidate_hash(file_text, uploaded_file.name)
                            job_hash = hashlib.md5(st.session_state.job_description.encode()).hexdigest()
                            cache_key = f"{candidate_hash}_{job_hash}"
                            
                            if cache_key in st.session_state.candidate_cache:
                                st.info("📋 Using cached STRICT analysis result")
                                result = st.session_state.candidate_cache[cache_key]
                            else:
                                # Step 3: STRICT AI Analysis
                                with st.spinner("🤖 Performing STRICT AI analysis..."):
                                    result = analyze_single_candidate(
                                        file_text,
                                        st.session_state.job_description,
                                        uploaded_file.name,
                                        batch_mode=False
                                    )
                                
                                if result and result.get('overall_score', 0) >= 0:
                                    st.session_state.candidate_cache[cache_key] = result
                                else:
                                    st.error("❌ STRICT analysis failed. Please try again.")
                                    st.stop()
                            
                            # Store and display results
                            if result:
                                result['timestamp'] = datetime.now()
                                st.session_state.analysis_results = [result]
                                
                                # Show result with strict evaluation context
                                name = result.get('candidate_name', 'Candidate')
                                score = result.get('overall_score', 0)
                                rec = result.get('recommendations', '').split(' -')[0] if ' -' in result.get('recommendations', '') else 'Unknown'
                                
                                if score >= 75:
                                    st.success(f"🎉 STRICT Analysis: {name} scored {score}% - {rec}")
                                elif score >= 50:
                                    st.warning(f"⚠️ STRICT Analysis: {name} scored {score}% - {rec}")
                                else:
                                    st.error(f"❌ STRICT Analysis: {name} scored {score}% - {rec}")
                                
                                # Force rerun to show results
                                st.rerun()
                            
                        except Exception as e:
                            logger.error(f"❌ Analysis error: {str(e)}")
                            st.error(f"❌ STRICT analysis failed: {str(e)}")
        
        elif uploaded_file and not st.session_state.job_description.strip():
            st.warning("⚠️ Please enter a job description first.")
        elif not uploaded_file and st.session_state.job_description.strip():
            st.info("👆 Upload a resume file to begin STRICT analysis.")
        else:
            st.info("👆 Upload a resume file and enter job description to begin analysis.")
    
    with tab2:
        st.markdown("### 📁 Batch Resume Analysis")
        st.markdown("Analyze up to 5 resumes simultaneously with STRICT evaluation.")
        render_file_limit_warning()
        
        batch_files_key = f"batch_files_{st.session_state.session_id}"
        if 'clear_trigger' in st.session_state:
            batch_files_key = f"batch_files_{st.session_state.session_id}_{int(st.session_state.clear_trigger)}"
        
        uploaded_files = st.file_uploader(
            f"Choose up to {BATCH_LIMIT} resume files (PDF, DOCX, TXT)",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            key=batch_files_key,
            help=f"Maximum {BATCH_LIMIT} files per batch for STRICT analysis"
        )
        
        # Show uploaded files info
        if uploaded_files:
            st.info(f"📁 {len(uploaded_files)} files uploaded for STRICT batch analysis")
            for file in uploaded_files:
                size_mb = len(file.getvalue()) / (1024 * 1024)
                st.write(f"• {file.name} ({size_mb:.1f} MB)")
        
        # Show job description status
        if st.session_state.job_description.strip():
            st.info(f"📋 Job description ready ({len(st.session_state.job_description)} characters)")
        else:
            st.warning("⚠️ Job description needed for batch analysis")
        
        # FIXED: Batch analysis with RIGHT-ALIGNED button
        if uploaded_files and st.session_state.job_description.strip():
            # Validate files
            valid_files, errors = validate_uploaded_files(uploaded_files, is_batch=True)
            
            if errors:
                display_persistent_errors(errors)
            else:
                st.success(f"✅ {len(valid_files)} valid files ready for STRICT batch analysis")
                
                # Show files to be processed
                with st.expander("📋 Files to Process", expanded=False):
                    for i, file in enumerate(valid_files, 1):
                        file_size_mb = len(file.getvalue()) / (1024 * 1024)
                        st.write(f"{i}. **{file.name}** ({file_size_mb:.1f} MB)")
                
                # FIXED: Right-aligned batch analysis button
                st.markdown("### 🔍 Batch Analysis")
                
                # Create unique key for batch button
                files_hash = hashlib.md5(''.join([f.name for f in valid_files]).encode()).hexdigest()[:8]
                job_hash = hashlib.md5(st.session_state.job_description.encode()).hexdigest()[:8]
                batch_button_key = f"batch_analyze_{files_hash}_{job_hash}"
                
                if render_right_aligned_analyze_button("🔍 Analyze All Resumes", batch_button_key):
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    batch_results = []
                    
                    try:
                        for i, file in enumerate(valid_files):
                            # Update progress
                            progress = (i + 1) / len(valid_files)
                            progress_bar.progress(progress)
                            status_text.info(f"🔄 STRICT processing {file.name} ({i+1}/{len(valid_files)})")
                            
                            # Extract text
                            file_text = extract_text_from_file(file)
                            
                            if file_text and file_text.strip():
                                # Check cache
                                candidate_hash = generate_candidate_hash(file_text, file.name)
                                job_hash = hashlib.md5(st.session_state.job_description.encode()).hexdigest()
                                cache_key = f"{candidate_hash}_{job_hash}"
                                
                                if cache_key in st.session_state.candidate_cache:
                                    result = st.session_state.candidate_cache[cache_key]
                                    status_text.info(f"📋 Using cached STRICT result for {file.name}")
                                else:
                                    # Analyze with STRICT AI
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
                                    
                                    # Show intermediate result with strict context
                                    score = result.get('overall_score', 0)
                                    name = result.get('candidate_name', 'Unknown')
                                    rec = result.get('recommendations', '').split(' -')[0] if ' -' in result.get('recommendations', '') else 'Unknown'
                                    
                                    if score >= 75:
                                        status_text.success(f"✅ {file.name}: {name} - {score}% ({rec})")
                                    elif score >= 50:
                                        status_text.warning(f"⚠️ {file.name}: {name} - {score}% ({rec})")
                                    else:
                                        status_text.error(f"❌ {file.name}: {name} - {score}% ({rec})")
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
                            
                            # API rate limiting
                            time.sleep(1)
                        
                        # Batch complete
                        progress_bar.progress(1.0)
                        
                        successful_count = len([r for r in batch_results if r.get('overall_score', 0) > 0])
                        status_text.success(f"🎉 STRICT batch analysis complete! {successful_count}/{len(valid_files)} candidates analyzed successfully.")
                        
                        # Store results
                        st.session_state.analysis_results = batch_results
                        
                        # Clear progress indicators
                        time.sleep(2)
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Force rerun to show results
                        st.rerun()
                        
                    except Exception as e:
                        logger.error(f"❌ Batch analysis error: {str(e)}")
                        status_text.error(f"❌ Batch STRICT analysis failed: {str(e)}")
                        st.error(f"Batch analysis failed: {str(e)}")
        
        elif uploaded_files and not st.session_state.job_description.strip():
            st.warning("⚠️ Please enter a job description first.")
        elif not uploaded_files and st.session_state.job_description.strip():
            st.info("👆 Upload resume files to begin STRICT batch analysis.")

    # Display results section - outside of tabs
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown("## 📊 STRICT Analysis Results")
        
        # Show summary stats
        total_candidates = len(st.session_state.analysis_results)
        successful_analyses = len([r for r in st.session_state.analysis_results if r.get('overall_score', 0) > 0])
        avg_score = sum([r.get('overall_score', 0) for r in st.session_state.analysis_results]) / total_candidates if total_candidates > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Candidates", total_candidates)
        with col2:
            st.metric("Successful Analyses", successful_analyses)
        with col3:
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        # Show model info
        st.info("🤖 **Model Used:** Google Gemini 1.5 Flash (FREE) | **Evaluation:** STRICT Scoring")
        
        display_analysis_results(st.session_state.analysis_results, st.session_state.job_description)
    
    # Debug information (can be removed in production)
    if st.checkbox("🔧 Show Debug Info", help="Toggle debug information"):
        st.markdown("### 🔍 Debug Information")
        
        with st.expander("Session State", expanded=False):
            debug_info = {
                'session_id': st.session_state.get('session_id'),
                'job_description_length': len(st.session_state.get('job_description', '')),
                'analysis_results_count': len(st.session_state.get('analysis_results', [])),
                'cache_size': len(st.session_state.get('candidate_cache', {})),
                'has_clear_trigger': 'clear_trigger' in st.session_state,
                'model_confirmed': 'Gemini 1.5 Flash (FREE)',
                'scoring_method': 'STRICT (Skills 50% + Experience 30% + Education 20%)'
            }
            st.json(debug_info)
        
        with st.expander("Current Analysis Results Summary", expanded=False):
            if st.session_state.analysis_results:
                for i, result in enumerate(st.session_state.analysis_results):
                    debug_result = {
                        'index': i + 1,
                        'candidate_name': result.get('candidate_name'),
                        'overall_score': result.get('overall_score'),
                        'recommendation': result.get('recommendations', '').split(' -')[0] if ' -' in result.get('recommendations', '') else 'Unknown',
                        'has_skills_analysis': bool(result.get('skills_analysis')) and len(result.get('skills_analysis', '')) > 20,
                        'has_experience_analysis': bool(result.get('experience_analysis')) and len(result.get('experience_analysis', '')) > 20,
                        'has_education_analysis': bool(result.get('education_analysis')) and len(result.get('education_analysis', '')) > 20,
                        'has_interview_questions': len(result.get('interview_questions', [])) >= 6,
                        'strengths_count': len(result.get('strengths', [])),
                        'weaknesses_count': len(result.get('weaknesses', [])),
                        'timestamp': str(result.get('timestamp', 'Not set'))
                    }
                    st.json(debug_result)
            else:
                st.info("No analysis results available")

if __name__ == "__main__":
    main()
