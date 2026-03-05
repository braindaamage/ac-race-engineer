import { create } from "zustand";

interface UIState {
  activeSection: string;
  sidebarCollapsed: boolean;
  setActiveSection: (id: string) => void;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeSection: "sessions",
  sidebarCollapsed: false,
  setActiveSection: (id) => set({ activeSection: id }),
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
}));
