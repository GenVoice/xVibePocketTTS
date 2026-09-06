# xVibePocketTTS

**Full fine-tune [Pocket TTS от Kyutai](https://github.com/kyutai-labs/pocket-tts) на русской речи.** Синтезирует речь на CPU, клонирует голос по короткому аудиообразцу и поддерживает явные ударения.

[Демо модели](https://huggingface.co/spaces/Brakanier/xVibePocketTTS) · [Веса на Hugging Face](https://huggingface.co/genvoice/xVibePocketTTS) · [xVibeNot](https://t.me/xVibeNot)

- Около 90 млн параметров в FlowLM; выходное аудио — 24 кГц, моно.
- Три готовых голоса и клонирование собственного голоса.
- Автоматические ударения через RUAccent и ручная расстановка ударений.
- Локальное веб-демо, командная строка и Python API с потоковой генерацией.
- Работа на CPU; при наличии совместимого PyTorch можно использовать CUDA.

## Установка и первый запуск

Понадобятся Git и [uv](https://docs.astral.sh/uv/getting-started/installation/). Поддерживается Python 3.10–3.13; команда ниже создаст окружение с Python 3.12 и установит зависимости.

```bash
git clone https://github.com/GenVoice/xVibePocketTTS.git
cd xVibePocketTTS
uv sync --python 3.12 --extra demo --frozen
uv run xvibe-tts serve
```

Откройте **http://127.0.0.1:7860**: введите текст, выберите голос и нажмите «Синтезировать». Для своего голоса загрузите или запишите чистый образец длительностью 1–30 секунд.

Чтобы сразу сохранить речь в WAV без веб-интерфейса:

```bash
uv run xvibe-tts generate --text "Привет! Это проверка русской речи." --output output.wav
```

Файл `output.wav` появится в текущей папке. Все команды с `uv run` ниже выполняются из папки репозитория.

При первом запуске автоматически загружаются веса и токенизатор с Hugging Face — около 458 МБ вместе с тремя голосами. При первом запросе с автоматическими ударениями RUAccent отдельно скачивает модели и словари. Поэтому первый запуск дольше последующих; скачанные файлы сохраняются в кэше.

<details>
<summary>Установка через pip</summary>

Из папки склонированного репозитория создайте виртуальное окружение:

```bash
python -m venv .venv
```

Активируйте его: `source .venv/bin/activate` на Linux/macOS или `.venv\Scripts\activate` в Windows cmd.

На Linux сначала установите CPU-сборку PyTorch, затем пакет с веб-демо:

```bash
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install '.[demo]'
xvibe-tts serve
```

На macOS достаточно `python -m pip install '.[demo]'`; на Windows cmd используйте двойные кавычки: `python -m pip install ".[demo]"`. Для Python API и командной строки без веб-демо устанавливайте `python -m pip install .`.

После установки через pip запускайте `xvibe-tts` напрямую, без `uv run`.

</details>

## Голоса

| Название | Значение `--voice` |
| :--- | :--- |
| Глубокий мужской | `male_deep` — по умолчанию |
| Мягкий женский | `female_silky` |
| Уверенный мужской | `male_authoritative` |

```bash
# Готовый голос
uv run xvibe-tts generate --text "Добрый вечер!" --voice female_silky

# Клонирование из WAV — референс уже есть в репозитории
uv run xvibe-tts generate --text "Этот голос клонирован из аудиообразца." --voice examples/voices/male_deep.wav

# Текст из файла UTF-8
uv run xvibe-tts generate --text-file ./text.txt --output ./audio/result.wav
```

В [examples/voices/male_deep.wav](examples/voices/male_deep.wav) лежит исходный синтетический референс голоса `male_deep`: 8,82 секунды, 24 кГц, моно. При передаче WAV модель сама кодирует голос из аудио; `--voice male_deep` загружает готовое состояние голоса. Для своего голоса замените путь на путь к вашему файлу.

Качество клонирования зависит от образца: лучше использовать одного говорящего, без музыки и шума. CLI и Python API также принимают файлы состояния голоса `.safetensors`, экспортированные для этих же весов.

## Ударения

RUAccent включён по умолчанию. Для ручного ударения поставьте `+` **перед гласной**: `з+амок` или `зам+ок`. Также поддерживается знак U+0301 после гласной: `за́мок`. Ручное ударение имеет приоритет над автоматическим; над `ё` дополнительный знак не нужен.

```bash
uv run xvibe-tts generate --text "Ст+арый з+амок закрыт на зам+ок."
```

Чтобы отключить RUAccent, добавьте `--no-auto-accent`. Модель продолжит учитывать заданные вручную ударения.

## Python API

После установки пакета сохраните пример в `example.py` и выполните `uv run python example.py`:

```python
import soundfile as sf
from xvibe_pocket_tts import RussianTTS

tts = RussianTTS()
audio = tts.generate("Привет! Это проверка русской речи.", voice="male_deep")
sf.write("output.wav", audio.numpy(), tts.sample_rate)
```

Клонирование из WAV на примере приложенного референса:

```python
audio = tts.generate(
    "Этот голос клонирован из аудиообразца.",
    voice="examples/voices/male_deep.wav",
)
sf.write("cloned.wav", audio.numpy(), tts.sample_rate)
```

Для собственного голоса замените путь на путь к вашему аудиофайлу. Создавайте `RussianTTS` один раз и используйте повторно: модель, RUAccent и состояния голосов остаются в памяти. Результат — одномерный CPU-тензор `float32`, 24 кГц, моно.

Ударения можно проверить и отредактировать перед синтезом:

```python
prepared = tts.prepare_text("Ст+арый з+амок закрыт.")
print(prepared)
audio = tts.generate(prepared, auto_accent=False)
```

<details>
<summary>Потоковая генерация</summary>

`generate_stream()` выдаёт аудиофрагменты по мере синтеза. Например, этот код последовательно записывает их в WAV:

```python
from contextlib import closing
import soundfile as sf
from xvibe_pocket_tts import RussianTTS

tts = RussianTTS()
with sf.SoundFile("stream.wav", "w", samplerate=tts.sample_rate, channels=1) as output:
    with closing(tts.generate_stream("Аудио поступает по частям, по мере генерации.")) as chunks:
        for chunk in chunks:
            output.write(chunk.numpy())
```

Фрагменты можно передавать в аудиоплеер или сетевой транспорт. При досрочном завершении закройте итератор. Один экземпляр обрабатывает запросы последовательно; для параллельного синтеза используйте отдельные процессы.

</details>

## Настройки

По умолчанию: CPU, температура `0.5`, EOS `−1`, RUAccent включён.

```bash
uv run xvibe-tts generate --text "Проверка настроек." --temperature 0.5 --eos-threshold -1 --seed 42
```

В Python: `RussianTTS(temperature=0.5, eos_threshold=-1.0, auto_accent=True)`, а seed задаётся при генерации: `tts.generate("Привет!", seed=42)`.

Длинные тексты движок делит на фрагменты. Ограничение 600 символов относится только к веб-демо. После первой загрузки ресурсов можно работать без сети, установив переменные окружения `HF_HUB_OFFLINE=1` и `TRANSFORMERS_OFFLINE=1`.

<details>
<summary>Запуск на GPU</summary>

Для CUDA создайте отдельное виртуальное окружение, установите совместимую с вашим драйвером CUDA-сборку PyTorch, затем выполните `python -m pip install '.[demo]'` из папки репозитория.

```bash
xvibe-tts generate --device cuda --text "Проверка синтеза на видеокарте."
xvibe-tts serve --device cuda
```

В Python: `RussianTTS(device="cuda")`. RUAccent остаётся на CPU, итоговое аудио также возвращается на CPU.

Для этого окружения используйте команды напрямую: `uv sync` проекта выбирает CPU-сборку PyTorch на Linux и Windows.

</details>

## Скорость и качество

| Оборудование | RTF ↓ | Скорость ↑ | Первый аудиофрагмент ↓ |
| :--- | :--- | :--- | :--- |
| Ryzen 7 3700X | 0,412 | 2,42× реального времени | ≈193 мс |
| RTX 3090 | 0,138 | 7,26× реального времени | ≈37,5 мс |

Замеры русского runtime: `step80000`, FP32, batch 1, температура `0.5`, EOS `−1`. Один текст длительностью около 29 секунд, один мужской референс; медианы пяти повторов после прогрева. Загрузка модели, подготовка голоса и RUAccent в эти значения не входят. RTF — отношение времени синтеза к длительности аудио; чем меньше, тем быстрее.

Некоторые голоса и отдельные слова могут звучать неудачно; ошибки произношения и обрывы окончаний возможны. Подробности обучения и оценки — в [карточке модели](https://huggingface.co/genvoice/xVibePocketTTS).

<details>
<summary>Устройство пакета и разработка</summary>

Этот репозиторий содержит пакет `xvibe-pocket-tts`: русскую конфигурацию, обработку ударений, CLI и веб-демо. Движок `pocket-tts==3.0.2` устанавливается из PyPI отдельной зависимостью. Веса, токенизатор и голоса загружаются с HF; версии ресурсов закреплены. В `uv.lock` сохранены версии зависимостей. Проверено на Linux, Python 3.12, CPU.

```bash
uv sync --extra demo --frozen
uv run ruff check .
uv run pytest -m 'not integration'
# Проверка с загрузкой весов и реальным синтезом
uv run pytest -m integration
uv build
```

CI проверяет код, тесты без загрузки модели и сборку пакета.

</details>

## Благодарности и лицензия

Спасибо [Kyutai](https://huggingface.co/kyutai) за [Pocket TTS](https://github.com/kyutai-labs/pocket-tts), [RUAccent](https://github.com/Den4ikAI/ruaccent) за обработку ударений, [ESpeech](https://huggingface.co/ESpeech) и [Lab260](https://huggingface.co/lab260) за работу над русскоязычными речевыми данными.

Код этого репозитория — [MIT](LICENSE). Сведения о сторонних компонентах — в [NOTICE.md](NOTICE.md). Базовые веса Kyutai Pocket TTS заявлены под CC BY 4.0; лицензия кода не заменяет условия использования весов и других ресурсов.

[GenVoice](https://genvoice.ru/?utm_source=github)
