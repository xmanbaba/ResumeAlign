import streamlit as st
import io
import os
import tempfile
import logging
from typing import Optional, BinaryIO
import PyPDF2
import pdfplumber
from docx import Document
import zipfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_file(uploaded_file) -> Optional[str]:
    """
    Extract text from uploaded file with enhanced error handling and multiple extraction methods
    """
    if not uploaded_file:
        logger.error("No file provided")
        return None
    
    try:
        file_extension = uploaded_file.name.lower().split('.')[-1]
        logger.info(f"Processing file: {uploaded_file.name} (type: {file_extension})")
        
        if file_extension == 'pdf':
            return extract_text_from_pdf(uploaded_file)
        elif file_extension == 'docx':
            return extract_text_from_docx(uploaded_file)
        elif file_extension == 'txt':
            return extract_text_from_txt(uploaded_file)
        else:
            logger.error(f"Unsupported file type: {file_extension}")
            st.error(f"❌ Unsupported file type: {file_extension}. Please use PDF, DOCX, or TXT files.")
            return None
    
    except Exception as e:
        logger.error(f"Error extracting text from {uploaded_file.name}: {str(e)}")
        st.error(f"❌ Error processing file {uploaded_file.name}: {str(e)}")
        return None

def extract_text_from_pdf(uploaded_file) -> Optional[str]:
    """Extract text from PDF file using multiple methods for better reliability"""
    try:
        # Reset file pointer
        uploaded_file.seek(0)
        
        # Method 1: Try pdfplumber first (better for complex layouts)
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                text_content = []
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                        else:
                            logger.warning(f"No text found on page {page_num + 1} using pdfplumber")
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1} with pdfplumber: {str(e)}")
                        continue
                
                if text_content:
                    full_text = '\n\n'.join(text_content)
                    logger.info(f"Successfully extracted {len(full_text)} characters using pdfplumber")
                    return clean_extracted_text(full_text)
        
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {str(e)}, trying PyPDF2")
        
        # Method 2: Fallback to PyPDF2
        uploaded_file.seek(0)
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text_content = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                    else:
                        logger.warning(f"No text found on page {page_num + 1} using PyPDF2")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1} with PyPDF2: {str(e)}")
                    continue
            
            if text_content:
                full_text = '\n\n'.join(text_content)
                logger.info(f"Successfully extracted {len(full_text)} characters using PyPDF2")
                return clean_extracted_text(full_text)
        
        except Exception as e:
            logger.error(f"PyPDF2 extraction also failed: {str(e)}")
        
        # If both methods fail
        logger.error("Both PDF extraction methods failed")
        st.error("❌ Could not extract text from PDF. The file might be corrupted, password-protected, or contain only images.")
        return None
    
    except Exception as e:
        logger.error(f"PDF processing error: {str(e)}")
        st.error(f"❌ Error processing PDF file: {str(e)}")
        return None

def extract_text_from_docx(uploaded_file) -> Optional[str]:
    """Extract text from DOCX file with enhanced error handling"""
    try:
        uploaded_file.seek(0)
        
        # Create a temporary file to work with python-docx
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file.flush()
            
            try:
                # Open the document
                doc = Document(tmp_file.name)
                text_content = []
                
                # Extract text from paragraphs
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        text_content.append(paragraph.text)
                
                # Extract text from tables
                for table in doc.tables:
                    for row in table.rows:
                        row_text = []
                        for cell in row.cells:
                            if cell.text.strip():
                                row_text.append(cell.text.strip())
                        if row_text:
                            text_content.append(' | '.join(row_text))
                
                # Extract text from headers/footers if needed
                for section in doc.sections:
                    if section.header:
                        for paragraph in section.header.paragraphs:
                            if paragraph.text.strip():
                                text_content.append(paragraph.text)
                    
                    if section.footer:
                        for paragraph in section.footer.paragraphs:
                            if paragraph.text.strip():
                                text_content.append(paragraph.text)
                
                if text_content:
                    full_text = '\n\n'.join(text_content)
                    logger.info(f"Successfully extracted {len(full_text)} characters from DOCX")
                    return clean_extracted_text(full_text)
                else:
                    logger.warning("No text content found in DOCX file")
                    st.warning("⚠️ The DOCX file appears to be empty or contains no readable text.")
                    return None
            
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
    
    except zipfile.BadZipFile:
        logger.error("Invalid DOCX file format")
        st.error("❌ Invalid DOCX file format. Please ensure the file is not corrupted.")
        return None
    
    except Exception as e:
        logger.error(f"DOCX processing error: {str(e)}")
        st.error(f"❌ Error processing DOCX file: {str(e)}")
        return None

