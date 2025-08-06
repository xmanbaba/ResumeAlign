"""
PDF generation module for ResumeAlign
Handles PDF report creation and batch ZIP file generation
"""

import json
import zipfile
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.colors import blue
from reportlab.lib.enums import TA_CENTER

from file_utils import create_safe_filename


def build_pdf(report, linkedin_url="", candidate_name="", extracted_from_cv=False):
    """Generate a PDF report for a single candidate"""
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
