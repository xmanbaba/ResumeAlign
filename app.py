# app.py -- ResumeAlign v1.1 Enhanced with Batch Processing

import os, json, streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.colors import blue
from reportlab.lib.enums import TA_CENTER
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import zipfile
import time

# ---------- CONFIG ----------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def extract_candidate_name(text):
    """Extract candidate name from CV text using various strategies"""
    if not text.strip():
        return "Unknown Candidate"
    
    lines = text.strip().split('\n')
    # Remove empty lines
    lines = [line.strip() for line in lines if line.strip()]
    
    if not lines:
        return "Unknown Candidate"
    
    # Strategy 1: First non-empty line is often the name
    first_line = lines[0].strip()
    
    # Clean up common prefixes/suffixes
    prefixes_to_remove = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sir', 'madam']
    suffixes_to_remove = ['cv', 'resume', 'curriculum vitae', 'profile']
    
    # Convert to lowercase for comparison but keep original case
    first_line_lower = first_line.lower()
    
    # Remove common prefixes
    for prefix in prefixes_to_remove:
        if first_line_lower.startswith(prefix):
            first_line = first_line[len(prefix):].strip()
            break
    
    # Remove common suffixes
    for suffix in suffixes_to_remove:
        if first_line_lower.endswith(suffix):
            first_line = first_line[:-len(suffix)].strip()
            break
    
    # Strategy 2: Look for patterns like "Name: John Doe" or "Full Name: John Doe"
    name_patterns = ['name:', 'full name:', 'candidate name:', 'applicant name:']
    for line in lines[:5]:  # Check first 5 lines
        line_lower = line.lower()
        for pattern in name_patterns:
            if pattern in line_lower:
                name_part = line[line_lower.index(pattern) + len(pattern):].strip()
                if name_part and len(name_part.split()) >= 2:
                    return name_part
    
    # Strategy 3: If first line looks like a name (2-4 words, no numbers, reasonable length)
    words = first_line.split()
    if (2 <= len(words) <= 4 and 
        all(word.replace('.', '').replace(',', '').isalpha() for word in words) and
        5 <= len(first_line) <= 50):
        return first_line
    
    # Strategy 4: Look for capitalized words that could be names in first few lines
    for line in lines[:3]:
        words = line.split()
        if (2 <= len(words) <= 4 and 
            all(word[0].isupper() and word[1:].islower() for word in words if word.isalpha()) and
            10 <= len(line) <= 50):
            return line
    
    # Fallback: Return first line cleaned up
    return first_line if first_line else "Unknown Candidate"
    if not upload:
        return ""
    if upload.type == "application/pdf":
        return "\n".join(p.extract_text() or "" for p in PdfReader(upload).pages)
    if upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(upload).paragraphs)
    return ""

def build_pdf(report, linkedin_url="", candidate_name="", extracted_from_cv=False):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)
    
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.drawCentredString(A4[0] / 2, 0.75 * inch, f"© 2025 ResumeAlign -- AI Resume & CV Analyzer | Page {doc.page}")
        canvas.restoreState()
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=16, spaceAfter=12, textColor=blue)
    normal_style = ParagraphStyle("Normal", fontSize=11, spaceAfter=6)
    
    # Use the provided candidate name, or extract from summary as fallback
    if not candidate_name and 'candidate_summary' in report:
        candidate_name = report.get('candidate_summary', '').split(' is ')[0] if ' is ' in report.get('candidate_summary', '') else "Unknown Candidate"
    elif not candidate_name:
        candidate_name = "Unknown Candidate"
    
    story = [
        Paragraph("ResumeAlign Analysis Report", title_style),
        Paragraph(f"<b>Name of Candidate:</b> {candidate_name}", normal_style),
        Paragraph(f"<b>Review Date:</b> {datetime.now():%d %B %Y}", normal_style),
    ]
    
    if linkedin_url:
        story.append(Paragraph(f"<b>LinkedIn URL:</b> {linkedin_url}", normal_style))
    
    story.extend([
        Paragraph(f"<b>Alignment Score:</b> {report['alignment_score']} / 10", title_style),
        Paragraph(f"<b>Experience Estimate:</b> {report['experience_years']['raw_estimate']} ({report['experience_years']['confidence']} confidence)", normal_style),
        Paragraph("<b>Summary:</b>", title_style),
        Paragraph(report.get("candidate_summary", ""), normal_style),
        Paragraph("<b>Strengths:</b>", title_style),
    ])
    
    for s in report.get("strengths", []):
        story.append(Paragraph(f"• {s}", normal_style))
    
    story.append(Paragraph("<b>Areas for Improvement:</b>", title_style))
    for a in report.get("areas_for_improvement", []):
        story.append(Paragraph(f"• {a}", normal_style))
    
    story.append(Paragraph("<b>Interview Questions:</b>", title_style))
    for i, q in enumerate(report.get("suggested_interview_questions", []), 1):
        story.append(Paragraph(f"{i}. {q}", normal_style))
    
    story.append(Paragraph("<b>Recommendation:</b>", title_style))
    story.append(Paragraph(report.get("next_round_recommendation", ""), normal_style))
    
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

