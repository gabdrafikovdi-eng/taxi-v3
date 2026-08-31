"""
Автономный тест STT-сервиса через микрофон с использованием Silero VAD.
Полная имитация телефонного звонка: детекция начала/конца речи, конвертация
в G.711 mu-law, отправка на сервер.
Оптимизировано для macOS: запись 48 кГц, внутренний ресемплинг до 16 кГц
для стабильной работы Silero VAD.

Режимы:
* production (по умолчанию) — POST /api/v1/transcribe;
* benchmark (--benchmark)   — POST /api/v1/benchmark/transcribe.

Benchmark строго последовательный (FSM IDLE → RECORDING → PROCESSING → IDLE):
одна фраза → одна запись → ОДИН HTTP-запрос → все модели → отчёт. Пока
HTTP-запрос выполняется, аудио-callback отбрасывает чанки БЕЗ запуска VAD:
ни новых записей, ни новых «🔴 ОБНАРУЖЕНА РЕЧЬ», ни параллельных запросов.
Следующая фраза может быть записана только после полного завершения
предыдущего benchmark.
"""

from __future__ import annotations

import argparse
import enum
import io
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import torch
from silero_vad import load_silero_vad

# Endpoints production и benchmark; выбор зависит от флага --benchmark.
DEFAULT_SERVER = "http://localhost:8001"
PRODUCTION_PATH = "/api/v1/transcribe"
BENCHMARK_PATH = "/api/v1/benchmark/transcribe"
DEBUG_WAV_PATH = Path("debug_last_record.wav")
DEBUG_ULAW_PATH = Path("debug_last_record.ulaw")

# Настройки аудио
REC_SAMPLE_RATE = 48000  # Родная частота микрофонов Mac
VAD_SAMPLE_RATE = 16000  # Частота, которую "понимает" Silero VAD
CHUNK_DURATION = 0.1  # Длительность одного блока записи (100 мс)
CHUNK_SAMPLES_48K = int(REC_SAMPLE_RATE * CHUNK_DURATION)  # 4800
CHUNK_SAMPLES_16K = int(VAD_SAMPLE_RATE * CHUNK_DURATION)  # 1600
VAD_WINDOW_SAMPLES = 512  # Стандартное окно для Silero VAD на 16 кГц

# Настройки логики VAD
SILENCE_DURATION = 1.5  # Секунд тишины для завершения фразы
MIN_SPEECH_DURATION = (
    0.4  # Минимальная длительность речи, чтобы не реагировать на щелчки
)

max_silence_chunks = int(SILENCE_DURATION / CHUNK_DURATION)  # 15 блоков
min_speech_chunks = int(MIN_SPEECH_DURATION / CHUNK_DURATION)  # 4 блока

# Таймауты HTTP (сек). Benchmark последовательно грузит 8 моделей, а при
# первом запуске ещё и скачивает чекпоинты — поэтому таймаут заметно больше.
PRODUCTION_HTTP_TIMEOUT = 600.0
BENCHMARK_HTTP_TIMEOUT = 1800.0

class ClientState(enum.Enum):
    """Состояния клиентского конечного автомата."""

    IDLE = "IDLE"  # ждём речь
    RECORDING = "RECORDING"  # пишем фразу
    PROCESSING = "PROCESSING"  # HTTP-запрос выполняется; аудио игнорируется


