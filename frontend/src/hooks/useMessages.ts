import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type { MessageListResponse } from "../lib/types";

export function useMessages(sessionId: string | null) {
  return useQuery<MessageListResponse>({
    queryKey: ["messages", sessionId],
    queryFn: () =>
      apiGet<MessageListResponse>(`/sessions/${sessionId}/messages`),
    enabled: !!sessionId,
    staleTime: 0,
    refetchOnMount: true,
  });
}
