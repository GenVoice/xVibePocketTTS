"""Run explicitly with `pytest -m integration`; requires access to the HF model."""

from contextlib import closing

import pytest
import soundfile as sf
import torch

from xvibe_pocket_tts import RussianTTS
from xvibe_pocket_tts.runtime import VOICES

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def tts():
    return RussianTTS(auto_accent=False)


def assert_audio(audio):
    assert audio.ndim == 1
    assert audio.device.type == "cpu"
    assert audio.numel() > 2400
    assert torch.isfinite(audio).all()
    assert audio.abs().max() > 0.001


@pytest.mark.parametrize("voice", VOICES)
def test_builtin_voice(tts, voice):
    assert tts.sample_rate == 24000
    assert_audio(tts.generate("Прив+ет! Э+то пров+ерка р+усской р+ечи.", voice=voice, seed=42))


def test_stream_and_clone(tts, tmp_path):
    with closing(tts.generate_stream("С+ейчас зв+ук поступ+ает по част+ям.", seed=42)) as stream:
        chunks = list(stream)
    assert len(chunks) > 1
    audio = torch.cat(chunks)
    assert_audio(audio)
    reference = tmp_path / "reference.wav"
    sf.write(reference, audio.numpy(), tts.sample_rate)
    assert_audio(tts.generate("Пров+ерка своег+о г+олоса.", voice=reference, seed=42))


def test_real_ruaccent_preserves_manual_stress(tts):
    prepared = tts.prepare_text("Ст+арый з+амок закрывает замок.", auto_accent=True)
    assert "Ста́рый за́мок" in prepared
    assert "POCKETTTSMANUALSTRESS" not in prepared
    assert "+" not in prepared
    assert_audio(tts.generate(prepared, auto_accent=False, seed=42))
