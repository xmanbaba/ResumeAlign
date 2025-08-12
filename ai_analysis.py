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
    """Enhanced name extraction with better accuracy"""
    if not text:
        return "Unknown Candidate"
    
    lines = text.split('\n')[:10]  # Check first 10 lines
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
            
        # Skip common headers and keywords
        skip_keywords = [
            'resume', 'cv', 'curriculum', 'profile', 'contact', 'real', 
            'document', 'name', 'email', 'phone', 'address', 'objective',
            'summary', 'education', 'experience', 'skills', 'work', 'personal'
        ]
        
        if any(keyword in line.lower() for keyword in skip_keywords):
            continue
            
        # Look for name pattern - 2-4 words, each starting with capital
        words = line.split()
        if 2 <= len(words) <= 4:
            # Check if all words look like names
            name_words = []
            for word in words:
                # Clean punctuation but keep letters
                clean_word = re.sub(r'[^\w\s]', '', word)
                if (clean_word.isalpha() and 
                    clean_word[0].isupper() and 
                    len(clean_word) >= 2 and 
                    len(clean_word) <= 15):
                    name_words.append(clean_word)
            
            if len(name_words) >= 2:
                name = ' '.join(name_words[:3])  # Max 3 words
                if len(name) <= 50:  # Reasonable name length
                    return name
    
    return "Unknown Candidate"

def extract_name_from_filename_simple(filename: str) -> str:
    """Enhanced filename-based name extraction"""
    if not filename:
        return "Unknown Candidate"
    
    # Remove extension
    name_part = filename.rsplit('.', 1)[0]
    
    # Replace separators with spaces
    name_part = re.sub(r'[_-]', ' ', name_part)
    
    # Remove common keywords (case insensitive)
    name_part = re.sub(r'(?i)\b(resume|cv|real|test|sample|document|file)\b', '', name_part)
    
    # Clean and format
    name_part = name_part.strip()
    words = name_part.split()
    
    if len(words) >= 2:
        clean_words = []
        for word in words:
            if word.isalpha() and len(word) >= 2:
                clean_words.append(word.capitalize())
        
        if len(clean_words) >= 2:
            return ' '.join(clean_words[:3])  # Max 3 words
    
    return "Unknown Candidate"

def configure_gemini():
    """Configure Gemini API - FREE MODEL ONLY"""
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ Gemini API key not found in secrets.")
            return False
        
        genai.configure(api_key=api_key)
        logger.info("Successfully configured Gemini API (FREE MODEL)")
        return True
        
    except Exception as e:
        logger.error(f"Gemini configuration error: {str(e)}")
        st.error(f"❌ Failed to configure Gemini API: {str(e)}")
        return False

def create_enhanced_analysis_prompt(resume_text: str, job_description: str, candidate_name: str) -> str:
    """Create STRICT analysis prompt with proper scoring thresholds"""
    
    prompt = f"""You are a STRICT professional HR analyst. Analyze this candidate against job requirements with HONEST, RIGOROUS scoring.

CANDIDATE: {candidate_name}

JOB DESCRIPTION:
{job_description}

RESUME/CV CONTENT:
{resume_text}

CRITICAL SCORING RULES:
1. BE HARSH AND REALISTIC - Don't inflate scores
2. STRICT Scoring Scale (0-100):
   - 90-100: EXCEPTIONAL - Exceeds ALL requirements significantly
   - 80-89: STRONG - Meets ALL major requirements well
   - 70-79: GOOD - Meets MOST requirements adequately
   - 60-69: MODERATE - Meets SOME requirements, notable gaps
   - 50-59: WEAK - Major gaps in key requirements
   - 0-49: POOR - Does not meet job requirements

3. RECOMMENDATION RULES (STRICTLY ENFORCED):
   - 85+: "Strong Yes"
   - 75-84: "Yes" 
   - 65-74: "Conditional Yes"
   - 50-64: "Maybe"
   - Below 50: "No"

4. ALWAYS start ALL analysis text with: "{candidate_name}"
5. Calculate: Overall = (Skills × 50% + Experience × 30% + Education × 20%)
6. Be SPECIFIC about why scores are given

Return ONLY this JSON (no markdown, no explanations):
{{
    "candidate_name": "{candidate_name}",
    "skills_score": <0-100 integer>,
    "experience_score": <0-100 integer>,
    "education_score": <0-100 integer>,
    "overall_score": <calculated to 1 decimal>,
    "skills_analysis": "{candidate_name} demonstrates [DETAILED skills analysis with specific examples from resume]",
    "experience_analysis": "{candidate_name}'s experience shows [DETAILED experience analysis with specific examples]",
    "education_analysis": "{candidate_name}'s educational background [DETAILED education analysis]",
    "fit_assessment": "{candidate_name} presents [COMPREHENSIVE assessment linking all factors]",
    "strengths": ["<specific strength 1>", "<specific strength 2>", "<specific strength 3>"],
    "weaknesses": ["<specific weakness 1>", "<specific weakness 2>", "<specific weakness 3>"],
    "recommendations": "<Strong Yes/Yes/Conditional Yes/Maybe/No> - {candidate_name} [specific reasoning based on ACTUAL score]",
    "interview_questions": [
        "<relevant technical question>",
        "<behavioral question>", 
        "<role-specific question>",
        "<experience question>",
        "<cultural fit question>",
        "<motivation question>"
    ]
}}

BE BRUTALLY HONEST. Don't inflate scores. A 47% candidate should get "No", not "Conditional Yes"!"""
    
    return prompt

