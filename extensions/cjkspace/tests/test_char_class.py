"""Unit tests for ``is_cjk_char`` — the character class driving removal.

Removal only happens when both sides of a whitespace run are CJK. These
tests pin the class: wide/fullwidth letters, digits and punctuation are
CJK; ASCII, Latin, halfwidth/ambiguous punctuation (— “” ·) and wide
symbols/emoji are not.
"""

from __future__ import annotations

import pytest

from extensions.cjkspace import is_cjk_char


@pytest.mark.parametrize(
    "char",
    [
        "中",  # CJK ideograph (W)
        "日",  # CJK ideograph (W)
        "한",  # hangul syllable (W)
        "あ",  # hiragana (W)
        "。",  # ideographic full stop (W, Po)
        "、",  # ideographic comma (W, Po)
        "！",  # fullwidth exclamation mark (F, Po)
        "？",  # fullwidth question mark (F, Po)
        "（",  # fullwidth left paren (F, Ps)
        "）",  # fullwidth right paren (F, Pe)
        "「",  # left corner bracket (W, Ps)
        "」",  # right corner bracket (W, Pe)
        "【",  # left black lenticular bracket (W, Ps)
        "１",  # fullwidth digit one (F, Nd)
        "％",  # fullwidth percent sign (F, Po)
        "，",  # fullwidth comma (F, Po)
        # Ambiguous-width punctuation used as CJK punctuation.
        "—",  # em dash (A, Pd): ——
        "–",  # en dash (A, Pd)
        "…",  # horizontal ellipsis (A, Po): ……
        "“",  # left double quotation mark (A, Pi)
        "”",  # right double quotation mark (A, Pf)
        "·",  # middle dot (A, Po)
    ],
)
def test_cjk_characters(char):
    assert is_cjk_char(char)


@pytest.mark.parametrize(
    "char",
    [
        "",
        "A",
        "z",
        "0",
        " ",
        ",",  # ASCII comma
        "é",  # ambiguous-width letter: European prose
        "α",  # ambiguous-width Greek letter
        "Ж",  # ambiguous-width Cyrillic letter
        "😀",  # wide, but a symbol (So), not text
        "→",  # arrow: a symbol
        "©",  # ambiguous-width symbol
        "\u3000",  # ideographic space: spacing (Zs), handled as whitespace
    ],
)
def test_non_cjk_characters(char):
    assert not is_cjk_char(char)
