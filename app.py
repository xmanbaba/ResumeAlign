# app.py – ResumeAlign v2.0 - Batch Processing
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

def get_candidate_name_from_report(report):
    """Extract candidate name from the summary"""
    summary = report.get('candidate_summary', '')
    if ' is ' in summary:
        return summary.split(' is ')[0].strip()
    return "Unknown Candidate"

def build_single_pdf(report, linkedin_url="", candidate_name=""):
    """Build PDF for a single candidate"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.drawCentredString(A4[0] / 2, 0.75 * inch, f"© 2025 ResumeAlign – AI Resume & CV Analyzer   |   Page {doc.page}")
        canvas.restoreState()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=16, spaceAfter=12, textColor=blue)
    normal_style = ParagraphStyle("Normal", fontSize=11, spaceAfter=6)

    # Use provided candidate name or extract from summary
    display_name = candidate_name if candidate_name else get_candidate_name_from_report(report)

    story = [
        Paragraph("ResumeAlign Analysis Report", title_style),
        Paragraph(f"<b>Name of Candidate:</b> {display_name}", normal_style),
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

def build_combined_pdf(reports_data):
    """Build combined PDF with all candidates"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.drawCentredText(A4[0] / 2, 0.75 * inch, f"© 2025 ResumeAlign – AI Resume & CV Analyzer   |   Page {doc.page}")
        canvas.restoreState()

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=16, spaceAfter=12, textColor=blue)
    normal_style = ParagraphStyle("Normal", fontSize=11, spaceAfter=6)
    header_style = ParagraphStyle("Header", fontSize=18, spaceAfter=15, textColor=blue, alignment=TA_CENTER)

    story = [
        Paragraph("ResumeAlign Batch Analysis Report", header_style),
        Paragraph(f"<b>Analysis Date:</b> {datetime.now():%d %B %Y}", normal_style),
        Paragraph(f"<b>Total Candidates Analyzed:</b> {len(reports_data)}", normal_style),
        Spacer(1, 0.3*inch),
    ]

    for i, (filename, report) in enumerate(reports_data, 1):
        candidate_name = get_candidate_name_from_report(report)
        
        # Add page break before each new candidate (except the first)
        if i > 1:
            story.append(PageBreak())
        
        story.extend([
            Paragraph(f"Candidate {i}: {candidate_name}", header_style),
            Paragraph(f"<b>Source File:</b> {filename}", normal_style),
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
        for j, q in enumerate(report.get("suggested_interview_questions", []), 1):
            story.append(Paragraph(f"{j}. {q}", normal_style))
        story.append(Paragraph("<b>Recommendation:</b>", title_style))
        story.append(Paragraph(report.get("next_round_recommendation", ""), normal_style))

    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    buffer.seek(0)
    return buffer

def create_zip_download(reports_data):
    """Create a ZIP file containing all individual PDF reports"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, report in reports_data:
            # Create individual PDF
            pdf_buffer = build_single_pdf(report)
            
            # Clean filename for PDF (remove extension and add .pdf)
            clean_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            pdf_filename = f"ResumeAlign_Report_{clean_name}.pdf"
            
            # Add to ZIP
            zip_file.writestr(pdf_filename, pdf_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

SYSTEM_PROMPT = "Use only the text provided. Return valid JSON matching the schema."

def build_prompt(jd, profile_text, file_text, filename):
    extra = file_text.strip() if file_text.strip() else "None provided"
    return (
        f"Job Description:\n{jd}\n\n"
        f"Candidate CV/Resume (from file: {filename}):\n{profile_text}\n\n"
        f"Additional File Text:\n{extra}\n\n"
        "Return valid JSON:\n"
        "{\n"
        '  "alignment_score": <0-10>,\n'
        '  "experience_years": {"raw_estimate": "<string>", "confidence": "<High|Medium|Low>", "source": "<Manual text|File>"},\n'
        '  "candidate_summary": "<300 words>",\n'
        '  "areas_for_improvement": ["<string>","<string>","<string>","<string>","<string>"],\n'
        '  "strengths": ["<string>","<string>","<string>","<string>","<string>"],\n'
        '  "suggested_interview_questions": ["<string>","<string>","<string>","<string>","<string>"],\n'
        '  "next_round_recommendation": "<Yes|No|Maybe – brief reason>",\n'
        '  "sources_used": ["File"]\n'
        '}'
    )

# ---------- UI ----------
st.set_page_config(page_title="ResumeAlign - Batch Processing", layout="wide")
st.title("ResumeAlign – AI Resume & CV Analyzer (Batch Processing)")

st.markdown("### 📁 Batch CV Analysis")
st.info("Upload up to 5 CV/Resume files (PDF or DOCX) to analyze them all against the same job description.")

with st.form("batch_analyzer"):
    job_desc = st.text_area("Job Description (paste the full job description)", height=250)
    
    uploaded_files = st.file_uploader(
        "Upload CV/Resume Files (Maximum 5 files)", 
        type=["pdf", "docx"], 
        accept_multiple_files=True,
        help="Select multiple PDF or DOCX files. Maximum 5 files allowed."
    )
    
    submitted = st.form_submit_button("🚀 Analyze All CVs", type="primary")

if submitted:
    if not job_desc.strip():
        st.error("❌ Job Description is required.")
        st.stop()
    
    if not uploaded_files:
        st.error("❌ Please upload at least one CV/Resume file.")
        st.stop()
    
    if len(uploaded_files) > 5:
        st.error("❌ Maximum 5 files allowed. Please select fewer files.")
        st.stop()
    
    # Process all files
    st.success(f"✅ Processing {len(uploaded_files)} files...")
    
    all_reports = []
    progress_bar = st.progress(0)
    
    for i, uploaded_file in enumerate(uploaded_files):
        with st.spinner(f"Analyzing {uploaded_file.name} ({i+1}/{len(uploaded_files)})..."):
            try:
                # Extract text from file
                file_text = extract_text(uploaded_file)
                
                if not file_text.strip():
                    st.warning(f"⚠️ Could not extract text from {uploaded_file.name}. Skipping...")
                    continue
                
                # Build prompt and analyze
                prompt = build_prompt(job_desc, file_text, "", uploaded_file.name)
                response = model.generate_content([SYSTEM_PROMPT, prompt])
                
                # Parse response
                report_text = response.text.strip("```json").strip("```")
                report = json.loads(report_text)
                
                # Store report with filename
                all_reports.append((uploaded_file.name, report))
                
            except Exception as e:
                st.error(f"❌ Error analyzing {uploaded_file.name}: {str(e)}")
                continue
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    if all_reports:
        st.session_state["batch_reports"] = all_reports
        st.session_state["job_description"] = job_desc
        
        # Success message
        st.success(f"🎉 Successfully analyzed {len(all_reports)} out of {len(uploaded_files)} files!")

# Display results if available
if "batch_reports" in st.session_state:
    reports_data = st.session_state["batch_reports"]
    
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    # Download options
    st.markdown("### 📥 Download Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Individual reports as ZIP
        zip_data = create_zip_download(reports_data)
        st.download_button(
            "📦 Download Individual Reports (ZIP)",
            data=zip_data,
            file_name=f"ResumeAlign_Individual_Reports_{datetime.now():%Y%m%d_%H%M%S}.zip",
            mime="application/zip"
        )
    
    with col2:
        # Combined PDF
        combined_pdf = build_combined_pdf(reports_data)
        st.download_button(
            "📄 Download Combined Report (PDF)",
            data=combined_pdf,
            file_name=f"ResumeAlign_Combined_Report_{datetime.now():%Y%m%d_%H%M%S}.pdf",
            mime="application/pdf"
        )
    
    with col3:
        # All reports as JSON
        all_json_data = {f"report_{i+1}_{filename}": report for i, (filename, report) in enumerate(reports_data)}
        st.download_button(
            "💾 Download All JSON Data",
            data=json.dumps(all_json_data, indent=2),
            file_name=f"ResumeAlign_All_Reports_{datetime.now():%Y%m%d_%H%M%S}.json",
            mime="application/json"
        )
    
    # Display individual reports
    st.markdown("### 📋 Individual Reports")
    
    # Report selector
    report_names = [f"{i+1}. {filename}" for i, (filename, _) in enumerate(reports_data)]
    selected_index = st.selectbox(
        "Select a report to view:",
        range(len(report_names)),
        format_func=lambda x: report_names[x]
    )
    
    if selected_index is not None:
        filename, report = reports_data[selected_index]
        candidate_name = get_candidate_name_from_report(report)
        
        st.markdown(f"#### 👤 Report for: {candidate_name}")
        st.markdown(f"**Source File:** `{filename}`")
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Alignment Score", f"{report['alignment_score']}/10")
        with col2:
            st.metric("Experience", report['experience_years']['raw_estimate'])
        with col3:
            recommendation = report['next_round_recommendation']
            color = "🟢" if recommendation.lower().startswith('yes') else "🟡" if recommendation.lower().startswith('maybe') else "🔴"
            st.metric("Recommendation", f"{color} {recommendation}")
        
        # Display detailed report
        with st.expander("📄 Full Report Details", expanded=True):
            st.write("**Summary:**")
            st.write(report["candidate_summary"])
            
            st.write("**Strengths:**")
            for s in report["strengths"]:
                st.write(f"• {s}")
            
            st.write("**Areas for Improvement:**")
            for a in report["areas_for_improvement"]:
                st.write(f"• {a}")
            
            st.write("**Suggested Interview Questions:**")
            for i, q in enumerate(report["suggested_interview_questions"], 1):
                st.write(f"{i}. {q}")

# Footer
st.markdown("---")
st.markdown("*ResumeAlign v2.0 - Batch Processing | Powered by Google Gemini 2.5 Flash*")
