import { useState, useEffect, useRef, useCallback } from "react";
import { API_BASE_URL, HEALTH_POLL_INTERVAL, HEALTH_MAX_RETRIES } from "../lib/constants";
import { apiPost } from "../lib/api";

type BackendStatus = "polling" | "ready" | "error";

interface Child {
  kill: () => Promise<void>;
}

const isTauri = (): boolean =>
  typeof window !== "undefined" && "__TAURI__" in window;

export function useBackendStatus() {
  const [status, setStatus] = useState<BackendStatus>("polling");
  const retriesRef = useRef(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const childRef = useRef<Child | null>(null);

  const startPolling = useCallback(() => {
    setStatus("polling");
    retriesRef.current = 0;

    intervalRef.current = setInterval(async () => {
      try {
        const resp = await fetch(`${API_BASE_URL}/health`);
        if (resp.ok) {
          if (intervalRef.current !== null) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setStatus("ready");
        }
      } catch {
        retriesRef.current += 1;
        if (retriesRef.current >= HEALTH_MAX_RETRIES) {
          if (intervalRef.current !== null) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          setStatus("error");
        }
      }
    }, HEALTH_POLL_INTERVAL);
  }, []);

  const spawnSidecar = useCallback(async () => {
    if (!isTauri()) return;
    try {
      const { Command } = await import("@tauri-apps/plugin-shell");
      const command = Command.sidecar("binaries/api-server", [
        "--port",
        "57832",
      ]);
      const child = await command.spawn();
      childRef.current = child;
    } catch {
      // Sidecar failed to spawn — polling will timeout
    }
  }, []);

  const shutdown = useCallback(async () => {
    try {
      await apiPost("/shutdown");
    } catch {
      // Best effort
    }

    // Wait briefly, then kill
    await new Promise((resolve) => setTimeout(resolve, 2000));

    if (childRef.current) {
      try {
        await childRef.current.kill();
      } catch {
        // Best effort
      }
      childRef.current = null;
    }
  }, []);

  const retry = useCallback(() => {
    spawnSidecar().then(startPolling).catch(startPolling);
  }, [spawnSidecar, startPolling]);

  useEffect(() => {
    spawnSidecar().then(startPolling).catch(startPolling);

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
      }
    };
  }, [spawnSidecar, startPolling]);

  return { status, retry, shutdown };
}
