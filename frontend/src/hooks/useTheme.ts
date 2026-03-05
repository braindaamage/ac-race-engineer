import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../lib/api";
import { useThemeStore } from "../store/themeStore";

interface ConfigResponse {
  ui_theme: string;
}

export function useTheme() {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  const { isLoading } = useQuery({
    queryKey: ["config-theme"],
    queryFn: () => apiGet<ConfigResponse>("/config"),
    staleTime: 60_000,
    select: (data) => data.ui_theme,
  });

  const configTheme = useQuery({
    queryKey: ["config-theme"],
    queryFn: () => apiGet<ConfigResponse>("/config"),
    staleTime: 60_000,
    select: (data) => data.ui_theme,
  }).data;

  useEffect(() => {
    if (configTheme && configTheme !== theme) {
      document.documentElement.dataset.theme = configTheme;
      useThemeStore.setState({ theme: configTheme });
    }
  }, [configTheme, theme]);

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return { theme, toggleTheme, isLoading };
}