class PhraseStateMachine:
    """Потокобезопасный FSM клиента: IDLE → RECORDING → PROCESSING → IDLE.

    ``handle_chunk`` вызывается из потока PortAudio-callback,
    ``release`` — из главного потока ПОСЛЕ полной обработки фразы
    (конвертация → HTTP-запрос → вывод отчёта).

    Пока автомат в состоянии PROCESSING, чанки отбрасываются без запуска
    VAD: длинный benchmark-запрос не может спровоцировать новую запись
    или повторную отправку (главный дефект прежней реализации).
    """

    def __init__(
        self,
        vad_fn: Callable[[np.ndarray], bool],
        *,
        min_speech_chunks: int = 4,
        max_silence_chunks: int = 15,
        on_speech_start: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
        emit: Callable[[str], None] = print,
    ) -> None:
        self._vad_fn = vad_fn
        self._min_speech = max(1, min_speech_chunks)
        self._max_silence = max(1, max_silence_chunks)
        self._on_speech_start = on_speech_start or (lambda: None)
        self._on_release = on_release or (lambda: None)
        self._emit = emit
        self._lock = threading.Lock()
        self._state = ClientState.IDLE
        self._buffer: list[np.ndarray] = []
        self._silence_chunks = 0
        self._speech_chunks = 0
        self._dropped_chunks = 0

    @property
    def state(self) -> ClientState:
        with self._lock:
            return self._state

    def handle_chunk(self, chunk: np.ndarray) -> list[np.ndarray] | None:
        """Обработать один аудио-блок.

        :param chunk: float32-чанк 48 кГц (как отдаёт PortAudio).
        :return: завершённая фраза (список чанков) при переходе
            RECORDING → PROCESSING, иначе ``None``.
        """
        with self._lock:
            if self._state is ClientState.PROCESSING:
                # Идёт HTTP-запрос: аудио (и VAD!) не трогаем — защита от
                # ложных срабатываний и повторных отправок.
                self._dropped_chunks += 1
                return None

            if self._vad_fn(chunk):
                if self._state is ClientState.IDLE:
                    self._state = ClientState.RECORDING
                    self._buffer = []
                    self._silence_chunks = 0
                    self._speech_chunks = 0
                    self._emit("\n🔴 ОБНАРУЖЕНА РЕЧЬ...")
                    self._on_speech_start()
                self._buffer.append(chunk)
                self._silence_chunks = 0
                self._speech_chunks += 1
                return None

            if self._state is not ClientState.RECORDING:
                return None

            self._silence_chunks += 1
            self._buffer.append(chunk)  # хвост тишины, чтобы не обрезать слово
            if self._silence_chunks < self._max_silence:
                return None

            phrase = self._buffer
            too_short = self._speech_chunks < self._min_speech
            self._buffer = []
            self._silence_chunks = 0
            self._speech_chunks = 0
            if too_short:
                # Короткий шум (щелчок клавиатуры и т.п.) — игнорируем:
                # критерий — именно длительность РЕЧИ, а не всего буфера
                # (тишиной шум не «дотягивается» до минимальной фразы).
                self._state = ClientState.IDLE
                self._on_release()
                self._emit("⚠️ Слишком короткий звук (шум), игнорируем...")
                return None

            self._state = ClientState.PROCESSING
            self._emit("\n⏸️ ПАУЗА. Отправка на распознавание...")
            return phrase

    def release(self) -> None:
        """Вернуться в IDLE после обработки фразы (идемпотентно).

        Вызывается гарантированно (в т.ч. после ошибок HTTP), чтобы клиент
        не «залип» в PROCESSING навсегда. Сбрасывает накопленное аудио и
        счётчик пропущенных блоков.
        """
        with self._lock:
            dropped, self._dropped_chunks = self._dropped_chunks, 0
            self._buffer = []
            self._silence_chunks = 0
            self._speech_chunks = 0
            self._state = ClientState.IDLE
        self._on_release()
        if dropped:
            self._emit(
                f"🔇 Пока шла обработка, пропущено {dropped * CHUNK_DURATION:.1f} с "
                f"аудио ({dropped} блоков)"
            )


def make_silero_vad_fn(
    vad_model: torch.nn.Module, threshold: float
) -> Callable[[np.ndarray], bool]:
    """VAD-функция: 48 кГц чанк → ресемпл 16 кГц → окна 512 → Silero."""

    def vad_fn(chunk: np.ndarray) -> bool:
        x_old = np.linspace(0.0, 1.0, num=len(chunk), endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=CHUNK_SAMPLES_16K, endpoint=False)
        chunk_16k = np.interp(x_new, x_old, chunk)

        for i in range(0, len(chunk_16k), VAD_WINDOW_SAMPLES):
            window = chunk_16k[i : i + VAD_WINDOW_SAMPLES]
            if len(window) < VAD_WINDOW_SAMPLES:
                window = np.pad(
                    window, (0, VAD_WINDOW_SAMPLES - len(window)), mode="constant"
                )
            tensor = torch.from_numpy(window).float()
            with torch.no_grad():
                prob = vad_model(tensor, VAD_SAMPLE_RATE).item()
            if prob >= threshold:
                return True
        return False

    return vad_fn


