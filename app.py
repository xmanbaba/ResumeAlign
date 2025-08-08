# app.py -- ResumeAlign v1.4 with Enhanced UI/UX Design - FIXED VERSION

import os, json, streamlit as st
from datetime import datetime
import time

# Import all refactored modules
from file_utils import extract_text, create_safe_filename
from name_extraction import extract_candidate_name, extract_candidate_name_from_ai_report
from pdf_generator import build_pdf, create_batch_zip
from ui_components import (
    apply_custom_css, render_logo_header, render_main_header, 
    render_feature_card, render_analysis_card, render_linkedin_helper,
    render_copy_paste_guide, render_app_footer, clear_session
)
from ai_analysis import analyze_single_candidate

# ---------- UI ----------
st.set_page_config(
    page_title="ResumeAlign - AI Resume Analyzer", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🎯"
)

# Apply custom CSS
apply_custom_css()

# Logo Header Section
render_logo_header()

# Main Title Section
render_main_header()

# Clear Session Button (Streamlit version for functionality) - FIXED: Added black border styling
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    # Use custom CSS class for black border
    st.markdown("""
    <style>
    .clear-session-btn button {
        background: linear-gradient(135deg, #718096 0%, #4A5568 100%) !important;
        color: white !important;
        border: 2px solid #000000 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .clear-session-btn button:hover {
        background: linear-gradient(135deg, #4A5568 0%, #718096 100%) !important;
        transform: translateY(-1px) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Clear Session", help="Clear all data and start fresh", key="clear_btn", use_container_width=True):
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
    # LinkedIn Profile Helper - FIXED: Removed blank button
    render_feature_card("🔗 LinkedIn Profile Helper")
    profile_url = render_linkedin_helper()
    
    # Copy-paste guide
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
        if not job_desc.strip():
            st.error("❌ Job Description is required for analysis.")
            st.stop()
        
        if not profile_text.strip() and not uploaded_file:
            st.error("❌ Please provide either candidate text or upload a CV file.")
            st.stop()
        
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
            st.stop()
        
        # Store results
        st.session_state["last_report"] = report
        st.session_state["linkedin_url"] = profile_url.strip()
        
        st.success("✅ Analysis completed successfully!")

else:
    # Batch processing interface - FIXED: Removed gibberish content
    st.markdown("""
    <div class="feature-card">
        <h3>📁 Batch Processing Mode</h3>
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%); 
                    padding: 1rem; border-radius: 8px; border: 2px solid #000000; margin-top: 0.5rem;">
            <p style="margin: 0; color: #1e40af; font-weight: 500;">
                📋 Upload up to 5 CV files (PDF/DOCX) for batch analysis against a single job description.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
        if not job_desc.strip():
            st.error("❌ Job Description is required for batch analysis.")
            st.stop()
        
        if not uploaded_files:
            st.error("❌ Please upload at least one CV file.")
            st.stop()
        
        if len(uploaded_files) > 5:
            st.error("❌ Maximum 5 files allowed for batch processing.")
            st.stop()
        
        # Process batch with enhanced UI
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

