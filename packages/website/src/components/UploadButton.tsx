import React from 'react';
import { uploadDocument } from '../api';

interface Props {
  onUploaded: () => void;
}

export function UploadButton({ onUploaded }: Props): React.ReactElement {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleChange(e: React.ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      await uploadDocument(file);
      onUploaded();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'upload failed');
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = '';
    }
  }

  return (
    <div className="upload">
      <button
        type="button"
        disabled={busy}
        onClick={() => inputRef.current?.click()}
      >
        {busy ? 'Uploading…' : '+ Upload PDF'}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        onChange={handleChange}
        hidden
      />
      {error && <div className="error">{error}</div>}
    </div>
  );
}
