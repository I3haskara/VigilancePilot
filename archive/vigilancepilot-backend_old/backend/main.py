# LEGACY BACKEND – not used for VigilancePilot child safety or hackathon demo.
# Kept only as a reference for the older API testing tool.
"""
VigilancePilot FastAPI Backend Server
Main application entry point for API validation and testing orchestration
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Dict, Any, List
import uvicorn

from models import (
    APITestRequest,
    APITestResponse,
    ValidationResult,
    HealthCheck,
    AGIScoreRequest,
    AGIScoreResponse,
)
from agi_scorer import AGIScorer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global AGI Scorer instance
agi_scorer: AGIScorer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global agi_scorer
    
    # Startup
    logger.info("Starting VigilancePilot Backend Server...")
    agi_scorer = AGIScorer()
    await agi_scorer.initialize()
    logger.info("AGI Scorer initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down VigilancePilot Backend Server...")
    if agi_scorer:
        await agi_scorer.cleanup()
    logger.info("Cleanup completed")


# Initialize FastAPI app
app = FastAPI(
    title="VigilancePilot API",
    description="Intelligent API validation and testing orchestration platform",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "VigilancePilot API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    agi_status = await agi_scorer.check_health() if agi_scorer else False
    
    return HealthCheck(
        status="healthy" if agi_status else "degraded",
        agi_scorer_ready=agi_status,
        version="0.1.0"
    )


@app.post("/api/test", response_model=APITestResponse)
async def test_api_endpoint(request: APITestRequest):
    """
    Test an API endpoint and validate responses
    
    Args:
        request: API test configuration including URL, method, headers, etc.
    
    Returns:
        Validation results with AGI scoring
    """
    try:
        logger.info(f"Testing API: {request.method} {request.url}")
        
        # Execute API test
        result = await agi_scorer.test_and_validate(
            url=request.url,
            method=request.method,
            headers=request.headers,
            body=request.body,
            expected_status=request.expected_status,
            validation_rules=request.validation_rules
        )
        
        logger.info(f"API test completed: {result.status}")
        return result
        
    except Exception as e:
        logger.error(f"API test failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"API test failed: {str(e)}")


@app.post("/api/score", response_model=AGIScoreResponse)
async def score_api_response(request: AGIScoreRequest):
    """
    Score an API response using AGI
    
    Args:
        request: API response data to score
    
    Returns:
        AGI scoring results with recommendations
    """
    try:
        logger.info(f"Scoring API response for: {request.endpoint}")
        
        score_result = await agi_scorer.score_response(
            endpoint=request.endpoint,
            response_data=request.response_data,
            expected_schema=request.expected_schema,
            context=request.context
        )
        
        logger.info(f"Scoring completed: {score_result.overall_score}/100")
        return score_result
        
    except Exception as e:
        logger.error(f"Scoring failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


@app.post("/api/validate/batch", response_model=List[APITestResponse])
async def validate_batch(
    requests: List[APITestRequest],
    background_tasks: BackgroundTasks
):
    """
    Batch validate multiple API endpoints
    
    Args:
        requests: List of API test requests
        background_tasks: FastAPI background tasks
    
    Returns:
        List of validation results
    """
    try:
        logger.info(f"Batch validation started: {len(requests)} endpoints")
        
        results = await agi_scorer.batch_validate(requests)
        
        logger.info(f"Batch validation completed: {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Batch validation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch validation failed: {str(e)}"
        )


@app.get("/api/history", response_model=List[Dict[str, Any]])
async def get_test_history(limit: int = 50):
    """
    Get recent test history
    
    Args:
        limit: Maximum number of results to return
    
    Returns:
        List of historical test results
    """
    try:
        history = await agi_scorer.get_history(limit=limit)
        return history
        
    except Exception as e:
        logger.error(f"Failed to retrieve history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve history: {str(e)}"
        )


@app.delete("/api/history")
async def clear_history():
    """Clear test history"""
    try:
        await agi_scorer.clear_history()
        return {"message": "History cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear history: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
