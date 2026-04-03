"""
Parse qwizlet.txt → 5 JSON files for EGE tasks 4, 9, 10, 14, 15.

Sections in the file (by line number, 0-indexed):
  0-70   → Task 10  (пре/при)
  73-234 → Task 4   (ударения)
  236-613→ Task 14  (слитно/раздельно/дефис)
  615-949→ Task 9   (чередующиеся гласные)
  951-1644→ Task 15 (Н/НН)
  1646+  → Паронимы (skip)
"""
import json, re, os

SRC  = os.path.join(os.path.dirname(__file__), "..", "qwizlet.txt")
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

RU_VOWELS_UP  = "АЕЁИОУЫЭЮЯ"
RU_VOWELS_LO  = "аеёиоуыэюя"

# ─────────────────────────────── helpers ───────────────────────────────

def is_junk(line):
    s = line.strip()
    if not s:                          return True
    if re.match(r'^\d+ / \d+$', s):   return True
    if 'quizlet.com' in s.lower():     return True
    if s.startswith('Изучать'):        return True
    if s.startswith('---') or s.startswith('==='):  return True
    return False

def first_uppercase_vowel(word):
    for i, c in enumerate(word):
        if c in RU_VOWELS_UP or c == 'Ё':
            return i, c.lower()
    return -1, None

# ─────────────────────────────── Task 10 ────────────────────────────────

def parse_task10(lines):
    questions = []
    for raw in lines:
        if is_junk(raw): continue
        line = raw.strip()
        if '..' not in line: continue

        parts = line.split()
        if len(parts) < 2: continue

        display_raw = parts[0]
        answer_raw  = parts[1]

        # correct letter is е or и right after "пр"
        m = re.search(r'[Пп][Рр]([ЕеИи])', answer_raw)
        if not m: continue

        correct = m.group(1).lower()
        wrong   = ['и'] if correct == 'е' else ['е']
        display = display_raw.replace('..', '_')

        questions.append({
            "word_display":   display,
            "correct_answer": correct,
            "wrong_options":  wrong,
            "explanation":    f"{answer_raw}."
        })
    return questions

# ─────────────────────────────── Task 4 ─────────────────────────────────

def stress_variants(correct_word):
    """Generate up to 2 wrong stress placements."""
    base = correct_word.lower()
    vowel_pos = [i for i, c in enumerate(base) if c in RU_VOWELS_LO]
    if len(vowel_pos) <= 1:
        return []
    stress_pos, _ = first_uppercase_vowel(correct_word)
    if stress_pos == -1:
        return []
    variants = []
    for vp in vowel_pos:
        if vp == stress_pos: continue
        v = list(base)
        v[vp] = v[vp].upper()
        variants.append(''.join(v))
    return variants[:2]

def parse_task4(lines):
    questions = []
    for raw in lines:
        if is_junk(raw): continue
        line = raw.strip()
        if not line: continue

        tokens = line.split()
        # Find index of first token that has an uppercase vowel → start of answers
        split = None
        for i, tok in enumerate(tokens):
            clean = tok.strip('.,;:()')
            if any(c in RU_VOWELS_UP or c == 'Ё' for c in clean):
                split = i
                break
        if split is None or split == 0:
            continue

        display_tokens = tokens[:split]
        answer_tokens  = tokens[split:]

        def clean_list(toks):
            result = []
            for t in toks:
                for part in re.split(r'[,;]', t):
                    p = part.strip('.,;:()!')
                    if p: result.append(p)
            return result

        dwords = clean_list(display_tokens)
        awords = [w for w in clean_list(answer_tokens)
                  if any(c in RU_VOWELS_UP or c == 'Ё' for c in w)]

        for dw, aw in zip(dwords, awords):
            dw_lo = dw.lower()
            aw_lo = aw.lower()
            # sanity: first 3 chars of base must match
            if dw_lo.replace('ё', 'е')[:3] != aw_lo.replace('ё', 'е')[:3]:
                continue
            wrong = stress_variants(aw)
            if not wrong:
                continue
            questions.append({
                "word_display":   dw_lo,
                "correct_answer": aw,
                "wrong_options":  wrong,
                "explanation":    f"Правильное ударение: {aw}."
            })

    # deduplicate by word_display
    seen = set()
    deduped = []
    for q in questions:
        if q["word_display"] not in seen:
            seen.add(q["word_display"])
            deduped.append(q)
    return deduped

