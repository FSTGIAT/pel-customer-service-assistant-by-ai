import os
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from fastapi import HTTPException
from fastapi.responses import FileResponse
import PyPDF2
import re
from pathlib import Path
import logging
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PDFMetadata:
    """Structured metadata for PDF files"""
    path: str
    name: str
    date: datetime
    url: str
    pages: int
    size: int
    preview: str
    is_valid: bool
    customer_id: str

class PDFService:
    """Service for handling PDF operations with enhanced functionality"""
    
    def __init__(self, base_directory: str):
        """Initialize with base directory for PDFs"""
        self.base_directory = base_directory
        self.debug = True
        
        # Set up logging first
        self._setup_logging()
        
        # Then ensure directory exists
        self._ensure_directory_exists()

    def _setup_logging(self):
        """Configure logging for PDF operations"""
        # Create logger
        self.logger = logging.getLogger('pdf_service')
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            # Add file handler
            log_dir = Path(self.base_directory).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_path = log_dir / 'pdf_operations.log'
            
            file_handler = logging.FileHandler(str(log_path))
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)

            # Add console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(levelname)s - %(message)s')
            )
            self.logger.addHandler(console_handler)
            
            self.logger.info("Logging initialized")

    def _ensure_directory_exists(self):
        """Ensure the PDF directory exists"""
        try:
            os.makedirs(self.base_directory, exist_ok=True)
            self.logger.info(f"Using PDF directory: {self.base_directory}")
        except Exception as e:
            self.logger.error(f"Error creating directory: {str(e)}")
            raise


    def _parse_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from filename with format checking"""
        try:
            # Extract date portion from filename (e.g., "07012024" from "3694388_07012024.pdf")
            date_match = re.search(r'_(\d{8})', filename)
            if not date_match:
                return None
            
            date_str = date_match.group(1)
            return datetime.strptime(date_str, '%d%m%Y')
        except Exception as e:
            self.logger.warning(f"Failed to parse date from filename {filename}: {str(e)}")
            return None

    async def _validate_pdf(self, file_path: str) -> Tuple[bool, str, int]:
        """Validate PDF file and return basic metadata"""
        try:
            with open(file_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                # Check if we can read at least one page
                _ = pdf.pages[0].extract_text()
                return True, pdf.pages[0].extract_text()[:200], len(pdf.pages)
        except Exception as e:
            self.logger.error(f"PDF validation failed for {file_path}: {str(e)}")
            return False, str(e), 0

    async def get_customer_pdfs(self, customer_id: str) -> List[PDFMetadata]:
        """Get the last 5 valid PDFs for a customer with enhanced metadata."""
        try:
            self.logger.info(f"Searching PDFs for customer: {customer_id}")
            pdf_files = []
            customer_base = customer_id.split('_')[0]
            
            # Get all matching PDF files
            for file in os.listdir(self.base_directory):
                if not (file.startswith(customer_base) and file.endswith('.pdf')):
                    continue
                
                full_path = os.path.join(self.base_directory, file)
                
                # Get file metadata
                try:
                    file_date = self._parse_date_from_filename(file)
                    if not file_date:
                        self.logger.warning(f"Invalid date format in filename: {file}")
                        continue

                    # Validate PDF and get metadata
                    is_valid, preview_text, total_pages = await self._validate_pdf(full_path)
                    
                    if not is_valid:
                        self.logger.warning(f"Invalid PDF file: {file}")
                        continue

                    metadata = PDFMetadata(
                        path=full_path,
                        name=file,
                        date=file_date,
                        url=f"/api/pdf/view/{file}",
                        pages=total_pages,
                        size=os.path.getsize(full_path),
                        preview=preview_text,
                        is_valid=is_valid,
                        customer_id=customer_base
                    )
                    
                    pdf_files.append(metadata)
                    self.logger.debug(f"Added PDF: {file} with {total_pages} pages")
                    
                except Exception as e:
                    self.logger.error(f"Error processing PDF {file}: {str(e)}")
                    continue
            
            if not pdf_files:
                self.logger.warning(f"No valid PDFs found for customer {customer_id}")
                return []
            
            # Sort by date and get last 5
            pdf_files.sort(key=lambda x: x.date, reverse=True)
            return pdf_files[:5]
            
        except Exception as e:
            error_msg = f"Error accessing PDFs: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    async def extract_pdf_text(self, file_path: str, page_number: Optional[int] = None) -> str:
        """Extract text from PDF file with enhanced Hebrew text handling."""
        try:
            self.logger.info(f"Extracting text from PDF: {file_path}")

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if page_number is not None:
                    if 0 <= page_number < len(pdf_reader.pages):
                        text = pdf_reader.pages[page_number].extract_text()
                        text = self._fix_hebrew_text(text)
                        self.logger.debug(f"Extracted text from page {page_number}")
                        return text
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid page number. PDF has {len(pdf_reader.pages)} pages"
                        )
                
                # Extract from all pages
                pdf_text = []
                for i, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    text = self._fix_hebrew_text(text)
                    pdf_text.append(text)
                    self.logger.debug(f"Extracted text from page {i+1}")
                
                return "\n".join(pdf_text)

        except Exception as e:
            error_msg = f"Error extracting PDF text: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    def _fix_hebrew_text(self, text: str) -> str:
        """Enhanced Hebrew text cleanup with additional fixes"""
        # Remove extra spaces between Hebrew characters
        text = re.sub(r'(?<=[\u0590-\u05FF])\s+(?=[\u0590-\u05FF])', '', text)
        
        # Fix common Hebrew letter substitutions
        replacements = {
            '×': 'א',
            '÷': 'ח',
            'ñ': 'ם',
            'í': 'ן',
            'ó': 'ס',
            'ú': 'ץ',
            'ö': 'צ',
            # Add more replacements as needed
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Fix RTL markers and other special characters
        text = text.replace('\u200e', '').replace('\u200f', '')
        text = text.replace('\u0591', '').replace('\u0592', '')  # Remove Hebrew vowel points
        
        # Normalize spaces and line endings
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    async def get_pdf_metadata(self, file_path: str) -> Dict:
        """Get comprehensive PDF metadata"""
        try:
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="PDF not found")
                
            filename = os.path.basename(file_path)
            date = self._parse_date_from_filename(filename)
            is_valid, preview, pages = await self._validate_pdf(file_path)
            
            return {
                "filename": filename,
                "date": date.isoformat() if date else None,
                "pages": pages,
                "size": os.path.getsize(file_path),
                "preview": preview if is_valid else None,
                "is_valid": is_valid,
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            }
                
        except Exception as e:
            error_msg = f"Error getting PDF metadata: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

# Create PDF service instance
pdf_service = PDFService("/root/telecom-customer-service/pdf-test")