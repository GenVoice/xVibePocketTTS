"""Small Russian runtime without modifying the installed Pocket TTS package."""

import threading
from collections.abc import Iterator
from pathlib import Path

import torch
from pocket_tts import TTSModel

from xvibe_pocket_tts.text import prepare_russian_text, to_model_stress_notation

MODEL_REPO = "genvoice/xVibePocketTTS"
ASSET_REVISION = "v0.1.0"
CONFIG = Path(__file__).parent / "config" / "russian.yaml"
VOICES = {
    "male_deep": "voice_3_male_deep.safetensors",
    "female_silky": "voice_2_female_silky.safetensors",
    "male_authoritative": "voice_1_male_authoritative.safetensors",
}
DEFAULT_VOICE = "male_deep"


class RussianTTS:
    """Load once and reuse; requests on one instance are serialized.

    Audio is a mono CPU tensor at ``sample_rate`` Hz, including when using CUDA.
    Streaming holds the instance lock until the iterator is exhausted or closed.
    """

    def __init__(
        self,
        *,
        device: str = "cpu",
        temperature: float = 0.5,
        eos_threshold: float = -1.0,
        auto_accent: bool = True,
    ):
        if device not in ("cpu", "cuda"):
            raise ValueError("Устройство должно быть cpu или cuda.")
        if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA недоступна. Установите совместимый PyTorch или выберите cpu.")
        self.model = TTSModel.load_model(
            config=CONFIG, temp=temperature, eos_threshold=eos_threshold
        ).to(device)
        self.model.eval()
        self.sample_rate = self.model.sample_rate
        self.auto_accent = auto_accent
        self._accentizer = None
        self._lock = threading.RLock()

    def prepare_text(self, text: str, *, auto_accent: bool | None = None) -> str:
        """Return model-ready text; explicit +vowel / U+0301 stress takes precedence."""
        enabled = self.auto_accent if auto_accent is None else auto_accent
        with self._lock:
            if enabled and self._accentizer is None:
                from xvibe_pocket_tts.accent import load_ruaccent

                self._accentizer = load_ruaccent()
            return to_model_stress_notation(
                prepare_russian_text(text, use_ruaccent=enabled, accentizer=self._accentizer)
            )

    def _voice_state(self, voice: str | Path) -> dict:
        if str(voice) in VOICES:
            source = f"hf://{MODEL_REPO}/voices/{VOICES[str(voice)]}@{ASSET_REVISION}"
        else:
            source = Path(voice).expanduser()
            if not source.is_file():
                raise ValueError(
                    f"Неизвестный голос или файл: {voice}. Голоса: {', '.join(VOICES)}"
                )
        return self.model.get_state_for_audio_prompt(source)

    def generate_stream(
        self,
        text: str,
        *,
        voice: str | Path = DEFAULT_VOICE,
        auto_accent: bool | None = None,
        seed: int | None = None,
    ) -> Iterator[torch.Tensor]:
        """Yield mono float32 PCM chunks on CPU. Close the iterator if stopping early."""
        with self._lock:
            prepared = self.prepare_text(text, auto_accent=auto_accent)
            state = self._voice_state(voice)
            if seed is not None:
                torch.manual_seed(seed)
            for chunk in self.model.generate_audio_stream(state, prepared, copy_state=True):
                yield chunk.detach().float().cpu()

    def generate(
        self,
        text: str,
        *,
        voice: str | Path = DEFAULT_VOICE,
        auto_accent: bool | None = None,
        seed: int | None = None,
    ) -> torch.Tensor:
        """Generate the complete waveform, preserving the cached voice state."""
        return torch.cat(
            list(self.generate_stream(text, voice=voice, auto_accent=auto_accent, seed=seed))
        )
