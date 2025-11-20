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
    ) -> Tuple[bool, float, str, Dict]:
        """
        Check if a checklist item has been completed
        
        Args:
            item_id: Item identifier
            item_content: What should be discussed/said
            item_type: "discuss" or "say"
            conversation_text: Recent conversation (Indonesian)
            
        Returns:
            (completed: bool, confidence: float, evidence: str, debug_info: dict)
        """
        # Guard: Skip if conversation too short
        if len(conversation_text.strip()) < 30:
            debug_info = {
                "stage": "guard_context_too_short",
                "context_length": len(conversation_text.strip())
            }
            return False, 0.0, "Insufficient conversation context", debug_info
        
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

CRITICAL RULES:
1. The conversation is in Bahasa Indonesia
2. Look for MEANING and INTENT, not exact words
3. Be EXTREMELY STRICT: require clear, direct evidence
4. The evidence quote MUST directly show the action was completed
5. Avoid false positives from unrelated mentions

EVIDENCE MUST BE RELEVANT:
✅ GOOD: Evidence directly shows the action
   Action: "Ask about child's age"
   Evidence: "Usia anaknya berapa tahun?" 
   
✅ GOOD: Evidence proves the discussion happened
   Action: "Identify parent concerns"
   Evidence: "Papa khawatir anak kurang fokus belajar"

❌ BAD: Evidence is just nearby but unrelated
   Action: "Identify parent concerns"  
   Evidence: "Oke, selamat datang" ← This is just greeting!

❌ BAD: Evidence doesn't prove the action
   Action: "Explain curriculum"
   Evidence: "Oke baik" ← Just acknowledgment, not explanation!

If you're not 100% sure the evidence PROVES the action was done, mark completed=false.

Return ONLY valid JSON:
{{
  "completed": true/false,
  "confidence": 0.0-1.0,
  "evidence": "direct quote proving completion (or empty if not completed)",
  "reasoning": "one sentence explaining why evidence proves this action"
}}
"""
        
        try:
            response = self._call_llm(prompt, temperature=0.2, max_tokens=200)
            result = json.loads(response)
            
            completed = result.get("completed", False)
            confidence = result.get("confidence", 0.0)
            evidence = result.get("evidence", "")
            reasoning = result.get("reasoning", "")
            
            debug_info = {
                "stage": "initial_check",
                "context_preview": conversation_text[-200:],  # Last 200 chars
                "first_completed": completed,
                "first_confidence": confidence,
                "first_evidence": evidence,
                "first_reasoning": reasoning,
                "guards_passed": []
            }
            
            # Guard 1: Only accept high confidence completions
            if completed and confidence < 0.8:
                debug_info["stage"] = "guard_1_low_confidence"
                debug_info["guards_passed"].append("confidence < 0.8")
                return False, confidence, "Confidence too low", debug_info
            
            # Guard 2: Evidence must exist and be substantial
            if completed and len(evidence.strip()) < 10:
                debug_info["stage"] = "guard_2_evidence_too_short"
                debug_info["guards_passed"].append("evidence length < 10")
                return False, confidence, "Evidence too short", debug_info
            
            # Guard 3: Validate evidence relevance with second LLM call
            validation_result = None
            if completed and confidence >= 0.8:
                validation_passed = self._validate_evidence_relevance(
                    item_content=item_content,
                    evidence=evidence,
                    reasoning=reasoning
                )
                validation_result = validation_passed
                debug_info["validation_passed"] = validation_passed
                
                if not validation_passed:
                    print(f"   ⚠️ Evidence validation FAILED for '{item_content[:50]}...'")
                    debug_info["stage"] = "guard_3_validation_failed"
                    debug_info["guards_passed"].append("validation failed")
                    return False, confidence, f"Evidence not relevant: {evidence[:100]}", debug_info
            
            debug_info["stage"] = "accepted"
            debug_info["final_decision"] = "completed" if completed else "not_completed"
            return completed, confidence, evidence, debug_info
            
        except Exception as e:
            print(f"   ⚠️ Item check failed for {item_id}: {e}")
            debug_info = {
                "stage": "error",
                "error": str(e)
            }
            return False, 0.0, str(e), debug_info
    
    def _validate_evidence_relevance(
        self,
        item_content: str,
        evidence: str,
        reasoning: str
    ) -> bool:
        """
        Validate that evidence actually proves the action was completed
        This is a second-pass check to catch false positives
        
        Args:
            item_content: The action that should be completed
            evidence: The quote provided as proof
            reasoning: The reasoning from first check
            
        Returns:
            True if evidence is relevant, False if not
        """
        if not evidence or len(evidence.strip()) < 5:
            return False
        
        validation_prompt = f"""You are validating evidence quality for a sales call checklist.

REQUIRED ACTION:
"{item_content}"

