# telephony-service — слой телефонии taxi-v3

Оркестрация голосовых звонков такси: **Asterisk 22.10.1** (SIP/PBX-ядро) +
**telephony-service** (ARI-оркестратор) + существующие **speech-service**
(STT/TTS) и **backend** (LLM/диалоги). Существующие сервисы не изменяются.

```text
GSM (SIM Beeline)
  ↓
GoIP4 (192.168.1.50)
  ↓ SIP 5060/UDP
Asterisk 22.10.1 (контейнер taxi-asterisk)
  ↓ ARI (HTTP 8088 + WebSocket) · RTP externalMedia (18000+/UDP)
telephony-service (контейнер taxi-telephony)
  ↓ HTTP                                      ↓ HTTP
speech-service (STT µ-law → текст)            speech-service (TTS → MP3/WAV)
  ↓                                                  ↓
backend (LLM, call session)               G.711 µ-law → RTP → Asterisk → GoIP4
```

Обратный поток (ответ абоненту): текст ответа → TTS → PCM16 8 кГц → G.711
µ-law → RTP-пакеты 20 мс → Asterisk → GoIP4 → GSM.

---

## Архитектура

### Разделение ответственности

* **Asterisk** — SIP-транспорт, PJSIP-эндпоинты, RTP, бриджи, кодеки,
  маршрутизация входящих (`from-goip → Stasis(taxi)`).
* **telephony-service** — управление жизненным циклом звонков через ARI
  (Stasis-приложение `taxi`), медиа-pipeline (RTP-приём/отправка),
  сегментация фраз, интеграции со speech-service/backend, health,
  конфигурация, логирование.
* **speech-service** (не изменяется) — STT (`POST /api/v1/transcribe`,
  принимает G.711 µ-law/A-law по content-type) и TTS
  (`POST /api/v1/synthesize`; edge-tts возвращает MP3 — декодируется здесь
  через ffmpeg).
* **backend** (не изменяется) — бизнес-логика диалога. Интеграция — через
  адаптер `BackendClient` (см. «Интеграция с backend»).

### Медиа-топология звонка

```text
caller(PJSIP/goip4) ──┐
                      ├─ mixing bridge (ARI)
UnicastRTP ───────────┘   external_host = taxi-telephony:18000
      │ RTP µ-law (PCMU, PT 0)
      ▼
UDP-сокет telephony-service (18000-18050)
      │ PhraseDetector (энергетическая сегментация фраз, 20 мс чанки)
      ▼ speech-service STT (raw G.711, без перекодирования)
      ▼ backend (текст → текст)
      ▼ speech-service TTS (MP3/WAV → ffmpeg → PCM16 8k → G.711)
      ▼ RTP обратно на адрес источника Asterisk
```

Преобразований «на лету» между Asterisk и telephony-service нет — аудио
передаётся в исходном G.711. STT принимает µ-law напрямую (speech-service
декодирует сам); TTS-ответ декодируется ffmpeg'ом в контейнере telephony.

### Состояния звонка

`RINGING → CONNECTED → LISTENING ⇄ PROCESSING ⇄ SPEAKING → ENDING → ENDED`,
`FAILED` — из любого активного состояния. Переходы валидируются
(`app/calls/state.py`), дубликаты ARI-событий дедуплицируются.

### Обработка ошибок

* Asterisk/ARI недоступен — реконнект WebSocket с экспоненциальным backoff,
  health = degraded;
* speech-service STT/TTS timeout/ошибки — retry, звонок не падает
  (пропускается шаг с логом `stt_failed`/`tts_failed`);
* backend недоступен — `setup_failed`/`backend_message_failed`, звонок
  корректно завершается;
* caller hangup / StasisEnd / максимум длительности (watchdog) — полный
  teardown (externalMedia, bridge, backend.end_call);
* malformed audio/события — изолируются логом, сервис живёт.

---

## Структура

```text
telephony-service/
├── app/
│   ├── main.py               # точка входа (ARI + health + shutdown)
│   ├── config.py             # pydantic-settings (все параметры через env)
│   ├── logging.py            # JSON-логи, correlation call_id (contextvar)
│   ├── health.py             # /health, /readyz
│   ├── g711.py               # G.711 µ-law/A-law ↔ PCM16
│   ├── rtp.py                # RTP parse/build (RFC 3550)
│   ├── wavutil.py            # WAV/MP3/OGG → PCM16, ресемплинг (ffmpeg)
│   ├── phrase.py             # сегментация фраз (turn-taking)
│   ├── ari/client.py         # ARI REST + WebSocket, reconnect
│   ├── calls/                # state machine, Call, pipeline, CallManager
│   ├── speech/client.py      # клиент speech-service (STT/TTS/health)
│   └── backend/              # адаптер backend: mock | http
├── asterisk/
│   ├── config/               # pjsip/extensions/ari/http/rtp/logger (шаблоны)
│   └── scripts/render-config.sh  # рендер секретов при старте контейнера
├── tests/                    # unit + integration
├── scripts/                  # ari_smoke, speech_smoke, make_test_sound
├── Dockerfile                # python:3.12-slim + ffmpeg
├── docker-compose.yml        # asterisk + telephony
└── .env.example
```

