import google.generativeai as genai
import streamlit as st
import logging
import time
import json
import re
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_name_from_text_simple(text: str) -> str:
    """Simple name extraction function to avoid import issues"""
    if not text:
        return "Unknown Candidate"
    
    lines = text.split('\n')[:5]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Skip common headers
        if any(keyword in line.lower() for keyword in [
            'resume', 'cv', 'curriculum', 'profile', 'contact', 'real', 'document'
        ]):
            continue
            
        # Look for name pattern
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(word.isalpha() and word[0].isupper() and len(word) > 1 for word in words):
                name = ' '.join(words)
                if len(name) < 50:  # Reasonable name length
                    return name
    
    return "Unknown Candidate"

def extract_name_from_filename_simple(filename: str) -> str:
    """Simple filename-based name extraction"""
    if not filename:
        return "Unknown Candidate"
    
    # Remove extension
    name_part = filename.rsplit('.', 1)[0]
    
    # Replace underscores/hyphens with spaces
    name_part = re.sub(r'[_-]', ' ', name_part)
    
    # Remove common keywords
    name_part = re.sub(r'(?i)(resume|cv|real|test|sample)', '', name_part)
    
    # Clean and format
    name_part = name_part.strip()
    words = name_part.split()
    
    if len(words) >= 2:
        clean_words = [word.capitalize() for word in words if word.isalpha()]
        if len(clean_words) >= 2:
            return ' '.join(clean_words[:3])  # Max 3 words
    
    return "Unknown Candidate"

def configure_gemini():
    """Configure Gemini API"""
    try:
        # Get API key from Streamlit secrets
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

def create_enhanced_analysis_prompt(resume_text: str, job_description: str, candidate_name: str) -> str:
    """Create enhanced analysis prompt with STRICT scoring and better consistency"""
    
    prompt = f"""You are a professional HR analyst. Analyze this candidate against the job requirements with STRICT and CONSISTENT scoring.

CANDIDATE: {candidate_name}

JOB DESCRIPTION:
{job_description}

RESUME/CV CONTENT:
{resume_text}

CRITICAL INSTRUCTIONS:
1. ALWAYS start your analysis text with the candidate's name: "{candidate_name}"
2. Use STRICT scoring - be honest about gaps and mismatches
3. Score 0-100 where:
   - 90-100: Exceptional match, exceeds requirements significantly
   - 80-89: Strong match, meets most requirements well
   - 70-79: Good match, meets core requirements
   - 60-69: Adequate match, some gaps but workable
   - 50-59: Poor match, significant gaps in key areas
   - Below 50: Not suitable, major misalignment

4. Calculate overall score: (Skills × 50% + Experience × 30% + Education × 20%)

5. Make recommendations based on ACTUAL scores:
   - 85+: "Strong Yes"
   - 75-84: "Yes"
   - 65-74: "Conditional Yes"
   - 50-64: "Maybe"
   - Below 50: "No"

6. ALWAYS mention the candidate's name in your detailed analysis

Return ONLY this JSON format:
{{
    "candidate_name": "{candidate_name}",
    "skills_score": <0-100>,
    "experience_score": <0-100>,
    "education_score": <0-100>,
    "overall_score": <calculated score to 1 decimal>,
    "skills_analysis": "{candidate_name} demonstrates... [detailed skills analysis]",
    "experience_analysis": "{candidate_name}'s experience shows... [detailed experience analysis]",
    "education_analysis": "{candidate_name}'s educational background... [detailed education analysis]",
    "fit_assessment": "{candidate_name} presents... [comprehensive overall assessment]",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>", "<weakness 3>"],
    "recommendations": "<Strong Yes/Yes/Conditional Yes/Maybe/No> - {candidate_name} [specific reasoning based on actual score]",
    "interview_questions": [
        "<relevant question 1>",
        "<relevant question 2>",
        "<relevant question 3>",
        "<relevant question 4>",
        "<relevant question 5>",
        "<relevant question 6>"
    ]
}}

BE STRICT and HONEST in your evaluation. Don't inflate scores!"""
    
    return prompt

