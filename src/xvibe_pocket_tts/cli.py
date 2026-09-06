"""Command line entry points."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="xVibePocketTTS — синтез русской речи")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("voices", help="Показать готовые голоса")
    generate = commands.add_parser("generate", help="Сохранить речь в WAV")
    text = generate.add_mutually_exclusive_group(required=True)
    text.add_argument("--text")
    text.add_argument("--text-file", type=Path, help="Текстовый файл UTF-8")
    generate.add_argument("--voice", default="male_deep", help="Имя голоса или путь к аудиофайлу")
    generate.add_argument("--output", type=Path, default=Path("output.wav"))
    generate.add_argument("--seed", type=int)
    serve = commands.add_parser("serve", help="Открыть локальное веб-демо")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=7860)
    for command in (generate, serve):
        command.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
        command.add_argument("--temperature", type=float, default=0.5)
        command.add_argument("--eos-threshold", type=float, default=-1.0)
        command.add_argument("--no-auto-accent", action="store_true")
    args = parser.parse_args()
    if args.command == "voices":
        from xvibe_pocket_tts.runtime import VOICES

        print("\n".join(VOICES))
        return
    if args.command == "serve":
        try:
            from xvibe_pocket_tts.demo import create_demo
        except ImportError as exc:
            parser.error(f"Установите веб-демо: pip install '.[demo]'. {exc}")
        create_demo(
            device=args.device,
            temperature=args.temperature,
            eos_threshold=args.eos_threshold,
            auto_accent=not args.no_auto_accent,
        ).launch(server_name=args.host, server_port=args.port)
        return
    import soundfile as sf

    from xvibe_pocket_tts import RussianTTS

    try:
        text = args.text_file.read_text(encoding="utf-8") if args.text_file else args.text
        tts = RussianTTS(
            device=args.device,
            temperature=args.temperature,
            eos_threshold=args.eos_threshold,
            auto_accent=not args.no_auto_accent,
        )
        audio = tts.generate(text, voice=args.voice, seed=args.seed)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        sf.write(args.output, audio.numpy(), tts.sample_rate, subtype="PCM_16")
        print(f"Сохранено: {args.output} ({audio.numel() / tts.sample_rate:.2f} с)")
    except (ValueError, OSError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
