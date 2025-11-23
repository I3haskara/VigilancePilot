"""
AGI scoring function for VigilancePilot backend
"""

from backend.agi_scorer import AGIScorer
import asyncio

# Standalone async scoring function
async def score_message(message_content: str):
    scorer = AGIScorer()
    return await scorer.score_message(message_content)

def sync_score_message(message_content: str):
    # If the original function is async, call it using a local event loop:
    # return asyncio.run(score_message(message_content))
    
    # OR, if the original function is a standard, sync LLM call, just return it:
    # return original_sync_scoring_function(message_content)
    
    # For now, just return a placeholder to get the server running:
    return 5.0 # Placeholder risk score
