import React from "react";

interface Props {
  docId: string;
  docName: string;
  onClose: () => void;
}

export function PdfPreviewModal({
  docId,
  docName,
  onClose,
}: Props): React.ReactElement {
  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>): void {
    if (e.target === e.currentTarget) onClose();
  }

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal">
        <div className="modal-header">
          <span className="modal-title">{docName}</span>
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <iframe
          className="modal-pdf"
          src={`/api/documents/${docId}/content`}
          title={docName}
        />
      </div>
    </div>
  );
}
