"""
Real-time intent detection for in-call assistance
Detects triggers in transcript and suggests coaching hints
"""

import json
import os
import re
from typing import Optional, Dict, List
from datetime import datetime, timedelta


class IntentDetector:
    """Detects intent triggers in conversation and returns coaching hints"""
    
    def __init__(self, playbook_path: str = None):
        """
        Initialize intent detector
        
        Args:
            playbook_path: Path to playbook.json with triggers and hints
        """
        if playbook_path is None:
            # Default to backend/playbook.json
            playbook_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "playbook.json"
            )
        
        self.playbook_path = playbook_path
        self.playbook = self._load_playbook()
        self.last_trigger = None
        self.last_trigger_time = None
        self.trigger_cooldown_seconds = 30  # Don't repeat same trigger within 30s
        
        print(f"🎯 IntentDetector initialized with {len(self.playbook)} triggers")
    
    def _load_playbook(self) -> List[Dict]:
        """Load triggers from playbook.json"""
        try:
            with open(self.playbook_path, 'r', encoding='utf-8') as f:
                playbook = json.load(f)
            print(f"📖 Playbook loaded: {self.playbook_path}")
            return playbook
        except Exception as e:
            print(f"⚠️ Failed to load playbook: {e}")
            return []
    
    def detect_trigger(self, transcript: str, language: str = "id") -> Optional[Dict]:
        """
        Detect trigger in transcript
        
        Args:
            transcript: Recent transcription text
            language: Language code (for future LLM-based detection)
            
        Returns:
            Trigger dict with title, hint, priority if found, None otherwise
        """
        if not transcript or len(transcript.strip()) < 5:
            return None
        
        transcript_lower = transcript.lower()
        best_match = None
        best_priority = -1
        
        print(f"\n   🔎 Intent Detector: checking {len(self.playbook)} triggers")
        print(f"      Text: '{transcript_lower[:80]}'")
        
        # Check each trigger in playbook
        for trigger in self.playbook:
            trigger_id = trigger.get("id")
            match_keywords = trigger.get("match", [])
            priority = trigger.get("priority", 0)
            
            # Check if any keyword matches
            for keyword in match_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in transcript_lower:
                    # For Cyrillic, word boundaries (\b) don't work, so use simple substring match
                    # For ASCII, use word boundary for precision
                    if keyword.isascii():
                        pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                        if not re.search(pattern, transcript_lower):
                            continue  # ASCII keyword needs word boundary
                    
                    # Found a match
                    print(f"      ✅ MATCH: '{keyword}' in '{trigger_id}' (priority {priority})")
                    if priority > best_priority:
                        best_priority = priority
                        best_match = trigger
                    break
                else:
                    # Substring check failed, but for debugging only show for first few triggers
                    if trigger_id == "price_objection":  # Debug only for price trigger
                        print(f"      ❌ No '{keyword}' in text")
        
        if not best_match:
            print(f"      ❌ No triggers matched")
            return None
        
        # Anti-spam: don't repeat same trigger within cooldown
        trigger_id = best_match.get("id")
        if self.last_trigger == trigger_id:
            time_since_last = datetime.now() - self.last_trigger_time
            if time_since_last.total_seconds() < self.trigger_cooldown_seconds:
                print(f"   ⏳ Trigger '{trigger_id}' already active (skip spam)")
                return None
        
        # Update last trigger
        self.last_trigger = trigger_id
        self.last_trigger_time = datetime.now()
        
        print(f"🎯 TRIGGER DETECTED: {best_match.get('title')}")
        print(f"   Hint: {best_match.get('hint')}")
        
        return best_match
    
    def reload_playbook(self):
        """Reload playbook from disk (for live editing)"""
        self.playbook = self._load_playbook()
        print(f"🔄 Playbook reloaded: {len(self.playbook)} triggers")


# Global instance
_detector: Optional[IntentDetector] = None


def get_intent_detector() -> IntentDetector:
    """Get or create global intent detector instance"""
    global _detector
    if _detector is None:
        _detector = IntentDetector()
    return _detector


def reset_detector():
    """Reset detector (for testing)"""
    global _detector
    _detector = None
