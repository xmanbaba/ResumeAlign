"""
Candidate name extraction utilities for ResumeAlign - IMPROVED VERSION
Enhanced name extraction with better accuracy for batch processing
"""

import re
import google.generativeai as genai
import os

# Initialize Gemini model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def extract_candidate_name_from_ai_report(report):
    """Extract candidate name from AI-generated report - Enhanced for better accuracy"""
    try:
        if 'candidate_summary' in report and report['candidate_summary']:
            summary = report['candidate_summary']
            
            # Enhanced patterns to capture names
            name_patterns = [
                # Pattern: "John Doe is a..." or "John Doe brings..."
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z]\.?)*)\s+(?:is|brings|has|possesses|demonstrates|shows|works|serves)\s',
                # Pattern: "Name, a professional..." or "Name is a..."
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),?\s+(?:a|an|is)\s',
                # Pattern: Direct name at start followed by professional title
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:with|having|working)',
                # Pattern: "Mr./Ms./Dr. Name" 
                r'^(?:Mr\.?|Ms\.?|Mrs\.?|Dr\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, summary)
                if match:
                    extracted_name = match.group(1).strip()
                    # Clean up any trailing punctuation
                    extracted_name = re.sub(r'[,.]$', '', extracted_name)
                    if is_valid_name(extracted_name):
                        return clean_name(extracted_name)
            
            # Fallback: Look for capitalized words at the beginning
            words = summary.split()[:5]  # First 5 words
            for i in range(2, min(4, len(words) + 1)):  # Try 2-3 word combinations
                potential_name = " ".join(words[:i])
                if is_valid_name(potential_name):
                    return clean_name(potential_name)
        
        return None
    except Exception as e:
        print(f"Error extracting name from AI report: {e}")
        return None


def extract_candidate_name(text):
    """Enhanced candidate name extraction with improved LinkedIn and CV support"""
    if not text or not text.strip():
        return "Unknown Candidate"
    
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines:
        return "Unknown Candidate"
    
    # Strategy 1: Look for explicit name labels
    name_patterns = [
        r'(?:name|full\s*name|candidate\s*name|applicant\s*name)\s*[:\-]?\s*(.+)',
        r'(?:nome|naam|имя)\s*[:\-]?\s*(.+)',  # Multi-language support
    ]
    
    for line in lines[:10]:
        for pattern in name_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted_name = match.group(1).strip()
                if is_valid_name(extracted_name):
                    return clean_name(extracted_name)
    
    # Strategy 2: Enhanced LinkedIn profile handling
    is_linkedin = detect_linkedin_profile(lines)
    
    if is_linkedin:
        name = extract_name_from_linkedin(lines)
        if name:
            return name
    
    # Strategy 3: Handle formal documents with titles
    for line in lines[:15]:
        # Pattern for formal titles with names
        title_patterns = [
            r'^(?:MR\.?|MS\.?|MRS\.?|DR\.?|PROF\.?)\s+([A-Z][A-Z\s.]+?)(?:\s*[-\–\—]|\s*\$|\s*\n|$)',
            r'^([A-Z][A-Z\s.]+?)\s*[-\–\—]\s*(?:CURRICULUM|RESUME|CV)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip()
                # Clean up and validate
                potential_name = re.sub(r'\s+', ' ', potential_name)
                if is_valid_name(potential_name):
                    return clean_name(potential_name)
    
    # Strategy 4: First meaningful line analysis
    for line in lines[:8]:  # Extended search
        if is_valid_name(line):
            return clean_name(line)
    
    # Strategy 5: Look for name patterns in content
    for line in lines[:15]:
        # Find sequences of capitalized words
        words = line.split()
        if 2 <= len(words) <= 4:
            capitalized_words = []
            for word in words:
                clean_word = re.sub(r'[^\w\s\'-]', '', word)
                if clean_word and clean_word[0].isupper() and clean_word.isalpha():
                    capitalized_words.append(clean_word)
            
            if len(capitalized_words) >= 2 and len(capitalized_words) == len([w for w in words if w]):
                candidate_name = ' '.join(capitalized_words)
                if is_valid_name(candidate_name):
                    return clean_name(candidate_name)
    
    # Strategy 6: AI-assisted extraction (last resort)
    try:
        text_sample = text[:1000]  # Increased sample size
        ai_extracted_name = extract_name_with_ai(text_sample)
        if ai_extracted_name and is_valid_name(ai_extracted_name):
            return clean_name(ai_extracted_name)
    except:
        pass
    
    # Fallback: Use first reasonable line
    for line in lines[:3]:
        cleaned = clean_name(line)
        if cleaned and cleaned != "Unknown Candidate":
            return cleaned
    
    return "Unknown Candidate"


def detect_linkedin_profile(lines):
    """Detect if the text appears to be from a LinkedIn profile"""
    linkedin_indicators = [
        'linkedin', 'about', 'experience', 'education', 'skills', 
        'endorsements', 'recommendations', 'connections', 'activity',
        'top skills',
