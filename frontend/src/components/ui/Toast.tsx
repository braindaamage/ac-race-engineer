import "./Toast.css";

interface ToastNotification {
  id: string;
  type: "info" | "success" | "warning" | "error";
  message: string;
  createdAt: number;
}

interface ToastProps {
  notification: ToastNotification;
  onDismiss: (id: string) => void;
}

export function Toast({ notification, onDismiss }: ToastProps) {
  return (
    <div className={`ace-toast ace-toast--${notification.type}`}>
      <span className="ace-toast__message">{notification.message}</span>
      <button
        className="ace-toast__dismiss"
        onClick={() => onDismiss(notification.id)}
        aria-label="Dismiss"
      >
        &times;
      </button>
    </div>
  );
}
