import json
import sys
from pathlib import Path

from pydantic import ValidationError

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE))
sys.path.append(str(HERE.parent / "evaluator-agent" / "Parley"))

from parley import parleyChatCompletion

from schema_models import TurnStructure

MODEL = "bedrock/claude-haiku-4-5"

SYSTEM = """You extract the structure of a student's argument in a discussion section on land use and environmental law.

The warrant is the part that matters and the part the student almost never says out loud. If a student says "Berman upheld a taking for slum clearance, so this one is fine too," the warrant is "a taking that produces a public benefit qualifies as a public use." Write that sentence yourself.

Always state the warrant affirmatively, as a rule someone could adopt. Never state it as a denial. Use the stance field to record whether the student is relying on it or arguing against it:

  asserts - the student's conclusion depends on this rule being right
  rejects - the student is arguing this rule is wrong or too broad

A student arguing "economic development should not count as public use" is REJECTING the rule "a taking for economic development qualifies as a public use". The warrant stays affirmative; only the stance changes.

Strip proper nouns from the warrant even when the student used them, so it can match a source the student never mentioned. Keep the names in invoked_sources.

Set has_argument to false when there is no argument to extract. Do not invent one.

Respond with JSON only. No prose, no markdown fences. Match this schema:

""" + json.dumps(TurnStructure.model_json_schema(), indent=2)


def _strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text.removeprefix("json").strip()
    return text


def extract_turn(turn_text, model=MODEL):
    """Returns a TurnStructure, or None when the turn carries no argument."""
    raw = parleyChatCompletion(
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": "Student turn:\n\n" + turn_text}],
        model=model, temperature=0.0, max_tokens=800,
    )
    if not raw:
        return None
    try:
        t = TurnStructure.model_validate_json(_strip_fences(raw))
    except ValidationError as e:
        print("  [invalid] " + str(e))
        return None
    return t if t.has_argument and t.warrant_text else None