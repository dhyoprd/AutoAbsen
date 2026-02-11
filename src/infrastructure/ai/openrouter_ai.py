import json
import requests
from typing import Dict, Any, Optional

from src.core.interfaces import IContentGenerator
from src.core.entities import Report
from .prompt_template import PromptTemplate

class OpenRouterAI(IContentGenerator):
    """
    Implementation of IContentGenerator using OpenRouter API.
    Follows OCP: Can be extended or swapped with OpenAI/Claude without changing core logic.
    """
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/dhyoprd/AutoAbsen",
        }

    def generate_content(self, context: str, user_input: str) -> Report:
        prompt = PromptTemplate.generate_report_prompt(context, user_input)
        
        try:
            response_json = self._call_api(prompt)
            data = self._parse_json_response(response_json)
            
            # Helper to extend short content
            data['activity'] = self._ensure_length(data.get('activity', ''), 'activity')
            data['learning'] = self._ensure_length(data.get('learning', ''), 'learning')
            data['obstacles'] = self._ensure_length(data.get('obstacles', ''), 'obstacles')
            
            return Report(
                activity=data['activity'],
                learning=data['learning'],
                obstacles=data['obstacles']
            )
            
        except Exception as e:
            # Fallback mechanism could be implemented here or let it bubble up
            # For now, we raise a specific error or return a dummy report (depending on requirements)
            print(f"AI Generation failed: {e}")
            raise

    def _call_api(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        clean_text = text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text.replace("```json", "").replace("```", "")
        elif clean_text.startswith("```"):
             clean_text = clean_text.replace("```", "")
             
        return json.loads(clean_text)

    def _ensure_length(self, text: str, field_type: str) -> str:
        if len(text) >= 100:
            return text
            
        # Extension logic
        try:
            prompt = PromptTemplate.extend_content_prompt(text, field_type)
            return self._call_api(prompt).strip()
        except:
            return text  # Return original if extension fails
