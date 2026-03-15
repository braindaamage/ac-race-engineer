import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type { CarStatsListResponse, CarStatsRecord } from "../lib/types";

export function useCarStats(): {
  cars: CarStatsRecord[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
} {
  const { data, isLoading, error, refetch } = useQuery<CarStatsListResponse>({
    queryKey: ["car-stats"],
    queryFn: () => apiGet<CarStatsListResponse>("/sessions/grouped/cars"),
    staleTime: 60_000,
  });

  return {
    cars: data?.cars ?? [],
    isLoading,
    error: error as Error | null,
    refetch,
  };
}
