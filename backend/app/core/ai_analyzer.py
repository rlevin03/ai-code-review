import json
import re
from typing import Dict, List, Optional
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
        """