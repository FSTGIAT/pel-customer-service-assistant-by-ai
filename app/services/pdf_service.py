import json

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
import hashlib
from app.core.database import db 
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

    def _validate_pdf(self, file_path: str) -> Tuple[bool, str, int]:
        """Validate PDF file - changed to sync function"""
        try:
            with open(file_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                _ = pdf.pages[0].extract_text()
                return True, pdf.pages[0].extract_text()[:200], len(pdf.pages)
        except Exception as e:
            self.logger.error(f"PDF validation failed for {file_path}: {str(e)}")
            return False, str(e), 0

    async def get_customer_pdfs(self, customer_id: str) -> List[PDFMetadata]:
        """Get the last 5 valid PDFs for a customer with database caching."""
        try:
            self.logger.info(f"Searching PDFs for customer: {customer_id}")
            customer_base = customer_id.split('_')[0]
            pdf_files = []

            # First try to get from database
            query = """
                SELECT 
                    path,
                    filename as name,
                    date,
                    url,
                    pages,
                    size,
                    preview,
                    is_valid,
                    customer_id
                FROM telecom.pdf_documents 
                WHERE customer_id = $1 
                ORDER BY date DESC 
                LIMIT 5
            """
            
            cached_pdfs = await db.fetch_all(query, customer_base)
            
            if cached_pdfs:
                self.logger.debug(f"Found {len(cached_pdfs)} cached PDFs in database")
                return [PDFMetadata(
                    path=pdf['path'],
                    name=pdf['name'],
                    date=pdf['date'],
                    url=f"/api/pdf/view/{pdf['name']}",
                    pages=pdf['pages'],
                    size=pdf['size'],
                    preview=pdf['preview'],
                    is_valid=pdf['is_valid'],
                    customer_id=pdf['customer_id']
                ) for pdf in cached_pdfs]

            # If not in database, scan directory
            self.logger.info("No cached PDFs found, scanning directory")
            for file in os.listdir(self.base_directory):
                if not (file.startswith(customer_base) and file.endswith('.pdf')):
                    continue
                
                full_path = os.path.join(self.base_directory, file)
                
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

                    # Calculate hash for tracking changes
                    content_hash = self._calculate_file_hash(full_path)

                    # Store in database for future use
                    insert_query = """
                        INSERT INTO telecom.pdf_documents 
                        (customer_id, filename, path, date, pages, size, preview, 
                        content_hash, is_valid, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (content_hash) DO UPDATE 
                        SET preview = EXCLUDED.preview,
                            is_valid = EXCLUDED.is_valid,
                            date = EXCLUDED.date
                        RETURNING id
                    """
                    
                    metadata_json = {
                        'last_validated': datetime.now().isoformat(),
                        'file_size': os.path.getsize(full_path),
                        'validation_info': 'Scanned during directory check'
                    }

                    await db.execute(
                        insert_query,
                        customer_base,
                        file,
                        full_path,
                        file_date,
                        total_pages,
                        os.path.getsize(full_path),
                        preview_text,
                        content_hash,
                        is_valid,
                        metadata_json
                    )

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
        try:
            content_hash = self._calculate_file_hash(file_path)
            
            # Try cache first
            cache_query = """
                SELECT content FROM telecom.pdf_content_cache 
                WHERE content_hash = $1 AND page_number = $2
            """
            cached_content = await db.fetch_one(cache_query, content_hash, page_number)
            
            if cached_content:
                return self._fix_hebrew_text(cached_content['content'])

            # Direct file reading if cache miss
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if page_number is not None:
                    if 0 <= page_number < len(pdf_reader.pages):
                        text = pdf_reader.pages[page_number].extract_text()
                    else:
                        raise HTTPException(status_code=400, 
                                        detail=f"Invalid page number. PDF has {len(pdf_reader.pages)} pages")
                else:
                    text = '\n'.join(page.extract_text() for page in pdf_reader.pages)

                text = self._fix_hebrew_text(text)
                
                # Cache in background
                await db.execute(
                    """
                    INSERT INTO telecom.pdf_content_cache 
                    (content_hash, page_number, content)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (content_hash, page_number) 
                    DO UPDATE SET content = EXCLUDED.content
                    """,
                    content_hash, page_number, text
                )
                
                return text

        except Exception as e:
            self.logger.error(f"Error extracting PDF text: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _fix_hebrew_text(self, text: str) -> str:
        """Enhanced Hebrew text cleanup with improved handling"""
        try:
            if not text:
                return ""
                
            # Remove extra spaces between Hebrew characters
            text = re.sub(r'(?<=[\u0590-\u05FF])\s+(?=[\u0590-\u05FF])', '', text)
            
            # Fix common Hebrew letter substitutions
            hebrew_replacements = {
                '×': 'א',
                '÷': 'ח',
                'ñ': 'ם',
                'í': 'ן',
                'ó': 'ס',
                'ú': 'ץ',
                'ö': 'צ',
                # Common PDF encoding issues
                '\u200e': '',  # Left-to-Right Mark
                '\u200f': '',  # Right-to-Left Mark
                '\u202a': '',  # Left-to-Right Embedding
                '\u202b': '',  # Right-to-Left Embedding
                '\u202c': '',  # Pop Directional Formatting
                '¬': '',       # Soft hyphen
            }
            
            for old, new in hebrew_replacements.items():
                text = text.replace(old, new)
            
            # Remove Hebrew vowel points (nikkud)
            text = re.sub(r'[\u0591-\u05C7]', '', text)
            
            # Normalize spaces and line endings
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            # Add RTL marker for Hebrew text blocks
            text = re.sub(
                r'([\u0590-\u05FF]+)',
                lambda m: f'[{m.group(1)}]{{dir="rtl"}}',
                text
            )
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error in Hebrew text cleanup: {str(e)}")
            return text  # Return original text if cleanup fails



    async def get_customer_pdfs(self, customer_id: str) -> List[PDFMetadata]:
        try:
            self.logger.info(f"Searching PDFs for customer: {customer_id}")
            customer_base = customer_id.split('_')[0]

            # Try database first
            query = """
                SELECT 
                    path,
                    filename as name,
                    date,
                    pages,
                    size,
                    preview,
                    is_valid,
                    customer_id,
                    content_hash,
                    url
                FROM telecom.pdf_documents 
                WHERE customer_id = $1 
                    AND is_valid = true
                ORDER BY date DESC 
                LIMIT 5
            """
            
            pdf_files = []
            for file in os.listdir(self.base_directory):
                if not (file.startswith(customer_base) and file.endswith('.pdf')):
                    continue
                
                full_path = os.path.join(self.base_directory, file)
                try:
                    metadata = await self._process_and_store_pdf(full_path, customer_base)
                    if metadata:
                        pdf_files.append(metadata)
                except Exception as e:
                    self.logger.error(f"Error processing PDF {file}: {str(e)}")
                    continue

            if not pdf_files:
                self.logger.warning(f"No valid PDFs found for customer {customer_id}")
                return []

            return sorted(pdf_files, key=lambda x: x.date, reverse=True)[:5]

        except Exception as e:
            error_msg = f"Error accessing PDFs: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

    async def _process_and_store_pdf(self, file_path: str, customer_id: str) -> Optional[PDFMetadata]:
        try:
            file_name = os.path.basename(file_path)
            file_date = self._parse_date_from_filename(file_name)
            is_valid, preview_text, total_pages = self._validate_pdf(file_path)
            content_hash = self._calculate_file_hash(file_path)
            
            if not is_valid:
                return None

            query = """
                INSERT INTO telecom.pdf_documents 
                (customer_id, filename, path, date, pages, size, preview, content_hash, is_valid, metadata, url)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (content_hash) 
                DO UPDATE SET 
                    date = EXCLUDED.date,
                    preview = EXCLUDED.preview,
                    is_valid = EXCLUDED.is_valid,
                    metadata = EXCLUDED.metadata
                RETURNING id, path, filename, date, pages, size, preview, is_valid, customer_id, url
            """
            
            metadata = json.dumps({
                'last_validated': datetime.now().isoformat(),
                'file_size': os.path.getsize(file_path)
            })

            url = f"/api/pdf/view/{file_name}"
            
            result = await db.fetch_one(
                query,
                customer_id,
                file_name,
                str(file_path),
                file_date,
                total_pages,
                os.path.getsize(file_path),
                preview_text,
                content_hash,
                is_valid,
                metadata,
                url
            )

            if result:
                return PDFMetadata(
                    path=result['path'],
                    name=result['filename'],
                    date=result['date'],
                    url=result['url'],
                    pages=result['pages'],
                    size=result['size'],
                    preview=result['preview'],
                    is_valid=result['is_valid'],
                    customer_id=result['customer_id']
                )

        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return None


    async def _calculate_file_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
            

    async def _extract_and_cache_text(self, file_path: str, content_hash: str, page_number: Optional[int]) -> str:
        """Extract text and store in cache"""
        with open(file_path, 'rb') as file:
            pdf = PyPDF2.PdfReader(file)
            
            if page_number is not None:
                if 0 <= page_number < len(pdf.pages):
                    text = pdf.pages[page_number].extract_text()
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid page number. PDF has {len(pdf.pages)} pages"
                    )
            else:
                text = '\n'.join(page.extract_text() for page in pdf.pages)

            # Store in cache
            cache_query = """
                INSERT INTO telecom.pdf_content_cache 
                (content_hash, page_number, content)
                VALUES ($1, $2, $3)
                ON CONFLICT (content_hash, page_number) 
                DO UPDATE SET content = EXCLUDED.content
            """
            await db.execute(cache_query, content_hash, page_number, text)
            
            return text

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        

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

