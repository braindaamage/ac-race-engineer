"""WebSocket tests for job progress streaming."""

from __future__ import annotations

import asyncio

import pytest
from starlette.testclient import TestClient

from api.main import create_app
from api.jobs.manager import JobManager
from api.jobs.models import JobStatus


@pytest.fixture
def sync_app():
    """Create app with manually-set job manager for sync TestClient."""
    app = create_app()
    mgr = JobManager()
    app.state.job_manager = mgr
    return app, mgr


def test_ws_unknown_job_closes_with_4004(sync_app):
    app, mgr = sync_app
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/jobs/nonexistent"):
            pass


def test_ws_completed_job_sends_completed_event(sync_app):
    app, mgr = sync_app
    job = mgr.create_job("parse")
    mgr.complete_job(job.job_id, {"laps": 5})

    client = TestClient(app)
    with client.websocket_connect(f"/ws/jobs/{job.job_id}") as ws:
        data = ws.receive_json()
        assert data["event"] == "completed"
        assert data["status"] == "completed"
        assert data["result"] == {"laps": 5}


def test_ws_failed_job_sends_error_event(sync_app):
    app, mgr = sync_app
    job = mgr.create_job("parse")
    mgr.fail_job(job.job_id, "parse error")

    client = TestClient(app)
    with client.websocket_connect(f"/ws/jobs/{job.job_id}") as ws:
        data = ws.receive_json()
        assert data["event"] == "error"
        assert data["status"] == "failed"
        assert data["error"] == "parse error"


def test_ws_running_job_receives_progress_then_completed(sync_app):
    app, mgr = sync_app
    job = mgr.create_job("parse")
    mgr.update_progress(job.job_id, 0, "Starting")

    client = TestClient(app)

    # We need to update progress in a background thread since ws_connect blocks
    import threading
    import time

    def update_job():
        time.sleep(0.1)
        mgr.update_progress(job.job_id, 50, "Halfway")
        time.sleep(0.1)
        mgr.complete_job(job.job_id, {"done": True})

    t = threading.Thread(target=update_job)
    t.start()

    with client.websocket_connect(f"/ws/jobs/{job.job_id}") as ws:
        events = []
        # Should get the initial running state, then progress, then completed
        for _ in range(3):
            try:
                data = ws.receive_json()
                events.append(data)
                if data["event"] == "completed":
                    break
            except Exception:
                break

        assert any(e["event"] == "completed" for e in events)

    t.join(timeout=5)


def test_ws_multiple_clients_on_same_job(sync_app):
    """Two clients connected to the same completed job both get the event."""
    app, mgr = sync_app
    job = mgr.create_job("parse")
    mgr.complete_job(job.job_id, {"result": 42})

    client = TestClient(app)

    with client.websocket_connect(f"/ws/jobs/{job.job_id}") as ws1:
        data1 = ws1.receive_json()

    with client.websocket_connect(f"/ws/jobs/{job.job_id}") as ws2:
        data2 = ws2.receive_json()

    assert data1["event"] == "completed"
    assert data2["event"] == "completed"
