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
        self.drawString(30, 30, f"© 2025 ResumeAlign - STRICT AI Analysis | Page {page_num}")

def create_definitive_recommendation(candidate_data: Dict[str, Any]) -> str:
    """Create definitive STRICT recommendation based on analysis"""
    
    overall_score = candidate_data.get('overall_score', 0)
    candidate_name = candidate_data.get('candidate_name', 'The candidate')
    
    # Use existing recommendations if available, otherwise create STRICT ones
    existing_rec = candidate_data.get('recommendations', '')
    if existing_rec and len(existing_rec) > 10:
        return existing_rec
    
    # STRICT recommendation logic matching the AI analysis
    if overall_score >= 85:
        recommendation = f"**Strong Yes** - {candidate_name} is an exceptional candidate with {overall_score}% alignment. Highly recommended for immediate progression to interview stage with minimal additional screening required."
        
    elif overall_score >= 75:
        recommendation = f"**Yes** - {candidate_name} is a strong candidate with {overall_score}% alignment. Recommended for standard interview process with confidence in their capabilities."
        
    elif overall_score >= 65:
        recommendation = f"**Conditional Yes** - {candidate_name} shows {overall_score}% alignment with some gaps. Consider for interview but address identified skill gaps during evaluation process."
        
    elif overall_score >= 50:
        recommendation = f"**Maybe** - {candidate_name} has {overall_score}% alignment with significant concerns. Only consider if candidate pool is extremely limited and extensive training resources are available."
        
    else:
        recommendation = f"**No** - {candidate_name} has {overall_score}% alignment and does not meet minimum requirements. Not recommended for interview stage due to substantial misalignment with job requirements."
    
    return recommendation

def safe_get_list_item(data_list: list, index: int, default: str = "Not available") -> str:
    """FIXED: Safely get list item to prevent index errors"""
    try:
        if isinstance(data_list, list) and len(data_list) > index:
            item = data_list[index]
            if item and str(item).strip() and len(str(item).strip()) > 3:
                return str(item).strip()
        return default
    except (IndexError, TypeError, AttributeError):
        return default

def safe_get_analysis_text(result: Dict[str, Any], field: str, candidate_name: str) -> str:
    """FIXED: Safely get analysis text with fallbacks"""
    try:
        text = result.get(field, '')
        if text and str(text).strip() and len(str(text).strip()) > 20:
            return str(text).strip()
        else:
            field_name = field.replace('_', ' ').title()
            return f"{candidate_name}'s {field_name.lower()} analysis is not available in sufficient detail."
    except (TypeError, AttributeError):
        field_name = field.replace('_', ' ').title()
        return f"{candidate_name}'s {field_name.lower()} assessment could not be retrieved."

