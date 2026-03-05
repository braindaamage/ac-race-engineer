import { create } from "zustand";

interface SessionState {
  selectedSessionId: string | null;
  selectSession: (id: string) => void;
  clearSession: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  selectedSessionId: null,
  selectSession: (id) => set({ selectedSessionId: id }),
  clearSession: () => set({ selectedSessionId: null }),
}));
