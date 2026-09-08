"""String manipulation utilities"""


def capitalize_words(text: str) -> str:
    """Capitalize the first letter of each word"""
    return ' '.join(word.capitalize() for word in text.split())


def reverse_string(text: str) -> str:
    """Reverse a string"""
    return text[::-1]


def count_vowels(text: str) -> int:
    """Count the number of vowels in a string"""
    vowels = set('aeiouAEIOU')
    return sum(1 for char in text if char in vowels)
