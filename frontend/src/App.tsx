import { useEffect } from "react";
import { RouterProvider } from "react-router-dom";
import { useTheme } from "./hooks/useTheme";
import { useBackendStatus } from "./hooks/useBackendStatus";
import { useConfig } from "./hooks/useConfig";
import { SplashScreen } from "./components/layout/SplashScreen";
import { OnboardingWizard } from "./components/onboarding/OnboardingWizard";
import { router } from "./router";

export function App() {
  const { status, retry, shutdown } = useBackendStatus();
  const { config, isLoading: configLoading, error: configError } = useConfig();
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

  if (configLoading) {
    return <SplashScreen status="polling" onRetry={retry} />;
  }

  // If config fetch fails or onboarding not completed, show wizard
  if (configError || !config?.onboarding_completed) {
    return (
      <OnboardingWizard
        onComplete={() => {
          // Config will be refetched automatically via TanStack Query invalidation
        }}
      />
    );
  }

  return <RouterProvider router={router} />;
}
