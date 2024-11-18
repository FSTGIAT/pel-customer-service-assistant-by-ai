# In app/services/claude_service.py

from typing import Optional, List, Dict
import aiohttp
import json
import re
import os
from dotenv import load_dotenv
from pathlib import Path

class ClaudeService:
    def __init__(self):
        """Initialize Claude service"""
        self.debug = True
        self._load_environment()
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        if self.debug:
            print("Claude service initialized")

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
        pdf_content: Optional[str] = None,
        context: Optional[List[Dict]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Get response from Claude using direct text"""
        try:
            if self.debug:
                print(f"\nProcessing request: {message}")

            # Build a structured prompt with the bill content
            prompt = """אתה נציג שירות לקוחות של פלאפון המנתח חשבונית.

=== תוכן החשבונית ===
{content}
=====================

הנחיות:
1. התייחס אך ורק למידע שמופיע בחשבונית למעלה
2. כשמדובר בסכומים, השתמש תמיד בסימן ₪
3. אם המידע המבוקש לא נמצא בחשבונית, ציין זאת בבירור
4. בתשובתך התייחס לתקופת החיוב הרלוונטית

שאלת הלקוח: {question}"""

            # Build API request
            body = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt.format(
                            content=pdf_content,
                            question=message
                        )
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
                "system": """You are a Pelephone customer service representative analyzing billing data.
Always answer in Hebrew and be specific about what information you find or don't find in the bill content."""
            }

            if self.debug:
                print("Sending request to Claude API...")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=body
                ) as response:
                    response_text = await response.text()
                    if self.debug:
                        print(f"Raw response: {response_text}")
                        
                    if response.status == 200:
                        data = json.loads(response_text)
                        return self._process_claude_response(data)
                    else:
                        print(f"API Error: {response_text}")
                        return "מצטער, נתקלתי בבעיה בתקשורת עם השרת. אנא נסה שוב."

        except Exception as e:
            print(f"Error in get_response: {str(e)}")
            return "מצטער, אירעה שגיאה. אנא נסה שוב."

    def _process_claude_response(self, response_data: Dict) -> str:
        """Process Claude's response data with better handling"""
        try:
            if self.debug:
                print(f"Processing response data: {json.dumps(response_data, ensure_ascii=False)}")

            # Handle the new Claude API response structure
            if isinstance(response_data, dict):
                # Check for content array (Claude 3 format)
                if 'content' in response_data and isinstance(response_data['content'], list):
                    for item in response_data['content']:
                        if item.get('type') == 'text':
                            return item['text'].strip()
                
                # Fallbacks for other response formats
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

    def _get_default_prompt(self) -> str:
        """Get default system prompt"""
        return """אתה נציג שירות לקוחות של חברת פלאפון.
עליך לענות בעברית בצורה ברורה ומקצועית.
כאשר אתה מזכיר סכומים, השתמש תמיד בסימן ₪.
אם אין לך את המידע המבוקש, ציין זאת בבירור."""

    def _handle_error(self, error_msg: str) -> str:
        """Handle errors with user-friendly messages"""
        print(f"Handling error: {error_msg}")
        
        if "API key" in error_msg:
            return "מצטער, יש בעיה בגישה למערכת. אנא פנה לתמיכה."
        elif "timeout" in error_msg.lower():
            return "מצטער, התגובה לוקחת יותר מדי זמן. אנא נסה שוב."
        elif "bill data" in error_msg.lower():
            return "מצטער, לא הצלחתי לגשת לנתוני החשבונית. אנא נסה שוב."
        else:
            return "מצטער, נתקלתי בבעיה בעיבוד הבקשה. אנא נסה שוב או נסח את השאלה מחדש."

# Create and export the service instance
claude_service = ClaudeService()

# Export the instance
__all__ = ['claude_service']