import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type {
  RecommendationListResponse,
  RecommendationDetailResponse,
} from "../lib/types";

export function useRecommendations(sessionId: string | null) {
  return useQuery<RecommendationListResponse>({
    queryKey: ["recommendations", sessionId],
    queryFn: () =>
      apiGet<RecommendationListResponse>(
        `/sessions/${sessionId}/recommendations`,
      ),
    enabled: !!sessionId,
    staleTime: 0,
    refetchOnMount: true,
  });
}

export function useRecommendationDetail(
  sessionId: string | null,
  recommendationId: string | null,
) {
  return useQuery<RecommendationDetailResponse>({
    queryKey: ["recommendation", sessionId, recommendationId],
    queryFn: () =>
      apiGet<RecommendationDetailResponse>(
        `/sessions/${sessionId}/recommendations/${recommendationId}`,
      ),
    enabled: !!sessionId && !!recommendationId,
    staleTime: Infinity,
  });
}
