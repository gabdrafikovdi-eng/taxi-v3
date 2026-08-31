# speech-service

Микросервис распознавания и синтеза речи для голосового бота такси.

- **STT** — [GigaAM](https://github.com/salute-developers/GigaAM) **v2 / v3 / multilingual**
  через единый ASR-протокол; production-модель выбирается настройкой `STT_MODEL`
  (GPU в проде, CPU для локальных тестов);
- **TTS** — [edge-tts](https://github.com/rany2/edge-tts) (облачный Microsoft, без локальных весов);
- **VAD** — [Silero VAD](https://github.com/snakers4/silero-vad) (CPU);
- Аудио-конвертация G.711 µ-law/A-law (GoIP) ↔ PCM 16 кГц 16 бит;
- JSON-логирование через `structlog`; конфиг через `pydantic-settings`.

Сервис слушает `0.0.0.0:8001` (по умолчанию). Основной бэкенд
обращается к нему по HTTP, например `http://192.168.1.100:8001`.

## Архитектура STT

```text
app/stt/
├── protocols.py            # ASR-протокол (единый интерфейс транскрипции)
├── registry.py             # ЕДИНСТВЕННОЕ место со списком моделей (MODEL_REGISTRY)
├── factory.py              # Создание модели по ключу + выбор устройства
├── client.py               # STTClient: PCM16 → 16 kHz WAV → ASR (без if/elif по моделям)
├── benchmark.py            # Последовательный benchmark: load → infer → unload
└── models/
    ├── gigaam_v2.py        # адаптер GigaAM v2 (ctc/rnnt)
    ├── gigaam_v3.py        # адаптер GigaAM v3 (ctc/rnnt/e2e_*)
    └── gigaam_multilingual.py

audio → decode (G.711/WAV) → PCM16 → 16 kHz → VAD (1 раз) → ASR-модель
```

Реестр моделей (порядок = порядок benchmark):

| Ключ (`STT_MODEL`) | GigaAM ID | Семейство |
|---|---|---|
| `gigaam_v2_ctc` | `v2_ctc` | v2 |
| `gigaam_v2_rnnt` | `v2_rnnt` | v2 |
| `gigaam_v3_ctc` | `v3_ctc` | v3 |
| `gigaam_v3_rnnt` | `v3_rnnt` | v3 |
| `gigaam_v3_e2e_ctc` | `v3_e2e_ctc` | v3 |
| `gigaam_v3_e2e_rnnt` | `v3_e2e_rnnt` | v3 |
| `gigaam_multilingual_ctc` | `multilingual_ctc` | multilingual |
| `gigaam_multilingual_large_ctc` | `multilingual_large_ctc` | multilingual |

Принимаются также старые имена (`rnnt`, `v3_rnnt`, `gigaam-v2-ctc`, …) —
см. `LEGACY_ALIASES` в `registry.py`. SSL/Emo-модели GigaAM не являются
ASR (у них нет `transcribe`) и в реестр транскрипции не включены.

> Библиотека `gigaam` ставится из master-ветки GitHub (см. `pyproject.toml`):
> PyPI-релиз 0.1.0 не содержит v3/multilingual моделей. Фактический API
> проверен по установленной версии (`gigaam.load_model`, `model.transcribe(audio_path)`).

## Запуск локально (CPU, Mac M1/M2)

```bash
cd speech-service
uv venv --python 3.11 .venv
source .venv/bin/activate
pip install -e .
STT_DEVICE=cpu uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Или через `uv`:

```bash
cd speech-service
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

> При первом старте выбранная GigaAM-модель и Silero VAD докачают веса
> в `~/.cache`. В production загружается **только одна** модель — та,
> что указана в `STT_MODEL` (Apple M2 / 8 GB unified memory: держите
> `STT_DEVICE=cpu`).

## Запуск в Docker с GPU

```bash
docker build -t speech-service -f speech-service/Dockerfile speech-service
docker run --rm --gpus all -p 8001:8001 \
  -e STT_DEVICE=cuda:0 \
  -v ~/.cache:/root/.cache \
  speech-service
```

Если GPU на хосте нет (`nvidia-smi` отсутствует), сервис всё равно
стартует: при `STT_FALLBACK_TO_CPU=true` GigaAM загрузится на CPU,
`/health` вернёт `"device": "cpu"`.

## Конфигурация

Все настройки — через переменные окружения или файл `.env`
(образец: [`.env.example`](.env.example)).

| Переменная | По умолчанию | Описание |
|---|---|---|
| `STT_MODEL` | `gigaam_v3_rnnt` | Ключ модели из реестра (см. таблицу выше) |
| `STT_LANGUAGE` | `ru` | Язык (метаданные; `gigaam.transcribe` язык не принимает) |
| `STT_DEVICE` | `cpu` | `cuda:0` (GPU-сервер) или `cpu` (Mac) |
| `STT_FALLBACK_TO_CPU` | `true` | Fallback на CPU, если GPU недоступен |
| `STT_BENCHMARK_RELEASES_PRODUCTION` | `false` | Выгружать production-модель на время benchmark (экономия RAM на 8 GB unified memory; следующий production-запрос перезагрузит модель лениво) |
| `TTS_VOICE` | `ru-RU-DmitryNeural` | Голос edge-tts |
| `MAX_AUDIO_DURATION_SEC` | `30` | Лимит длительности аудио на STT |
| `LOG_LEVEL` | `INFO` | Уровень логов |
| `HOST` / `PORT` | `0.0.0.0` / `8001` | Адрес/порт uvicorn |

## Проверка /health

```bash
curl http://localhost:8001/health
# {"status":"ok","stt_loaded":true,"tts_loaded":true,"gpu_available":false,
#  "stt_model":"gigaam_v3_rnnt","device":"cpu","stt_reloadable":false,
#  "available_benchmark_models":["gigaam_v2_ctc", ...]}
```

`stt_reloadable: true` означает, что модель временно выгружена benchmark'ом
(при `STT_BENCHMARK_RELEASES_PRODUCTION=true`) и будет перезагружена лениво
при первом же production-запросе.

## API

### POST /api/v1/transcribe — аудио → текст (production)

Производственная ручка: всегда **одна** модель из `STT_MODEL`.
Принимает `multipart/form-data` (поле `audio`): WAV, G.711 µ-law
(`audio/x-mulaw`, 8 кГц) или A-law (`audio/x-alaw`, 8 кГц).

```bash
curl -F "audio=@speech.wav;type=audio/wav" http://localhost:8001/api/v1/transcribe
curl -F "audio=@g711.ulaw;type=audio/x-mulaw" http://localhost:8001/api/v1/transcribe
```

Ответ `200`:

```json
{"text": "Мне нужна машина на улицу Ленина", "duration_ms": 2400,
 "sample_rate": 16000, "model": "gigaam_v3_rnnt", "inference_time_ms": 640}
```

Ошибки: `400 Empty audio`, `413 Audio too long` (> `MAX_AUDIO_DURATION_SEC`),
`503 STT/VAD models not loaded`.

### POST /api/v1/transcribe/stream — фразовый STT

Псевдо-потоковый режим (не WebSocket): клиент присылает накопленный батч
POST-запросом с `multipart/form-data` (поле `audio`, сырой PCM16 или WAV);
сервис возвращает распознанный текст и `is_final` для каждого запроса.

```bash
ffmpeg -i speech.wav -f s16le -ac 1 -ar 16000 speech.pcm
curl -X POST "http://localhost:8001/api/v1/transcribe/stream?sample_rate=16000" \
  -F "audio=@speech.pcm;type=application/octet-stream"
```

Ответ `200`: `{"text": "...", "is_final": true}`.

### POST /api/v1/benchmark/transcribe — сравнение всех моделей

Исследовательская ручка. Принимает тот же input, что и production.
Аудио декодируется и прогоняется через VAD **один раз**, затем все модели
из реестра запускаются **последовательно**: `load → inference → unload`
(в памяти никогда не больше одной benchmark-модели — рассчитано на
Apple M2 / 8 GB unified memory). Падение одной модели не останавливает
прогон; подробный stack trace попадает только в логи.

Input нормализуется так же, как в production-ручке: µ-law/A-law (8 кГц)
декодируются в PCM16 и **ресемплируются до 16 кГц** до упаковки во
временный WAV — все модели реестра получают один и тот же WAV (16 кГц /
mono / PCM16), байт-в-байт равный тому, что production-путь отдаёт модели
через `STTClient`. Инвариант: одинаковый input + та же модель = одинаковый
текст в production и benchmark (регрессионные тесты:
`tests/test_benchmark_parity.py`, реальный parity на весах GigaAM —
`tests/test_real_models_parity.py`).

```bash
curl -F "audio=@speech.wav;type=audio/wav" \
  http://localhost:8001/api/v1/benchmark/transcribe
```

Ответ `200`:

```json
{
  "duration_ms": 2400,
  "sample_rate": 16000,
  "speech_detected": true,
  "results": [
    {"model": "gigaam_v2_ctc", "text": "...", "load_time_ms": 3100,
     "inference_time_ms": 420, "total_time_ms": 3520, "success": true},
    {"model": "gigaam_v2_rnnt", "text": "...", "load_time_ms": 3400,
     "inference_time_ms": 510, "total_time_ms": 3910, "success": true},
    {"model": "gigaam_v3_e2e_rnnt", "text": "", "load_time_ms": 0,
     "inference_time_ms": 0, "total_time_ms": 0, "success": false,
     "error": "load failed"}
  ]
}
```

`load_time_ms` и `inference_time_ms` измеряются отдельно — загрузка модели
не входит в inference latency. Если VAD не нашёл речи, `speech_detected`
будет `false`, а `results` — пустым.

При `STT_BENCHMARK_RELEASES_PRODUCTION=true` benchmark перед прогоном
выгружает production-модель (в памяти остаётся не больше одной модели
вообще), а после ответа production-ручки лениво перезагружают её
(`stt_production_reloaded` в логах). Обычный startup при этом не меняется.

### POST /api/v1/synthesize — текст → аудио (edge-tts)

```bash
curl -X POST http://localhost:8001/api/v1/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Куда вас подать?", "speaker": "ru-RU-SvetlanaNeural"}' \
  --output answer.wav
```

Ответ `200` — аудио-поток edge-tts. `400 Empty text`,
`503 TTS client not initialized`.

## Тесты

```bash
cd speech-service
.venv/bin/python -m pytest tests -q
```

Покрытие: registry/factory (валидные и legacy-ключи), benchmark runner
(последовательность, разделение load/inference, устойчивость к падению
одной модели), API (health, transcribe, stream, benchmark, synthesize, TTS),
клиентский FSM `test_telephony_mic.py` (одна фраза → один запрос; VAD-события
во время долгого запроса игнорируются; следующая фраза — только после
завершения; ошибки HTTP возвращают в IDLE; короткий шум отбрасывается),
release/lazy-reload production-модели при benchmark,
паритет production/benchmark (`tests/test_benchmark_parity.py`): один и тот
же µ-law/A-law вход → байт-в-байт одинаковый WAV у модели в обоих путях,
свежий адаптер на модель + unload после инференса, результат benchmark не
зависит от загруженной production-модели, `A → unload → B → unload → A`
не меняет результат A, семантика `unload()` адаптера.
Модели в тестах заменяются фейками — веса не загружаются.

Опциональный parity-тест на РЕАЛЬНЫХ весах GigaAM (запускается вручную,
нужны чекпоинты в `~/.cache/gigaam` и ffmpeg):

```bash
SPEECH_SERVICE_REAL_MODELS=1 .venv/bin/python -m pytest tests/test_real_models_parity.py -q
```

Он сравнивает текст production-пути (`STTClient`) и benchmark-пути
(`BenchmarkRunner`) для `v2_ctc`, `v2_rnnt`, `v3_ctc`, `v3_rnnt` на одном WAV
(`debug_last_record.wav`); набор моделей расширяется через
`SPEECH_SERVICE_REAL_MODEL_KEYS=all`.

## Микрофонный тест

`test_telephony_mic.py` имитирует телефонный звонок: запись с микрофона →
Silero VAD → G.711 µ-law 8 кГц → POST в сервис.

```bash
# production endpoint (модель из STT_MODEL)
python test_telephony_mic.py

# benchmark endpoint: одна фраза → результаты всех моделей
python test_telephony_mic.py --benchmark

# полезные флаги
python test_telephony_mic.py --list-devices
python test_telephony_mic.py --device 2 --threshold 0.6 --use-wav \
  --server http://192.168.1.100:8001
```

### Семантика benchmark-режима (`--benchmark`)

Клиент работает как конечный автомат `IDLE → RECORDING → PROCESSING → IDLE`
и ведёт себя **строго последовательно**:

```text
одна запись  →  один HTTP-запрос  →  8 моделей последовательно  →  8 результатов
```

* пока benchmark-запрос выполняется (это может занимать минуты на CPU),
  аудио-callback отбрасывает чанки **без запуска VAD**: ни новых
  «ОБНАРУЖЕНА РЕЧЬ», ни новых записей, ни параллельных запросов;
* следующая фраза может быть записана только после полного завершения
  предыдущего benchmark (получен HTTP-ответ и выведен отчёт);
* скрытое состояние Silero VAD сбрасывается при старте записи и при
  возврате в ожидание — «залипшая» после паузы LSTM не даёт ложных
  срабатываний;
* короткий шум (щелчок клавиатуры и т.п.) отбрасывается: фраза отправляется
  только если суммарная длительность **речи** ≥ 0.4 с (`MIN_SPEECH_DURATION`),
  тишиной «дотянуть» щелчок до фразы нельзя;
* таймауты: 600 с (production) / 1800 с (benchmark), переопределяются
  флагом `--timeout`.

Пример вывода `--benchmark`:

```text
============================================================
STT BENCHMARK
============================================================
Фраза отправлена.
Audio duration: 2430 ms

------------------------------------------------------------
GigaAM v2 CTC
------------------------------------------------------------
Text:
"Мне нужна машина на улицу Советская дом двадцать три"

Load:      3120 ms
Inference: 420 ms
Total:     3540 ms
...
============================================================
SUMMARY
============================================================
Model                       Inference        Total
------------------------------------------------------------
gigaam_v2_ctc                   420 ms      3540 ms
gigaam_v2_rnnt                  510 ms      3910 ms
```

## Замечания

- Логи пишутся только через `structlog` (JSON), `print()` не используется.
  Ключевые события STT: `stt_model_loaded`, `stt_inference_started/finished/failed`,
  `benchmark_started`, `benchmark_model_started/finished`, `benchmark_finished`.
- GigaAM использует `ffmpeg` для чтения аудио — он должен быть установлен.
- Benchmark при первом запуске докачивает веса всех моделей в `~/.cache/gigaam`
  (суммарно несколько ГБ); `load_time_ms` первого прогона включает скачивание,
  поэтому **первый benchmark может быть значительно дольше последующих** —
  последующие прогоны используют уже скачанные чекпоинты.
- Для сборки wheels на Mac/tests можно использовать `uv`; в Docker
  достаточно штатного `pip`.

