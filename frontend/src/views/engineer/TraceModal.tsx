import { Modal } from "../../components/ui";

interface TraceModalProps {
  open: boolean;
  onClose: () => void;
  traceContent: string | null;
}

export function TraceModal({ open, onClose, traceContent }: TraceModalProps) {
  return (
    <Modal open={open} onClose={onClose} title="Diagnostic Trace">
      <div className="ace-trace-modal">
        {traceContent ? (
          <pre className="ace-trace-modal__content">{traceContent}</pre>
        ) : (
          <p className="ace-trace-modal__empty">No trace content available.</p>
        )}
      </div>
    </Modal>
  );
}
