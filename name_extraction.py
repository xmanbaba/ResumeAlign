import google.generativeai as genai
import streamlit as st
import logging
import time
import json
import re
from typing import Dict, Any, Optional, List

# SIMPLIFIED IMPORT - Test if this works
try:
    from name_extraction import extract_name_from_text, extract_name_from_filename
    logger = logging.getLogger(__name__)
    logger.info("Successfully imported name extraction functions")
except ImportError as e:
    st.error(f"Import error: {str(e)}")
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import name extraction functions: {str(e)}")
    # Fallback functions
    def extract_name_from_text(text):
        return "Unknown Candidate"
    def extract_name_from_filename(filename):
        return "Unknown Candidate"

# Configure logging
logging.basicConfig(level=logging.INFO)

def configure_gemini():
    """Configure Gemini API"""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Gemini API key not found in secrets.")
            return False
        
        genai.configure(api_key=api_key)
        logger.info("Successfully configured Gemini API")
        return True
        
    except Exception as e:
        logger.error(f"Gemini configuration error: {str(e)}")
        st.error(f"❌ Failed to configure Gemini API: {str(e)}")
        return False

def create_comprehensive_analysis_prompt(resume_text: str, job_description: str, candidate_name: str, batch_mode: bool = False) -> str:
    """Create a comprehensive analysis prompt with interview questions"""
    
    prompt = f"""
    You are an expert HR analyst. Analyze this resume against the job requirements and provide a comprehensive evaluation.

    CANDIDATE: {candidate_name}
    
    JOB DESCRIPTION:
    {job_description}
    
    RESUME TEXT:
    {resume_text}
    
    ANALYSIS REQUIREMENTS:
    1. Rate each category 0-100 based on job fit:
       - Skills: Match between candidate skills and job requirements
       - Experience: Relevance and depth of experience
       - Education: Educational background alignment
    
    2. Calculate overall score: (Skills × 0.5 + Experience × 0.3 + Education × 0.2)
    
    3. Provide detailed analysis for each category explaining the rating
    
    4. Generate 6-8 relevant interview questions based on:
       - Candidate's strengths and weaknesses
       - Job requirements
       - Areas that need clarification
       - Competency-based questions
    
    5. Create definitive, actionable recommendations (Strong Yes/Yes/Conditional Yes/Maybe/No)
    
    Respond ONLY with this JSON format (no markdown, no code blocks):
    {{
        "candidate_name": "{candidate_name}",
        "skills_score": <number 0-100>,
        "experience_score": <number 0-100>, 
        "education_score": <number 0-100>,
        "overall_score": <calculated score rounded to 1 decimal>,
        "skills_analysis": "<detailed analysis of skills match, specific examples>",
        "experience_analysis": "<detailed analysis of experience relevance and depth>",
        "education_analysis": "<detailed analysis of educational background>",
        "fit_assessment": "<comprehensive summary of overall candidate fit>",
        "strengths": ["<specific strength 1>", "<specific strength 2>", "<specific strength 3>"],
        "weaknesses": ["<area for improvement 1>", "<area for improvement 2>", "<area for improvement 3>"],
        "recommendations": "<definitive hiring recommendation: Strong Yes/Yes/Conditional Yes/Maybe/No with specific reasoning>",
        "interview_questions": [
            "<competency-based question 1>",
            "<situational question 2>", 
            "<technical/role-specific question 3>",
            "<behavioral question 4>",
            "<growth/development question 5>",
            "<culture fit question 6>",
            "<motivation question 7>",
            "<future goals question 8>"
        ]
    }}
    
    IMPORTANT: 
    - Be specific and detailed in your analysis
    - Make recommendations definitive (Strong Yes/Yes/Conditional Yes/Maybe/No)
    - Interview questions should be directly relevant to the candidate and role
    - Focus on actionable insights
    - Include exactly 6-8 interview questions
    """
    
    return prompt

def create_default_comprehensive_result(candidate_name: str) -> Dict[str, Any]:
    """Create default comprehensive result when analysis fails completely"""
    return {
        'candidate_name': candidate_name,
        'skills_score': 0,
        'experience_score': 0,
        'education_score': 0,
        'overall_score': 0.0,
        'skills_analysis': 'Analysis failed - please try again with a clearer resume format',
        'experience_analysis': 'Analysis failed - please try again with a clearer resume format',
        'education_analysis': 'Analysis failed - please try again with a clearer resume format',
        'fit_assessment': 'Analysis could not be completed - please retry the analysis',
        'recommendations': 'No - Please retry the analysis with a clearer resume format or different file',
        'strengths': ['Analysis pending', 'Retry recommended', 'Check resume format'],
        'weaknesses': ['Analysis incomplete', 'File processing issue', 'Retry needed'],
        'interview_questions': [
            "Please tell me about your professional background.",
            "What interests you about this role?",
            "Describe your relevant experience.",
            "What are your key strengths?",
            "How do you handle challenges?",
            "What are your career aspirations?",
            "Why do you want to join our team?",
            "Do you have any questions for us?"
        ]
    }

