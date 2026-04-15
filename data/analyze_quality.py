#!/usr/bin/env python3
import json
import re
import os

files = [
    'task_04_orthoepy.json',
    'task_05_paronyms.json',
    'task_09_dictionary.json',
    'task_09_roots.json',
    'task_10_prefixes.json',
    'task_11_suffixes.json',
    'task_12_verb_endings.json',
    'task_14_spelling.json',
    'task_15_n_nn.json'
]

def get_all_questions(data):
    """Extract all questions from various file structures"""
    questions = []
    if 'subcategories' in data:
        for subcat in data['subcategories']:
            if 'questions' in subcat:
                questions.extend(subcat['questions'])
    elif isinstance(data, list):
        questions = data
    return questions

def is_trivial_explanation(exp):
    """Check if explanation is empty, null, or trivial"""
    if not exp:
        return True
    if exp is None:
        return True
    # Check for very short trivial explanations
    exp_str = str(exp).strip()
    if len(exp_str) == 0:
        return True
    # Pattern like "Правильный ответ: X" is trivial
    if re.match(r'^[Пп]равильн[ый]+ ответ:\s*[А-Яа-я]\.?$', exp_str):
        return True
    if re.match(r'^Correct answer:\s*[A-Za-z]\.?$', exp_str):
        return True
    return False

print("=" * 80)
print("COMPREHENSIVE DATA QUALITY ANALYSIS")
print("=" * 80)

for filename in files:
    filepath = os.path.join('/d/my_projects/ege_bot/data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions = get_all_questions(data)
        total = len(questions)
        
        # Count trivial explanations
        trivial_count = 0
        trivial_samples = []
        illogical_samples = []
        
        for i, q in enumerate(questions):
            explanation = q.get('explanation', '')
            
            if is_trivial_explanation(explanation):
                trivial_count += 1
                if len(trivial_samples) < 5:
                    trivial_samples.append({
                        'idx': i + 1,
                        'question': q.get('word_display') or q.get('question') or str(q)[:50],
                        'explanation': explanation
                    })
            
            # Check wrong options logic
            correct = q.get('correct_answer', '')
            wrong = q.get('wrong_options', [])
            
            # For spelling tasks, check if wrong options test right difficulty
            if filename in ['task_09_roots.json', 'task_09_dictionary.json', 'task_10_prefixes.json', 
                           'task_11_suffixes.json', 'task_12_verb_endings.json', 'task_14_spelling.json']:
                # Simple check: if correct and wrong options are very similar
                if correct and wrong and len(wrong) > 0:
                    # Check if variations test the intended difficulty
                    if len(illogical_samples) < 5:
                        # Log for manual review
                        q_display = q.get('word_display') or q.get('question') or ''
                        illogical_samples.append({
                            'idx': i + 1,
                            'question': q_display[:60],
                            'correct': correct,
                            'wrong_options': wrong[:3]
                        })
        
        print(f"\n{'='*80}")
        print(f"FILE: {filename}")
        print(f"Total questions: {total}")
        print(f"Questions with trivial/missing explanations: {trivial_count} ({100*trivial_count//total}%)")
        
        print(f"\nSample questions with bad/missing explanations (up to 5):")
        for sample in trivial_samples[:5]:
            exp_display = sample['explanation'][:50] if sample['explanation'] else "(empty)"
            print(f"  Q{sample['idx']}: {sample['question']}")
            print(f"    Explanation: '{exp_display}'")
        
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"FILE: {filename}")
        print(f"ERROR: {e}")

