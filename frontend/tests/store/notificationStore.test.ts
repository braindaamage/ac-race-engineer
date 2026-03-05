import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { useNotificationStore } from "../../src/store/notificationStore";

describe("notificationStore", () => {
  beforeEach(() => {
    useNotificationStore.setState({ notifications: [] });
  });

  it("addNotification creates notification with unique id", () => {
    const { addNotification } = useNotificationStore.getState();
    const id1 = addNotification("info", "First");
    const id2 = addNotification("success", "Second");

    expect(id1).not.toBe(id2);

    const { notifications } = useNotificationStore.getState();
    expect(notifications).toHaveLength(2);
    expect(notifications[0]!.message).toBe("First");
    expect(notifications[1]!.message).toBe("Second");
  });

  it("removeNotification removes by id", () => {
    const { addNotification } = useNotificationStore.getState();
    const id = addNotification("info", "To remove");
    expect(useNotificationStore.getState().notifications).toHaveLength(1);

    useNotificationStore.getState().removeNotification(id);
    expect(useNotificationStore.getState().notifications).toHaveLength(0);
  });

  describe("auto-removal", () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it("non-error notifications are auto-removed after timeout", () => {
      const { addNotification } = useNotificationStore.getState();
      addNotification("info", "Auto remove me");
      expect(useNotificationStore.getState().notifications).toHaveLength(1);

      vi.advanceTimersByTime(5000);
      expect(useNotificationStore.getState().notifications).toHaveLength(0);
    });

    it("error notifications are NOT auto-removed", () => {
      const { addNotification } = useNotificationStore.getState();
      addNotification("error", "Persistent error");
      expect(useNotificationStore.getState().notifications).toHaveLength(1);

      vi.advanceTimersByTime(10000);
      expect(useNotificationStore.getState().notifications).toHaveLength(1);
    });
  });
});
