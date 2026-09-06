"""Local demo with a shared, serialized model instance."""

import gradio as gr
import soundfile as sf

from xvibe_pocket_tts import RussianTTS
from xvibe_pocket_tts.runtime import DEFAULT_VOICE
from xvibe_pocket_tts.text import MAX_TEXT_CHARS, to_display_stress_notation, validate_text

VOICE_LABELS = [
    ("Глубокий мужской", "male_deep"),
    ("Мягкий женский", "female_silky"),
    ("Уверенный мужской", "male_authoritative"),
]


def create_demo(**runtime_options) -> gr.Blocks:
    tts = RussianTTS(**runtime_options)

    def prepare(text, automatic):
        try:
            text = validate_text(text, max_chars=MAX_TEXT_CHARS)
            return to_display_stress_notation(tts.prepare_text(text, auto_accent=automatic))
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc

    def synthesize(text, automatic, voice, reference, seed):
        prepared = prepare(text, automatic)
        if reference:
            try:
                info = sf.info(reference)
                if not 1 <= info.duration <= 30:
                    raise ValueError("Голосовой референс должен длиться от 1 до 30 секунд.")
            except (ValueError, RuntimeError) as exc:
                raise gr.Error(str(exc)) from exc
        audio = tts.generate(prepared, voice=reference or voice, auto_accent=False, seed=int(seed))
        return prepared, (tts.sample_rate, audio.numpy())

    with gr.Blocks(title="xVibePocketTTS") as demo:
        gr.Markdown(
            "# xVibePocketTTS\n"
            "Full fine-tune Pocket TTS на русской речи. "
            "[xVibeNot](https://t.me/xVibeNot)\n\n"
            "Выберите готовый голос или загрузите свой образец. "
            "Ручные ударения `з+амок` и `зам+ок` имеют приоритет над автоматическими."
        )
        with gr.Row():
            with gr.Column(scale=2):
                text = gr.Textbox(
                    label=f"Русский текст, до {MAX_TEXT_CHARS} символов",
                    value="Ст+арый з+амок ст+оит д+орого, а дв+ерь закрыв+ает зам+ок.",
                    lines=5,
                )
                automatic = gr.Checkbox(
                    label="Автоматические ударения RUAccent", value=tts.auto_accent
                )
                prepared = gr.Textbox(label="Текст с ударениями", interactive=False, lines=4)
            with gr.Column():
                voice = gr.Dropdown(choices=VOICE_LABELS, value=DEFAULT_VOICE, label="Голос")
                reference = gr.Audio(
                    label="Свой голос — 1–30 секунд (приоритет над готовым)",
                    sources=["upload", "microphone"],
                    type="filepath",
                )
                seed = gr.Number(value=42, precision=0, label="Seed")
        with gr.Row():
            preview = gr.Button("Проверить ударения")
            generate = gr.Button("Синтезировать", variant="primary")
        audio = gr.Audio(label="Результат")
        preview.click(
            prepare, [text, automatic], prepared, concurrency_id="tts", concurrency_limit=1
        )
        generate.click(
            synthesize,
            [text, automatic, voice, reference, seed],
            [prepared, audio],
            concurrency_id="tts",
            concurrency_limit=1,
        )
        gr.Markdown("[GenVoice](https://genvoice.ru/?utm_source=github)")
    return demo.queue(default_concurrency_limit=1, max_size=8)
