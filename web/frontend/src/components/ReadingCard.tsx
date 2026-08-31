import { useNavigate } from "react-router-dom";
import { readingPdfUrl } from "../api/client";
import type { Reading } from "../types";
import { RadarChart, type RadarDatum } from "./RadarChart";

const PILLAR_LABELS: Record<string, string> = {
  logical_reasoning: "Logic",
  organization: "Org.",
  persuasiveness: "Persuasion",
  clarity: "Clarity",
};

export function ReadingCard({ reading }: { reading: Reading }) {
  const navigate = useNavigate();
  const evaluation = reading.latest_evaluation;

  function openChat() {
    navigate(`/chat/${reading.doc_uuid}`, { state: { title: reading.title } });
  }

  let overallData: RadarDatum[] = [];
  let overallMean: number | null = null;
  let rubricData: RadarDatum[] = [];
  let rubricMean: number | null = null;

  if (evaluation) {
    const pillars = Object.entries(PILLAR_LABELS).map(([key, label]) => ({
      label,
      score: evaluation.overall_reasoning[key as keyof typeof evaluation.overall_reasoning].score,
    }));
    overallData = pillars.map((p) => ({ label: p.label, value: p.score / 5 }));
    overallMean = pillars.reduce((sum, p) => sum + p.score, 0) / pillars.length;

    if (evaluation.rubric_alignment.length > 0) {
      rubricData = evaluation.rubric_alignment.map((item) => ({
        label: item.criterion.length > 14 ? `${item.criterion.slice(0, 13)}…` : item.criterion,
        value: item.points_awarded / item.max_points,
      }));
      const totalAwarded = evaluation.rubric_alignment.reduce((s, i) => s + i.points_awarded, 0);
      const totalMax = evaluation.rubric_alignment.reduce((s, i) => s + i.max_points, 0);
      rubricMean = totalMax > 0 ? (totalAwarded / totalMax) * 100 : null;
    }
  }

  return (
    <button className="reading-card" onClick={openChat}>
      <div className="reading-card-title">{reading.title}</div>

      {evaluation ? (
        <div className="reading-card-preview">
          <div className="reading-card-metric">
            <div className="reading-card-metric-label">Overall Reasoning</div>
            <RadarChart data={overallData} height={110} />
            <div className="reading-card-metric-value">{overallMean?.toFixed(1)}/5</div>
          </div>
          {rubricData.length > 0 && (
            <div className="reading-card-metric">
              <div className="reading-card-metric-label">Rubric Alignment</div>
              <RadarChart data={rubricData} height={110} />
              <div className="reading-card-metric-value">{rubricMean?.toFixed(0)}%</div>
            </div>
          )}
        </div>
      ) : (
        <div className="reading-card-empty">Not attempted yet</div>
      )}

      <div className="reading-card-actions">
        {reading.has_pdf ? (
          <a
            className="reading-card-pdf-link"
            href={readingPdfUrl(reading.doc_uuid)}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            Preview reading →
          </a>
        ) : (
          <span className="reading-card-pdf-disabled">Preview unavailable</span>
        )}
      </div>
    </button>
  );
}
