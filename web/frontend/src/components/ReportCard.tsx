import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Evaluation } from "../types";

const PILLAR_LABELS: Record<string, string> = {
  logical_reasoning: "Logical Reasoning",
  organization: "Organization",
  persuasiveness: "Persuasiveness",
  clarity: "Clarity",
};

export function ReportCard({ evaluation }: { evaluation: Evaluation }) {
  return (
    <div className="report-card">
      <h2>Overall Reasoning</h2>
      {Object.entries(PILLAR_LABELS).map(([key, label]) => {
        const pillar = evaluation.overall_reasoning[key as keyof Evaluation["overall_reasoning"]];
        return (
          <div key={key}>
            <div className="pillar-row">
              <div className="pillar-name">{label}</div>
              <div className="meter">
                <div className="meter-fill" style={{ width: `${(pillar.score / 5) * 100}%` }} />
              </div>
              <div>{pillar.score}/5</div>
            </div>
            {pillar.feedback && (
              <div className="pillar-feedback">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{pillar.feedback}</ReactMarkdown>
              </div>
            )}
          </div>
        );
      })}

      {evaluation.rubric_alignment.length > 0 && (
        <>
          <h2>Rubric Alignment</h2>
          {evaluation.rubric_alignment.map((item, i) => (
            <div className="rubric-item" key={i}>
              <div className="rubric-item-head">
                <span>{item.criterion}</span>
                <span>
                  {item.points_awarded}/{item.max_points}
                </span>
              </div>
              <div className="meter" style={{ marginTop: "0.35rem" }}>
                <div
                  className="meter-fill"
                  style={{ width: `${(item.points_awarded / item.max_points) * 100}%` }}
                />
              </div>
              {item.feedback && (
                <div className="rubric-item-feedback">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.feedback}</ReactMarkdown>
                </div>
              )}
            </div>
          ))}
        </>
      )}

      {evaluation.groundedness_notes && (
        <div className="groundedness">Groundedness: {evaluation.groundedness_notes}</div>
      )}
    </div>
  );
}
