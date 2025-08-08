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
        
        return f"""You are an expert {file_extension} code reviewer. Analyze this code change and produce actionable suggestions that GitHub can apply directly.

File: {filename}
Changes:
{patch}

Identify issues such as security vulnerabilities, performance problems, code quality issues, logic errors, and best practice violations.

For each issue, respond with a JSON object containing:
1. "line": the target line number on the RIGHT (new) side of the diff (required if no range)
2. "severity": one of high | medium | low
3. "message": a concise human-readable explanation (single sentence)
4. "suggestion": the exact replacement code for the target line(s). This must be RAW code only (no backticks, no commentary)
5. Optional: "start_line": the first line number (inclusive) if suggesting changes spanning multiple lines on the RIGHT side
6. Optional: "end_line": the last line number (inclusive) for a multi-line suggestion

Rules:
- Only reference lines that exist on the RIGHT (new) side of the diff; do not reference removed lines.
- Prefer single-line suggestions; use start_line/end_line only when necessary.
- The suggestion content must contain ONLY the final code for the targeted lines.

Respond in JSON format:
{
    "issues": [
        {
            "line": <line_number>,
            "message": "<short explanation>",
            "severity": "<high|medium|low>",
            "suggestion": "<replacement code>",
            "start_line": <optional_start_line>,
            "end_line": <optional_end_line>
        }
    ]
}
"""

    async def _call_ai(self, prompt: str) -> str:
        """Make API call to OpenAI"""
        try:
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model="o4-mini-2025-04-16",
                messages=[
                    {"role": "system", "content": "You are an expert code reviewer."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return '{"issues": []}'
    
    def _parse_ai_response(self, response: str, added_lines: Dict[int, str]) -> Dict:
        """Parse AI response and validate line numbers"""
        try:
            result = json.loads(response)

            valid_issues = []
            for issue in result.get('issues', []):
                # Must have a suggestion and at least one target line
                suggestion = issue.get('suggestion')
                line_num = issue.get('line')
                start_line = issue.get('start_line')
                end_line = issue.get('end_line')

                if not suggestion or (not line_num and not (start_line and end_line)):
                    continue

                # Normalize types and ranges
                if isinstance(line_num, str) and line_num.isdigit():
                    line_num = int(line_num)
                    issue['line'] = line_num
                if isinstance(start_line, str) and start_line.isdigit():
                    start_line = int(start_line)
                    issue['start_line'] = start_line
                if isinstance(end_line, str) and end_line.isdigit():
                    end_line = int(end_line)
                    issue['end_line'] = end_line

                if start_line and not end_line:
                    end_line = start_line
                    issue['end_line'] = end_line
                if end_line and not start_line:
                    start_line = end_line
                    issue['start_line'] = start_line

                # Basic sanity checks
                if start_line and end_line and start_line > end_line:
                    start_line, end_line = end_line, start_line
                    issue['start_line'] = start_line
                    issue['end_line'] = end_line

                # Keep the issue; rely on GitHub to validate exact line availability in the diff
                valid_issues.append(issue)

            return {"issues": valid_issues}
        except json.JSONDecodeError:
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