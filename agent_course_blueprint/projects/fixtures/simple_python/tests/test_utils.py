"""Tests for string utilities"""

from string_utils import capitalize_words, reverse_string, count_vowels


def test_capitalize_words():
    assert capitalize_words("hello world") == "Hello World"
    assert capitalize_words("python programming") == "Python Programming"


def test_reverse_string():
    assert reverse_string("hello") == "olleh"
    assert reverse_string("python") == "nohtyp"


def test_count_vowels():
    assert count_vowels("hello") == 2
    assert count_vowels("python") == 1
    assert count_vowels("AEIOU") == 5
