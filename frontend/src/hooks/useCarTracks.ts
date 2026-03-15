import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type { TrackStatsListResponse } from "../lib/types";

export function useCarTracks(carId: string | undefined): {
  data: TrackStatsListResponse | undefined;
  isLoading: boolean;
  error: Error | null;
} {
  const { data, isLoading, error } = useQuery<TrackStatsListResponse>({
    queryKey: ["car-tracks", carId],
    queryFn: () =>
      apiGet<TrackStatsListResponse>(
        `/sessions/grouped/cars/${encodeURIComponent(carId!)}/tracks`,
      ),
    staleTime: 60_000,
    enabled: !!carId,
  });

  return {
    data,
    isLoading,
    error: error as Error | null,
  };
}
