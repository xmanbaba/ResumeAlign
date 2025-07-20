# app.py  – AI LinkedIn Profile Analyzer (Gemini Flash 2.5, no scraping)
import os, json, streamlit as st
from datetime import datetime
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document

# ---------- 1. Configure Gemini ----------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ---------- 2. Helpers ----------
def extract_text(upload):
    if not upload:
        return ""
    if upload.type == "application/pdf":
        return "\n".join(p.extract_text() or "" for p in PdfReader(upload).pages)
    if upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(upload).paragraphs)
    return ""

SYSTEM_PROMPT = """
You are an expert recruiter.  
Accept any formatting (bullets, emojis, PDF text).  
Return only valid JSON that matches the schema.
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

# ---------- 3. Streamlit UI ----------
st.set_page_config(page_title="AI LinkedIn Profile Analyzer", layout="wide")
st.title("AI LinkedIn Profile Analyzer (Gemini Flash 2.5)")

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
            data = json.loads(response.text.strip("```json").strip("```"))
        except Exception as e:
            st.error(f"Analysis error: {e}")
            st.stop()

    st.success("Done!")
    st.json(data)
    st.subheader("Formatted Report")
    st.metric("Alignment Score", f"{data['alignment_score']} / 10")
    st.write("**Summary:**", data["candidate_summary"])
    st.write("**Strengths:**")
    for s in data["strengths"]:
        st.write("-", s)
    st.write("**Areas for Improvement:**")
    for a in data["areas_for_improvement"]:
        st.write("-", a)
    st.write("**Interview Questions:**")
    for i, q in enumerate(data["suggested_interview_questions"], 1):
        st.write(f"{i}.", q)
    st.write("**Recommendation:**", data["next_round_recommendation"])

    fname = f"report_{datetime.now():%Y%m%d_%H%M%S}.json"
    st.download_button("Download JSON", json.dumps(data, indent=2), fname, "application/json")
