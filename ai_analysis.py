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
    """Configure Gemini API with enhanced error handling"""
    try:
        # Try multiple ways to get the API key
        api_key = None
        
        # Method 1: From Streamlit secrets
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
            if api_key:
                logger.info("API key found in Streamlit secrets")
        except Exception as e:
            logger.warning(f"Could not access Streamlit secrets: {e}")
        
        # Method 2: From environment variables
        if not api_key:
            import os
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                logger.info("API key found in environment variables")
        
        # Method 3: From Streamlit secrets with different key names
        if not api_key:
            try:
                api_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("gemini_api_key")
                if api_key:
                    logger.info("API key found with alternative key name")
            except:
                pass
        
        if not api_key:
            error_msg = """
            ❌ Gemini API key not found. Please add your API key to Streamlit secrets.
            
            **To fix this:**
            1. Get your API key from Google AI Studio: https://aistudio.google.com/app/apikey
            2. Add it to your Streamlit secrets as 'GEMINI_API_KEY'
            3. Or set it as an environment variable: GEMINI_API_KEY=your_key_here
            """
            st.error(error_msg)
            return False
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Test the connection
        try:
            models = list(genai.list_models())
            logger.info(f"Successfully connected to Gemini. Available models: {len(models)}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Gemini API: {e}")
            st.error(f"❌ Failed to connect to Gemini API. Please check your API key: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Gemini configuration error: {str(e)}")
        st.error(f"❌ Failed to configure Gemini API: {str(e)}")
        return False

def create_analysis_prompt(resume_text: str, job_description: str, candidate_name: str, batch_mode: bool = False) -> str:
    """Create a detailed analysis prompt with consistency measures"""
    
    consistency_note = """
    CONSISTENCY REQUIREMENTS FOR BATCH ANALYSIS:
    - Use identical evaluation criteria across all candidates
    - Be objective and consistent in scoring methodology
    - Focus on measurable skills and experience alignment
    - Apply the same scoring rubric for all analyses
    """ if batch_mode else ""
    
    prompt = f"""
    You are an expert HR analyst and technical recruiter. Analyze this resume against the job requirements with precision and consistency.
    
    {consistency_note}
    
    CANDIDATE: {candidate_name}
    
    JOB REQUIREMENTS:
    {job_description}
    
    CANDIDATE'S RESUME:
    {resume_text}
    
    ANALYSIS INSTRUCTIONS:
    
    1. SKILLS EVALUATION (0-100%):
       - Identify required technical and soft skills from job description
       - Match candidate's skills with requirements
       - Consider skill depth/proficiency level
       - Account for transferable skills
    
    2. EXPERIENCE EVALUATION (0-100%):
       - Compare years of experience with requirements
       - Evaluate relevance of previous roles
       - Assess industry background alignment
       - Consider leadership/project experience
    
    3. EDUCATION EVALUATION (0-100%):
       - Match educational background with requirements
       - Consider relevant certifications
       - Evaluate continuous learning efforts
       - Account for degree relevance
    
    4. OVERALL SCORE CALCULATION:
       - Skills: 50% weight
       - Experience: 30% weight  
       - Education: 20% weight
       - Calculate: (Skills×0.5 + Experience×0.3 + Education×0.2)
    
    SCORING GUIDELINES:
    - 90-100%: Exceptional match - Significantly exceeds requirements
    - 80-89%: Strong match - Meets requirements with additional value
    - 70-79%: Good match - Solid alignment with core requirements  
    - 60-69%: Moderate match - Meets basic requirements
    - 40-59%: Fair match - Some alignment but gaps exist
    - 20-39%: Poor match - Major misalignment
    - 0-19%: Very poor match - Little to no alignment
    
    CRITICAL: Respond ONLY with valid JSON. No additional text, explanations, or markdown formatting.
    
    JSON FORMAT:
    {{
        "candidate_name": "{candidate_name}",
        "skills_score": <integer_0_to_100>,
        "experience_score": <integer_0_to_100>,
        "education_score": <integer_0_to_100>,
        "overall_score": <calculated_weighted_average_rounded_to_1_decimal>,
        "skills_analysis": "<detailed_skills_evaluation_2_3_sentences>",
        "experience_analysis": "<detailed_experience_evaluation_2_3_sentences>",
        "education_analysis": "<detailed_education_evaluation_2_3_sentences>",
        "recommendations": "<specific_improvement_suggestions>",
        "strengths": ["<strength1>", "<strength2>", "<strength3>"],
        "weaknesses": ["<weakness1>", "<weakness2>", "<weakness3>"],
        "fit_assessment": "<overall_fit_summary_2_3_sentences>"
    }}
    """
    
    return prompt

