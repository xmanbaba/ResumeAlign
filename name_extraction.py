"""
Candidate name extraction utilities for ResumeAlign
Handles name extraction from CVs, resumes, and AI reports
"""

import re
import google.generativeai as genai
import os

# Initialize Gemini model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def extract_candidate_name_from_ai_report(report):
    """Extract candidate name from AI-generated report - primary method for batch processing"""
    try:
        # Method 1: Extract from candidate_summary (most reliable)
        if 'candidate_summary' in report:
            summary = report['candidate_summary']
            # Look for patterns like "John Doe is a...", "John Doe brings...", etc.
            name_patterns = [
                r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,? [A-Z]+\.?)*) is ',
                r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,? [A-Z]+\.?)*) brings ',
                r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,? [A-Z]+\.?)*) has ',
                r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,? [A-Z]+\.?)*) possesses ',
                r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,? [A-Z]+\.?)*) demonstrates ',
                r'^([A-Z][a-z]+(?: [A-Z][a-z]+)*(?:,? [A-Z]+\.?)*) shows '
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, summary)
                if match:
                    extracted_name = match.group(1).strip()
                    # Clean up any trailing punctuation
                    extracted_name = re.sub(r'[,.]$', '', extracted_name)
                    if is_valid_name(extracted_name):
                        return clean_name(extracted_name)
        return None
    except:
        return None


def extract_candidate_name(text):
    """Enhanced candidate name extraction with LinkedIn profile support"""
    if not text.strip():
        return "Unknown Candidate"
    
    lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
    if not lines:
        return "Unknown Candidate"
    
    # Strategy 1: Look for explicit name patterns first
    name_patterns = [
        r'name\s*[:]?\s*(.+)',
        r'full\s*name\s*[:]?\s*(.+)',
        r'candidate\s*name\s*[:]?\s*(.+)',
        r'applicant\s*name\s*[:]?\s*(.+)'
    ]
    
    for line in lines[:10]:  # Check first 10 lines
        for pattern in name_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted_name = match.group(1).strip()
                if is_valid_name(extracted_name):
                    return clean_name(extracted_name)
    
    # Strategy 2: Handle LinkedIn profiles specifically
    linkedin_indicators = ['contact', 'about', 'experience', 'education', 'skills', 'linkedin']
    
    # Check if this looks like a LinkedIn profile
    first_few_lines = ' '.join(lines[:5]).lower()
    is_linkedin = any(indicator in first_few_lines for indicator in linkedin_indicators)
    
    if is_linkedin:
        # For LinkedIn, skip navigation elements and look for name patterns
        for i, line in enumerate(lines[:20]):  # Extended search for LinkedIn
            line_lower = line.lower()
            
            # Skip obvious navigation/section headers
            skip_terms = ['contact', 'about', 'experience', 'education', 'skills', 'linkedin',
                         'profile', 'top skills', 'summary', 'recommendations', 'accomplishments',
                         'licenses', 'certifications', 'volunteer', 'publications', 'projects']
            
            if any(term in line_lower for term in skip_terms):
                continue
            
            # Skip lines that look like job titles or companies
            job_keywords = ['engineer', 'manager', 'director', 'analyst', 'consultant', 'developer',
                           'specialist', 'coordinator', 'assistant', 'lead', 'senior', 'junior',
                           'company', 'inc', 'ltd', 'corp', 'llc', 'university', 'college',
                           'executive', 'supervisor', 'administrator', 'technician', 'officer']
            
            if any(keyword in line_lower for keyword in job_keywords):
                continue
            
            # Skip lines with email, phone, or URL patterns
            if any(char in line for char in ['@', 'http', 'www', '+', '(', ')']):
                continue
            
            # Check if this line looks like a name
            if is_valid_name(line):
                return clean_name(line)
    
    # Strategy 3: Handle combined documents (Cover Letter + Resume)
    # Look for patterns like "MR. JOHN DOE", "MS. JANE SMITH", etc.
    for line in lines[:15]:
        # Pattern for formal titles with names
        title_pattern = r'^(?:MR\.?|MS\.?|MRS\.?|DR\.?|PROF\.?)\s+([A-Z][A-Z\s.]+)(?:\s*-|\s*--|\$)'
        match = re.search(title_pattern, line, re.IGNORECASE)
        if match:
            potential_name = match.group(1).strip()
            # Clean up and validate
            potential_name = re.sub(r'\s+', ' ', potential_name)  # Normalize spaces
            if is_valid_name(potential_name):
                return clean_name(potential_name)
    
    # Strategy 4: Traditional CV approach - first meaningful line
    for line in lines[:5]:
        if is_valid_name(line):
            return clean_name(line)
    
    # Strategy 5: Look for capitalized sequences that could be names
    for line in lines[:10]:
        # Look for 2-4 capitalized words
        words = line.split()
        if 2 <= len(words) <= 4:
            capitalized_words = [w for w in words if w and w[0].isupper() and w.isalpha()]
            if len(capitalized_words) >= 2 and len(capitalized_words) == len(words):
                candidate_name = ' '.join(capitalized_words)
                if is_valid_name(candidate_name):
                    return clean_name(candidate_name)
    
    # Strategy 6: Use AI to extract name as last resort
    try:
        # Take first 800 characters and ask AI to extract the name
        text_sample = text[:800]
        ai_extracted_name = extract_name_with_ai(text_sample)
        if ai_extracted_name and is_valid_name(ai_extracted_name):
            return clean_name(ai_extracted_name)
    except:
        pass  # Fall back to unknown if AI extraction fails
    
    # Fallback: Use first line if nothing else works
    return clean_name(lines[0]) if lines else "Unknown Candidate"


