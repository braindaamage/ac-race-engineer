import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type { TraceResponse } from "../lib/types";

export function useTrace(
  sessionId: string | null,
  traceType: "recommendation" | "message",
  id: string | null,
) {
  const endpoint =
    traceType === "recommendation"
      ? `/sessions/${sessionId}/recommendations/${id}/trace`
      : `/sessions/${sessionId}/messages/${id}/trace`;

  return useQuery<TraceResponse>({
    queryKey: ["trace", traceType, id],
    queryFn: () => apiGet<TraceResponse>(endpoint),
    enabled: !!sessionId && !!id,
    staleTime: Infinity,
  });
}