def parse_enhanced_response(response_text: str, candidate_name: str) -> Optional[Dict[str, Any]]:
    """Parse AI response with enhanced validation"""
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
        
        # Validate and enhance result
        validated = validate_and_enhance_result(result, candidate_name)
        return validated
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed for {candidate_name}: {str(e)}")
        return create_fallback_result(candidate_name, 45)  # Default low score
    except Exception as e:
        logger.error(f"Response parsing failed for {candidate_name}: {str(e)}")
        return create_fallback_result(candidate_name, 45)

def validate_and_enhance_result(result: Dict[str, Any], candidate_name: str) -> Dict[str, Any]:
    """Validate and enhance analysis results with STRICT recommendations"""
    
    try:
        # Extract and validate scores
        skills_score = max(0, min(100, int(float(result.get('skills_score', 45)))))
        experience_score = max(0, min(100, int(float(result.get('experience_score', 45)))))
        education_score = max(0, min(100, int(float(result.get('education_score', 45)))))
        
        # Calculate overall score
        overall_score = round(
            skills_score * 0.5 + experience_score * 0.3 + education_score * 0.2, 1
        )
        
        # ENHANCED: Ensure candidate name appears in ALL analysis fields
        def enhance_analysis_text(text, field_name):
            if not text or str(text).strip() in ['N/A', 'n/a', 'None', 'null', '']:
                return f"{candidate_name}'s {field_name.lower()} analysis is not available"
            
            text = str(text).strip()
            # If candidate name is not mentioned, add it at the beginning
            if candidate_name not in text and not text.startswith(candidate_name):
                text = f"{candidate_name} {text[0].lower() + text[1:] if len(text) > 1 else text}"
            
            return text
        
        # Clean and enhance analysis fields
        skills_analysis = enhance_analysis_text(result.get('skills_analysis'), 'Skills')
        experience_analysis = enhance_analysis_text(result.get('experience_analysis'), 'Experience')
        education_analysis = enhance_analysis_text(result.get('education_analysis'), 'Education')
        fit_assessment = enhance_analysis_text(result.get('fit_assessment'), 'Overall fit')
        
        # FIXED: STRICT recommendation logic based on ACTUAL scores
        recommendations = create_strict_recommendation(overall_score, candidate_name)
        
        # Clean arrays
        def clean_array(arr, default_size=3):
            if not isinstance(arr, list):
                return [f'{candidate_name} analysis pending'] * default_size
            cleaned = [str(item).strip() for item in arr if item and str(item).strip()]
            while len(cleaned) < default_size:
                cleaned.append(f'Additional {candidate_name} assessment needed')
            return cleaned[:default_size]
        
        # Ensure interview questions are present
        interview_questions = result.get('interview_questions', [])
        if not isinstance(interview_questions, list) or len(interview_questions) < 6:
            interview_questions = [
                f"Can you walk me through your experience relevant to this role, {candidate_name.split()[0] if candidate_name else 'candidate'}?",
                "Describe a challenging project you've worked on and how you handled it.",
                "What interests you most about this position and our organization?",
                "How do you stay updated with industry trends and developments?",
                "Tell me about a time you had to learn something new quickly.",
                "Where do you see yourself in 3-5 years professionally?"
            ]
        
        validated = {
            'candidate_name': candidate_name,
            'skills_score': skills_score,
            'experience_score': experience_score,
            'education_score': education_score,
            'overall_score': overall_score,
            'skills_analysis': skills_analysis,
            'experience_analysis': experience_analysis,
            'education_analysis': education_analysis,
            'fit_assessment': fit_assessment,
            'recommendations': recommendations,
            'strengths': clean_array(result.get('strengths', []), 3),
            'weaknesses': clean_array(result.get('weaknesses', []), 3),
            'interview_questions': interview_questions[:6]  # Limit to 6 questions
        }
        
        logger.info(f"Enhanced result for {candidate_name}: {validated['overall_score']}% - {recommendations.split(' -')[0]}")
        return validated
        
    except Exception as e:
        logger.error(f"Validation error for {candidate_name}: {str(e)}")
        return create_fallback_result(candidate_name, 35)

