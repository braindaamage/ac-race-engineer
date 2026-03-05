import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPatch } from "../lib/api";
import type { ConfigResponse, ConfigUpdateRequest } from "../lib/validation";

export function useConfig() {
  const queryClient = useQueryClient();

  const { data: config, isLoading, error } = useQuery<ConfigResponse>({
    queryKey: ["config"],
    queryFn: () => apiGet<ConfigResponse>("/config"),
    staleTime: 60_000,
  });

  const mutation = useMutation<ConfigResponse, Error, Partial<ConfigUpdateRequest>>({
    mutationFn: (fields) => apiPatch<ConfigResponse>("/config", fields),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
    },
  });

  return {
    config,
    isLoading,
    error: error ?? null,
    updateConfig: mutation.mutateAsync,
    isUpdating: mutation.isPending,
  };
}
