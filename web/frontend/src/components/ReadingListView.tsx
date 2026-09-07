import dayjs from "dayjs";
import relativeTime from "dayjs/plugin/relativeTime";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { readingPdfUrl } from "../api/client";
import type { Reading } from "../types";
import { summarizeEvaluation } from "../utils/evaluationSummary";

dayjs.extend(relativeTime);

type SortColumn = "title" | "overall" | "rubric" | "attempted";
type SortDirection = "asc" | "desc";

function formatRelative(createdAt: string): string {
  return dayjs(`${createdAt.replace(" ", "T")}Z`).fromNow();
}

// Nulls (never-attempted readings) always sort last, regardless of direction —
// otherwise "sort ascending" would put untried readings confusingly first.
function compareNullable(a: number | string | null, b: number | string | null, dir: 1 | -1): number {
  if (a === null && b === null) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  if (typeof a === "number" && typeof b === "number") return (a - b) * dir;
  return String(a).localeCompare(String(b)) * dir;
}

export function ReadingListView({ readings }: { readings: Reading[] }) {
  const navigate = useNavigate();
  const [sortColumn, setSortColumn] = useState<SortColumn>("title");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  function toggleSort(column: SortColumn) {
    if (column === sortColumn) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(column);
      setSortDirection("asc");
    }
  }

  const rows = useMemo(() => {
    const withSummary = readings.map((reading) => ({
      reading,
      summary: reading.latest_evaluation ? summarizeEvaluation(reading.latest_evaluation) : null,
    }));

    const dir: 1 | -1 = sortDirection === "asc" ? 1 : -1;
    return [...withSummary].sort((a, b) => {
      switch (sortColumn) {
        case "title":
          return a.reading.title.localeCompare(b.reading.title) * dir;
        case "overall":
          return compareNullable(a.summary?.overallMean ?? null, b.summary?.overallMean ?? null, dir);
        case "rubric":
          return compareNullable(a.summary?.rubricPct ?? null, b.summary?.rubricPct ?? null, dir);
        case "attempted":
          return compareNullable(a.reading.latest_attempt_at, b.reading.latest_attempt_at, dir);
      }
    });
  }, [readings, sortColumn, sortDirection]);

  function sortIndicator(column: SortColumn) {
    if (column !== sortColumn) return null;
    return <span className="sort-arrow">{sortDirection === "asc" ? "▲" : "▼"}</span>;
  }

  function headerButton(column: SortColumn, label: string) {
    return (
      <button type="button" className="reading-list-col" onClick={() => toggleSort(column)}>
        {label} {sortIndicator(column)}
      </button>
    );
  }

  return (
    <div className="reading-list">
      <div className="reading-list-header">
        {headerButton("title", "Title")}
        {headerButton("overall", "Overall")}
        {headerButton("rubric", "Rubric")}
        {headerButton("attempted", "Last Attempt")}
        <span className="reading-list-col reading-list-col-preview" />
      </div>

      {rows.map(({ reading, summary }) => (
        <div
          key={reading.doc_uuid}
          className="reading-list-row"
          onClick={() => navigate(`/chat/${reading.doc_uuid}`, { state: { title: reading.title } })}
        >
          <div className="reading-list-col reading-list-col-title">{reading.title}</div>
          <div className="reading-list-col">{summary ? `${summary.overallMean.toFixed(1)}/5` : "—"}</div>
          <div className="reading-list-col">
            {summary?.rubricPct != null ? `${summary.rubricPct.toFixed(0)}%` : "—"}
          </div>
          <div className="reading-list-col">
            {reading.latest_attempt_at ? formatRelative(reading.latest_attempt_at) : "—"}
          </div>
          <div className="reading-list-col reading-list-col-preview">
            {reading.has_pdf ? (
              <a
                href={readingPdfUrl(reading.doc_uuid)}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                Preview →
              </a>
            ) : (
              <span className="reading-card-pdf-disabled">—</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