def create_strict_recommendation(overall_score: float, candidate_name: str) -> str:
    """FIXED: Create STRICT recommendations based on actual scores"""
    
    # ENFORCE STRICT THRESHOLDS
    if overall_score >= 85:
        return f"Strong Yes - {candidate_name} is an exceptional candidate with {overall_score}% alignment. Highly recommended for immediate progression to interview stage."
    elif overall_score >= 75:
        return f"Yes - {candidate_name} is a strong candidate with {overall_score}% alignment. Recommended for interview with standard preparation."
    elif overall_score >= 65:
        return f"Conditional Yes - {candidate_name} shows {overall_score}% alignment. Consider for interview but address identified skill gaps during evaluation."
    elif overall_score >= 50:
        return f"Maybe - {candidate_name} has {overall_score}% alignment with significant concerns. Only consider if candidate pool is extremely limited."
    else:
        return f"No - {candidate_name} has {overall_score}% alignment and does not meet minimum requirements. Not recommended for interview stage."

def parse_enhanced_response(response_text: str, candidate_name: str) -> Optional[Dict[str, Any]]:
    """Parse AI response with enhanced validation and error handling"""
    try:
        cleaned_text = response_text.strip()
        logger.info(f"Parsing response for {candidate_name}, length: {len(cleaned_text)}")
        
        # Remove markdown formatting
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
        return create_fallback_result(candidate_name, 35)  # Low score for parsing failure
    except Exception as e:
        logger.error(f"Response parsing failed for {candidate_name}: {str(e)}")
        return create_fallback_result(candidate_name, 35)