PROVIDED EVIDENCE:
"{evidence}"

REASONING (from first check):
"{reasoning}"

CRITICAL QUESTION: Does the evidence DIRECTLY prove that the required action was completed?

Examples of INVALID evidence:
❌ Evidence is just a greeting when action is "identify concerns"
❌ Evidence is asking about time when action is "ask about child's age"  
❌ Evidence is unrelated chit-chat
❌ Evidence is from a different topic

Examples of VALID evidence:
✅ Evidence shows the exact question was asked
✅ Evidence shows the information was discussed
✅ Evidence directly relates to the required action

Return ONLY valid JSON:
{{
  "is_valid": true/false,
  "explanation": "why evidence does or doesn't prove the action"
}}
"""
        
        try:
            response = self._call_llm(validation_prompt, temperature=0.1, max_tokens=100)
            result = json.loads(response)
            is_valid = result.get("is_valid", False)
            explanation = result.get("explanation", "")
            
            if not is_valid:
                print(f"      🔍 Validation: {explanation}")
            
            return is_valid
            
        except Exception as e:
            print(f"   ⚠️ Evidence validation error: {e}")
            # On error, be conservative - accept the original decision
            return True
    
    def extract_client_card_fields(
        self,
        conversation_text: str,
        current_values: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """
        Extract/update client card fields from conversation
        
        Args:
            conversation_text: Recent conversation in Indonesian
            current_values: Current field values (to avoid rewriting)
            
        Returns:
            Dict of field_id → {value: str, evidence: str} (only fields with new info)
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

CRITICAL RULES:
1. Only extract if CONFIDENT and EXPLICITLY mentioned
2. Keep extractions brief (1-2 sentences max per field)
3. If not mentioned, omit the field
4. Conversation is in Indonesian, but respond in English
5. Evidence MUST be a direct quote that PROVES the information
6. DO NOT extract from greetings, acknowledgments, or unrelated text

EVIDENCE MUST BE RELEVANT:
✅ GOOD:
   Field: child_name
   Value: "Andi"
   Evidence: "Nama anaknya Andi"

✅ GOOD:
   Field: child_interests
   Value: "Playing Roblox and Minecraft"
   Evidence: "Andi suka main Roblox dan Minecraft"

❌ BAD:
   Field: child_name
   Value: "Seki"
   Evidence: "Oke, selamat datang, Seki" ← Just greeting!

❌ BAD:
   Field: parent_goal
   Value: "Learning"
   Evidence: "Kita akan belajar hari ini" ← Not parent's goal!

Return ONLY valid JSON with confidence:
{{
  "field_id": {{
    "value": "extracted text",
    "evidence": "direct quote proving this information",
    "confidence": 0.0-1.0
  }}
}}

If no clear information, return empty object: {{}}
"""
        
        try:
            response = self._call_llm(prompt, temperature=0.3, max_tokens=800)
            result = json.loads(response)
            
            # Filter out fields that already have values (don't overwrite unless significantly different)
            updates = {}
            for field_id, field_data in result.items():
                if field_id in current_values and current_values[field_id]:
                    # Skip if we already have this field filled
                    continue
                
                # Handle both old format (string) and new format (dict with value/evidence)
                if isinstance(field_data, dict):
                    value = field_data.get('value', '')
                    evidence = field_data.get('evidence', '')
                    confidence = field_data.get('confidence', 1.0)
                else:
                    value = str(field_data)
                    evidence = ''
                    confidence = 1.0
                
                # Guard 1: Value must be substantial
                if not value or len(value.strip()) <= 5:
                    continue
                
                # Guard 2: Confidence must be high
                if confidence < 0.7:
                    print(f"   ⚠️ Low confidence ({confidence:.0%}) for {field_id}, skipping")
                    continue
                
                # Guard 3: Evidence must exist
                if not evidence or len(evidence.strip()) < 10:
                    print(f"   ⚠️ Evidence too short for {field_id}, skipping")
                    continue
                
                # Guard 4: Validate evidence relevance
                # Get field label for validation
                field_label = next((f['label'] for f in self.client_card_fields if f['id'] == field_id), field_id)
                
                validation_passed = self._validate_client_field_evidence(
                    field_label=field_label,
                    value=value,
                    evidence=evidence
                )
                
                if not validation_passed:
                    print(f"   ⚠️ Evidence validation FAILED for {field_id}")
                    continue
                
                updates[field_id] = {
                    'value': value.strip(),
                    'evidence': evidence.strip()
                }
            
            return updates
            
        except Exception as e:
            print(f"   ⚠️ Client card extraction failed: {e}")
            return {}
    
    def _validate_client_field_evidence(
        self,
        field_label: str,
        value: str,
        evidence: str
    ) -> bool:
        """
        Validate that evidence actually proves the extracted client information
        This prevents false extractions from greetings or unrelated text
        
        Args:
            field_label: Human-readable field name (e.g. "Child's Name")
            value: The extracted value
            evidence: The quote provided as proof
            
        Returns:
            True if evidence is relevant, False if not
        """
        if not evidence or len(evidence.strip()) < 5:
            return False
        
        validation_prompt = f"""You are validating evidence quality for client information extraction.

