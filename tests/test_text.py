import re

import pytest

from xvibe_pocket_tts.text import (
    COMBINING_ACUTE,
    MANUAL_STRESS_SKIP_REGEX,
    RUACCENT_SKIP_REGEX,
    prepare_russian_text,
    to_display_stress_notation,
    to_model_stress_notation,
)


class FakeAccentizer:
    def __init__(self, result: str):
        self.result = result
        self.calls = []

    def process_all(self, text: str, skip_regex: str | None = None) -> str:
        self.calls.append((text, skip_regex))
        return self.result


class EchoAccentizer(FakeAccentizer):
    def __init__(self):
        super().__init__("")

    def process_all(self, text: str, skip_regex: str | None = None) -> str:
        self.calls.append((text, skip_regex))
        return text


def test_converts_display_notation_to_model_notation():
    assert to_model_stress_notation("зам+ок и з+амок") == "замо́к и за́мок"


def test_converts_model_notation_to_display_notation():
    assert to_display_stress_notation("замо́к и за́мок") == "зам+ок и з+амок"


def test_yo_never_gets_an_extra_stress_mark():
    assert to_model_stress_notation("тяж+ёлый и надё́жный") == "тяжёлый и надёжный"
    assert to_display_stress_notation("тяж+ёлый и надё́жный") == "тяжёлый и надёжный"


def test_literal_non_stress_plus_is_preserved():
    assert to_model_stress_notation("C++ и 2+2") == "C++ и 2+2"


def test_literal_plus_is_preserved_by_ruaccent():
    accentizer = FakeAccentizer("два + два")
    result = prepare_russian_text("два + два", use_ruaccent=True, accentizer=accentizer)

    assert result == "два + два"
    assert accentizer.calls == [("два + два", RUACCENT_SKIP_REGEX)]


def test_auto_accent_uses_manual_stress_skip_pattern():
    accentizer = FakeAccentizer("POCKETTTSMANUALSTRESS0000TOKEN закрывает зам+ок")
    result = prepare_russian_text(
        "з+амок закрывает замок", use_ruaccent=True, accentizer=accentizer
    )

    assert result == "з+амок закрывает зам+ок"
    assert accentizer.calls == [
        ("POCKETTTSMANUALSTRESS0000TOKEN закрывает замок", RUACCENT_SKIP_REGEX)
    ]
    assert re.search(MANUAL_STRESS_SKIP_REGEX, f"за{COMBINING_ACUTE}мок")


def test_adjacent_manually_stressed_words_keep_spaces():
    accentizer = EchoAccentizer()
    text = "Ст+арый з+амок ст+оит д+орого, а дв+ерь закрыв+ает зам+ок."

    assert prepare_russian_text(text, use_ruaccent=True, accentizer=accentizer) == text
    sent_to_ruaccent = accentizer.calls[0][0]
    assert "TOKEN POCKETTTSMANUALSTRESS" in sent_to_ruaccent


def test_disabled_auto_accent_keeps_manual_stress_in_display_notation():
    accentizer = FakeAccentizer("unused")
    assert prepare_russian_text("  з+амок  ", use_ruaccent=False, accentizer=accentizer) == "з+амок"
    assert accentizer.calls == []


def test_legacy_acute_input_is_shown_as_plus():
    accentizer = FakeAccentizer("unused")
    assert prepare_russian_text("за́мок", use_ruaccent=False, accentizer=accentizer) == "з+амок"


@pytest.mark.parametrize("text", ["", "   "])
def test_rejects_invalid_text(text):
    with pytest.raises(ValueError):
        prepare_russian_text(text, use_ruaccent=False, accentizer=FakeAccentizer("unused"))


def test_api_accepts_long_text():
    text = "Привет, мир. " * 100
    assert (
        prepare_russian_text(text, use_ruaccent=False, accentizer=FakeAccentizer(""))
        == text.strip()
    )


def test_missing_manual_stress_placeholder_fails_instead_of_silently_changing_stress():
    with pytest.raises(ValueError, match="ручное ударение"):
        prepare_russian_text("з+амок", use_ruaccent=True, accentizer=FakeAccentizer("замок"))