def create_strict_recommendation(overall_score: float, candidate_name: str) -> str:
    """Create STRICT recommendations based on actual scores - FIXED LOGIC"""
    
    if overall_score >= 85:
        return f"Strong Yes - {candidate_name} is an exceptional candidate with {overall_score}% alignment. Excellent fit for the role with minimal training needed."
    elif overall_score >= 75:
        return f"Yes - {candidate_name} is a strong candidate with {overall_score}% alignment. Good fit for the role with standard onboarding."
    elif overall_score >= 65:
        return f"Conditional Yes - {candidate_name} shows {overall_score}% alignment. Consider with targeted training to address skill gaps."
    elif overall_score >= 50:
        return f"Maybe - {candidate_name} has {overall_score}% alignment with significant gaps. Only consider if candidate pool is limited."
    else:
        return f"No - {candidate_name} has {overall_score}% alignment with major misalignment. Not recommended for this role."

def create_fallback_result(candidate_name: str, default_score: int = 35) -> Dict[str, Any]:
    """Create fallback result with candidate name properly included"""
    
    overall_score = round(default_score * 0.5 + default_score * 0.3 + default_score * 0.2, 1)
    
    return {
        'candidate_name': candidate_name,
        'skills_score': default_score,
        'experience_score': default_score,
        'education_score': default_score,
        'overall_score': overall_score,
        'skills_analysis': f"{candidate_name}'s skills analysis encountered processing issues. Please retry analysis for detailed evaluation.",
        'experience_analysis': f"{candidate_name}'s experience assessment could not be completed. Recommend manual review of resume.",
        'education_analysis': f"{candidate_name}'s educational background analysis failed. Please check resume format and retry.",
        'fit_assessment': f"{candidate_name} requires manual evaluation due to analysis processing issues. Overall automated score: {overall_score}%",
        'recommendations': f"No - {candidate_name} analysis incomplete ({overall_score}%). Manual review required before making hiring decision.",
        'strengths': [f'{candidate_name} analysis incomplete', 'Manual review needed', 'Retry analysis recommended'],
        'weaknesses': ['Analysis processing failed', 'Resume format issues possible', 'Detailed evaluation needed'],
        'interview_questions': [
            f"Could you tell me about your background and experience, {candidate_name.split()[0] if candidate_name else 'candidate'}?",
            "What interests you about this role and our organization?",
            "Describe your most relevant professional experience.",
            "What are your key strengths for this position?",
            "How do you handle challenges in your work?",
            "What are your career goals and aspirations?"
        ]
    }

