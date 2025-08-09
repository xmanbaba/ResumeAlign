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
    """Configure Gemini API with error handling"""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Gemini API key not found in secrets. Please add GEMINI_API_KEY to your secrets.")
            return False
        
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        logger.error(f"Gemini configuration error: {str(e)}")
        st.error(f"❌ Failed to configure Gemini API: {str(e)}")
        return False

def create_analysis_prompt(resume_text: str, job_description: str, candidate_name: str, batch_mode: bool = False) -> str:
    """Create a detailed analysis prompt with consistency measures"""
    
    # Use more deterministic temperature for batch processing
    consistency_note = """
    CONSISTENCY REQUIREMENTS:
    - Use the same evaluation criteria for all candidates
    - Base scores on objective skill matching, not subjective impressions
    - Be consistent with scoring rubrics across all analyses
    - Focus on quantifiable experience and concrete skills
    """ if batch_mode else ""
    
    prompt = f"""
    {consistency_note}
    
    As an expert HR analyst and technical recruiter, analyze this resume against the job requirements.
    
    CANDIDATE: {candidate_name}
    
    JOB DESCRIPTION:
    {job_description}
    
    RESUME CONTENT:
    {resume_text}
    
    ANALYSIS REQUIREMENTS:
    1. Evaluate skills match (0-100%): Compare candidate's technical and soft skills with job requirements
    2. Evaluate experience (0-100%): Assess years of experience, relevant roles, and industry background  
    3. Evaluate education (0-100%): Review educational background, certifications, and continuous learning
    4. Calculate overall score: Weighted average (Skills: 50%, Experience: 30%, Education: 20%)
    
    SCORING GUIDELINES:
    - 90-100%: Exceptional match, exceeds requirements significantly
    - 80-89%: Strong match, meets most requirements with some extras
    - 70-79%: Good match, meets core requirements
    - 60-69%: Moderate match, meets some requirements, has potential
    - 50-59%: Fair match, limited alignment with requirements
    - Below 50%: Poor match, major gaps in requirements
    
    Return your analysis in this EXACT JSON format (no markdown formatting):
    {{
        "candidate_name": "{candidate_name}",
        "skills_score": <number>,
        "experience_score": <number>, 
        "education_score": <number>,
        "overall_score": <calculated_weighted_average>,
        "skills_analysis": "<detailed_skills_analysis>",
        "experience_analysis": "<detailed_experience_analysis>", 
        "education_analysis": "<detailed_education_analysis>",
        "recommendations": "<improvement_suggestions>",
        "strengths": ["<strength1>", "<strength2>", "<strength3>"],
        "weaknesses": ["<weakness1>", "<weakness2>", "<weakness3>"],
        "fit_assessment": "<overall_fit_summary>"
    }}
    """
    
    return prompt

def parse_analysis_response(response_text: str, candidate_name: str) -> Optional[Dict[str, Any]]:
    """Parse and validate the AI response with enhanced error handling"""
    try:
        # Clean the response text
        cleaned_text = response_text.strip()
        
        # Remove any markdown code block formatting
        if cleaned_text.startswith('```'):
            cleaned_text = re.sub(r'^```(?:json)?\s*', '', cleaned_text)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        else:
            json_str = cleaned_text
        
        # Parse JSON
        result = json.loads(json_str)
        
        # Validate and clean the result
        validated_result = validate_analysis_result(result, candidate_name)
        return validated_result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        logger.error(f"Response text: {response_text}")
        
        # Try to extract scores manually as fallback
        return extract_scores_fallback(response_text, candidate_name)
    
    except Exception as e:
        logger.error(f"Response parsing error: {str(e)}")
        return None

def validate_analysis_result(result: Dict[str, Any], candidate_name: str) -> Dict[str, Any]:
    """Validate and clean analysis results"""
    
    # Ensure all required fields exist with defaults
    validated = {
        'candidate_name': result.get('candidate_name', candidate_name),
        'skills_score': max(0, min(100, int(result.get('skills_score', 0)))),
        'experience_score': max(0, min(100, int(result.get('experience_score', 0)))),
        'education_score': max(0, min(100, int(result.get('education_score', 0)))),
        'skills_analysis': result.get('skills_analysis', 'Analysis not available'),
        'experience_analysis': result.get('experience_analysis', 'Analysis not available'),
        'education_analysis': result.get('education_analysis', 'Analysis not available'),
        'recommendations': result.get('recommendations', 'No specific recommendations'),
        'strengths': result.get('strengths', []) if isinstance(result.get('strengths'), list) else [],
        'weaknesses': result.get('weaknesses', []) if isinstance(result.get('weaknesses'), list) else [],
        'fit_assessment': result.get('fit_assessment', 'Assessment not available')
    }
    
    # Calculate overall score with consistent weighting
    skills_weight = 0.5
    experience_weight = 0.3
    education_weight = 0.2
    
    calculated_overall = (
        validated['skills_score'] * skills_weight +
        validated['experience_score'] * experience_weight +
        validated['education_score'] * education_weight
    )
    
    validated['overall_score'] = round(calculated_overall, 1)
    
    return validated

