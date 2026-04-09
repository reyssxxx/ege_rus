"""
Fix illogical wrong_options in task_09_dictionary.json.

Replaces implausible vowel alternatives with standard confusion pairs.
Run with --dry-run first to review changes, then without to apply.
"""
import json
import sys

DATA_PATH = "data/task_09_dictionary.json"

# Standard confusion pairs for unstressed Russian vowels
# Key = correct answer, Value = plausible wrong options
PLAUSIBLE_PAIRS = {
    "а": ["о"],
    "о": ["а"],
    "е": ["и"],
    "и": ["е"],
    "я": ["е"],
    "у": ["о"],
    "ю": ["у"],
    "э": ["е"],
}


def fix_wrong_options(data: dict, dry_run: bool = True) -> int:
    changed = 0
    for subcat in data.get("subcategories", []):
        for q in subcat.get("questions", []):
            correct = q["correct_answer"].lower()
            old_wrong = q["wrong_options"]
            plausible = PLAUSIBLE_PAIRS.get(correct, [])

            if not plausible:
                continue

            # Filter wrong options to only plausible ones
            new_wrong = [w for w in old_wrong if w.lower() in plausible]

            # If filtering removed everything, use the plausible pair
            if not new_wrong:
                new_wrong = list(plausible)

            if new_wrong != old_wrong:
                changed += 1
                if dry_run:
                    print(f"  {q['word_display']}: correct={correct}, "
                          f"old={old_wrong} -> new={new_wrong}")
                q["wrong_options"] = new_wrong

    return changed


def main():
    dry_run = "--dry-run" in sys.argv

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_questions = sum(
        len(subcat["questions"])
        for subcat in data.get("subcategories", [])
    )

    print(f"Total questions: {total_questions}")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLY'}\n")

    changed = fix_wrong_options(data, dry_run=dry_run)

    print(f"\nChanged: {changed} questions")

    if not dry_run and changed > 0:
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Written to {DATA_PATH}")


if __name__ == "__main__":
    main()
