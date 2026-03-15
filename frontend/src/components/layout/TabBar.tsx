import { NavLink, useLocation, useParams } from "react-router-dom";
import "./TabBar.css";

interface TabItem {
  label: string;
  to: string;
  disabled?: boolean;
}

export function TabBar() {
  const location = useLocation();
  const params = useParams<{
    carId?: string;
    trackId?: string;
    sessionId?: string;
  }>();

  const isSessionDetail = location.pathname.startsWith("/session/") && params.sessionId;

  const tabs: TabItem[] = isSessionDetail
    ? getSessionTabs(params.sessionId!)
    : getGlobalTabs(params.carId, params.trackId);

  return (
    <nav className="ace-tabbar" aria-label="Navigation tabs">
      <div className="ace-tabbar__list">
        {tabs.map((tab) =>
          tab.disabled ? (
            <span
              key={tab.label}
              className="ace-tabbar__tab ace-tabbar__tab--disabled"
            >
              {tab.label}
            </span>
          ) : (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.to === "/garage" || tab.to === "/settings"}
              className={({ isActive }) =>
                `ace-tabbar__tab${isActive ? " ace-tabbar__tab--active" : ""}`
              }
            >
              {tab.label}
            </NavLink>
          ),
        )}
      </div>
    </nav>
  );
}

function getGlobalTabs(carId?: string, trackId?: string): TabItem[] {
  return [
    { label: "Garage Home", to: "/garage" },
    {
      label: "Tracks",
      to: carId ? `/garage/${encodeURIComponent(carId)}/tracks` : "#",
      disabled: !carId,
    },
    {
      label: "Sessions",
      to:
        carId && trackId
          ? `/garage/${encodeURIComponent(carId)}/tracks/${encodeURIComponent(trackId)}/sessions`
          : "#",
      disabled: !carId || !trackId,
    },
    { label: "Settings", to: "/settings" },
  ];
}

function getSessionTabs(sessionId: string): TabItem[] {
  const base = `/session/${sessionId}`;
  return [
    { label: "Lap Analysis", to: `${base}/laps` },
    { label: "Setup Compare", to: `${base}/setup` },
    { label: "Engineer", to: `${base}/engineer` },
  ];
}
