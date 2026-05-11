from filepilot.names import clean_filename_stem


def test_clean_filename_removes_noise_and_unsafe_characters():
    assert clean_filename_stem("  Final Report (copy) [FINAL] !! ") == "report"


def test_clean_filename_removes_duplicate_words_but_keeps_numbers():
    assert clean_filename_stem("Invoice Invoice 2024 2024") == "invoice-2024-2024"


def test_clean_filename_falls_back_when_empty():
    assert clean_filename_stem("() [] !!!") == "untitled"

