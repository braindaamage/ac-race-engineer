import { create } from "zustand";
import { NOTIFICATION_DURATION } from "../lib/constants";

export interface Notification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  message: string;
  createdAt: number;
}

interface NotificationState {
  notifications: Notification[];
  addNotification: (type: Notification["type"], message: string) => string;
  removeNotification: (id: string) => void;
}

let nextId = 0;

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  addNotification: (type, message) => {
    const id = `notif-${++nextId}-${Date.now()}`;
    const notification: Notification = {
      id,
      type,
      message,
      createdAt: Date.now(),
    };
    set((s) => ({ notifications: [...s.notifications, notification] }));

    if (type !== "error") {
      setTimeout(() => {
        get().removeNotification(id);
      }, NOTIFICATION_DURATION);
    }

    return id;
  },
  removeNotification: (id) =>
    set((s) => ({
      notifications: s.notifications.filter((n) => n.id !== id),
    })),
}));