def create_batch_zip(reports, job_desc):
    """Create a ZIP file containing all batch reports"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add individual PDF reports
        for i, report_data in enumerate(reports, 1):
            report, filename, candidate_name = report_data['report'], report_data['filename'], report_data['candidate_name']
            pdf_buffer = build_pdf(report, candidate_name=candidate_name, extracted_from_cv=True)
            # Use candidate name for filename if available, otherwise use original filename
            safe_name = candidate_name.replace(' ', '_').replace('/', '_').replace('\\', '_') if candidate_name != "Unknown Candidate" else filename.rsplit('.', 1)[0]
            zip_file.writestr(f"Report_{i}_{safe_name}.pdf", pdf_buffer.read())
        
        # Add summary JSON
        summary = {
            "job_description": job_desc,
            "analysis_date": datetime.now().strftime("%d %B %Y"),
            "total_candidates": len(reports),
            "candidates": [
                {
                    "candidate_name": r['candidate_name'],
                    "filename": r['filename'],
                    "alignment_score": r['report']['alignment_score'],
                    "recommendation": r['report']['next_round_recommendation'],
                    "experience": r['report']['experience_years']['raw_estimate']
                } for r in reports
            ]
        }
        zip_file.writestr("batch_summary.json", json.dumps(summary, indent=2))
    
    zip_buffer.seek(0)
    return zip_buffer

SYSTEM_PROMPT = "Use only the text provided. Return valid JSON matching the schema."

def build_prompt(jd, profile_text, file_text):
    extra = file_text.strip() if file_text.strip() else "None provided"
    return (
        "Job Description:\n" + jd + "\n\n"
        "Candidate Profile / CV:\n" + profile_text + "\n\n"
        "Extra File Text:\n" + extra + "\n\n"
        "Return valid JSON:\n"
        "{\n"
        ' "alignment_score": <0-10>,\n'
        ' "experience_years": {"raw_estimate": "<string>", "confidence": "<High|Medium|Low>", "source": "<Manual text|File>"},\n'
        ' "candidate_summary": "<300 words>",\n'
        ' "areas_for_improvement": ["<string>","<string>","<string>","<string>","<string>"],\n'
        ' "strengths": ["<string>","<string>","<string>","<string>","<string>"],\n'
        ' "suggested_interview_questions": ["<string>","<string>","<string>","<string>","<string>"],\n'
        ' "next_round_recommendation": "<Yes|No|Maybe -- brief reason>",\n'
        ' "sources_used": ["Manual text","File"]\n'
        '}'
    )

def analyze_single_candidate(job_desc, profile_text, file_text=""):
    """Analyze a single candidate and return the report"""
    prompt = build_prompt(job_desc, profile_text, file_text)
    try:
        response = model.generate_content([SYSTEM_PROMPT, prompt])
        report = json.loads(response.text.strip("```json").strip("```"))
        return report, None
    except Exception as e:
        return None, str(e)

# ---------- UI ----------
st.set_page_config(page_title="ResumeAlign", layout="wide")
st.title("ResumeAlign -- AI Resume & CV Analyzer")

# Add mode selector
analysis_mode = st.radio(
    "Choose Analysis Mode:",
    ["Single Candidate", "Batch Processing (up to 5 files)"],
    horizontal=True
)

if analysis_mode == "Single Candidate":
    # Original single candidate interface
    st.markdown("### 🔗 LinkedIn Helpers")
    
    with st.popover("ℹ️ How to use the URL", use_container_width=False):
        st.markdown(
            "**Step-by-step (no copy-paste needed):**<br>"
            "1. Paste the candidate's LinkedIn URL --- the URL is **automatically detected**<br>"
            "2. Click **📄 Save to PDF (LinkedIn)** to open the exact profile page<br>"
            "3. On the profile page, click **More → Save to PDF**<br>"
            "4. Upload the downloaded PDF instead of copying text",
            unsafe_allow_html=True
        )
    
    col1, col2 = st.columns([4, 2])
    with col1:
        profile_url = st.text_input("", placeholder="https://linkedin.com/in/...", label_visibility="collapsed")
    with col2:
        target = profile_url.strip() if profile_url.strip() else "https://linkedin.com"
        st.link_button("📄 Save to PDF (LinkedIn)", target, use_container_width=True)
    
    with st.popover("📋 Copy-Paste Guide", use_container_width=False):
        st.markdown(
            "**Sections to copy:**<br>"
            "1. Name & Headline<br>"
            "2. About<br>"
            "3. Experience<br>"
            "4. Skills<br>"
            "5. Education<br>"
            "6. Licenses & Certifications",
            unsafe_allow_html=True
        )
    
    st.markdown(
        '<style>[data-testid="stTextInput"] > div > div > input {border: 2px solid #007BFF !important; border-radius: 6px;}</style>',
        unsafe_allow_html=True,
    )
    
    with st.form("analyzer"):
        job_desc = st.text_area("Job Description (paste as-is)", height=250)
        profile_text = st.text_area("LinkedIn / CV Text (paste as-is)", height=300)
        uploaded = st.file_uploader("OR upload PDF / DOCX CV (optional)", type=["pdf", "docx"])
        submitted = st.form_submit_button("Analyze", type="primary")
    
    if submitted:
        if not job_desc:
            st.error("Job Description is required.")
            st.stop()
        
        file_text = extract_text(uploaded)
        
        with st.spinner("Analyzing with Gemini Flash 2.5..."):
            report, error = analyze_single_candidate(job_desc, profile_text, file_text)
            
            if error:
                st.error(f"Analysis error: {error}")
                st.stop()
        
        st.session_state["last_report"] = report
        st.session_state["linkedin_url"] = profile_url.strip()

else:
    # Batch processing interface
    st.markdown("### 📁 Batch Processing Mode")
    st.info("Upload up to 5 CV files (PDF/DOCX) for batch analysis against a single job description.")
    
    with st.form("batch_analyzer"):
        job_desc = st.text_area("Job Description (paste as-is)", height=250)
        uploaded_files = st.file_uploader(
            "Upload CV files (PDF / DOCX)", 
            type=["pdf", "docx"], 
            accept_multiple_files=True,
            help="Select up to 5 files for batch processing"
        )
        batch_submitted = st.form_submit_button("Analyze Batch", type="primary")
    
    if batch_submitted:
        if not job_desc:
            st.error("Job Description is required.")
            st.stop()
        
        if not uploaded_files:
            st.error("Please upload at least one CV file.")
            st.stop()
        
        if len(uploaded_files) > 5:
            st.error("Maximum 5 files allowed for batch processing.")
            st.stop()
        
        # Process batch
        batch_reports = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Analyzing {uploaded_file.name}... ({i+1}/{len(uploaded_files)})")
            
            file_text = extract_text(uploaded_file)
            if not file_text.strip():
                st.warning(f"Could not extract text from {uploaded_file.name}. Skipping...")
                continue
            
            # Extract candidate name from CV text
            candidate_name = extract_candidate_name(file_text)
            
            with st.spinner(f"Processing {uploaded_file.name}..."):
                report, error = analyze_single_candidate(job_desc, "", file_text)
                
                if error:
                    st.error(f"Error analyzing {uploaded_file.name}: {error}")
                    continue
                
                batch_reports.append({
                    'report': report,
                    'filename': uploaded_file.name,
                    'candidate_name': candidate_name
                })
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            time.sleep(0.5)  # Small delay to avoid rate limiting
        
        status_text.text("Analysis complete!")
        
        if batch_reports:
            st.session_state["batch_reports"] = batch_reports
            st.session_state["batch_job_desc"] = job_desc

# Display results for single candidate
if "last_report" in st.session_state and analysis_mode == "Single Candidate":
    report = st.session_state["last_report"]
    st.success("Report ready!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📄 Download PDF Report", data=build_pdf(report, st.session_state.get("linkedin_url", "")), file_name="ResumeAlign_Report.pdf", mime="application/pdf")
    with col2:
        st.download_button("💾 Download JSON", data=json.dumps(report, indent=2), file_name="ResumeAlign_Report.json", mime="application/json")
    
    st.subheader("Formatted Report")
    st.metric("Alignment Score", f"{report['alignment_score']} / 10")
    st.write("**Summary:**", report["candidate_summary"])
    
    st.write("**Strengths:**")
    for s in report["strengths"]:
        st.write("-", s)
    
    st.write("**Areas for Improvement:**")
    for a in report["areas_for_improvement"]:
        st.write("-", a)
    
    st.write("**Interview Questions:**")
    for i, q in enumerate(report["suggested_interview_questions"], 1):
        st.write(f"{i}.", q)
    
    st.write("**Recommendation:**", report["next_round_recommendation"])

# Display results for batch processing
if "batch_reports" in st.session_state and analysis_mode == "Batch Processing (up to 5 files)":
    batch_reports = st.session_state["batch_reports"]
    job_desc = st.session_state["batch_job_desc"]
    
    st.success(f"Batch analysis complete! Processed {len(batch_reports)} candidates.")
    
    # Download options
    col1, col2 = st.columns(2)
    with col1:
        zip_data = create_batch_zip(batch_reports, job_desc)
        st.download_button(
            "📦 Download All Reports (ZIP)", 
            data=zip_data, 
            file_name=f"ResumeAlign_Batch_{datetime.now().strftime('%Y%m%d_%H%M')}.zip", 
            mime="application/zip"
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
                    "recommendation": r['report']['next_round_recommendation'],
                    "experience": r['report']['experience_years']['raw_estimate']
                } for r in batch_reports
            ]
        }
        st.download_button(
            "📊 Download Summary (JSON)", 
            data=json.dumps(summary_json, indent=2), 
            file_name="batch_summary.json", 
            mime="application/json"
        )
    
    # Display summary table
    st.subheader("Batch Results Summary")
    
    summary_data = []
    for i, report_data in enumerate(batch_reports, 1):
        report = report_data['report']
        candidate_name = report_data['candidate_name']
        filename = report_data['filename']
        display_name = candidate_name if candidate_name != "Unknown Candidate" else filename
        summary_data.append({
            "Candidate": f"{i}. {display_name}",
            "Score": f"{report['alignment_score']}/10",
            "Experience": report['experience_years']['raw_estimate'],
            "Recommendation": report['next_round_recommendation']
        })
    
    st.table(summary_data)
    
    # Individual reports
    st.subheader("Individual Reports")
    
    for i, report_data in enumerate(batch_reports, 1):
        report = report_data['report']
        filename = report_data['filename']
        candidate_name = report_data['candidate_name']
        display_name = candidate_name if candidate_name != "Unknown Candidate" else filename
        
        with st.expander(f"📄 {display_name} ({filename})", expanded=False):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Score", f"{report['alignment_score']}/10")
            with col2:
                st.write("**Recommendation:**", report['next_round_recommendation'])
            
            st.write("**Summary:**", report["candidate_summary"])
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Strengths:**")
                for s in report["strengths"]:
                    st.write("-", s)
            
            with col2:
                st.write("**Areas for Improvement:**")
                for a in report["areas_for_improvement"]:
                    st.write("-", a)
            
            st.write("**Interview Questions:**")
            for j, q in enumerate(report["suggested_interview_questions"], 1):
                st.write(f"{j}. {q}")
