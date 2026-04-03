"""Parse raw_task09.txt and generate task_09_dictionary.json for the bot.

Each line: "word_with_dots answer_with_CAPS"
For each missing letter (marked by ..), we create a separate question.
"""

import json
import re
import os

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw_task09.txt")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "task_09_dictionary.json")

# Common vowel confusions for generating wrong options
VOWEL_GROUPS = [
    {"а", "о"},
    {"е", "и"},
    {"я", "е"},
    {"ю", "у"},
    {"ы", "и"},
]


def get_wrong_options(correct_letter: str) -> list[str]:
    correct_lower = correct_letter.lower()
    wrongs = set()
    for group in VOWEL_GROUPS:
        if correct_lower in group:
            wrongs.update(group - {correct_lower})
    if not wrongs:
        # Fallback: common vowels
        all_vowels = {"а", "о", "е", "и", "у", "я", "ы"}
        wrongs = all_vowels - {correct_lower}
    # Return 1-2 most plausible wrong options
    priority = ["а", "о", "е", "и", "я", "у", "ы"]
    result = sorted(wrongs, key=lambda x: priority.index(x) if x in priority else 99)
    return result[:2]


def parse_line(line: str):
    """Parse a line like 'аб..туриент абИтуриент' into questions."""
    line = line.strip()
    if not line:
        return []

    # Remove parenthetical notes for matching, but keep for display
    note = ""
    note_match = re.search(r"\(.*?\)", line)

    # Split into display and answer parts
    # The answer starts where we see a word with uppercase letters
    parts = line.split()
    if len(parts) < 2:
        return []

    # Find the split point: first part has "..", second part has uppercase
    display_parts = []
    answer_parts = []
    found_answer = False

    for part in parts:
        if not found_answer and (".." in part or not any(c.isupper() for c in part)):
            display_parts.append(part)
        else:
            found_answer = True
            answer_parts.append(part)

    display_word = " ".join(display_parts)
    answer_word = " ".join(answer_parts)

    if not display_word or not answer_word:
        return []

    # Extract just the core words (without notes) for matching
    display_clean = re.sub(r"\(.*?\)", "", display_word).strip()
    answer_clean = re.sub(r"\(.*?\)", "", answer_word).strip()

    # Find positions of ".." in display and corresponding uppercase letters in answer
    questions = []

    # Walk through both strings to find gaps
    di = 0  # display index
    ai = 0  # answer index

    while di < len(display_clean) and ai < len(answer_clean):
        if display_clean[di] == "." and di + 1 < len(display_clean) and display_clean[di + 1] == ".":
            # Found a gap — the answer character should be uppercase
            correct_letter = answer_clean[ai]
            if correct_letter.isupper():
                correct_lower = correct_letter.lower()
            else:
                correct_lower = correct_letter
                correct_letter = correct_letter.upper()

            # Build word_display with underscore at this position
            # Replace THIS specific ".." with "_", and fill other ".." with their correct letters (lowercase)
            word_display = build_display(display_clean, answer_clean, gap_pos=di)
            wrong = get_wrong_options(correct_lower)

            questions.append({
                "word_display": word_display,
                "correct_answer": correct_lower,
                "wrong_options": wrong,
                "explanation": f"Словарное слово: {answer_clean}.",
            })

            di += 2  # skip both dots
            ai += 1  # skip one answer char

            # Handle case where "...." means two consecutive missing letters
            # Check if next chars are also dots
        else:
            di += 1
            ai += 1

    return questions


def build_display(display: str, answer: str, gap_pos: int) -> str:
    """Build the display word with '_' at gap_pos and other gaps filled in."""
    result = []
    di = 0
    ai = 0

    while di < len(display) and ai < len(answer):
        if display[di] == "." and di + 1 < len(display) and display[di + 1] == ".":
            if di == gap_pos:
                result.append("_")
            else:
                result.append(answer[ai].lower())

            # Check for 4 dots (two consecutive missing letters like "....")
            if di + 2 < len(display) and display[di + 2] == "." and di + 3 < len(display) and display[di + 3] == ".":
                ai += 1
                di += 2
                if di == gap_pos:
                    # This is actually the second gap in a 4-dot sequence
                    result.append("_")
                else:
                    result.append(answer[ai].lower())
                di += 2
                ai += 1
            else:
                di += 2
                ai += 1
        else:
            result.append(display[di])
            di += 1
            ai += 1

    return "".join(result)


def main():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    all_questions = []
    for line in lines:
        qs = parse_line(line)
        all_questions.extend(qs)

    data = {
        "task_number": 9,
        "task_name": "Словарные слова",
        "subcategories": [
            {
                "code": "dictionary",
                "name": "Словарные слова",
                "rule": "Непроверяемые гласные — запомните написание.",
                "questions": all_questions,
            }
        ],
    }

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(all_questions)} questions from {len(lines)} lines")


if __name__ == "__main__":
    main()
