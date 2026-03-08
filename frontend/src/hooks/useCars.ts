import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiDelete } from "../lib/api";
import type { CarListResponse, CarStatusRecord } from "../lib/types";

export function useCars(): {
  cars: CarStatusRecord[];
  isLoading: boolean;
  error: Error | null;
  invalidateCar: (carName: string) => void;
  invalidateAll: () => void;
  isInvalidating: boolean;
} {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<CarListResponse>({
    queryKey: ["cars"],
    queryFn: () => apiGet<CarListResponse>("/cars"),
    staleTime: 60_000,
  });

  const invalidateCarMutation = useMutation({
    mutationFn: (carName: string) => apiDelete(`/cars/${carName}/cache`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cars"] });
    },
  });

  const invalidateAllMutation = useMutation({
    mutationFn: () => apiDelete("/cars/cache"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cars"] });
    },
  });

  return {
    cars: data?.cars ?? [],
    isLoading,
    error: error as Error | null,
    invalidateCar: invalidateCarMutation.mutate,
    invalidateAll: () => invalidateAllMutation.mutate(),
    isInvalidating: invalidateCarMutation.isPending || invalidateAllMutation.isPending,
  };
}