def parse_analysis_response(response_text: str, candidate_name: str) -> Optional[Dict[str, Any]]:
    """Parse and validate AI response with comprehensive error handling"""
    try:
        logger.info(f"Parsing response for {candidate_name} - Length: {len(response_text)}")
        
        # Clean the response text
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks
        if '```' in cleaned_text:
            # Extract content between code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(1)
            else:
                # Remove code block markers
                cleaned_text = re.sub(r'```(?:json)?\s*', '', cleaned_text)
                cleaned_text = re.sub(r'\s*```', '', cleaned_text)
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        else:
            json_str = cleaned_text
        
        # Parse JSON
        result = json.loads(json_str)
        logger.info(f"Successfully parsed JSON for {candidate_name}")
        
        # Validate and clean the result
        validated_result = validate_analysis_result(result, candidate_name)
        return validated_result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error for {candidate_name}: {str(e)}")
        logger.error(f"Response text: {response_text[:500]}...")
        
        # Try fallback extraction
        return extract_scores_fallback(response_text, candidate_name)
    
    except Exception as e:
        logger.error(f"Response parsing error for {candidate_name}: {str(e)}")
        return extract_scores_fallback(response_text, candidate_name)

def validate_analysis_result(result: Dict[str, Any], candidate_name: str) -> Dict[str, Any]:
    """Validate and clean analysis results with proper defaults"""
    
    # Extract and validate scores
    skills_score = max(0, min(100, int(float(result.get('skills_score', 0)))))
    experience_score = max(0, min(100, int(float(result.get('experience_score', 0)))))
    education_score = max(0, min(100, int(float(result.get('education_score', 0)))))
    
    # Calculate overall score with proper weighting
    calculated_overall = (
        skills_score * 0.5 +
        experience_score * 0.3 +
        education_score * 0.2
    )
    
    # Clean text fields
    def clean_text(text):
        if not text or text in ['N/A', 'n/a', 'None', 'null']:
            return 'Analysis not available'
        return str(text).strip()
    
    # Clean arrays
    def clean_array(arr):
        if not isinstance(arr, list):
            return []
        return [str(item).strip() for item in arr if item and str(item).strip()]
    
    validated = {
        'candidate_name': str(result.get('candidate_name', candidate_name)).strip(),
        'skills_score': skills_score,
        'experience_score': experience_score,
        'education_score': education_score,
        'overall_score': round(calculated_overall, 1),
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

def extract_scores_fallback(response_text: str, candidate_name: str) -> Dict[str, Any]:
    """Fallback method to extract scores when JSON parsing fails"""
    try:
        logger.warning(f"Using fallback score extraction for {candidate_name}")
        
        # Try to extract numeric scores using regex patterns
        patterns = {
            'skills': r'(?:skill|technical)(?:\s+(?:score|match|rating))?[:\s]*(\d+)(?:%|\s|$)',
            'experience': r'experience(?:\s+(?:score|match|rating))?[:\s]*(\d+)(?:%|\s|$)',
            'education': r'education(?:\s+(?:score|match|rating))?[:\s]*(\d+)(?:%|\s|$)',
            'overall': r'overall(?:\s+(?:score|match|rating))?[:\s]*(\d+)(?:%|\s|$)'
        }
        
        scores = {}
        for category, pattern in patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                scores[category] = max(0, min(100, score))
            else:
                scores[category] = 50  # Default middle score
        
        # Calculate overall if not found
        if 'overall' not in scores or scores['overall'] == 50:
            scores['overall'] = round(
                scores['skills'] * 0.5 + 
                scores['experience'] * 0.3 + 
                scores['education'] * 0.2, 1
            )
        
        # Try to extract some analysis text
        analysis_text = response_text[:200] + "..." if len(response_text) > 200 else response_text
        
        fallback_result = {
            'candidate_name': candidate_name,
            'skills_score': scores['skills'],
            'experience_score': scores['experience'],
            'education_score': scores['education'],
            'overall_score': scores['overall'],
            'skills_analysis': f"Skills evaluation completed. Score: {scores['skills']}%",
            'experience_analysis': f"Experience evaluation completed. Score: {scores['experience']}%",
            'education_analysis': f"Education evaluation completed. Score: {scores['education']}%",
            'recommendations': 'Please re-run analysis for detailed recommendations',
            'strengths': [],
            'weaknesses': [],
            'fit_assessment': f"Overall assessment score: {scores['overall']}%"
        }
        
        logger.info(f"Fallback extraction successful for {candidate_name}")
        return fallback_result
    
    except Exception as e:
        logger.error(f"Fallback extraction failed for {candidate_name}: {str(e)}")
        return create_default_result(candidate_name)

def create_default_result(candidate_name: str) -> Dict[str, Any]:
    """Create a default result when all parsing fails"""
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

def analyze_single_candidate(resume_text: str, job_description: str, filename: str, batch_mode: bool = False, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Analyze a single candidate with improved error handling and consistency"""
    
    logger.info(f"Starting analysis for {filename} (batch_mode: {batch_mode})")
    
    # Validate inputs
    if not resume_text or not resume_text.strip():
        logger.error(f"Empty resume text for {filename}")
        return create_default_result("Unknown Candidate")
    
    if not job_description or not job_description.strip():
        logger.error(f"Empty job description for {filename}")
        return create_default_result("Unknown Candidate")
    
    # Configure Gemini API
    if not configure_gemini():
        logger.error("Failed to configure Gemini API")
        return create_default_result("Unknown Candidate")
    
    # Extract candidate name
    candidate_name = extract_name_from_text(resume_text)
    if not candidate_name or candidate_name == "Unknown Candidate":
        candidate_name = extract_name_from_filename(filename)
    
    logger.info(f"Analyzing candidate: {candidate_name}")
    
    # Configure model with appropriate settings
    generation_config = {
        "temperature": 0.1 if batch_mode else 0.2,  # Lower for consistency
        "top_p": 0.8,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config=generation_config
        )
        
        # Create analysis prompt
        prompt = create_analysis_prompt(resume_text, job_description, candidate_name, batch_mode)
        
        # Attempt analysis with retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Analysis attempt {attempt + 1} for {candidate_name}")
                
                # Generate response
                response = model.generate_content(prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    logger.info(f"Received response for {candidate_name} - Length: {len(response.text)}")
                    
                    # Parse the response
                    result = parse_analysis_response(response.text, candidate_name)
                    
                    if result and result.get('overall_score', 0) > 0:
                        logger.info(f"Successfully analyzed {candidate_name} - Score: {result['overall_score']}%")
                        return result
                    else:
                        logger.warning(f"Invalid result for {candidate_name} (attempt {attempt + 1})")
                
                else:
                    logger.warning(f"Empty or invalid response for {candidate_name} (attempt {attempt + 1})")
                
                # Wait before retry
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            
            except Exception as e:
                logger.error(f"Analysis error for {candidate_name} (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {candidate_name}")
        
        # If all retries failed, return default result
        logger.error(f"Analysis completely failed for {candidate_name} after {max_retries} attempts")
        return create_default_result(candidate_name)
    
    except Exception as e:
        logger.error(f"Critical error during analysis setup for {candidate_name}: {str(e)}")
        return create_default_result(candidate_name)

def analyze_batch_candidates(candidates_data: List[Dict[str, str]], job_description: str, progress_callback=None) -> List[Dict[str, Any]]:
    """Analyze multiple candidates with improved consistency and error handling"""
    
    logger.info(f"Starting batch analysis of {len(candidates_data)} candidates")
    
    if not configure_gemini():
        logger.error("Failed to configure Gemini for batch analysis")
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
                batch_mode=True  # Enable batch mode for consistency
            )
            
            if result and result.get('overall_score', 0) >= 0:  # Accept even 0 scores
                results.append(result)
                logger.info(f"Batch analysis success: {filename} - Score: {result.get('overall_score', 0)}%")
            else:
                logger.warning(f"Batch analysis failed for {filename}")
        
        except Exception as e:
            logger.error(f"Error in batch analysis for {filename}: {str(e)}")
        
        # Rate limiting for API calls
        if i < total_candidates - 1:  # Don't delay after the last candidate
            time.sleep(1.5)  # Slightly longer delay for batch processing
    
    if progress_callback:
        progress_callback(1.0, f"Analysis complete! Processed {len(results)} candidates")
    
    logger.info(f"Batch analysis completed: {len(results)}/{total_candidates} successful")
    return results

def get_candidate_summary(result: Dict[str, Any]) -> str:
    """Generate a brief summary of the candidate analysis"""
    name = result.get('candidate_name', 'Unknown')
    overall_score = result.get('overall_score', 0)
    
    if overall_score >= 80:
        rating = "Excellent"
        emoji = "🌟"
    elif overall_score >= 60:
        rating = "Good"
        emoji = "⭐"
    elif overall_score >= 40:
        rating = "Fair"
        emoji = "📋"
    else:
        rating = "Poor"
        emoji = "❌"
    
    top_strengths = result.get('strengths', [])[:2]
    strengths_text = ", ".join(top_strengths) if top_strengths else "No specific strengths identified"
    
    return f"{emoji} {name}: {overall_score}% ({rating} match) - Key strengths: {strengths_text}"

def validate_gemini_connection() -> bool:
    """Test Gemini API connection"""
    try:
        if not configure_gemini():
            return False
        
        # Try a simple test request
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content("Say 'API connection successful'")
        
        if response and hasattr(response, 'text'):
            logger.info("Gemini API connection test successful")
            return True
        else:
            logger.error("Gemini API connection test failed - no response")
            return False
    
    except Exception as e:
        logger.error(f"Gemini API connection test failed: {str(e)}")
        return False

def get_analysis_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate statistics from analysis results"""
    if not results:
        return {}
    
    scores = [r.get('overall_score', 0) for r in results]
    
    stats = {
        'total_candidates': len(results),
        'average_score': sum(scores) / len(scores) if scores else 0,
        'highest_score': max(scores) if scores else 0,
        'lowest_score': min(scores) if scores else 0,
        'excellent_candidates': len([s for s in scores if s >= 80]),
        'good_candidates': len([s for s in scores if 60 <= s < 80]),
        'fair_candidates': len([s for s in scores if 40 <= s < 60]),
        'poor_candidates': len([s for s in scores if s < 40])
    }
    
    return stats

def create_batch_summary(results: List[Dict[str, Any]]) -> str:
    """Create a summary of batch analysis results"""
    if not results:
        return "No candidates were successfully analyzed."
    
    stats = get_analysis_statistics(results)
    
    summary = f"""
    📊 **Batch Analysis Summary**
    
    **Total Candidates Analyzed:** {stats['total_candidates']}
    **Average Score:** {stats['average_score']:.1f}%
    **Score Range:** {stats['lowest_score']}% - {stats['highest_score']}%
    
    **Score Distribution:**
    - 🌟 Excellent (80-100%): {stats['excellent_candidates']} candidates
    - ⭐ Good (60-79%): {stats['good_candidates']} candidates  
    - 📋 Fair (40-59%): {stats['fair_candidates']} candidates
    - ❌ Poor (0-39%): {stats['poor_candidates']} candidates
    """
    
    return summary
