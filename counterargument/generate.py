import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.append(str(HERE.parent / "evaluator-agent" / "Parley"))

from parley import parleyChatCompletion

MODEL = "bedrock/claude-haiku-4-5"


FRAMING = {
    ("refused", "court"):
        "a court rejected this rule outright",
    ("refused", "author"):
        "the author of this reading argues against this rule",
    ("refused", "other"):
        "this rule was pressed and rejected",
    ("distinguished", "court"):
        "a court accepted this rule but drew a line the student's case may fall outside of",
    ("distinguished", "author"):
        "the author accepts this rule but limits how far it reaches",
    ("distinguished", "other"):
        "this rule was accepted but limited",
    ("applied", "court"):
        "a court applied this rule and reached a result the student may not accept",
    ("applied", "author"):
        "the author applies this rule to reach a result the student may not accept",
    ("applied", "other"):
        "this rule was applied to reach a result the student may not accept",
}

STANCE_LINE = {
    "asserts": "The student is relying on this rule: their conclusion follows from it.",
    "rejects": "The student is arguing AGAINST this rule. Do not open by saying their "
               "argument rests on it. Open by naming what they are arguing against.",
}

SYSTEM = """You are the instructor in a graduate seminar on land use and environmental law, in a planning department. Students are not law students. 
They read cases and scholarship to reason about policy, so treat doctrine as something to argue with, not recite.

A student has made an argument. 
You are putting a passage to them: 
a court or scholar that took a position on the same rule their argument depends on. 
Open by naming the rule at issue and where the student stands on it, then put the source against it, then ask them to answer it.

- Say what the source held and why, in enough detail to push against.
- End on a question about that reasoning, not a yes-or-no about the student's claim.
- Name the source. Answering a court is not the same as answering a scholar.
- Use only the material given. Add no holdings, facts or dates.
- Gloss a term of art in a clause if it is doing real work. No lecturing.
- Never name a fallacy or call their reasoning flawed.
- If there is a distinction to draw, that is the student's job, not yours.
- Two to four sentences.
- Plain text only, no markdown.

Example, court source:

So your argument turns on 
public benefit being enough: if the project serves the public, 
the taking is a public use. But in Kelo the Court drew a line there, 
saying a city could not take property simply to hand it to a particular 
identifiable private party, even when the transfer produced benefits. 
What separates a taking that benefits the public from one that benefits a chosen recipient who happens to produce public benefits?

Example, scholar source:

You are treating the public-private distinction as doing the work: 
public actors and public purposes on one side, private on the other. 
McFarlane argues that line cannot be drawn reliably, 
because redevelopment always runs through private developers and private specifications, 
so the label tracks who holds title rather than who bears the cost.
If the distinction does not hold up, what is left of your test?"""


def clean_source(filename):
    if not filename:
        return "an assigned reading"
    t = filename
    for ext in (".pdf", ".PDF", ".docx", ".DOCX", ".doc"):
        t = t.replace(ext, "")
    t = t.replace("_", " ").replace("+", " ")
    t = re.sub(r"\s*\d+\s*S\.?Ct\.?\s*\d+", "", t)
    return re.sub(r"\s+", " ", t).strip(" -,")


def generate_challenge(student_warrant, parallel, student_claim=None,
                       stance="asserts", model=MODEL, max_chunk_chars=1800):
    """
    student_warrant : the unstated rule the student's argument rests on
    parallel        : one row from retrieve.find_parallel
    """
    key = (parallel["reaction"], parallel["reaction_from"])
    framing = FRAMING.get(key, "this rule is at issue")
    source = clean_source(parallel.get("filename"))
    chunk = (parallel.get("chunk_text") or "")[:max_chunk_chars]

    user = "The student's argument turns on this rule:\n  " + student_warrant + "\n"
    user += STANCE_LINE.get(stance, STANCE_LINE["asserts"]) + "\n\n"
    if student_claim:
        user += "Their claim: " + student_claim + "\n\n"
    user += (
        "In " + source + ", " + framing + ":\n"
        "  rule:       " + parallel["warrant_text"] + "\n"
        "  applied to: " + (parallel.get("applied_to") or "") + "\n"
        "  result:     " + (parallel.get("conclusion") or "") + "\n\n"
        "Source text:\n" + chunk + "\n"
    )

    out = parleyChatCompletion(
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": user}],
        model=model, temperature=0.4, max_tokens=250,
    )
    return (out or "").strip()