def analyze_single_candidate(resume_text: str, job_description: str, filename: str, batch_mode: bool = False, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """Analyze single candidate using Gemini 2.5 Flash model"""
    
    logger.info(f"Analyzing {filename} with Gemini 2.5 Flash")
    
    # Validate inputs
    if not resume_text or not resume_text.strip():
        error_msg = f"❌ Could not extract text from {filename}"
        logger.error(error_msg)
        st.error(error_msg)
        return create_default_comprehensive_result("Unknown Candidate")
    
    if not job_description or not job_description.strip():
        error_msg = "❌ Job description is required"
        logger.error(error_msg)
        st.error(error_msg)
        return create_default_comprehensive_result("Unknown Candidate")
    
    # Configure API
    if not configure_gemini():
        return create_default_comprehensive_result("Unknown Candidate")
    
    # Extract candidate name
    try:
        candidate_name = extract_name_from_text(resume_text)
        if not candidate_name or candidate_name == "Unknown Candidate":
            candidate_name = extract_name_from_filename(filename)
    except Exception as e:
        logger.warning(f"Name extraction failed: {str(e)}")
        candidate_name = "Unknown Candidate"
    
    logger.info(f"Extracted candidate name: {candidate_name}")
    
    try:
        # Use Gemini 2.5 Flash model
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-002",
            generation_config={
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        prompt = create_comprehensive_analysis_prompt(resume_text, job_description, candidate_name, batch_mode)
        
        # Simple single attempt for testing
        try:
            logger.info(f"Attempting analysis for {candidate_name}")
            st.info(f"🔄 Analyzing {candidate_name} with Gemini 2.5 Flash...")
            
            response = model.generate_content(prompt)
            
            if response and hasattr(response, 'text') and response.text:
                logger.info(f"Received response for {candidate_name}, length: {len(response.text)}")
                
                # Simple JSON parsing
                try:
                    # Clean response
                    response_text = response.text.strip()
                    if '```json' in response_text:
                        response_text = response_text.split('```json')[1].split('```')[0]
                    elif '```' in response_text:
                        response_text = response_text.split('```')[1].split('```')[0]
                    
                    # Try to find JSON
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        
                        # Basic validation
                        if result.get('overall_score', 0) >= 0:
                            logger.info(f"✅ Success: {candidate_name} - {result.get('overall_score', 0)}%")
                            st.success(f"✅ Analysis completed for {candidate_name} - {result.get('overall_score', 0)}% match")
                            return result
                
                except Exception as parse_error:
                    logger.error(f"JSON parsing failed: {str(parse_error)}")
                    st.error(f"❌ Analysis parsing failed: {str(parse_error)}")
            
        except Exception as api_error:
            logger.error(f"API call failed: {str(api_error)}")
            st.error(f"❌ API call failed: {str(api_error)}")
        
        # If we get here, analysis failed
        st.error(f"❌ Analysis failed for {candidate_name}")
        return create_default_comprehensive_result(candidate_name)
    
    except Exception as e:
        logger.error(f"Critical error for {candidate_name}: {str(e)}")
        st.error(f"❌ Analysis error: {str(e)}")
        return create_default_comprehensive_result(candidate_name)

def analyze_batch_candidates(candidates_data: List[Dict[str, str]], job_description: str, progress_callback=None) -> List[Dict[str, Any]]:
    """Batch analysis with improved error handling"""
    
    # Enforce batch limit
    if len(candidates_data) > 5:
        st.error("❌ Maximum 5 resumes per batch. Please select fewer files.")
        return []
    
    logger.info(f"Starting batch analysis of {len(candidates_data)} candidates")
    
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
        
        # Rate limiting
        if i < total_candidates - 1:
            time.sleep(4)
    
    if progress_callback:
        progress_callback(1.0, f"Completed! {len(results)}/{total_candidates} successful")
    
    logger.info(f"Batch analysis completed: {len(results)}/{total_candidates} successful")
    return results

def create_excel_report(results):
    """Create Excel report with error handling"""
    try:
        import pandas as pd
        import io
        
        data = []
        for result in results:
            interview_questions = result.get('interview_questions', [])
            questions_text = '\n'.join([f"{i+1}. {q}" for i, q in enumerate(interview_questions)])
            
            data.append({
                'Candidate Name': result.get('candidate_name', 'Unknown'),
                'Overall Score': result.get('overall_score', 0),
                'Skills Score': result.get('skills_score', 0),
                'Experience Score': result.get('experience_score', 0),
                'Education Score': result.get('education_score', 0),
                'Skills Analysis': result.get('skills_analysis', ''),
                'Experience Analysis': result.get('experience_analysis', ''),
                'Education Analysis': result.get('education_analysis', ''),
                'Fit Assessment': result.get('fit_assessment', ''),
                'Recommendations': result.get('recommendations', ''),
                'Strengths': '; '.join(result.get('strengths', [])),
                'Areas for Improvement': '; '.join(result.get('weaknesses', [])),
                'Interview Questions': questions_text
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Analysis Results', index=False)
        
        return output.getvalue()
    except Exception as e:
        logger.error(f"Excel generation error: {str(e)}")
        return None

def create_json_report(results):
    """Create JSON report"""
    try:
        import json
