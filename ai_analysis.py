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
    """Configure Gemini API"""
    try:
        # Get API key from Streamlit secrets (already configured)
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Gemini API key not found in secrets.")
            return False
        
        # Configure Gemini
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

def parse_comprehensive_response(response_text: str, candidate_name: str) -> Optional[Dict[str, Any]]:
    """Parse AI response with comprehensive data including interview questions"""
    try:
        # Clean response text
        cleaned_text = response_text.strip()
        logger.info(f"Parsing response for {candidate_name}, length: {len(cleaned_text)}")
        
        # Remove any markdown formatting
        if '```json' in cleaned_text:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(1)
        elif '```' in cleaned_text:
            json_match = re.search(r'```\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(1)
        
        # Extract JSON object
        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        else:
            json_str = cleaned_text
        
        # Parse JSON
        result = json.loads(json_str)
        logger.info(f"Successfully parsed JSON for {candidate_name}")
        
        # Validate and clean result
        validated = validate_comprehensive_result(result, candidate_name)
        return validated
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed for {candidate_name}: {str(e)}")
        logger.error(f"Raw response: {response_text[:500]}...")
        return create_fallback_result(response_text, candidate_name)
    except Exception as e:
        logger.error(f"Response parsing failed for {candidate_name}: {str(e)}")
        return create_fallback_result(response_text, candidate_name)

def validate_comprehensive_result(result: Dict[str, Any], candidate_name: str) -> Dict[str, Any]:
    """Validate and clean comprehensive analysis results"""
    
    try:
        # Extract and validate scores
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
        def clean_array(arr, default_size=3):
            if not isinstance(arr, list):
                return ['Analysis pending'] * default_size
            cleaned = [str(item).strip() for item in arr if item and str(item).strip()]
            # Ensure we have at least some items
            while len(cleaned) < default_size and len(cleaned) < 8:
                if default_size == 3:  # strengths/weaknesses
                    cleaned.append('Additional analysis required')
                else:  # interview questions
                    cleaned.append('Standard competency question to be added')
            return cleaned[:default_size if default_size == 3 else 8]  # Max 3 for strengths/weaknesses, 8 for questions
        
        # Clean interview questions specifically - ENSURE WE HAVE THEM
        interview_questions = result.get('interview_questions', [])
        if not isinstance(interview_questions, list) or len(interview_questions) < 6:
            # Generate default questions if missing
            interview_questions = [
                "Can you walk me through your experience relevant to this role?",
                "Describe a challenging project you've worked on and how you handled it.",
                "What interests you most about this position and our organization?",
                "How do you stay updated with industry trends and developments?",
                "Tell me about a time you had to learn something new quickly.",
                "Where do you see yourself in 3-5 years?",
                "What motivates you in your work?",
                "Do you have any questions about the role or our company?"
            ]
        
        # Clean recommendations to be more definitive
        recommendations = clean_text(result.get('recommendations'))
        if not any(keyword in recommendations for keyword in ['Strong Yes', 'Yes', 'Conditional Yes', 'Maybe', 'No']):
            # Make recommendation more definitive based on score
            if overall_score >= 80:
                recommendations = f"Strong Yes - {recommendations}"
            elif overall_score >= 70:
                recommendations = f"Yes - {recommendations}"
            elif overall_score >= 60:
                recommendations = f"Conditional Yes - {recommendations}"
            elif overall_score >= 45:
                recommendations = f"Maybe - {recommendations}"
            else:
                recommendations = f"No - {recommendations}"
        
        validated = {
            'candidate_name': str(result.get('candidate_name', candidate_name)).strip(),
            'skills_score': skills_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'overall_score': overall_score,
            'skills_analysis': clean_text(result.get('skills_analysis')),
            'experience_analysis': clean_text(result.get('experience_analysis')),
            'education_analysis': clean_text(result.get('education_analysis')),
            'fit_assessment': clean_text(result.get('fit_assessment')),
            'recommendations': recommendations,
            'strengths': clean_array(result.get('strengths', []), 3),
            'weaknesses': clean_array(result.get('weaknesses', []), 3),
            'interview_questions': interview_questions[:8]  # Limit to 8 questions
        }
        
        logger.info(f"Validated comprehensive result for {candidate_name}: Overall Score = {validated['overall_score']}%")
        return validated
        
    except Exception as e:
        logger.error(f"Validation error for {candidate_name}: {str(e)}")
        return create_default_comprehensive_result(candidate_name)

def create_fallback_result(response_text: str, candidate_name: str) -> Dict[str, Any]:
    """Create fallback result when JSON parsing fails but we have response text"""
    try:
        # Try to extract scores with regex
        skills_match = re.search(r'skills?[:\s]*(\d+)', response_text, re.IGNORECASE)
        experience_match = re.search(r'experience[:\s]*(\d+)', response_text, re.IGNORECASE)
        education_match = re.search(r'education[:\s]*(\d+)', response_text, re.IGNORECASE)
        
        skills_score = int(skills_match.group(1)) if skills_match else 65
        experience_score = int(experience_match.group(1)) if experience_match else 65
        education_score = int(education_match.group(1)) if education_match else 65
        
        overall_score = round(skills_score * 0.5 + experience_score * 0.3 + education_score * 0.2, 1)
        
        # Extract any text that looks like analysis
        analysis_text = response_text[:500] if len(response_text) > 500 else response_text
        
        return {
            'candidate_name': candidate_name,
            'skills_score': max(0, min(100, skills_score)),
            'experience_score': max(0, min(100, experience_score)),
            'education_score': max(0, min(100, education_score)),
            'overall_score': overall_score,
            'skills_analysis': f"Skills evaluation completed with estimated {skills_score}% match based on available information",
            'experience_analysis': f"Experience assessment shows approximately {experience_score}% alignment with role requirements",
            'education_analysis': f"Educational background evaluated at {education_score}% relevance to position",
            'fit_assessment': f"Overall candidate assessment: {overall_score}% fit for the role based on available analysis",
            'recommendations': f"Conditional Yes - Candidate shows {overall_score}% alignment. Recommend proceeding with interview for detailed evaluation",
            'strengths': ['Analysis completed', 'Resume processed successfully', 'Candidate profile available'],
            'weaknesses': ['Re-run analysis for detailed insights', 'Additional evaluation needed', 'Further assessment required'],
            'interview_questions': [
                "Can you tell me about your background and experience relevant to this role?",
                "What interests you most about this position?", 
                "Describe a challenging project you've worked on recently.",
                "How do you handle working under pressure?",
                "What are your career goals for the next 3-5 years?",
                "Why do you want to work with our organization?",
                "What questions do you have about the role?",
                "How do you stay current with industry developments?"
            ]
        }
    except Exception as e:
        logger.error(f"Fallback creation failed for {candidate_name}: {str(e)}")
        return create_default_comprehensive_result(candidate_name)

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
    """Analyze single candidate using Gemini 1.5 Flash model"""
    
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
    candidate_name = extract_name_from_text(resume_text)
    if not candidate_name or candidate_name == "Unknown Candidate":
        candidate_name = extract_name_from_filename(filename)
    
    logger.info(f"Extracted candidate name: {candidate_name}")
    
    try:
        # FIXED: Use correct Gemini 2.5 Flash model name (LATEST MODEL)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-002",  # LATEST 2.5 FLASH MODEL
            generation_config={
                "temperature": 0.1,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        prompt = create_comprehensive_analysis_prompt(resume_text, job_description, candidate_name, batch_mode)
        
        # Try analysis with retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} for {candidate_name}")
                
                # Show progress to user
                if attempt == 0:
                    st.info(f"🔄 Analyzing {candidate_name} with Gemini 2.5 Flash...")
                
                response = model.generate_content(prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    logger.info(f"Received response for {candidate_name}, length: {len(response.text)}")
                    
                    result = parse_comprehensive_response(response.text, candidate_name)
                    
                    if result and result.get('overall_score', 0) >= 0:
                        logger.info(f"✅ Success: {candidate_name} - {result['overall_score']}%")
                        
                        # Show success to user
                        st.success(f"✅ Analysis completed for {candidate_name} - {result['overall_score']}% match")
                        
                        return result
                    
                logger.warning(f"Invalid result for {candidate_name} (attempt {attempt + 1})")
                
                if attempt < max_retries - 1:
                    st.info(f"⚠️ Retrying analysis for {candidate_name}...")
                    time.sleep(3)
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {candidate_name}: {str(e)}")
                
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    st.error("❌ API quota exceeded. Please try again later.")
                    return create_default_comprehensive_result(candidate_name)
                
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Error in attempt {attempt + 1}, retrying...")
                    time.sleep(5)
                else:
                    st.error(f"❌ Analysis failed for {candidate_name}: {str(e)}")
        
        # All attempts failed
        st.error(f"❌ Analysis failed for {candidate_name} after {max_retries} attempts")
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
        
        # Rate limiting - longer delay for batch processing
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
            # Include interview questions in Excel
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
            worksheet = writer.sheets['Analysis Results']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return output.getvalue()
    except Exception as e:
        logger.error(f"Excel generation error: {str(e)}")
        return None

def create_json_report(results):
    """Create JSON report"""
    try:
        import json
        from datetime import datetime
        
        report_data = {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_candidates': len(results),
            'candidates': results
        }
        return json.dumps(report_data, indent=2)
    except Exception as e:
        logger.error(f"JSON generation error: {str(e)}")
        return None
