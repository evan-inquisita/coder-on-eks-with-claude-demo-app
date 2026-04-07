import type { Document, Message } from "./types";

const BASE = "/api";

async function json<T>(resp: Response): Promise<T> {
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }
  return resp.json() as Promise<T>;
}

export async function listDocuments(): Promise<Document[]> {
  return json<Document[]>(await fetch(`${BASE}/documents`));
}

export async function uploadDocument(file: File): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  return json<Document>(
    await fetch(`${BASE}/documents`, { method: "POST", body: form }),
  );
}

export async function deleteDocument(id: string): Promise<void> {
  const resp = await fetch(`${BASE}/documents/${id}`, { method: "DELETE" });
  if (!resp.ok) throw new Error(`Delete failed: ${resp.status}`);
}

export async function listMessages(docId: string): Promise<Message[]> {
  return json<Message[]>(await fetch(`${BASE}/documents/${docId}/messages`));
}

export async function postMessage(
  docId: string,
  content: string,
): Promise<Message> {
  return json<Message>(
    await fetch(`${BASE}/documents/${docId}/messages`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ content }),
    }),
  );
}
