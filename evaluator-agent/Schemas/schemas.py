from pydantic import BaseModel


class SocraticExchange(BaseModel):
    question: str
    response: str


class StudentArgument(BaseModel):
    argument_text: str
    rounds: list[SocraticExchange] = []


class PillarAssessment(BaseModel):
    score: int  # 1-5, holistic judgment call for this pillar
    feedback: str | None = None


class OverallReasoning(BaseModel):
    logical_reasoning: PillarAssessment
    organization: PillarAssessment
    persuasiveness: PillarAssessment
    clarity: PillarAssessment


class RubricItemGrade(BaseModel):
    criterion: str
    max_points: int
    points_awarded: int
    feedback: str


class EvaluationOutput(BaseModel):
    overall_reasoning: OverallReasoning
    rubric_alignment: list[RubricItemGrade] = []
    groundedness_notes: str | None = None
