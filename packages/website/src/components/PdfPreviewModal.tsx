import React from "react";
import type { Document } from "../types";

interface Props {
  document: Document;
  onClose: () => void;
}

export function PdfPreviewModal({
  document,
  onClose,
}: Props): React.ReactElement {
  React.useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">{document.name}</span>
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>
        <iframe
          className="pdf-viewer"
          src={`/api/documents/${document.id}/file`}
          title={document.name}
        />
      </div>
    </div>
  );
}
