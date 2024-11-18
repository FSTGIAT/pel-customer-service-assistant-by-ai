from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
import json
from app.utils.custom_logger import logger

@dataclass
class BillSection:
    name: str
    start_marker: str
    end_marker: str
    content: str = ""

@dataclass
class UsageDetails:
    calls: Dict[str, str]        
    calls_minutes: Dict[str, float]
    sms: int
    data_mb: float
    package: Dict[str, str]

    def to_dict(self):
        """Convert UsageDetails to a dictionary"""
        return {
            'calls': self.calls,
            'calls_minutes': self.calls_minutes,
            'sms': self.sms,
            'data_mb': self.data_mb,
            'package': self.package
        }

@dataclass
class BillData:
    total_amount: float = 0.0
    billing_period: str = ""
    phones: List[str] = None
    usage: Dict[str, UsageDetails] = None
    charges: Dict[str, float] = None

    def __post_init__(self):
        self.phones = self.phones or []
        self.usage = self.usage or {}
        self.charges = self.charges or {}

class TelecomBillProcessor:
    def __init__(self):
        self.content = ""
        self.debug = True
        self.sections = {
            "summary": BillSection(
                name="summary",
                # Update these markers to match your PDF
                start_marker="פירוט חשבון",  # Changed from "סיכום החשבון"
                end_marker="פירוט שירותים"
            ),
            "fixed_charges": BillSection(
                name="fixed_charges",
                start_marker="תשלום חודשי קבוע",  # Changed from "חיובים קבועים למנוי"
                end_marker="חיובים חד פעמיים"
            ),
            "usage": BillSection(
                name="usage",
                start_marker="פירוט שיחות",  # Changed from "צריכת דקות והודעות SMS"
                end_marker="סה\"כ חיובים"
            ),
            "packages": BillSection(
                name="packages",
                start_marker="פירוט חבילות",  # Changed from "שיעור שימוש בחבילות"
                end_marker="סיכום חיובים"
            )
        }

    # Update process_bill method to use the correct method name
    def process_bill(self, content: str) -> Dict:
        """Process complete bill with all subscriber data"""
        self.content = content
        try:
            if self.debug:
                logger.info("Starting bill processing...")
                
            self._extract_sections()
            phones = self.extract_phone_numbers()
            total_amount = self._extract_total_amount()
            
            bill_data = {
                "total_amount": total_amount,
                "billing_period": self._extract_billing_period(),
                "phones": phones,
                "usage": {},
                "charges": self._extract_service_charges()
            }
            
            # Process each subscriber using new method
            for phone in phones:
                subscriber_data = self._extract_subscriber_usage(phone)
                bill_data["usage"][phone] = subscriber_data
                if self.debug:
                    logger.info(f"Processed data for {phone}: {json.dumps(subscriber_data, ensure_ascii=False)}")
                    
            if self.debug:
                logger.info(f"Processed bill data: {json.dumps(bill_data, ensure_ascii=False)}")
                
            return bill_data
                    
        except Exception as e:
            logger.error(f"Error processing bill: {str(e)}")
            return {}


    def _analyze_content(self):
        """Analyze the content for debugging purposes"""
        try:
            logger.debug("\n=== CONTENT ANALYSIS ===")
            logger.debug(f"Content length: {len(self.content)}")
            
            # Look for key phrases
            key_phrases = [
                "סיכום החשבון",
                "חיובים קבועים",
                "מספר פלאפון",
                "צריכת דקות",
                "שיעור שימוש"
            ]
            
            logger.debug("\nKey phrase positions:")
            for phrase in key_phrases:
                pos = self.content.find(phrase)
                if pos != -1:
                    logger.debug(f"'{phrase}' found at position {pos}")
                    context = self.content[max(0, pos-20):min(len(self.content), pos+50)]
                    logger.debug(f"Context: ...{context}...")
                else:
                    logger.debug(f"'{phrase}' not found")
                    
            # Look for phone numbers
            phone_pattern = r'050-\d{7}'
            phones = re.findall(phone_pattern, self.content)
            logger.debug(f"\nFound phone numbers: {phones}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return False

    def _extract_subscriber_usage(self, phone_number: str) -> Dict:
        """Extract complete usage details for a specific subscriber"""
        try:
            subscriber_data = {}
            
            # 1. Get fixed charges section for this subscriber
            fixed_section = self._get_subscriber_section(phone_number, "fixed")
            if fixed_section:
                # Monthly fee
                if fee_match := re.search(r'תשלום חודשי קבוע.*?(\d+\.\d+)', fixed_section):
                    subscriber_data['monthly_fee'] = float(fee_match.group(1))
                    if self.debug:
                        logger.debug(f"Found monthly fee for {phone_number}: {subscriber_data['monthly_fee']}")
                
                # Services like CYBER
                if cyber_match := re.search(r'CYBER.*?Pelephone.*?(\d+\.\d+)', fixed_section):
                    subscriber_data['services'] = {'cyber': float(cyber_match.group(1))}
                    if self.debug:
                        logger.debug(f"Found services for {phone_number}: {subscriber_data['services']}")

            # 2. Get usage section for this subscriber
            usage_section = self._get_subscriber_section(phone_number, "usage")
            if usage_section:
                # Calls
                call_pattern = f"{phone_number}\\s+שיחות\\s+(\\d+:\\d+)\\s+(\\d+:\\d+)\\s+(\\d+:\\d+)\\s+(\\d+:\\d+)"
                if call_match := re.search(call_pattern, usage_section):
                    subscriber_data['calls'] = {
                        'internal': call_match.group(1),
                        'external': call_match.group(2),
                        'landline': call_match.group(3),
                        'total': call_match.group(4)
                    }
                    subscriber_data['minutes'] = {
                        key: self._convert_time_to_minutes(value)
                        for key, value in subscriber_data['calls'].items()
                    }
                    if self.debug:
                        logger.debug(f"Found calls for {phone_number}: {subscriber_data['calls']}")

                # SMS
                sms_pattern = f"SMS/MMS\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)\\s+(\\d+)"
                if sms_match := re.search(sms_pattern, usage_section):
                    subscriber_data['sms'] = {
                        'internal': int(sms_match.group(1)),
                        'external': int(sms_match.group(2)),
                        'received': int(sms_match.group(3)),
                        'total': int(sms_match.group(4))
                    }
                    if self.debug:
                        logger.debug(f"Found SMS for {phone_number}: {subscriber_data['sms']}")

            # 3. Get package usage for this subscriber
            package_section = self._get_subscriber_section(phone_number, "package")
            if package_section:
                # Minutes package
                minutes_pattern = f"{phone_number}.*?דקות שיחה\\s+(\\d+:\\d+)\\s+(\\d+:\\d+)\\s+(\\d+)"
                if minutes_match := re.search(minutes_pattern, package_section):
                    subscriber_data['package'] = {
                        'minutes': {
                            'limit': minutes_match.group(1),
                            'usage': minutes_match.group(2),
                            'percent': int(minutes_match.group(3))
                        }
                    }

                # Data package
                data_pattern = f"{phone_number}.*?גלישה באינטרנט בארץ.*?MB\\s+(\\d+)\\s+([0-9.]+)\\s+(\\d+)"
                if data_match := re.search(data_pattern, package_section):
                    if 'package' not in subscriber_data:
                        subscriber_data['package'] = {}
                    subscriber_data['package']['data'] = {
                        'limit_mb': int(data_match.group(1)),
                        'usage_mb': float(data_match.group(2)),
                        'percent': int(data_match.group(3))
                    }
                
                if self.debug:
                    logger.debug(f"Found package details for {phone_number}: {subscriber_data.get('package', {})}")

            # Calculate total charges for this subscriber
            subscriber_total = subscriber_data.get('monthly_fee', 0)
            if 'services' in subscriber_data:
                subscriber_total += sum(subscriber_data['services'].values())
            subscriber_data['total_charges'] = subscriber_total

            if self.debug:
                logger.info(f"Complete data for {phone_number}: {json.dumps(subscriber_data, ensure_ascii=False)}")

            return subscriber_data

        except Exception as e:
            logger.error(f"Error extracting subscriber usage for {phone_number}: {e}", exc_info=True)
            return {}


    def _get_subscriber_section(self, phone_number: str, section_type: str) -> str:
        """Get section specific to a subscriber"""
        try:
            patterns = {
                "fixed": f"חיובים קבועים למנוי {phone_number}.*?(?=חיובים קבועים למנוי|חיובים משתנים למנוי|$)",
                "usage": f"חיובים משתנים למנוי {phone_number}.*?(?=חיובים משתנים למנוי|שיעור שימוש|$)",
                "package": f"שיעור שימוש בחבילות.*?{phone_number}.*?(?=תיבת ההודעות|$)"
            }
            
            if pattern := patterns.get(section_type):
                if match := re.search(pattern, self.content, re.DOTALL):
                    section = match.group(0)
                    if self.debug:
                        logger.debug(f"Found {section_type} section for {phone_number}, length: {len(section)}")
                    return section
            return ""
        except Exception as e:
            logger.error(f"Error getting {section_type} section for {phone_number}: {e}")
            return ""

    def _extract_phone_numbers(self) -> List[str]:
        """Extract all phone numbers from the bill content"""
        try:
            # Pattern for Israeli mobile numbers (050, 051, 052, 053, 054, 055, 058)
            pattern = r'(05\d-\d{7})'
            
            # First try to get phone numbers from summary section
            summary_section = self.sections["summary"].content
            if summary_section:
                numbers = re.findall(pattern, summary_section)
                if numbers:
                    if self.debug:
                        print(f"Found phone numbers in summary: {numbers}")
                    return list(set(numbers))  # Remove duplicates
            
            # If not found in summary, try fixed charges section
            fixed_charges = self.sections["fixed_charges"].content
            if fixed_charges:
                numbers = re.findall(pattern, fixed_charges)
                if numbers:
                    if self.debug:
                        print(f"Found phone numbers in fixed charges: {numbers}")
                    return list(set(numbers))
            
            # As a fallback, search in entire content
            numbers = re.findall(pattern, self.content)
            if numbers:
                if self.debug:
                    print(f"Found phone numbers in full content: {numbers}")
                return list(set(numbers))
            
            if self.debug:
                print("No phone numbers found")
            return []
            
        except Exception as e:
            print(f"Error extracting phone numbers: {str(e)}")
            return []

    def _validate_phone_number(self, phone: str) -> bool:
        """Validate if a phone number is a valid Israeli mobile number"""
        try:
            # Remove any spaces or special characters
            phone = re.sub(r'[^0-9-]', '', phone)
            
            # Check format: 05X-XXXXXXX where X is 0-9
            pattern = r'^05\d-\d{7}$'
            return bool(re.match(pattern, phone))
            
        except Exception as e:
            print(f"Error validating phone number {phone}: {str(e)}")
            return False


    def _extract_subscriber_amount(self, fixed_charges_content: str) -> float:
        """Extract subscriber amount from fixed charges section"""
        try:
            if fixed_charges_content:
                # Pattern to match דמי מנוי amount - fix the pattern to match your bill format
                pattern = r'דמי מנוי\s+(\d+\.\d+)'
                if match := re.search(pattern, fixed_charges_content):
                    amount = float(match.group(1))
                    if self.debug:
                        logger.info(f"Found subscriber amount from דמי מנוי: {amount} ₪")
                    return amount
                    
                # Secondary pattern for backup
                pattern2 = r'תשלום חודשי קבוע[^0-9]*(\d+\.\d+)'
                if match := re.search(pattern2, fixed_charges_content):
                    amount = float(match.group(1))
                    if self.debug:
                        logger.info(f"Found subscriber amount from תשלום חודשי קבוע: {amount} ₪")
                    return amount

            return 0.0

        except Exception as e:
            logger.error(f"Error extracting subscriber amount: {str(e)}")
            return 0.0


    def safe_extract(default_value):
        """Decorator for safe data extraction with default value"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                    return default_value
            return wrapper
        return decorator
            
    @safe_extract(0)
    def _extract_sms_count(self, phone_number: str) -> int:
        """Extract SMS details for specific subscriber"""
        try:
            # Look for SMS data in usage section
            usage_pattern = f"צריכת דקות והודעות.*?{phone_number}.*?SMS/MMS\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"
            
            if match := re.search(usage_pattern, self.content, re.DOTALL):
                # Sum all SMS counts (internal, external, etc.)
                sms_count = sum(int(count) for count in match.groups())
                
                if self.debug:
                    logger.info(f"Found SMS count for {phone_number}: {sms_count}")
                    # Log the matched content for verification
                    logger.debug(f"SMS match: {match.group(0)}")
                    
                return sms_count

            logger.warning(f"No SMS data found for {phone_number}")
            return 0
            
        except Exception as e:
            logger.error(f"Error extracting SMS count for {phone_number}: {e}")
            return 0

    def _extract_sections(self):
        """Extract all bill sections with debug info"""
        for section in self.sections.values():
            if self.debug:
                print(f"\nLooking for section {section.name}")
                print(f"Start marker: {section.start_marker}")
                print(f"End marker: {section.end_marker}")
                
            section.content = self._get_section(section.start_marker, section.end_marker)
            
            if self.debug:
                print(f"Found content: {'Yes' if section.content else 'No'}")
                if section.content:
                    print(f"Content sample: {section.content[:100]}")
                                
    def _get_section(self, start_marker: str, end_marker: str) -> str:
        """Extract content between markers with improved debugging"""
        try:
            if self.debug:
                print(f"\nSearching content for markers:")
                print(f"Start: '{start_marker}'")
                print(f"End: '{end_marker}'")
                print(f"Content sample: {self.content[:200]}")

            # First, check if markers exist
            if start_marker not in self.content:
                print(f"Warning: Start marker '{start_marker}' not found in content")
                return ""
            if end_marker not in self.content:
                print(f"Warning: End marker '{end_marker}' not found in content")
                return ""

            pattern = f"({re.escape(start_marker)}).*?(?={re.escape(end_marker)})"
            match = re.search(pattern, self.content, re.DOTALL)
            
            if match:
                section_content = match.group(0).strip()
                if self.debug:
                    print(f"Found section content: {section_content[:100]}...")
                return section_content

            if self.debug:
                print("No match found between markers")
            return ""

        except Exception as e:
            print(f"Error in get_section: {str(e)}")
            return ""
                
    def _extract_total_amount(self) -> float:
        """Extract total bill amount from first part of bill"""
        try:
            # Take just the first part of content where total appears
            first_section = self.content[:1000]  # First 1000 chars should include the total
            
            patterns = [
                # Exact pattern as appears in bill
                r'סה"כ\s+חשבון\s+נוכחי\s+כולל\s+מע"מ\s+([0-9]+\.[0-9]+)',
                # Alternative in case of different spacing/formatting
                r'סה"כ[^0-9]*כולל[^0-9]*מע"מ[^0-9]*([0-9]+\.[0-9]+)'
            ]

            for pattern in patterns:
                if match := re.search(pattern, first_section):
                    amount = float(match.group(1))
                    if self.debug:
                        logger.info(f"Found total amount in first section: {amount} ₪")
                        # Log exact matching text
                        logger.debug(f"Matched text: {match.group(0)}")
                        # Log surrounding context
                        start = max(0, match.start() - 50)
                        end = min(len(first_section), match.end() + 50)
                        logger.debug(f"Context: {first_section[start:end]}")
                    return amount

            # If no match found, log what we're searching in
            if self.debug:
                logger.debug("First section content:")
                logger.debug(first_section)
                # Look for key phrases
                if "סה\"כ" in first_section:
                    pos = first_section.find("סה\"כ")
                    logger.debug(f"Found סה\"כ at position {pos}")
                    logger.debug(f"Content after סה\"כ: {first_section[pos:pos+100]}")

            logger.warning("No total amount found")
            return 0.0

        except Exception as e:
            logger.error(f"Error extracting total amount: {str(e)}")
            logger.error(f"Content type: {type(self.content)}")
            return 0.0


    @safe_extract({})#toy
    def _extract_subscriber_charges(self, phone_number: str) -> Dict[str, float]:
        """Extract charges for specific subscriber"""
        try:
            # Look for the specific subscriber section
            subscriber_pattern = f"חיובים קבועים למנוי {phone_number}"
            start_pos = self.content.find(subscriber_pattern)
            
            if start_pos == -1:
                logger.warning(f"No charges section found for {phone_number}")
                return {}
                
            # Get content until next section or 1000 chars
            section_content = self.content[start_pos:start_pos+1000]
            
            charges = {}
            
            # Pattern for monthly fee
            monthly_pattern = r'תשלום חודשי קבוע.*?(\d+\.\d+)'
            if match := re.search(monthly_pattern, section_content):
                charges['monthly_fee'] = float(match.group(1))
                
            # Pattern for service charges
            service_patterns = {
                'cyber': r'CYBER.*?(\d+\.\d+)',
                'repairs': r'שירות תיקונים.*?(\d+\.\d+)',
                'data_package': r'חבילת גלישה.*?(\d+\.\d+)'
            }
            
            for service, pattern in service_patterns.items():
                if match := re.search(pattern, section_content):
                    charges[service] = float(match.group(1))

            if self.debug:
                logger.info(f"Found charges for {phone_number}: {charges}")
                
            return charges

        except Exception as e:
            logger.error(f"Error extracting charges for {phone_number}: {e}")
            return {}


    def _extract_billing_period(self) -> str:
        """Extract billing period with improved Hebrew pattern matching"""
        try:
            patterns = [
                r'תקופת\s+החשבון\s*:\s*(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})',
                r'תקופה\s*:\s*(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})',
                r'(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})',
                r'חשבון\s+לתקופה\s*:\s*(\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4})'
            ]
            
            # First try in summary section
            section = self.sections["summary"].content
            for pattern in patterns:
                # Try in summary section first
                if section:
                    if match := re.search(pattern, section):
                        if self.debug:
                            logger.info(f"Found billing period in summary: {match.group(1)}")
                        return match.group(1)
                
                # Try in full content if not found in summary
                if match := re.search(pattern, self.content):
                    if self.debug:
                        logger.info(f"Found billing period in full content: {match.group(1)}")
                    return match.group(1)

            if self.debug:
                logger.warning("No billing period found")
                logger.debug(f"Content sample: {self.content[:200]}")
            return ""

        except Exception as e:
            logger.error(f"Error extracting billing period: {str(e)}")
            return ""

    def extract_phone_numbers(self) -> List[str]:
        """Extract phone numbers with improved pattern matching"""
        try:
            # Try both summary section and full content
            search_text = self.sections["summary"].content or self.content
            
            # Pattern for phone numbers
            pattern = r'(050-[0-9]{7}|051-[0-9]{7}|052-[0-9]{7}|053-[0-9]{7}|054-[0-9]{7}|055-[0-9]{7}|058-[0-9]{7})'
            matches = re.findall(pattern, search_text)
            
            # Filter out service numbers
            service_numbers = {'050-7078888', '050-7078000', '050-9999166'}
            customer_phones = [num for num in matches if num not in service_numbers]
            
            if self.debug:
                logger.debug(f"Found phone numbers: {customer_phones}")
                
            return list(set(customer_phones))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting phone numbers: {e}")
            return []



    def _extract_service_charges(self) -> Dict[str, float]:
        """Extract service charges with improved pattern matching"""
        charges = {}
        try:
            # First try the fixed charges section
            section = self.sections["fixed_charges"].content
            if section:
                patterns = {
                    "repairs_top": r'[שירות תיקונים]{dir="rtl"}.*?Top.*?[למספר אלקטרוני]{dir="rtl"}.*?(\d+\.\d+)',
                    "repairs_regular": r'[שירות תיקונים פלאפון למספר אלקטרוני]{dir="rtl"}.*?(\d+\.\d+)',
                    "cyber": r'(?:CYBER|[סייבר]{dir="rtl"}).*?[לגלישה בטוחה ברשת]{dir="rtl"}.*?(\d+\.\d+)'

                }

                # Search in both fixed charges and full content
                for service, pattern in patterns.items():
                    for text in [section, self.content]:
                        matches = list(re.finditer(pattern, text, re.DOTALL))
                        for idx, match in enumerate(matches, 1):
                            try:
                                amount = float(match.group(1))
                                key = service if idx == 1 else f"{service}_{idx}"
                                charges[key] = amount
                                if self.debug:
                                    logger.info(f"Found {service} charge: {amount} ₪")
                            except ValueError:
                                continue

            if self.debug:
                if charges:
                    logger.info(f"Found service charges: {charges}")
                else:
                    logger.warning("No service charges found")
                    logger.debug(f"Fixed charges section content: {section[:200] if section else 'No section found'}")

            return charges

        except Exception as e:
            logger.error(f"Error extracting service charges: {str(e)}")
            return charges

    def _extract_usage_details(self) -> Dict[str, Dict]:
        """Extract usage details for all subscribers with enhanced charge extraction"""
        usage = {}
        try:
            phones = self.extract_phone_numbers()
            if not phones:
                logger.warning("No phone numbers found")
                return {}
                
            for phone in phones:
                if self.debug:
                    logger.debug(f"Processing usage for {phone}")
                    
                # Get subscriber charges
                charges = self._extract_subscriber_charges(phone)
                if not charges:
                    logger.warning(f"No charges found for {phone}")
                    continue
                    
                # Get call details
                calls, minutes = self._extract_call_details(phone)
                
                usage[phone] = {
                    "charges": charges,
                    "calls": calls,
                    "calls_minutes": minutes,
                    "sms": self._extract_sms_count(phone),
                    "data_mb": self._extract_data_usage(phone),
                    "package": self._extract_package_details(phone)
                }
                
                if self.debug:
                    logger.info(f"Complete usage details for {phone}: {usage[phone]}")
                    
            return usage
            
        except Exception as e:
            logger.error(f"Error extracting usage details: {e}")
            return {}


    def _extract_call_details(self, phone: str) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Extract call details for a subscriber"""
        try:
            # Pattern to match call details line
            # Example: "0503060366 שיחות 247:54 710:37 73:11 1031:42"
            call_pattern = (
                rf"{phone}\s+[שיחות]{{dir=\"rtl\"}}\s+"
                r"(\d+:\d+)\s+"  # Internal
                r"(\d+:\d+)\s+"  # External
                r"(\d+:\d+)\s+"  # Landline
                r"(\d+:\d+)"     # Total
            )
            
            if match := re.search(call_pattern, self.sections["usage"].content):
                calls = {
                    "internal": match.group(1),
                    "external": match.group(2),
                    "landline": match.group(3),
                    "total": match.group(4)
                }
                
                calls_minutes = {
                    key: self._convert_time_to_minutes(time)
                    for key, time in calls.items()
                }
                
                return calls, calls_minutes
                
            return {}, {}
            
        except Exception as e:
            logger.error(f"Error extracting call details for {phone}: {e}")
            return {}, {}

    def _extract_package_details(self, phone: str) -> Dict:
        """Extract package details for a phone"""
        try:
            section = self.sections["packages"].content
            if not section:
                return {}

            patterns = [
                (r"דקות שיחה", "minutes"),
                (r"גלישה באינטרנט", "data"),
                (r"הודעות SMS", "sms")
            ]
            
            package_info = {}
            for pattern, key in patterns:
                full_pattern = (
                    rf"{phone}.*?{pattern}\s+"
                    r"(\d+(?::\d+)?(?:\.\d+)?)\s+"  # Limit
                    r"(\d+(?::\d+)?(?:\.\d+)?)\s+"  # Usage
                    r"(\d+)\s*%"                    # Percentage
                )
                
                if match := re.search(full_pattern, section):
                    package_info[key] = {
                        "limit": match.group(1),
                        "usage": match.group(2),
                        "percentage": match.group(3)
                    }
                    if self.debug:
                        logger.debug(f"Found {key} package for {phone}: {package_info[key]}")
            
            return package_info

        except Exception as e:
            logger.error(f"Error extracting package details: {str(e)}")
            return {}

    @safe_extract(0.0)
    def _extract_data_usage(self, phone: str) -> float:
        """Extract data usage in MB"""
        try:
            patterns = [
                rf"{phone}.*?גלישה באינטרנט בארץ\s*\(ב-MB\)\s*(\d+\.?\d*)",
                rf"{phone}.*?נפח גלישת אינטרנט כלול ב\s*-\s*MB\s*(\d+\.?\d*)"
            ]
            
            for pattern in patterns:
                if match := re.search(pattern, self.content, re.DOTALL):
                    usage = float(match.group(1))
                    if self.debug:
                        logger.debug(f"Found data usage for {phone}: {usage} MB")
                    return usage
            return 0.0
        except Exception as e:
            logger.error(f"Error extracting data usage: {str(e)}")
            return 0.0

    def _convert_time_to_minutes(self, time_str: str) -> float:
        """Convert time format to minutes"""
        try:
            parts = time_str.split(':')
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 60 + minutes + seconds/60
            elif len(parts) == 2:  # HH:MM
                hours, minutes = map(int, parts)
                return hours * 60 + minutes
            return 0
        except Exception as e:
            logger.error(f"Error converting time {time_str}: {str(e)}")
            return 0

class TelecomQueryProcessor:
    """Process queries for the telecom bill data"""
    
    def __init__(self):
        """Initialize the TelecomQueryProcessor"""
        self.debug = True

    def create_prompt(self, query: str, bill_data: Dict) -> str:
        """Create detailed prompt for Claude"""
        try:
            total_amount = bill_data.get('total_amount', 0)
            usage_data = bill_data.get('usage', {})
            
            # Use double curly braces {{ }} for literal braces in f-strings
            prompt = f"""[אתה נציג שירות לקוחות של פלאפון. להלן הנתונים המדויקים מהחשבונית]{{dir="rtl"}}:

    [מידע כללי]{{dir="rtl"}}:
    =========
    • [סכום כולל לתשלום]{{dir="rtl"}}: {total_amount:.2f} [₪]{{dir="rtl"}}
    • [תקופת החיוב]{{dir="rtl"}}: {bill_data.get('billing_period', '')}

    [פירוט חיובים לפי מנוי]{{dir="rtl"}}:
    =================="""

            # Add specific subscriber details
            for phone, data in usage_data.items():
                subscriber_charges = data.get('charges', {})
                monthly_fee = subscriber_charges.get('monthly_fee', 0)
                
                prompt += f"""

        מנוי {phone}:
        • [תשלום חודשי קבוע]{{dir="rtl"}}: {monthly_fee:.2f} [₪]{{dir="rtl"}}"""

            # Add instructions for response
            prompt += """

    [הנחיות למענה]{{dir="rtl"}}:
    ===========
    1. [השתמש אך ורק בנתונים המדויקים שצוינו למעלה]{{dir="rtl"}}
    2. [בתשובות על סכומים, ציין תמיד את הסימן ₪]{{dir="rtl"}}
    3. [בתשובות על מנוי ספציפי, השתמש בחיובים המתאימים למנוי זה]{{dir="rtl"}}
    4. [אם המידע המבוקש לא מופיע בפירוט למעלה, ציין זאת בבירור]{{dir="rtl"}}

    [שאלת הלקוח]{{dir="rtl"}}: {query}"""

            if self.debug:
                logger.info(f"Created prompt with usage data: {usage_data}")
            
            return prompt

        except Exception as e:
            logger.error(f"Error creating prompt: {e}")
            return self._get_default_prompt()
            
            
    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return """[אתה נציג שירות לקוחות של חברת פלאפון]{{dir="rtl"}}.
[עליך לענות בעברית בצורה ברורה ומקצועית]{{dir="rtl"}}.
[כאשר אתה מזכיר סכומים, השתמש תמיד בסימן ₪]{{dir="rtl"}}.
[אם אין לך את המידע המבוקש, ציין זאת בבירור]{{dir="rtl"}}."""



# Create instances
bill_processor = TelecomBillProcessor()
query_processor = TelecomQueryProcessor()

# Export both instances
__all__ = ['bill_processor', 'query_processor']