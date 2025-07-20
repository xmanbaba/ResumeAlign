# app.py – ResumeFit FINAL (footer + page numbers, no URL in footer)
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

def build_pdf(report):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=16, spaceAfter=12, textColor=blue)
    normal_style = ParagraphStyle("Normal", parent=styles["Normal"], fontSize=11, spaceAfter=6)

    def add_footer(canvas, doc):
        canvas.saveState()
        footer_text = f"© 2025 ResumeFit – AI Resume & CV Analyzer   |   Page {doc.page}"
        canvas.drawCentredString(A4[0] / 2, 0.75 * inch, footer_text)
        canvas.restoreState()

    story = []
    story.append(Paragraph("ResumeFit Analysis Report", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Name of Candidate:</b> {report.get('candidate_summary','').split(' is ')[0]}", normal_style))
    story.append(Paragraph(f"<b>Review Date:</b> {datetime.now():%d %B %Y}", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Alignment Score:</b> {report['alignment_score']} / 10", title_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Experience Estimate:</b>", title_style))
    story.append(Paragraph(f"{report['experience_years']['raw_estimate']} ({report['experience_years']['confidence']} confidence)", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Summary:</b>", title_style))
    story.append(Paragraph(report.get("candidate_summary", ""), normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Strengths:</b>", title_style))
    for s in report.get("strengths", []):
        story.append(Paragraph(f"• {s}", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Areas for Improvement:</b>", title_style))
    for a in report.get("areas_for_improvement", []):
        story.append(Paragraph(f"• {a}", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Interview Questions:</b>", title_style))
    for i, q in enumerate(report.get("suggested_interview_questions", []), 1):
        story.append(Paragraph(f"{i}. {q}", normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Recommendation:</b>", title_style))
    story.append(Paragraph(report.get("next_round_recommendation", ""), normal_style))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

SYSTEM_PROMPT = "You are an expert recruiter. Use ONLY the text provided; do not invent data. Return only valid JSON matching the schema below."

def build_prompt(jd, profile_text, file_text):
    return f"Job Description:\n{jd}\n\nCandidate Profile / CV:\n{profile_text}\n\nExtra File Text:\n{file_text if file_text.strip() else 'None provided'}\n\nReturn valid JSON:\n{{\n  'alignment_score': <0-10>,\n  'experience_years': {'raw_estimate': '<string>', 'confidence': '<High|Medium|Low>', 'source': '<Manual text|File>'},\n  'candidate_summary': '<300 words>',\n  'areas_for_improvement': ['<string>','<string>','<string>','<string>','<string>'],\n  'strengths': ['<string>','<string>','<string>','<string>','<string>'],\n  'suggested_interview_questions': ['<string>','<string>','<string>','<string>','<string>'],\n  'next_round_recommendation': '<Yes|No|Maybe – brief reason>',\n  'sources_used': ['Manual text','File']\n}}"

# ---------- UI ----------
st.set_page_config(page_title="ResumeFit", layout="wide")
st.title("ResumeFit – AI Resume & CV Analyzer")

st.markdown("### 🔗  LinkedIn Helpers")
with st.popover("ℹ️  How to use the URL", use_container_width=False):
    st.markdown(
        "**Step-by-step (no copy-paste needed):**  \n"
        "1. Paste the candidate's LinkedIn URL – **URL is auto-detected**  \n"
        "2. Click **📄 Save to PDF (LinkedIn)** to open the exact profile page  \n"
        "3. On the profile page, click **More** → **Save to PDF**  \n"
        "4. Upload the downloaded PDF instead of copying text  \n"
        "**Tip:** If it ever fails, press **Enter** after pasting."
    )

col1, col2 = st.columns([4, 2])
with col1:
    profile_url = st.text_input("", placeholder="https://linkedin.com/in/...", label_visibility="collapsed")
with col2:
    target = profile_url.strip() if profile_url.strip() else "https://linkedin.com"
    st.link_button("📄 Save to PDF (LinkedIn)", target, use_container_width=True)

with st.expander("📋 Copy-Paste Guide (click to open)", expanded=False):
    st.markdown(
        "**Sections to copy:**  \n"
        "1. Name & Headline  \n"
        "2. About  \n"
        "3. Experience  \n"
        "4. Skills  \n"
        "5. Education  \n"
        "6. Licenses & Certifications"
    )

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
    st.session_state["last_report"] = report

if "last_report" in st.session_state:
    report = st.session_state["last_report"]
    st.success("Report ready!")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📄 Download PDF Report", data=build_pdf(report), file_name="ResumeFit_Report.pdf", mime="application/pdf")
    with col2:
        st.download_button("💾 Download JSON", data=json.dumps(report, indent=2), file_name="ResumeFit_Report.json", mime="application/json")
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