# Display results for single candidate
if "last_report" in st.session_state and analysis_mode == "🧑‍💼 Single Candidate Analysis":
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
    
    # Results display - FIXED: Proper header alignment without separate buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Alignment Score", f"{percentage}%", f"{score}/10")
    with col2:
        experience = report['experience_years']['raw_estimate']
        confidence = report['experience_years']['confidence']
        st.metric("💼 Experience Level", experience, f"{confidence} confidence")
    with col3:
        recommendation = report['next_round_recommendation'].split(' - ')[0] if ' - ' in report['next_round_recommendation'] else report['next_round_recommendation']
        st.metric("📋 Recommendation", recommendation)
    
    # FIXED: Streamlined sections without problematic button styling
    st.markdown("### 📝 Candidate Summary")
    st.write(report["candidate_summary"])
    
    # Strengths and improvements
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Key Strengths")
        for i, strength in enumerate(report["strengths"], 1):
            st.markdown(f"**{i}.** {strength}")
    
    with col2:
        st.markdown("### 🎯 Areas for Development")
        for i, area in enumerate(report["areas_for_improvement"], 1):
            st.markdown(f"**{i}.** {area}")
    
    # Interview questions
    st.markdown("### 🤔 Suggested Interview Questions")
    for i, question in enumerate(report["suggested_interview_questions"], 1):
        st.markdown(f"**{i}.** {question}")
    
    # Final recommendation
    st.markdown("### 🎯 Final Recommendation")
    st.markdown(f"**Decision:** {report['next_round_recommendation']}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Display results for batch processing - FIXED: Complete functionality restored
if "batch_reports" in st.session_state and analysis_mode == "📁 Batch Processing (up to 5 files)":
    batch_reports = st.session_state["batch_reports"]
    job_desc = st.session_state["batch_job_desc"]
    
    render_analysis_card(f"✅ Batch Analysis Complete - {len(batch_reports)} Candidates Processed")
    
    # Download options - FIXED: Both buttons now work
    col1, col2 = st.columns(2)
    with col1:
        zip_data = create_batch_zip(batch_reports, job_desc)
        st.download_button(
            "📦 Download All Reports (ZIP)",
            data=zip_data,
            file_name=f"ResumeAlign_Batch_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
            use_container_width=True
        )
    
    with col2:
        summary_json = {
            "job_description": job_desc,
            "analysis_date": datetime.now().strftime("%d %B %Y"),
            "total_candidates": len(batch_reports),
            "candidates": [
                {
                    "candidate_name": r['candidate_name'],
                    "filename": r['filename'],
                    "alignment_score": r['report']['alignment_score'],
                    "alignment_percentage": int((r['report']['alignment_score'] / 10) * 100),
                    "recommendation": r['report']['next_round_recommendation'],
                    "experience": r['report']['experience_years']['raw_estimate']
                } for r in batch_reports
            ]
        }
        
        st.download_button(
            "📊 Download Summary (JSON)",
            data=json.dumps(summary_json, indent=2),
            file_name=f"ResumeAlign_Summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Summary overview - FIXED: Streamlined headers
    st.markdown("### 📊 Batch Results Overview")
    
    # Create enhanced summary data
    summary_data = []
    for i, report_data in enumerate(batch_reports, 1):
        report = report_data['report']
        candidate_name = report_data['candidate_name']
        filename = report_data['filename']
        
        display_name = candidate_name if candidate_name != "Unknown Candidate" else filename
        score = report['alignment_score']
        percentage = int((score / 10) * 100)
        
        # Determine status emoji based on score
        if percentage >= 80:
            status = "🟢 Excellent"
        elif percentage >= 60:
            status = "🟡 Good"
        elif percentage >= 40:
            status = "🟠 Fair"
        else:
            status = "🔴 Poor"
        
        summary_data.append({
            "Rank": f"#{i}",
            "Candidate": display_name,
            "Score": f"{percentage}%",
            "Status": status,
            "Experience": report['experience_years']['raw_estimate'],
            "Recommendation": report['next_round_recommendation'].split(' - ')[0] if ' - ' in report['next_round_recommendation'] else report['next_round_recommendation']
        })
    
    # Sort by score descending
    summary_data.sort(key=lambda x: int(x["Score"].replace('%', '')), reverse=True)
    for i, item in enumerate(summary_data, 1):
        item["Rank"] = f"#{i}"
    
    st.dataframe(summary_data, use_container_width=True, hide_index=True)
    
    # Individual candidate details - FIXED: Streamlined header
    st.markdown("### 👥 Individual Candidate Reports")
    
    for i, report_data in enumerate(batch_reports, 1):
        report = report_data['report']
        filename = report_data['filename']
        candidate_name = report_data['candidate_name']
        
        display_name = candidate_name if candidate_name != "Unknown Candidate" else filename
        score = report['alignment_score']
        percentage = int((score / 10) * 100)
        
        # Status indicator
        if percentage >= 80:
            indicator = "🟢"
        elif percentage >= 60:
            indicator = "🟡"
        elif percentage >= 40:
            indicator = "🟠"
        else:
            indicator = "🔴"
        
        with st.expander(f"{indicator} **{display_name}** ({percentage}%) - {filename}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🎯 Alignment", f"{percentage}%")
            with col2:
                st.metric("💼 Experience", report['experience_years']['raw_estimate'])
            with col3:
                recommendation = report['next_round_recommendation'].split(' - ')[0] if ' - ' in report['next_round_recommendation'] else report['next_round_recommendation']
                st.metric("📋 Decision", recommendation)
            
            st.markdown("**📝 Summary:**")
            st.write(report["candidate_summary"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**✅ Strengths:**")
                for strength in report["strengths"]:
                    st.markdown(f"• {strength}")
            
            with col2:
                st.markdown("**🎯 Development Areas:**")
                for area in report["areas_for_improvement"]:
                    st.markdown(f"• {area}")
            
            st.markdown("**🤔 Interview Questions:**")
            for j, question in enumerate(report["suggested_interview_questions"], 1):
                st.markdown(f"{j}. {question}")
            
            st.markdown("**🎯 Final Recommendation:**")
            st.info(report['next_round_recommendation'])

# Footer - FIXED: Removed "Built with love by Streamlit & Google Gemini AI" as requested
render_app_footer()
