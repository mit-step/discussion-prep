import { useEffect, useState } from "react";
import { api } from "../api/client";
import { ReadingCard } from "../components/ReadingCard";
import { SearchBox } from "../components/SearchBox";
import { useUser } from "../context/UserContext";
import type { Reading } from "../types";

export function LibraryPage() {
  const { user, logout } = useUser();
  const [readings, setReadings] = useState<Reading[] | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

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
          <div className="app-header-actions">
            <span className="round-badge">{user?.name}</span>
            <button type="button" className="secondary" onClick={logout}>
              Log out
            </button>
          </div>
        </div>

        <SearchBox onQueryChange={setQuery} />

        {error && <div className="bubble system">Error: {error}</div>}
        {readings === null && !error && <div className="library-empty">Loading readings…</div>}
        {readings?.length === 0 && <div className="library-empty">No matching readings.</div>}
        {readings && readings.length > 0 && (
          <div className="reading-grid">
            {readings.map((reading) => (
              <ReadingCard key={reading.doc_uuid} reading={reading} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
