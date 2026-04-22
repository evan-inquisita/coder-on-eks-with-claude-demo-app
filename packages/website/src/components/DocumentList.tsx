import React from "react";
import { listDocuments } from "../api";
import type { Document } from "../types";
import { UploadButton } from "./UploadButton";
import { PdfPreviewModal } from "./PdfPreviewModal";

interface Props {
  selectedId: string | null;
  onSelect: (id: string) => void;
  refreshKey: number;
  onChange: () => void;
}

export function DocumentList({
  selectedId,
  onSelect,
  refreshKey,
  onChange,
}: Props): React.ReactElement {
  const [docs, setDocs] = React.useState<Document[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [previewDoc, setPreviewDoc] = React.useState<Document | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listDocuments()
      .then((d) => {
        if (!cancelled) {
          setDocs(d);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  return (
    <div className="document-list">
      <UploadButton onUploaded={onChange} />
      {loading && <div className="muted">Loading…</div>}
      {error && <div className="error">{error}</div>}
      {!loading && docs.length === 0 && (
        <div className="muted">No documents yet.</div>
      )}
      <ul>
        {docs.map((d) => (
          <li
            key={d.id}
            className={d.id === selectedId ? "selected" : ""}
            onClick={() => onSelect(d.id)}
          >
            <span className="doc-name">{d.name}</span>
            <button
              className="preview-btn"
              title="Preview PDF"
              onClick={(e) => {
                e.stopPropagation();
                setPreviewDoc(d);
              }}
            >
              Preview
            </button>
          </li>
        ))}
      </ul>
      {previewDoc && (
        <PdfPreviewModal
          document={previewDoc}
          onClose={() => setPreviewDoc(null)}
        />
      )}
    </div>
  );
}
