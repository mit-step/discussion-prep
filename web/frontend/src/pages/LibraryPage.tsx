import { useEffect, useState } from "react";
import { api, BASE } from "../api/client";
import { ProfileMenu } from "../components/ProfileMenu";
import { ReadingCard } from "../components/ReadingCard";
import { ReadingListView } from "../components/ReadingListView";
import { SearchBox } from "../components/SearchBox";
import type { Reading } from "../types";

type ViewMode = "grid" | "list";
const VIEW_MODE_KEY = "discussion-prep:library-view-mode";

export function LibraryPage() {
  const [readings, setReadings] = useState<Reading[] | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>(
    () => (localStorage.getItem(VIEW_MODE_KEY) as ViewMode | null) ?? "grid",
  );

  useEffect(() => {
    localStorage.setItem(VIEW_MODE_KEY, viewMode);
  }, [viewMode]);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    const request = query.trim() ? api.searchReadings(query) : api.listReadings();
    request
      .then((data) => {
        if (!cancelled) setReadings(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load readings");
      });
    return () => {
      cancelled = true;
    };
  }, [query]);

  return (
    <div className="library-page">
      <div className="library-container">
        <div className="library-header">
          <h1>Discussion Prep</h1>
          <div className="library-header-actions">
            <div className="view-toggle">
              <button
                type="button"
                className={viewMode === "grid" ? "active" : ""}
                title="Card view"
                onClick={() => setViewMode("grid")}
              >
                ⊞
              </button>
              <button
                type="button"
                className={viewMode === "list" ? "active" : ""}
                title="List view"
                onClick={() => setViewMode("list")}
              >
                ☰
              </button>
            </div>
            <a
              className="knowledge-graph-link"
              href={`${BASE}/api/knowledge-graph`}
              target="_blank"
              rel="noreferrer"
            >
              Knowledge Graph
            </a>
            <ProfileMenu />
          </div>
        </div>

        <div className="library-search-row">
          <SearchBox onQueryChange={setQuery} />
        </div>

        {error && <div className="bubble system">Error: {error}</div>}
        {readings === null && !error && <div className="library-empty">Loading readings…</div>}
        {readings?.length === 0 && <div className="library-empty">No matching readings.</div>}
        {readings && readings.length > 0 && viewMode === "grid" && (
          <div className="reading-grid">
            {readings.map((reading) => (
              <ReadingCard key={reading.doc_uuid} reading={reading} />
            ))}
          </div>
        )}
        {readings && readings.length > 0 && viewMode === "list" && <ReadingListView readings={readings} />}
      </div>
    </div>
  );
}
