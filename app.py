# app.py -- ResumeAlign v1.4 with Enhanced UI/UX Design

import os, json, streamlit as st
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.colors import blue
from reportlab.lib.enums import TA_CENTER
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import zipfile
import time
import re

# ---------- CONFIG ----------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

def extract_text(upload):
    if not upload:
        return ""
    if upload.type == "application/pdf":
        return "\n".join(p.extract_text() or "" for p in PdfReader(upload).pages)
    if upload.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join(p.text for p in Document(upload).paragraphs)
    return ""

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

def create_safe_filename(candidate_name, filename, index):
    """Create a safe filename ensuring uniqueness"""
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

def build_pdf(report, linkedin_url="", candidate_name="", extracted_from_cv=False):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)
    
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.drawCentredString(A4[0] / 2, 0.75 * inch, f"© 2025 ResumeAlign -- AI Resume & CV Analyzer | Page {doc.page}")
        canvas.restoreState()
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=16, spaceAfter=12, textColor=blue)
    normal_style = ParagraphStyle("Normal", fontSize=11, spaceAfter=6)
    
    # Use the provided candidate name, or extract from summary as fallback
    if not candidate_name and 'candidate_summary' in report:
        candidate_name = report.get('candidate_summary', '').split(' is ')[0] if ' is ' in report.get('candidate_summary', '') else "Unknown Candidate"
    elif not candidate_name:
        candidate_name = "Unknown Candidate"
    
    story = [
        Paragraph("ResumeAlign Analysis Report", title_style),
        Paragraph(f"<b>Name of Candidate:</b> {candidate_name}", normal_style),
        Paragraph(f"<b>Review Date:</b> {datetime.now():%d %B %Y}", normal_style),
    ]
    
    if linkedin_url:
        story.append(Paragraph(f"<b>LinkedIn URL:</b> {linkedin_url}", normal_style))
    
    story.extend([
        Paragraph(f"<b>Alignment Score:</b> {report['alignment_score']} / 10", title_style),
        Paragraph(f"<b>Experience Estimate:</b> {report['experience_years']['raw_estimate']} ({report['experience_years']['confidence']} confidence)", normal_style),
        Paragraph("<b>Summary:</b>", title_style),
        Paragraph(report.get("candidate_summary", ""), normal_style),
        Paragraph("<b>Strengths:</b>", title_style),
    ])
    
    for s in report.get("strengths", []):
        story.append(Paragraph(f"• {s}", normal_style))
    
    story.append(Paragraph("<b>Areas for Improvement:</b>", title_style))
    for a in report.get("areas_for_improvement", []):
        story.append(Paragraph(f"• {a}", normal_style))
    
    story.append(Paragraph("<b>Interview Questions:</b>", title_style))
    for i, q in enumerate(report.get("suggested_interview_questions", []), 1):
        story.append(Paragraph(f"{i}. {q}", normal_style))
    
    story.append(Paragraph("<b>Recommendation:</b>", title_style))
    story.append(Paragraph(report.get("next_round_recommendation", ""), normal_style))
    
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

def create_batch_zip(reports, job_desc):
    """Create a ZIP file containing all batch reports with improved filename handling"""
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Track used filenames to avoid duplicates
        used_filenames = set()
        
        # Add individual PDF reports
        for i, report_data in enumerate(reports, 1):
            report = report_data['report']
            filename = report_data['filename']
            candidate_name = report_data['candidate_name']
            
            # Generate PDF
            pdf_buffer = build_pdf(report, candidate_name=candidate_name, extracted_from_cv=True)
            
            # Create safe, unique filename
            safe_filename = create_safe_filename(candidate_name, filename, i)
            
            # Ensure uniqueness
            counter = 1
            original_safe_filename = safe_filename
            while safe_filename in used_filenames:
                base_name = original_safe_filename.rsplit('.', 1)[0]
                safe_filename = f"{base_name}_v{counter}.pdf"
                counter += 1
            
            used_filenames.add(safe_filename)
            
            # Add to ZIP
            zip_file.writestr(safe_filename, pdf_buffer.read())
            
            # Debug logging
            print(f"Added to ZIP: {safe_filename} (Original: {filename}, Name: {candidate_name})")
        
        # Add summary JSON
        summary = {
            "job_description": job_desc,
            "analysis_date": datetime.now().strftime("%d %B %Y"),
            "total_candidates": len(reports),
            "candidates": [
                {
                    "candidate_name": r['candidate_name'],
                    "filename": r['filename'],
                    "alignment_score": r['report']['alignment_score'],
                    "recommendation": r['report']['next_round_recommendation'],
                    "experience": r['report']['experience_years']['raw_estimate']
                } for r in reports
            ]
        }
        
        zip_file.writestr("batch_summary.json", json.dumps(summary, indent=2))
    
    zip_buffer.seek(0)
    return zip_buffer

