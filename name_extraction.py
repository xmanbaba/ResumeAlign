import re
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_name_from_text(text: str) -> str:
    """Extract candidate name from resume text using multiple strategies with improved consistency"""
    
    if not text:
        return "Unknown Candidate"
    
    # Clean the text
    text = text.strip()
    
    # Strategy 1: Look for explicit name patterns at the beginning
    name = try_explicit_patterns(text)
    if name and is_valid_name(name):
        logger.info(f"Name extracted using explicit patterns: {name}")
        return name
    
    # Strategy 2: Look for name in first few lines
    name = try_first_lines_extraction(text)
    if name and is_valid_name(name):
        logger.info(f"Name extracted from first lines: {name}")
        return name
    
    # Strategy 3: Look for email-based name extraction
    name = try_email_based_extraction(text)
    if name and is_valid_name(name):
        logger.info(f"Name extracted from email: {name}")
        return name
    
    # Strategy 4: Look for capitalized words pattern
    name = try_capitalized_pattern(text)
    if name and is_valid_name(name):
        logger.info(f"Name extracted using capitalized pattern: {name}")
        return name
    
    # Strategy 5: Look for structured resume patterns
    name = try_structured_patterns(text)
    if name and is_valid_name(name):
        logger.info(f"Name extracted using structured patterns: {name}")
        return name
    
    logger.warning("Could not extract name from resume text")
    return "Unknown Candidate"

def try_explicit_patterns(text: str) -> Optional[str]:
    """Try to extract name using explicit patterns"""
    lines = text.split('\n')
    first_lines = [line.strip() for line in lines[:5] if line.strip()]
    
    patterns = [
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*(?:\s+[A-Z][a-z]+)+)$',  # Full name pattern
        r'^Name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # "Name: John Doe"
        r'^([A-Z][A-Z\s]+)$',  # ALL CAPS names
        r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s|$)',  # Standard name format
    ]
    
    for line in first_lines:
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                name = match.group(1).strip()
                if len(name.split()) >= 2 and is_valid_name(name):  # Ensure we have at least first and last name
                    return format_name(name)
    
    return None

def try_first_lines_extraction(text: str) -> Optional[str]:
    """Extract name from the first few meaningful lines"""
    lines = text.split('\n')
    
    for i, line in enumerate(lines[:7]):  # Check first 7 lines
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        # Skip common resume headers and false positives
        if any(keyword in line.lower() for keyword in [
            'resume', 'cv', 'curriculum', 'profile', 'contact', 'real', 'document',
            'confidential', 'draft', 'version', 'page', 'template'
        ]):
            continue
        
        # Check if line looks like a name
        words = line.split()
        if 2 <= len(words) <= 4:  # Names typically have 2-4 parts
            if all(is_likely_name_word(word) for word in words):
                name = ' '.join(words)
                if is_valid_name(name):
                    return format_name(name)
    
    return None

def try_email_based_extraction(text: str) -> Optional[str]:
    """Extract name from email address"""
    email_pattern = r'\b([a-zA-Z0-9._%+-]+)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    matches = re.findall(email_pattern, text)
    
    for email_part in matches:
        # Split by common separators
        parts = re.split(r'[._-]+', email_part.lower())
        
        if len(parts) >= 2:
            # Capitalize each part and filter out common non-name parts
            name_parts = []
            for part in parts:
                if part.isalpha() and len(part) > 1 and not is_common_non_name_word(part):
                    name_parts.append(part.capitalize())
            
            if len(name_parts) >= 2:
                name = ' '.join(name_parts[:3])  # Take up to 3 parts
                if is_valid_name(name):
                    return format_name(name)
    
    return None

def try_capitalized_pattern(text: str) -> Optional[str]:
    """Look for capitalized word patterns that might be names"""
    lines = text.split('\n')[:10]  # Check first 10 lines
    
    for line in lines:
        line = line.strip()
        
        # Look for capitalized words at the start of a line
        pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)*(?:\s+[A-Z][a-z]+)+)'
        match = re.match(pattern, line)
        
        if match:
            potential_name = match.group(1).strip()
            words = potential_name.split()
            
            # Validate it looks like a name
            if 2 <= len(words) <= 4 and all(is_likely_name_word(word) for word in words):
                if is_valid_name(potential_name):
                    return format_name(potential_name)
    
    return None

