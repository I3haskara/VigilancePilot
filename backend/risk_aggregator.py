
"""
Risk Aggregator - Combines Rule-Based + LLM Scores
Uses weighted formula: 60% rules + 40% LLM
"""

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