def generate_single_candidate_pdf(result: Dict[str, Any], job_description: str) -> Optional[bytes]:
    """FIXED: Generate PDF with comprehensive error handling and no list index errors"""
    
    try:
        logger.info("Starting FIXED PDF generation for single candidate")
        
        # CRITICAL: Validate input data
        if not result or not isinstance(result, dict):
            logger.error("Invalid or missing result data for PDF generation")
            st.error("❌ No valid analysis data available for PDF generation")
            return None
            
        candidate_name = result.get('candidate_name', 'Unknown Candidate')
        if not candidate_name or candidate_name == 'Unknown Candidate':
            candidate_name = 'Candidate Analysis'
            
        logger.info(f"Generating PDF for: {candidate_name}")
        
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document with proper error handling
        try:
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=100,
                title=f"ResumeAlign Analysis - {candidate_name}"
            )
        except Exception as doc_error:
            logger.error(f"Document creation error: {str(doc_error)}")
            st.error(f"❌ PDF document creation failed: {str(doc_error)}")
            return None
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
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
        
        # Build story
        story = []
        
        # Title
        story.append(Paragraph("ResumeAlign - STRICT Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # FIXED: Safe data extraction with proper defaults
        overall_score = float(result.get('overall_score', 0))
        skills_score = int(result.get('skills_score', 0))
        experience_score = int(result.get('experience_score', 0))
        education_score = int(result.get('education_score', 0))
        current_date = datetime.now().strftime('%d %B %Y')
        
        # Basic info table with safe data
        basic_info = [
            ['Candidate Name:', candidate_name],
            ['Analysis Date:', current_date],
            ['Overall Alignment Score:', f"{overall_score}%"],
            ['Skills Score:', f"{skills_score}%"],
            ['Experience Score:', f"{experience_score}%"],
            ['Education Score:', f"{education_score}%"],
            ['Evaluation Method:', 'STRICT AI Analysis (Gemini 1.5 Flash)']
        ]
        
        # Create table with error handling
        try:
            basic_table = Table(basic_info, colWidths=[2.2*inch, 4.3*inch])
            basic_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.grey),
            ]))
            
            story.append(basic_table)
            story.append(Spacer(1, 20))
            
        except Exception as table_error:
            logger.warning(f"Table creation error, using text format: {str(table_error)}")
            # Fallback to text format
            for key, value in basic_info:
                story.append(Paragraph(f"<b>{key}</b> {value}", body_style))
            story.append(Spacer(1, 20))
        
        # FIXED: Analysis sections with comprehensive error handling
        story.append(Paragraph("Executive Summary:", heading_style))
        
        # Use safe text extraction
        skills_analysis = safe_get_analysis_text(result, 'skills_analysis', candidate_name)
        experience_analysis = safe_get_analysis_text(result, 'experience_analysis', candidate_name)
        education_analysis = safe_get_analysis_text(result, 'education_analysis', candidate_name)
        fit_assessment = safe_get_analysis_text(result, 'fit_assessment', candidate_name)
        
        # Create comprehensive summary
        summary_parts = []
        if skills_analysis != f"{candidate_name}'s skills analysis is not available in sufficient detail.":
            summary_parts.append(f"Skills Assessment: {skills_analysis}")
        
        if experience_analysis != f"{candidate_name}'s experience analysis is not available in sufficient detail.":
            summary_parts.append(f"Experience Evaluation: {experience_analysis}")
            
        if fit_assessment != f"{candidate_name}'s fit assessment is not available in sufficient detail.":
            summary_parts.append(f"Overall Fit: {fit_assessment}")
        
        if summary_parts:
            summary_text = " | ".join(summary_parts)
        else:
            summary_text = f"{candidate_name} has been evaluated using STRICT AI analysis criteria with an overall alignment score of {overall_score}%. Detailed manual review is recommended for comprehensive assessment."
        
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 15))
        
        # FIXED: Strengths section with safe list handling
        strengths = result.get('strengths', [])
        if strengths and isinstance(strengths, list):
            story.append(Paragraph("Key Strengths:", heading_style))
            strength_count = 0
            for strength in strengths:
                if strength and str(strength).strip() and len(str(strength).strip()) > 5:
                    story.append(Paragraph(f"• {str(strength).strip()}", body_style))
                    strength_count += 1
                    if strength_count >= 5:  # Limit to 5 strengths
                        break
            
            if strength_count == 0:
                story.append(Paragraph(f"• {candidate_name} shows potential for development", body_style))
                story.append(Paragraph(f"• Detailed strengths assessment requires additional evaluation", body_style))
                
            story.append(Spacer(1, 15))
        
        # FIXED: Areas for Improvement with safe list handling
        weaknesses = result.get('weaknesses', [])
        if weaknesses and isinstance(weaknesses, list):
            story.append(Paragraph("Areas for Improvement:", heading_style))
            weakness_count = 0
            for weakness in weaknesses:
                if weakness and str(weakness).strip() and len(str(weakness).strip()) > 5:
                    story.append(Paragraph(f"• {str(weakness).strip()}", body_style))
                    weakness_count += 1
                    if weakness_count >= 5:  # Limit to 5 weaknesses
                        break
            
            if weakness_count == 0:
                story.append(Paragraph(f"• Comprehensive skills assessment needed", body_style))
                story.append(Paragraph(f"• Additional evaluation required for detailed feedback", body_style))
                
            story.append(Spacer(1, 15))
        
        # FIXED: Interview Questions with guaranteed content
        story.append(Paragraph("Suggested Interview Questions:", heading_style))
        
        interview_questions = result.get('interview_questions', [])
        
        # Ensure we have interview questions
        if not interview_questions or not isinstance(interview_questions, list):
            # Generate default questions if missing
            first_name = candidate_name.split()[0] if len(candidate_name.split()) > 1 else "candidate"
            interview_questions = [
                f"Can you walk me through your most relevant experience for this role, {first_name}?",
                "Describe a challenging project you've worked on and how you overcame obstacles.",
                "What specific skills do you bring that align with our job requirements?",
                "How do you stay current with industry trends and professional development?",
                "Tell me about a time you had to learn something new quickly for work.",
                "What interests you most about this position and our organization?",
                "How would you approach the key responsibilities outlined in this job description?",
                "What are your career goals for the next 3-5 years?"
            ]
        
        # Add questions with guaranteed content
        question_count = 0
        for i, question in enumerate(interview_questions):
            if question and str(question).strip() and len(str(question).strip()) > 15:
                question_count += 1
                story.append(Paragraph(f"{question_count}. {str(question).strip()}", body_style))
                story.append(Spacer(1, 4))
                
                if question_count >= 8:  # Limit to 8 questions
                    break
        
        # Ensure minimum questions
        if question_count == 0:
            default_questions = [
                "Please describe your background and relevant experience.",
                "What interests you about this role and our organization?",
                "How do you approach challenging situations in your work?",
                "What are your key professional strengths?",
                "Where do you see yourself professionally in the next few years?"
            ]
            
            for i, question in enumerate(default_questions, 1):
                story.append(Paragraph(f"{i}. {question}", body_style))
                story.append(Spacer(1, 4))
        
        story.append(Spacer(1, 15))
        
        # FIXED: Recommendation section with definitive advice
        story.append(Paragraph("Final Recommendation:", heading_style))
        
        recommendation_text = create_definitive_recommendation(result)
        story.append(Paragraph(recommendation_text, body_style))
        
        # Add scoring explanation
        story.append(Spacer(1, 10))
        story.append(Paragraph("Scoring Methodology:", heading_style))
        scoring_text = f"This analysis uses STRICT evaluation criteria: Skills (50%), Experience (30%), Education (20%). Scores: 85+ = Strong Yes, 75-84 = Yes, 65-74 = Conditional Yes, 50-64 = Maybe, <50 = No."
        story.append(Paragraph(scoring_text, body_style))
        
        # FIXED: Build PDF with comprehensive error handling
        try:
            logger.info("Building PDF document...")
            doc.build(story, canvasmaker=NumberedCanvas)
            
            pdf_data = buffer.getvalue()
            buffer.close()
            
            if pdf_data and len(pdf_data) > 1000:  # Ensure we have substantial PDF data
                logger.info(f"✅ Successfully generated PDF for {candidate_name} ({len(pdf_data)} bytes)")
                return pdf_data
            else:
                logger.error(f"PDF data too small or empty: {len(pdf_data) if pdf_data else 0} bytes")
                st.error("❌ Generated PDF appears to be empty or corrupted")
                return None
        
        except Exception as build_error:
            logger.error(f"PDF build error for {candidate_name}: {str(build_error)}")
            buffer.close()
            st.error(f"❌ Error building PDF document: {str(build_error)}")
            return None
    
    except Exception as e:
        logger.error(f"Critical error in PDF generation: {str(e)}")
        st.error(f"❌ PDF generation failed: {str(e)}")
        return None

