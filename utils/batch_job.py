"""
NanoBanana Batch Job Management Module

Implements batch generation job management with progress tracking,
async processing, and job persistence for bulk asset generation.
"""

import asyncio
import threading
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Batch job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GenerationRequest(BaseModel):
    """Individual asset generation request"""
    type: str = Field(..., description="Asset type (parchment, enso, sigil, giraffe, kangaroo)")
    count: int = Field(1, ge=1, le=1000, description="Number of assets to generate")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional generation parameters")
    
    @validator('type')
    def validate_asset_type(cls, v):
        valid_types = ['parchment', 'enso', 'sigil', 'giraffe', 'kangaroo']
        if v not in valid_types:
            raise ValueError(f"Invalid asset type. Must be one of: {valid_types}")
        return v


class BatchOptions(BaseModel):
    """Batch generation options"""
    parallel: bool = Field(True, description="Enable parallel processing")
    notify_progress: bool = Field(False, description="Enable progress notifications")
    max_workers: Optional[int] = Field(None, ge=1, le=20, description="Maximum parallel workers")


class BatchRequest(BaseModel):
    """Batch generation request"""
    requests: List[GenerationRequest] = Field(..., min_items=1, max_items=100)
    options: BatchOptions = Field(default_factory=BatchOptions)
    
    @validator('requests')
    def validate_total_count(cls, v):
        total = sum(req.count for req in v)
        if total > 1000:
            raise ValueError("Total count cannot exceed 1000 items per batch")
        return v


class AssetResult(BaseModel):
    """Result of a single asset generation"""
    request_index: int
    asset_index: int
    asset_type: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchJob(BaseModel):
    """Batch generation job"""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    assets: List[AssetResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    cancelled: bool = False
    
    class Config:
        use_enum_values = True


@dataclass
class JobInfo:
    """Runtime job information"""
    job: BatchJob
    task: Optional[asyncio.Task] = None
    cancellation_event: threading.Event = field(default_factory=threading.Event)
    progress_callbacks: List[Callable] = field(default_factory=list)


class JobManager:
    """
    Manages batch generation jobs with in-memory storage.
    
    Provides thread-safe job management with progress tracking,
    cancellation support, and job persistence.
    """
    
    def __init__(self):
        """Initialize job manager"""
        self._jobs: Dict[str, JobInfo] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    def create_job(self, batch_request: BatchRequest) -> BatchJob:
        """
        Create a new batch job.
        
        Args:
            batch_request: Batch generation request
            
        Returns:
            BatchJob instance with unique job_id
        """
        total_items = sum(req.count for req in batch_request.requests)
        
        job = BatchJob(
            total_items=total_items,
            status=JobStatus.PENDING
        )
        
        job_info = JobInfo(job=job)
        
        with self._lock:
            self._jobs[job.job_id] = job_info
        
        return job
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            BatchJob if found, None otherwise
        """
        with self._lock:
            job_info = self._jobs.get(job_id)
            return job_info.job if job_info else None
    
    def update_job_status(self, job_id: str, status: JobStatus, **kwargs):
        """
        Update job status and optional fields.
        
        Args:
            job_id: Job identifier
            status: New status
            **kwargs: Additional fields to update
        """
        with self._lock:
            job_info = self._jobs.get(job_id)
            if job_info:
                job_info.job.status = status
                for key, value in kwargs.items():
                    if hasattr(job_info.job, key):
                        setattr(job_info.job, key, value)
    
    def add_asset_result(self, job_id: str, result: AssetResult):
        """
        Add asset result to job.
        
        Args:
            job_id: Job identifier
            result: Asset generation result
        """
        with self._lock:
            job_info = self._jobs.get(job_id)
            if job_info:
                job_info.job.assets.append(result)
                if result.success:
                    job_info.job.completed_items += 1
                else:
                    job_info.job.failed_items += 1
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was cancelled, False if not found or already completed
        """
        with self._lock:
            job_info = self._jobs.get(job_id)
            if not job_info:
                return False
            
            if job_info.job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False
            
            # Signal cancellation
            job_info.cancellation_event.set()
            job_info.job.cancelled = True
            job_info.job.status = JobStatus.CANCELLED
            job_info.job.completed_at = datetime.utcnow()
            
            # Cancel the asyncio task if it exists
            if job_info.task:
                job_info.task.cancel()
            
            return True
    
    def get_all_jobs(self) -> List[BatchJob]:
        """
        Get all jobs.
        
        Returns:
            List of all BatchJob instances
        """
        with self._lock:
            return [job_info.job for job_info in self._jobs.values()]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Remove old completed jobs.
        
        Args:
            max_age_hours: Maximum age in hours for jobs to keep
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        with self._lock:
            to_remove = []
            for job_id, job_info in self._jobs.items():
                job_time = job_info.job.created_at.timestamp()
                if job_time < cutoff_time and job_info.job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    to_remove.append(job_id)
            
            for job_id in to_remove:
                del self._jobs[job_id]
        
        return len(to_remove)
    
    def get_job_info(self, job_id: str) -> Optional[JobInfo]:
        """
        Get internal job info.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobInfo if found, None otherwise
        """
        with self._lock:
            return self._jobs.get(job_id)


# Global job manager instance
_job_manager: Optional[JobManager] = None
_job_manager_lock = threading.Lock()


def get_job_manager() -> JobManager:
    """
    Get or create global job manager instance (singleton pattern).
    
    Returns:
        Global JobManager instance
    """
    global _job_manager
    if _job_manager is None:
        with _job_manager_lock:
            if _job_manager is None:
                _job_manager = JobManager()
    return _job_manager