def list_devices():
    print("\n🎤 Доступные устройства ввода:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            print(
                f"  [{i}] {device['name']} (max channels: {device['max_input_channels']})"
            )
    print()


def select_input_device() -> int:
    devices = sd.query_devices()
    input_devices = [
        (i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0
    ]
    if not input_devices:
        print("❌ Не найдено ни одного устройства ввода (микрофона).")
        sys.exit(1)

    # Безопасное получение дефолтного устройства
    default_dev = sd.default.device
    if isinstance(default_dev, (list, tuple)):
        default_in = default_dev[0]
    else:
        default_in = default_dev

    print("\n🎤 Выберите микрофон:")
    for idx, (i, d) in enumerate(input_devices):
        is_default = str(i) == str(default_in)
        mark = " (по умолчанию)" if is_default else ""
        print(f"  [{idx}] {d['name']}{mark}")

    choice = input("Номер микрофона [Enter — по умолчанию]: ").strip()
    if choice == "":
        # Возвращаем реальный индекс из списка input_devices для дефолтного, или просто первый
        for i, d in input_devices:
            if str(i) == str(default_in):
                return i
        return input_devices[0][0]  # Fallback

    try:
        selected = int(choice)
    except ValueError:
        print(f"❌ Некорректный ввод. Укажите число из списка.")
        sys.exit(1)

    if not 0 <= selected < len(input_devices):
        print(f"❌ Нет микрофона с номером {selected}.")
        sys.exit(1)

    return input_devices[selected][0]


def convert_to_telephony_format(audio_array: np.ndarray, original_sr: int) -> bytes:
    """Конвертирует float32 аудио в G.711 mu-law 8 кГц."""
    audio_int16 = (audio_array * 32767).astype(np.int16)

    # Отладочный WAV в оригинальном качестве
    with sf.SoundFile(
        DEBUG_WAV_PATH, mode="w", samplerate=original_sr, channels=1, subtype="PCM_16"
    ) as f:
        f.write(audio_int16)

    if original_sr != 8000:
        target_len = max(1, round(len(audio_int16) * 8000 / original_sr))
        x_old = np.linspace(0.0, 1.0, num=len(audio_int16), endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=target_len, endpoint=False)
        audio_8k = np.interp(x_new, x_old, audio_int16.astype(np.float32))
        audio_8k = np.clip(audio_8k, -32768, 32767).astype(np.int16)
    else:
        audio_8k = audio_int16

    ulaw_buffer = io.BytesIO()
    with sf.SoundFile(
        ulaw_buffer, mode="w", samplerate=8000, channels=1, format="RAW", subtype="ULAW"
    ) as f:
        f.write(audio_8k)

    ulaw_bytes = ulaw_buffer.getvalue()
    with open(DEBUG_ULAW_PATH, "wb") as f:
        f.write(ulaw_bytes)

    return ulaw_bytes


def send_to_server(
    ulaw_bytes: bytes,
    url: str,
    use_wav: bool = False,
    timeout: float = PRODUCTION_HTTP_TIMEOUT,
    poster: Callable[..., requests.Response] | None = None,
    long_running: bool = False,
) -> dict:
    """Отправить аудио на сервер (production или benchmark endpoint).

    :param poster: инъекция HTTP-вызова для тестов (по умолчанию requests.post).
    :param long_running: True для benchmark — печатает предупреждение о
        длительном последовательном прогоне всех моделей.
    """
    post = poster or requests.post
    start_time = time.time()
    try:
        if use_wav:
            with open(DEBUG_WAV_PATH, "rb") as f:
                wav_bytes = f.read()
            files = {"audio": ("audio.wav", wav_bytes, "audio/wav")}
            print(f"⚙️ [ДИАГНОСТИКА] Отправка WAV ({len(wav_bytes)} байт)...")
        else:
            files = {"audio": ("audio.ulaw", ulaw_bytes, "audio/x-mulaw")}
            print(f"⚙️ [ТЕЛЕФОНИЯ] Отправка mu-law 8kHz ({len(ulaw_bytes)} байт)...")

        if long_running:
            print(
                "\n⏳ BENCHMARK ВЫПОЛНЯЕТСЯ — все модели последовательно "
                "(load → inference → unload)..."
            )
            print("   Первый запуск может быть заметно дольше: скачивание")
            print("   чекпоинтов в ~/.cache/gigaam.\n")

        response = post(url, files=files, timeout=timeout)
        elapsed_ms = round((time.time() - start_time) * 1000, 1)
        response.raise_for_status()
        result = response.json()
        result["http_time_ms"] = elapsed_ms
        return result
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Не удалось подключиться к серверу (порт 8001?)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return {"text": "", "duration_ms": 0, "http_time_ms": 0}


def handle_phrase(
    phrase: list[np.ndarray],
    *,
    fsm: PhraseStateMachine,
    benchmark: bool,
    server_url: str,
    use_wav: bool,
    timeout: float,
    poster: Callable[..., requests.Response] | None = None,
) -> None:
    """Обработать ОДНУ фразу: конвертация → HTTP-запрос → отчёт → release().

    ``fsm.release()`` вызывается гарантированно (finally): после ошибки
    клиент возвращается в состояние ожидания, а не залипает в PROCESSING.
    """
    try:
        audio_array = np.concatenate(phrase, axis=0)
        print("⚙️ Конвертация и отправка...")
        ulaw_bytes = convert_to_telephony_format(
            audio_array, original_sr=REC_SAMPLE_RATE
        )
        result = send_to_server(
            ulaw_bytes,
            url=server_url,
            use_wav=use_wav,
            timeout=timeout,
            poster=poster,
            long_running=benchmark,
        )

        if benchmark:
            print("\n" + "=" * 60)
            print("STT BENCHMARK")
            print("=" * 60)
            print("Фраза отправлена.")
            print(f"Audio duration: {result.get('duration_ms', 0)} ms")
            print()
            print_benchmark_report(result)
        else:
            print("\n" + "=" * 50)
            print(f'🗣️  Текст: "{result.get("text", "ПУСТО")}"')
            print(
                f"⏱️  Длительность аудио: {result.get('duration_ms', 0)} мс | "
                f"HTTP: {result.get('http_time_ms', 0)} мс"
            )
            print("=" * 50)
    except SystemExit:
        raise
    except Exception as exc:  # ошибка не должна оставить FSM в PROCESSING
        print(f"❌ Ошибка обработки фразы: {exc}")
    finally:
        fsm.release()
        print("🟢 Ожидание следующей фразы...")


def _model_display_name(model_key: str) -> str:
    """Человекочитаемое имя модели из реестра (fallback — сам ключ)."""
    try:
        from app.stt.registry import MODEL_REGISTRY

        spec = MODEL_REGISTRY.get(model_key)
        return spec.name if spec else model_key
    except Exception:
        return model_key


def print_benchmark_report(payload: dict) -> None:
    """Читаемый отчёт по ответу /api/v1/benchmark/transcribe."""
    results = payload.get("results", [])
    if payload.get("speech_detected") is False or not results:
        print("⚠️ Речь в записи не обнаружена (VAD) — сравнивать нечего.")
        return

    summary_rows: list[tuple[str, str, str]] = []
    for result in results:
        model = result.get("model", "?")
        print("-" * 60)
        print(_model_display_name(model))
        print("-" * 60)
        if not result.get("success"):
            print(f'Ошибка: {result.get("error", "неизвестно")}')
            summary_rows.append((model, "FAIL", "FAIL"))
            continue
        print('Text:')
        print(f'"{result.get("text", "")}"')
        load_ms = result.get("load_time_ms", 0)
        infer_ms = result.get("inference_time_ms", 0)
        total_ms = result.get("total_time_ms", 0)
        print(f"\nLoad:      {load_ms:>8.0f} ms")
        print(f"Inference: {infer_ms:>8.0f} ms")
        print(f"Total:     {total_ms:>8.0f} ms")
        summary_rows.append((model, f"{infer_ms:.0f} ms", f"{total_ms:.0f} ms"))

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Model':<24} {'Inference':>12} {'Total':>12}")
    print("-" * 60)
    for model, infer_ms, total_ms in summary_rows:
        print(f"{model:<24} {infer_ms:>12} {total_ms:>12}")
    print(
        f"\nСуммарное время HTTP-запроса: {payload.get('http_time_ms', 0)} ms"
        " (включает последовательную загрузку всех моделей)"
    )


def main():
    parser = argparse.ArgumentParser(description="Автономный тест STT с Silero VAD")
    parser.add_argument(
        "--list-devices", action="store_true", help="Показать список микрофонов"
    )
    parser.add_argument("--device", type=int, default=None, help="Индекс микрофона")
    parser.add_argument(
        "--threshold", type=float, default=0.5, help="Порог VAD (0.0 - 1.0)"
    )
    parser.add_argument(
        "--use-wav", action="store_true", help="Отправлять WAV вместо mu-law"
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help=f"Базовый URL сервиса (по умолчанию {DEFAULT_SERVER})",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help=(
            "Отправить запись на /api/v1/benchmark/transcribe: одна и та же фраза "
            "последовательно прогоняется через все ASR-модели реестра"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help=(
            "Таймаут HTTP-запроса, сек (по умолчанию "
            f"{PRODUCTION_HTTP_TIMEOUT:.0f} для production, "
            f"{BENCHMARK_HTTP_TIMEOUT:.0f} для benchmark)"
        ),
    )
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    endpoint = BENCHMARK_PATH if args.benchmark else PRODUCTION_PATH
    server_url = args.server.rstrip("/") + endpoint
    timeout = (
        args.timeout
        if args.timeout is not None
        else (BENCHMARK_HTTP_TIMEOUT if args.benchmark else PRODUCTION_HTTP_TIMEOUT)
    )

    device = args.device if args.device is not None else select_input_device()

    # Валидация
    try:
        info = sd.query_devices(device)
        if info["max_input_channels"] < 1:
            print(f"❌ Устройство [{device}] — это устройство ВЫВОДА, а не ввода.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Устройство [{device}] недоступно: {e}")
        sys.exit(1)

    print("=" * 60)
    print("📞 ТЕЛЕФОННЫЙ ТЕСТ STT (Silero VAD + G.711 mu-law)")
    mode = "BENCHMARK (все модели последовательно)" if args.benchmark else "PRODUCTION"
    print(f"Режим: {mode}")
    print(f"Endpoint: {server_url}")
    print(f"Частота записи: {REC_SAMPLE_RATE} Гц (оптимизировано для macOS)")
    print(f"Порог срабатывания: {args.threshold}")
    print(f"🎤 Устройство: [{device}] {info['name']}")
    print("Загрузка модели Silero VAD...")

    vad_model = load_silero_vad()
    vad_model.eval()

    # Сброс скрытого состояния Silero при старте записи и при возврате в IDLE:
    # «залипшее» после паузы LSTM-состояние даёт ложные срабатывания VAD.
    fsm = PhraseStateMachine(
        vad_fn=make_silero_vad_fn(vad_model, args.threshold),
        min_speech_chunks=min_speech_chunks,
        max_silence_chunks=max_silence_chunks,
        on_speech_start=vad_model.reset_states,
        on_release=vad_model.reset_states,
    )

    pending_phrase: list[np.ndarray] = []
    ready_to_process = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        nonlocal pending_phrase
        if status:
            print(f"⚠️ Статус потока: {status}")
        # FSM сам решает: копить, отбрасывать (PROCESSING) или отдать фразу.
        phrase = fsm.handle_chunk(indata.flatten().astype(np.float32))
        if phrase is not None:
            pending_phrase = phrase
            ready_to_process.set()

    try:
        with sd.InputStream(
            samplerate=REC_SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=device,
            blocksize=CHUNK_SAMPLES_48K,
            callback=audio_callback,
        ):
            print("✅ Модель загружена. Нажмите Ctrl+C для выхода.")
            print("=" * 60)
            print("🟢 Ожидание речи... (скажи что-нибудь в микрофон)")
            while True:
                if ready_to_process.is_set():
                    ready_to_process.clear()
                    phrase, pending_phrase = pending_phrase, []
                    if not phrase:
                        continue
                    # Блокирующе ждём ПОЛНЫЙ HTTP-ответ и печатаем отчёт.
                    # Только после этого handle_phrase вернёт FSM в IDLE и
                    # клиент снова начнёт слушать микрофон.
                    handle_phrase(
                        phrase,
                        fsm=fsm,
                        benchmark=args.benchmark,
                        server_url=server_url,
                        use_wav=args.use_wav,
                        timeout=timeout,
                    )

                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n👋 Завершение работы.")
        sys.exit(0)


if __name__ == "__main__":
    main()