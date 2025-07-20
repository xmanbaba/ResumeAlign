# app.py – ResumeFit v8 (no string-inside-string issues)
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

def build_pdf(report):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=inch, bottomMargin=inch)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], fontSize=16, spaceAfter=12, textColor=blue)
    normal_style = ParagraphStyle("Normal", parent=styles["Normal"], fontSize=11, spaceAfter=6)

    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.drawCentredString(A4[0] / 2, 0.75 * inch, f"© 2025 ResumeFit – AI Resume & CV Analyzer   |   Page {doc.page}")
        canvas.restoreState()

    story = []
    story.append(Paragraph("ResumeFit Analysis Report", title_style))
    story.append(Paragraph(f"<b>Name of Candidate:</b> {report.get('candidate_summary','').split(' is ')[0]}", normal_style))
    story.append(Paragraph(f"<b>Review Date:</b> {datetime.now():%d %B %Y}", normal_style))
    story.append(Paragraph(f"<b>Alignment Score:</b> {report['alignment_score']} / 10", title_style))
    story.append(Paragraph(f"<b>Experience Estimate:</b> {report['experience_years']['raw_estimate']} ({report['experience_years']['confidence']} confidence)", normal_style))
    story.append(Paragraph("<b>Summary:</b>", title_style))
    story.append(Paragraph(report.get("candidate_summary", ""), normal_style))
    story.append(Paragraph("<b>Strengths:</b>", title_style))
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

SYSTEM_PROMPT = "Use only the text provided. Return valid JSON matching the schema."

def build_prompt(jd, profile_text, file_text):
    extra = file_text.strip() if file_text.strip() else "None provided"
    return f"""
Job Description:
{jd}

Candidate Profile / CV:
{profile_text}

Extra File Text:
{extra}

Return valid JSON:
{{
  "alignment_score": <0-10>,
  "experience_years": {{"raw_estimate": "<string>", "confidence": "<High|Medium|Low>", "source": "<Manual text|File>"}},
  "candidate_summary": "<300 words>",
  "areas_for_improvement": ["<string>","<string>","<string>","<string>","<string>"],
  "strengths": ["<string>","<string>","<string>","<string>","<string>"],
  "suggested_interview_questions": ["<string>","<string>","<string>","<string>","<string>"],
  "next_round_recommendation": "<Yes|No|Maybe – brief reason>",
  "sources_used": ["Manual text","File"]
}}
