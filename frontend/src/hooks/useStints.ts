import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type { StintListResponse, StintComparisonResponse } from "../lib/types";

export function useStints(sessionId: string | null) {
  return useQuery<StintListResponse>({
    queryKey: ["stints", sessionId],
    queryFn: () => apiGet<StintListResponse>(`/sessions/${sessionId}/stints`),
    enabled: !!sessionId,
    staleTime: Infinity,
  });
}

export function useStintComparison(
  sessionId: string | null,
  stintA: number | null,
  stintB: number | null,
) {
  return useQuery<StintComparisonResponse>({
    queryKey: ["stint-comparison", sessionId, stintA, stintB],
    queryFn: () =>
      apiGet<StintComparisonResponse>(
        `/sessions/${sessionId}/compare?stint_a=${stintA}&stint_b=${stintB}`,
      ),
    enabled: !!sessionId && stintA != null && stintB != null,
    staleTime: Infinity,
  });
}
