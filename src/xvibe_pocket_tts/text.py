"""Russian text preparation for xVibePocketTTS."""

import re
import unicodedata
from typing import Protocol

COMBINING_ACUTE = "\u0301"
MAX_TEXT_CHARS = 600  # Local demo limit; the Python API accepts longer text.
RUSSIAN_VOWELS = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"

_PREFIX_STRESS = re.compile(rf"\+([{RUSSIAN_VOWELS}])")
_SUFFIX_STRESS = re.compile(rf"([{RUSSIAN_VOWELS}]){COMBINING_ACUTE}")
_PREFIX_YO_STRESS = re.compile(r"\+([ёЁ])")
_SUFFIX_YO_STRESS = re.compile(rf"([ёЁ]){COMBINING_ACUTE}")
_MANUAL_STRESS_PLACEHOLDER_PREFIX = "POCKETTTSMANUALSTRESS"

# RUAccent otherwise normalizes away U+0301 and recomputes the word. We use this
# pattern to temporarily protect an explicitly stressed word.
MANUAL_STRESS_SKIP_REGEX = rf"(?iu:(?<![а-яё])[а-яё]+{COMBINING_ACUTE}[а-яё]*(?![а-яё]))"
RUACCENT_SKIP_REGEX = r"[^\w\s]"


class Accentizer(Protocol):
    def process_all(self, text: str, skip_regex: str | None = None) -> str: ...


def to_model_stress_notation(text: str) -> str:
    """Convert the user-facing ``+о`` notation to the model's U+0301 form."""

    normalized = unicodedata.normalize("NFC", text)
    # Ё is inherently stressed in Russian, so an additional mark is redundant
    # and can create an out-of-distribution tokenizer sequence.
    normalized = _PREFIX_YO_STRESS.sub(r"\1", normalized)
    normalized = _SUFFIX_YO_STRESS.sub(r"\1", normalized)
    normalized = _PREFIX_STRESS.sub(rf"\1{COMBINING_ACUTE}", normalized)
    return unicodedata.normalize("NFC", normalized)


def to_display_stress_notation(text: str) -> str:
    """Convert either supported stress notation to ``+о`` for the demo UI."""

    normalized = to_model_stress_notation(text)
    return _SUFFIX_STRESS.sub(r"+\1", normalized)


def _protect_manual_stress(text: str) -> tuple[str, dict[str, str]]:
    """Hide manually stressed words from RUAccent without consuming whitespace."""

    protected: dict[str, str] = {}

    def replace(match: re.Match[str]) -> str:
        placeholder = f"{_MANUAL_STRESS_PLACEHOLDER_PREFIX}{len(protected):04d}TOKEN"
        protected[placeholder] = match.group(0)
        return placeholder

    return re.sub(MANUAL_STRESS_SKIP_REGEX, replace, text), protected


def _restore_manual_stress(text: str, protected: dict[str, str]) -> str:
    for placeholder, word in protected.items():
        text, replacements = re.subn(
            re.escape(placeholder),
            lambda _, replacement=word: replacement,
            text,
            count=1,
            flags=re.IGNORECASE,
        )
        if replacements != 1:
            raise ValueError("Не удалось сохранить ручное ударение. Попробуйте изменить текст.")
    return text


def validate_text(text: str, max_chars: int | None = None) -> str:
    if not isinstance(text, str):
        raise TypeError("Текст должен быть строкой.")

    stripped = text.strip()
    if not stripped:
        raise ValueError("Введите текст для синтеза.")
    if max_chars is not None and len(stripped) > max_chars:
        raise ValueError(
            f"Слишком длинный текст: {len(stripped)} символов. Максимум — {max_chars}."
        )
    return stripped


def prepare_russian_text(text: str, *, use_ruaccent: bool, accentizer: Accentizer) -> str:
    """Validate and optionally accent text, returning user-facing ``+о`` marks."""

    # Manual +vowel marks become combining acutes, then their words are replaced
    # by ordinary word-like placeholders. Unlike skip_regex matches, placeholders
    # do not make RUAccent discard spaces between adjacent protected words.
    prepared = to_model_stress_notation(validate_text(text))
    if use_ruaccent:
        prepared, protected = _protect_manual_stress(prepared)
        prepared = accentizer.process_all(prepared, skip_regex=RUACCENT_SKIP_REGEX)
        prepared = _restore_manual_stress(prepared, protected)
    return to_display_stress_notation(prepared)
