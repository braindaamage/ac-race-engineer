interface AssistantMessageProps {
  content: string;
  timestamp: string;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function AssistantMessage({ content, timestamp }: AssistantMessageProps) {
  return (
    <div className="ace-message ace-message--assistant">
      <div className="ace-message__content">{content}</div>
      <div className="ace-message__timestamp">{formatTime(timestamp)}</div>
    </div>
  );
}
