import type { Evaluation } from "../types";

const PILLAR_KEYS = ["logical_reasoning", "organization", "persuasiveness", "clarity"] as const;

export interface EvaluationSummary {
  overallMean: number;
  rubricPct: number | null;
}

export function summarizeEvaluation(evaluation: Evaluation): EvaluationSummary {
  const scores = PILLAR_KEYS.map((key) => evaluation.overall_reasoning[key].score);
  const overallMean = scores.reduce((a, b) => a + b, 0) / scores.length;

  let rubricPct: number | null = null;
  if (evaluation.rubric_alignment.length > 0) {
    const awarded = evaluation.rubric_alignment.reduce((s, i) => s + i.points_awarded, 0);
    const max = evaluation.rubric_alignment.reduce((s, i) => s + i.max_points, 0);
    rubricPct = max > 0 ? (awarded / max) * 100 : null;
  }
  return { overallMean, rubricPct };
}
