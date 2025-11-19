"""
Trial Class Call Analyzer

Real-time LLM analysis specifically for trial class sales calls.
Handles:
1. Checklist item completion detection
2. Client card field extraction
3. Uses Indonesian conversation context

Optimized for low latency and cost.
"""

import json
import os
from typing import Dict, List, Tuple, Optional
import requests
from dotenv import load_dotenv

from call_structure_config import get_default_call_structure
from client_card_config import get_default_client_card_fields, get_extraction_hint

load_dotenv()


class TrialClassAnalyzer:
    """LLM-based analyzer for trial class sales calls"""
    
    def __init__(self, model: str = None):
        """
        Initialize analyzer
        
        Args:
            model: OpenRouter model (e.g. "anthropic/claude-3-haiku", "meta-llama/llama-3.3-70b-instruct:free")
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Use env var or provided model, default to Haiku for speed + cost
        self.model = model or os.getenv("LLM_MODEL", "anthropic/claude-3-haiku")
        print(f"🤖 Trial Class Analyzer initialized with model: {self.model}")
        
        # Load configs
        self.call_structure = get_default_call_structure()
        self.client_card_fields = get_default_client_card_fields()
    
    def check_checklist_item(
        self,
        item_id: str,
        item_content: str,
        item_type: str,
        conversation_text: str
    ) -> Tuple[bool, float, str]:
        """
        Check if a checklist item has been completed
        
        Args:
            item_id: Item identifier
            item_content: What should be discussed/said
            item_type: "discuss" or "say"
            conversation_text: Recent conversation (Indonesian)
            
        Returns:
            (completed: bool, confidence: float, evidence: str)
        """
        # Guard: Skip if conversation too short
        if len(conversation_text.strip()) < 30:
            return False, 0.0, "Insufficient conversation context"
        
        # Build prompt based on item type
        if item_type == "discuss":
            action_description = "asked about or discussed"
        else:  # "say"
            action_description = "explained or mentioned"
        
        prompt = f"""You are analyzing a sales call transcript in Bahasa Indonesia.

Check if this sales action was completed:
Action: "{item_content}"
Type: {action_description}

Recent conversation:
{conversation_text}

Was this action completed in the conversation? Consider:
- The conversation is in Bahasa Indonesia
- Look for MEANING and INTENT, not exact words
- Be STRICT: require clear evidence
- Avoid false positives from partial mentions

Return ONLY valid JSON:
{{
  "completed": true/false,
  "confidence": 0.0-1.0,
  "evidence": "brief quote showing completion (or empty if not completed)"
}}
"""
        
        try:
            response = self._call_llm(prompt, temperature=0.2, max_tokens=150)
            result = json.loads(response)
            
            completed = result.get("completed", False)
            confidence = result.get("confidence", 0.0)
            evidence = result.get("evidence", "")
            
            # Guard: Only accept high confidence completions
            if completed and confidence < 0.8:
                return False, confidence, "Confidence too low"
            
            return completed, confidence, evidence
            
        except Exception as e:
            print(f"   ⚠️ Item check failed for {item_id}: {e}")
            return False, 0.0, str(e)
    
    def extract_client_card_fields(
        self,
        conversation_text: str,
        current_values: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Extract/update client card fields from conversation
        
        Args:
            conversation_text: Recent conversation in Indonesian
            current_values: Current field values (to avoid rewriting)
            
        Returns:
            Dict of field_id → extracted text (only fields with new info)
        """
        # Guard: Skip if conversation too short
        if len(conversation_text.strip()) < 50:
            return {}
        
        # Build field descriptions for LLM
        field_descriptions = []
        for field in self.client_card_fields:
            field_id = field['id']
            label = field['label']
            hint = get_extraction_hint(field_id)
            current = current_values.get(field_id, "")
            
            field_descriptions.append(f"- {field_id} ({label}): {hint}")
        
        fields_str = "\n".join(field_descriptions)
        
        prompt = f"""You are analyzing a sales call in Bahasa Indonesia to extract client information.

Conversation (Bahasa Indonesia):
{conversation_text}

Extract information for these fields (only if clearly mentioned):
{fields_str}

Rules:
- Only extract if CONFIDENT and EXPLICITLY mentioned
- Keep extractions brief (1-2 sentences max per field)
- If not mentioned, omit the field
- Conversation is in Indonesian, but respond in English

Return ONLY valid JSON:
{{
  "field_id": "extracted text",
  "another_field_id": "extracted text"
}}

If no clear information, return empty object: {{}}
"""
        
        try:
            response = self._call_llm(prompt, temperature=0.3, max_tokens=500)
            result = json.loads(response)
            
            # Filter out fields that already have values (don't overwrite unless significantly different)
            updates = {}
            for field_id, value in result.items():
                if field_id in current_values and current_values[field_id]:
                    # Skip if we already have this field filled
                    continue
                if value and len(value.strip()) > 5:
                    updates[field_id] = value.strip()
            
            return updates
            
        except Exception as e:
            print(f"   ⚠️ Client card extraction failed: {e}")
            return {}
    
    def batch_check_items(
        self,
        items: List[Dict],
        conversation_text: str
    ) -> Dict[str, Tuple[bool, float, str]]:
        """
        Batch check multiple items at once (more efficient)
        
        Args:
            items: List of {id, content, type} dicts
            conversation_text: Recent conversation
            
        Returns:
            Dict of item_id → (completed, confidence, evidence)
        """
        # For now, check items individually
        # TODO: Could optimize with a single LLM call for multiple items
        results = {}
        for item in items:
            completed, confidence, evidence = self.check_checklist_item(
                item['id'],
                item['content'],
                item['type'],
                conversation_text
            )
            results[item['id']] = (completed, confidence, evidence)
        
        return results
    
    def _call_llm(self, prompt: str, temperature: float = 0.5, max_tokens: int = 500) -> str:
        """
        Call OpenRouter API
        
        Args:
            prompt: The prompt
            temperature: Creativity level
            max_tokens: Max response length
            
        Returns:
            LLM response text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        content = data["choices"][0]["message"]["content"]
        
        # Try to extract JSON if wrapped in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        return content.strip()


# Global instance
_analyzer: Optional[TrialClassAnalyzer] = None


def get_trial_class_analyzer() -> TrialClassAnalyzer:
    """Get or create global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TrialClassAnalyzer()
    return _analyzer


def reset_analyzer():
    """Reset analyzer (for testing/new session)"""
    global _analyzer
    _analyzer = None