SYSTEM_PROMPT = "Use only the text provided. Return valid JSON matching the schema."

def build_prompt(jd, profile_text, file_text):
    extra = file_text.strip() if file_text.strip() else "None provided"
    return (
        "Job Description:\n" + jd + "\n\n"
        "Candidate Profile / CV:\n" + profile_text + "\n\n"
        "Extra File Text:\n" + extra + "\n\n"
        "Return valid JSON:\n"
        "{\n"
        ' "alignment_score": <0-10>,\n'
        ' "experience_years": {"raw_estimate": "<string>", "confidence": "<High|Medium|Low>", "source": "<Manual text|File>"},\n'
        ' "candidate_summary": "<300 words>",\n'
        ' "areas_for_improvement": ["<string>","<string>","<string>","<string>","<string>"],\n'
        ' "strengths": ["<string>","<string>","<string>","<string>","<string>"],\n'
        ' "suggested_interview_questions": ["<string>","<string>","<string>","<string>","<string>"],\n'
        ' "next_round_recommendation": "<Yes|No|Maybe -- brief reason>",\n'
        ' "sources_used": ["Manual text","File"]\n'
        '}'
    )

def analyze_single_candidate(job_desc, profile_text, file_text=""):
    """Analyze a single candidate and return the report"""
    prompt = build_prompt(job_desc, profile_text, file_text)
    
    try:
        response = model.generate_content([SYSTEM_PROMPT, prompt])
        report = json.loads(response.text.strip("```json").strip("```"))
        return report, None
    except Exception as e:
        return None, str(e)

