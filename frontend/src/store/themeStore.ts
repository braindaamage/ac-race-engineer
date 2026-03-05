import { create } from "zustand";
import { apiPatch } from "../lib/api";

interface ThemeState {
  theme: string;
  setTheme: (id: string) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: "dark",
  setTheme: (id) => {
    document.documentElement.dataset.theme = id;
    set({ theme: id });
    apiPatch("/config", { ui_theme: id }).catch(() => {
      // fire-and-forget: theme applies in-memory even if persist fails
    });
  },
}));
