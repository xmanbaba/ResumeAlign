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
import re

# ---------- CONFIG ----------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def extract_text(upload):
    if not upload:
        return ""
    if upload.type == "application/pdf":
        return "\n".join(p.extract_text() or "" for p in PdfReader(upload).pages)
    if upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(upload).paragraphs)
    return ""

def extract_candidate_name(text):
    """Enhanced candidate name extraction with LinkedIn profile and combined document support"""
    if not text.strip():
        return "Unknown Candidate"
   
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
   
    if not lines:
        return "Unknown Candidate"
   
    # Strategy 1: Look for explicit name patterns first
    name_patterns = [
        r'name\s*[:]\s*(.+)',
        r'full\s*name\s*[:]\s*(.+)',
        r'candidate\s*name\s*[:]\s*(.+)',
        r'applicant\s*name\s*[:]\s*(.+)'
    ]
   
    for line in lines[:10]: # Check first 10 lines
        for pattern in name_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted_name = match.group(1).strip()
                if is_valid_name(extracted_name):
                    return clean_name(extracted_name)
   
    # Strategy 2: Handle LinkedIn and combined docs
    linkedin_indicators = ['contact', 'about', 'experience', 'education', 'skills', 'linkedin']
    first_few_lines = ' '.join(lines[:5]).lower()
    is_linkedin_or_combined = any(indicator in first_few_lines for indicator in linkedin_indicators)
   
    if is_linkedin_or_combined:
        for i, line in enumerate(lines[:15]):
            line_lower = line.lower()
            # Skip section headers and common non-name lines
            if line_lower in ['contact', 'about', 'experience', 'education', 'skills', 'linkedin', 
                             'profile', 'summary', 'objective', 'cover letter']:
                continue
            # Skip job-related lines
            job_keywords = ['engineer', 'manager', 'director', 'analyst', 'consultant', 'developer',
                          'specialist', 'coordinator', 'assistant', 'lead', 'senior', 'junior',
                          'company', 'inc', 'ltd', 'corp', 'llc', 'university', 'college']
            if any(keyword in line_lower for keyword in job_keywords):
                continue
            if is_valid_name(line):
                return clean_name(line)
   
    # Strategy 3: First valid name in top 5 lines
    for line in lines[:5]:
        if is_valid_name(line):
            return clean_name(line)
   
    # Strategy 4: Capitalized name sequences
    for line in lines[:10]:
        words = line.split()
        if 2 <= len(words) <= 4:
            capitalized_words = [w for w in words if w and w[0].isupper() and w.isalpha()]
            if len(capitalized_words) >= 2 and len(capitalized_words) == len(words):
                candidate_name = ' '.join(capitalized_words)
                if is_valid_name(candidate_name):
                    return clean_name(candidate_name)
   
    # Strategy 5: AI extraction as last resort
    try:
        text_sample = text[:500]
        ai_extracted_name = extract_name_with_ai(text_sample)
        if ai_extracted_name and is_valid_name(ai_extracted_name):
            return clean_name(ai_extracted_name)
    except:
        pass
   
    return clean_name(lines[0]) if lines else "Unknown Candidate"

def is_valid_name(name_candidate):
    """Check if a string looks like a valid name"""
    if not name_candidate or not name_candidate.strip():
        return False
   
    name = name_candidate.strip()
   
    # Basic checks
    if len(name) < 2 or len(name) > 100:
        return False
   
    # Should not contain numbers
    if any(char.isdigit() for char in name):
        return False
   
    # Should not be common non-name words
    non_names = ['contact', 'about', 'experience', 'education', 'skills', 'profile', 'resume', 'cv',
                'curriculum', 'vitae', 'linkedin', 'email', 'phone', 'address', 'objective',
                'summary', 'unknown', 'candidate', 'applicant']
   
    if name.lower() in non_names:
        return False
   
    # Should have at least 2 parts (first and last name)
    parts = name.split()
    if len(parts) < 2:
        return False
   
    # Each part should be mostly alphabetic
    for part in parts:
        if not part.replace('.', '').replace(',', '').replace('-', '').replace("'", '').isalpha():
            return False
   
    return True

