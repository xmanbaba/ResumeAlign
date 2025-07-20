# app.py – ResumeFit v4  (PDF never truncates, report persists)
import os, json, streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.colors import blue
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
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=16, spaceAfter=12, textColor=blue
    )
    normal_style = ParagraphStyle(
        "Normal", parent=styles["Normal"], fontSize=11, spaceAfter=6
    )
    story = []

    # Header
    story.append(Paragraph("ResumeFit Analysis Report", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Name of Candidate:</b> {report.get('candidate_summary','').split(' is ')[0]}", normal_style))
    story.append(Paragraph(f"<b>Review Date:</b> {datetime.now():%d %B %Y}", normal_style))
    story.append(Spacer(1, 12))

    # Alignment
    story.append(Paragraph(f"<b>Alignment Score:</b> {report['alignment_score']} / 10", title_style))
    story.append(Spacer(1, 6))

    # Experience
    story.append(Paragraph("<b>Experience Estimate:</b>", title_style))
    story.append(Paragraph(f"{report['experience_years']['raw_estimate']} ({report['experience_years']['confidence']} confidence)", normal_style))
    story.append(Spacer(1, 12))

    # Summary
    story.append(Paragraph("<b>Summary:</b>", title_style))
    story.append(Paragraph(report.get("candidate_summary", ""), normal_style))
    story.append(Spacer(1, 12))

    # Strengths
    story.append(Paragraph("<b>Strengths:</b>", title_style))
    for s in report.get("strengths", []):
        story.append(Paragraph(f"• {s}", normal_style))
    story.append(Spacer(1, 12))

    # Areas for Improvement
    story.append(Paragraph("<b>Areas for Improvement:</b>", title_style))
    for a in report.get("areas_for_improvement", []):
        story.append(Paragraph(f"• {a}", normal_style))
    story.append(Spacer(1, 12))

    # Interview Questions
    story.append(Paragraph("<b>Interview Questions:</b>", title_style))
    for i, q in enumerate(report.get("suggested_interview_questions", []), 1):
        story.append(Paragraph(f"{i}. {q}", normal_style))
    story.append(Spacer(1, 12))

    # Recommendation
    story.append(Paragraph("<b>Recommendation:</b>", title_style))
    story.append(Paragraph(report.get("next_round_recommendation", ""), normal_style))
    story.append(PageBreak())

    # Footer
    story.append(Paragraph("© 2025 ResumeFit – AI Resume & CV Analyzer", normal_style))
    doc.build(story)
    buffer.seek(0)
    return buffer

SYSTEM_PROMPT = """
You are an expert recruiter. Use ONLY the text provided; do not invent data.
Return only valid JSON matching the schema below.
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

# ---------- LINKEDIN HELPERS ----------
st.markdown("### 🔗  LinkedIn Helpers")

# 1.  Always-visible info tooltip **above** the URL field
with st.popover("ℹ️  How to use the URL", use_container_width=False):
    st.markdown(
        """
        **Step-by-step (no copy-paste needed):**  
        1. **Paste the candidate’s LinkedIn URL** **→ press Enter key (important!)**  
        2. Click **📄 Save to PDF (LinkedIn)** – this opens the exact profile page  
        3. On the profile page, click the **More** button  
        4. Choose **Save to PDF** 📥  
        5. Upload the downloaded PDF below instead of copying text
        """
    )

# 2.  URL field + blue border
st.markdown(
    """
    <style>
    [data-testid="stTextInput"] > div > div > input {
        border: 2px solid #007BFF !important;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns([4, 2])
with col1:
    profile_url = st.text_input(
        "",
        placeholder="https://linkedin.com/in/...",
        label_visibility="collapsed",
    )
with col2:
    # Always link to whatever is currently in the box (no Enter required)
    target = profile_url.strip() if profile_url.strip() else "https://linkedin.com"
    st.link_button("📄 Save to PDF (LinkedIn)", target, use_container_width=True)

# 3.  Copy-paste guide (unchanged)
with st.expander("📋  Copy-Paste Guide (click to open)", expanded=False):
    st.markdown(
        "**Sections to copy:**  \n"
        "1. **Name & Headline**  \n"
        "2. **About**  \n"
        "3. **Experience**  \n"
        "4. **Skills**  \n"
        "5. **Education**  \n"
        "6. **Licenses & Certifications**"
    )
# Blue border on URL field
st.markdown(
    """
    <style>
    [data-testid="stTextInput"] > div > div > input {
        border: 2px solid #007BFF !important;
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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

    # Persist report in session state
    st.session_state["last_report"] = report
    st.session_state["last_time"]   = datetime.now()

# ---------- PERSISTENT RESULTS ----------
if "last_report" in st.session_state:
    report = st.session_state["last_report"]
    st.success("Report ready!")
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
