import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCarStats } from "../../hooks/useCarStats";
import { EmptyState, Skeleton } from "../../components/ui";
import { API_BASE_URL } from "../../lib/constants";
import "./GarageView.css";

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

export function GarageView() {
  const navigate = useNavigate();
  const { cars, isLoading, error } = useCarStats();
  const [search, setSearch] = useState("");

  const filtered = cars.filter((car) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      car.display_name.toLowerCase().includes(q) ||
      car.brand.toLowerCase().includes(q) ||
      car.car_class.toLowerCase().includes(q)
    );
  });

  return (
    <div className="ace-garage" data-testid="garage-view">
      <div className="ace-garage__header">
        <h1>My Garage</h1>
      </div>

      {isLoading && (
        <div className="ace-garage-grid">
          <Skeleton variant="rect" height="180px" />
          <Skeleton variant="rect" height="180px" />
          <Skeleton variant="rect" height="180px" />
        </div>
      )}

      {!isLoading && error && (
        <EmptyState
          icon={<i className="fa-solid fa-triangle-exclamation" />}
          title="Failed to load garage"
          description={error.message}
        />
      )}

      {!isLoading && !error && cars.length === 0 && (
        <EmptyState
          icon={<i className="fa-solid fa-car" />}
          title="My Garage"
          description="Your cars with session data will appear here."
        />
      )}

      {!isLoading && !error && cars.length > 0 && (
        <>
          <div className="ace-garage-search">
            <i className="fa-solid fa-magnifying-glass ace-garage-search__icon" />
            <input
              type="text"
              className="ace-garage-search__input"
              placeholder="Search cars..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              data-testid="garage-search"
            />
          </div>

          {filtered.length === 0 && (
            <EmptyState
              icon={<i className="fa-solid fa-magnifying-glass" />}
              title="No cars match your search"
              description="Try a different search term."
            />
          )}

          {filtered.length > 0 && (
            <div className="ace-garage-grid">
              {filtered.map((car) => (
                <div
                  key={car.car_name}
                  className="ace-car-card"
                  onClick={() => navigate(`/garage/${encodeURIComponent(car.car_name)}/tracks`)}
                  data-testid={`car-card-${car.car_name}`}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      navigate(`/garage/${encodeURIComponent(car.car_name)}/tracks`);
                    }
                  }}
                >
                  <div className="ace-car-badge">
                    {car.badge_url ? (
                      <img
                        src={`${API_BASE_URL}${car.badge_url}`}
                        alt={car.display_name}
                        onError={(e) => {
                          const target = e.currentTarget;
                          target.style.display = "none";
                          target.nextElementSibling?.classList.remove("ace-hidden");
                        }}
                      />
                    ) : null}
                    <i
                      className={`fa-solid fa-car ace-car-badge__fallback${car.badge_url ? " ace-hidden" : ""}`}
                    />
                  </div>
                  <div className="ace-car-card__body">
                    <div className="ace-car-card__name">{car.display_name}</div>
                    {(car.brand || car.car_class) && (
                      <div className="ace-car-card__subtitle">
                        {[car.brand, car.car_class].filter(Boolean).join(" · ")}
                      </div>
                    )}
                    <div className="ace-garage-stats">
                      <span className="ace-garage-stats__item">
                        <i className="fa-solid fa-road" />
                        <span className="ace-garage-stats__value">{car.track_count}</span>
                        tracks
                      </span>
                      <span className="ace-garage-stats__item">
                        <i className="fa-solid fa-flag-checkered" />
                        <span className="ace-garage-stats__value">{car.session_count}</span>
                        sessions
                      </span>
                    </div>
                    <div className="ace-car-card__time">
                      {formatRelativeTime(car.last_session_date)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
