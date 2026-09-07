from enum import Enum

from pydantic import BaseModel, Field


class Reaction(str, Enum):
    """What is being done to the rule in this passage."""

    applied = "applied"              # used, to reach a result
    refused = "refused"              # rejected, repudiated, declined to extend
    distinguished = "distinguished"  # rule stands but does not reach these facts


class Role(str, Enum):
    """Who a rule or a reaction belongs to."""

    court = "court"    # a court, in a holding or established doctrine
    author = "author"  # the author of this article
    other = "other"    # anyone else: a dissent, a party, another scholar


class Warrant(BaseModel):
    warrant_text: str = Field(
        description=(
            "The general rule that licenses moving from facts to conclusion. "
            "One sentence, stated affirmatively as something a court could adopt. "
            "Contains NO case names, party names, statute names, place names or "
            "dates. It must be stated so that it could apply to a situation this "
            "passage never mentions."
        )
    )
    applied_to: str = Field(
        description="The concrete situation in this passage the rule was applied to."
    )
    conclusion: str = Field(
        description="The result that followed in this passage."
    )
    reaction: Reaction
    rule_from: Role = Field(
        description=(
            "Whose rule this is: 'court' for a rule from a holding or doctrine, "
            "'author' for the article author's own proposed rule, 'other' for "
            "anyone else's (a dissent, a party's argument, another scholar)."
        )
    )
    reaction_from: Role = Field(
        description=(
            "Who is applying, refusing or distinguishing the rule in this passage. "
            "Often different from rule_from. When an author criticizes a court's "
            "rule, rule_from is 'court' and reaction_from is 'author'."
        )
    )


class WarrantList(BaseModel):
    warrants: list[Warrant] = Field(
        description="Empty when the passage contains no rule."
    )

class Stance(str, Enum):
    """What the student is doing with the rule their argument rests on."""

    asserts = "asserts"  # relying on it: their conclusion follows from it
    rejects = "rejects"  # arguing against it


class TurnStructure(BaseModel):
    has_argument: bool = Field(
        description="False for a question, a clarification, agreement, or small talk."
    )
    claim: str = Field(description="The position the student is defending.")
    premises: list[str] = Field(
        description="Reasons the student actually stated. Do not add reasons they did not give."
    )
    warrant_text: str = Field(
        description=(
            "The unstated general rule that licenses moving from the premises to the "
            "claim. One sentence, stated affirmatively as something a court could "
            "adopt. NO case names, party names, statutes, places or dates, even if "
            "the student used them."
        )
    )
    stance: Stance = Field(
        description=(
            "Whether the student is relying on the warrant or arguing against it. "
            "State the warrant affirmatively either way: if the student argues that "
            "public benefit is NOT enough for public use, the warrant is still "
            "'a taking producing public benefit qualifies as public use' and the "
            "stance is 'rejects'."
        )
    )
    invoked_sources: list[str] = Field(
        description="Readings or cases the student named. Empty if none."
    )