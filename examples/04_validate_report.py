"""Lesson 4: prove 12-section coverage without making a model call."""

from report_contract import SECTION_KEYS, empty_report


def main() -> None:
    report = empty_report("Example Company")
    print(report.model_dump_json(indent=2))
    print(f"Validated {len(SECTION_KEYS)} required section keys.")
    print("These are NOT RESEARCHED placeholders, not a company report.")


if __name__ == "__main__":
    main()
