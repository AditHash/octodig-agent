# Benchmark fixtures

These versioned inputs make benchmark runs reproducible without pretending that
live web evidence is static. They contain target instructions and a fictional
seller catalog; they do not contain verified company research.

`companies.json` covers five evaluation profiles: rich public material, medium
public material, ambiguous identity, sparse controlled data, and time-sensitive
research. `seller_offerings.json` is the complete approved catalog for these
fixtures. A generated opportunity may use only that fixture's
`allowed_offering_ids`; otherwise it must be recorded as an unmatched
suggestion.

Validate the corpus before a benchmark:

```bash
uv run python fixtures/benchmark/validate.py
```

For live fixtures, record source snapshots, retrieval dates, model IDs, prompts,
usage, and provider bills in the benchmark artifact. The fictional sparse
fixture must not trigger internet research. The ambiguous fixture may finish
with an unresolved identity and no seller-qualified opportunity.

This corpus is benchmark setup, not a production research dataset.
