import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { SessionLayout } from "./components/layout/SessionLayout";
import { GarageView } from "./views/garage";
import { CarTracksView } from "./views/tracks";
import { SessionsView } from "./views/sessions";
import { AnalysisView } from "./views/analysis";
import { CompareView } from "./views/compare";
import { EngineerView } from "./views/engineer";
import { SettingsView } from "./views/settings";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/garage" replace /> },
      { path: "garage", element: <GarageView /> },
      { path: "garage/:carId/tracks", element: <CarTracksView /> },
      { path: "garage/:carId/tracks/:trackId/sessions", element: <SessionsView /> },
      {
        path: "session/:sessionId",
        element: <SessionLayout />,
        children: [
          { index: true, element: <Navigate to="laps" replace /> },
          { path: "laps", element: <AnalysisView /> },
          { path: "setup", element: <CompareView /> },
          { path: "engineer", element: <EngineerView /> },
        ],
      },
      { path: "settings", element: <SettingsView /> },
      { path: "*", element: <Navigate to="/garage" replace /> },
    ],
  },
]);
