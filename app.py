# app.py  – ResumeFit with helper buttons
import os, json, streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document

# ---------- CONFIG ----------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------- HELPERS ----------
def extract_text(upload):
    if not upload:
        return ""
    if upload.type == "application/pdf":
        return "\n".join(p.extract_text() or "" for p in PdfReader(upload).pages)
    if upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(upload).paragraphs)
    return ""

def build_pdf(report):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    text = json.dumps(report, indent=2, ensure_ascii=False)
    y = height - 40
    for line in text.splitlines():
        if y < 40:
            c.showPage()
            y = height - 40
        c.drawString(40, y, line[:90])
        y -= 14
    c.save()
    buffer.seek(0)
    return buffer

SYSTEM_PROMPT = """
You are an expert recruiter. Use ONLY the text provided; do not invent data.
Return valid JSON matching the schema below.
"""

def build_prompt(jd, profile_text, file_text):
    return f"""
Job Description:
{jd}

Candidate Profile / CV:
{profile_text}

Extra File Text:
{file_text if file_text.strip() else "None provided"}

Return valid JSON:
{{
  "alignment_score": <0-10>,
  "experience_years": {{"raw_estimate": "<string>", "confidence": "<High|Medium|Low>", "source": "<Manual text|File>"}},
  "candidate_summary": "<300 words>",
  "areas_for_improvement": ["<string>", "<string>", "<string>", "<string>", "<string>"],
  "strengths": ["<string>", "<string>", "<string>", "<string>", "<string>"],
  "suggested_interview_questions": ["<string>", "<string>", "<string>", "<string>", "<string>"],
  "next_round_recommendation": "<Yes|No|Maybe – brief reason>",
  "sources_used": ["Manual text", "File"]
}}
"""

# ---------- UI ----------
st.set_page_config(page_title="ResumeFit", layout="wide")
st.title("ResumeFit – AI Resume & CV Analyzer")

# ---------- 3 HELPER BUTTONS ----------
st.markdown("### 🆘  LinkedIn Helpers")
col1, col2, col3 = st.columns(3)

with col1:
    profile_url = st.text_input("LinkedIn profile URL (optional)", placeholder="https://linkedin.com/in/...")
    if profile_url:
        st.link_button("🔗  Open Profile", profile_url, use_container_width=True)

with col2:
    if st.button("📋  Copy-Paste Guide", use_container_width=True):
        st.info(
            "**Sections to copy:**\n"
            "1. **About** – summary paragraph\n"
            "2. **Experience** – job titles, companies, dates, descriptions\n"
            "3. **Skills** – listed skills or endorsements"
        )

with col3:
    if profile_url:
        pdf_url = profile_url.rstrip("/") + "/detail/contact-info/overlay/save-to-pdf"
        st.link_button("📄  Save to PDF (LinkedIn)", pdf_url, use_container_width=True)
    else:
        st.link_button("📄  Save to PDF (LinkedIn)", "https://linkedin.com", use_container_width=True)

st.markdown("---")

# ---------- ANALYZER ----------
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
    prompt = build_prompt(job_desc, profile_text, file_text)

    with st.spinner("Analyzing with Gemini Flash 2.5…"):
        try:
            response = model.generate_content([SYSTEM_PROMPT, prompt])
            report = json.loads(response.text.strip("```json").strip("```"))
        except Exception as e:
            st.error(f"Analysis error: {e}")
            st.stop()

    st.success("Done!")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📄  Download PDF Report", data=build_pdf(report), file_name="ResumeFit_Report.pdf", mime="application/pdf")
    with col2:
        st.download_button("💾  Download JSON", data=json.dumps(report, indent=2), file_name="ResumeFit_Report.json", mime="application/json")

    st.subheader("Formatted Report")
    st.metric("Alignment Score", f"{report['alignment_score']} / 10")
    st.write("**Summary:**", report["candidate_summary"])
    st.write("**Strengths:**")
    for s in report["strengths"]: st.write("-", s)
    st.write("**Areas for Improvement:**")
    for a in report["areas_for_improvement"]: st.write("-", a)
    st.write("**Interview Questions:**")
    for i, q in enumerate(report["suggested_interview_questions"], 1): st.write(f"{i}.", q)
    st.write("**Recommendation:**", report["next_round_recommendation"])
