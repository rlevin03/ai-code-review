from openai import OpenAI
from typing import Dict
from app.config import settings

# Initialize client with API key from settings
client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def analyze_code(filename: str, patch: str, full_content: str = None) -> Dict:
    """Analyze code using AI"""
    
    # Create a prompt for the AI
    prompt = f"""
    Review the following code changes in {filename}:
    
    ```diff
    {patch}
    ```
    
    Please identify:
    1. Potential bugs or errors
    2. Security vulnerabilities
    3. Performance issues
    4. Code style improvements
    
    Format your response as JSON with this structure:
    {{
        "issues": [
            {{
                "line": <line_number>,
                "severity": "error|warning|info",
                "message": "Description of the issue",
                "suggestion": "How to fix it"
            }}
        ]
    }}
    """
    
    try:
        response = await client.ChatCompletion.acreate(
            model="o4-mini",
            reasoning={"effort": "medium"},
            input=[
                {"role": "system", "content": "You are an expert code reviewer."},
                {"role": "user", "content": prompt}
            ],
        )
        
        # Parse the response
        import json
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error analyzing code: {e}")
        return {"issues": []}