import io
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
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
    """Custom canvas for page numbering"""
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
        self.drawString(30, 30, "ResumeAlign - Analysis Report")

def generate_comparison_pdf(results: List[Dict[str, Any]], job_description: str) -> Optional[bytes]:
    """Generate a comprehensive PDF comparison report"""
    try:
        # Create a BytesIO buffer
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2d3748')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#4a5568')
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.HexColor('#667eea')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        # Build the story (content)
        story = []
        
        # Title page
        story.append(Paragraph("ResumeAlign", title_style))
        story.append(Paragraph("AI-Powered Resume Analysis Report", heading_style))
        story.append(Spacer(1, 20))
        
        # Report metadata
        metadata_data = [
            ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Total Candidates:', str(len(results))],
            ['Analysis Engine:', 'Google Gemini AI'],
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 30))
        
        # Job description section
        story.append(Paragraph("Job Description", heading_style))
        job_desc_truncated = job_description[:1000] + "..." if len(job_description) > 1000 else job_description
        story.append(Paragraph(job_desc_truncated, body_style))
        story.append(Spacer(1, 20))
        
        # Executive summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        if results:
            # Sort results by score
            sorted_results = sorted(results, key=lambda x: x.get('overall_score', 0), reverse=True)
            
            avg_score = sum(r.get('overall_score', 0) for r in results) / len(results)
            top_candidate = sorted_results[0]
            
            summary_text = f"""
            This report analyzes {len(results)} candidate(s) against the provided job description. 
            The average overall score is {avg_score:.1f}%. 
            The top-performing candidate is {top_candidate.get('candidate_name', 'Unknown')} 
            with an overall score of {top_candidate.get('overall_score', 0)}%.
            """
            
            story.append(Paragraph(summary_text, body_style))
            story.append(Spacer(1, 20))
            
            # Rankings table
            story.append(Paragraph("Candidate Rankings", heading_style))
            
            rankings_data = [['Rank', 'Candidate Name', 'Overall Score', 'Skills', 'Experience', 'Education']]
            
            for i, result in enumerate(sorted_results, 1):
                rankings_data.append([
                    str(i),
                    result.get('candidate_name', 'Unknown'),
                    f"{result.get('overall_score', 0)}%",
                    f"{result.get('skills_score', 0)}%",
                    f"{result.get('experience_score', 0)}%",
                    f"{result.get('education_score', 0)}%"
                ])
            
            rankings_table = Table(rankings_data, colWidths=[0.6*inch, 2.2*inch, 1*inch, 0.8*inch, 1*inch, 0.9*inch])
            rankings_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                
                # Alternating row colors
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f0fff4')),  # Top candidate
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fffbf0')),  # Second
                ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#fef2f2')),  # Third
            ]))
            
            story.append(rankings_table)
            story.append(PageBreak())
            
            # Detailed candidate analysis
            story.append(Paragraph("Detailed Candidate Analysis", heading_style))
            
            for i, result in enumerate(sorted_results, 1):
                # Candidate header
                name = result.get('candidate_name', 'Unknown Candidate')
                overall_score = result.get('overall_score', 0)
                
                candidate_header = f"#{i} - {name} (Overall Score: {overall_score}%)"
                story.append(Paragraph(candidate_header, subheading_style))
                
                # Score breakdown
                score_data = [
                    ['Category', 'Score', 'Details'],
                    ['Skills Match', f"{result.get('skills_score', 0)}%", result.get('skills_analysis', 'N/A')[:150] + '...'],
                    ['Experience', f"{result.get('experience_score', 0)}%", result.get('experience_analysis', 'N/A')[:150] + '...'],
                    ['Education', f"{result.get('education_score', 0)}%", result.get('education_analysis', 'N/A')[:150] + '...']
                ]
                
                score_table = Table(score_data, colWidths=[1.5*inch, 1*inch, 4*inch])
                score_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ]))
                
                story.append(score_table)
                story.append(Spacer(1, 15))
                
                # Strengths and weaknesses
                strengths = result.get('strengths', [])
                weaknesses = result.get('weaknesses', [])
                
                if strengths or weaknesses:
                    strength_weakness_data = []
                    
                    # Add headers
                    strength_weakness_data.append(['Strengths', 'Areas for Improvement'])
                    
                    # Prepare data
                    max_items = max(len(strengths), len(weaknesses))
                    for j in range(max_items):
                        strength = strengths[j] if j < len(strengths) else ""
                        weakness = weaknesses[j] if j < len(weaknesses) else ""
                        strength_weakness_data.append([strength, weakness])
                    
                    sw_table = Table(strength_weakness_data, colWidths=[3.25*inch, 3.25*inch])
                    sw_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#22c55e')),
                        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#ef4444')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                    ]))
                    
                    story.append(sw_table)
                    story.append(Spacer(1, 15))
                
                # Recommendations
                recommendations = result.get('recommendations', '')
                if recommendations and recommendations != 'No specific recommendations':
                    story.append(Paragraph("Recommendations:", ParagraphStyle(
                        'RecommendationHeader',
                        parent=body_style,
                        fontSize=10,
                        textColor=colors.HexColor('#667eea'),
                        fontName='Helvetica-Bold'
                    )))
                    story.append(Paragraph(recommendations, body_style))
                
                # Add space between candidates
                if i < len(sorted_results):
                    story.append(Spacer(1, 20))
                    story.append(Paragraph("_" * 80, ParagraphStyle(
                        'Divider',
                        parent=body_style,
                        alignment=TA_CENTER,
                        textColor=colors.HexColor('#e2e8f0')
                    )))
                    story.append(Spacer(1, 20))
        
        else:
            story.append(Paragraph("No candidates were analyzed.", body_style))
        
        # Build the PDF
        doc.build(story, canvasmaker=NumberedCanvas)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Successfully generated PDF report with {len(results)} candidates")
        return pdf_data
    
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}")
        st.error(f"❌ Error generating PDF report: {str(e)}")
        return None