# ─────────────────────────────── Task 14 ────────────────────────────────

BRACKET_RE = re.compile(r'\(([А-ЯЁа-яёA-Za-z\-]+)\)([А-ЯЁа-яё\-]+)')

def parse_task14(lines):
    questions = []
    for raw in lines:
        if is_junk(raw): continue
        line = raw.strip()
        if not line: continue

        m = BRACKET_RE.search(line)
        if not m: continue

        x = m.group(1)   # part in brackets, e.g. "В", "НА"
        y = m.group(2)   # word after bracket, e.g. "МЕСТО", "БЕГУ"

        x_lo = x.lower()
        y_lo = y.lower()

        slitno = (x_lo + y_lo).upper()
        razd   = (x_lo + ' ' + y_lo).upper()
        defis  = (x_lo + '-' + y_lo).upper()

        # Which form appears in the part AFTER the bracket pattern?
        after = line[m.end():]
        after_lo = after.lower()

        # Check forms (longest first to avoid false substr matches)
        candidates = sorted(
            [(slitno, slitno.lower()),
             (razd,   razd.lower()),
             (defis,  defis.lower())],
            key=lambda t: -len(t[1])
        )
        correct = None
        for form_up, form_lo in candidates:
            if form_lo in after_lo:
                correct = form_up
                break

        if not correct:
            continue

        # Wrong options: all other forms that differ from correct
        all_forms_up = list(dict.fromkeys([slitno, defis, razd]))
        wrong = [f for f in all_forms_up if f != correct][:2]
        if not wrong:
            continue

        # Display: up to 2 context words before + (X)Y + up to 2 words after
        before = line[:m.start()].strip()
        ctx_before = ' '.join(before.split()[-2:]) if before else ''

        after_words = after.strip().split()
        ctx_after_parts = []
        stop_tokens = {slitno.lower(), razd.lower(), defis.lower(),
                       x_lo, y_lo, x_lo+y_lo}
        # Stop ctx_after as soon as we hit a word from before (duplicate half of Quizlet card)
        before_words_lo = {w.strip('.,!?;—-').lower() for w in before.split()}
        for w in after_words[:4]:
            wc = w.strip('.,!?;—-').lower()
            if wc in stop_tokens or wc in before_words_lo: break
            ctx_after_parts.append(w)
            if len(ctx_after_parts) >= 2: break

        display_parts = []
        if ctx_before: display_parts.append(ctx_before)
        display_parts.append(f'({x}){y}')
        display_parts.extend(ctx_after_parts)
        display = ' '.join(display_parts)

        # Explanation: prefer (= ...) pattern, else first parenthetical
        expl_m = re.search(r'\(=\s*([^)]+)\)', after)
        if expl_m:
            explanation = expl_m.group(1).strip()
        else:
            expl_m = re.search(r'\(([^)]{3,80})\)', after)
            explanation = expl_m.group(1).strip() if expl_m else f"Правильное написание: {correct}."

        questions.append({
            "word_display":   display,
            "correct_answer": correct,
            "wrong_options":  wrong,
            "explanation":    explanation
        })

    seen = set()
    deduped = []
    for q in questions:
        key = q["word_display"]
        if key not in seen:
            seen.add(key)
            deduped.append(q)
    return deduped

# ─────────────────────────────── Task 9 ─────────────────────────────────

ROOT_SUBCAT = {
    'БЕР-БИР':      'бер/бир',
    'БЛЕСТ':        'блест/блист',
    'БЛИСТ':        'блест/блист',
    'ДЕР-ДИР':      'дер/дир',
    'ЖЕ':           'жег/жиг',
    'МЕР-МИР':      'мер/мир',
    'ПЕР-ПИР':      'пер/пир',
    'СТЕЛ-СТИЛ':    'стел/стил',
    'ТЕР-ТИР':      'тер/тир',
    'ЧЕТ':          'чет/чит',
    'ЧИТ':          'чет/чит',
    'КАС-КОС':      'кас/кос',
    'А(Я)-ИМ':      'им/ин',
    'А(Я)-ИН':      'им/ин',
    'ЛОЖ-ЛАГ':      'лаг/лож',
    'РОС-РАСТ':     'раст/рос',
    'СКОЧ-СКАК':    'скак/скоч',
    'ГОР-ГАР':      'гор/гар',
    'ТВОР-ТВАР':    'твор/твар',
    'КЛОН-КЛАН':    'клон/клан',
    'ЗОР-ЗАР':      'зор/зар',
    'МАК-МОК':      'мак/мок',
    'РОВН-РАВН':    'ровн/равн',
    'ПЛОВ-ПЛАВ':    'плав/плов',
    'ПЛЫВ':         'плав/плов',
}

