import { useEffect, useState } from "react";
import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { api } from "../api/client";
import type { HistoryEntry } from "../types";

dayjs.extend(relativeTime);

function formatRelative(createdAt: string): string {
  // SQLite's CURRENT_TIMESTAMP is UTC but has no timezone suffix — normalize
  // the "YYYY-MM-DD HH:MM:SS" shape to an ISO string dayjs parses as UTC.
  return dayjs(`${createdAt.replace(" ", "T")}Z`).fromNow();
}

export function HistoryPanel({ docUuid, onClose }: { docUuid: string; onClose: () => void }) {
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);

  useEffect(() => {
    api
      .readingHistory(docUuid)
      .then(setEntries)
      .catch(() => setEntries([]));
  }, [docUuid]);

  return (
    <div className="history-panel-backdrop" onClick={onClose}>
      <div className="history-panel" onClick={(e) => e.stopPropagation()}>
        <div className="history-panel-header">
          <h2>Past sessions</h2>
          <button type="button" className="secondary" onClick={onClose}>
            Close
          </button>
        </div>
        {entries === null && <div className="history-empty">Loading…</div>}
        {entries !== null && entries.length === 0 && (
          <div className="history-empty">No past sessions on this reading yet.</div>
        )}
        {entries?.map((entry) => (
          <a
            key={entry.session_id}
            className="history-row"
            href={`/discussion-prep/transcript/${entry.session_id}`}
            target="_blank"
            rel="noreferrer"
          >
            <div className="history-row-time">{formatRelative(entry.created_at)}</div>
            <div className="history-row-scores">
              {entry.overall_mean !== null && <span>Overall {entry.overall_mean}/5</span>}
              {entry.rubric_total !== null && (
                <span>
                  Rubric {entry.rubric_total}/{entry.rubric_max}
                </span>
              )}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
