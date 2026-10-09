"""GPT vs Gemini same-context smoke test. No web/search/agents.

Requires paid API access for each selected model. Does NOT verify citations,
measure search quality, or calculate dollar cost. Never use fabricated context
as if it were actual company research.
"""

import argparse
import json
import time

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from provider_config import get_provider_config, summarize_usage
from text_utils import readable_text


# Explicitly fictional account information used for both provider calls.
SHARED_CONTEXT = """
Fictional account: Northstar Logistics (NOT a real researched company).
Company notes:
- Operates regional B2B freight brokerage in two unspecified markets.
- Public-facing products in this example: shipment tracking and carrier matching.
- Recently launched a customer portal according to this fictitious brief.
- No verified employee count, revenue, leadership names, cloud vendor,
  hiring details, named competitors or investment data is provided.
Seller-approved hypothetical services:
- offering_1: Customer-support workflow automation
- offering_2: Logistics analytics assessment
"""

SHARED_TASK = (
    "Using ONLY the fictional notes supplied below, write a short account brief. "
    "Clearly distinguish stated information from suggested questions or hypotheses. "
    "Include: company offerings, two sales opportunities matched to approved "
    "services, and at least four important evidence gaps. "
    "Never fill unknown revenue, technology, people or competitor details by guessing.\n\n"
    + SHARED_CONTEXT
)


def compare(provider: str) -> dict:
    cfg = get_provider_config(provider)
    # The same interface and task are used for both providers.
    model = init_chat_model(cfg.model, timeout=60, max_retries=0)
    start = time.perf_counter()
    response = model.invoke(
        [
            {
                "role": "system",
                "content": (
                    "You are a cautious analyst. Do not invent company information. "
                    "The company in this exercise is fictional. Do not search the web."
                ),
            },
            {"role": "user", "content": SHARED_TASK},
        ]
    )
    duration_ms = round((time.perf_counter() - start) * 1000)
    return {
        "provider": cfg.key,
        "model": cfg.model,
        "benchmark_track": "A: identical fictional evidence (no tools or search)",
        "duration_ms": duration_ms,
        "usage": summarize_usage(getattr(response, "usage_metadata", None)),
        "price": None,  # Unknown until provider pricing/billing is checked.
        "answer": readable_text(response.content),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare shared-context GPT/Gemini calls")
    parser.add_argument("--provider", choices=("gpt", "gemini", "both"), default="both")
    args = parser.parse_args()
    load_dotenv()
    selected = ["gpt", "gemini"] if args.provider == "both" else [args.provider]

    # Check credentials first, before making paid calls to either provider.
    try:
        for provider in selected:
            get_provider_config(provider)
    except ValueError as exc:
        parser.error(str(exc))

    print("CAUTION: Paid API calls; fictional input; no web/search; no cost calculation.")
    for provider in selected:
        print(f"\n--- {provider.upper()} ---", flush=True)
        try:
            print(json.dumps(compare(provider), indent=2, ensure_ascii=False))
        except Exception as exc:
            # Do not dump raw provider exception strings: they can include request
            # metadata or other details unsuitable for sharing.
            print(json.dumps({
                "provider": provider,
                "failed": True,
                "error_type": type(exc).__name__,
            }, indent=2))


if __name__ == "__main__":
    main()
