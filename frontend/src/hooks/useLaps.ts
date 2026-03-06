import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type {
  LapListResponse,
  LapDetailResponse,
  LapTelemetryResponse,
} from "../lib/types";

export function useLaps(sessionId: string | null) {
  return useQuery<LapListResponse>({
    queryKey: ["laps", sessionId],
    queryFn: () => apiGet<LapListResponse>(`/sessions/${sessionId}/laps`),
    enabled: !!sessionId,
    staleTime: Infinity,
  });
}

export function useLapDetail(
  sessionId: string | null,
  lapNumber: number | null,
  enabled: boolean = true,
) {
  return useQuery<LapDetailResponse>({
    queryKey: ["lap-detail", sessionId, lapNumber],
    queryFn: () =>
      apiGet<LapDetailResponse>(
        `/sessions/${sessionId}/laps/${lapNumber}`,
      ),
    enabled: enabled && !!sessionId && lapNumber != null,
    staleTime: Infinity,
  });
}

export function useLapTelemetry(
  sessionId: string | null,
  lapNumber: number | null,
  enabled: boolean = true,
) {
  return useQuery<LapTelemetryResponse>({
    queryKey: ["telemetry", sessionId, lapNumber],
    queryFn: () =>
      apiGet<LapTelemetryResponse>(
        `/sessions/${sessionId}/laps/${lapNumber}/telemetry`,
      ),
    enabled: enabled && !!sessionId && lapNumber != null,
    staleTime: Infinity,
  });
}
