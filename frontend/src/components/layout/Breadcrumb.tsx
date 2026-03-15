import { Link, useLocation, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { formatCarTrack } from "../../views/sessions/utils";
import type { SessionListResponse } from "../../lib/types";
import "./Breadcrumb.css";

interface BreadcrumbSegment {
  label: string;
  to: string;
  isCurrent: boolean;
  isIcon?: boolean;
}

export function Breadcrumb() {
  const location = useLocation();
  const params = useParams<{
    carId?: string;
    trackId?: string;
    sessionId?: string;
  }>();
  const queryClient = useQueryClient();

  const segments = buildSegments(location.pathname, params, queryClient);

  if (segments.length === 0) return null;

  return (
    <nav className="ace-breadcrumb" aria-label="Breadcrumb">
      {segments.map((segment, index) => (
        <span key={segment.to} className="ace-breadcrumb__item">
          {index > 0 && (
            <i className="fa-solid fa-chevron-right ace-breadcrumb__separator" />
          )}
          {segment.isCurrent ? (
            <span className="ace-breadcrumb__current">
              {segment.isIcon ? (
                <i className="fa-solid fa-house" />
              ) : (
                segment.label
              )}
            </span>
          ) : (
            <Link to={segment.to} className="ace-breadcrumb__link">
              {segment.isIcon ? (
                <i className="fa-solid fa-house" />
              ) : (
                segment.label
              )}
            </Link>
          )}
        </span>
      ))}
    </nav>
  );
}

function buildSegments(
  pathname: string,
  params: { carId?: string; trackId?: string; sessionId?: string },
  queryClient: ReturnType<typeof useQueryClient>,
): BreadcrumbSegment[] {
  const segments: BreadcrumbSegment[] = [];

  // Settings route
  if (pathname.startsWith("/settings")) {
    segments.push({ label: "Home", to: "/garage", isCurrent: false, isIcon: true });
    segments.push({ label: "Settings", to: "/settings", isCurrent: true });
    return segments;
  }

  // Session detail routes
  if (pathname.startsWith("/session/") && params.sessionId) {
    const sessionData = resolveSessionData(params.sessionId, queryClient);

    segments.push({ label: "Home", to: "/garage", isCurrent: false, isIcon: true });

    if (sessionData) {
      segments.push({
        label: formatCarTrack(sessionData.car),
        to: `/garage/${encodeURIComponent(sessionData.car)}/tracks`,
        isCurrent: false,
      });
      segments.push({
        label: formatCarTrack(sessionData.track),
        to: `/garage/${encodeURIComponent(sessionData.car)}/tracks/${encodeURIComponent(sessionData.track)}/sessions`,
        isCurrent: false,
      });
      const dateLabel = new Date(sessionData.session_date).toLocaleDateString();
      segments.push({
        label: dateLabel,
        to: `/session/${params.sessionId}`,
        isCurrent: true,
      });
    } else {
      segments.push({
        label: params.sessionId,
        to: `/session/${params.sessionId}`,
        isCurrent: true,
      });
    }
    return segments;
  }

  // Garage hierarchy
  segments.push({
    label: "Home",
    to: "/garage",
    isCurrent: !params.carId && pathname === "/garage",
    isIcon: true,
  });

  if (params.carId) {
    const isTracksCurrent = !params.trackId;
    segments.push({
      label: formatCarTrack(params.carId),
      to: `/garage/${encodeURIComponent(params.carId)}/tracks`,
      isCurrent: isTracksCurrent,
    });

    if (params.trackId) {
      segments.push({
        label: formatCarTrack(params.trackId),
        to: `/garage/${encodeURIComponent(params.carId)}/tracks/${encodeURIComponent(params.trackId)}/sessions`,
        isCurrent: true,
      });
    }
  }

  return segments;
}

function resolveSessionData(
  sessionId: string,
  queryClient: ReturnType<typeof useQueryClient>,
) {
  const sessionsData = queryClient.getQueryData<SessionListResponse>(["sessions"]);
  if (!sessionsData) return null;
  return sessionsData.sessions.find((s) => s.session_id === sessionId) ?? null;
}
