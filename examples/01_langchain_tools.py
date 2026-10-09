"""Lesson 1: LangChain model + bounded local tool. No external research."""

import json
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool


@tool
def approved_offerings() -> str:
    """Return the fictional seller's approved offerings catalog."""
    catalog = [
        {"id": "cloud_migration", "name": "Cloud migration assessment"},
        {"id": "support_automation", "name": "Customer-support automation"},
    ]
    return json.dumps(catalog)


def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY in your local .env first.")

    agent = create_agent(
        model=os.getenv("OCTODIG_MODEL", "openai:gpt-5-nano"),
        tools=[approved_offerings],
        system_prompt=(
            "You are a sales research assistant. Only describe approved "
            "offerings returned by the catalog tool. Never invent an offering. "
            "This is a fictional catalog and NOT research about a real company."
        ),
    )
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "List our approved offerings and their IDs.",
                }
            ]
        }
    )
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
