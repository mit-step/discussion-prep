export interface PillarAssessment {
  score: number;
  feedback: string | null;
}

export interface OverallReasoning {
  logical_reasoning: PillarAssessment;
  organization: PillarAssessment;
  persuasiveness: PillarAssessment;
  clarity: PillarAssessment;
}

export interface RubricItemGrade {
  criterion: string;
  max_points: number;
  points_awarded: number;
  feedback: string;
}

export interface Evaluation {
  overall_reasoning: OverallReasoning;
  rubric_alignment: RubricItemGrade[];
  groundedness_notes: string | null;
}

export interface Reading {
  doc_uuid: string;
  filename: string;
  title: string;
  has_pdf: boolean;
  latest_evaluation: Evaluation | null;
  latest_attempt_at: string | null;
}

export interface HistoryEntry {
  session_id: string;
  created_at: string;
  overall_mean: number | null;
  rubric_total: number | null;
  rubric_max: number | null;
}

export interface Exchange {
  question: string;
  response: string;
}

export interface RespondResult {
  completed?: boolean;
  evaluation?: Evaluation;
  round?: number;
  rounds_total?: number;
  question?: string;
}

export interface TranscriptDetail {
  session_id: string;
  reading_id: string;
  argument: string;
  exchanges: Exchange[];
  evaluation: Evaluation;
  created_at: string;
}
