import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import type { SessionListResponse, SessionRecord } from "../lib/types";

export function useSessions(): {
  sessions: SessionRecord[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
} {
  const { data, isLoading, error, refetch } = useQuery<SessionListResponse>({
    queryKey: ["sessions"],
    queryFn: () => apiGet<SessionListResponse>("/sessions"),
    refetchInterval: 5000,
    select: undefined,
  });

  return {
    sessions: data?.sessions ?? [],
    isLoading,
    error: error as Error | null,
    refetch,
  };
}
