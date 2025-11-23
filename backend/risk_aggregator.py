"""
Risk Aggregator for VigilancePilot
----------------------------------
This module orchestrates:
- RuleEngine for rule-based grooming detection
- AGIScorer for LLM/AI-driven risk scoring
- Normalization of outputs
- Combined risk score + level classification

This file is intentionally clean and minimal.
"""

from typing import Any, Dict

from backend.rule_engine import RuleEngine
from backend.agi_scorer import AGIScorer

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert any numeric-looking field to a float.
    """
    try:
        return float(value)
    except Exception:
        return default


def _extract_score(result: Dict[str, Any], default: float = 0.0) -> float:
    """
    RuleEngine and AGIScorer may return different score keys.
    Normalize by pulling from the first matching key.
    """
    possible = ("score", "risk_score", "rule_score", "agi_score")
    for key in possible:
        if key in result and isinstance(result[key], (int, float)):
            return _safe_float(result[key])
    return default


# Weights for combining rule-based and AI-based scoring
RULE_WEIGHT = 0.6
AI_WEIGHT = 0.4

# Thresholds for final classification
THRESHOLD_LOW = 40.0
THRESHOLD_MEDIUM = 70.0


# ---------------------------------------------------------------------------
# Risk Combination Logic
# ---------------------------------------------------------------------------

def combine_scores(rule_score: float, ai_score: float) -> float:
    """
    Weighted combination of rule-based and AGI-based scores.
    Returns a value between 0 and 100.
    """
    rule_score = max(0.0, min(100.0, rule_score))
    ai_score = max(0.0, min(100.0, ai_score))

    combined = (rule_score * RULE_WEIGHT) + (ai_score * AI_WEIGHT)
    return round(combined, 2)


def classify_risk(score: float) -> str:
    """
    Convert numeric score → risk band.
    """
    if score < THRESHOLD_LOW:
        return "low"
    if score < THRESHOLD_MEDIUM:
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# MAIN ENTRYPOINT USED BY FASTAPI
# ---------------------------------------------------------------------------

def run_full_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Master analysis function called by FastAPI endpoint /api/analyze.
    Performs rule engine scoring + AGI scoring, then aggregates.
    """

    # Extract fields with safe defaults
    message: str = payload.get("message", "") or ""
    child_id = payload.get("child_id")
    platform = payload.get("platform")
    context: Dict[str, Any] = payload.get("context") or {}
    timestamp = payload.get("timestamp")
    conversation_id = payload.get("conversation_id")

    # ----------------------------------------------------------------------
    # RuleEngine analysis
    # ----------------------------------------------------------------------
    rule_engine = RuleEngine()
    rule_raw = rule_engine.analyze_message(
        message=message,
        child_id=child_id,
        platform=platform,
        context=context,
        timestamp=timestamp,
        conversation_id=conversation_id,
    )

    rule_score = _extract_score(rule_raw, default=0.0)

    # ----------------------------------------------------------------------
    # AGI (LLM) analysis
    # ----------------------------------------------------------------------
    agi = AGIScorer()
    ai_raw = agi.analyze_message(
        message=message,
        child_id=child_id,
        platform=platform,
        context=context,
        timestamp=timestamp,
        conversation_id=conversation_id,
    )

    ai_score = _extract_score(ai_raw, default=0.0)

    # ----------------------------------------------------------------------
    # Combine into final output
    # ----------------------------------------------------------------------
    final_score = combine_scores(rule_score, ai_score)
    risk_level = classify_risk(final_score)

    return {
        "child_id": child_id,
        "platform": platform,
        "message": message,
        "risk_score": final_score,
        "risk_level": risk_level,
        "rule_score": rule_score,
        "agi_score": ai_score,
        "timestamp": timestamp,
        "conversation_id": conversation_id,
        "rule_details": rule_raw,
        "agi_details": ai_raw,
    }

"""
Central risk aggregation for VigilancePilot.

Combines rule-based and AGI-based scores using weighted formula (60% rules, 40% LLM).
Returns a flat dict that FastAPI can serialize directly.
Includes utilities for risk breakdown and classification.
"""

from typing import Any, Dict, Optional
from backend.rule_engine import RuleEngine
from backend.agi_scorer import AGIScorer

# Risk thresholds
THRESHOLD_LOW = 40.0
THRESHOLD_MEDIUM = 70.0

# Weights
RULE_WEIGHT = 0.6
LLM_WEIGHT = 0.4

def _safe_get_score(result: Dict[str, Any], default: float = 0.0) -> float:
    """
    Extract score from result dict, fallback to default.
    """
    for key in ("rule_score", "agi_score", "risk_score", "score"):
        if key in result and isinstance(result[key], (int, float)):
            return float(result[key])
    return float(default)

def aggregate_risk(rule_score: float, llm_score: float) -> float:
    """
    Combine rule and LLM scores using weighted formula.
    """
    rule_score = max(0.0, min(100.0, rule_score))
    llm_score = max(0.0, min(100.0, llm_score))
    return round((rule_score * RULE_WEIGHT) + (llm_score * LLM_WEIGHT), 2)

def classify_risk_level(score: float) -> str:
    """
    Classify risk level based on score.
    """
    if score < THRESHOLD_LOW:
        return "LOW"
    elif score < THRESHOLD_MEDIUM:
        return "MEDIUM"
    else:
        return "HIGH"

