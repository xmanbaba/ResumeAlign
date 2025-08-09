"""
AI Analysis module for ResumeAlign - IMPROVED VERSION
Handles Gemini AI integration for resume analysis with enhanced consistency
"""

import json
import google.generativeai as genai
import os

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# Enhanced system prompt for more consistent results
SYSTEM_PROMPT = """You are a professional HR analyst. Your task is to provide consistent, objective analysis of candidates against job requirements. 

IMPORTANT GUIDELINES:
1. Be consistent in your scoring - similar candidates with similar qualifications should receive similar scores
2. Base your analysis strictly on the provided content
3. Return valid JSON matching the exact schema provided
4. Use specific examples from the candidate's profile to justify your assessment
5. Ensure candidate names are properly extracted and included in the summary

SCORING CRITERIA:
- 9-10: Exceptional match, exceeds most requirements
- 7-8: Strong match, meets most requirements well
- 5-6: Good match, meets basic requirements
- 3-4: Partial match, some gaps in requirements
- 1-2: Poor match, significant gaps

Be thorough and consistent in your evaluation."""


def build_prompt(jd, profile_text, file_text):
    """Build the enhanced analysis prompt for Gemini AI with better consistency"""
    extra = file_text.strip() if file_text.strip() else "None provided"
    
    return f"""ANALYZE this candidate against the job requirements and return ONLY valid JSON.

JOB DESCRIPTION:
{jd}

CANDIDATE PROFILE/CV:
{profile_text}

ADDITIONAL FILE CONTENT:
{extra}

INSTRUCTIONS:
1. Carefully analyze the candidate's qualifications against job requirements
2. Extract the candidate's full name from their profile/CV and start the summary with their name
3. Be consistent in scoring - use the same criteria for all candidates
4. Provide specific, actionable feedback based on the content provided

Return ONLY this JSON structure (no additional text or formatting):
{{
 "alignment_score": <0-10 integer>,
 "experience_years": {{"raw_estimate": "<specific years/level>", "confidence": "<High|Medium|Low>", "source": "<Manual text|File>"}},
 "candidate_summary": "<Start with candidate name. 250-300 words professional summary>",
 "areas_for_improvement": ["<specific area 1>","<specific area 2>","<specific area 3>","<specific area 4>","<specific area 5>"],
 "strengths": ["<specific strength 1>","<specific strength 2>","<specific strength 3>","<specific strength 4>","<specific strength 5>"],
 "suggested_interview_questions": ["<question 1>","<question 2>","<question 3>","<question 4>","<question 5>"],
 "next_round_recommendation": "<Yes|No|Maybe> - <brief specific reason based on analysis>",
 "sources_used": ["<Manual text|File>"]
}}"""


def analyze_single_candidate(job_desc, profile_text, file_text=""):
    """Analyze a single candidate and return the report with improved consistency"""
    prompt = build_prompt(job_desc, profile_text, file_text)
    
    try:
        # Use temperature=0.3 for more consistent results while maintaining quality
        response = model.generate_content(
            [SYSTEM_PROMPT, prompt],
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistency
                candidate_count=1,
                max_output_tokens=2048,
            )
        )
        
        # Clean up response text
        response_text = response.text.strip()
        
        # Remove markdown formatting if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        report = json.loads(response_text)
        
        # Validate required fields
        required_fields = [
            'alignment_score', 'experience_years', 'candidate_summary',
            'areas_for_improvement', 'strengths', 'suggested_interview_questions',
            'next_round_recommendation', 'sources_used'
        ]
        
        for field in required_fields:
            if field not in report:
                return None, f"Missing required field: {field}"
        
        # Ensure alignment_score is within valid range
        if not isinstance(report['alignment_score'], int) or not (0 <= report['alignment_score'] <= 10):
            return None, "Invalid alignment_score: must be integer between 0-10"
        
        return report, None
        
    except json.JSONDecodeError as e:
        return None, f"JSON parsing error: {str(e)}"
    except Exception as e:
        return None, f"Analysis error: {str(e)}")


def extract_candidate_name_from_summary(summary):
    """Extract candidate name from the beginning of the summary"""
    if not summary:
        return None
    
    # Look for name at the beginning of summary
    words = summary.split()
    if len(words) >= 2:
        # Check if first 2-3 words look like a name
        potential_name = " ".join(words[:3])
        if any(char.isalpha() for char in potential_name) and not any(char.isdigit() for char in potential_name):
            # Basic name validation
            name_words = potential_name.split()
            if all(word[0].isupper() for word in name_words if word):
                return potential_name
        
        # Try first 2 words
        potential_name = " ".join(words[:2])
        if any(char.isalpha() for char in potential_name) and not any(char.isdigit() for char in potential_name):
            name_words = potential_name.split()
            if all(word[0].isupper() for word in name_words if word):
                return potential_name
    
    return None, f"Analysis error: {str(e)}
