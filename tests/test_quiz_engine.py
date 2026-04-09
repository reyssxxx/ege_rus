from services.quiz_engine import build_options, check_answer


def test_build_options_contains_all(sample_question):
    options = build_options(sample_question)
    assert sample_question.correct_answer in options
    for wrong in sample_question.wrong_options:
        assert wrong in options
    assert len(options) == 3  # 1 correct + 2 wrong


def test_build_options_shuffles(sample_question):
    """Over many runs, options should not always be in the same order."""
    results = set()
    for _ in range(50):
        options = build_options(sample_question)
        results.add(tuple(options))
    assert len(results) > 1  # at least 2 different orderings


def test_check_answer_correct(sample_question):
    assert check_answer(sample_question, sample_question.correct_answer) is True


def test_check_answer_wrong(sample_question):
    assert check_answer(sample_question, sample_question.wrong_options[0]) is False