def is_valid_name(name_candidate):
    """Check if a string looks like a valid name"""
    if not name_candidate or not name_candidate.strip():
        return False
    
    name = name_candidate.strip()
    
    # Basic checks
    if len(name) < 2 or len(name) > 100:
        return False
    
    # Should not contain numbers
    if any(char.isdigit() for char in name):
        return False
    
    # Should not be common non-name words
    non_names = ['contact', 'about', 'experience', 'education', 'skills', 'profile', 'resume', 'cv',
                'curriculum', 'vitae', 'linkedin', 'email', 'phone', 'address', 'objective',
                'summary', 'unknown', 'candidate', 'applicant', 'top skills', 'recommendations',
                'accomplishments', 'certifications', 'volunteer', 'publications', 'projects',
                'suitability', 'leadership', 'role', 'position', 'job', 'employment', 'career']
    
    if name.lower() in non_names:
        return False
    
    # Should not contain job-related phrases
    job_phrases = ['business leadership', 'real estate', 'for real estate', 'leadership role',
                  'business development', 'account manager', 'sales manager', 'project manager']
    
    if any(phrase in name.lower() for phrase in job_phrases):
        return False
    
    # Should have at least 2 parts (first and last name) for most cases
    parts = name.split()
    if len(parts) < 2:
        # Allow single names only if they look very name-like
        if not (name[0].isupper() and name[1:].islower() and len(name) >= 4):
            return False
    
    # Each part should be mostly alphabetic
    for part in parts:
        if not part.replace('.', '').replace(',', '').replace('-', '').replace("'", '').isalpha():
            return False
    
    return True


def clean_name(name):
    """Clean and format extracted name"""
    if not name:
        return "Unknown Candidate"
    
    # Remove common prefixes and suffixes
    prefixes = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sir', 'madam']
    suffixes = ['cv', 'resume', 'curriculum vitae', 'profile', 'summary', 'profile summary']
    
    name = name.strip()
    name_lower = name.lower()
    
    # Remove prefixes
    for prefix in prefixes:
        if name_lower.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    
    # Remove suffixes
    for suffix in suffixes:
        if name_lower.endswith(suffix):
            name = name[:-len(suffix)].strip()
            break
    
    # Remove content after common separators
    separators = [' - ', ' -- ', ' | ', ' for ', ' cv', ' resume']
    for sep in separators:
        if sep in name.lower():
            name = name.split(sep)[0].strip()
            break
    
    # Title case the name
    words = name.split()
    cleaned_words = []
    for word in words:
        if word:
            # Handle names with apostrophes and hyphens
            if "'" in word or "-" in word:
                parts = re.split(r"([\'-])", word)
                title_parts = []
                for part in parts:
                    if part in ["'", "-"]:
                        title_parts.append(part)
                    else:
                        title_parts.append(part.capitalize())
                cleaned_words.append(''.join(title_parts))
            else:
                cleaned_words.append(word.capitalize())
    
    result = ' '.join(cleaned_words)
    return result if result else "Unknown Candidate"


def extract_name_with_ai(text_sample):
    """Use AI to extract name from text as last resort"""
    try:
        prompt = f"""Extract only the candidate's full name from this CV/resume text. Return only the name, nothing else.

Text: {text_sample}

Name:"""
        
        response = model.generate_content(prompt)
        extracted = response.text.strip()
        
        # Clean up AI response
        extracted = re.sub(r'^(name:|full name:|candidate name:)', '', extracted, flags=re.IGNORECASE).strip()
        extracted = extracted.replace('"', '').replace("'", '').strip()
        
        return extracted if extracted else None
    except:
        return None