def clean_name(name):
    """Clean and format extracted name"""
    if not name:
        return "Unknown Candidate"
   
    # Remove common prefixes and suffixes
    prefixes = ['mr.', 'mrs.,', 'ms.,', 'dr.,', 'prof.,', 'sir', 'madam']
    suffixes = ['cv', 'resume', 'curriculum vitae', 'profile']
   
    name = name.strip()
    name_lower = name.lower()
   
    # Remove prefixes
    for prefix in prefixes:
        if name_lower.startswith(prefix):
            name = name[len(prefix):].strip()
            break
   
    # Remove suffixes
    for suffix in suffixes:
        if name_lower.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break
   
    # Title case the name
    words = name.split()
    cleaned_words = []
    for word in words:
        if word:
            # Handle names with apostrophes and hyphens
            if "'" in word or "-" in word:
                parts = re.split(r"(['-])", word)
                title_parts = []
                for part in parts:
                    if part in ["'", "-"]:
                        title_parts.append(part)
                    else:
                        title_parts.append(part.capitalize())
                cleaned_words.append(''.join(title_parts))
            else:
                cleaned_words.append(word.capitalize())
   
    result = ' '.join(cleaned_words)
    return result if result else "Unknown Candidate"

def extract_name_with_ai(text_sample):
    """Use AI to extract name from text as last resort"""
    try:
        prompt = f"""Extract only the candidate's full name from this CV/resume text. Return only the name, nothing else.

Text: {text_sample}

Name:"""
       
        response = model.generate_content(prompt)
        extracted = response.text.strip()
       
        # Clean up AI response
        extracted = re.sub(r'^(name:|full name:|candidate name:)', '', extracted, flags=re.IGNORECASE).strip()
        extracted = extracted.replace('"', '').replace("'", '').strip()
       
        return extracted if extracted else None
    except:
        return None

def create_safe_filename(candidate_name, filename, index):
    """Create a safe filename ensuring uniqueness"""
    if candidate_name and candidate_name != "Unknown Candidate":
        # Use candidate name as base
        base_name = candidate_name.replace(' ', '_')
    else:
        # Use original filename without extension
        base_name = filename.rsplit('.', 1)[0]
   
    # Remove unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
    safe_name = re.sub(r'[^\w\-_\.]', '_', safe_name)
   
    # Ensure uniqueness by adding index
    return f"Report_{index:02d}_{safe_name}.pdf"

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
    """Create a ZIP file containing all batch reports with improved filename handling"""
    zip_buffer = BytesIO()
   
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Track used filenames to avoid duplicates
        used_filenames = set()
       
        # Add individual PDF reports
        for i, report_data in enumerate(reports, 1):
            report = report_data['report']
            filename = report_data['filename']
            candidate_name = report_data['candidate_name']
           
            # Generate PDF
            pdf_buffer = build_pdf(report, candidate_name=candidate_name, extracted_from_cv=True)
           
            # Create safe, unique filename
            safe_filename = create_safe_filename(candidate_name, filename, i)
           
            # Ensure uniqueness
            counter = 1
            original_safe_filename = safe_filename
            while safe_filename in used_filenames:
                base_name = original_safe_filename.rsplit('.', 1)[0]
                safe_filename = f"{base_name}_v{counter}.pdf"
                counter += 1
           
            used_filenames.add(safe_filename)
           
            # Add to ZIP
            zip_file.writestr(safe_filename, pdf_buffer.read())
           
            # Debug logging
            print(f"Added to ZIP: {safe_filename} (Original: {filename}, Name: {candidate_name})")
       
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
           
            # Extract candidate name with enhanced logic first
            candidate_name = extract_candidate_name(file_text)
           
            # Debug display for testing
            st.info(f"Extracted name for {uploaded_file.name}: '{candidate_name}'")
           
            with st.spinner(f"Processing {uploaded_file.name}..."):
                report, error = analyze_single_candidate(job_desc, "", file_text)
               
                if error:
                    st.error(f"Error analyzing {uploaded_file.name}: {error}")
                    continue
               
                # Use candidate_summary as fallback if name extraction failed
                if not candidate_name and 'candidate_summary' in report:
                    candidate_name = report.get('candidate_summary', '').split(' is ')[0] if ' is ' in report.get('candidate_summary', '') else candidate_name
                    if not candidate_name or not is_valid_name(candidate_name):
                        candidate_name = "Unknown Candidate"
               
                batch_reports.append({
                    'report': report,
                    'filename': uploaded_file.name,
                    'candidate_name': candidate_name
                })
           
            progress_bar.progress((i + 1) / len(uploaded_files))
            time.sleep(0.5) # Small delay to avoid rate limiting
       
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