def apply_custom_css():
    """Apply modern CSS styling with ResumeAlign brand colors"""
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: #ffffff;
        min-height: 100vh;
    }
    
    /* Main Container */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        margin: 0 auto;
        background: #ffffff;
    }
    
    /* Header Styling */
    .main-header {
        background: #ffffff;
        border: 2px solid #E53E3E;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(229, 62, 62, 0.1);
    }
    
    .main-title {
        background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-subtitle {
        text-align: center;
        color: #2D3748;
        font-size: 1.2rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    /* Card Styling */
    .analysis-card {
        background: #ffffff;
        border: 2px solid #f7fafc;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(45, 55, 72, 0.08);
        transition: all 0.3s ease;
    }
    
    .analysis-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(45, 55, 72, 0.12);
        border-color: #E53E3E;
    }
    
    /* Mode Selector */
    .stRadio > label {
        background: #ffffff;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stRadio > label:hover {
        border-color: #E53E3E;
        background: rgba(229, 62, 62, 0.05);
    }
    
    /* Form Elements */
    .stTextArea textarea, .stTextInput input {
        border: 2px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        background: #ffffff !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #E53E3E !important;
        box-shadow: 0 0 0 3px rgba(229, 62, 62, 0.1) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(229, 62, 62, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(229, 62, 62, 0.4) !important;
        background: linear-gradient(135deg, #C53030 0%, #E53E3E 100%) !important;
    }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2D3748 0%, #1A202C 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(45, 55, 72, 0.3) !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(45, 55, 72, 0.4) !important;
        background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%) !important;
    }
    
    /* File Uploader */
    .stFileUploader {
        background: #ffffff;
        border: 2px dashed #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #E53E3E;
        background: rgba(229, 62, 62, 0.02);
    }
    
    /* Metrics */
    .stMetric {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(45, 55, 72, 0.05);
    }
    
    /* Progress Bar */
    .stProgress .css-1cpxqw2 {
        background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%);
        border-radius: 10px;
    }
    
    /* Info/Success/Error Messages */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 2px 10px rgba(45, 55, 72, 0.08);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #ffffff;
    }
    
    /* Tables */
    .stTable {
        background: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(45, 55, 72, 0.05);
        border: 1px solid #e2e8f0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        font-weight: 600;
        color: #2D3748;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #E53E3E;
        background: rgba(229, 62, 62, 0.02);
    }
    
    /* LinkedIn Helper Section */
    .linkedin-section {
        background: rgba(0, 119, 181, 0.05);
        border: 2px solid rgba(0, 119, 181, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Link Button Styling */
    .stLinkButton > a {
        background: linear-gradient(135deg, #0077b5 0%, #005582 100%) !important;
        color: white !important;
        text-decoration: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        display: block !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(0, 119, 181, 0.3) !important;
    }
    
    .stLinkButton > a:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(0, 119, 181, 0.4) !important;
    }
    
    /* Popover Styling */
    .stPopover {
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(45, 55, 72, 0.15);
        border: 1px solid #e2e8f0;
        background: #ffffff;
    }
    
    /* Animation for loading */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .stSpinner {
        animation: pulse 2s ease-in-out infinite;
    }
    
    /* Custom spacing */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Clear Button Styling */
    .clear-button {
        background: linear-gradient(135deg, #718096 0%, #4A5568 100%) !important;
    }
    
    .clear-button:hover {
        background: linear-gradient(135deg, #4A5568 0%, #718096 100%) !important;
    }
    
    /* Success/Error Styling */
    .stSuccess {
        background: rgba(72, 187, 120, 0.1);
        border-left: 4px solid #48bb78;
        color: #22543d;
    }
    
    .stError {
        background: rgba(229, 62, 62, 0.1);
        border-left: 4px solid #E53E3E;
        color: #742a2a;
    }
    
    .stInfo {
        background: rgba(49, 130, 206, 0.1);
        border-left: 4px solid #3182ce;
        color: #2c5aa0;
    }
    
    .stWarning {
        background: rgba(237, 137, 54, 0.1);
        border-left: 4px solid #ed8936;
        color: #9c4221;
    }
    
    /* Remove default Streamlit branding adjustments */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

def clear_session():
    """Clear all session state data"""
    keys_to_clear = ["last_report", "linkedin_url", "batch_reports", "batch_job_desc"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# ---------- UI ----------
st.set_page_config(
    page_title="ResumeAlign - AI Resume Analyzer", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🎯"
)

# Apply custom CSS
apply_custom_css()

# Header Section
st.markdown("""
<div class="main-header">
    <h1 class="main-title">ResumeAlign</h1>
    <p class="main-subtitle">AI-Powered Resume & CV Analysis Platform</p>
</div>
""", unsafe_allow_html=True)

# Clear Session Button with custom styling
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("🔄 Clear Session", help="Clear all data and start fresh", key="clear_btn"):
        clear_session()
        st.rerun()

# Add custom CSS for clear button
st.markdown("""
<style>
[data-testid="stButton"][data-baseweb="button"] button[kind="secondary"]:has-text("🔄 Clear Session") {
    background: linear-gradient(135deg, #718096 0%, #4A5568 100%) !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# Add mode selector with enhanced styling
st.markdown("""
<div class="analysis-card">
    <h3 style="color: #1e293b; margin-bottom: 1rem; font-weight: 600;">Choose Analysis Mode</h3>
</div>
""", unsafe_allow_html=True)

analysis_mode = st.radio(
    "",
    ["🧑‍💼 Single Candidate Analysis", "📁 Batch Processing (up to 5 files)"],
    horizontal=True,
    label_visibility="collapsed"
)

if analysis_mode == "🧑‍💼 Single Candidate Analysis":
    # Single candidate interface with enhanced design
    st.markdown("""
    <div class="analysis-card">
        <h3 style="color: #1e293b; margin-bottom: 1rem; font-weight: 600;">🔗 LinkedIn Profile Helper</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # LinkedIn helper section
    st.markdown('<div class="linkedin-section">', unsafe_allow_html=True)
    
    with st.popover("ℹ️ How to use LinkedIn URL", use_container_width=False):
        st.markdown("""
        **Step-by-step Guide:**
        
        1. **Paste LinkedIn URL** - The URL is automatically detected
        2. **Click 'Save to PDF'** - Opens the exact profile page  
        3. **On LinkedIn page** - Click **More → Save to PDF**
        4. **Upload PDF** - Upload the downloaded PDF file
        
        💡 **Tip:** This method provides the most accurate analysis!
        """)
    
    col1, col2 = st.columns([4, 2])
    with col1:
        profile_url = st.text_input(
            "LinkedIn Profile URL", 
            placeholder="https://linkedin.com/in/candidate-name",
            help="Paste the candidate's LinkedIn profile URL here"
        )
    
    with col2:
        target = profile_url.strip() if profile_url.strip() else "https://linkedin.com"
        st.link_button("📱 Open LinkedIn Profile", target, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Copy-paste guide
    with st.popover("📋 Manual Copy-Paste Guide", use_container_width=False):
        st.markdown("""
        **Essential LinkedIn Sections to Copy:**
        
        ✅ **Name & Professional Headline**  
        ✅ **About Section** (complete summary)  
        ✅ **Experience** (all positions with descriptions)  
        ✅ **Skills & Endorsements**  
        ✅ **Education** (degrees, institutions, dates)  
        ✅ **Certifications & Licenses**  
        
        **Pro Tips:**
        - Copy each section completely for better analysis
        - Include job descriptions and achievements
        - Don't forget skills and endorsements
        """)
    
    # Main analysis form
    st.markdown("""
    <div class="analysis-card">
        <h3 style="color: #1e293b; margin-bottom: 1rem; font-weight: 600;">📊 Candidate Analysis</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("single_analyzer", clear_on_submit=False):
        job_desc = st.text_area(
            "📝 Job Description", 
            height=250,
            placeholder="Paste the complete job description here...\n\nInclude:\n• Job title and department\n• Key responsibilities\n• Required qualifications\n• Preferred skills\n• Experience requirements",
            help="Paste the full job description for accurate matching analysis"
        )
        
        profile_text = st.text_area(
            "👤 Candidate Profile / LinkedIn Text", 
            height=300,
            placeholder="Paste the candidate's LinkedIn profile or CV text here...\n\nInclude all relevant sections:\n• Professional summary\n• Work experience\n• Skills and endorsements\n• Education and certifications",
            help="Copy and paste text from LinkedIn profile or CV"
        )
        
        uploaded_file = st.file_uploader(
            "📎 Or Upload CV/Resume File (Optional)", 
            type=["pdf", "docx"],
            help="Upload a PDF or Word document instead of copy-pasting text"
        )
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submitted = st.form_submit_button("🚀 Analyze Candidate", type="primary", use_container_width=True)
    
    if submitted:
        if not job_desc.strip():
            st.error("❌ Job Description is required for analysis.")
            st.stop()
        
        if not profile_text.strip() and not uploaded_file:
            st.error("❌ Please provide either candidate text or upload a CV file.")
            st.stop()
        
        # Extract file text if uploaded
        file_text = extract_text(uploaded_file) if uploaded_file else ""
        
        # Show processing animation
        with st.spinner("🤖 AI is analyzing the candidate profile..."):
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            report, error = analyze_single_candidate(job_desc, profile_text, file_text)
        
        if error:
            st.error(f"❌ Analysis error: {error}")
            st.stop()
        
        # Store results
        st.session_state["last_report"] = report
        st.session_state["linkedin_url"] = profile_url.strip()
        
        st.success("✅ Analysis completed successfully!")

else:
    # Batch processing interface with enhanced design
    st.markdown("""
    <div class="analysis-card">
        <h3 style="color: #1e293b; margin-bottom: 1rem; font-weight: 600;">📁 Batch Processing Mode</h3>
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%); 
                    padding: 1rem; border-radius: 12px; border-left: 4px solid #3b82f6;">
            <p style="margin: 0; color: #1e40af; font-weight: 500;">
                📋 Upload up to 5 CV files (PDF/DOCX) for batch analysis against a single job description.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("batch_analyzer", clear_on_submit=False):
        job_desc = st.text_area(
            "📝 Job Description", 
            height=250,
            placeholder="Paste the complete job description here...\n\nThis will be used to analyze all uploaded CVs",
            help="All CV files will be analyzed against this job description"
        )
        
        uploaded_files = st.file_uploader(
            "📎 Upload CV Files (PDF / DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Select up to 5 CV files for batch processing"
        )
        
        if uploaded_files:
            st.info(f"📄 **{len(uploaded_files)} files selected:** {', '.join([f.name for f in uploaded_files])}")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            batch_submitted = st.form_submit_button("🚀 Analyze Batch", type="primary", use_container_width=True)
    
    if batch_submitted:
        if not job_desc.strip():
            st.error("❌ Job Description is required for batch analysis.")
            st.stop()
        
        if not uploaded_files:
            st.error("❌ Please upload at least one CV file.")
            st.stop()
        
        if len(uploaded_files) > 5:
            st.error("❌ Maximum 5 files allowed for batch processing.")
            st.stop()
        
        # Process batch with enhanced UI
        batch_reports = []
        
        # Create progress tracking
        progress_container = st.container()
        with progress_container:
            st.markdown("### 🔄 Processing Files...")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process each file
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.markdown(f"**Processing:** `{uploaded_file.name}` ({i+1}/{len(uploaded_files)})")
                
                file_text = extract_text(uploaded_file)
                if not file_text.strip():
                    st.warning(f"⚠️ Could not extract text from `{uploaded_file.name}`. Skipping...")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    continue
                
                # Analyze with AI
                with st.spinner(f"🤖 AI analyzing {uploaded_file.name}..."):
                    report, error = analyze_single_candidate(job_desc, "", file_text)
                
                if error:
                    st.error(f"❌ Error analyzing `{uploaded_file.name}`: {error}")
                    progress_bar.progress((i + 1) / len(uploaded_files))
                    continue
                
                # Extract candidate name
                candidate_name = extract_candidate_name_from_ai_report(report)
                if not candidate_name or candidate_name == "Unknown Candidate":
                    candidate_name = extract_candidate_name(file_text)
                
                # Show extraction result
                st.success(f"✅ **Processed:** `{uploaded_file.name}` → **Candidate:** `{candidate_name}`")
                
                batch_reports.append({
                    'report': report,
                    'filename': uploaded_file.name,
                    'candidate_name': candidate_name
                })
                
                progress_bar.progress((i + 1) / len(uploaded_files))
                time.sleep(0.3)  # Small delay for better UX
            
            status_text.markdown("✅ **Batch processing completed!**")
        
        if batch_reports:
            st.session_state["batch_reports"] = batch_reports
            st.session_state["batch_job_desc"] = job_desc

# Display results for single candidate
if "last_report" in st.session_state and analysis_mode == "🧑‍💼 Single Candidate Analysis":
    report = st.session_state["last_report"]
    
    st.markdown("""
    <div class="analysis-card">
        <h3 style="color: #059669; margin-bottom: 1rem; font-weight: 600;">✅ Analysis Results</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Download buttons
    col1, col2 = st.columns(2)
    with col1:
        pdf_data = build_pdf(report, st.session_state.get("linkedin_url", ""))
        st.download_button(
            "📄 Download PDF Report", 
            data=pdf_data, 
            file_name=f"ResumeAlign_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", 
            mime="application/pdf",
            use_container_width=True
        )
    
    with col2:
        st.download_button(
            "💾 Download JSON Data", 
            data=json.dumps(report, indent=2), 
            file_name=f"ResumeAlign_Data_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 
            mime="application/json",
            use_container_width=True
        )
    
    # Results display
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    
    # Score display
    score = report['alignment_score']
    percentage = int((score / 10) * 100)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Alignment Score", f"{percentage}%", f"{score}/10")
    with col2:
        experience = report['experience_years']['raw_estimate']
        confidence = report['experience_years']['confidence']
        st.metric("💼 Experience Level", experience, f"{confidence} confidence")
    with col3:
        recommendation = report['next_round_recommendation'].split(' - ')[0] if ' - ' in report['next_round_recommendation'] else report['next_round_recommendation']
        st.metric("📋 Recommendation", recommendation)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Detailed analysis
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### 📝 **Candidate Summary**")
    st.write(report["candidate_summary"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Strengths and improvements
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.markdown("### ✅ **Key Strengths**")
        for i, strength in enumerate(report["strengths"], 1):
            st.markdown(f"**{i}.** {strength}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.markdown("### 🎯 **Areas for Development**")
        for i, area in enumerate(report["areas_for_improvement"], 1):
            st.markdown(f"**{i}.** {area}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Interview questions
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### 🤔 **Suggested Interview Questions**")
    for i, question in enumerate(report["suggested_interview_questions"], 1):
        st.markdown(f"**{i}.** {question}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Final recommendation
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### 🎯 **Final Recommendation**")
    st.markdown(f"**Decision:** {report['next_round_recommendation']}")
    st.markdown('</div>', unsafe_allow_html=True)

# Display results for batch processing
if "batch_reports" in st.session_state and analysis_mode == "📁 Batch Processing (up to 5 files)":
    batch_reports = st.session_state["batch_reports"]
    job_desc = st.session_state["batch_job_desc"]
    
    st.markdown(f"""
    <div class="analysis-card">
        <h3 style="color: #059669; margin-bottom: 1rem; font-weight: 600;">
            ✅ Batch Analysis Complete - {len(batch_reports)} Candidates Processed
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Download options
    col1, col2 = st.columns(2)
    with col1:
        zip_data = create_batch_zip(batch_reports, job_desc)
        st.download_button(
            "📦 Download All Reports (ZIP)",
            data=zip_data,
            file_name=f"ResumeAlign_Batch_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
            use_container_width=True
        )
    
    with col2:
        summary_json = {
            "job_description": job_desc,
            "analysis_date": datetime.now().strftime("%d %B %Y"),
            "total_candidates": len(batch_reports),
            "candidates": [
                {
                    "candidate_name": r['candidate_name'],
                    "filename": r['filename'],
                    "alignment_score": r['report']['alignment_score'],
                    "alignment_percentage": int((r['report']['alignment_score'] / 10) * 100),
                    "recommendation": r['report']['next_round_recommendation'],
                    "experience": r['report']['experience_years']['raw_estimate']
                } for r in batch_reports
            ]
        }
        
        st.download_button(
            "📊 Download Summary (JSON)",
            data=json.dumps(summary_json, indent=2),
            file_name=f"ResumeAlign_Summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    # Summary overview
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### 📊 **Batch Results Overview**")
    
    # Create enhanced summary data
    summary_data = []
    for i, report_data in enumerate(batch_reports, 1):
        report = report_data['report']
        candidate_name = report_data['candidate_name']
        filename = report_data['filename']
        
        display_name = candidate_name if candidate_name != "Unknown Candidate" else filename
        score = report['alignment_score']
        percentage = int((score / 10) * 100)
        
        # Determine status emoji based on score
        if percentage >= 80:
            status = "🟢 Excellent"
        elif percentage >= 60:
            status = "🟡 Good"
        elif percentage >= 40:
            status = "🟠 Fair"
        else:
            status = "🔴 Poor"
        
        summary_data.append({
            "Rank": f"#{i}",
            "Candidate": display_name,
            "Score": f"{percentage}%",
            "Status": status,
            "Experience": report['experience_years']['raw_estimate'],
            "Recommendation": report['next_round_recommendation'].split(' - ')[0] if ' - ' in report['next_round_recommendation'] else report['next_round_recommendation']
        })
    
    # Sort by score descending
    summary_data.sort(key=lambda x: int(x["Score"].replace('%', '')), reverse=True)
    for i, item in enumerate(summary_data, 1):
        item["Rank"] = f"#{i}"
    
    st.dataframe(summary_data, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Individual candidate details
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### 👥 **Individual Candidate Reports**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    for i, report_data in enumerate(batch_reports, 1):
        report = report_data['report']
        filename = report_data['filename']
        candidate_name = report_data['candidate_name']
        
        display_name = candidate_name if candidate_name != "Unknown Candidate" else filename
        score = report['alignment_score']
        percentage = int((score / 10) * 100)
        
        # Status indicator
        if percentage >= 80:
            indicator = "🟢"
        elif percentage >= 60:
            indicator = "🟡"
        elif percentage >= 40:
            indicator = "🟠"
        else:
            indicator = "🔴"
        
        with st.expander(f"{indicator} **{display_name}** ({percentage}%) - {filename}", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🎯 Alignment", f"{percentage}%")
            with col2:
                st.metric("💼 Experience", report['experience_years']['raw_estimate'])
            with col3:
                recommendation = report['next_round_recommendation'].split(' - ')[0] if ' - ' in report['next_round_recommendation'] else report['next_round_recommendation']
                st.metric("📋 Decision", recommendation)
            
            st.markdown("**📝 Summary:**")
            st.write(report["candidate_summary"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**✅ Strengths:**")
                for strength in report["strengths"]:
                    st.markdown(f"• {strength}")
            
            with col2:
                st.markdown("**🎯 Development Areas:**")
                for area in report["areas_for_improvement"]:
                    st.markdown(f"• {area}")
            
            st.markdown("**🤔 Interview Questions:**")
            for j, question in enumerate(report["suggested_interview_questions"], 1):
                st.markdown(f"{j}. {question}")
            
            st.markdown("**🎯 Final Recommendation:**")
            st.info(report['next_round_recommendation'])

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #64748b; font-size: 0.9rem;">
    <p>© 2025 ResumeAlign - AI-Powered Resume Analysis Platform</p>
    <p>Built with ❤️ using Streamlit & Google Gemini AI</p>
</div>
""", unsafe_allow_html=True)
