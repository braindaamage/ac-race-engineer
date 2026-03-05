import { useEffect } from "react";
import { useTheme } from "./hooks/useTheme";
import { useBackendStatus } from "./hooks/useBackendStatus";
import { SplashScreen } from "./components/layout/SplashScreen";
import { AppShell } from "./components/layout/AppShell";

export function App() {
  const { status, retry, shutdown } = useBackendStatus();
  useTheme();

  useEffect(() => {
    let cleanup: (() => void) | undefined;

    const setupCloseHandler = async () => {
      if (typeof window !== "undefined" && "__TAURI__" in window) {
        try {
          const { getCurrentWindow } = await import("@tauri-apps/api/window");
          const unlisten = await getCurrentWindow().onCloseRequested(
            async (event) => {
              event.preventDefault();
              await shutdown();
              await getCurrentWindow().destroy();
            },
          );
          cleanup = unlisten;
        } catch {
          // Non-Tauri environment
        }
      }
    };

    setupCloseHandler();

    return () => {
      cleanup?.();
    };
  }, [shutdown]);

  if (status === "polling" || status === "error") {
    return <SplashScreen status={status} onRetry={retry} />;
  }

  return <AppShell />;
}
