import json
import re
from typing import Dict
import openai
from app.config import settings

class CodeAnalyzer:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        
    async def analyze_code(self, file_data: dict) -> Dict:
        """Analyze a single file's changes"""
        filename = file_data['filename']
        patch = file_data.get('patch', '')
        
        # Skip if no changes
        if not patch:
            return {"issues": []}
        
        # Parse the diff to understand what changed
        added_lines = self._parse_diff(patch)
        
        # Create a focused prompt
        prompt = self._create_prompt(filename, patch, added_lines)
        
        try:
            response = await self._call_ai(prompt)
            return self._parse_ai_response(response, added_lines)
        except Exception as e:
            print(f"AI analysis error: {e}")
            return {"issues": []}
    
    def _parse_diff(self, patch: str) -> Dict[int, str]:
        """Extract added lines with their line numbers"""
        added_lines = {}
        current_line = 0
        
        for line in patch.split('\n'):
            if line.startswith('@@'):
                # Parse line number from diff header
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line = int(match.group(1)) - 1
            elif line.startswith('+') and not line.startswith('+++'):
                current_line += 1
                added_lines[current_line] = line[1:]  # Remove the +
            elif not line.startswith('-'):
                current_line += 1
                
        return added_lines
    
    def _create_prompt(self, filename: str, patch: str, added_lines: Dict[int, str]) -> str:
        """Create an effective prompt for the AI"""
        file_extension = filename.split('.')[-1]
        
        return f"""You are an expert {file_extension} code reviewer. Analyze this code change:

File: {filename}
Changes:
{patch}

Please review this code and identify any potential issues such as:
- Security vulnerabilities
- Performance problems
- Code quality issues
- Logic errors
- Best practice violations

For each issue found, provide:
1. Line number (if applicable)
2. Issue description
3. Severity level (high/medium/low)
4. Suggested fix

Respond in JSON format:
{{
    "issues": [
        {{
            "line": <line_number>,
            "message": "<description and suggested fix>",
            "severity": "<high|medium|low>"
        }}
    ]
}}
"""

    async def _call_ai(self, prompt: str) -> str:
        """Make API call to OpenAI"""
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return '{"issues": []}'
    
    def _parse_ai_response(self, response: str, added_lines: Dict[int, str]) -> Dict:
        """Parse AI response and validate line numbers"""
        try:
            # Try to parse JSON response
            result = json.loads(response)
            
            # Validate and filter issues
            valid_issues = []
            for issue in result.get('issues', []):
                line_num = issue.get('line')
                if line_num and line_num in added_lines:
                    valid_issues.append(issue)
                elif not line_num:
                    # General issue not tied to specific line
                    valid_issues.append(issue)
            
            return {"issues": valid_issues}
        except json.JSONDecodeError:
            # If AI didn't return valid JSON, try to extract useful info
            print(f"Failed to parse AI response: {response}")
            return {"issues": []}

# Create a global analyzer instance
_analyzer = None

async def analyze_code(filename: str, patch: str, full_content: str = None) -> Dict:
    """Standalone function to analyze code changes"""
    global _analyzer
    if _analyzer is None:
        _analyzer = CodeAnalyzer()
    
    file_data = {
        'filename': filename,
        'patch': patch,
        'full_content': full_content
    }
    
    return await _analyzer.analyze_code(file_data)