# speech-service

Микросервис распознавания и синтеза речи для голосового бота такси.

- **STT** — [GigaAM v3-rnnt](https://github.com/salute-developers/GigaAM) (GPU в проде, CPU для локальных тестов);
- **TTS** — [Silero TTS](https://github.com/snakers4/silero-models) v5 (CPU);
- **VAD** — [Silero VAD](https://github.com/snakers4/silero-vad) (CPU);
- Аудио-конвертация G.711 µ-law/A-law (GoIP) ↔ PCM 16 кГц 16 бит;
- JSON-логирование через `structlog`; конфиг через `pydantic-settings`.

Сервис слушает `0.0.0.0:8001` (по умолчанию). Основной бэкенд
обращается к нему по HTTP, например `http://192.168.1.100:8001`.

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

> При первом старте GigaAM, Silero TTS и Silero VAD докачают веса
> в `~/.cache`. VAD (~2 МБ) уже входит в пакет `silero-vad` и работает
> офлайн. Для CPU-режима убедитесь, что `STT_DEVICE=cpu`.

## Запуск в Docker с GPU

Подключите сервис к NVIDIA runtime (см. основной `docker-compose.yml`
проекта либо запустите образ напрямую):

```bash
docker build -t speech-service -f speech-service/Dockerfile speech-service
docker run --rm --gpus all -p 8001:8001 \
  -e STT_DEVICE=cuda:0 \
  -v ~/.cache:/root/.cache \
  speech-service
```

Либо добавьте в корневой `docker-compose.yml` сервис вида:

```yaml
speech-service:
  build: ./speech-service
  ports: ["8001:8001"]
  environment:
    STT_DEVICE: cuda:0
    STT_FALLBACK_TO_CPU: "true"
  deploy:
    resources:
      reservations:
        devices:
          - capabilities: [gpu]
  volumes:
    - ~/.cache:/root/.cache
```

Если GPU на хосте нет (`nvidia-smi` отсутствует), сервис всё равно
стартует: GigaAM загрузится на CPU, `/health` вернёт
`"gpu_available": false`.

## Конфигурация

Все настройки — через переменные окружения или файл `.env`
(образец: [`.env.example`](.env.example)).

| Переменная | По умолчанию | Описание |
|---|---|---|
| `STT_MODEL` | `gigaam-v3-rnnt` | Имя STT-модели |
| `STT_DEVICE` | `cuda:0` | `cuda:0` (GPU) или `cpu` (Mac) |
| `STT_FALLBACK_TO_CPU` | `true` | Fallback на CPU, если GPU недоступен |
| `TTS_SPEAKER` | `baya` | Голос Silero TTS |
| `TTS_SAMPLE_RATE` | `48000` | Частота TTS (8000/24000/48000) |
| `MAX_AUDIO_DURATION_SEC` | `30` | Лимит длительности аудио на STT |
| `LOG_LEVEL` | `INFO` | Уровень логов |
| `HOST` / `PORT` | `0.0.0.0` / `8001` | Адрес/порт uvicorn |

## Проверка /health

```bash
curl http://localhost:8001/health
# {"status":"ok","stt_loaded":true,"tts_loaded":true,
#  "gpu_available":true,"stt_model":"gigaam-v3-rnnt","device":"cuda:0"}
```

## API

### POST /api/v1/transcribe — аудио → текст

Принимает `multipart/form-data` (поле `audio`): WAV, G.711 µ-law
(`audio/x-mulaw`, 8 кГц) или A-law (`audio/x-alaw`, 8 кГц).

```bash
# WAV
curl -F "audio=@speech.wav;type=audio/wav" http://localhost:8001/api/v1/transcribe

# G.711 µ-law от GoIP-шлюза
curl -F "audio=@g711.ulaw;type=audio/x-mulaw" http://localhost:8001/api/v1/transcribe
```

Ответ `200`:

```json
{"text": "распознанный текст", "duration_ms": 1500, "sample_rate": 16000}
```

Ошибки: `400 Empty audio`, `413 Audio too long` (> `MAX_AUDIO_DURATION_SEC`),
`503 STT model not loaded`.

### POST /api/v1/synthesize — текст → аудио (WAV)

```bash
curl -X POST http://localhost:8001/api/v1/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Куда вас подать?", "speaker": "baya", "sample_rate": 48000}' \
  --output answer.wav
```

Ответ `200` — `audio/wav` (бинарный WAV). `400 Empty text`,
`503 TTS model not loaded`.

### POST /api/v1/transcribe/stream — потоковый STT с VAD

Принимает `application/octet-stream` — сырые PCM 16 кГц / 16 бит / mono.
Клиент накапливает аудио батчами и присылает их POST-запросами; когда
хвост батча тихий дольше `silence_threshold_ms`, сервис считает фразу
завершённой и возвращает распознанный текст.

```bash
# подготовить сырой PCM 16 кГц / 16 бит / mono
ffmpeg -i speech.wav -f s16le -ac 1 -ar 16000 speech.pcm

curl -X POST "http://localhost:8001/api/v1/transcribe/stream?sample_rate=16000&silence_threshold_ms=800" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @speech.pcm
```

Ответ `200` (фраза завершена): `{"text": "...", "is_final": true}`.
Ответ `200` (фраза ещё не завершена): `{"text": "", "is_final": false}`.

## Структура

```
speech-service/
├── app/
│   ├── main.py          # FastAPI, lifespan, роуты, middleware
│   ├── config.py        # pydantic-settings
│   ├── logging.py       # structlog (JSON)
│   ├── stt/
│   │   ├── client.py    # GigaAM STT
│   │   └── vad.py       # Silero VAD
│   ├── tts/
│   │   └── client.py    # Silero TTS
│   └── audio/
│       └── converter.py # G.711 <-> PCM16, resample, WAV
├── pyproject.toml
├── Dockerfile
└── .env.example
```

## Замечания

- Логи пишутся только через `structlog` (JSON), `print()` не используется.
- GigaAM использует `ffmpeg` для чтения аудио — он должен быть установлен.
- Для сборки wheels на Mac/tests можно использовать `uv`; в Docker
  достаточно штатного `pip`.