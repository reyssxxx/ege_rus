"""Скрипт для поиска проблемных wrong_options в JSON файлах."""

import json
from pathlib import Path


def find_potential_issues():
    data_dir = Path(__file__).parent.parent / "data"
    
    for f in sorted(data_dir.glob("task_*.json")):
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        
        task_num = data.get("task_number", "?")
        
        for subcat in data.get("subcategories", []):
            subcat_name = subcat.get("name", "???")
            
            # Собираем все correct_answer для этого subcategory
            all_correct = set()
            for q in subcat.get("questions", []):
                all_correct.add(q["correct_answer"])
            
            # Проверяем каждый вопрос
            for q in subcat.get("questions", []):
                word = q["word_display"]
                correct = q["correct_answer"]
                wrongs = q.get("wrong_options", [])
                
                # Проблема 1: wrong_options содержит correct_answer
                if correct in wrongs:
                    print(f"[{task_num}] {subcat_name}: {word} — correct_answer '{correct}' дублируется в wrong_options!")
                
                # Проблема 2: wrong_options > 2 (не влезет в клавиатуру)
                if len(wrongs) > 2:
                    print(f"[{task_num}] {subcat_name}: {word} — {len(wrongs)} wrong_options (макс 2)!")
                
                # Проблема 3: wrong_options содержит букву, которая не встречается как correct_answer ни в одном слове этого subcategory
                for w in wrongs:
                    if w not in all_correct and len(w) == 1:
                        print(f"[{task_num}] {subcat_name}: {word} — wrong_option '{w}' не встречается как correct_answer в других словах (возможно нелогичен)")


if __name__ == "__main__":
    find_potential_issues()
