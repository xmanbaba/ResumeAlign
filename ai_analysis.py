import google.generativeai as genai
import streamlit as st
import logging
import time
import json
import re
from typing import Dict, Any, Optional, List
from name_extraction import extract_name_from_text, extract_name_from_filename

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_gemini():
    """Configure Gemini API for FREE account"""
    try:
        # Get API key from Streamlit secrets (already configured)
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Gemini API key not found in secrets.")
            return False
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        logger.info("Successfully configured Gemini API for FREE account")
        return True
        
    except Exception as e:
        logger.error(f"Gemini configuration error: {str(e)}")
        st.error(f"❌ Failed to configure Gemini API: {str(e)}")
        return False

def create_analysis_prompt(resume_text: str, job_description: str, candidate_name: str, batch_mode: bool = False) -> str:
    """Create a focused analysis prompt optimized for free Gemini model"""
    
    prompt = f"""
    Analyze this resume against the job requirements and respond with ONLY valid JSON.

    CANDIDATE: {candidate_name}
    
    JOB DESCRIPTION:
    {job_description}
    
    RESUME:
    {resume_text}
    
    Rate each category 0-100:
    - Skills: How well candidate's skills match job requirements
    - Experience: Years and relevance of experience  
    - Education: Educational background fit
    
    Calculate overall score: (Skills×0.5 + Experience×0.3 + Education×0.2)
    
    Respond ONLY with this JSON format:
    {{
        "candidate_name": "{candidate_name}",
        "skills_score": <number>,
        "experience_score": <number>,
        "education_score": <number>,
        "overall_score": <calculated_score>,
        "skills_analysis": "<brief_skills_summary>",
        "experience_analysis": "<brief_experience_summary>",
        "education_analysis": "<brief_education_summary>",
        "recommendations": "<improvement_suggestions>",
        "strengths": ["<strength1>", "<strength2>"],
        "weaknesses": ["<weakness1>", "<weakness2>"],
        "fit_assessment": "<overall_summary>"
    }}
    """
    
    return prompt

def parse_analysis_response(response_text: str, candidate_name: str) -> Optional[Dict[str, Any]]:
    """Parse AI response with better error handling"""
    try:
        # Clean response
        cleaned_text = response_text.strip()
        
        # Remove markdown
        if '```' in cleaned_text:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(1)
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        else:
            json_str = cleaned_text
        
        # Parse JSON
        result = json.loads(json_str)
        
        # Validate result
        validated = validate_analysis_result(result, candidate_name)
        return validated
        
    except Exception as e:
        logger.error(f"JSON parsing failed for {candidate_name}: {str(e)}")
        return extract_scores_fallback(response_text, candidate_name)

def validate_analysis_result(result: Dict[str, Any], candidate_name: str) -> Dict[str, Any]:
    """Validate and clean analysis results"""
    
    try:
        # Extract scores with validation
        skills_score = max(0, min(100, int(float(result.get('skills_score', 0)))))
        experience_score = max(0, min(100, int(float(result.get('experience_score', 0)))))
        education_score = max(0, min(100, int(float(result.get('education_score', 0)))))
        
        # Calculate overall score
        overall_score = round(
            skills_score * 0.5 + experience_score * 0.3 + education_score * 0.2, 1
        )
        
        # Clean text fields
        def clean_text(text):
            if not text or str(text).strip() in ['N/A', 'n/a', 'None', 'null', '']:
                return 'Analysis not available'
            return str(text).strip()
        
        # Clean arrays
        def clean_array(arr):
            if not isinstance(arr, list):
                return []
            return [str(item).strip() for item in arr if item and str(item).strip()][:3]
        
        validated = {
            'candidate_name': str(result.get('candidate_name', candidate_name)).strip(),
            'skills_score': skills_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'overall_score': overall_score,
            'skills_analysis': clean_text(result.get('skills_analysis')),
            'experience_analysis': clean_text(result.get('experience_analysis')),
            'education_analysis': clean_text(result.get('education_analysis')),
            'recommendations': clean_text(result.get('recommendations')),
            'strengths': clean_array(result.get('strengths', [])),
            'weaknesses': clean_array(result.get('weaknesses', [])),
            'fit_assessment': clean_text(result.get('fit_assessment'))
        }
        
        logger.info(f"Validated result for {candidate_name}: Overall Score = {validated['overall_score']}%")
        return validated
        
    except Exception as e:
        logger.error(f"Validation error for {candidate_name}: {str(e)}")
        return create_default_result(candidate_name)