def extract_text_from_txt(uploaded_file) -> Optional[str]:
    """Extract text from TXT file with encoding detection"""
    try:
        uploaded_file.seek(0)
        
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                uploaded_file.seek(0)
                content = uploaded_file.read()
                
                if isinstance(content, bytes):
                    text_content = content.decode(encoding)
                else:
                    text_content = content
                
                if text_content.strip():
                    logger.info(f"Successfully extracted {len(text_content)} characters from TXT using {encoding}")
                    return clean_extracted_text(text_content)
            
            except (UnicodeDecodeError, UnicodeError):
                logger.warning(f"Failed to decode TXT file with {encoding}")
                continue
        
        logger.error("Could not decode TXT file with any supported encoding")
        st.error("❌ Could not read the text file. Please ensure it uses a supported encoding (UTF-8, Latin-1, etc.).")
        return None
    
    except Exception as e:
        logger.error(f"TXT processing error: {str(e)}")
        st.error(f"❌ Error processing TXT file: {str(e)}")
        return None

def clean_extracted_text(text: str) -> str:
    """Clean and normalize extracted text"""
    if not text:
        return ""
    
    # Remove excessive whitespace and normalize line breaks
    import re
    
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Replace multiple line breaks with double line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Remove excessive empty lines at the beginning and end
    text = text.strip()
    
    # Ensure minimum text length
    if len(text.strip()) < 50:
        logger.warning(f"Extracted text is very short ({len(text)} characters)")
    
    return text

def validate_file_size(uploaded_file, max_size_mb: int = 10) -> bool:
    """Validate file size"""
    try:
        file_size = len(uploaded_file.read())
        uploaded_file.seek(0)  # Reset file pointer
        
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            st.error(f"❌ File too large. Maximum size allowed: {max_size_mb}MB. Your file: {file_size / (1024*1024):.1f}MB")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"File size validation error: {str(e)}")
        return True  # Allow processing if validation fails

def save_uploaded_file(uploaded_file, directory: str = None) -> Optional[str]:
    """Save uploaded file to temporary directory and return path"""
    try:
        if directory is None:
            directory = tempfile.gettempdir()
        
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Create safe filename
        safe_filename = "".join(c for c in uploaded_file.name if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()
        file_path = os.path.join(directory, safe_filename)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.read())
        
        # Reset file pointer
        uploaded_file.seek(0)
        
        logger.info(f"File saved to: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        return None

def get_file_info(uploaded_file) -> dict:
    """Get comprehensive file information"""
    try:
        file_info = {
            'name': uploaded_file.name,
            'size': len(uploaded_file.read()),
            'type': uploaded_file.type,
            'extension': uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
        }
        
        uploaded_file.seek(0)  # Reset file pointer
        
        # Add size in readable format
        size_bytes = file_info['size']
        if size_bytes < 1024:
            file_info['size_readable'] = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            file_info['size_readable'] = f"{size_bytes / 1024:.1f} KB"
        else:
            file_info['size_readable'] = f"{size_bytes / (1024 * 1024):.1f} MB"
        
        return file_info
    
    except Exception as e:
        logger.error(f"Error getting file info: {str(e)}")
        return {
            'name': getattr(uploaded_file, 'name', 'Unknown'),
            'size': 0,
            'size_readable': 'Unknown',
            'type': 'Unknown',
            'extension': ''
        }

def is_supported_file_type(filename: str) -> bool:
    """Check if file type is supported"""
    if not filename:
        return False
    
    supported_extensions = {'pdf', 'docx', 'txt'}
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    return file_extension in supported_extensions

def batch_validate_files(uploaded_files) -> tuple:
    """Validate multiple uploaded files and return valid and invalid files"""
    valid_files = []
    invalid_files = []
    
    for uploaded_file in uploaded_files:
        try:
            # Check file type
            if not is_supported_file_type(uploaded_file.name):
                invalid_files.append({
                    'file': uploaded_file,
                    'reason': f"Unsupported file type: {uploaded_file.name.split('.')[-1]}"
                })
                continue
            
            # Check file size
            if not validate_file_size(uploaded_file, max_size_mb=10):
                invalid_files.append({
                    'file': uploaded_file,
                    'reason': "File too large (>10MB)"
                })
                continue
            
            valid_files.append(uploaded_file)
        
        except Exception as e:
            invalid_files.append({
                'file': uploaded_file,
                'reason': f"Validation error: {str(e)}"
            })
    
    return valid_files, invalid_files