FIELD: {field_label}
EXTRACTED VALUE: "{value}"
PROVIDED EVIDENCE: "{evidence}"

CRITICAL QUESTION: Does the evidence DIRECTLY prove this information about the client?

Examples of INVALID evidence:
❌ Evidence is just a greeting when field is "child's name"
❌ Evidence is about the lesson plan when field is "parent's goal"
❌ Evidence is unrelated chit-chat
❌ Evidence mentions the word but in different context

Examples of VALID evidence:
✅ Evidence shows the child's actual name being mentioned
✅ Evidence shows parent stating their goal
✅ Evidence shows the specific information being discussed

Return ONLY valid JSON:
{{
  "is_valid": true/false,
  "explanation": "why evidence does or doesn't prove the information"
}}
"""
        
        try:
            response = self._call_llm(validation_prompt, temperature=0.1, max_tokens=100)
            result = json.loads(response)
            is_valid = result.get("is_valid", False)
            explanation = result.get("explanation", "")
            
            if not is_valid:
                print(f"      🔍 Client field validation: {explanation}")
            
            return is_valid
            
        except Exception as e:
            print(f"   ⚠️ Client field validation error: {e}")
            # On error, be conservative - accept the original decision
            return True
    
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
    
    def detect_current_stage(
        self,
        conversation_text: str,
        stages: List[Dict],
        call_elapsed_seconds: int
    ) -> Tuple[str, float]:
        """
        Detect which stage the conversation is currently in based on context
        
        Args:
            conversation_text: Recent conversation (last ~2000 chars)
            stages: List of stage definitions with names and items
            call_elapsed_seconds: Time elapsed (used as context, not decision)
            
        Returns:
            (stage_id: str, confidence: float)
        """
        # Guard: Skip if conversation too short
        if len(conversation_text.strip()) < 100:
            # At start, assume first stage
            return stages[0]['id'] if stages else '', 0.5
        
        # Build stage descriptions for LLM
        stage_descriptions = []
        for i, stage in enumerate(stages):
            items_summary = []
            for item in stage['items'][:3]:  # First 3 items as examples
                items_summary.append(f"- {item['content']}")
            items_text = "\n".join(items_summary)
            if len(stage['items']) > 3:
                items_text += f"\n- ...and {len(stage['items']) - 3} more"
            
            recommended_time = f"{stage['startOffsetSeconds']//60}-{(stage['startOffsetSeconds'] + stage['durationSeconds'])//60} min"
            
            stage_descriptions.append(
                f"{i+1}. **{stage['name']}** (recommended: {recommended_time})\n"
                f"   Focus: {items_text}"
            )
        
        stages_text = "\n\n".join(stage_descriptions)
        
        prompt = f"""You are analyzing a sales call in Bahasa Indonesia to determine the current stage.

Call elapsed time: {call_elapsed_seconds // 60} minutes {call_elapsed_seconds % 60} seconds (reference only)

Recent conversation:
{conversation_text}

Available stages:
{stages_text}

Based on the CONTENT and TOPICS being discussed (NOT just the time), which stage is the conversation currently in?

Rules:
- Focus on WHAT is being discussed, not how long has passed
- Look for keywords and topics matching the stage focus
- If transitioning between stages, pick the one that matches CURRENT topic
- Conversation is in Indonesian
- Be confident - avoid jumping between stages too quickly

Return ONLY valid JSON:
{{
  "stage_id": "stage_id_here",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of why this stage"
}}
"""
        
        try:
            response = self._call_llm(prompt, temperature=0.2, max_tokens=200)
            result = json.loads(response)
            
            stage_id = result.get("stage_id", "")
            confidence = result.get("confidence", 0.0)
            
            # Validate stage_id exists
            valid_ids = [s['id'] for s in stages]
            if stage_id not in valid_ids:
                print(f"   ⚠️ Invalid stage_id '{stage_id}', using first stage")
                return stages[0]['id'] if stages else '', 0.5
            
            return stage_id, confidence
            
        except Exception as e:
            print(f"   ⚠️ Stage detection failed: {e}")
            # Fallback to time-based detection
            for stage in stages:
                start = stage['startOffsetSeconds']
                end = start + stage['durationSeconds']
                if start <= call_elapsed_seconds < end:
                    return stage['id'], 0.3  # Low confidence = fallback
            return stages[0]['id'] if stages else '', 0.3
    
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

