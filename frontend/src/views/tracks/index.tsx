import { useParams, useNavigate } from "react-router-dom";
import { useCarTracks } from "../../hooks/useCarTracks";
import { EmptyState, Skeleton } from "../../components/ui";
import { API_BASE_URL } from "../../lib/constants";
import "./CarTracksView.css";

function formatLapTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds - mins * 60;
  return `${mins}:${secs.toFixed(3).padStart(6, "0")}`;
}

function formatLength(meters: number): string {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)}km`;
  }
  return `${Math.round(meters)}m`;
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60_000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export function CarTracksView() {
  const { carId } = useParams<{ carId: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useCarTracks(carId);

  return (
    <div className="ace-tracks" data-testid="tracks-view">
      {isLoading && (
        <>
          <Skeleton variant="rect" height="80px" />
          <div className="ace-tracks-grid">
            <Skeleton variant="rect" height="200px" />
            <Skeleton variant="rect" height="200px" />
          </div>
        </>
      )}

      {!isLoading && error && (
        <EmptyState
          icon={<i className="fa-solid fa-triangle-exclamation" />}
          title="Failed to load tracks"
          description={error.message}
        />
      )}

      {!isLoading && !error && data && (
        <>
          <div className="ace-car-header">
            <div className="ace-car-header__badge">
              {data.badge_url ? (
                <img
                  src={`${API_BASE_URL}${data.badge_url}`}
                  alt={data.car_display_name}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                    e.currentTarget.nextElementSibling?.classList.remove("ace-hidden");
                  }}
                />
              ) : null}
              <i className={`fa-solid fa-car ace-car-header__fallback${data.badge_url ? " ace-hidden" : ""}`} />
            </div>
            <div className="ace-car-header__info">
              <h1 className="ace-car-header__name">{data.car_display_name}</h1>
              {(data.car_brand || data.car_class) && (
                <div className="ace-car-header__subtitle">
                  {[data.car_brand, data.car_class].filter(Boolean).join(" · ")}
                </div>
              )}
              <div className="ace-car-header__stats">
                <span>
                  <span className="ace-mono">{data.track_count}</span> tracks
                </span>
                <span>
                  <span className="ace-mono">{data.session_count}</span> sessions
                </span>
                {data.last_session_date && (
                  <span className="ace-mono">
                    {formatRelativeTime(data.last_session_date)}
                  </span>
                )}
              </div>
            </div>
          </div>

          {data.tracks.length === 0 && (
            <EmptyState
              icon={<i className="fa-solid fa-road" />}
              title="No tracks yet"
              description="Tracks driven with this car will appear here."
            />
          )}

          {data.tracks.length > 0 && (
            <div className="ace-tracks-grid">
              {data.tracks.map((track) => {
                const configSuffix = track.track_config
                  ? ` - ${track.track_config}`
                  : "";
                return (
                  <div
                    key={`${track.track_name}-${track.track_config}`}
                    className="ace-track-card"
                    onClick={() => {
                      const base = `/garage/${encodeURIComponent(carId!)}/tracks/${encodeURIComponent(track.track_name)}/sessions`;
                      const qs = track.track_config
                        ? `?config=${encodeURIComponent(track.track_config)}`
                        : "";
                      navigate(`${base}${qs}`);
                    }}
                    data-testid={`track-card-${track.track_name}`}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        const base = `/garage/${encodeURIComponent(carId!)}/tracks/${encodeURIComponent(track.track_name)}/sessions`;
                        const qs = track.track_config
                          ? `?config=${encodeURIComponent(track.track_config)}`
                          : "";
                        navigate(`${base}${qs}`);
                      }
                    }}
                  >
                    <div className="ace-track-preview">
                      {track.preview_url ? (
                        <img
                          src={`${API_BASE_URL}${track.preview_url}`}
                          alt={track.display_name}
                          onError={(e) => {
                            e.currentTarget.style.display = "none";
                            e.currentTarget.nextElementSibling?.classList.remove("ace-hidden");
                          }}
                        />
                      ) : null}
                      <i
                        className={`fa-solid fa-road ace-track-preview__fallback${track.preview_url ? " ace-hidden" : ""}`}
                      />
                    </div>
                    <div className="ace-track-card__body">
                      <div className="ace-track-card__name">
                        {track.display_name}{configSuffix}
                      </div>
                      {track.country && (
                        <div className="ace-track-card__country">{track.country}</div>
                      )}
                      <div className="ace-track-stats">
                        <span className="ace-track-stats__item">
                          <i className="fa-solid fa-flag-checkered" />
                          <span className="ace-mono">{track.session_count}</span>
                        </span>
                        {track.best_lap_time != null && (
                          <span className="ace-track-stats__item">
                            <i className="fa-solid fa-stopwatch" />
                            <span className="ace-mono">{formatLapTime(track.best_lap_time)}</span>
                          </span>
                        )}
                        {track.length_m != null && (
                          <span className="ace-track-stats__item">
                            <i className="fa-solid fa-ruler" />
                            <span className="ace-mono">{formatLength(track.length_m)}</span>
                          </span>
                        )}
                      </div>
                      <div className="ace-track-card__time">
                        {formatRelativeTime(track.last_session_date)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
