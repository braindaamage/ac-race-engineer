import { useNotificationStore } from "../../store/notificationStore";
import { Toast } from "../ui/Toast";
import "./ToastContainer.css";

export function ToastContainer() {
  const notifications = useNotificationStore((s) => s.notifications);
  const removeNotification = useNotificationStore(
    (s) => s.removeNotification,
  );

  if (notifications.length === 0) return null;

  return (
    <div className="ace-toast-container">
      {notifications.map((n) => (
        <Toast key={n.id} notification={n} onDismiss={removeNotification} />
      ))}
    </div>
  );
}
