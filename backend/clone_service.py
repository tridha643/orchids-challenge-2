import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
import uuid

from scraper import WebScraper
from llm_service import LLMService
from precision_calculator import precision_calculator
from models import (
    CloneRequest, CloneOptions, CloneStatus, CloneResult, ScrapedData, PrecisionMetrics,
    clone_jobs, clone_results, generate_clone_id
)
from config import settings

class CloneService:
    """Main service for orchestrating website cloning"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.active_jobs: Dict[str, asyncio.Task] = {}
        
    async def start_clone_job(self, request: CloneRequest) -> str:
        """
        Start a new website cloning job
        
        Returns:
            str: Clone job ID
        """
        # Generate unique job ID
        clone_id = generate_clone_id()
        
        # Create initial job status
        now = datetime.now()
        job_status = CloneStatus(
            id=clone_id,
            status="pending",
            progress=0,
            message="Clone job started",
            created_at=now,
            updated_at=now,
            estimated_completion=now + timedelta(seconds=60)
        )
        
        # Store job status
        clone_jobs[clone_id] = job_status
        
        # Start the cloning task
        task = asyncio.create_task(self._process_clone_job(clone_id, request))
        self.active_jobs[clone_id] = task
        
        return clone_id
    
    async def get_clone_status(self, clone_id: str) -> Optional[CloneStatus]:
        """Get the status of a clone job"""
        return clone_jobs.get(clone_id)
    
    async def get_clone_result(self, clone_id: str) -> Optional[CloneResult]:
        """Get the result of a completed clone job"""
        return clone_results.get(clone_id)
    
    async def cancel_clone_job(self, clone_id: str) -> bool:
        """Cancel an active clone job"""
        if clone_id in self.active_jobs:
            task = self.active_jobs[clone_id]
            task.cancel()
            
            # Update status
            if clone_id in clone_jobs:
                clone_jobs[clone_id].status = "error"
                clone_jobs[clone_id].message = "Job cancelled by user"
                clone_jobs[clone_id].updated_at = datetime.now()
            
            del self.active_jobs[clone_id]
            return True
        return False
    
    async def _process_clone_job(self, clone_id: str, request: CloneRequest):
        """
        Process a clone job through all stages
        """
        try:
            start_time = time.time()
            
            # Update status: scraping
            await self._update_job_status(
                clone_id, 
                "scraping", 
                10, 
                "Scraping website data..."
            )
            
            # Phase 1: Scrape the website
            scraped_data = await self._scrape_website(str(request.url), request.options)
            
            # Update status: processing
            await self._update_job_status(
                clone_id, 
                "processing", 
                40, 
                "Processing scraped data..."
            )
            
            # Small delay to simulate processing
            await asyncio.sleep(1)
            
            # Update status: generating
            await self._update_job_status(
                clone_id, 
                "generating", 
                70, 
                "Generating HTML/CSS with AI..."
            )
            
            # Phase 2: Generate HTML/CSS using LLM
            html_content, css_content = await self._generate_clone(scraped_data, request.options)
            
            # Update status: finalizing
            await self._update_job_status(
                clone_id, 
                "generating", 
                90, 
                "Finalizing clone..."
            )
            
            # Phase 3: Calculate precision metrics
            await self._update_job_status(
                clone_id, 
                "generating", 
                95, 
                "Calculating precision metrics..."
            )
            
            precision_metrics = await self._calculate_precision_metrics(
                scraped_data.html, 
                html_content
            )
            
            # Phase 4: Save result and create preview
            preview_url = await self._save_clone_result(clone_id, html_content)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create final result
            result = CloneResult(
                id=clone_id,
                status="complete",
                original_url=str(request.url),
                generated_html=html_content,
                generated_css=css_content,
                preview_url=preview_url,
                processing_time=processing_time,
                precision_metrics=precision_metrics,
                # Keep similarity_score for backwards compatibility
                similarity_score=precision_metrics.overall_precision if precision_metrics else 0.0,
                created_at=clone_jobs[clone_id].created_at,
                completed_at=datetime.now()
            )
            
            # Store result
            clone_results[clone_id] = result
            
            # Update final status
            await self._update_job_status(
                clone_id, 
                "complete", 
                100, 
                "Clone completed successfully!"
            )
            
        except asyncio.CancelledError:
            # Job was cancelled
            await self._update_job_status(
                clone_id, 
                "error", 
                0, 
                "Job was cancelled"
            )
            
        except Exception as e:
            # Handle errors
            error_message = f"Clone failed: {str(e)}"
            
            # Create error result
            result = CloneResult(
                id=clone_id,
                status="error",
                original_url=str(request.url),
                error_message=error_message,
                created_at=clone_jobs[clone_id].created_at,
                completed_at=datetime.now()
            )
            
            clone_results[clone_id] = result
            
            await self._update_job_status(
                clone_id, 
                "error", 
                0, 
                error_message
            )
            
        finally:
            # Clean up active job
            if clone_id in self.active_jobs:
                del self.active_jobs[clone_id]
    
    async def _scrape_website(self, url: str, options: CloneOptions) -> ScrapedData:
        """Scrape website data using WebScraper"""
        
        async with WebScraper() as scraper:
            scraped_data = await scraper.scrape_website(url, options)
            return scraped_data
    
    async def _generate_clone(self, scraped_data: ScrapedData, options: CloneOptions) -> tuple[str, str]:
        """Generate HTML/CSS clone using LLM service"""
        
        html_content, css_content = await self.llm_service.generate_website_clone(
            scraped_data, 
            options
        )
        
        return html_content, css_content
    
    async def _calculate_precision_metrics(self, original_html: str, generated_html: str) -> Optional[PrecisionMetrics]:
        """Calculate precision metrics comparing original and generated HTML"""
        
        try:
            # Run precision calculation in a thread pool to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            
            metrics_dict = await loop.run_in_executor(
                None,
                precision_calculator.calculate_precision,
                original_html,
                generated_html
            )
            
            # Convert to PrecisionMetrics model
            precision_metrics = PrecisionMetrics(**metrics_dict)
            
            return precision_metrics
            
        except Exception as e:
            print(f"Failed to calculate precision metrics: {e}")
            # Return default metrics on error
            return PrecisionMetrics(
                overall_precision=0.0,
                structure_similarity=0.0,
                content_similarity=0.0,
                styling_similarity=0.0,
                semantic_similarity=0.0,
                layout_similarity=0.0,
                confidence="low"
            )
    
    async def _save_clone_result(self, clone_id: str, html_content: str) -> str:
        """Save the generated HTML and create preview URL"""
        
        try:
            # Create previews directory if it doesn't exist
            previews_dir = Path("storage/previews")
            previews_dir.mkdir(parents=True, exist_ok=True)
            
            # Save HTML file
            html_file = previews_dir / f"{clone_id}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Return preview URL (relative path)
            return f"/api/clone/{clone_id}/preview"
            
        except Exception as e:
            print(f"Failed to save clone result: {e}")
            return None
    
    async def _update_job_status(
        self, 
        clone_id: str, 
        status: str, 
        progress: int, 
        message: str
    ):
        """Update job status"""
        
        if clone_id in clone_jobs:
            job = clone_jobs[clone_id]
            job.status = status
            job.progress = progress
            job.message = message
            job.updated_at = datetime.now()
    
    async def get_preview_html(self, clone_id: str) -> Optional[str]:
        """Get the generated HTML for preview"""
        
        try:
            html_file = Path("storage/previews") / f"{clone_id}.html"
            if html_file.exists():
                with open(html_file, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"Failed to read preview HTML: {e}")
        
        return None
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old jobs and results"""
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        # Clean up old job statuses
        expired_jobs = [
            job_id for job_id, job in clone_jobs.items()
            if job.created_at < cutoff_time
        ]
        
        for job_id in expired_jobs:
            # Remove from memory
            clone_jobs.pop(job_id, None)
            clone_results.pop(job_id, None)
            
            # Remove preview file
            try:
                html_file = Path("storage/previews") / f"{job_id}.html"
                if html_file.exists():
                    html_file.unlink()
            except:
                pass
        
        return len(expired_jobs)

# Global clone service instance
clone_service = CloneService() 