def get_risk_breakdown(rule_score: float, llm_score: float) -> Dict[str, Any]:
    """
    Get detailed breakdown of risk calculation.
    """
    final_score = aggregate_risk(rule_score, llm_score)
    risk_level = classify_risk_level(final_score)
    return {
        "final_score": final_score,
        "risk_level": risk_level,
        "components": {
            "rule_score": round(rule_score, 2),
            "rule_contribution": round(rule_score * RULE_WEIGHT, 2),
            "rule_weight": RULE_WEIGHT,
            "llm_score": round(llm_score, 2),
            "llm_contribution": round(llm_score * LLM_WEIGHT, 2),
            "llm_weight": LLM_WEIGHT
        },
        "thresholds": {
            "low": THRESHOLD_LOW,
            "medium": THRESHOLD_MEDIUM
        }
    }

def run_full_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrate rule + AGI scoring and aggregate risk.
    Returns unified dict for FastAPI serialization.
    """
    message: str = payload.get("message", "")
    child_id: Optional[str] = payload.get("child_id")
    platform: Optional[str] = payload.get("platform")
    context: Dict[str, Any] = payload.get("context") or {}
    timestamp: Optional[str] = payload.get("timestamp")
    conversation_id: Optional[str] = payload.get("conversation_id")

    rule_engine = RuleEngine()
    rule_result: Dict[str, Any] = rule_engine.analyze_message(
        message=message,
        child_id=child_id,
        platform=platform,
        context=context,
        timestamp=timestamp,
        conversation_id=conversation_id,
    )

    agi = AGIScorer()
    agi_result: Dict[str, Any] = agi.analyze_message(
        message=message,
        child_id=child_id,
        platform=platform,
        context=context,
        timestamp=timestamp,
        conversation_id=conversation_id,
    )

    rule_score = _safe_get_score(rule_result, default=0.0)
    agi_score = _safe_get_score(agi_result, default=0.0)
    risk_score = aggregate_risk(rule_score, agi_score)
    risk_level = classify_risk_level(risk_score)

    return {
        "child_id": child_id,
        "platform": platform,
        "message": message,
        "rule_score": rule_score,
        "agi_score": agi_score,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "timestamp": timestamp,
        "conversation_id": conversation_id,
        "rule_details": rule_result,
        "agi_details": agi_result
    }

if __name__ == "__main__":
    # Simple test cases
    test_cases = [
        (20, 30),   # LOW
        (50, 60),   # MEDIUM
        (80, 90),   # HIGH
        (70, 50),   # MEDIUM
    ]
    for rule, llm in test_cases:
        breakdown = get_risk_breakdown(rule, llm)
        print(f"\nRule: {rule}, LLM: {llm}")
        print(f"Final: {breakdown['final_score']} → {breakdown['risk_level']}")
# Risk thresholds
THRESHOLD_LOW = 40.0
THRESHOLD_MEDIUM = 70.0

# Weights
RULE_WEIGHT = 0.6
LLM_WEIGHT = 0.4

def aggregate_risk(rule_score: float, llm_score: float) -> float:
    """
    Combine rule and LLM scores using weighted formula
    
    Args:
        rule_score: Score from rule engine (0-100)
        llm_score: Score from LLM (0-100)
    
    Returns:
        Final aggregated score (0-100)
    """
    # Validate inputs
    rule_score = max(0.0, min(100.0, rule_score))
    llm_score = max(0.0, min(100.0, llm_score))
    
    # Weighted combination
    final_score = (rule_score * RULE_WEIGHT) + (llm_score * LLM_WEIGHT)
    
    return max(0.0, min(100.0, final_score))

def classify_risk_level(score: float) -> str:
    """
    Classify risk level based on score
    
    Args:
        score: Aggregated score (0-100)
    
    Returns:
        "LOW", "MEDIUM", or "HIGH"
    """
    if score < THRESHOLD_LOW:
        return "LOW"
    elif score < THRESHOLD_MEDIUM:
        return "MEDIUM"
    else:
        return "HIGH"

def get_risk_breakdown(rule_score: float, llm_score: float) -> dict:
    """
    Get detailed breakdown of risk calculation
    
    Returns:
        Dictionary with final_score, risk_level, and component details
    """
    final_score = aggregate_risk(rule_score, llm_score)
    risk_level = classify_risk_level(final_score)
    
    return {
        "final_score": round(final_score, 2),
        "risk_level": risk_level,
        "components": {
            "rule_score": round(rule_score, 2),
            "rule_contribution": round(rule_score * RULE_WEIGHT, 2),
            "rule_weight": RULE_WEIGHT,
            "llm_score": round(llm_score, 2),
            "llm_contribution": round(llm_score * LLM_WEIGHT, 2),
            "llm_weight": LLM_WEIGHT
        },
        "thresholds": {
            "low": THRESHOLD_LOW,
            "medium": THRESHOLD_MEDIUM
        }
    }

if __name__ == "__main__":
    # Test
    test_cases = [
        (20, 30),   # LOW
        (50, 60),   # MEDIUM
        (80, 90),   # HIGH
        (70, 50),   # MEDIUM
    ]
    
    for rule, llm in test_cases:
        breakdown = get_risk_breakdown(rule, llm)
        print(f"\nRule: {rule}, LLM: {llm}")
        print(f"Final: {breakdown['final_score']} → {breakdown['risk_level']}")