def get_subcat9(text):
    for key, val in ROOT_SUBCAT.items():
        if key in text.upper():
            return val
    return 'другие корни'

def merge_task9_entries(lines):
    """Merge multi-line entries. A new entry starts with a word containing '..'"""
    entries = []
    current = []
    for raw in lines:
        if is_junk(raw): continue
        line = raw.strip()
        if not line: continue
        first_word = line.split()[0] if line.split() else ''
        if '..' in first_word or '...' in first_word:
            if current:
                entries.append('\n'.join(current))
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        entries.append('\n'.join(current))
    return entries

def parse_task9(lines):
    entries = merge_task9_entries(lines)
    questions = []

    for entry in entries:
        parts_all = entry.split()
        if not parts_all: continue

        display_raw = parts_all[0]
        if '..' not in display_raw and '...' not in display_raw:
            continue

        # Find answer word: first token after display with uppercase vowel
        answer_raw = None
        rest_idx = 1
        for i, p in enumerate(parts_all[1:], 1):
            clean = p.strip('.,;:()')
            if any(c in RU_VOWELS_UP or c == 'Ё' for c in clean):
                answer_raw = clean
                rest_idx = i + 1
                break

        if not answer_raw: continue

        # Display
        word_display = re.sub(r'\.{2,}', '_', display_raw)

        # Correct letter: first uppercase vowel in answer
        stress_pos, correct = first_uppercase_vowel(answer_raw)
        if not correct: continue

        # Wrong options
        if correct in ('е', 'ё'):  wrong = ['и']
        elif correct == 'и':       wrong = ['е']
        elif correct == 'а':       wrong = ['о']
        elif correct == 'о':       wrong = ['а']
        elif correct == 'ы':       wrong = ['и']
        else:                      wrong = ['е']

        # Explanation
        expl_parts = parts_all[rest_idx:]
        explanation = ' '.join(expl_parts)
        if explanation.startswith(','):
            explanation = explanation[1:].strip()
        # Shorten
        if len(explanation) > 160:
            m = re.search(r'корень с чередованием ([^,\.]+)', explanation, re.IGNORECASE)
            if m:
                explanation = f"Корень с чередованием {m.group(1).strip()}."
            else:
                explanation = f"Правильное написание: {answer_raw}."

        subcategory = get_subcat9(explanation)

        questions.append({
            "word_display":   word_display,
            "correct_answer": correct,
            "wrong_options":  wrong,
            "explanation":    explanation,
            "subcategory":    subcategory,
        })

    seen = set()
    deduped = []
    for q in questions:
        if q["word_display"] not in seen:
            seen.add(q["word_display"])
            deduped.append(q)
    return deduped

# ─────────────────────────────── Task 15 ────────────────────────────────

def merge_task15_entries(lines):
    """Merge multi-line entries. Entry starts with word containing '..'"""
    entries = []
    current = []
    for raw in lines:
        if is_junk(raw): continue
        line = raw.strip()
        if not line: continue
        first_word = line.split()[0] if line.split() else ''
        if '..' in first_word:
            if current:
                entries.append('\n'.join(current))
            current = [line]
        else:
            if current:
                current.append(line)
    if current:
        entries.append('\n'.join(current))
    return entries

