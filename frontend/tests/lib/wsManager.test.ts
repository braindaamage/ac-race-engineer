import { describe, it, expect, beforeEach, vi } from "vitest";
import { useJobStore } from "../../src/store/jobStore";
import { useNotificationStore } from "../../src/store/notificationStore";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: ((event: { wasClean: boolean; code: number }) => void) | null =
    null;
  onerror: (() => void) | null = null;
  readyState = 1;
  closed = false;
  url: string;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.closed = true;
  }
}

vi.stubGlobal("WebSocket", MockWebSocket);

// Dynamic import after mocking WebSocket
const { jobWSManager } = await import("../../src/lib/wsManager");

function getLastWS(): MockWebSocket {
  const ws = MockWebSocket.instances[MockWebSocket.instances.length - 1];
  if (!ws) throw new Error("No WebSocket instance");
  return ws;
}

describe("wsManager", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    useJobStore.setState({ jobProgress: {} });
    useNotificationStore.setState({ notifications: [] });
  });

  it("trackJob opens WebSocket with correct URL", () => {
    jobWSManager.trackJob("job-1");
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(getLastWS().url).toBe("ws://127.0.0.1:57832/ws/jobs/job-1");
  });

  it("progress message updates job store", () => {
    jobWSManager.trackJob("job-2");
    const ws = getLastWS();

    ws.onmessage!({
      data: JSON.stringify({
        event: "progress",
        job_id: "job-2",
        status: "running",
        progress: 50,
        current_step: "Analyzing laps",
        result: null,
        error: null,
      }),
    });

    const job = useJobStore.getState().jobProgress["job-2"];
    expect(job).toBeDefined();
    expect(job!.status).toBe("running");
    expect(job!.progress).toBe(50);
    expect(job!.currentStep).toBe("Analyzing laps");
  });

  it("completed message triggers success notification and closes connection", () => {
    jobWSManager.trackJob("job-3");
    const ws = getLastWS();

    ws.onmessage!({
      data: JSON.stringify({
        event: "completed",
        job_id: "job-3",
        status: "completed",
        progress: 100,
        current_step: null,
        result: { summary: "done" },
        error: null,
      }),
    });

    const notifications = useNotificationStore.getState().notifications;
    expect(notifications).toHaveLength(1);
    expect(notifications[0]!.type).toBe("success");
    expect(notifications[0]!.message).toContain("job-3");
    expect(ws.closed).toBe(true);
  });

  it("failed message triggers error notification", () => {
    jobWSManager.trackJob("job-4");
    const ws = getLastWS();

    ws.onmessage!({
      data: JSON.stringify({
        event: "error",
        job_id: "job-4",
        status: "failed",
        progress: 30,
        current_step: null,
        result: null,
        error: "Something went wrong",
      }),
    });

    const notifications = useNotificationStore.getState().notifications;
    expect(notifications).toHaveLength(1);
    expect(notifications[0]!.type).toBe("error");
    expect(notifications[0]!.message).toBe("Something went wrong");
    expect(ws.closed).toBe(true);
  });
});
