"""Job status endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from api.jobs.models import Job
from api.deps import get_job_manager
from api.jobs.manager import JobManager

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, manager: JobManager = Depends(get_job_manager)) -> Job:
    job = manager.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job
