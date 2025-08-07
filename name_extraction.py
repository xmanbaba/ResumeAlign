import re
from typing import Optional

def extract_candidate_name(resume_text: str) -> Optional[str]:
    """
    Extract candidate name from resume text using various patterns
    """
    if not resume_text:
        return None
    
    lines = resume_text.strip().split('\n')
    
    # Pattern 1: Look for name in first few lines
    for i, line in enumerate(lines[:5]):
        line = line.strip()
        if not line:
            continue
            
        # Skip common headers
        skip_patterns = [
            r'resume', r'cv', r'curriculum vitae', 
            r'contact', r'email', r'phone', r'address'
        ]
        
        if any(re.search(pattern, line.lower()) for pattern in skip_patterns):
            continue
        
        # Look for name pattern (2-4 words, mostly alphabetic)
        words = line.split()
        if 2 <= len(words) <= 4:
            # Check if words are mostly alphabetic
            if all(word.replace('.', '').replace(',', '').isalpha() 
                   for word in words if len(word) > 1):
                return line.title()
    
    # Pattern 2: Look for "Name:" label
    name_pattern = r'(?i)name\s*[:]\s*([A-Za-z\s.]+)'
    match = re.search(name_pattern, resume_text)
    if match:
        return match.group(1).strip().title()
    
    # Pattern 3: Extract from email if present
    email_pattern = r'([a-zA-Z.]+)@'
    email_match = re.search(email_pattern, resume_text)
    if email_match:
        email_name = email_match.group(1)
        # Convert email format to proper name
        name_parts = email_name.replace('.', ' ').split()
        if len(name_parts) >= 2:
            return ' '.join(word.title() for word in name_parts[:2])
    
    return "Candidate"

def format_candidate_name(name: str) -> str:
    """Format candidate name for consistency"""
    if not name:
        return "Candidate"
    
    # Remove extra whitespace and format
    formatted_name = ' '.join(name.split()).title()
    
    # Handle common name patterns
    formatted_name = re.sub(r'\b(Mc|Mac)([a-z])', 
                           lambda m: m.group(1) + m.group(2).upper(), 
                           formatted_name)
    
    return formatted_name if formatted_name else "Candidate"
