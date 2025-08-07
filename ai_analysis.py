import google.generativeai as genai
import streamlit as st
import json
from typing import Dict, Any, Optional

def configure_gemini():
    """Configure Gemini API"""
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Gemini API key not found in secrets!")
        return None
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-pro')

def analyze_resume_job_match(resume_text: str, job_description: str, candidate_name: str) -> Dict[str, Any]:
    """
    Analyze resume against job description using Gemini AI
    """
    model = configure_gemini()
    if not model:
        return None
    
    prompt = f"""
    As an expert HR analyst, analyze this resume against the job description and provide a comprehensive assessment.

    CANDIDATE: {candidate_name}

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    Please provide your analysis in the following JSON format:
    {{
        "overall_score": <number 0-100>,
        "skills_score": <number 0-100>,
        "experience_score": <number 0-100>,
        "education_score": <number 0-100>,
        "strengths": ["strength1", "strength2", "strength3"],
        "weaknesses": ["weakness1", "weakness2", "weakness3"],
        "missing_skills": ["skill1", "skill2", "skill3"],
        "recommendations": ["recommendation1", "recommendation2", "recommendation3"],
        "key_matches": ["match1", "match2", "match3"],
        "experience_analysis": "detailed analysis of experience relevance",
        "skills_analysis": "detailed analysis of skills match",
        "improvement_areas": ["area1", "area2", "area3"],
        "interview_focus": ["focus1", "focus2", "focus3"],
        "cultural_fit_notes": "assessment of cultural alignment",
        "next_steps": "recommended next steps for this candidate"
    }}

    Ensure all scores are realistic and well-justified. Provide actionable insights.
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Parse JSON response
        response_text = response.text
        
        # Clean up response if it has markdown formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        analysis = json.loads(response_text)
        return analysis
        
    except json.JSONDecodeError as e:
        st.error(f"Error parsing AI response: {e}")
        return None
    except Exception as e:
        st.error(f"Error in AI analysis: {e}")
        return None

def generate_improvement_suggestions(analysis: Dict[str, Any]) -> str:
    """
    Generate specific improvement suggestions based on analysis
    """
    model = configure_gemini()
    if not model or not analysis:
        return ""
    
    prompt = f"""
    Based on this resume analysis, provide specific, actionable improvement suggestions:

    Analysis Results:
    - Overall Score: {analysis.get('overall_score', 0)}%
    - Missing Skills: {analysis.get('missing_skills', [])}
    - Weaknesses: {analysis.get('weaknesses', [])}
    - Improvement Areas: {analysis.get('improvement_areas', [])}

    Provide 5-7 concrete, actionable steps the candidate can take to improve their profile for this role.
    Format as a bulleted list with specific actions.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating suggestions: {e}")
        return ""

def validate_analysis_response(analysis: Dict[str, Any]) -> bool:
    """
    Validate that the AI response contains required fields
    """
    required_fields = [
        'overall_score', 'skills_score', 'experience_score', 'education_score',
        'strengths', 'weaknesses', 'missing_skills', 'recommendations'
    ]
    
    return all(field in analysis for field in required_fields)
