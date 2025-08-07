"""
ResumeAlign - AI-Powered Resume & CV Analysis Platform
Main Streamlit application file (refactored and modular)
"""

import streamlit as st
import json
import time
from datetime import datetime

# Import our custom modules
from ui_components import (
    apply_custom_css, render_logo_header, render_main_header, 
    render_feature_card, render_analysis_card, render_linkedin_helper,
    render_copy_paste_guide, render_app_footer, clear_session
)
from file_utils import extract_text
from name_extraction import extract_candidate_name, extract_candidate_name_from_ai_report
from ai_analysis import analyze_single_candidate
from pdf_generator import build_pdf, create_batch_zip

# ---------- STREAMLIT CONFIG ----------
st.set_page_config(
    page_title="ResumeAlign - AI Resume Analyzer", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🎯"
)

# ---------- MAIN APP ----------
def main():
    """Main application function"""
    
    # Apply styling
    apply_custom_css()
    
    # Header sections
    render_logo_header()
    render_main_header()
    
    # Clear Session Button (functional version)
    col1, col2, col3 = st.columns([6, 1, 1])
    with col3:
        if st.button("🔄 Clear Session", help="Clear all data and start fresh", key="clear_btn"):
            clear_session()
            st.rerun()
    
    # Mode Selector
    render_feature_card("Choose Analysis Mode")
    
    analysis_mode = st.radio(
        "",
        ["🧑‍💼 Single Candidate Analysis", "📁 Batch Processing (up to 5 files)"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if analysis_mode == "🧑‍💼 Single Candidate Analysis":
        handle_single_candidate_analysis()
    else:
        handle_batch_processing()
    
    # Display results
    display_results(analysis_mode)
    
    # Footer
    render_app_footer()


def handle_single_candidate_analysis():
    """Handle single candidate analysis UI and logic"""
    
    # LinkedIn Profile Helper
    render_feature_card("🔗 LinkedIn Profile Helper")
    profile_url = render_linkedin_helper()
    render_copy_paste_guide()
    
    # Main analysis form
    render_feature_card("📊 Candidate Analysis")
    
    with st.form("single_analyzer", clear_on_submit=False):
        job_desc = st.text_area(
            "📝 Job Description", 
            height=200,
            placeholder="Paste the complete job description here...\n\nInclude:\n• Job title and department\n• Key responsibilities\n• Required qualifications\n• Preferred skills\n• Experience requirements",
            help="Paste the full job description for accurate matching analysis"
        )
        
        profile_text = st.text_area(
            "👤 Candidate Profile / LinkedIn Text", 
            height=220,
            placeholder="Paste the candidate's LinkedIn profile or CV text here...\n\nInclude all relevant sections:\n• Professional summary\n• Work experience\n• Skills and endorsements\n• Education and certifications",
            help="Copy and paste text from LinkedIn profile or CV"
        )
        
        uploaded_file = st.file_uploader(
            "📎 Or Upload CV/Resume File (Optional)", 
            type=["pdf", "docx"],
            help="Upload a PDF or Word document instead of copy-pasting text"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submitted = st.form_submit_button("🚀 Analyze Candidate", type="primary", use_container_width=True)
    
    if submitted:
        process_single_candidate(job_desc, profile_text, uploaded_file, profile_url)


def handle_batch_processing():
    """Handle batch processing UI and logic"""
    
    render_feature_card(
        "📁 Batch Processing Mode",
        """<div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%); 
                    padding: 1rem; border-radius: 8px; border: 2px solid #000000; margin-top: 0.5rem;">
            <p style="margin: 0; color: #1e40af; font-weight: 500;">
                📋 Upload up to 5 CV files (PDF/DOCX) for batch analysis against a single job description.
            </p>
        </div>"""
    )
    
    with st.form("batch_analyzer", clear_on_submit=False):
        job_desc = st.text_area(
            "📝 Job Description", 
            height=200,
            placeholder="Paste the complete job description here...\n\nThis will be used to analyze all uploaded CVs",
            help="All CV files will be analyzed against this job description"
        )
        
        uploaded_files = st.file_uploader(
            "📎 Upload CV Files (PDF / DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Select up to 5 CV files for batch processing"
        )
        
        if uploaded_files:
            st.info(f"📄 **{len(uploaded_files)} files selected:** {', '.join([f.name for f in uploaded_files])}")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            batch_submitted = st.form_submit_button("🚀 Analyze Batch", type="primary", use_container_width=True)
    
    if batch_submitted:
        process_batch_analysis(job_desc, uploaded_files)


def process_single_candidate(job_desc, profile_text, uploaded_file, profile_url):
    """Process single candidate analysis"""
    
    # Validation
    if not job_desc.strip():
        st.error("❌ Job Description is required for analysis.")
        return
    
    if not profile_text.strip() and not uploaded_file:
        st.error("❌ Please provide either candidate text or upload a CV file.")
        return
    
    # Extract file text if uploaded
    file_text = extract_text(uploaded_file) if uploaded_file else ""
    
    # Show processing animation
    with st.spinner("🤖 AI is analyzing the candidate profile..."):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            progress_bar.progress(i + 1)
        
        report, error = analyze_single_candidate(job_desc, profile_text, file_text)
    
    if error:
        st.error(f"❌ Analysis error: {error}")
        return
    
    # Store results
    st.session_state["last_report"] = report
    st.session_state["linkedin_url"] = profile_url.strip()
    
    st.success("✅ Analysis completed successfully!")


def process_batch_analysis(job_desc, uploaded_files):
    """Process batch analysis"""
    
    # Validation
    if not job_desc.strip():
        st.error("❌ Job Description is required for batch analysis.")
        return
    
    if not uploaded_files:
        st.error("❌ Please upload at least one CV file.")
        return
    
    if len(uploaded_files) > 5:
        st.error("❌ Maximum 5 files allowed for batch processing.")
        return
    
    # Process batch
    batch_reports = []
    
    # Create progress tracking
    progress_container = st.container()
    with progress_container:
        st.markdown("### 🔄 Processing Files...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Process each file
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.markdown(f"**Processing:** `{uploaded_file.name}` ({i+1}/{len(uploaded_files)})")
            
            file_text = extract_text(uploaded_file)
            if not file_text.strip():
                st.warning(f"⚠️ Could not extract text from `{uploaded_file.name}`. Skipping...")
                progress_bar.progress((i + 1) / len(uploaded_files))
                continue
            
            # Analyze with AI
            with st.spinner(f"🤖 AI analyzing {uploaded_file.name}..."):
                report, error = analyze_single_candidate(job_desc, "", file_text)
            
            if error:
                st.error(f"❌ Error analyzing `{uploaded_file.name}`: {error}")
                progress_bar.progress((i + 1) / len(uploaded_files))
                continue
            
            # Extract candidate name
            candidate_name = extract_candidate_name_from_ai_report(report)
            if not candidate_name or candidate_name == "Unknown Candidate":
                candidate_name = extract_candidate_name(file_text)
            
            # Show extraction result
            st.success(f"✅ **Processed:** `{uploaded_file.name}` → **Candidate:** `{candidate_name}`")
            
            batch_reports.append({
                'report': report,
                'filename': uploaded_file.name,
                'candidate_name': candidate_name
            })
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            time.sleep(0.3)  # Small delay for better UX
        
        status_text.markdown("✅ **Batch processing completed!**")
    
    if batch_reports:
        st.session_state["batch_reports"] = batch_reports
        st.session_state["batch_job_desc"] = job_desc


def display_results(analysis_mode):
    """Display analysis results based on mode"""
    
    if analysis_mode == "🧑‍💼 Single Candidate Analysis":
        display_single_results()
    else:
        display_batch_results()


def display_single_results():
    """Display single candidate results"""
    
    if "last_report" not in st.session_state:
        return
    
    report = st.session_state["last_report"]
    
    render_analysis_card("✅ Analysis Results")
    
    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        pdf_data = build_pdf(report, st.session_state.get("linkedin_url", ""))
        st.download_button(
            "📄 Download PDF Report", 
            data=pdf_data, 
            file_name=f"ResumeAlign_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", 
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        st.download_button(
            "💾 Download JSON Data", 
            data=json.dumps(report, indent=2), 
            file_name=f"ResumeAlign_Data_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 
            mime="application/json",
            use_container_width=True
        )
    
    # Display detailed results (metrics, summary, etc.)
    display_detailed_single_results(report)


def display_batch_results():
    """Display batch processing results"""
    
    if "batch_reports" not in st.session_state:
        return
    
    batch_reports = st.session_state["batch_reports"]
    job_desc = st.session_state["batch_job_desc"]
    
    render_analysis_card(f"✅ Batch Analysis Complete - {len(batch_reports)} Candidates Processed")
    
    # Download options and detailed results display
    display_detailed_batch_results(batch_reports, job_desc)


def display_detailed_single_results(report):
    """Display detailed single candidate results"""
    # Implementation for detailed single results display
    # This would include metrics, summary, strengths, etc.
    # (Extracted from original code for brevity)
    pass


def display_detailed_batch_results(batch_reports, job_desc):
    """Display detailed batch results"""
    # Implementation for detailed batch results display
    # This would include summary table, individual reports, etc.
    # (Extracted from original code for brevity)
    pass


if __name__ == "__main__":
    main()