---

## Запуск (development, Mac/Colima)

```bash
# 1. Сконфигурировать окружение
cd telephony-service
cp .env.example .env
#   обязательно поменять ASTERISK_ARI_PASSWORD и GOIP_SIP_PASSWORD

# 2. Поднять Asterisk + telephony-service
docker-compose up -d --build

# 3. Проверки
docker ps                                    # оба контейнера healthy
docker exec taxi-asterisk asterisk -rx 'pjsip show endpoints'   # goip4 (+loopback)
docker exec taxi-asterisk asterisk -rx 'ari show apps'          # taxi
curl http://localhost:8090/health            # состояние оркестратора
curl http://localhost:8090/readyz            # 200, если ARI подключён
python scripts/ari_smoke.py                  # smoke-тест ARI

# 4. speech-service (существующий сервис, на хосте Mac)
cd ../speech-service
STT_DEVICE=cpu uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
# telephony-service видит его как http://host.docker.internal:8001
```

### Self-loop тест без GoIP (полный цикл)

Тестовый endpoint `loopback` — Asterisk вызывает сам себя:

```bash
docker exec taxi-asterisk asterisk -rx \
  'channel originate PJSIP/601@loopback application Playback custom/voice'
```

`custom/voice` (шум 10 с, генерируется при старте) — проверка топологии.
Для STT/TTS с реальной речью:

```bash
speech-service/.venv/bin/python scripts/make_test_sound.py    # voice.ulaw из audio/*.ogg
docker cp voice.ulaw taxi-asterisk:/var/lib/asterisk/sounds/custom/voice.ulaw
# повторить originate и смотреть логи:
docker logs -f taxi-telephony
# ожидание: rtp_source_learned → speaking_started (greeting) →
#           phrase_recognized (STT) → speaking_started (ответ TTS) → call_ended
```

---

## Настройка GoIP4

Веб-интерфейс `http://192.168.1.50` → Configuration → Mobile → SIP settings
(на каждый SIM-порт):

| Параметр GoIP         | dev (digest)                       | production (VPN, ip)           |
|-----------------------|------------------------------------|--------------------------------|
| Mode                  | Single Server / SIP Client         | то же                          |
| SIP Server Address    | `<Mac IP>` (например 192.168.1.18) | `<VPN IP сервера>`             |
| SIP Server Port       | `5060`                             | `5060`                         |
| SIP User ID           | `goip4`                            | (не требуется)                 |
| SIP Authentication ID | `goip4`                            | (не требуется)                 |
| SIP Password          | `GOIP_SIP_PASSWORD` из .env        | (не требуется)                 |

В `.env`: `GOIP_AUTH_MODE=digest` (dev, Docker NAT скрывает IP GoIP) или
`GOIP_AUTH_MODE=ip` + `GOIP_HOST=<IP GoIP>` (production/VPN — identification
по IP через `[identify-goip4]`).

Проверка: наберите SIM-номер GoIP с телефона → в логах telephony появится
`call_incoming` (context=from-goip) → `call_established`, бот проиграет
приветствие.

---

## Проверка SIP

```bash
docker exec taxi-asterisk asterisk -rx 'pjsip show endpoints'    # состояния
docker exec taxi-asterisk asterisk -rx 'pjsip show contacts'
docker exec taxi-asterisk asterisk -rx 'pjsip set logger on'     # дамп SIP
docker logs -f taxi-asterisk                                     # смотреть INVITE
docker logs taxi-asterisk 2>&1 | grep -i 'failed to authenticate'  # ошибки auth
```

---

## Проверка RTP/аудио

```bash
docker exec taxi-asterisk asterisk -rx 'pjsip show channelstats' # Count/Lost/Jitter
docker exec taxi-asterisk asterisk -rx 'rtp set debug on'        # дамп RTP
docker logs -f taxi-telephony | grep pipeline_stats              # приём RTP в pipeline
```

Диапазоны портов разделены: **Asterisk RTP 10000-10100/UDP** (проброшен
наружу — нужен GoIP) и **telephony-service 18000-18050/UDP** (external
media; наружу не пробрасывается). Echo-тест кодеков без оркестратора:
позвоните с GoIP на extension `600` (контекст `test`) — `Echo()` вернёт
аудио обратно.

---

## Интеграция с speech-service (сервис не изменяется)

* `POST /api/v1/transcribe` — multipart-поле `audio`. telephony отправляет
  **raw G.711 µ-law** с content-type `audio/x-mulaw` (для alaw —
  `audio/x-alaw`): speech-service декодирует сам, перекодирований нет.
  Ответ: `{"text", "duration_ms", "sample_rate", ...}`.
* `POST /api/v1/synthesize` — `{"text"}` → аудиопоток. edge-tts отдаёт
  **MP3** при content-type `audio/wav` (особенность сервиса): telephony
  декодирует через ffmpeg в контейнере → PCM16 8 кГц → G.711.
* `GET /health` — фоновая проверка (каждые 30 с), участвует в `/health`.

