import { useParams } from "react-router-dom";
import { useSessions } from "../../hooks/useSessions";
import { useCarTracks } from "../../hooks/useCarTracks";
import { Badge, Skeleton } from "../ui";
import { API_BASE_URL } from "../../lib/constants";
import type { SessionRecord, TrackStatsRecord } from "../../lib/types";
import "./SessionHeader.css";

function formatLapTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds - mins * 60;
  return `${mins}:${secs.toFixed(3).padStart(6, "0")}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

type BadgeVariant = "info" | "success" | "warning" | "error" | "neutral";

function stateToVariant(state: string): BadgeVariant {
  switch (state) {
    case "analyzed":
      return "info";
    case "engineered":
      return "success";
    default:
      return "neutral";
  }
}

export function SessionHeader() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { sessions, isLoading: sessionsLoading } = useSessions();
  const session: SessionRecord | undefined = sessions?.find(
    (s) => s.session_id === sessionId,
  );
  const { data: carTracksData, isLoading: carTracksLoading } = useCarTracks(
    session?.car,
  );

  const isLoading = sessionsLoading || (session != null && carTracksLoading);

  if (isLoading) {
    return (
      <div className="ace-session-header" data-testid="session-header">
        <Skeleton variant="rect" width="200px" height="48px" />
        <Skeleton variant="rect" width="200px" height="48px" />
        <Skeleton variant="rect" width="300px" height="48px" />
      </div>
    );
  }

  if (!session) return null;

  const carDisplayName = carTracksData?.car_display_name ?? session.car;
  const carBrand = carTracksData?.car_brand;
  const carClass = carTracksData?.car_class;
  const carBadgeUrl = carTracksData?.badge_url;

  const matchingTrack: TrackStatsRecord | undefined = carTracksData?.tracks.find(
    (t) => t.track_name === session.track && t.track_config === session.track_config,
  );
  const trackDisplayName = matchingTrack?.display_name
    ? matchingTrack.display_name +
      (session.track_config ? ` - ${session.track_config}` : "")
    : session.track + (session.track_config ? ` - ${session.track_config}` : "");
  const trackPreviewUrl = matchingTrack?.preview_url ?? null;

  return (
    <div className="ace-session-header" data-testid="session-header">
      <div className="ace-session-header__car">
        <div className="ace-session-header__badge">
          {carBadgeUrl ? (
            <img
              src={`${API_BASE_URL}${carBadgeUrl}`}
              alt={carDisplayName}
              className="ace-session-header__badge-img"
              onError={(e) => {
                e.currentTarget.style.display = "none";
                e.currentTarget.nextElementSibling?.classList.remove("ace-hidden");
              }}
            />
          ) : null}
          <i
            className={`fa-solid fa-car ace-session-header__fallback${carBadgeUrl ? " ace-hidden" : ""}`}
            data-testid="car-fallback-icon"
          />
        </div>
        <div className="ace-session-header__name-group">
          <div className="ace-session-header__name">{carDisplayName}</div>
          {(carBrand || carClass) && (
            <div className="ace-session-header__subtitle">
              {[carBrand, carClass].filter(Boolean).join(" · ")}
            </div>
          )}
        </div>
      </div>

      <div className="ace-session-header__track">
        <div className="ace-session-header__badge ace-session-header__badge--track">
          {trackPreviewUrl ? (
            <img
              src={`${API_BASE_URL}${trackPreviewUrl}`}
              alt={trackDisplayName}
              className="ace-session-header__badge-img ace-session-header__badge-img--track"
              onError={(e) => {
                e.currentTarget.style.display = "none";
                e.currentTarget.nextElementSibling?.classList.remove("ace-hidden");
              }}
            />
          ) : null}
          <i
            className={`fa-solid fa-road ace-session-header__fallback${trackPreviewUrl ? " ace-hidden" : ""}`}
            data-testid="track-fallback-icon"
          />
        </div>
        <div className="ace-session-header__name">{trackDisplayName}</div>
      </div>

      <div className="ace-session-header__stats">
        <div className="ace-session-header__stat">
          <span className="ace-session-header__stat-label">Date</span>
          <span className="ace-session-header__stat-value">
            {formatDate(session.session_date)}
          </span>
        </div>
        <div className="ace-session-header__stat">
          <span className="ace-session-header__stat-label">Laps</span>
          <span className="ace-session-header__stat-value ace-mono">
            {session.lap_count}
          </span>
        </div>
        <div className="ace-session-header__stat">
          <span className="ace-session-header__stat-label">Best</span>
          <span className="ace-session-header__stat-value ace-mono">
            {session.best_lap_time != null
              ? formatLapTime(session.best_lap_time)
              : "\u2014"}
          </span>
        </div>
        <Badge variant={stateToVariant(session.state)}>{session.state}</Badge>
      </div>
    </div>
  );
}
