import React from "react";
import { listMessages, postMessage } from "../api";
import type { Message } from "../types";
import { MessageBubble } from "./MessageBubble";

interface Props {
  documentId: string;
}

export function ChatPanel({ documentId }: Props): React.ReactElement {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    listMessages(documentId)
      .then((m) => {
        if (!cancelled) setMessages(m);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [documentId]);

  async function handleSend(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const content = input.trim();
    if (!content || busy) return;
    setBusy(true);
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content }]);
    setInput("");
    try {
      const assistant = await postMessage(documentId, content);
      setMessages((prev) => [...prev, assistant]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "send failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-history">
        {messages.length === 0 && (
          <div className="muted">No messages yet. Ask a question to begin.</div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
      </div>
      {error && <div className="error">{error}</div>}
      <form className="chat-input" onSubmit={handleSend}>
        <input
          type="text"
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()}>
          {busy ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
