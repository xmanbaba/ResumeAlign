import streamlit as st
import PyPDF2
import docx2txt
from io import BytesIO
import os

# Import our custom modules
from ui_components import (
    load_custom_css, display_header, display_score_metrics, 
    display_recommendation_box, display_footer
)
from file_utils import save_uploaded_file, cleanup_temp_files, validate_file_type
from name_extraction import extract_candidate_name, format_candidate_name
from ai_analysis import analyze_resume_job_match, generate_improvement_suggestions, validate_analysis_response
from pdf_generator import generate_pdf_download_button

# Page config
st.set_page_config(
    page_title="ResumeAlign - AI Resume Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
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
    try:
        return docx2txt.process(BytesIO(docx_file.read()))
    except Exception as e:
        st.error(f"Error reading DOCX: {str(e)}")
        return None

def main():
    """Main application function"""
    
    # Load custom CSS
    load_custom_css()
    
    # Display header
    display_header()
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Upload Documents")
        
        # Resume upload
        st.subheader("1. Upload Resume")
        resume_file = st.file_uploader(
            "Choose resume file",
            type=['pdf', 'docx', 'txt'],
            help="Upload your resume in PDF, DOCX, or TXT format"
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
                type=['pdf', 'docx', 'txt'],
                help="Upload job description in PDF, DOCX, or TXT format"
            )
            if job_file:
                if job_file.type == "application/pdf":
                    job_description = extract_text_from_pdf(job_file)
                elif job_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    job_description = extract_text_from_docx(job_file)
                else:
                    job_description = str(job_file.read(), "utf-8")
        
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
                if resume_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(resume_file)
                elif resume_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    resume_text = extract_text_from_docx(resume_file)
                else:
                    resume_text = str(resume_file.read(), "utf-8")
            
            if resume_text:
                # Extract candidate name
                candidate_name = format_candidate_name(
                    extract_candidate_name(resume_text)
                )
                
                st.success(f"✅ Resume processed successfully for **{candidate_name}**")
                
                # Analyze button
                if st.button("🚀 Analyze Resume Match", type="primary", use_container_width=True):
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
                        st.error("❌ Analysis failed. Please try again.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.info("👆 Please upload a resume and provide a job description to get started.")
    
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
                generate_pdf_download_button(analysis, candidate_name, job_title)
    
    # Footer
    display_footer()

if __name__ == "__main__":
    main()