def parse_task15(lines):
    entries = merge_task15_entries(lines)
    questions = []

    for entry in entries:
        all_parts = entry.split()
        if not all_parts: continue

        display_raw = all_parts[0]
        if '..' not in display_raw:
            continue

        # Answer word: first word containing НН or isolated Н surrounded by lowercase
        answer_raw = None
        for p in all_parts[1:]:
            clean = p.strip('.,;:()')
            if re.search(r'НН', clean):
                answer_raw = clean
                break
            # Single Н between lowercase letters (not inside a word with uppercase vowel)
            if re.search(r'[а-яё]Н[а-яё]', clean) or re.search(r'Н[а-яё]', clean) or re.search(r'[а-яё]Н$', clean):
                if not any(c in RU_VOWELS_UP for c in clean):  # no other uppercase → Н IS the answer
                    answer_raw = clean
                    break

        if not answer_raw: continue

        # Determine н or нн
        if 'НН' in answer_raw:
            correct = 'нн'
            wrong   = ['н']
        elif 'Н' in answer_raw:
            correct = 'н'
            wrong   = ['нн']
        else:
            continue

        word_display = re.sub(r'\.{2,}', '_', display_raw)

        # Explanation: text in parentheses (possibly spanning multiple lines)
        full_text = ' '.join(all_parts[1:])
        expl_m = re.search(r'\(([^)]{10,})\)', full_text, re.DOTALL)
        if expl_m:
            explanation = re.sub(r'\s+', ' ', expl_m.group(1)).strip()
            if len(explanation) > 180:
                explanation = explanation[:180].rsplit(' ', 1)[0] + '...'
        else:
            explanation = f"Правильное написание: {answer_raw}."

        questions.append({
            "word_display":   word_display,
            "correct_answer": correct,
            "wrong_options":  wrong,
            "explanation":    explanation,
        })

    seen = set()
    deduped = []
    for q in questions:
        if q["word_display"] not in seen:
            seen.add(q["word_display"])
            deduped.append(q)
    return deduped

# ─────────────────────────────── assemble JSONs ─────────────────────────

def build_task9_json(questions):
    """Group by subcategory."""
    groups = {}
    for q in questions:
        sub = q.pop('subcategory')
        groups.setdefault(sub, []).append(q)

    subcategories = []
    for name, qs in sorted(groups.items()):
        subcategories.append({
            "code":      name.replace('/', '_'),
            "name":      name,
            "rule":      "",
            "questions": qs
        })
    return {
        "task_number": 9,
        "task_name":   "Правописание корней (чередующиеся гласные)",
        "subcategories": subcategories
    }

def build_simple_json(task_number, task_name, subcategory_name, questions):
    return {
        "task_number": task_number,
        "task_name":   task_name,
        "subcategories": [{
            "code":      "main",
            "name":      subcategory_name,
            "rule":      "",
            "questions": questions
        }]
    }

# ─────────────────────────────── main ────────────────────────────────────

def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Slice sections (0-indexed)
    task10_lines = lines[0:71]
    task4_lines  = lines[73:235]
    task14_lines = lines[236:614]
    task9_lines  = lines[615:950]
    task15_lines = lines[951:1645]

    # Parse
    q10  = parse_task10(task10_lines)
    q4   = parse_task4(task4_lines)
    q14  = parse_task14(task14_lines)
    q9   = parse_task9(task9_lines)
    q15  = parse_task15(task15_lines)

    print(f"Task  4: {len(q4)} questions")
    print(f"Task  9: {len(q9)} questions")
    print(f"Task 10: {len(q10)} questions")
    print(f"Task 14: {len(q14)} questions")
    print(f"Task 15: {len(q15)} questions")

    # Write JSONs
    def save(path, data):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {os.path.basename(path)}")

    save(os.path.join(DATA, "task_04_orthoepy.json"),
         build_simple_json(4, "Орфоэпия (ударения)", None, q4))

    save(os.path.join(DATA, "task_09_roots.json"),
         build_task9_json(q9))

    save(os.path.join(DATA, "task_10_prefixes.json"),
         build_simple_json(10, "Правописание приставок (пре/при)", "пре/при", q10))

    save(os.path.join(DATA, "task_14_spelling.json"),
         build_simple_json(14, "Слитное, дефисное, раздельное написание", "Наречия и предлоги", q14))

    save(os.path.join(DATA, "task_15_n_nn.json"),
         build_simple_json(15, "Правописание Н/НН", "Н/НН", q15))

    print("Done.")

if __name__ == "__main__":
    main()
