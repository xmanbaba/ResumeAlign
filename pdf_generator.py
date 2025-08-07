from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import streamlit as st
from datetime import datetime
import io
from typing import Dict, Any

def create_analysis_pdf(analysis: Dict[str, Any], candidate_name: str, job_title: str = "") -> bytes:
    """
    Create a PDF report of the resume analysis
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=18)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2E86AB')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.HexColor('#2E86AB'),
        borderWidth=1,
        borderColor=colors.HexColor('#2E86AB'),
        borderPadding=5
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.alignment = TA_JUSTIFY
    
    # Build PDF content
    content = []
    
    # Title
    title_text = f"Resume Analysis Report"
    if job_title:
        title_text += f"<br/><font size='16'>{job_title}</font>"
    content.append(Paragraph(title_text, title_style))
    content.append(Spacer(1, 20))
    
    # Candidate Info
    content.append(Paragraph(f"<b>Candidate:</b> {candidate_name}", normal_style))
    content.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
    content.append(Spacer(1, 30))
    
    # Score Summary Table
    content.append(Paragraph("📊 Score Summary", heading_style))
    score_data = [
        ['Metric', 'Score'],
        ['Overall Match', f"{analysis.get('overall_score', 0)}%"],
        ['Skills Match', f"{analysis.get('skills_score', 0)}%"],
        ['Experience Relevance', f"{analysis.get('experience_score', 0)}%"],
        ['Education Alignment', f"{analysis.get('education_score', 0)}%"]
    ]
    
    score_table = Table(score_data, colWidths=[3*inch, 2*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(score_table)
    content.append(Spacer(1, 30))
    
    # Strengths
    content.append(Paragraph("✅ Key Strengths", heading_style))
    strengths = analysis.get('strengths', [])
    for strength in strengths[:5]:  # Limit to top 5
        content.append(Paragraph(f"• {strength}", normal_style))
    content.append(Spacer(1, 20))
    
    # Areas for Improvement
    content.append(Paragraph("🎯 Areas for Improvement", heading_style))
    weaknesses = analysis.get('weaknesses', [])
    for weakness in weaknesses[:5]:
        content.append(Paragraph(f"• {weakness}", normal_style))
    content.append(Spacer(1, 20))
    
    # Missing Skills
    content.append(Paragraph("🔍 Missing Skills", heading_style))
    missing_skills = analysis.get('missing_skills', [])
    for skill in missing_skills[:5]:
        content.append(Paragraph(f"• {skill}", normal_style))
    content.append(Spacer(1, 20))
    
    # Recommendations
    content.append(Paragraph("💡 Recommendations", heading_style))
    recommendations = analysis.get('recommendations', [])
    for rec in recommendations[:5]:
        content.append(Paragraph(f"• {rec}", normal_style))
    content.append(Spacer(1, 20))
    
    # Detailed Analysis
    if analysis.get('experience_analysis'):
        content.append(Paragraph("📋 Experience Analysis", heading_style))
        content.append(Paragraph(analysis['experience_analysis'], normal_style))
        content.append(Spacer(1, 15))
    
    if analysis.get('skills_analysis'):
        content.append(Paragraph("🛠️ Skills Analysis", heading_style))
        content.append(Paragraph(analysis['skills_analysis'], normal_style))
        content.append(Spacer(1, 15))
    
    # Next Steps
    if analysis.get('next_steps'):
        content.append(Paragraph("🚀 Next Steps", heading_style))
        content.append(Paragraph(analysis['next_steps'], normal_style))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()

def generate_pdf_download_button(analysis: Dict[str, Any], candidate_name: str, job_title: str = ""):
    """
    Generate PDF and create download button
    """
    try:
        pdf_bytes = create_analysis_pdf(analysis, candidate_name, job_title)
        
        filename = f"Resume_Analysis_{candidate_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            help="Download detailed analysis as PDF"
        )
        return True
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return False
