from __future__ import annotations

import json
from pathlib import Path

from Agent.socratic_agent import SocraticAgent
from Schemas.schemas import SocraticExchange, StudentArgument

ROUNDS = 3


def load_rubric_items() -> list[dict]:
    rubric_path = Path(__file__).parent / "sample_rubric.json"
    return json.loads(rubric_path.read_text())["criteria"]


def load_reading_text() -> str | None:
    path_str = input("Path to a reading to use as context (optional, press enter to skip): ").strip()
    if not path_str:
        return None
    path = Path(path_str)
    if not path.exists():
        print(f"Couldn't find '{path_str}' — continuing without it.")
        return None
    return path.read_text()


def print_evaluation(result) -> None:
    print("\n=== Overall Reasoning ===")
    for pillar_name, pillar in result.overall_reasoning:
        print(f"{pillar_name.replace('_', ' ').title()}: {pillar.score}/5")
        if pillar.feedback:
            print(f"  {pillar.feedback}")

    print("\n=== Rubric Alignment ===")
    if not result.rubric_alignment:
        print("(no rubric was supplied)")
    for item in result.rubric_alignment:
        print(f"{item.criterion}: {item.points_awarded}/{item.max_points}")
        print(f"  {item.feedback}")

    if result.groundedness_notes:
        print("\n=== Groundedness ===")
        print(result.groundedness_notes)


def main() -> None:
    rubric_items = load_rubric_items()
    reading_text = load_reading_text()

    print("\nState your argument:")
    argument_text = input("> ").strip()
    argument = StudentArgument(argument_text=argument_text)

    agent = SocraticAgent(rubric_items=rubric_items, reading_text=reading_text)

    for round_num in range(1, ROUNDS + 1):
        question = agent.ask_question(argument, round_num=round_num)
        print(f"\n[{round_num}/{ROUNDS}] {question}")
        response = input("> ").strip()
        argument.rounds.append(SocraticExchange(question=question, response=response))

    result = agent.evaluate(argument)
    print_evaluation(result)


if __name__ == "__main__":
    main()
