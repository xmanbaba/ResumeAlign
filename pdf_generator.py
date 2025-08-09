import io
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import zipfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NumberedCanvas(canvas.Canvas):
    """Custom canvas for page numbering with ResumeAlign branding"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for (page_num, page_state) in enumerate(self._saved_page_states):
            self.__dict__.update(page_state)
            self.draw_page_number(page_num + 1, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_num, total_pages):
        width, height = letter
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.grey)
        self.drawRightString(width - 30, 30, f"Page {page_num} of {total_pages}")
        self.drawString(30, 30, f"© 2025 ResumeAlign -- AI Resume & CV Analyzer | Page {page_num}")

def generate_interview_questions(candidate_data: Dict[str, Any], job_description: str) -> List[str]:
    """Generate relevant interview questions based on candidate analysis"""
    
    # Extract key info
    candidate_name = candidate_data.get('candidate_name', 'Unknown Candidate')
    skills_analysis = candidate_data.get('skills_analysis', '')
    experience_analysis = candidate_data.get('experience_analysis', '')
    weaknesses = candidate_data.get('weaknesses', [])
    strengths = candidate_data.get('strengths', [])
    
    # Base interview questions
    questions = []
    
    # Skills-based questions
    if 'technical' in skills_analysis.lower() or 'software' in skills_analysis.lower():
        questions.append("Can you walk me through your experience with the specific technical skills mentioned in the job description and how you've applied them in previous roles?")
    
    if 'management' in skills_analysis.lower() or 'leadership' in skills_analysis.lower():
        questions.append("Describe a challenging team situation you've managed and how you handled it. What was the outcome?")
    
    # Experience-based questions
    if 'years' in experience_analysis.lower():
        questions.append("Tell me about a project from your experience that you're most proud of and how it relates to this position.")
    
    # Weakness-based questions (areas for improvement)
    for weakness in weaknesses[:2]:  # Focus on top 2 weaknesses
        if weakness and len(weakness) > 10:
            questions.append(f"I noticed from your background that there might be room for growth in {weakness.lower()}. How would you approach developing this area?")
    
    # Strength-based questions
    for strength in strengths[:2]:  # Focus on top 2 strengths
        if strength and len(strength) > 10:
            questions.append(f"You mentioned strong capabilities in {strength.lower()}. Can you provide a specific example of how you've leveraged this strength to achieve results?")
    
    # Job-specific questions based on common job requirements
    if 'sales' in job_description.lower():
        questions.append("Can you describe your approach to building relationships with new clients and how you maintain existing client relationships?")
    
    if 'customer' in job_description.lower():
        questions.append("Tell me about a time when you had to handle a difficult customer situation. What was your approach and what was the result?")
    
    if 'analysis' in job_description.lower() or 'data' in job_description.lower():
        questions.append("How do you approach data analysis and what tools do you use to derive insights for decision-making?")
    
    # General closing questions
    questions.extend([
        "What attracts you most to this role and our organization, and how do you see yourself contributing in the first 90 days?",
        "Where do you see yourself in 3-5 years, and how does this position align with your career goals?"
    ])
    
    # Return top 8 questions (manageable for interviewer)
    return questions[:8]

def create_definitive_recommendation(candidate_data: Dict[str, Any]) -> str:
    """Create a definitive recommendation based on analysis"""
    
    overall_score = candidate_data.get('overall_score', 0)
    candidate_name = candidate_data.get('candidate_name', 'The candidate')
    strengths = candidate_data.get('strengths', [])
    
    if overall_score >= 85:
        recommendation = f"**Strong Yes** -- {candidate_name} is an exceptional candidate who demonstrates outstanding alignment with the role requirements. "
        recommendation += f"With an overall score of {overall_score}%, they bring significant value and should be prioritized for immediate next steps."
        
    elif overall_score >= 75:
        recommendation = f"**Yes** -- {candidate_name} is a strong candidate with solid qualifications and good alignment with the role. "
        recommendation += f"Their {overall_score}% overall score indicates they would be a valuable addition to the team."
        
    elif overall_score >= 65:
        recommendation = f"**Conditional Yes** -- {candidate_name} shows promise with a {overall_score}% alignment score. "
        recommendation += "Consider proceeding with interviews to assess cultural fit and address any skill gaps through training."
        
    elif overall_score >= 50:
        recommendation = f"**Maybe** -- {candidate_name} has some relevant qualifications but significant gaps remain. "
        recommendation += f"With a {overall_score}% score, consider only if the candidate pool is limited and training resources are available."
        
    else:
        recommendation = f"**No** -- {candidate_name} does not meet the minimum requirements for this role. "
        recommendation += f"The {overall_score}% alignment score indicates substantial misalignment with job requirements."
    
    # Add specific strengths that support the recommendation
    if strengths and len(strengths) > 0:
        top_strengths = strengths[:3]  # Top 3 strengths
        recommendation += f" Key strengths include: {', '.join(top_strengths).lower()}."
    
    return recommendation

def generate_single_candidate_pdf(result: Dict[str, Any], job_description: str) -> Optional[bytes]:
    """Generate a detailed PDF report for a single candidate matching the original format"""
    try:
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=100
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles matching the original format
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=15,
            textColor=colors.HexColor('#000000'),
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        story = []
        
        # Title
        story.append(Paragraph("ResumeAlign Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Candidate details
        candidate_name = result.get('candidate_name', 'Unknown Candidate')
        overall_score = result.get('overall_score', 0)
        current_date = datetime.now().strftime('%d %B %Y')
        
        # Basic info table
        basic_info = [
            ['Name of Candidate:', candidate_name],
            ['Review Date:', current_date],
            ['Alignment Score:', f"{overall_score}%"],
            ['Experience Estimate:', 'Based on resume analysis (High confidence)']
        ]
        
        basic_table = Table(basic_info, colWidths=[2*inch, 4.5*inch])
        basic_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        story.append(basic_table)
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Summary:", heading_style))
        
        # Create comprehensive summary
        skills_analysis = result.get('skills_analysis', 'Skills analysis not available')
        experience_analysis = result.get('experience_analysis', 'Experience analysis not available')
        fit_assessment = result.get('fit_assessment', 'Fit assessment not available')
        
        summary_text = f"{candidate_name} brings {experience_analysis.lower()} "
        summary_text += f"The candidate demonstrates {skills_analysis.lower()} "
        summary_text += f"Overall assessment: {fit_assessment}"
        
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 15))
        
        # Strengths section
        strengths = result.get('strengths', [])
        if strengths:
            story.append(Paragraph("Strengths:", heading_style))
            for strength in strengths:
                story.append(Paragraph(f"• {strength}", body_style))
            story.append(Spacer(1, 15))
        
        # Areas for Improvement section
        weaknesses = result.get('weaknesses', [])
        if weaknesses:
            story.append(Paragraph("Areas for Improvement:", heading_style))
            for weakness in weaknesses:
                story.append(Paragraph(f"• {weakness}", body_style))
            story.append(Spacer(1, 15))
        
        # Interview Questions section
        story.append(Paragraph("Interview Questions:", heading_style))
        interview_questions = generate_interview_questions(result, job_description)
        
        for i, question in enumerate(interview_questions, 1):
            story.append(Paragraph(f"{i}. {question}", body_style))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 15))
        
        # Recommendation section
        story.append(Paragraph("Recommendation:", heading_style))
        recommendation = create_definitive_recommendation(result)
        story.append(Paragraph(recommendation, body_style))
        
        # Build PDF
        doc.build(story, canvasmaker=NumberedCanvas)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Successfully generated single candidate PDF for {candidate_name}")
        return pdf_data
    
    except Exception as e:
        logger.error(f"Error generating single candidate PDF: {str(e)}")
        st.error(f"❌ Error generating PDF: {str(e)}")
        return None

def generate_batch_zip_reports(results: List[Dict[str, Any]], job_description: str) -> Optional[bytes]:
    """Generate ZIP file containing individual PDF reports for each candidate"""
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Generate individual PDF for each candidate
            for i, result in enumerate(results, 1):
                try:
                    candidate_name = result.get('candidate_name', f'Candidate_{i}')
                    
                    # Clean candidate name for filename
                    safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '_', '-')).strip()
                    safe_name = safe_name.replace(' ', '_')
                    
                    # Generate PDF
                    pdf_data = generate_single_candidate_pdf(result, job_description)
                    
                    if pdf_data:
                        # Create filename following the pattern: Report_01_Candidate_Name.pdf
                        filename = f"Report_{i:02d}_{safe_name}.pdf"
                        zip_file.writestr(filename, pdf_data)
                        logger.info(f"Added {filename} to ZIP")
                    else:
                        logger.warning(f"Failed to generate PDF for {candidate_name}")
                
                except Exception as e:
                    logger.error(f"Error processing candidate {i}: {str(e)}")
                    continue
            
            # Add batch summary JSON
            try:
                import json
                
                summary_data = {
                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_candidates': len(results),
                    'job_description': job_description[:500] + '...' if len(job_description) > 500 else job_description,
                    'candidates': [
                        {
                            'name': r.get('candidate_name', 'Unknown'),
                            'overall_score': r.get('overall_score', 0),
                            'skills_score': r.get('skills_score', 0),
                            'experience_score': r.get('experience_score', 0),
                            'education_score': r.get('education_score', 0)
                        } for r in results
                    ]
                }
                
                zip_file.writestr('batch_summary.json', json.dumps(summary_data, indent=2))
                
            except Exception as e:
                logger.warning(f"Could not add JSON summary: {str(e)}")
        
        zip_data = zip_buffer.getvalue()
        zip_buffer.close()
        
        logger.info(f"Successfully generated ZIP file with {len(results)} candidate reports")
        return zip_data
    
    except Exception as e:
        logger.error(f"Error generating ZIP file: {str(e)}")
        st.error(f"❌ Error generating ZIP file: {str(e)}")
        return None

def generate_comparison_pdf(results: List[Dict[str, Any]], job_description: str) -> Optional[bytes]:
    """Generate a comprehensive PDF comparison report for batch analysis"""
    try:
        # For batch analysis, return ZIP file instead of single PDF
        if len(results) > 1:
            return generate_batch_zip_reports(results, job_description)
        elif len(results) == 1:
            # Single candidate - return individual PDF
            return generate_single_candidate_pdf(results[0], job_description)
        else:
            logger.warning("No results provided for PDF generation")
            return None
    
    except Exception as e:
        logger.error(f"Error in generate_comparison_pdf: {str(e)}")
        st.error(f"❌ Error generating report: {str(e)}")
        return None
