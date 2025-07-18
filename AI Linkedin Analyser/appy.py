# app.py
import os, json, streamlit as st
from datetime import datetime
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document

# ---------- CONFIG ----------
# On Vercel, set GEMINI_API_KEY in Environment Variables (Settings → Environment Variables)
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    st.error("GEMINI_API_KEY not found.  Add it to Vercel environment variables.")
    st.stop()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------- HELPERS ----------
def extract_text(upload):
    if upload is None:
        return ""
    if upload.type == "application/pdf":
        return "\n".join(p.extract_text() for p in PdfReader(upload).pages)
    if upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(upload).paragraphs)
    return ""

SYSTEM_PROMPT = "You are an expert recruiter. Return valid JSON matching the schema exactly."

def build_prompt(jd, profile_text, file_text):
    return f"""
Job Description:
{jd}

LinkedIn / CV Text:
{profile_text}

Additional File Text:
{file_text if file_text.strip() else "None provided"}

Produce a single JSON object:
{{
  "alignment_score": <integer 0–10>,
  "experience_years": {{
    "raw_estimate": "<string>",
    "confidence": "<High | Medium | Low>",
    "source": "<Manual text | File>"
  }},
  "candidate_summary": "<300 words>",
  "areas_for_improvement": ["<string>", "<string>", "<string>", "<string>", "<string>"],
  "strengths": ["<string>", "<string>", "<string>", "<string>", "<string>"],
  "suggested_interview_questions": ["<string>", "<string>", "<string>", "<string>", "<string>"],
  "next_round_recommendation": "<Yes | No | Maybe – brief reason>",
  "sources_used": ["Manual text", "File"]
}}
"""

# ---------- UI ----------
st.set_page_config(page_title="AI LinkedIn Profile Analyzer", layout="wide")
st.title("AI LinkedIn Profile Analyzer (Gemini)")
st.markdown("Paste the Job Description and LinkedIn/CV text. Optionally upload a PDF/DOCX.")

with st.form("analyzer"):
    jd = st.text_area("Job Description", height=220)
    profile_text = st.text_area("LinkedIn / CV Text", height=300)
    uploaded = st.file_uploader("Upload PDF / DOCX CV (optional)", type=["pdf", "docx"])
    submitted = st.form_submit_button("Analyze", type="primary")

if submitted:
    if not jd or not profile_text:
        st.error("Both Job Description and Profile text are required.")
        st.stop()

    file_text = extract_text(uploaded)
    prompt = build_prompt(jd, profile_text, file_text)

    with st.spinner("Analyzing with Gemini..."):
        try:
            resp = model.generate_content([SYSTEM_PROMPT, prompt])
            result = json.loads(resp.text.strip("```json").strip("```"))
        except Exception as e:
            st.error(f"LLM error: {e}")
            st.stop()

    st.success("Done!")
    st.json(result)
    st.subheader("Formatted Report")
    st.write("**Alignment Score:**", result["alignment_score"], "/10")
    st.write("**Experience Estimate:**", result["experience_years"]["raw_estimate"],
             f"({result['experience_years']['confidence']} confidence)")
    st.write("**Summary:**", result["candidate_summary"])
    st.write("**Strengths:**")
    st.write("\n".join(f"- {s}" for s in result["strengths"]))
    st.write("**Areas for Improvement:**")
    st.write("\n".join(f"- {a}" for a in result["areas_for_improvement"]))
    st.write("**Interview Questions:**")
    st.write("\n".join(f"{i+1}. {q}" for i, q in enumerate(result["suggested_interview_questions"])))
    st.write("**Recommendation:**", result["next_round_recommendation"])

    fname = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button("Download JSON", json.dumps(result, indent=2), fname, "application/json")