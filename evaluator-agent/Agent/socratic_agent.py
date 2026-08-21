from __future__ import annotations

from pydantic import ValidationError

from Agent import prompts, rag_tool
from Parley.parley import parleyChatCompletion
from Schemas.schemas import EvaluationOutput, StudentArgument


class SocraticAgent:
    def __init__(self, rubric_items: list[dict] | None = None, reading_text: str | None = None):
        self.rubric_items = rubric_items
        self.reading_text = reading_text

    def ask_question(self, argument: StudentArgument, round_num: int = 1) -> str:
        grounding = rag_tool.check_groundedness(argument.argument_text)
        system_prompt = prompts.build_socratic_prompt(round_num, [row["content"] for row in grounding])
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._format_argument_state(argument)},
        ]
        return parleyChatCompletion(messages)

    def evaluate(self, argument: StudentArgument) -> EvaluationOutput:
        grounding = rag_tool.check_groundedness(argument.argument_text)
        system_prompt = prompts.build_evaluation_prompt(self.rubric_items)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": self._format_full_transcript(argument, grounding)},
        ]
        raw = parleyChatCompletion(messages, max_tokens=2500)
        return self._parse_output(messages, raw)

    def _parse_output(self, messages: list[dict], raw: str | None) -> EvaluationOutput:
        try:
            return EvaluationOutput.model_validate_json(_strip_code_fence(raw or ""))
        except (ValidationError, ValueError):
            retry_messages = messages + [
                {"role": "assistant", "content": raw or ""},
                {"role": "user", "content": "That was not valid JSON matching the required schema. Reply with only the corrected JSON object."},
            ]
            raw_retry = parleyChatCompletion(retry_messages, max_tokens=2500)
            return EvaluationOutput.model_validate_json(_strip_code_fence(raw_retry or ""))

    def _format_argument_state(self, argument: StudentArgument) -> str:
        parts = [f"Student's argument:\n{argument.argument_text}"]
        if self.reading_text:
            parts.append(f"Assigned reading (context):\n{self.reading_text}")
        for i, exchange in enumerate(argument.rounds, start=1):
            parts.append(f"Follow-up {i} - Q: {exchange.question}\nFollow-up {i} - A: {exchange.response}")
        return "\n\n".join(parts)

    def _format_full_transcript(self, argument: StudentArgument, grounding: list[dict]) -> str:
        parts = [self._format_argument_state(argument)]
        if grounding:
            snippets = "\n".join(f"- {row['content']}" for row in grounding)
            parts.append(f"Retrieved source material:\n{snippets}")
        return "\n\n".join(parts)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.removeprefix("json").strip()
    return text
