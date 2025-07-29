# app.py – ResumeAlign v1.0 + Batch Analyse (feature-v2)

import os
import json
import streamlit as st
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

def build_pdf(report, linkedin_url):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.drawCentredString(A4[0] / 2, 0.75 * inch, f"© 2025 ResumeAlign – AI Resume & CV Analyzer   |   Page {doc.page}")
        canvas.restoreState()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=16, spaceAfter=12, textColor=blue)
    normal_style = ParagraphStyle("Normal", fontSize=11, spaceAfter=6)

    story = [
        Paragraph("ResumeAlign Analysis Report", title_style),
        Paragraph(f"<b>Name of Candidate:</b> {report.get('candidate_summary','').split(' is ')[0]}", normal_style),
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

# ---------- NEW: batch helper ----------
def build_batch_zip(reports_and_pdfs):
    from zipfile import ZipFile
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zf:
        for filename_base, pdf_bytes in reports_and_pdfs:
            zf.writestr(f"{filename_base}_ResumeAlign_Report.pdf", pdf_bytes.getvalue())
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
        '  "alignment_score": <0-10>,\n'
        '  "experience_years": {"raw_estimate": "<string>", "confidence": "<High|Medium|Low>", "source": "<Manual text|File>"},\n'
        '  "candidate_summary": "<300 words>",\n'
        '  "areas_for_improvement": ["<string>","<string>","<string>","<string>","<string>"],\n'
        '  "strengths": ["<string>","<string>","<string>","<string>","<string>"],\n'
        '  "suggested_interview_questions": ["<string>","<string>","<string>","<string>","<string>"],\n'
        '  "next_round_recommendation": "<Yes|No|Maybe – brief reason>",\n'
        '  "sources_used": ["Manual text","File"]\n'
        '}'
    )

# ---------- UI ----------
st.set_page_config(page_title="ResumeAlign", layout="wide")
st.title("ResumeAlign – AI Resume & CV Analyzer")

st.markdown("### 🔗  LinkedIn Helpers")
with st.popover("ℹ️  How to use the URL", use_container_width=False):
    st.markdown(
        "**Step-by-step (no copy-paste needed):**<br>"
        "1. Paste the candidate’s LinkedIn URL — the URL is **automatically detected**<br>"
        "2. Click **📄 Save to PDF (LinkedIn)** to open the exact profile page<br>"
        "3. On the profile page, click **More → Save to PDF**<br>"
        "4. Upload the downloaded PDF instead of copying text",
        unsafe_allow_html=True,
    )

col1, col2 = st.columns([4, 2])
with col1:
    profile_url = st.text_input("", placeholder="https://linkedin.com/in/...", label_visibility="collapsed")
with col2:
    target = profile_url.strip() if profile_url.strip() else "https://linkedin.com"
    st.link_button("📄 Save to PDF (LinkedIn)", target, use_container_width=True)

with st.popover("📋 Copy-Paste Guide (click to open)", use_container_width=False):
    st.markdown(
        "**Sections to copy:**<br>"
        "1. Name & Headline<br>"
        "2. About<br>"
        "3. Experience<br>"
        "4. Skills<br>"
        "5. Education<br>"
        "6. Licenses & Certifications"
    )

st.markdown(
    '<style>[data-testid="stTextInput"] > div > div > input {border: 2px solid #007BFF !important; border-radius: 6px;}</style>',
    unsafe_allow_html=True,
)

with st.form("analyzer"):
    job_desc = st.text_area("Job Description (paste as-is)", height=250)
    profile_text = st.text_area("LinkedIn / CV Text (paste as-is)", height=300)

    # SINGLE FILE UPLOADER
    uploaded = st.file_uploader("OR upload PDF / DOCX CV (optional)", type=["pdf", "docx"])

    # BATCH UPLOADER
    st.markdown("---")
    batch_files = st.file_uploader(
        "📂 Batch Upload (max 5 CVs)",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Select up to 5 PDF or DOCX files to analyse in one go.",
    )
    if len(batch_files) > 5:
        st.error("Please select 5 files or fewer for batch analysis.")
        st.stop()

    # BUTTONS
    submitted = st.form_submit_button("Analyze", type="primary", disabled=bool(batch_files))
    batch_analyse = st.form_submit_button(
        "🚀 Batch Analyse",
        type="secondary",
        disabled=not batch_files or len(batch_files) == 0,
        help="Generate one PDF report per file selected above.",
    )

# ---------- SINGLE ANALYSIS ----------
if submitted:
    if not job_desc:
        st.error("Job Description is required.")
        st.stop()
    file_text = extract_text(uploaded)
    prompt = build_prompt(job_desc, profile_text, file_text)
    with st.spinner("Analyzing with Gemini Flash 2.5…"):
        try:
            response = model.generate_content([SYSTEM_PROMPT, prompt])
            report = json.loads(response.text.strip("```json").strip("```"))
        except Exception as e:
            st.error(f"Analysis error: {e}")
            st.stop()
    st.session_state["last_report"] = report
    st.session_state["linkedin_url"] = profile_url.strip()

if "last_report" in st.session_state:
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

# ---------- BATCH ANALYSIS ----------
if batch_analyse:
    if not job_desc:
        st.error("Job Description is required for batch analysis.")
        st.stop()

    if not batch_files:
        st.error("Please select at least one CV for batch analysis.")
        st.stop()

    progress = st.progress(0)
    results = []

    for idx, file in enumerate(batch_files, 1):
        file_text = extract_text(file)
        prompt = build_prompt(job_desc, "", file_text)
        with st.spinner(f"Analysing file {idx}/{len(batch_files)} …"):
            try:
                response = model.generate_content([SYSTEM_PROMPT, prompt])
                report = json.loads(response.text.strip("```json").strip("```"))
                pdf_buffer = build_pdf(report, "")
                base_name = os.path.splitext(file.name)[0]
                results.append((base_name, pdf_buffer))
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")
                continue
        progress.progress(idx / len(batch_files))

    if results:
        zip_buffer = build_batch_zip(results)
        st.success("Batch analysis complete!")
        st.download_button(
            label="📦 Download All Reports (ZIP)",
            data=zip_buffer,
            file_name="ResumeAlign_Batch_Reports.zip",
            mime="application/zip",
        )
