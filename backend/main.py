import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import settings
from models import (
    CloneRequest, CloneResponse, CloneStatus, CloneResult, ErrorResponse,
    CloneOptions
)
from clone_service import clone_service
from services.agentic_clone_service import agentic_clone_service

# Ensure storage directories exist
os.makedirs("storage/previews", exist_ok=True)
os.makedirs("storage/assets", exist_ok=True)
os.makedirs("storage/screenshots", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    print("🚀 Website Cloner API starting up...")
    
    # Initialize Agentic Clone service
    await agentic_clone_service.initialize()
    
    # Install Playwright browsers if needed
    try:
        import playwright
        print("📦 Installing Playwright browsers...")
        os.system("playwright install chromium")
    except Exception as e:
        print(f"⚠️ Playwright setup warning: {e}")
    
    yield
    
    # Shutdown
    print("👋 Website Cloner API shutting down...")
    
    # Clean up Agentic services
    await agentic_clone_service.close()
    
    # Clean up any active jobs
    for job_id, task in clone_service.active_jobs.items():
        task.cancel()

# Create FastAPI app
app = FastAPI(
    title="Website Cloner API",
    description="AI-powered website cloning service using web scraping and LLM generation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mount static files for previews
app.mount("/static", StaticFiles(directory="storage"), name="static")

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Website Cloner API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "clone": "POST /api/clone",
            "status": "GET /api/clone/{id}",
            "result": "GET /api/clone/{id}/result",
            "preview": "GET /api/clone/{id}/preview",
            "precision": "GET /api/clone/{id}/precision"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "website-cloner-api",
        "active_jobs": len(clone_service.active_jobs)
    }

# Clone endpoints
@app.post("/api/clone", response_model=CloneResponse)
async def create_clone(request: CloneRequest, background_tasks: BackgroundTasks):
    """
    Standard website cloning (existing functionality)
    """
    """
    Start a new website cloning job
    
    - **url**: The website URL to clone
    - **options**: Cloning options (optional)
    """
    try:
        # Validate URL
        url_str = str(request.url)
        if not url_str.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid URL format. Must start with http:// or https://"
            )
        
        # Check if we have too many active jobs
        if len(clone_service.active_jobs) >= settings.max_concurrent_clones:
            raise HTTPException(
                status_code=429,
                detail=f"Too many active cloning jobs. Maximum: {settings.max_concurrent_clones}"
            )
        
        # Start the cloning job
        clone_id = await clone_service.start_clone_job(request)
        
        # Schedule cleanup task
        background_tasks.add_task(cleanup_old_jobs)
        
        return CloneResponse(
            id=clone_id,
            status="pending",
            message="Clone job started successfully",
            estimated_time=60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start clone job: {str(e)}")

@app.post("/api/agentic-clone", response_model=CloneResponse)
async def create_agentic_clone(request: CloneRequest):
    """
    AI-powered website cloning with memory and style intelligence
    
    - **url**: The website URL to clone
    - **options**: Enhanced cloning options with target_style, animations, etc.
    """
    try:
        # Validate URL
        url_str = str(request.url)
        if not url_str.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid URL format. Must start with http:// or https://"
            )
        
        # Process through Agentic Clone pipeline
        result = await agentic_clone_service.clone_website(request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agentic clone failed: {str(e)}")

@app.get("/api/clone/{clone_id}", response_model=CloneStatus)
async def get_clone_status(clone_id: str):
    """
    Get the status of a cloning job
    
    - **clone_id**: The ID of the clone job
    """
    job_status = await clone_service.get_clone_status(clone_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="Clone job not found")
    
    return job_status

@app.get("/api/clone/{clone_id}/result", response_model=CloneResult)
async def get_clone_result(clone_id: str):
    """
    Get the result of a completed cloning job
    
    - **clone_id**: The ID of the clone job
    """
    result = await clone_service.get_clone_result(clone_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Clone result not found")
    
    return result

@app.get("/api/clone/{clone_id}/preview", response_class=HTMLResponse)
async def get_clone_preview(clone_id: str):
    """
    Get the generated HTML preview of a cloned website
    
    - **clone_id**: The ID of the clone job
    """
    html_content = await clone_service.get_preview_html(clone_id)
    
    if not html_content:
        raise HTTPException(status_code=404, detail="Preview not found")
    
    return HTMLResponse(content=html_content)

@app.get("/api/clone/{clone_id}/precision")
async def get_precision_metrics(clone_id: str):
    """
    Get detailed precision metrics for a completed clone job
    
    - **clone_id**: The ID of the clone job
    """
    result = await clone_service.get_clone_result(clone_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Clone result not found")
    
    if result.status != "complete":
        raise HTTPException(status_code=400, detail="Clone job is not completed yet")
    
    if not result.precision_metrics:
        raise HTTPException(status_code=404, detail="Precision metrics not available")
    
    return {
        "clone_id": clone_id,
        "original_url": result.original_url,
        "precision_metrics": result.precision_metrics,
        "calculation_timestamp": result.completed_at,
        "interpretation": {
            "overall_precision": _interpret_score(result.precision_metrics.overall_precision),
            "structure_similarity": _interpret_score(result.precision_metrics.structure_similarity),
            "content_similarity": _interpret_score(result.precision_metrics.content_similarity),
            "styling_similarity": _interpret_score(result.precision_metrics.styling_similarity),
            "semantic_similarity": _interpret_score(result.precision_metrics.semantic_similarity),
            "layout_similarity": _interpret_score(result.precision_metrics.layout_similarity),
        }
    }

def _interpret_score(score: float) -> str:
    """Interpret precision score with human-readable descriptions"""
    if score >= 0.9:
        return "Excellent - Nearly identical"
    elif score >= 0.8:
        return "Very Good - High similarity"
    elif score >= 0.7:
        return "Good - Substantial similarity"
    elif score >= 0.6:
        return "Fair - Moderate similarity"
    elif score >= 0.4:
        return "Poor - Limited similarity"
    else:
        return "Very Poor - Minimal similarity"

@app.delete("/api/clone/{clone_id}")
async def cancel_clone_job(clone_id: str):
    """
    Cancel an active cloning job
    
    - **clone_id**: The ID of the clone job
    """
    success = await clone_service.cancel_clone_job(clone_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Clone job not found or already completed")
    
    return {"message": "Clone job cancelled successfully"}

@app.get("/api/clone")
async def list_recent_clones():
    """
    List recent clone jobs (last 50)
    """
    from models import clone_jobs, clone_results
    
    # Get recent jobs
    recent_jobs = list(clone_jobs.values())[-50:]
    recent_results = list(clone_results.values())[-50:]
    
    return {
        "active_jobs": len(clone_service.active_jobs),
        "recent_jobs": len(recent_jobs),
        "recent_results": len(recent_results),
        "jobs": [
            {
                "id": job.id,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
                "updated_at": job.updated_at.isoformat()
            }
            for job in recent_jobs
        ]
    }

# Preview proxy endpoint
@app.get("/api/preview-proxy")
async def preview_proxy(url: str):
    """
    Proxy endpoint to serve preview content with proper headers
    """
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.text()
                
                # Force proper content type for HTML
                if url.endswith('.html') or 'html' in content.lower()[:100]:
                    return HTMLResponse(
                        content=content,
                        headers={
                            "Content-Type": "text/html; charset=utf-8",
                            "X-Frame-Options": "ALLOWALL",
                            "Access-Control-Allow-Origin": "*"
                        }
                    )
                else:
                    return Response(
                        content=content,
                        media_type=response.headers.get('content-type', 'text/plain'),
                        headers={
                            "Access-Control-Allow-Origin": "*"
                        }
                    )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to proxy URL: {str(e)}")

# Utility endpoints
@app.post("/api/test")
async def test_endpoint(url: str = "https://example.com"):
    """
    Test endpoint for quick functionality check
    """
    try:
        # Test with minimal options
        options = CloneOptions(
            max_wait_time=10,
            include_images=False,
            include_fonts=False
        )
        
        request = CloneRequest(url=url, options=options)
        clone_id = await clone_service.start_clone_job(request)
        
        return {
            "message": "Test clone started",
            "clone_id": clone_id,
            "check_status": f"/api/clone/{clone_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# Background tasks
async def cleanup_old_jobs():
    """Background task to cleanup old jobs"""
    try:
        cleaned_count = await clone_service.cleanup_old_jobs(max_age_hours=24)
        if cleaned_count > 0:
            print(f"🧹 Cleaned up {cleaned_count} old clone jobs")
    except Exception as e:
        print(f"❌ Cleanup task failed: {e}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "message": "The requested resource was not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"}
    )

# Development server
def main():
    """Run the development server"""
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 