# test_anthropic.py
from anthropic import Anthropic

# Replace with your API key
api_key = "your-api-key-here"
client = Anthropic(api_key=api_key)

try:
    response = client.beta.messages.create(
        model="claude-3-opus-20240229",
        messages=[{
            "role": "user",
            "content": "Hello, Claude!"
        }],
        max_tokens=1024
    )
    print("Success!")
    print("Response:", response.content[0].text)
except Exception as e:
    print("Error:", str(e))