def generate_single_candidate_pdf(result: Dict[str, Any], job_description: str) -> Optional[bytes]:
    """Generate a detailed PDF report for a single candidate"""
    try:
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2d3748')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#4a5568')
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT
        )
        
        story = []
        
        # Title
        candidate_name = result.get('candidate_name', 'Unknown Candidate')
        story.append(Paragraph(f"Resume Analysis Report", title_style))
        story.append(Paragraph(f"Candidate: {candidate_name}", heading_style))
        story.append(Spacer(1, 20))
        
        # Analysis summary
        overall_score = result.get('overall_score', 0)
        
        # Score interpretation
        if overall_score >= 80:
            interpretation = "Excellent match - Highly recommended"
            color = colors.HexColor('#22c55e')
        elif overall_score >= 60:
            interpretation = "Good match - Recommended"
            color = colors.HexColor('#f59e0b')
        else:
            interpretation = "Moderate match - Consider with reservations"
            color = colors.HexColor('#ef4444')
        
        summary_data = [
            ['Overall Score', f"{overall_score}%"],
            ['Assessment', interpretation],
            ['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('TEXTCOLOR', (1, 1), (1, 1), color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Detailed scores
        story.append(Paragraph("Detailed Score Breakdown", heading_style))
        
        detailed_scores = [
            ['Category', 'Score', 'Analysis'],
            ['Skills Match', f"{result.get('skills_score', 0)}%", result.get('skills_analysis', 'N/A')],
            ['Experience', f"{result.get('experience_score', 0)}%", result.get('experience_analysis', 'N/A')],
            ['Education', f"{result.get('education_score', 0)}%", result.get('education_analysis', 'N/A')]
        ]
        
        detailed_table = Table(detailed_scores, colWidths=[1.5*inch, 1*inch, 4*inch])
        detailed_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ]))
        
        story.append(detailed_table)
        story.append(Spacer(1, 20))
        
        # Fit assessment
        fit_assessment = result.get('fit_assessment', '')
        if fit_assessment and fit_assessment != 'Assessment not available':
            story.append(Paragraph("Overall Fit Assessment", heading_style))
            story.append(Paragraph(fit_assessment, body_style))
            story.append(Spacer(1, 15))
        
        # Recommendations
        recommendations = result.get('recommendations', '')
        if recommendations and recommendations != 'No specific recommendations':
            story.append(Paragraph("Recommendations", heading_style))
            story.append(Paragraph(recommendations, body_style))
        
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