def validate_and_enhance_result(result: Dict[str, Any], candidate_name: str) -> Dict[str, Any]:
    """FIXED: Validate with STRICT scoring and proper name inclusion"""
    
    try:
        # Extract and validate scores (ensure they're realistic)
        skills_score = max(0, min(100, int(float(result.get('skills_score', 40)))))
        experience_score = max(0, min(100, int(float(result.get('experience_score', 40)))))
        education_score = max(0, min(100, int(float(result.get('education_score', 40)))))
        
        # Calculate overall score with proper rounding
        overall_score = round(
            skills_score * 0.5 + experience_score * 0.3 + education_score * 0.2, 1
        )
        
        # CRITICAL FIX: Ensure candidate name appears in ALL analysis fields
        def ensure_name_in_analysis(text, field_name):
            if not text or str(text).strip() in ['N/A', 'n/a', 'None', 'null', '']:
                return f"{candidate_name}'s {field_name.lower()} could not be fully assessed from the provided resume."
            
            text = str(text).strip()
            # If candidate name is not at the beginning, add it
            if not text.startswith(candidate_name):
                # Remove any existing name at start and add correct one
                words = text.split()
                if len(words) >= 2 and words[0].istitle() and words[1].istitle():
                    # Likely has a name, replace it
                    text = ' '.join(words[2:]) if len(words) > 2 else text
                
                # Add correct name at beginning
                if text and not text[0].isupper():
                    text = text[0].upper() + text[1:]
                text = f"{candidate_name} {text.lower()}" if text else f"{candidate_name}'s analysis is pending."
            
            return text
        
        # Enhanced analysis fields with guaranteed name inclusion
        skills_analysis = ensure_name_in_analysis(result.get('skills_analysis'), 'skills')
        experience_analysis = ensure_name_in_analysis(result.get('experience_analysis'), 'experience')
        education_analysis = ensure_name_in_analysis(result.get('education_analysis'), 'education')
        fit_assessment = ensure_name_in_analysis(result.get('fit_assessment'), 'overall fit')
        
        # FIXED: STRICT recommendation logic - NO MORE 47% = "Conditional Yes"!
        recommendations = create_strict_recommendation(overall_score, candidate_name)
        
        # Clean and validate arrays
        def clean_array(arr, default_prefix, default_size=3):
            if not isinstance(arr, list):
                return [f'{default_prefix} assessment pending'] * default_size
            
            cleaned = []
            for item in arr:
                if item and str(item).strip() and len(str(item).strip()) > 5:
                    cleaned.append(str(item).strip())
            
            # Ensure minimum size
            while len(cleaned) < default_size:
                cleaned.append(f'Additional {default_prefix.lower()} evaluation needed')
            
            return cleaned[:default_size]  # Limit to requested size
        
        # Ensure interview questions exist and are relevant
        interview_questions = result.get('interview_questions', [])
        if not isinstance(interview_questions, list) or len(interview_questions) < 6:
            # Generate default professional questions
            first_name = candidate_name.split()[0] if candidate_name != "Unknown Candidate" else "candidate"
            interview_questions = [
                f"Can you walk me through your most relevant experience for this role, {first_name}?",
                "Describe a challenging project you've worked on and how you overcame obstacles.",
                "What specific skills do you bring that align with our job requirements?",
                "How do you stay current with industry trends and developments?",
                "Tell me about a time you had to learn something new quickly for work.",
                "What interests you most about this position and our organization?"
            ]
        
        # Build validated result
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
            'strengths': clean_array(result.get('strengths', []), 'Strength', 3),
            'weaknesses': clean_array(result.get('weaknesses', []), 'Area for improvement', 3),
            'interview_questions': interview_questions[:6]  # Exactly 6 questions
        }
        
        # Log the strict evaluation
        rec_type = recommendations.split(' -')[0] if ' -' in recommendations else recommendations
        logger.info(f"STRICT EVALUATION: {candidate_name} - {overall_score}% = {rec_type}")
        
        return validated
        
    except Exception as e:
        logger.error(f"Validation error for {candidate_name}: {str(e)}")
        return create_fallback_result(candidate_name, 35)

def create_fallback_result(candidate_name: str, default_score: int = 35) -> Dict[str, Any]:
    """Create fallback result with proper candidate name inclusion"""
    
    overall_score = round(default_score * 0.5 + default_score * 0.3 + default_score * 0.2, 1)
    
    # Create strict recommendation for fallback
    if overall_score >= 85:
        rec = f"Strong Yes - {candidate_name} shows exceptional potential"
    elif overall_score >= 75:
        rec = f"Yes - {candidate_name} meets most requirements"
    elif overall_score >= 65:
        rec = f"Conditional Yes - {candidate_name} has some gaps to address"
    elif overall_score >= 50:
        rec = f"Maybe - {candidate_name} has significant limitations"
    else:
        rec = f"No - {candidate_name} does not meet minimum requirements for this role"
    
    first_name = candidate_name.split()[0] if candidate_name != "Unknown Candidate" else "candidate"
    
    return {
        'candidate_name': candidate_name,
        'skills_score': default_score,
        'experience_score': default_score,
        'education_score': default_score,
        'overall_score': overall_score,
        'skills_analysis': f"{candidate_name} requires detailed skills assessment. Analysis encountered processing issues.",
        'experience_analysis': f"{candidate_name}'s experience evaluation needs manual review due to processing limitations.",
        'education_analysis': f"{candidate_name}'s educational background assessment failed automated processing.",
        'fit_assessment': f"{candidate_name} shows {overall_score}% preliminary alignment but requires comprehensive manual evaluation.",
        'recommendations': rec,
        'strengths': [f'{candidate_name} shows potential', 'Manual review recommended', 'Retry analysis suggested'],
        'weaknesses': ['Automated analysis incomplete', 'Resume format may need adjustment', 'Detailed manual evaluation required'],
        'interview_questions': [
            f"Could you tell me about your background and relevant experience, {first_name}?",
            "What specific skills do you bring to this role?",
            "Describe a challenging project you've completed recently.",
            "What interests you about this position?",
            "How do you approach learning new technologies or skills?",
            "What are your career goals for the next few years?"
        ]
    }

