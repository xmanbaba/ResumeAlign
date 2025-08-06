"""
File handling utilities for ResumeAlign
Handles text extraction from PDF and DOCX files
"""

from PyPDF2 import PdfReader
from docx import Document


def extract_text(upload):
    """Extract text from uploaded PDF or DOCX file"""
    if not upload:
        return ""
    
    if upload.type == "application/pdf":
        return "\n".join(p.extract_text() or "" for p in PdfReader(upload).pages)
    
    if upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(upload).paragraphs)
    
    return ""


def create_safe_filename(candidate_name, filename, index):
    """Create a safe filename ensuring uniqueness"""
    import re
    
    if candidate_name and candidate_name != "Unknown Candidate":
        # Use candidate name as base
        base_name = candidate_name.replace(' ', '_')
    else:
        # Use original filename without extension
        base_name = filename.rsplit('.', 1)[0]
    
    # Remove unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
    safe_name = re.sub(r'[^\w\-_\.]', '_', safe_name)
    
    # Ensure uniqueness by adding index
    return f"Report_{index:02d}_{safe_name}.pdf"