def extract_scores_fallback(response_text: str, candidate_name: str) -> Dict[str, Any]:
    """Fallback method to extract scores when JSON parsing fails"""
    try:
        # Try to extract numeric scores using regex
        skills_match = re.search(r'skills?\s*(?:score|match)?[:\s]*(\d+)', response_text, re.IGNORECASE)
        experience_match = re.search(r'experience?\s*(?:score|match)?[:\s]*(\d+)', response_text, re.IGNORECASE)
        education_match = re.search(r'education?\s*(?:score|match)?[:\s]*(\d+)', response_text, re.IGNORECASE)
        overall_match = re.search(r'overall?\s*(?:score|match)?[:\s]*(\d+)', response_text, re.IGNORECASE)
        
        skills_score = int(skills_match.group(1)) if skills_match else 50
        experience_score = int(experience_match.group(1)) if experience_match else 50
        education_score = int(education_match.group(1)) if education_match else 50
        overall_score = int(overall_match.group(1)) if overall_match else round((skills_score * 0.5 + experience_score * 0.3 + education_score * 0.2), 1)
        
        return {
            'candidate_name': candidate_name,
            'skills_score': max(0, min(100, skills_score)),
            'experience_score': max(0, min(100, experience_score)),
            'education_score': max(0, min(100, education_score)),
            'overall_score': max(0, min(100, overall_score)),
            'skills_analysis': 'Detailed analysis not available due to parsing error',
            'experience_analysis': 'Detailed analysis not available due to parsing error',
            'education_analysis': 'Detailed analysis not available due to parsing error',
            'recommendations': 'Please try the analysis again for detailed recommendations',
            'strengths': [],
            'weaknesses': [],
            'fit_assessment': 'Assessment not available due to parsing error'
        }
    
    except Exception as e:
        logger.error(f"Fallback parsing error: {str(e)}")
        return None

def analyze_single_candidate(resume_text: str, job_description: str, filename: str, batch_mode: bool = False, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Analyze a single candidate with improved consistency and error handling"""
    
    if not configure_gemini():
        return None
    
    if not resume_text or not job_description:
        logger.error("Missing resume text or job description")
        return None
    
    # Extract candidate name with multiple strategies
    candidate_name = extract_name_from_text(resume_text)
    if not candidate_name or candidate_name == "Unknown Candidate":
        candidate_name = extract_name_from_filename(filename)
    
    # Create the model with consistent settings
    generation_config = {
        "temperature": 0.1 if batch_mode else 0.2,  # Lower temperature for batch consistency
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-pro",
        generation_config=generation_config
    )
    
    # Create analysis prompt
    prompt = create_analysis_prompt(resume_text, job_description, candidate_name, batch_mode)
    
    # Attempt analysis with retries
    for attempt in range(max_retries):
        try:
            logger.info(f"Analyzing candidate: {candidate_name} (attempt {attempt + 1})")
            
            # Generate response
            response = model.generate_content(prompt)
            
            if response and response.text:
                # Parse the response
                result = parse_analysis_response(response.text, candidate_name)
                
                if result:
                    logger.info(f"Successfully analyzed candidate: {candidate_name}")
                    return result
                else:
                    logger.warning(f"Failed to parse response for {candidate_name} (attempt {attempt + 1})")
            
            else:
                logger.warning(f"Empty response for {candidate_name} (attempt {attempt + 1})")
            
            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(1)
        
        except Exception as e:
            logger.error(f"Analysis error for {candidate_name} (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
    
    # If all retries failed, return a basic result
    logger.error(f"All analysis attempts failed for {candidate_name}")
    return {
        'candidate_name': candidate_name,
        'skills_score': 0,
        'experience_score': 0,
        'education_score': 0,
        'overall_score': 0,
        'skills_analysis': 'Analysis failed - please try again',
        'experience_analysis': 'Analysis failed - please try again',
        'education_analysis': 'Analysis failed - please try again',
        'recommendations': 'Please try the analysis again',
        'strengths': [],
        'weaknesses': [],
        'fit_assessment': 'Analysis failed'
    }

def analyze_batch_candidates(candidates_data: List[Dict[str, str]], job_description: str, progress_callback=None) -> List[Dict[str, Any]]:
    """Analyze multiple candidates with improved consistency"""
    
    if not configure_gemini():
        return []
    
    results = []
    total_candidates = len(candidates_data)
    
    for i, candidate_data in enumerate(candidates_data):
        if progress_callback:
            progress_callback(i / total_candidates, f"Analyzing {candidate_data.get('filename', 'Unknown')}")
        
        result = analyze_single_candidate(
            candidate_data['resume_text'],
            job_description,
            candidate_data['filename'],
            batch_mode=True  # Enable batch mode for consistency
        )
        
        if result:
            results.append(result)
        
        # Rate limiting for API calls
        if i < total_candidates - 1:  # Don't delay after the last candidate
            time.sleep(1)  # Adjust delay as needed
    
    if progress_callback:
        progress_callback(1.0, "Analysis complete!")
    
    return results

def get_candidate_summary(result: Dict[str, Any]) -> str:
    """Generate a brief summary of the candidate analysis"""
    name = result.get('candidate_name', 'Unknown')
    overall_score = result.get('overall_score', 0)
    
    if overall_score >= 80:
        rating = "Excellent"
    elif overall_score >= 60:
        rating = "Good"
    elif overall_score >= 40:
        rating = "Fair"
    else:
        rating = "Poor"
    
    top_strengths = result.get('strengths', [])[:2]
    strengths_text = ", ".join(top_strengths) if top_strengths else "No specific strengths identified"
    
    return f"{name}: {overall_score}% ({rating} match) - Key strengths: {strengths_text}"