Таймауты: `STT_TIMEOUT_SEC`, `TTS_TIMEOUT_SEC`; 1 retry на сетевые ошибки
и 5xx (4xx без повторов).

## Интеграция с backend

### BLOCKER: backend не имеет HTTP API

```text
BLOCKER:
Что требуется изменить:   экспонировать в backend минимальный HTTP API
                          управления call session и диалогом.
Почему это требуется:     telephony-service должен передавать распознанный
                          текст в существующую бизнес-логику
                          (ConversationManager.handle_message) и получать
                          ответ, не дублируя логику и не трогая БД напрямую.
Почему нельзя решить
внутри telephony-service: backend read-only по условию задачи; его код
                          (app/llm, app/services) живёт в другом процессе
                          и окружении (Postgres, OPENAI-ключи).
Предлагаемое изменение:   добавить в backend FastAPI-слой:
    POST /api/v1/calls                 {"external_id","caller_phone"} -> {"call_session_id"}
    GET  /api/v1/calls/{id}/greeting   -> {"text"} | 404
    POST /api/v1/calls/{id}/messages   {"text"} -> {"response"}
    POST /api/v1/calls/{id}/end        -> 204
    (внутри — существующие CallSessionService + ConversationManager,
     channel=CallChannel.PHONE)
```

**Адаптер готов**: `BACKEND_MODE=http` реализует ровно этот контракт
(`app/backend/http_client.py`: retry, таймауты). Пока backend API нет,
используется `BACKEND_MODE=mock` (по умолчанию) — встроенная заглушка
возвращает приветствие и эхо-ответ, чего достаточно для проверки полного
телефонного контура. Модели/логика backend не менялись;
`backend_call_session_id` хранится только в telephony-сессии.

## Тесты

```bash
cd telephony-service
uv venv --python 3.12 .venv
uv pip install -p .venv/bin/python -q aiohttp pydantic pydantic-settings pytest pytest-asyncio
.venv/bin/python -m pytest                  # 52 unit (+3 integration auto-skip)
.venv/bin/python -m pytest -m integration   # с запущенными Asterisk/speech-service
```

Покрытие: G.711 (контрольные точки + round-trip), RTP parse/build,
WAV/float32/mixdown/resample, PhraseDetector, state machine, speech-клиент
(TestServer: retry/4xx/5xx/timeout), backend-клиенты, **CallManager —
полный медиа-цикл по реальному UDP** (ARI-событие → RTP-фраза → STT →
backend → TTS → RTP-ответ → teardown), дедупликация событий.

## Production-схема

```text
ОФИС                                  ДАТА-ЦЕНТР (Linux server)
Router (static public IP)             ┌────────────────────────────────┐
  │ WireGuard VPN (UDP 51820)         │ Asterisk    SIP 5060 (VPN)     │
  └────── GoIP4 (SIM Beeline) ───────▶│             RTP 10000-10100    │
        SIP: <VPN IP сервера>:5060    │ telephony   ARI 8088 (лок.)    │
        GOIP_AUTH_MODE=ip             │             RTP 18000-18050    │
                                      │ speech-service :8001 (внутр.)  │
                                      │ backend / postgres (внутр.)    │
                                      └────────────────────────────────┘
```

Чек-лист переноса с Mac/Colima:

1. `GOIP_AUTH_MODE=ip`, `GOIP_HOST=<VPN-IP GoIP4>`; digest-пароль можно
   оставить вторым фактором.
2. `asterisk/config/pjsip.conf`: transport `bind=0.0.0.0:5060` →
   `bind=<VPN-IP>:5060` (SIP только на VPN-интерфейсе).
3. Firewall: 5060/UDP и 10000-10100/UDP — только из VPN; 8088 (ARI) —
   только localhost/private; 8090 (health) — private.
4. Секреты: сильные `ASTERISK_ARI_PASSWORD`, `GOIP_SIP_PASSWORD` в `.env`
   (в репозитории только `.env.example`).
5. `SPEECH_SERVICE_URL`/`BACKEND_URL` — внутренние адреса docker-сети;
   speech-service: `STT_DEVICE=cuda:0` (латентность STT с ~6 с на CPU до
   <1 с на GPU).
6. Образ Asterisk зафиксирован (`andrius/asterisk:22.10.1_debian-trixie`);
   образ telephony собирается из `Dockerfile` (python:3.12-slim + ffmpeg),
   переносим arm64/amd64.
7. Healthchecks уже настроены в docker-compose; мониторить `/health`
   telephony (status: ok/degraded) и логи `pipeline_stats`.

### Ограничения / известные особенности

* Turn-taking — энергетический VAD, barge-in отключён (речь абонента во
  время ответа бота не собирается); `ENERGY_SPEECH_THRESHOLD` может
  требовать калибровки под конкретную GSM-линию.
* STT латентность на CPU (Mac) ~6 с на фразу — для продакшена нужен GPU.
* speech-service отдаёт TTS как MP3 с content-type `audio/wav` —
  telephony компенсирует ffmpeg-декодером (форматы различаются автоматически).
* Тестовый endpoint `loopback` в pjsip.conf можно удалить в production
  (на функциональность не влияет).
