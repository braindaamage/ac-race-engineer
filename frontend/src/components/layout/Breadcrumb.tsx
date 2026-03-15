import { Link, useLocation, useParams, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { formatCarTrack } from "../../views/sessions/utils";
import type {
  CarStatsListResponse,
  SessionListResponse,
  TrackStatsListResponse,
} from "../../lib/types";
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
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const segments = buildSegments(
    location.pathname,
    params,
    searchParams,
    queryClient,
  );

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

function resolveCarDisplayName(
  carId: string,
  queryClient: ReturnType<typeof useQueryClient>,
): string | null {
  // Try car-stats cache
  const carStats = queryClient.getQueryData<CarStatsListResponse>(["car-stats"]);
  if (carStats) {
    const found = carStats.cars.find((c) => c.car_name === carId);
    if (found) return found.display_name;
  }
  // Try car-tracks cache
  const carTracks = queryClient.getQueryData<TrackStatsListResponse>([
    "car-tracks",
    carId,
  ]);
  if (carTracks) return carTracks.car_display_name;
  return null;
}

function resolveTrackDisplayName(
  carId: string,
  trackId: string,
  trackConfig: string,
  queryClient: ReturnType<typeof useQueryClient>,
): string | null {
  const carTracks = queryClient.getQueryData<TrackStatsListResponse>([
    "car-tracks",
    carId,
  ]);
  if (!carTracks) return null;
  const found = carTracks.tracks.find(
    (t) => t.track_name === trackId && t.track_config === trackConfig,
  );
  if (!found) return null;
  const suffix = found.track_config ? ` - ${found.track_config}` : "";
  return `${found.display_name}${suffix}`;
}

function buildSegments(
  pathname: string,
  params: { carId?: string; trackId?: string; sessionId?: string },
  searchParams: URLSearchParams,
  queryClient: ReturnType<typeof useQueryClient>,
): BreadcrumbSegment[] {
  const segments: BreadcrumbSegment[] = [];
  const config = searchParams.get("config") ?? "";

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
      const carDisplayName =
        resolveCarDisplayName(sessionData.car, queryClient) ??
        formatCarTrack(sessionData.car);
      segments.push({
        label: carDisplayName,
        to: `/garage/${encodeURIComponent(sessionData.car)}/tracks`,
        isCurrent: false,
      });
      const trackConfig = sessionData.track_config ?? "";
      const trackDisplayName =
        resolveTrackDisplayName(
          sessionData.car,
          sessionData.track,
          trackConfig,
          queryClient,
        ) ?? formatCarTrack(sessionData.track);
      const sessionsUrl = `/garage/${encodeURIComponent(sessionData.car)}/tracks/${encodeURIComponent(sessionData.track)}/sessions${trackConfig ? `?config=${encodeURIComponent(trackConfig)}` : ""}`;
      segments.push({
        label: trackDisplayName,
        to: sessionsUrl,
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
    const carDisplayName =
      resolveCarDisplayName(params.carId, queryClient) ??
      formatCarTrack(params.carId);
    segments.push({
      label: carDisplayName,
      to: `/garage/${encodeURIComponent(params.carId)}/tracks`,
      isCurrent: isTracksCurrent,
    });

    if (params.trackId) {
      const trackDisplayName =
        resolveTrackDisplayName(params.carId, params.trackId, config, queryClient) ??
        formatCarTrack(params.trackId);
      const sessionsUrl = `/garage/${encodeURIComponent(params.carId)}/tracks/${encodeURIComponent(params.trackId)}/sessions${config ? `?config=${encodeURIComponent(config)}` : ""}`;
      segments.push({
        label: trackDisplayName,
        to: sessionsUrl,
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
