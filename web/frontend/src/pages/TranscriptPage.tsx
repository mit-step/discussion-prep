import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import { ReportCard } from "../components/ReportCard";
import type { TranscriptDetail } from "../types";

function formatDate(createdAt: string): string {
  return new Date(`${createdAt.replace(" ", "T")}Z`).toLocaleString();
}

export function TranscriptPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [transcript, setTranscript] = useState<TranscriptDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    api
      .getTranscript(sessionId)
      .then(setTranscript)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load transcript"));
  }, [sessionId]);

  if (error) {
    return (
      <div className="library-page">
        <div className="bubble system">Error: {error}</div>
      </div>
    );
  }

  if (!transcript) {
    return (
      <div className="library-page">
        <div className="library-empty">Loading…</div>
      </div>
    );
  }

  return (
    <div className="library-page">
      <div className="library-container transcript-page-container">
        <div>
          <h1>Session Transcript</h1>
          <div className="transcript-meta">{formatDate(transcript.created_at)}</div>
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <button type="button" className="secondary" onClick={() => navigate("/library")}>
            ← Back to Library
          </button>
          <Link to="/about" className="knowledge-graph-link">
            About
          </Link>
        </div>

        <ReportCard evaluation={transcript.evaluation} />

        <div className="transcript-section">
          <h2>Argument</h2>
          <div className="argument-text">{transcript.argument}</div>
        </div>

        <div className="transcript-section">
          <h2>Discussion</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {transcript.exchanges.map((exchange, i) => (
              <div className="exchange" key={i}>
                <div className="exchange-label">Q{i + 1}</div>
                <div className="exchange-q">{exchange.question}</div>
                <div className="exchange-label">A{i + 1}</div>
                <div className="exchange-a">{exchange.response}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