def try_structured_patterns(text: str) -> Optional[str]:
    """Try to find names in structured resume formats"""
    # Common structured patterns in resumes
    patterns = [
        r'(?:PERSONAL\s+INFORMATION|PERSONAL\s+DETAILS)[:\s\n]+.*?(?:Name[:\s]+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'(?:CANDIDATE|APPLICANT)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'^([A-Z][A-Z\s]{10,30}),  # Long caps names (headers)
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            name = match.group(1).strip()
            if is_valid_name(name):
                return format_name(name)
    
    return None

def is_common_non_name_word(word: str) -> bool:
    """Check if a word is commonly used in non-name contexts"""
    common_words = {
        'real', 'test', 'demo', 'sample', 'template', 'draft', 'version',
        'copy', 'final', 'new', 'old', 'temp', 'backup', 'original',
        'email', 'mail', 'contact', 'info', 'admin', 'user', 'account'
    }
    return word.lower() in common_words

def is_likely_name_word(word: str) -> bool:
    """Check if a word is likely part of a person's name - ENHANCED"""
    word = word.strip('.,')
    
    # Skip if too short or too long
    if len(word) < 2 or len(word) > 20:
        return False
    
    # Skip if contains numbers
    if any(char.isdigit() for char in word):
        return False
    
    # ENHANCED: Skip common non-name words including "REAL"
    skip_words = {
        'resume', 'cv', 'curriculum', 'vitae', 'profile', 'contact', 'phone', 'email',
        'address', 'objective', 'summary', 'experience', 'education', 'skills',
        'references', 'available', 'upon', 'request', 'professional', 'personal',
        'information', 'details', 'background', 'qualifications', 'real', 'draft',
        'confidential', 'template', 'document', 'version', 'copy', 'sample',
        'test', 'demo', 'temporary', 'backup', 'original', 'final', 'new', 'old'
    }
    
    if word.lower() in skip_words:
        return False
    
    # Check for common false positive patterns
    false_positive_patterns = [
        r'^real,  # Specifically catch "REAL"
        r'^test\d*,  # test, test1, test2, etc.
        r'^sample\d*,  # sample, sample1, etc.
        r'^temp\d*,  # temp, temp1, etc.
        r'^draft\d*,  # draft, draft1, etc.
    ]
    
    for pattern in false_positive_patterns:
        if re.match(pattern, word.lower()):
            return False
    
    # Must start with capital letter and contain only letters and common name characters
    if not word[0].isupper():
        return False
    
    # Allow only letters and common name characters
    return all(char.isalpha() or char in "'-." for char in word)

def is_valid_name(name: str) -> bool:
    """Validate if the extracted text is likely a valid name - ENHANCED"""
    if not name or len(name.strip()) < 3:
        return False
    
    words = name.split()
    
    # Should have at least 2 words (first and last name)
    if len(words) < 2:
        return False
    
    # Should not have too many words (likely not a name if > 4 words)
    if len(words) > 4:
        return False
    
    # Each word should be a likely name word
    if not all(is_likely_name_word(word) for word in words):
        return False
    
    # ENHANCED: Check for common false positives including "REAL"
    name_lower = name.lower()
    false_positives = [
        'resume objective', 'curriculum vitae', 'personal information',
        'contact information', 'professional summary', 'work experience',
        'education background', 'technical skills', 'core competencies',
        'real estate', 'real time', 'real world', 'real life', 'real name',
        'test case', 'sample data', 'draft version', 'template file',
        'confidential document', 'original copy', 'final version'
    ]
    
    if any(fp in name_lower for fp in false_positives):
        return False
    
    # Additional check: reject if name contains only common false positive words
    false_positive_words = {'real', 'test', 'sample', 'draft', 'template', 'document'}
    name_words_lower = {word.lower() for word in words}
    if name_words_lower.issubset(false_positive_words):
        return False
    
    # Reject single-word false positives even if capitalized
    if len(words) == 1 and words[0].lower() in false_positive_words:
        return False
    
    return True

def format_name(name: str) -> str:
    """Format the name consistently"""
    if not name:
        return "Unknown Candidate"
    
    # Clean and format
    name = ' '.join(name.split())  # Remove extra whitespace
    name = re.sub(r'[^\w\s\'-.]', '', name)  # Remove unwanted characters
    
    # Title case each word
    words = []
    for word in name.split():
        # Handle special cases like O'Connor, McDonald, etc.
        if "'" in word:
            parts = word.split("'")
            word = "'".join([part.capitalize() for part in parts])
        elif word.lower().startswith('mc') and len(word) > 2:
            word = 'Mc' + word[2:].capitalize()
        else:
            word = word.capitalize()
        words.append(word)
    
    formatted_name = ' '.join(words)
    
    # Final validation
    if len(formatted_name) > 50:  # Suspiciously long name
        return "Unknown Candidate"
    
    # Final check against false positives
    if not is_valid_name(formatted_name):
        return "Unknown Candidate"
    
    return formatted_name

def extract_name_from_filename(filename: str) -> str:
    """Extract candidate name from filename as fallback"""
    if not filename:
        return "Unknown Candidate"
    
    # Remove file extension
    name_part = filename.rsplit('.', 1)[0]
    
    # Common filename patterns
    patterns = [
        r'^([A-Z][a-z]+[_\s-]+[A-Z][a-z]+)',  # FirstName_LastName or FirstName-LastName
        r'^([A-Z][a-z]+[_\s-]+[A-Z]\.[A-Z][a-z]+)',  # FirstName_M.LastName
        r'([A-Z][a-z]+[_\s-]+[A-Z][a-z]+)[_\s-](?:resume|cv)',  # Name_Resume
        r'(?:resume|cv)[_\s-]+([A-Z][a-z]+[_\s-]+[A-Z][a-z]+)',  # Resume_Name
    ]
    
    for pattern in patterns:
        match = re.search(pattern, name_part, re.IGNORECASE)
        if match:
            name = match.group(1)
            # Replace underscores and dashes with spaces
            name = re.sub(r'[_-]', ' ', name)
            formatted_name = format_name(name)
            if is_valid_name(formatted_name):
                logger.info(f"Name extracted from filename: {formatted_name}")
                return formatted_name
    
    # Fallback: try to clean the filename
    cleaned_name = re.sub(r'[_-]', ' ', name_part)
    cleaned_name = re.sub(r'(?i)(resume|cv|curriculum|vitae|real|test|sample|draft)', '', cleaned_name)
    cleaned_name = cleaned_name.strip()
    
    if cleaned_name and is_valid_name(cleaned_name):
        formatted_name = format_name(cleaned_name)
        logger.info(f"Name extracted from cleaned filename: {formatted_name}")
        return formatted_name
    
    logger.warning(f"Could not extract name from filename: {filename}")
    return "Unknown Candidate"

def get_name_confidence_score(name: str, text: str) -> float:
    """Calculate confidence score for extracted name"""
    if name == "Unknown Candidate":
        return 0.0
    
    confidence = 0.5  # Base confidence
    
    # Decrease confidence for suspicious names
    if any(word.lower() in ['real', 'test', 'sample', 'draft'] for word in name.split()):
        confidence -= 0.3
    
    # Increase confidence if name appears multiple times in text
    name_count = text.lower().count(name.lower())
    if name_count > 1:
        confidence += 0.2
    
    # Increase confidence if name has proper structure
    words = name.split()
    if len(words) == 2:  # First Last
        confidence += 0.2
    elif len(words) == 3:  # First Middle Last
        confidence += 0.15
    
    # Increase confidence if name appears near top of document
    first_200_chars = text[:200].lower()
    if name.lower() in first_200_chars:
        confidence += 0.15
    
    return min(confidence, 1.0)