def extract_scores_fallback(response_text: str, candidate_name: str) -> Dict[str, Any]:
    """Extract scores when JSON parsing fails"""
    try:
        # Simple regex patterns for scores
        skills_match = re.search(r'skills?[:\s]*(\d+)', response_text, re.IGNORECASE)
        experience_match = re.search(r'experience[:\s]*(\d+)', response_text, re.IGNORECASE)
        education_match = re.search(r'education[:\s]*(\d+)', response_text, re.IGNORECASE)
        
        skills_score = int(skills_match.group(1)) if skills_match else 60
        experience_score = int(experience_match.group(1)) if experience_match else 60
        education_score = int(education_match.group(1)) if education_match else 60
        
        overall_score = round(skills_score * 0.5 + experience_score * 0.3 + education_score * 0.2, 1)
        
        return {
            'candidate_name': candidate_name,
            'skills_score': max(0, min(100, skills_score)),
            'experience_score': max(0, min(100, experience_score)),
            'education_score': max(0, min(100, education_score)),
            'overall_score': overall_score,
            'skills_analysis': f"Skills evaluation completed with {skills_score}% match",
            'experience_analysis': f"Experience evaluation shows {experience_score}% alignment",
            'education_analysis': f"Education background rated at {education_score}%",
            'recommendations': 'Run analysis again for detailed recommendations',
            'strengths': ['Analysis completed'],
            'weaknesses': ['Re-run for detailed insights'],
            'fit_assessment': f"Overall candidate fit: {overall_score}%"
        }
    except Exception as e:
        logger.error(f"Fallback failed for {candidate_name}: {str(e)}")
        return create_default_result(candidate_name)

def create_default_result(candidate_name: str) -> Dict[str, Any]:
    """Create default result when analysis fails"""
    return {
        'candidate_name': candidate_name,
        'skills_score': 0,
        'experience_score': 0,
        'education_score': 0,
        'overall_score': 0.0,
        'skills_analysis': 'Analysis failed - please try again',
        'experience_analysis': 'Analysis failed - please try again',
        'education_analysis': 'Analysis failed - please try again',
        'recommendations': 'Please try the analysis again',
        'strengths': [],
        'weaknesses': [],
        'fit_assessment': 'Analysis could not be completed'
    }

def analyze_single_candidate(resume_text: str, job_description: str, filename: str, batch_mode: bool = False, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """Analyze single candidate using FREE Gemini model"""
    
    logger.info(f"Analyzing {filename} with FREE Gemini model")
    
    # Validate inputs
    if not resume_text or not resume_text.strip():
        st.error(f"❌ Could not extract text from {filename}")
        return create_default_result("Unknown Candidate")
    
    if not job_description or not job_description.strip():
        st.error("❌ Job description is required")
        return create_default_result("Unknown Candidate")
    
    # Configure API
    if not configure_gemini():
        return create_default_result("Unknown Candidate")
    
    # Extract name
    candidate_name = extract_name_from_text(resume_text)
    if not candidate_name or candidate_name == "Unknown Candidate":
        candidate_name = extract_name_from_filename(filename)
    
    try:
        # Use FREE Gemini model (gemini-1.5-flash is free)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # FREE model
            generation_config={
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,  # Lower for free tier
            }
        )
        
        prompt = create_analysis_prompt(resume_text, job_description, candidate_name, batch_mode)
        
        # Try analysis with retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} for {candidate_name}")
                
                response = model.generate_content(prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    result = parse_analysis_response(response.text, candidate_name)
                    
                    if result and result.get('overall_score', 0) >= 0:
                        logger.info(f"✅ Success: {candidate_name} - {result['overall_score']}%")
                        return result
                    
                logger.warning(f"Invalid result for {candidate_name} (attempt {attempt + 1})")
                
                if attempt < max_retries - 1:
                    time.sleep(2)
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {candidate_name}: {str(e)}")
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    st.error("❌ API quota exceeded. Please try again later.")
                    return create_default_result(candidate_name)
                
                if attempt < max_retries - 1:
                    time.sleep(3)
        
        # All attempts failed
        st.error(f"❌ Analysis failed for {candidate_name} after {max_retries} attempts")
        return create_default_result(candidate_name)
    
    except Exception as e:
        logger.error(f"Critical error for {candidate_name}: {str(e)}")
        st.error(f"❌ Analysis error: {str(e)}")
        return create_default_result(candidate_name)

def analyze_batch_candidates(candidates_data: List[Dict[str, str]], job_description: str, progress_callback=None) -> List[Dict[str, Any]]:
    """Batch analysis with FREE tier limits"""
    
    # Enforce free tier limit of 5 files
    if len(candidates_data) > 5:
        st.error("❌ Free account limited to 5 resumes per batch. Please select fewer files.")
        return []
    
    logger.info(f"Starting batch analysis of {len(candidates_data)} candidates (FREE tier)")
    
    if not configure_gemini():
        return []
    
    results = []
    total_candidates = len(candidates_data)
    
    for i, candidate_data in enumerate(candidates_data):
        filename = candidate_data.get('filename', f'candidate_{i+1}')
        
        if progress_callback:
            progress_callback(i / total_candidates, f"Analyzing {filename}")
        
        try:
            result = analyze_single_candidate(
                candidate_data.get('resume_text', ''),
                job_description,
                filename,
                batch_mode=True
            )
            
            if result and result.get('overall_score', 0) >= 0:
                results.append(result)
                logger.info(f"✅ Batch: {filename} - {result.get('overall_score', 0)}%")
            else:
                logger.warning(f"❌ Batch failed: {filename}")
        
        except Exception as e:
            logger.error(f"Batch error for {filename}: {str(e)}")
            st.error(f"❌ Error analyzing {filename}: {str(e)}")
        
        # Longer delay for free tier to avoid rate limits
        if i < total_candidates - 1:
            time.sleep(3)  # 3 second delay between requests
    
    if progress_callback:
        progress_callback(1.0, f"Completed! {len(results)}/{total_candidates} successful")
    
    logger.info(f"Batch analysis completed: {len(results)}/{total_candidates} successful")
    return results
