"""
AI Analysis module for ResumeAlign
Handles Gemini AI integration for resume analysis
"""

import json
import google.generativeai as genai
import os

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# System prompt for consistent AI behavior
SYSTEM_PROMPT = "Use only the text provided. Return valid JSON matching the schema."


def build_prompt(jd, profile_text, file_text):
    """Build the analysis prompt for Gemini AI"""
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