def analyze_single_candidate(resume_text: str, job_description: str, filename: str, batch_mode: bool = False, max_retries: int = 2) -> Optional[Dict[str, Any]]:
    """FIXED: Analyze with FREE Gemini model and STRICT scoring"""
    
    logger.info(f"Analyzing {filename} with STRICT evaluation (FREE Gemini 1.5 Flash)")
    
    # Validate inputs
    if not resume_text or not resume_text.strip():
        logger.error(f"No text content for {filename}")
        st.error(f"❌ Could not extract text from {filename}")
        return create_fallback_result("Unknown Candidate", 25)
    
    if not job_description or not job_description.strip():
        logger.error("No job description provided")
        st.error("❌ Job description is required")
        return create_fallback_result("Unknown Candidate", 25)
    
    # Configure API
    if not configure_gemini():
        return create_fallback_result("Unknown Candidate", 25)
    
    # Extract candidate name with enhanced method
    candidate_name = extract_name_from_text_simple(resume_text)
    if not candidate_name or candidate_name == "Unknown Candidate":
        candidate_name = extract_name_from_filename_simple(filename)
    
    logger.info(f"EXTRACTED NAME: {candidate_name}")
    
    try:
        # CONFIRMED: Using FREE Gemini 1.5 Flash model
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # FREE MODEL - CONFIRMED
            generation_config={
                "temperature": 0.1,  # Very low for consistent, strict scoring
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )
        
        prompt = create_enhanced_analysis_prompt(resume_text, job_description, candidate_name)
        
        # Analysis with retries
        for attempt in range(max_retries):
            try:
                logger.info(f"STRICT Analysis attempt {attempt + 1} for {candidate_name}")
                
                if attempt == 0:
                    st.info(f"🔄 Performing STRICT analysis for {candidate_name}...")
                
                response = model.generate_content(prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    logger.info(f"Received response for {candidate_name}, length: {len(response.text)}")
                    
                    result = parse_enhanced_response(response.text, candidate_name)
                    
                    if result and result.get('overall_score', 0) >= 0:
                        score = result['overall_score']
                        rec_type = result['recommendations'].split(' -')[0] if ' -' in result['recommendations'] else 'Unknown'
                        
                        logger.info(f"✅ STRICT ANALYSIS COMPLETE: {candidate_name} - {score}% = {rec_type}")
                        
                        # Show success with strict scoring info
                        if score < 50:
                            st.warning(f"⚠️ STRICT evaluation: {candidate_name} - {score}% (Below minimum threshold)")
                        elif score < 65:
                            st.info(f"📊 STRICT evaluation: {candidate_name} - {score}% (Needs improvement)")
                        elif score < 80:
                            st.success(f"✅ STRICT evaluation: {candidate_name} - {score}% (Good candidate)")
                        else:
                            st.success(f"🌟 STRICT evaluation: {candidate_name} - {score}% (Excellent candidate)")
                        
                        return result
                    
                logger.warning(f"Invalid result for {candidate_name} (attempt {attempt + 1})")
                
                if attempt < max_retries - 1:
                    st.info(f"⚠️ Retrying strict analysis for {candidate_name}...")
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
                    st.error(f"❌ STRICT analysis failed for {candidate_name}: {str(e)}")
        
        # All attempts failed
        st.error(f"❌ STRICT analysis failed for {candidate_name} after {max_retries} attempts")
        return create_fallback_result(candidate_name, 30)
    
    except Exception as e:
        logger.error(f"Critical error for {candidate_name}: {str(e)}")
        st.error(f"❌ Analysis error: {str(e)}")
        return create_fallback_result(candidate_name, 30)

def analyze_batch_candidates(candidates_data: List[Dict[str, str]], job_description: str, progress_callback=None) -> List[Dict[str, Any]]:
    """FIXED: Batch analysis with STRICT scoring"""
    
    if len(candidates_data) > 5:
        st.error("❌ Maximum 5 resumes per batch. Please select fewer files.")
        return []
    
    logger.info(f"Starting STRICT batch analysis of {len(candidates_data)} candidates")
    
    if not configure_gemini():
        return []
    
    results = []
    total_candidates = len(candidates_data)
    
    for i, candidate_data in enumerate(candidates_data):
        filename = candidate_data.get('filename', f'candidate_{i+1}')
        
        if progress_callback:
            progress_callback(i / total_candidates, f"STRICT analysis: {filename}")
        
        try:
            result = analyze_single_candidate(
                candidate_data.get('resume_text', ''),
                job_description,
                filename,
                batch_mode=True
            )
            
            if result and result.get('overall_score', 0) >= 0:
                results.append(result)
                score = result.get('overall_score', 0)
                rec = result.get('recommendations', '').split(' -')[0] if ' -' in result.get('recommendations', '') else 'Unknown'
                logger.info(f"✅ STRICT batch result: {filename} - {score}% = {rec}")
            else:
                logger.warning(f"❌ STRICT batch failed: {filename}")
        
        except Exception as e:
            logger.error(f"STRICT batch error for {filename}: {str(e)}")
            st.error(f"❌ Error in STRICT analysis for {filename}: {str(e)}")
        
        # Rate limiting for API
        if i < total_candidates - 1:
            time.sleep(4)
    
    if progress_callback:
        progress_callback(1.0, f"STRICT analysis complete! {len(results)}/{total_candidates} successful")
    
    logger.info(f"STRICT batch analysis completed: {len(results)}/{total_candidates} successful")
    return results

def create_excel_report(results):
    """Create Excel report with enhanced formatting"""
    try:
        import pandas as pd
        import io
        
        if not results:
            logger.error("No results provided for Excel report")
            return None
        
        data = []
        for result in results:
            interview_questions = result.get('interview_questions', [])
            questions_text = '\n'.join([f"{i+1}. {q}" for i, q in enumerate(interview_questions) if q])
            
            data.append({
                'Candidate Name': result.get('candidate_name', 'Unknown'),
                'Overall Score': result.get('overall_score', 0),
                'Skills Score': result.get('skills_score', 0),
                'Experience Score': result.get('experience_score', 0),
                'Education Score': result.get('education_score', 0),
                'Skills Analysis': result.get('skills_analysis', 'Not available'),
                'Experience Analysis': result.get('experience_analysis', 'Not available'),
                'Education Analysis': result.get('education_analysis', 'Not available'),
                'Fit Assessment': result.get('fit_assessment', 'Not available'),
                'Recommendations': result.get('recommendations', 'Not available'),
                'Strengths': '; '.join(result.get('strengths', [])),
                'Areas for Improvement': '; '.join(result.get('weaknesses', [])),
                'Interview Questions': questions_text
            })
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='STRICT Analysis Results', index=False)
            worksheet = writer.sheets['STRICT Analysis Results']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_data = output.getvalue()
        output.close()
        
        logger.info(f"Successfully created Excel report with {len(results)} candidates")
        return excel_data
        
    except Exception as e:
        logger.error(f"Excel generation error: {str(e)}")
        st.error(f"❌ Excel generation failed: {str(e)}")
        return None

def create_json_report(results):
    """Create comprehensive JSON report"""
    try:
        if not results:
            logger.error("No results provided for JSON report")
            return None
            
        from datetime import datetime
        
        report_data = {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_version': 'ResumeAlign STRICT v2.1',
            'model_used': 'Google Gemini 1.5 Flash (FREE)',
            'total_candidates': len(results),
            'scoring_method': 'STRICT (Skills 50% + Experience 30% + Education 20%)',
            'recommendation_thresholds': {
                'Strong Yes': '85-100%',
                'Yes': '75-84%', 
                'Conditional Yes': '65-74%',
                'Maybe': '50-64%',
                'No': '0-49%'
            },
            'candidates': results
        }
        
        json_str = json.dumps(report_data, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully created JSON report with {len(results)} candidates")
        return json_str
        
    except Exception as e:
        logger.error(f"JSON generation error: {str(e)}")
        st.error(f"❌ JSON generation failed: {str(e)}")
        return None
