"""
Advanced Batch Processing System

Features:
- Priority queues
- Scheduled batch jobs
- Distributed processing
- Progress tracking
- Retry mechanisms
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
from collections import deque
import uuid


class BatchPriority(str, Enum):
    """Batch job priority levels"""
    URGENT = "urgent"       # Process immediately
    HIGH = "high"          # Within 5 minutes
    NORMAL = "normal"      # Within 30 minutes
    LOW = "low"            # When resources available


class BatchStatus(str, Enum):
    """Batch job status"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchJob(BaseModel):
    """Batch job model"""
    id: str
    name: str
    images: List[str]  # Image file paths or URLs
    priority: BatchPriority = BatchPriority.NORMAL
    status: BatchStatus = BatchStatus.PENDING
    progress: float = 0.0
    total_images: int
    processed_images: int = 0
    failed_images: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    user_id: str
    tenant_id: str
    xai_method: str = "gradcam"
    results: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class BatchProcessor:
    """Advanced batch processing engine"""
    
    def __init__(self, max_concurrent_jobs: int = 3, max_concurrent_images: int = 5):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.max_concurrent_images = max_concurrent_images
        
        # Priority queues
        self.urgent_queue: deque = deque()
        self.high_queue: deque = deque()
        self.normal_queue: deque = deque()
        self.low_queue: deque = deque()
        
        # Active jobs
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_tasks: Dict[str, asyncio.Task] = {}
        
        # Statistics
        self.total_jobs_processed = 0
        self.total_images_processed = 0
        
    async def submit_job(self, job: BatchJob) -> str:
        """Submit a batch job to the queue"""
        job.id = str(uuid.uuid4())
        job.status = BatchStatus.QUEUED
        job.created_at = datetime.now()
        job.total_images = len(job.images)
        
        # Add to appropriate queue based on priority
        if job.priority == BatchPriority.URGENT:
            self.urgent_queue.append(job)
        elif job.priority == BatchPriority.HIGH:
            self.high_queue.append(job)
        elif job.priority == BatchPriority.NORMAL:
            self.normal_queue.append(job)
        else:
            self.low_queue.append(job)
            
        # Start processor if not running
        await self._process_queue()
        
        return job.id
    
    async def schedule_job(self, job: BatchJob, scheduled_time: datetime) -> str:
        """Schedule a batch job for future execution"""
        job.scheduled_for = scheduled_time
        delay = (scheduled_time - datetime.now()).total_seconds()
        
        if delay > 0:
            # Schedule job
            await asyncio.sleep(delay)
        
        return await self.submit_job(job)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job"""
        # Check if job is in queue
        for queue in [self.urgent_queue, self.high_queue, self.normal_queue, self.low_queue]:
            for i, job in enumerate(queue):
                if job.id == job_id:
                    job.status = BatchStatus.CANCELLED
                    queue.remove(job)
                    return True
        
        # Check if job is active
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            job.status = BatchStatus.CANCELLED
            
            # Cancel task
            if job_id in self.job_tasks:
                self.job_tasks[job_id].cancel()
                
            return True
        
        return False
    
    async def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get job status"""
        # Check active jobs
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Check queues
        for queue in [self.urgent_queue, self.high_queue, self.normal_queue, self.low_queue]:
            for job in queue:
                if job.id == job_id:
                    return job
        
        return None
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "queued": {
                "urgent": len(self.urgent_queue),
                "high": len(self.high_queue),
                "normal": len(self.normal_queue),
                "low": len(self.low_queue),
                "total": len(self.urgent_queue) + len(self.high_queue) + len(self.normal_queue) + len(self.low_queue)
            },
            "active_jobs": len(self.active_jobs),
            "max_concurrent": self.max_concurrent_jobs,
            "total_processed": self.total_jobs_processed,
            "total_images_processed": self.total_images_processed
        }
    
    async def _process_queue(self):
        """Process jobs from queue"""
        while len(self.active_jobs) < self.max_concurrent_jobs:
            job = self._get_next_job()
            
            if job is None:
                break
            
            # Start processing job
            job.status = BatchStatus.PROCESSING
            job.started_at = datetime.now()
            self.active_jobs[job.id] = job
            
            # Create task
            task = asyncio.create_task(self._process_job(job))
            self.job_tasks[job.id] = task
    
    def _get_next_job(self) -> Optional[BatchJob]:
        """Get next job from highest priority queue"""
        for queue in [self.urgent_queue, self.high_queue, self.normal_queue, self.low_queue]:
            if len(queue) > 0:
                return queue.popleft()
        return None
    
    async def _process_job(self, job: BatchJob):
        """Process a single batch job"""
        try:
            # Process images in batches
            for i in range(0, len(job.images), self.max_concurrent_images):
                batch = job.images[i:i + self.max_concurrent_images]
                
                # Process batch concurrently
                tasks = [self._process_image(image, job) for image in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update progress
                for j, result in enumerate(results):
                    if isinstance(result, Exception):
                        job.failed_images += 1
                        job.errors.append({
                            "image": batch[j],
                            "error": str(result),
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
                        job.processed_images += 1
                        job.results.append(result)
                
                job.progress = (job.processed_images + job.failed_images) / job.total_images * 100
            
            # Mark as completed
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.now()
            self.total_jobs_processed += 1
            self.total_images_processed += job.processed_images
            
        except Exception as e:
            job.status = BatchStatus.FAILED
            job.errors.append({
                "type": "job_failure",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        finally:
            # Remove from active jobs
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            if job.id in self.job_tasks:
                del self.job_tasks[job.id]
            
            # Continue processing queue
            await self._process_queue()
    
    async def _process_image(self, image_path: str, job: BatchJob) -> Dict[str, Any]:
        """Process a single image (placeholder - integrate with actual API)"""
        # Simulate processing
        await asyncio.sleep(0.1)
        
        # In production, this would call the actual API
        # from api.routes import detect_defects, get_explanations
        # result = await detect_defects(image_path)
        # explanation = await get_explanations(result, job.xai_method)
        
        return {
            "image": image_path,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "detections": [],
            "explanations": {}
        }


# Global batch processor instance
batch_processor = BatchProcessor()
