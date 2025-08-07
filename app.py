import streamlit as st
from io import BytesIO
import os

# Try importing optional dependencies with graceful fallback
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    st.warning("PyPDF2 not installed. PDF support disabled.")

try:
    import docx2txt
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False
    st.warning("docx2txt not installed. DOCX support disabled.")

# Import our custom modules
try:
    from ui_components import (
        load_custom_css, display_header, display_score_metrics, 
        display_recommendation_box, display_footer
    )
    from file_utils import save_uploaded_file, cleanup_temp_files, validate_file_type
    from name_extraction import extract_candidate_name, format_candidate_name
    from ai_analysis import analyze_resume_job_match, generate_improvement_suggestions, validate_analysis_response
    from pdf_generator import generate_pdf_download_button
    MODULES_LOADED = True
except ImportError as e:
    st.error(f"Error importing custom modules: {e}")
    st.error("Please ensure all module files are present in your repository.")
    MODULES_LOADED = False

# Page config
st.set_page_config(
    page_title="ResumeAlign - AI Resume Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    if not PDF_SUPPORT:
        st.error("PDF support not available. Please install PyPDF2.")
        return None
    
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def extract_text_from_docx(docx_file):
    """Extract text from DOCX file"""
    if not DOCX_SUPPORT:
        st.error("DOCX support not available. Please install docx2txt.")
        return None
    
    try:
        return docx2txt.process(BytesIO(docx_file.read()))
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return None

def main():
    """Main application function"""
    
    # Check if modules are loaded
    if not MODULES_LOADED:
        st.error("❌ Required modules not found. Please check your repository structure.")
        st.info("Expected files: ui_components.py, file_utils.py, name_extraction.py, ai_analysis.py, pdf_generator.py")
        return
    
    # Load custom CSS
    load_custom_css()
    
    # Display header
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Upload Documents")
        
        # Resume upload
        st.subheader("1. Upload Resume")
        
        # Determine supported file types
        supported_types = ['txt']
        if PDF_SUPPORT:
            supported_types.append('pdf')
        if DOCX_SUPPORT:
            supported_types.append('docx')
        
        resume_file = st.file_uploader(
            "Choose resume file",
            type=supported_types,
            help=f"Supported formats: {', '.join(supported_types).upper()}"
        )
        
        # Job description input
        st.subheader("2. Job Description")
        job_input_method = st.radio(
            "How would you like to provide the job description?",
            ["Paste Text", "Upload File"]
        )
        
        job_description = ""
        job_title = ""
        
        if job_input_method == "Paste Text":
            job_title = st.text_input("Job Title (Optional)", placeholder="e.g., Senior Software Engineer")
            job_description = st.text_area(
                "Paste job description here",
                height=200,
                placeholder="Paste the complete job description here..."
            )
        else:
            job_file = st.file_uploader(
                "Upload job description file",
                type=supported_types,
                help=f"Supported formats: {', '.join(supported_types).upper()}"
            )
            if job_file:
                if job_file.type == "application/pdf" and PDF_SUPPORT:
                    job_description = extract_text_from_pdf(job_file)
                elif job_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" and DOCX_SUPPORT:
                    job_description = extract_text_from_docx(job_file)
                else:
                    try:
                        job_description = str(job_file.read(), "utf-8")
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
        
        # Analysis settings
        st.subheader("⚙️ Analysis Settings")
        include_suggestions = st.checkbox("Include Improvement Suggestions", value=True)
        generate_pdf = st.checkbox("Generate PDF Report", value=True)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if resume_file and job_description:
            st.markdown('<div class="analysis-section">', unsafe_allow_html=True)
            
            # Extract resume text
            with st.spinner("Processing resume..."):
                resume_text = None
                
                if resume_file.type == "application/pdf" and PDF_SUPPORT:
                    resume_text = extract_text_from_pdf(resume_file)
                elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" and DOCX_SUPPORT:
                    resume_text = extract_text_from_docx(resume_file)
                else:
                    try:
                        resume_text = str(resume_file.read(), "utf-8")
                    except Exception as e:
                        st.error(f"Error reading resume file: {e}")
            
            if resume_text:
                # Extract candidate name
                candidate_name = format_candidate_name(
                    extract_candidate_name(resume_text)
                )
                
                st.success(f"✅ Resume processed successfully for **{candidate_name}**")
                
                # Show preview of extracted text
                with st.expander("📄 Preview Extracted Text"):
                    st.text(resume_text[:500] + "..." if len(resume_text) > 500 else resume_text)
                
                # Analyze button
                if st.button("🚀 Analyze Resume Match", type="primary", use_container_width=True):
                    
                    # Check if Gemini API key is available
                    if not st.secrets.get("GEMINI_API_KEY"):
                        st.error("❌ Gemini API key not found in secrets. Please add your API key to continue.")
                        st.info("Add GEMINI_API_KEY to your Streamlit secrets")
                        return
                    
                    with st.spinner("Analyzing resume with AI... This may take a moment."):
                        analysis = analyze_resume_job_match(
                            resume_text, 
                            job_description, 
                            candidate_name
                        )
                    
                    if analysis and validate_analysis_response(analysis):
                        st.session_state['analysis'] = analysis
                        st.session_state['candidate_name'] = candidate_name
                        st.session_state['job_title'] = job_title
                        st.rerun()
                    else:
                        st.error("❌ Analysis failed. Please check your API key and try again.")
            else:
                st.error("❌ Failed to extract text from resume. Please try a different file.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.info("👆 Please upload a resume and provide a job description to get started.")
            
            # Show supported formats
            st.markdown("### 📄 Supported File Formats")
            format_status = []
            format_status.append("✅ TXT - Text files")
            
            if PDF_SUPPORT:
                format_status.append("✅ PDF - Adobe PDF files")
            else:
                format_status.append("❌ PDF - Install PyPDF2 for PDF support")
            
            if DOCX_SUPPORT:
                format_status.append("✅ DOCX - Microsoft Word documents")
            else:
                format_status.append("❌ DOCX - Install docx2txt for Word support")
            
            for status in format_status:
                st.markdown(status)
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        if 'analysis' in st.session_state:
            analysis = st.session_state['analysis']
            
            # Display metrics
            st.metric("Overall Score", f"{analysis.get('overall_score', 0)}%")
            st.metric("Skills Match", f"{analysis.get('skills_score', 0)}%")
            st.metric("Experience", f"{analysis.get('experience_score', 0)}%")
            st.metric("Education", f"{analysis.get('education_score', 0)}%")
        else:
            st.info("Upload resume to see analysis")
    
    # Display analysis results
    if 'analysis' in st.session_state:
        analysis = st.session_state['analysis']
        candidate_name = st.session_state.get('candidate_name', 'Candidate')
        job_title = st.session_state.get('job_title', '')
        
        st.markdown("---")
        st.markdown("## 📈 Detailed Analysis Results")
        
        # Score metrics
        scores = {
            'overall': analysis.get('overall_score', 0),
            'skills': analysis.get('skills_score', 0),
            'experience': analysis.get('experience_score', 0),
            'education': analysis.get('education_score', 0)
        }
        display_score_metrics(scores)
        
        # Analysis sections
        col1, col2 = st.columns(2)
        
        with col1:
            # Strengths
            st.subheader("✅ Key Strengths")
            strengths = analysis.get('strengths', [])
            for strength in strengths:
                st.markdown(f"• {strength}")
            
            # Missing skills
            st.subheader("🔍 Missing Skills")
            missing_skills = analysis.get('missing_skills', [])
            for skill in missing_skills:
                st.markdown(f"• {skill}")
        
        with col2:
            # Areas for improvement
            st.subheader("🎯 Areas for Improvement")
            weaknesses = analysis.get('weaknesses', [])
            for weakness in weaknesses:
                st.markdown(f"• {weakness}")
            
            # Key matches
            st.subheader("🎯 Key Matches")
            key_matches = analysis.get('key_matches', [])
            for match in key_matches:
                st.markdown(f"• {match}")
        
        # Recommendations
        st.subheader("💡 Recommendations")
        recommendations = analysis.get('recommendations', [])
        rec_text = "<br>".join([f"• {rec}" for rec in recommendations])
        display_recommendation_box(rec_text)
        
        # Detailed analyses
        if analysis.get('experience_analysis'):
            st.subheader("📋 Experience Analysis")
            st.write(analysis['experience_analysis'])
        
        if analysis.get('skills_analysis'):
            st.subheader("🛠️ Skills Analysis")
            st.write(analysis['skills_analysis'])
        
        # Improvement suggestions
        if include_suggestions:
            if st.button("Generate Improvement Suggestions"):
                with st.spinner("Generating personalized suggestions..."):
                    suggestions = generate_improvement_suggestions(analysis)
                    if suggestions:
                        st.subheader("🚀 Improvement Suggestions")
                        st.markdown(suggestions)
        
        # PDF download
        if generate_pdf:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                try:
                    generate_pdf_download_button(analysis, candidate_name, job_title)
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")
                    st.info("PDF generation requires reportlab package")
    
    # Footer
    display_footer()

if __name__ == "__main__":
    main()
