from unittest.mock import Mock

import pytest
import torch

from xvibe_pocket_tts import RussianTTS
from xvibe_pocket_tts.runtime import ASSET_REVISION, TTSModel


@pytest.fixture
def runtime(monkeypatch):
    model = Mock(sample_rate=24000)
    model.to.return_value = model
    model.get_state_for_audio_prompt.return_value = {"voice": "unchanged"}
    model.generate_audio_stream.side_effect = lambda *a, **kw: iter([torch.ones(160)])
    monkeypatch.setattr(TTSModel, "load_model", lambda **kw: model)
    return RussianTTS(auto_accent=False)


def test_canonical_text_reaches_unmodified_upstream(runtime):
    audio = runtime.generate("з+амок и зам+ок", seed=42)
    assert audio.shape == (160,)
    args, kwargs = runtime.model.generate_audio_stream.call_args
    assert args[1] == "за́мок и замо́к"
    assert kwargs["copy_state"] is True
    assert ASSET_REVISION in runtime.model.get_state_for_audio_prompt.call_args.args[0]


def test_unknown_voice_is_not_silently_replaced(runtime):
    with pytest.raises(ValueError, match="Неизвестный голос"):
        runtime.generate("Привет", voice="missing")


def test_can_generate_again_after_early_stream_close(runtime):
    stream = runtime.generate_stream("Привет")
    next(stream)
    stream.close()
    assert runtime.generate("Ещё раз").numel() == 160


def test_manual_mode_does_not_load_ruaccent(runtime):
    assert runtime.prepare_text("тяж+ёлый з+амок") == "тяжёлый за́мок"
    assert runtime._accentizer is None
