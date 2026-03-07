import { Modal } from "../../components/ui";
import type { RecommendationDetailResponse } from "../../lib/types";

interface ApplyConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  recommendation: RecommendationDetailResponse | null;
  isApplying: boolean;
}

export function ApplyConfirmModal({
  open,
  onClose,
  onConfirm,
  recommendation,
  isApplying,
}: ApplyConfirmModalProps) {
  if (!open || !recommendation) return null;

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Apply Setup Changes"
      actions={{
        confirm: {
          label: isApplying ? "Applying..." : "Apply Changes",
          onClick: onConfirm,
          variant: "primary",
        },
        cancel: {
          label: "Cancel",
          onClick: onClose,
        },
      }}
    >
      <div className="ace-apply-modal">
        <table className="ace-apply-modal__table">
          <thead>
            <tr>
              <th>Section</th>
              <th>Parameter</th>
              <th>Current</th>
              <th>New</th>
            </tr>
          </thead>
          <tbody>
            {recommendation.setup_changes.map((change, i) => (
              <tr key={i}>
                <td>{change.section}</td>
                <td>{change.parameter}</td>
                <td>{change.old_value}</td>
                <td>{change.new_value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}
