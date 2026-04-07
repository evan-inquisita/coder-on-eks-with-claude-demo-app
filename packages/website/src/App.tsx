import React from "react";
import { DocumentList } from "./components/DocumentList";
import { ChatPanel } from "./components/ChatPanel";

export function App(): React.ReactElement {
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const [refreshKey, setRefreshKey] = React.useState(0);

  return (
    <div className="app">
      <header className="app-header">
        <h1>doc-chat</h1>
      </header>
      <div className="app-body">
        <aside className="sidebar">
          <DocumentList
            selectedId={selectedId}
            onSelect={setSelectedId}
            refreshKey={refreshKey}
            onChange={() => setRefreshKey((k) => k + 1)}
          />
        </aside>
        <main className="main">
          {selectedId ? (
            <ChatPanel documentId={selectedId} />
          ) : (
            <div className="empty">
              Select or upload a document to start chatting.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
