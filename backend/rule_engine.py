"""
Rule-Based Grooming Detection Engine
Fast pattern matching for known grooming tactics
"""
import os
import json
import re
from typing import List, Dict, Tuple


class RuleEngine:
    """Pattern-based grooming detection using clinically validated indicators"""

    def __init__(self):
        """Initialize with grooming patterns"""
        self.rules = self._load_grooming_patterns()
        self._compile_patterns()

    def analyze_message(
        self,
        message: str,
        child_id: str = None,
        platform: str = None,
        context: dict = None,
        timestamp: str = None,
        conversation_id: str = None,
        **kwargs
    ) -> dict:
        """
        Analyze a message for grooming risk using rule patterns.
        Returns a dict compatible with risk_aggregator.py contract.
        """
        result = self.analyze(message)
        # Normalize output for risk_aggregator.py
        return {
            "risk_score": float(result.get("score", 0.0)),
            "risk_level": (
                "high" if result.get("score", 0.0) >= 75 else
                "medium" if result.get("score", 0.0) >= 40 else
                "low"
            ),
            "matched_patterns": result.get("triggered_rules", []),
            "reason": ", ".join([d.get("name", "") for d in result.get("rule_details", []) if d.get("name")]),
        }

    def _load_grooming_patterns(self) -> List[Dict]:
        """Load grooming patterns from JSON file"""
        try:
            BASE_DIR = os.path.dirname(__file__)
            PATTERNS_PATH = os.path.join(BASE_DIR, "grooming_rules", "grooming_patterns.json")
            with open(PATTERNS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("tactics", [])
        except Exception as e:
            print(f"Warning: Could not load grooming_patterns.json: {e}")
        # Fallback to hardcoded patterns
        return self._get_default_patterns()
    
    def _get_default_patterns(self) -> List[Dict]:
        """Default grooming patterns if JSON not available"""
        return [
            {
                "id": "secrecy_explicit",
                "name": "Explicit secrecy",
                "weight": 35,
                "keywords": ["don't tell", "our secret", "keep this secret"],
                "regex": ["don'?t tell (your )?parents", "\\bour secret\\b"]
            },
            {
                "id": "meeting_request",
                "name": "Meeting request",
                "weight": 40,
                "keywords": ["let's meet", "meet up", "come over"],
                "regex": ["\\b(let's|we should|can we) meet\\b", "\\bcome over\\b"]
            },
            {
                "id": "isolation",
                "name": "Isolation attempt",
                "weight": 30,
                "keywords": ["parents don't understand", "they don't get it"],
                "regex": ["parents.*(don't|won't|wouldn't).*understand"]
            },
            {
                "id": "age_request",
                "name": "Age probing",
                "weight": 10,
                "keywords": ["how old", "what grade", "age"],
                "regex": ["\\bhow old are (you|u)\\b"]
            },
            {
                "id": "gift_offer",
                "name": "Gift/incentive offer",
                "weight": 25,
                "keywords": ["i'll buy", "gift", "present", "money"],
                "regex": ["\\b(buy|get|give).*(you|u)\\b"]
            }
        ]
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        for rule in self.rules:
            rule["compiled_regex"] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in rule.get("regex", [])
            ]
    
    def analyze(self, message: str, history: List[Dict] = None) -> Dict:
        """
        Analyze message for grooming patterns
        
        Returns:
            {
                "score": float (0-100),
                "triggered_rules": List[str],
                "rule_details": List[Dict]
            }
        """
        history = history or []
        message_lower = message.lower()
        
        triggered_rules = []
        rule_details = []
        total_score = 0.0
        
        # Check each rule
        for rule in self.rules:
            is_triggered = False
            
            # Check keywords
            for keyword in rule.get("keywords", []):
                if keyword.lower() in message_lower:
                    is_triggered = True
                    break
            
            # Check regex patterns
            if not is_triggered:
                for pattern in rule.get("compiled_regex", []):
                    if pattern.search(message):
                        is_triggered = True
                        break
            
            if is_triggered:
                weight = rule.get("weight", 10)
                triggered_rules.append(rule["id"])
                total_score += weight
                
                rule_details.append({
                    "rule": rule["id"],
                    "name": rule.get("name", ""),
                    "score": weight
                })
        
        # Cap at 100
        total_score = min(total_score, 100.0)
        
        return {
            "score": total_score,
            "triggered_rules": triggered_rules,
            "rule_details": rule_details
        }


if __name__ == "__main__":
    # Test
    engine = RuleEngine()
    
    test_cases = [
        "Hi, how are you?",
        "Don't tell your parents about this",
        "Let's meet up tomorrow",
        "Your parents don't understand you"
    ]
    
    for msg in test_cases:
        result = engine.analyze(msg)
        print(f"\nMessage: {msg}")
        print(f"Score: {result['score']}")
        print(f"Triggered: {result['triggered_rules']}")
