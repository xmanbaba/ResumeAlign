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
        'top skills', 'licenses', 'certifications', 'volunteer',
        'publications', 'contact info', 'summary'
    ]
    
    first_few_lines = ' '.join(lines[:8]).lower()
    indicator_count = sum(1 for indicator in linkedin_indicators if indicator in first_few_lines)
    
    return indicator_count >= 2


def extract_name_from_linkedin(lines):
    """Extract name specifically from LinkedIn profile content"""
    skip_terms = [
        'contact', 'about', 'experience', 'education', 'skills', 'linkedin',
        'profile', 'top skills', 'summary', 'recommendations', 'accomplishments',
        'licenses', 'certifications', 'volunteer', 'publications', 'projects',
        'activity', 'interests', 'honors', 'awards', 'courses', 'languages'
    ]
    
    job_keywords = [
        'engineer', 'manager', 'director', 'analyst', 'consultant', 'developer',
        'specialist', 'coordinator', 'assistant', 'lead', 'senior', 'junior',
        'company', 'inc', 'ltd', 'corp', 'llc', 'university', 'college',
        'executive', 'supervisor', 'administrator', 'technician', 'officer',
        'founder', 'ceo', 'cto', 'cfo', 'president', 'vice', 'head'
    ]
    
    for i, line in enumerate(lines[:25]):  # Extended search for LinkedIn
        line_lower = line.lower().strip()
        
        # Skip empty lines
        if not line_lower:
            continue
            
        # Skip obvious navigation/section headers
        if any(term in line_lower for term in skip_terms):
            continue
        
        # Skip lines that look like job titles or companies
        if any(keyword in line_lower for keyword in job_keywords):
            continue
        
        # Skip lines with contact info patterns
        if any(char in line for char in ['@', 'http', 'www', '+', '(', ')', '.com', '.org']):
            continue
            
        # Skip lines with numbers (likely dates, phone numbers, etc.)
        if re.search(r'\d{2,}', line):
            continue
        
        # Check if this line looks like a name
        if is_valid_name(line.strip()):
            return clean_name(line.strip())
    
    return None


def is_valid_name(name_candidate):
    """Enhanced validation to check if a string looks like a valid name"""
    if not name_candidate or not name_candidate.strip():
        return False
    
    name = name_candidate.strip()
    
    # Basic length checks
    if len(name) < 2 or len(name) > 100:
        return False
    
    # Should not contain numbers
    if re.search(r'\d', name):
        return False
    
    # Should not be common non-name words/phrases
    non_names = [
        'contact', 'about', 'experience', 'education', 'skills', 'profile', 'resume', 'cv',
        'curriculum', 'vitae', 'linkedin', 'email', 'phone', 'address', 'objective',
        'summary', 'unknown', 'candidate', 'applicant', 'top skills', 'recommendations',
        'accomplishments', 'certifications', 'volunteer', 'publications', 'projects',
        'suitability', 'leadership', 'role', 'position', 'job', 'employment', 'career',
        'professional', 'expert', 'specialist', 'consultant', 'manager', 'director',
        'personal', 'information', 'details', 'overview', 'background', 'qualification'
    ]
    
    if name.lower() in non_names:
        return False
    
    # Should not contain job-related phrases
    job_phrases = [
        'business leadership', 'real estate', 'for real estate', 'leadership role',
        'business development', 'account manager', 'sales manager', 'project manager',
        'human resources', 'information technology', 'customer service', 'data analyst',
        'software engineer', 'marketing specialist', 'financial advisor'
    ]
    
    if any(phrase in name.lower() for phrase in job_phrases):
        return False
    
    # Check word structure
    parts = name.split()
    
    # Single word names - stricter validation
    if len(parts) == 1:
        word = parts[0]
        # Must be properly capitalized and reasonable length
        if not (word[0].isupper() and word[1:].islower() and 3 <= len(word) <= 20):
            return False
        # Should not be common single words
        common_words = ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'they', 'have', 'will']
        if word.lower() in common_words:
            return False
    
    # Multiple word names
    elif len(parts) >= 2:
        # Each part should be mostly alphabetic with proper capitalization
        for part in parts:
            clean_part = part.replace('.', '').replace(',', '').replace('-', '').replace("'", '')
            if not clean_part:
                continue
            if not clean_part.isalpha():
                return False
            # Should start with capital letter
            if not part[0].isupper():
                return False
    
    # Additional validation: should look like a real name
    # Names typically have vowels
    vowel_count = sum(1 for char in name.lower() if char in 'aeiou')
    if vowel_count == 0:
        return False
    
    return True


def clean_name(name):
    """Enhanced name cleaning and formatting"""
    if not name:
        return "Unknown Candidate"
    
    # Remove common prefixes and suffixes
    prefixes = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sir', 'madam', 'miss']
    suffixes = ['cv', 'resume', 'curriculum vitae', 'profile', 'summary', 'profile summary', 'bio']
    
    name = name.strip()
    name_lower = name.lower()
    
    # Remove prefixes
    for prefix in prefixes:
        if name_lower.startswith(prefix + ' '):
            name = name[len(prefix):].strip()
            name_lower = name.lower()
            break
    
    # Remove suffixes
    for suffix in suffixes:
        if name_lower.endswith(' ' + suffix):
            name = name[:-len(suffix)].strip()
            break
    
    # Remove content after common separators
    separators = [' - ', ' -- ', ' | ', ' for ', ' cv', ' resume', '\n', '\t']
    for sep in separators:
        if sep in name.lower():
            name = name.split(sep)[0].strip()
            break
    
    # Clean up extra whitespace
    name = re.sub(r'\s+', ' ', name)
    
    # Remove special characters except apostrophes and hyphens in names
    name = re.sub(r'[^\w\s\'-]', '', name)
    
    # Title case the name properly
    words = name.split()
    cleaned_words = []
    
    for word in words:
        if not word:
            continue
            
        # Handle names with apostrophes and hyphens (e.g., O'Connor, Mary-Jane)
        if "'" in word or "-" in word:
            parts = re.split(r"([\'-])", word)
            title_parts = []
            for part in parts:
                if part in ["'", "-"]:
                    title_parts.append(part)
                elif part:
                    title_parts.append(part.capitalize())
            cleaned_words.append(''.join(title_parts))
        else:
            cleaned_words.append(word.capitalize())
    
    result = ' '.join(cleaned_words)
    
    # Final validation
    if not result or not is_valid_name(result):
        return "Unknown Candidate"
    
    return result


def extract_name_with_ai(text_sample):
    """Use AI to extract name from text with improved prompting"""
    try:
        prompt = f"""Extract ONLY the candidate's full name from this CV/resume text. Look for the person's actual name, not job titles or company names.

The name should be a person's first and last name (and possibly middle name).

Text: {text_sample[:800]}

Instructions:
- Return ONLY the person's name
- Do not include titles like Mr., Dr., etc.
- Do not include job titles
- Do not include company names
- If you cannot find a clear name, return "Unknown"

Name:"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,  # Very low temperature for consistency
                max_output_tokens=50,
            )
        )
        
        extracted = response.text.strip()
        
        # Clean up AI response
        extracted = re.sub(r'^(name:|full name:|candidate name:)', '', extracted, flags=re.IGNORECASE).strip()
        extracted = extracted.replace('"', '').replace("'", '').strip()
        extracted = extracted.replace('Unknown', '').strip()
        
        return extracted if extracted and extracted != "Unknown" else None
        
    except Exception as e:
        print(f"AI name extraction error: {e}")
        return None
