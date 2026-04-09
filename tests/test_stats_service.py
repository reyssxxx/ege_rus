from services.stats_service import progress_bar


def test_progress_bar_full():
    bar = progress_bar(10, 10, 10)
    assert "▓" * 10 in bar
    assert "100%" in bar


def test_progress_bar_empty():
    bar = progress_bar(0, 10, 10)
    assert "░" * 10 in bar
    assert "0%" in bar


def test_progress_bar_zero_total():
    bar = progress_bar(0, 0, 10)
    assert "░" * 10 in bar
    assert "—" in bar


def test_progress_bar_half():
    bar = progress_bar(5, 10, 10)
    assert "50%" in bar
