# Сторонние компоненты

`examples/voices/male_deep.wav` — синтетический голосовой референс GenVoice, добавленный для примера клонирования из WAV.

- **Pocket TTS 3.0.2**, Kyutai: https://github.com/kyutai-labs/pocket-tts — устанавливается отдельной зависимостью, код MIT. Конфигурация архитектуры `src/xvibe_pocket_tts/config/russian.yaml` адаптирована из Pocket TTS; текст исходной лицензии приведён ниже.
- **RUAccent 1.5.8.3**: https://github.com/Den4ikAI/ruaccent — устанавливается отдельной зависимостью. Модели, словари и движок правил загружаются из https://huggingface.co/ruaccent/accentuator с закреплённой ревизии `b78ae5ea1e62beaf138bed1865cd8c3b0b5ca855`. Используется конфигурация `turbo3.1`, CPU, словари и полный режим обработки.
- **Веса, русский токенизатор и готовые состояния голосов** загружаются из https://huggingface.co/genvoice/xVibePocketTTS с ревизии `v0.1.0`. В Git-репозитории их нет. Базовая модель: https://huggingface.co/kyutai/pocket-tts, базовые веса заявлены под CC BY 4.0.

RUAccent 1.5.8.3 ожидает дополнительные модули `koziev` внутри установленного пакета. Загрузчик предварительно получает их с той же закреплённой ревизии. Используйте отдельное виртуальное окружение с доступом на запись; ресурсы остальных моделей сохраняются в пользовательском кэше.

## Pocket TTS — MIT

Permission is hereby granted, free of charge, to any
person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the
Software without restriction, including without
limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice
shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF
ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
