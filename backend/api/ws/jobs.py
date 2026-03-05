"""WebSocket handler for streaming job progress events."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from api.jobs.manager import JobManager
from api.jobs.models import JobEvent, JobStatus

router = APIRouter()


@router.websocket("/ws/jobs/{job_id}")
async def ws_job_progress(websocket: WebSocket, job_id: str) -> None:
    manager: JobManager = websocket.app.state.job_manager

    job = manager.get_job(job_id)
    if job is None:
        await websocket.close(code=4004, reason="Job not found")
        return

    await websocket.accept()

    try:
        # If job is already in a terminal state, send final event and close
        if job.status in (JobStatus.completed, JobStatus.failed):
            event = _make_event(job)
            await websocket.send_json(event.model_dump(mode="json"))
            await websocket.close(code=1000)
            return

        event_obj = manager.get_event(job_id)
        if event_obj is None:
            await websocket.close(code=4004, reason="Job not found")
            return

        last_progress = -1
        last_step: str | None = ""
        last_status = job.status

        while True:
            # Wait for a state change (with timeout to handle edge cases)
            try:
                await asyncio.wait_for(event_obj.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                # Re-check state even on timeout
                pass

            event_obj.clear()

            job = manager.get_job(job_id)
            if job is None:
                await websocket.close(code=4004, reason="Job not found")
                return

            # Only send event if state actually changed
            if (
                job.progress != last_progress
                or job.current_step != last_step
                or job.status != last_status
            ):
                last_progress = job.progress
                last_step = job.current_step
                last_status = job.status

                event = _make_event(job)
                await websocket.send_json(event.model_dump(mode="json"))

                # Terminal state → close connection
                if job.status in (JobStatus.completed, JobStatus.failed):
                    await websocket.close(code=1000)
                    return

    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass


def _make_event(job) -> JobEvent:  # type: ignore[no-untyped-def]
    """Build a JobEvent from the current job state."""
    if job.status == JobStatus.completed:
        event_type = "completed"
    elif job.status == JobStatus.failed:
        event_type = "error"
    else:
        event_type = "progress"

    return JobEvent(
        event=event_type,
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        current_step=job.current_step,
        result=job.result if job.status == JobStatus.completed else None,
        error=job.error if job.status == JobStatus.failed else None,
    )
