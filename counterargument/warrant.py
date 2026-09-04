import json
import sys
from pathlib import Path

from pydantic import ValidationError


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evaluator-agent" / "Parley"))

from parley import parleyChatCompletion, parleyStructured 

from schema_models import WarrantList  

MODEL = "bedrock/claude-haiku-4-5"

SYSTEM = """You read one passage from a course reading and record the general rules it engages with, and what the passage DOES to each rule.

The relation is the important part. Do not label a rule by what it says. Label it by how the passage treats it.

  applied  - the passage uses the rule and reaches a result on that basis
  refused  - the passage rejects, repudiates, abandons or declines to extend the rule
  distinguished - the rule stands, but the passage limits it: valid, yet not reaching these facts

A passage that says a court "repudiated", "abandoned", "rejected", "declined to apply" or "replaced" a test is refused, not applied. A passage that says a court applied heightened scrutiny INSTEAD OF deference is refusing the deferential rule. Read for the verb, not the doctrine.

Also record whose position each rule is:

  court  - a rule the deciding court adopts
  author - the article author's own claim
  other  - a position the passage attributes to someone else

That last one matters. Legal writing constantly states a losing argument, a dissent, or a view the author intends to attack. A rule stated inside a quotation from a dissent is held_by "other", not "court", even if it is phrased as though it were law. Getting this wrong means recording the losing side as settled doctrine.

State each rule abstractly, stripped of every proper noun.

Correct: "A taking that produces a public benefit qualifies as a public use."
Wrong: "Berman permits takings for slum clearance." That names a case, so it can only ever match passages about that case, which defeats the purpose.

Return an empty list when the passage has no rule in it: pure facts, procedural history, citation strings, footnote references, headnotes, narration, bibliographic headers. Most passages are like this. Do not invent a rule to fill the output. An empty list is the correct and common answer.

Respond with JSON only. No prose, no markdown fences. Match this schema:

State every rule affirmatively, as something a court could adopt. Never state a rule in negated form.

Wrong: "Substantive due process analysis does not belong in takings doctrine."
Right: "A regulation effects a taking if it does not substantially advance a legitimate state interest." -> relation: refused

If a passage rejects one rule and adopts another in its place, that is two entries: the rejected rule with relation "refused", and the replacement rule with relation "applied". Never record the replacement as refused just because the passage describes it using negative language.

""" + json.dumps(WarrantList.model_json_schema(), indent=2)


def _strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text.removeprefix("json").strip()
    return text


def extract_warrants(chunk_text, model=MODEL):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": "Passage:\n\n" + chunk_text},
    ]

    # try:
    #     return parleyStructured(messages, WarrantList, model=model).warrants
    # except Exception as e:
    #     print("  [structured failed] " + repr(e))

    raw = parleyChatCompletion(messages=messages, model=model, temperature=0.0, max_tokens=1500)
    if not raw:
        return []
    try:
        return WarrantList.model_validate_json(_strip_fences(raw)).warrants
    except ValidationError as e:
        print("  [invalid] " + str(e))
        print("  [raw] " + raw[:300])
        return []


if __name__ == "__main__":
    PASSAGE = """Subject to specific constitutional limitations, when the legislature
    has spoken, the public interest has been declared in terms well-nigh conclusive.
    In such cases the legislature, not the judiciary, is the main guardian of the
    public needs to be served by social legislation. This principle admits of no
    exception merely because the power of eminent domain is involved. The role of
    the judiciary in determining whether that power is being exercised for a public
    purpose is an extremely narrow one."""

    results = extract_warrants(PASSAGE)
    if not results:
        print("no warrants extracted")
    for w in results:
        print("[" + w.relation.value + "] " + w.warrant_text)
        print("    on: " + w.applied_to)
        print("    -> " + w.conclusion)
        print()