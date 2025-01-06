from typing import Dict, List, Optional
import re
from dataclasses import dataclass
from app.utils.custom_logger import logger

@dataclass
class TextSegment:
    text: str
    normalized: str
    start_pos: int
    end_pos: int

class BillTextProcessor:
    """Text preprocessing layer for Telecom bill processing"""

    def __init__(self):
        self.debug = True
        # Common Hebrew OCR fixes
        self.ocr_fixes = {
            'נוו': 'ניו',
            'ס"כ': 'סה"כ',
            'ש"ח': '₪',
            'ש״ח': '₪',
            'שח': '₪',
            'מעמ': 'מע"מ',
            'מע״מ': 'מע"מ',
            '05O': '050',  # Common OCR mistake with zero
            '051': '050'   # Number correction if needed
        }
        
        # Section markers with context
        self.section_markers = {
            "charges": {
                "start": ["חיובים קבועים", "תשלום חודשי קבוע"],
                "end": ["חיובים משתנים", "חיובים חד פעמיים"]
            },
            "usage": {
                "start": ["פירוט שיחות", "צריכת דקות"],
                "end": ["סה\"כ חיובים", "שיעור שימוש"]
            }
        }

    def process(self, text: str) -> str:
        """Main processing pipeline"""
        try:
            if self.debug:
                logger.debug(f"Processing text of length: {len(text)}")

            processed = text
            processed = self._fix_ocr_errors(processed)
            processed = self._standardize_formats(processed)
            processed = self._add_section_markers(processed)

            if self.debug:
                logger.debug(f"Processing complete. New length: {len(processed)}")

            return processed

        except Exception as e:
            logger.error(f"Error in text processing: {str(e)}")
            return text

    def _fix_ocr_errors(self, text: str) -> str:
        """Fix common OCR errors in Hebrew text"""
        try:
            fixed = text
            for error, correction in self.ocr_fixes.items():
                fixed = fixed.replace(error, correction)
                
            # Fix spacing around numbers
            fixed = re.sub(r'(\d+)\s*₪', r'\1 ₪', fixed)
            
            if self.debug:
                diff_count = sum(1 for i, j in zip(text, fixed) if i != j)
                if diff_count:
                    logger.debug(f"Fixed {diff_count} OCR errors")
                    
            return fixed

        except Exception as e:
            logger.error(f"Error fixing OCR errors: {str(e)}")
            return text

    def _standardize_formats(self, text: str) -> str:
        """Standardize number and date formats"""
        try:
            standardized = text
            
            # Standardize numbers with thousands separator
            standardized = re.sub(r'(\d),(\d)', r'\1\2', standardized)
            
            # Standardize date formats
            date_pattern = r'(\d{2})/(\d{2})/(\d{4})'
            standardized = re.sub(date_pattern, r'\1/\2/\3', standardized)

            # Standardize phone numbers
            phone_pattern = r'(\d{3})-?(\d{7})'
            standardized = re.sub(phone_pattern, r'\1-\2', standardized)

            return standardized

        except Exception as e:
            logger.error(f"Error standardizing formats: {str(e)}")
            return text

    def _add_section_markers(self, text: str) -> str:
        """Add machine-readable markers for section identification"""
        try:
            marked = text
            for section, markers in self.section_markers.items():
                for start in markers["start"]:
                    marked = marked.replace(
                        start,
                        f"[SECTION_{section.upper()}_START]{start}"
                    )
                for end in markers["end"]:
                    marked = marked.replace(
                        end,
                        f"{end}[SECTION_{section.upper()}_END]"
                    )
            return marked

        except Exception as e:
            logger.error(f"Error adding section markers: {str(e)}")
            return text

    def extract_section(self, text: str, section_name: str) -> Optional[TextSegment]:
        """Extract specific section with position information"""
        try:
            if section_name not in self.section_markers:
                return None
                
            markers = self.section_markers[section_name]
            
            # Find start position
            start_pos = -1
            for start_marker in markers["start"]:
                pos = text.find(start_marker)
                if pos != -1:
                    start_pos = pos
                    break
                    
            if start_pos == -1:
                return None
                
            # Find end position
            end_pos = len(text)
            for end_marker in markers["end"]:
                pos = text.find(end_marker, start_pos)
                if pos != -1:
                    end_pos = pos
                    break
                    
            section_text = text[start_pos:end_pos].strip()
            normalized = self.process(section_text)
            
            return TextSegment(
                text=section_text,
                normalized=normalized,
                start_pos=start_pos,
                end_pos=end_pos
            )

        except Exception as e:
            logger.error(f"Error extracting section {section_name}: {str(e)}")
            return None

# Integration function for your existing TelecomBillProcessor
def enhance_bill_processor(processor):
    """Add text processing capabilities to existing bill processor"""
    text_processor = BillTextProcessor()
    
    # Store original method
    original_process = processor.process_bill
    
    def enhanced_process_bill(content: str) -> Dict:
        # Preprocess text
        processed_content = text_processor.process(content)
        # Call original processing with enhanced text
        return original_process(processed_content)
        
    processor.process_bill = enhanced_process_bill
    return processor