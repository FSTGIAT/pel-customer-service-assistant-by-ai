# test_key.py
import os
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT


# Replace this with your actual API key from Anthropic console
API_KEY = "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"

def test_connection():
    client = Anthropic(api_key=API_KEY)
    
    try:
        # Using the completion API instead of messages
        response = client.completions.create(
            model="claude-2.1",  # Using a stable model version
            max_tokens_to_sample=1000,
            prompt=f"{HUMAN_PROMPT} Hello, Claude! {AI_PROMPT}",
        )
        print("Connection successful!")
        print("Claude's response:", response.completion)
        return True
    except Exception as e:
        print(f"Connection failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