def generate_batch_zip_reports(results: List[Dict[str, Any]], job_description: str) -> Optional[bytes]:
    """FIXED: Generate ZIP file with individual PDFs - comprehensive error handling"""
    
    try:
        # Validate inputs
        if not results or not isinstance(results, list) or len(results) == 0:
            logger.error("No valid results provided for ZIP generation")
            st.error("❌ No valid analysis results for ZIP generation")
            return None
            
        logger.info(f"Generating ZIP file for {len(results)} candidates")
        
        # Create ZIP buffer
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            successful_pdfs = 0
            failed_pdfs = []
            
            # Generate individual PDF for each candidate
            for i, result in enumerate(results, 1):
                try:
                    candidate_name = result.get('candidate_name', f'Candidate_{i}')
                    logger.info(f"Generating ZIP PDF {i}/{len(results)} for {candidate_name}")
                    
                    # Clean candidate name for filename
                    safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '_', '-')).strip()
                    safe_name = safe_name.replace(' ', '_')[:30]  # Limit length
                    if not safe_name or safe_name == '_' * len(safe_name):
                        safe_name = f"Candidate_{i}"
                    
                    # Generate individual PDF
                    pdf_data = generate_single_candidate_pdf(result, job_description)
                    
                    if pdf_data and len(pdf_data) > 1000:
                        # Create filename: Report_01_Candidate_Name.pdf
                        filename = f"Report_{i:02d}_{safe_name}.pdf"
                        zip_file.writestr(filename, pdf_data)
                        logger.info(f"✅ Added {filename} to ZIP ({len(pdf_data)} bytes)")
                        successful_pdfs += 1
                    else:
                        logger.warning(f"❌ Failed to generate valid PDF for {candidate_name}")
                        failed_pdfs.append(candidate_name)
                
                except Exception as e:
                    logger.error(f"Error processing candidate {i} ({result.get('candidate_name', 'Unknown')}): {str(e)}")
                    failed_pdfs.append(result.get('candidate_name', f'Candidate_{i}'))
                    continue
            
            # Add batch summary JSON with error handling
            try:
                import json
                
                summary_data = {
                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'analysis_version': 'ResumeAlign STRICT v2.1',
                    'model_used': 'Google Gemini 1.5 Flash (FREE)',
                    'total_candidates': len(results),
                    'successful_reports': successful_pdfs,
                    'failed_reports': len(failed_pdfs),
                    'failed_candidates': failed_pdfs,
                    'job_description_length': len(job_description),
                    'job_description_preview': job_description[:300] + '...' if len(job_description) > 300 else job_description,
                    'candidates_summary': []
                }
                
                # Add candidate summaries
                for i, r in enumerate(results, 1):
                    try:
                        candidate_summary = {
                            'number': i,
                            'name': r.get('candidate_name', f'Candidate_{i}'),
                            'overall_score': float(r.get('overall_score', 0)),
                            'skills_score': int(r.get('skills_score', 0)),
                            'experience_score': int(r.get('experience_score', 0)),
                            'education_score': int(r.get('education_score', 0)),
                            'recommendation': r.get('recommendations', 'No recommendation available').split(' -')[0] if ' -' in r.get('recommendations', '') else r.get('recommendations', 'Unknown'),
                            'pdf_generated': f"Report_{i:02d}_{r.get('candidate_name', f'Candidate_{i}').replace(' ', '_')[:30]}.pdf" in [name for name in zip_file.namelist()]
                        }
                        summary_data['candidates_summary'].append(candidate_summary)
                    except Exception as summary_error:
                        logger.warning(f"Error creating summary for candidate {i}: {str(summary_error)}")
                        continue
                
                # Write summary JSON
                zip_file.writestr('BATCH_ANALYSIS_SUMMARY.json', json.dumps(summary_data, indent=2, ensure_ascii=False))
                logger.info("✅ Added comprehensive batch summary JSON to ZIP")
                
            except Exception as json_error:
                logger.warning(f"Could not add JSON summary to ZIP: {str(json_error)}")
                # Add simple text summary as fallback
                try:
                    simple_summary = f"""ResumeAlign Batch Analysis Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Candidates: {len(results)}
Successful PDF Reports: {successful_pdfs}
Failed Reports: {len(failed_pdfs)}

Candidate Results:
"""
                    for i, r in enumerate(results, 1):
                        name = r.get('candidate_name', f'Candidate_{i}')
                        score = r.get('overall_score', 0)
                        rec = r.get('recommendations', '').split(' -')[0] if ' -' in r.get('recommendations', '') else 'Unknown'
                        simple_summary += f"{i}. {name} - {score}% ({rec})\n"
                    
                    zip_file.writestr('BATCH_SUMMARY.txt', simple_summary)
                    logger.info("✅ Added simple text summary to ZIP")
                except Exception as text_error:
                    logger.warning(f"Could not add text summary: {str(text_error)}")
        
        # Get ZIP data
        zip_data = zip_buffer.getvalue()
        zip_buffer.close()
        
        if zip_data and len(zip_data) > 1000:
            logger.info(f"✅ Successfully generated ZIP file: {successful_pdfs}/{len(results)} PDFs, {len(zip_data)} bytes")
            
            # Show summary to user
            if successful_pdfs == len(results):
                st.success(f"✅ All {successful_pdfs} candidate reports generated successfully!")
            elif successful_pdfs > 0:
                st.warning(f"⚠️ Generated {successful_pdfs}/{len(results)} reports. {len(failed_pdfs)} failed: {', '.join(failed_pdfs[:3])}")
            else:
                st.error(f"❌ No PDF reports could be generated")
                return None
            
            return zip_data
        else:
            logger.error(f"ZIP data too small: {len(zip_data) if zip_data else 0} bytes")
            st.error("❌ Generated ZIP file appears to be empty or corrupted")
            return None
    
    except Exception as e:
        logger.error(f"Critical error generating ZIP file: {str(e)}")
        st.error(f"❌ ZIP generation failed: {str(e)}")
        return None

def generate_comparison_pdf(results: List[Dict[str, Any]], job_description: str) -> Optional[bytes]:
    """FIXED: Main PDF generation function with proper routing"""
    
    try:
        # Validate inputs
        if not results or not isinstance(results, list) or len(results) == 0:
            logger.error("No valid results provided for PDF generation")
            st.error("❌ No analysis results available for PDF generation")
            return None
        
        logger.info(f"PDF generation requested for {len(results)} candidate(s)")
        
        # Route to appropriate function
        if len(results) == 1:
            # Single candidate - return individual PDF
            logger.info("Generating single candidate PDF")
            return generate_single_candidate_pdf(results[0], job_description)
        else:
            # Multiple candidates - return ZIP of individual PDFs
            logger.info(f"Generating ZIP of {len(results)} individual PDFs")
            return generate_batch_zip_reports(results, job_description)
    
    except Exception as e:
        logger.error(f"Error in main PDF generation function: {str(e)}")
        st.error(f"❌ PDF generation failed: {str(e)}")
        return None