def analyze_single_candidate(resume_text: str, job_description: str, filename: str, batch_mode: bool = False, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """Analyze single candidate with enhanced prompts and strict scoring"""
    
    logger.info(f"Analyzing {filename} with enhanced Gemini analysis")
    
    # Validate inputs
    if not resume_text or not resume_text.strip():
        error_msg = f"❌ Could not extract text from {filename}"
        logger.error(error_msg)
        st.error(error_msg)
        return create_fallback_result("Unknown Candidate", 25)
    
    if not job_description or not job_description.strip():
        error_msg = "❌ Job description is required"
        logger.error(error_msg)
        st.error(error_msg)
        return create_fallback_result("Unknown Candidate", 25)
    
    # Configure API
    if not configure_gemini():
        return create_fallback_result("Unknown Candidate", 25)
    
    # Extract candidate name using simple functions
    candidate_name = extract_name_from_text_simple(resume_text)
    if not candidate_name or candidate_name == "Unknown Candidate":
        candidate_name = extract_name_from_filename_simple(filename)
    
    logger.info(f"Extracted candidate name: {candidate_name}")
    
    try:
        # Use Gemini 1.5 Flash (free tier)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # FREE MODEL
            generation_config={
                "temperature": 0.2,  # Lower for more consistent results
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        prompt = create_enhanced_analysis_prompt(resume_text, job_description, candidate_name)
        
        # Try analysis with retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1} for {candidate_name}")
                
                if attempt == 0:
                    st.info(f"🔄 Analyzing {candidate_name} with enhanced AI evaluation...")
                
                response = model.generate_content(prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    logger.info(f"Received response for {candidate_name}, length: {len(response.text)}")
                    
                    result = parse_enhanced_response(response.text, candidate_name)
                    
                    if result and result.get('overall_score', 0) >= 0:
                        logger.info(f"✅ Enhanced analysis: {candidate_name} - {result['overall_score']}%")
                        st.success(f"✅ Enhanced analysis completed for {candidate_name} - {result['overall_score']}% match")
                        return result
                    
                logger.warning(f"Invalid result for {candidate_name} (attempt {attempt + 1})")
                
                if attempt < max_retries - 1:
                    st.info(f"⚠️ Retrying enhanced analysis for {candidate_name}...")
                    time.sleep(3)
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed for {candidate_name}: {str(e)}")
                
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    st.error("❌ API quota exceeded. Please try again later.")
                    return create_fallback_result(candidate_name, 30)
                
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Error in attempt {attempt + 1}, retrying...")
                    time.sleep(5)
                else:
                    st.error(f"❌ Enhanced analysis failed for {candidate_name}: {str(e)}")
        
        # All attempts failed
        st.error(f"❌ Enhanced analysis failed for {candidate_name} after {max_retries} attempts")
        return create_fallback_result(candidate_name, 30)
    
    except Exception as e:
        logger.error(f"Critical error for {candidate_name}: {str(e)}")
        st.error(f"❌ Analysis error: {str(e)}")
        return create_fallback_result(candidate_name, 30)

def analyze_batch_candidates(candidates_data: List[Dict[str, str]], job_description: str, progress_callback=None) -> List[Dict[str, Any]]:
    """Batch analysis with enhanced consistency"""
    
    if len(candidates_data) > 5:
        st.error("❌ Maximum 5 resumes per batch. Please select fewer files.")
        return []
    
    logger.info(f"Starting enhanced batch analysis of {len(candidates_data)} candidates")
    
    if not configure_gemini():
        return []
    
    results = []
    total_candidates = len(candidates_data)
    
    for i, candidate_data in enumerate(candidates_data):
        filename = candidate_data.get('filename', f'candidate_{i+1}')
        
        if progress_callback:
            progress_callback(i / total_candidates, f"Enhanced analysis: {filename}")
        
        try:
            result = analyze_single_candidate(
                candidate_data.get('resume_text', ''),
                job_description,
                filename,
                batch_mode=True
            )
            
            if result and result.get('overall_score', 0) >= 0:
                results.append(result)
                logger.info(f"✅ Enhanced batch: {filename} - {result.get('overall_score', 0)}%")
            else:
                logger.warning(f"❌ Enhanced batch failed: {filename}")
        
        except Exception as e:
            logger.error(f"Enhanced batch error for {filename}: {str(e)}")
            st.error(f"❌ Error in enhanced analysis for {filename}: {str(e)}")
        
        # Rate limiting
        if i < total_candidates - 1:
            time.sleep(4)
    
    if progress_callback:
        progress_callback(1.0, f"Enhanced analysis complete! {len(results)}/{total_candidates} successful")
    
    logger.info(f"Enhanced batch analysis completed: {len(results)}/{total_candidates} successful")
    return results

def create_excel_report(results):
    """Create Excel report with enhanced formatting"""
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
            df.to_excel(writer, sheet_name='Enhanced Analysis Results', index=False)
            worksheet = writer.sheets['Enhanced Analysis Results']
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
    """Create JSON report with enhanced data"""
    try:
        from datetime import datetime
        
        report_data = {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_version': 'Enhanced ResumeAlign v2.0',
            'total_candidates': len(results),
            'candidates': results
        }
        return json.dumps(report_data, indent=2)
    except Exception as e:
        logger.error(f"JSON generation error: {str(e)}")
        return None
