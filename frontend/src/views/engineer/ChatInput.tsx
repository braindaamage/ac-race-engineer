import { useState, useCallback, type KeyboardEvent } from "react";
import { Button } from "../../components/ui";

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  disabled,
  placeholder = "Ask your engineer...",
}: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  }, [text, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  return (
    <div className="ace-chat-input">
      <textarea
        className="ace-chat-input__textarea"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
      />
      <div className="ace-chat-input__send">
        <Button
          variant="primary"
          size="sm"
          disabled={disabled || !text.trim()}
          onClick={handleSend}
        >
          Send
        </Button>
      </div>
    </div>
  );
}
