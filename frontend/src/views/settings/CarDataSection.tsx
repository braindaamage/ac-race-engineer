import { Card, Button, Skeleton } from "../../components/ui";
import { useCars } from "../../hooks/useCars";
import type { CarStatusRecord } from "../../lib/types";
import "./CarDataSection.css";

function formatDate(iso: string | null): string {
  if (!iso) return "\u2014";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return "\u2014";
  }
}

function tierLabel(tier: number | null): string {
  if (tier === 1) return "Tier 1";
  if (tier === 2) return "Tier 2";
  return "";
}

export function CarDataSection() {
  const { cars, isLoading, error, invalidateCar, invalidateAll, isInvalidating } =
    useCars();

  const hasCachedCars = cars.some((c) => c.status === "resolved");

  if (isLoading) {
    return (
      <Card title="Car Data">
        <Skeleton height="120px" />
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Car Data">
        <div className="ace-car-data__error">
          Assetto Corsa installation path is not configured. Set it in the
          Assetto Corsa section above to view car data.
        </div>
      </Card>
    );
  }

  if (cars.length === 0) {
    return (
      <Card title="Car Data">
        <div className="ace-car-data__empty">
          No cars found. Check your AC installation path.
        </div>
      </Card>
    );
  }

  return (
    <Card title="Car Data">
      <div className="ace-car-data">
        <div className="ace-car-data__header">
          <span />
          <Button
            variant="secondary"
            size="sm"
            onClick={invalidateAll}
            disabled={!hasCachedCars || isInvalidating}
          >
            Invalidate All
          </Button>
        </div>
        <div className="ace-car-data__scroll">
          <table className="ace-car-data__table">
            <thead>
              <tr>
                <th>Car</th>
                <th>Status</th>
                <th>Defaults</th>
                <th>Last Resolved</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {cars.map((car: CarStatusRecord) => (
                <tr key={car.car_name}>
                  <td className="ace-car-data__name">{car.car_name}</td>
                  <td>
                    {car.status === "resolved" ? (
                      <span className="ace-car-data__status ace-car-data__status--resolved">
                        {tierLabel(car.tier)}
                      </span>
                    ) : (
                      <span className="ace-car-data__status ace-car-data__status--unresolved">
                        Unresolved
                      </span>
                    )}
                  </td>
                  <td>{car.has_defaults === true ? "Yes" : car.has_defaults === false ? "No" : "\u2014"}</td>
                  <td className="ace-car-data__date">
                    {formatDate(car.resolved_at)}
                  </td>
                  <td className="ace-car-data__actions">
                    {car.status === "resolved" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => invalidateCar(car.car_name)}
                        disabled={isInvalidating}
                      >
                        Invalidate
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Card>
  );
}
