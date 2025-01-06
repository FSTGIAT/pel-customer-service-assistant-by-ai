from typing import Optional, List, Dict
import aiohttp
import json
import re
import os
import asyncio
import logging
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from app.services.rate_limiting.service import RateLimitService, rate_limit_service

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self, rate_limit_service: RateLimitService):
        """Initialize Claude service with rate limiting"""
        self.debug = True
        self._load_environment()
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        self.rate_limiter = rate_limit_service
        
        if self.debug:
            print("Claude service initialized with rate limiting")

    def _load_environment(self):
        """Load and validate environment variables"""
        try:
            project_root = Path(__file__).parent.parent.parent
            env_path = project_root / '.env'
            
            if env_path.exists():
                load_dotenv(str(env_path))
                if self.debug:
                    print(f"Loaded environment from {env_path}")
            else:
                print(f"Warning: No .env file found at {env_path}")
                
            self.api_key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('\"\'')
            
            if not self.api_key:
                raise Exception(
                    "ANTHROPIC_API_KEY not found or empty. "
                    f"Checked location: {env_path}"
                )
            
            if self.debug:
                print("API key loaded successfully")
                
        except Exception as e:
            raise Exception(f"Environment loading failed: {str(e)}")

    async def get_response(
        self,
        message: str,
        customer_id: str,
        pdf_content: Optional[str] = None,
        context: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Get response from Claude using rate-limited access"""
        try:
            print("\n=== Starting Claude Request ===")
            print(f"Customer ID: {customer_id}")
            print(f"Message: {message}")
            
            # Check if this is a JSON request for customer info
            is_json_request = any(term in message.lower() for term in ['json', 'format', 'name', 'plan'])
            print(f"Is JSON request: {is_json_request}")

            # Build prompt based on request type
            if is_json_request:
                prompt = """Extract and return a JSON object with this exact format:
    {{
        "name": "[שם הלקוח המלא]{{dir=\"rtl\"}}",
        "plan": "[שם תכנית/מסלול]{{dir=\"rtl\"}}"
    }}

    [החשבונית]{{dir=\"rtl\"}}:
    {content}"""
            else:
                prompt = """[אתה נציג שירות לקוחות של פלאפון המנתח חשבונית]{{dir=\"rtl\"}}.

    === [תוכן החשבונית]{{dir=\"rtl\"}} ===
    {content}
    =====================

    [הנחיות]{{dir=\"rtl\"}}:
    1. [התייחס אך ורק למידע שמופיע בחשבונית למעלה]{{dir=\"rtl\"}}
    2. [כשמדובר בסכומים, השתמש תמיד בסימן ₪]{{dir=\"rtl\"}}
    3. [אם המידע המבוקש לא נמצא בחשבונית, ציין זאת בבירור]{{dir=\"rtl\"}}
    4. [בתשובתך התייחס לתקופת החיוב הרלוונטית]{{dir=\"rtl\"}}

    [שאלת הלקוח]{{dir=\"rtl\"}}: {question}"""

            # Format prompt
            formatted_prompt = prompt.format(
                content=pdf_content,
                question=message
            )
            print(f"Formatted prompt length: {len(formatted_prompt)}")

            # Make API call
            async with aiohttp.ClientSession() as session:
                try:
                    print("Making API call to Claude...")
                    
                    body = {
                        "model": self.model,
                        "messages": [{
                            "role": "user",
                            "content": formatted_prompt
                        }],
                        "max_tokens": 4000,
                        "temperature": 0.7,
                        "system": system_prompt or self._get_default_system_prompt()
                    }
                    
                    async with session.post(
                        self.api_url,
                        headers=self.headers,
                        json=body,
                        timeout=30
                    ) as response:
                        print(f"Response status: {response.status}")
                        response_text = await response.text()
                        print(f"Raw response start: {response_text[:200]}...")
                        
                        if response.status == 200:
                            try:
                                data = json.loads(response_text)
                                result = self._process_claude_response(data)
                                
                                # Handle JSON response
                                if is_json_request:
                                    try:
                                        if isinstance(result, str):
                                            # Extract JSON from string if needed
                                            json_match = re.search(r'\{.*\}', result, re.DOTALL)
                                            if json_match:
                                                result = json_match.group(0)
                                        # Validate JSON
                                        json.loads(result)
                                    except:
                                        result = '{"name": "לקוח", "plan": "תכנית סטנדרטית"}'
                                
                                print(f"Final response: {result[:100]}...")
                                return result
                            except json.JSONDecodeError:
                                return "מצטער, קיבלתי תשובה לא תקינה מהשרת. אנא נסה שוב."
                        else:
                            print(f"API Error: {response.status} - {response_text}")
                            if is_json_request:
                                return '{"name": "לקוח", "plan": "תכנית סטנדרטית"}'
                            return "מצטער, נתקלתי בבעיה בתקשורת עם השרת. אנא נסה שוב."
                            
                except asyncio.TimeoutError:
                    print("API request timed out")
                    if is_json_request:
                        return '{"name": "לקוח", "plan": "תכנית סטנדרטית"}'
                    return "מצטער, התשובה לוקחת יותר מדי זמן. אנא נסה שוב."
                except Exception as e:
                    print(f"API request error: {str(e)}")
                    if is_json_request:
                        return '{"name": "לקוח", "plan": "תכנית סטנדרטית"}'
                    return "מצטער, נתקלתי בבעיה בתקשורת עם השרת. אנא נסה שוב."

        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            if is_json_request:
                return '{"name": "לקוח", "plan": "תכנית סטנדרטית"}'
            return "מצטער, נתקלתי בבעיה בעיבוד הבקשה. אנא נסה שוב."


    def _process_pdf_content(self, content: str) -> str:
        """Process and trim PDF content to reduce tokens"""
        try:
            # Split content into sections
            sections = content.split("===")
            
            # Process each section
            processed_sections = []
            for section in sections:
                if not section.strip():
                    continue
                    
                # Keep only relevant information
                relevant_lines = [
                    line.strip() for line in section.split('\n')
                    if any(key in line.lower() for key in [
                        'סכום', 'תקופת', 'חיוב', '₪', 'תשלום', 'מנוי',
                        'שירות', 'תעריף', 'הנחה', 'זיכוי'
                    ])
                ]
                
                if relevant_lines:
                    processed_sections.append("\n".join(relevant_lines))
            
            # Join processed sections with clear separation
            processed_content = "\n===\n".join(processed_sections)
            
            # Ensure we're not exceeding token limits
            if len(processed_content) > 6000:  # Approximate token limit
                processed_content = processed_content[:6000] + "..."
                
            return processed_content
            
        except Exception as e:
            logger.error(f"Error processing PDF content: {e}")
            return "Error processing bill content"

    def _get_default_system_prompt(self) -> str:
        return """You are a Pelephone customer service representative analyzing billing data.
Always answer in Hebrew and be specific about what information you find or don't find in the bill content."""

    def _process_claude_response(self, response_data: Dict) -> str:
        """Process Claude's response data with better handling"""
        try:
            if self.debug:
                print(f"Processing response data: {json.dumps(response_data, ensure_ascii=False)}")

            if isinstance(response_data, dict):
                if 'content' in response_data and isinstance(response_data['content'], list):
                    for item in response_data['content']:
                        if item.get('type') == 'text':
                            return item['text'].strip()
                
                for key in ['text', 'response', 'content']:
                    if key in response_data:
                        content = response_data[key]
                        if isinstance(content, str):
                            return content.strip()
                        elif isinstance(content, list) and len(content) > 0:
                            return str(content[0]).strip()

            return "מצטער, לא הצלחתי לנתח את החשבונית כראוי. אנא נסה שוב."

        except Exception as e:
            print(f"Error processing Claude response: {str(e)}")
            return "מצטער, נתקלתי בבעיה בעיבוד התשובה. אנא נסה שוב."

    def _handle_error(self, error_msg: str) -> str:
        """Handle errors with user-friendly messages"""
        print(f"Handling error: {error_msg}")
        
        if "API key" in error_msg:
            return "מצטער, יש בעיה בגישה למערכת. אנא פנה לתמיכה."
        elif "timeout" in error_msg.lower():
            return "מצטער, התגובה לוקחת יותר מדי זמן. אנא נסה שוב."
        elif "rate limit" in error_msg.lower():
            return "מצטער, יש עומס על המערכת כרגע. אנא נסה שוב בעוד מספר דקות."
        elif "bill data" in error_msg.lower():
            return "מצטער, לא הצלחתי לגשת לנתוני החשבונית. אנא נסה שוב."
        else:
            return "מצטער, נתקלתי בבעיה בעיבוד הבקשה. אנא נסה שוב או נסח את השאלה מחדש."

# Modified service initialization
def create_claude_service(rate_limit_service: RateLimitService) -> ClaudeService:
    return ClaudeService(rate_limit_service)

claude_service = create_claude_service(rate_limit_service)
__all__ = ['claude_service']
