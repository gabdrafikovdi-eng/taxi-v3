#!/usr/bin/env python3
"""Сравнительное тестирование STT speech-service на разных моделях GigaAM.

Что делает скрипт:
  1. Автоматически собирает аудиофайлы из папки ``audio`` (*.wav, *.flac, *.ogg,
     *.opus, *.mp3, *.m4a, *.aac, *.ulaw, *.alaw). Если рядом лежит ``<имя>.txt`` —
     он считается эталонной транскрипцией этого файла.
  2. Для каждой модели GigaAM (по умолчанию ``rnnt`` и ``ctc``) поднимает ОТДЕЛЬНЫЙ
     экземпляр speech-service (uvicorn с нужной STT_MODEL), дожидается загрузки
     модели через /health и прогоняет на нём все аудио через POST /api/v1/transcribe.
  3. Формат отправки задаётся --format:
       * ``wav``   — несжатый WAV (PCM16, как есть) — диагностический режим;
       * ``ulaw``  — G.711 μ-law 8 кГц (как в телефонии GoIP) — реальный путь;
       * ``alaw``  — G.711 A-law 8 кГц (телефония E1/PBX).
  4. Считает метрики WER (ошибки по словам) и CER (ошибки по символам) относительно
     эталона и печатает отчёт по каждой модели + сводную сравнительную таблицу.
     Результаты можно сохранить в JSON (--json).

Основной код сервиса не меняется: экземпляр speech-service запускается штатно через
uvicorn, только с переменной окружения STT_MODEL. Если сервис уже запущен отдельно —
используйте режим --server-url.

Примеры:
  uv run python test_stt_models.py
  uv run python test_stt_models.py --models ctc
  uv run python test_stt_models.py --models rnnt,ctc --limit 3 --json report.json
  uv run python test_stt_models.py --server-url http://localhost:8001
  uv run python test_stt_models.py --server-url http://localhost:8001
  uv run python test_stt_models.py --format ulaw --keep-running --port 8009
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import requests
import soundfile as sf

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

#: Поддерживаемые расширения аудиофайлов (папка audio пополняется автоматически).
AUDIO_EXTS = (
    ".wav", ".flac", ".ogg", ".opus", ".mp3", ".m4a", ".aac",
    ".ulaw", ".alaw",
)

#: Модели GigaAM, доступные для ASR через STT_MODEL speech-service.
#: Ключ — короткое имя модели, значение — STT_MODEL.
#: (ssl/emo — не ASR-модели, у них нет transcribe, поэтому не тестируются.)
SUPPORTED_MODELS: dict[str, str] = {
    "rnnt": "gigaam-v3-rnnt",
    "ctc": "gigaam-v2-ctc",
}
DEFAULT_MODELS = "rnnt,ctc"

#: Форматы отправки аудио на сервер. ulaw/alaw — телефонные G.711 8 кГц.
#: Ключ — значение --format, значение — (расширение, HTTP content-type).
AUDIO_FORMATS: dict[str, tuple[str, str]] = {
    "wav": (".wav", "audio/wav"),
    "ulaw": (".ulaw", "audio/x-mulaw"),
    "alaw": (".alaw", "audio/x-alaw"),
}
DEFAULT_FORMAT = "wav"
TELEPHONY_SAMPLE_RATE = 8000  # G.711 в телефонии всегда 8 кГц

MAX_AUDIO_DURATION_SEC = 30  # лимит сервиса (settings.MAX_AUDIO_DURATION_SEC)

# ANSI-цвета для аккуратного вывода в терминале (--no-color — без них).
class C:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"

NO_COLOR = False


def c(code: str, text: str) -> str:
    """Раскрасить текст, если цвет включён."""
    if NO_COLOR or not code:
        return text
    return f"{code}{text}{C.RESET}"


# ---------------------------------------------------------------------------
# Пути / окружение
# ---------------------------------------------------------------------------

#: Корень speech-service — папка, где лежит этот скрипт.
BASE_DIR = Path(__file__).resolve().parent


def default_audio_dir() -> Path:
    """Папка с аудио по умолчанию — ``<repo>/speech-service/audio``."""
    return BASE_DIR / "audio"


def default_device() -> str:
    """Устройство по умолчанию — из STT_DEVICE окружения или cpu."""
    return os.environ.get("STT_DEVICE", "cpu").strip().lower() or "cpu"


# ---------------------------------------------------------------------------
# Метрики: WER / CER (чистый Python, без внешних зависимостей)
# ---------------------------------------------------------------------------

#: Токен слова: последовательности кириллицы/латиницы/цифр.
_TOKEN_RE = re.compile(r"[a-zа-яё0-9]+")

#: Русские числительные — для нормализации «тридцать один» → «31».
_RU_NUMBERS: dict[str, int] = {
    "ноль": 0, "один": 1, "одна": 1, "одно": 1, "два": 2, "две": 2,
    "три": 3, "четыре": 4, "пять": 5, "шесть": 6, "семь": 7,
    "восемь": 8, "девять": 9, "десять": 10,
    "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13,
    "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16,
    "семнадцать": 17, "восемнадцать": 18, "девятнадцать": 19,
    "двадцать": 20, "тридцать": 30, "сорок": 40, "пятьдесят": 50,
    "шестьдесят": 60, "семьдесят": 70, "восемьдесят": 80,
    "девяносто": 90,
    "сто": 100, "двести": 200, "триста": 300, "четыреста": 400,
    "пятьсот": 500, "шестьсот": 600, "семьсот": 700,
    "восемьсот": 800, "девятьсот": 900,
    "тысяча": 1000, "тысячи": 1000, "тысяч": 1000,
}

#: Нормализовать ли числительные в цифры при подсчёте WER/CER.
NUMBERS_TO_DIGITS = True


def collapse_russian_numbers(words: list[str]) -> list[str]:
    """Слить идущие подряд русские числительные в цифры.

    «тридцать один» → «31», «сто двадцать три» → «123», «две тысячи» → «2000».
    Обычные слова не изменяются.
    """
    if not NUMBERS_TO_DIGITS:
        return words
    out: list[str] = []
    i, n = 0, len(words)
    while i < n:
        if words[i] in _RU_NUMBERS:
            total = 0
            while i < n and words[i] in _RU_NUMBERS:
                val = _RU_NUMBERS[words[i]]
                if val >= 1000:
                    total = total * val if total else val
                elif val >= 100:
                    total += val if total else val
                else:
                    total += val
                i += 1
            out.append(str(total))
        else:
            out.append(words[i])
            i += 1
    return out


def normalize_words(text: str) -> list[str]:
    """Нормализация для сравнения: lowercase, ё→е, только слова.

    Числительные переводятся в цифры («тридцать один» → «31»), чтобы
    метрики были честными для адресов с номерами домов.
    Отключить можно через ``NUMBERS_TO_DIGITS = False``.
    """
    return collapse_russian_numbers(
        _TOKEN_RE.findall(text.lower().replace("ё", "е"))
    )


def normalize_chars(text: str) -> list[str]:
    """Символы (буквы и цифры) без пробелов/пунктуации — для CER."""
    return list("".join(normalize_words(text)))


def levenshtein(a: list[str], b: list[str]) -> int:
    """Расстояние Левенштейна между последовательностями токенов."""
    if len(a) < len(b):
        a, b = b, a
    i_len, j_len = len(a), len(b)
    if j_len == 0:
        return i_len
    prev = list(range(j_len + 1))
    for i in range(1, i_len + 1):
        cur = [i]
        ca = a[i - 1]
        for j in range(1, j_len + 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != b[j - 1])))
        prev = cur
    return prev[-1]


def word_error_rate(ref: str, hyp: str) -> float | None:
    """WER = edit-расстояние по словам / число слов эталона.

    None — если в эталоне нет слов (оценивать нечего).
    """
    ref_words = normalize_words(ref)
    if not ref_words:
        return None
    hyp_words = normalize_words(hyp)
    if not hyp_words:
        return 1.0
    return levenshtein(ref_words, hyp_words) / len(ref_words)


def char_error_rate(ref: str, hyp: str) -> float | None:
    """CER — то же самое, но посимвольно."""
    ref_chars = normalize_chars(ref)
    if not ref_chars:
        return None
    hyp_chars = normalize_chars(hyp)
    if not hyp_chars:
        return 1.0
    return levenshtein(ref_chars, hyp_chars) / len(ref_chars)


def fmt_pct(value: float | None, digits: int = 1) -> str:
    """Отформатировать долю (0..1) в проценты; None → «—»."""
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%"


def fmt_sec(seconds: float) -> str:
    return f"{seconds:.1f} с"


# ---------------------------------------------------------------------------
# Данные результата
# ---------------------------------------------------------------------------


@dataclass
class FileResult:
    """Результат распознавания одного аудиофайла одной моделью."""

    name: str                 # имя файла, например 01.ogg
    ground_truth: str         # эталон из <имя>.txt (может быть пустым)
    recognized: str           # текст, вернувшийся от STT
    duration_ms: int          # длительность аудио
    http_time_ms: float       # время HTTP-запроса, мс
    wer: float | None         # None — нет эталона или оценить нельзя
    cer: float | None
    fmt: str = "wav"          # формат отправки: wav | ulaw | alaw
    error: str = ""           # описания ошибок (декодирование, HTTP, 413 …)


@dataclass
class ModelResult:
    """Результаты прогона всех файлов на одной модели."""

    model_id: str             # rnnt / ctc
    stt_model_env: str        # gigaam-v3-rnnt и т.п.
    device: str
    base_url: str
    health: dict[str, Any] = field(default_factory=dict)
    startup_sec: float = 0.0  # время до stt_loaded=true
    elapsed_sec: float = 0.0  # время прогона всех файлов
    files: list[FileResult] = field(default_factory=list)

    # --- вспомогательные агрегаты ---------------------------------------
    @property
    def scored(self) -> list[FileResult]:
        """Файлы с оценимыми метриками (есть эталон и успешный ответ)."""
        return [f for f in self.files if f.wer is not None and not f.error]

    @property
    def errors(self) -> list[FileResult]:
        return [f for f in self.files if f.error]

    def mean_wer(self) -> float | None:
        scored = self.scored
        return sum(f.wer for f in scored) / len(scored) if scored else None

    def mean_cer(self) -> float | None:
        scored = self.scored
        return sum(f.cer for f in scored) / len(scored) if scored else None

    def exact_count(self) -> int:
        """Число файлов со 100% распознаванием (WER == 0)."""
        return sum(1 for f in self.scored if f.wer == 0.0)

    def empty_count(self) -> int:
        """Число успешных ответов с пустым распознанным текстом."""
        return sum(1 for f in self.files if not f.error and not f.recognized.strip())

    def ref_words(self) -> int:
        return sum(len(normalize_words(f.ground_truth)) for f in self.scored)
# ---------------------------------------------------------------------------
# Декодирование аудио в WAV (PCM16) для отправки на сервер
# ---------------------------------------------------------------------------


def pack_pcm16_wav(samples: np.ndarray, sample_rate: int) -> bytes:
    """Упаковать int16-сэмплы (моно) в WAV-буфер."""
    samples = np.asarray(samples, dtype=np.int16).reshape(-1)
    buf = io.BytesIO()
    with sf.SoundFile(buf, "w", samplerate=sample_rate, channels=1,
                      format="WAV", subtype="PCM_16") as wav:
        wav.write(samples)
    return buf.getvalue()


def _decode_with_torchaudio(path: Path) -> tuple[np.ndarray, int]:
    """Фолбэк-декодер на torchaudio (mp3/m4a/opus/wma и пр.)."""
    import torchaudio  # локальный импорт — нужен только для редких форматов

    wav, sample_rate = torchaudio.load(str(path))
    if wav.ndim > 1:
        wav = wav.mean(dim=0)          # стерео → моно
    pcm = (wav.clamp(-1.0, 1.0) * 32767.0).short().numpy()
    return pcm, int(sample_rate)


def decode_to_pcm16(path: Path) -> tuple[np.ndarray, int]:
    """Декодировать аудиофайл в моно PCM16 (int16) и вернуть (samples, sr).

    Порядок декодеров: libsndfile (wav/flac/ogg/mp3) → torchaudio (всё остальное).
    G.711 µ-law/A-law читаются как RAW-потоки (как в телефонии GoIP).
    """
    ext = path.suffix.lower()
    if ext in (".ulaw", ".alaw"):
        subtype = "ULAW" if ext == ".ulaw" else "ALAW"
        data, sr = sf.read(str(path), dtype="int16", format="RAW",
                           channels=1, samplerate=TELEPHONY_SAMPLE_RATE,
                           subtype=subtype)
        return np.asarray(data, dtype=np.int16), int(sr)

    try:
        data, sr = sf.read(str(path), dtype="int16", always_2d=False)
    except Exception:
        data, sr = _decode_with_torchaudio(path)

    if sr == 0 or data.size == 0:
        raise ValueError("пустой или битый аудиофайл")
    if data.ndim > 1:
        data = np.mean(data, axis=1).astype(np.int16)   # стерео → моно
    return np.asarray(data, dtype=np.int16), int(sr)


def decode_audio_as_wav(path: Path) -> tuple[bytes, int]:
    """Декодировать аудиофайл в WAV (PCM16) и вернуть (wav_bytes, sample_rate)."""
    samples, sample_rate = decode_to_pcm16(path)
    return pack_pcm16_wav(samples, sample_rate), sample_rate


def resample_int16(samples: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
    """Ресемплинг int16-сэмплов линейной интерполяцией (как в test_telephony_mic)."""
    if from_rate == to_rate or samples.size == 0:
        return samples
    target_len = max(1, round(len(samples) * to_rate / from_rate))
    x_old = np.linspace(0.0, 1.0, num=len(samples), endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=target_len, endpoint=False)
    resampled = np.interp(x_new, x_old, samples.astype(np.float32))
    return np.clip(resampled, -32768, 32767).astype(np.int16)


def encode_pcm16_to_g711(samples: np.ndarray, codec: str) -> bytes:
    """Упаковать PCM16 в RAW G.711 (ULAW|ALAW) 8 кГц для телефонии."""
    buf = io.BytesIO()
    with sf.SoundFile(
        buf, "w", samplerate=TELEPHONY_SAMPLE_RATE, channels=1,
        format="RAW", subtype=codec,
    ) as f:
        f.write(samples)
    return buf.getvalue()


def prepare_audio_payload(path: Path, fmt: str) -> tuple[bytes, str, str]:
    """Подготовить аудиофайл к отправке: (payload_bytes, filename, content_type).

    * fmt='wav'  — несжатый WAV в исходной частоте (PCM16);
    * fmt='ulaw' — телефонный G.711 μ-law 8 кГц (как с GoIP-шлюза);
    * fmt='alaw' — телефонный G.711 A-law 8 кГц (E1/PBX).
    """
    samples, sample_rate = decode_to_pcm16(path)

    if fmt == "wav":
        payload = pack_pcm16_wav(samples, sample_rate)
    else:
        codec = "ULAW" if fmt == "ulaw" else "ALAW"
        samples_8k = resample_int16(samples, sample_rate, TELEPHONY_SAMPLE_RATE)
        payload = encode_pcm16_to_g711(samples_8k, codec)

    ext, content_type = AUDIO_FORMATS[fmt]
    return payload, f"{path.stem}{ext}", content_type


# ---------------------------------------------------------------------------
# HTTP-общение с сервисом
# ---------------------------------------------------------------------------


@dataclass
class TranscribeResponse:
    """Ответ POST /api/v1/transcribe."""

    text: str
    duration_ms: int
    http_time_ms: float
    status_code: int
    error: str = ""


def send_to_server(base_url: str, payload: bytes, filename: str,
                   content_type: str, timeout: float) -> TranscribeResponse:
    """Отправить аудио на /api/v1/transcribe с ретраями на 5xx/сетевые ошибки."""
    url = base_url.rstrip("/") + "/api/v1/transcribe"
    files = {"audio": (filename, payload, content_type)}
    started = time.perf_counter()
    last_error = ""

    for attempt in range(3):
        try:
            resp = requests.post(url, files=files, timeout=timeout)
            http_time = (time.perf_counter() - started) * 1000.0
            if resp.status_code == 200:
                data = resp.json()
                return TranscribeResponse(
                    text=str(data.get("text", "")),
                    duration_ms=int(data.get("duration_ms", 0)),
                    http_time_ms=http_time, status_code=200,
                )
            if resp.status_code in (400, 413, 503):
                return TranscribeResponse(
                    text="", duration_ms=0, http_time_ms=http_time,
                    status_code=resp.status_code,
                    error=f"HTTP {resp.status_code}: {resp.text[:300]}",
                )
            last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(1.5 * (attempt + 1))

    return TranscribeResponse(
        text="", duration_ms=0,
        http_time_ms=(time.perf_counter() - started) * 1000.0,
        status_code=0, error=f"запрос не удался: {last_error}",
    )


def fetch_health(base_url: str, timeout: float = 5.0) -> dict[str, Any] | None:
    """GET /health; None, если ответить не удалось."""
    try:
        resp = requests.get(base_url.rstrip("/") + "/health", timeout=timeout)
        if resp.ok:
            return dict(resp.json())
    except requests.RequestException:
        return None
    return None
# ---------------------------------------------------------------------------
# Запуск/остановка собственного экземпляра speech-service
# ---------------------------------------------------------------------------


def find_free_port() -> int:
    """Найти свободный TCP-порт на localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def resolve_uvicorn(workdir: Path) -> list[str]:
    """Команда запуска uvicorn: .venv → uv run → системный uvicorn."""
    venv_uvicorn = workdir / ".venv" / "bin" / "uvicorn"
    if venv_uvicorn.exists():
        return [str(venv_uvicorn)]
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "uvicorn"]
    uvicorn = shutil.which("uvicorn")
    if uvicorn:
        return [uvicorn]
    raise SystemExit(
        "Не найден uvicorn. Активируйте venv speech-service "
        "(source .venv/bin/activate) или установите uv."
    )


class SpawnedServer:
    """Обёртка над процессом uvicorn (поднятым для одной модели)."""

    def __init__(self, proc: subprocess.Popen, log_path: Path, base_url: str) -> None:
        self.proc = proc
        self.log_path = log_path
        self.base_url = base_url

    @property
    def port(self) -> int:
        return int(self.base_url.rsplit(":", 1)[1])

    def alive(self) -> bool:
        return self.proc.poll() is None

    def stop(self) -> None:
        """Мягко завершить процесс uvicorn (терминация → kill через 15 с)."""
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=10)

    def tail_log(self, n: int = 40) -> str:
        """Последние строки лога сервера (для диагностики падений)."""
        try:
            lines = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            return "\n".join(lines[-n:])
        except OSError:
            return "<лог недоступен>"


def spawn_server(args: argparse.Namespace, stt_model_env: str,
                 port: int) -> SpawnedServer:
    """Поднять speech-service с нужной STT_MODEL на заданном порту."""
    log_dir = args.workdir / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"{stt_model_env}_{port}.log"

    cmd = [*resolve_uvicorn(args.workdir), "app.main:app",
           "--host", "127.0.0.1", "--port", str(port)]

    env = os.environ.copy()
    env.update({
        "STT_MODEL": stt_model_env,
        "STT_DEVICE": args.device,
        "STT_FALLBACK_TO_CPU": "true",
    })

    with open(log_path, "ab") as logf:
        proc = subprocess.Popen(
            cmd, cwd=str(args.workdir), env=env,
            stdout=logf, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print(c(C.CYAN, f"  старт сервера: {' '.join(cmd)} "
                    f"(STT_MODEL={stt_model_env}, STT_DEVICE={args.device})"))
    print(c(C.DIM, f"  лог: {log_path}"))
    return SpawnedServer(proc, log_path, f"http://127.0.0.1:{port}")


def wait_stt_loaded(server: SpawnedServer, args: argparse.Namespace,
                    model_id: str) -> dict[str, Any]:
    """Ждать /health со stt_loaded=true; вернуть данные /health."""
    deadline = time.monotonic() + args.startup_timeout
    started = time.monotonic()
    last_logged = 0

    while time.monotonic() < deadline:
        if not server.alive():
            raise RuntimeError(
                f"сервер упал при загрузке модели {model_id}.\n"
                f"--- хвост лога ---\n{server.tail_log()}"
            )
        health = fetch_health(server.base_url)
        if health and health.get("stt_loaded"):
            return health
        elapsed = int(time.monotonic() - started)
        if elapsed - last_logged >= 10:
            last_logged = elapsed
            print(c(C.DIM, f"  ⏳ {model_id}: ждём загрузку модели… "
                           f"{elapsed} с"))
        time.sleep(1)

    raise TimeoutError(
        f"Модель {model_id} не загрузилась за {args.startup_timeout} с.\n"
        f"--- хвост лога ---\n{server.tail_log()}"
    )


# ---------------------------------------------------------------------------
# Поиск аудиофайлов и эталонов
# ---------------------------------------------------------------------------


def discover_audio(audio_dir: Path, limit: int = 0) -> list[Path]:
    """Отсортированный список аудиофайлов в папке (подхватывает новые файлы)."""
    files = sorted(
        p for p in audio_dir.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS
    )
    if limit:
        files = files[:limit]
    return files


def load_ground_truth(audio_path: Path) -> str:
    """Эталонная транскрипция из <имя>.txt рядом с аудио (пусто, если нет)."""
    txt = audio_path.with_suffix(".txt")
    if txt.is_file():
        return txt.read_text(encoding="utf-8").strip()
    return ""
# ---------------------------------------------------------------------------
# Отчёты
# ---------------------------------------------------------------------------


def _max_name_width(files: list[Path]) -> int:
    return max((len(p.name) for p in files), default=10)


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def print_file_line(fr: FileResult, verbose: bool) -> None:
    """Одна строка по файлу внутри отчёта модели."""
    if fr.error:
        print(c(C.RED, f"  ✗ {fr.name}: {fr.error}"))
        return
    metrics = f"WER {fmt_pct(fr.wer)} · CER {fmt_pct(fr.cer)}"

    if fr.ground_truth.strip():
        words = len(normalize_words(fr.ground_truth))
        label = c(C.GREEN, "эталон") if fr.wer == 0.0 else c(C.YELLOW, "эталон")
        print(f"  {c(C.GREEN, '✓')} {fr.name} · fmt {fr.fmt} · "
              f"{label}: {words} сл. · {metrics}"
              f" · дл. {fr.duration_ms} мс · HTTP {fr.http_time_ms:.0f} мс")
    else:
        print(f"  {c(C.GREEN, '✓')} {fr.name} · fmt {fr.fmt} · "
              f"{c(C.DIM, 'без эталона')} · "
              f"дл. {fr.duration_ms} мс · HTTP {fr.http_time_ms:.0f} мс")

    if fr.ground_truth.strip() and verbose:
        print(f"      эталон     : {_truncate(fr.ground_truth, 120)}")
        print(f"      распознано : {_truncate(fr.recognized, 120)}")


def print_model_report(res: ModelResult, verbose: bool) -> None:
    """Развёрнутый отчёт по одной модели."""
    print()
    print(c(C.BOLD, f"=== Модель: {res.model_id} ({res.stt_model_env}) "
                    f"— устройство: {res.device} ==="))
    print(c(C.DIM, f"    health: {json.dumps(res.health, ensure_ascii=False)}"))
    print(c(C.DIM, f"    загрузка модели: {fmt_sec(res.startup_sec)} · "
                   f"прогон файлов: {fmt_sec(res.elapsed_sec)}"))

    for fr in res.files:
        print_file_line(fr, verbose)

    scored = res.scored
    errors = res.errors
    empty = [f for f in res.files if not f.error and not f.recognized.strip()]

    print()
    print(f"  Итог по {len(res.files)} файлам: "
          f"{c(C.GREEN, f'{len(scored)} c эталоном')} · "
          f"{c(C.RED, f'{len(errors)} ошибок')} · "
          f"{c(C.YELLOW, f'{len(empty)} пустых ответов')}")
    if scored:
        print(f"  Средний WER: {fmt_pct(res.mean_wer())} · "
              f"Средний CER: {fmt_pct(res.mean_cer())} · "
              f"Точных (WER=0): {res.exact_count()}/{len(scored)}")


def print_summary(results: list[ModelResult]) -> None:
    """Сводная таблица сравнения моделей (лучшие — сверху)."""
    print()
    print(c(C.BOLD, "=== Сравнение моделей ==="))
    if not results:
        print("  Нет результатов.")
        return

    header = (f"{'Модель':<8} {'Файлов':>7} {'Сред.WER':>9} "
              f"{'Сред.CER':>9} {'Точных':>7} {'Пустых':>7} {'Время':>9}")
    print("  " + header)
    print("  " + "-" * len(header))

    def sort_key(r: ModelResult) -> tuple:
        mw = r.mean_wer()
        return (mw if mw is not None else 99.0, r.model_id)

    for r in sorted(results, key=sort_key):
        exact = f"{r.exact_count()}/{len(r.scored)}"
        print(f"  {c(C.BOLD, r.model_id):<8} {len(r.scored):>7} "
              f"{fmt_pct(r.mean_wer()):>9} {fmt_pct(r.mean_cer()):>9} "
              f"{exact:>7} {r.empty_count():>7} "
              f"{fmt_sec(r.startup_sec + r.elapsed_sec):>9}")

    best = min(results, key=lambda r: r.mean_wer() or 99.0)
    print()
    print(c(C.GREEN, f"  Лучшая модель: {best.model_id} "
                     f"(средний WER {fmt_pct(best.mean_wer())})"))


# ---------------------------------------------------------------------------
# Прогон теста
# ---------------------------------------------------------------------------


def run_files_on_server(args: argparse.Namespace, base_url: str,
                        files: list[Path]) -> list[FileResult]:
    """Прогнать все аудиофайлы через /api/v1/transcribe на одном сервере."""
    results: list[FileResult] = []
    n = len(files)
    for i, path in enumerate(files, 1):
        print(c(C.DIM, f"  [{i}/{n}] {path.name} ({args.format}) …"))
        gt = load_ground_truth(path)

        try:
            payload, filename, content_type = prepare_audio_payload(path, args.format)
        except Exception as exc:  # noqa: BLE001 — любая проблема декодирования
            results.append(FileResult(
                name=path.name, ground_truth=gt, recognized="",
                duration_ms=0, http_time_ms=0.0,
                wer=None, cer=None, fmt=args.format,
                error=f"не удалось декодировать: {exc}",
            ))
            continue

        resp = send_to_server(base_url, payload, filename, content_type,
                              args.timeout)
        if resp.error:
            results.append(FileResult(
                name=path.name, ground_truth=gt, recognized="",
                duration_ms=0, http_time_ms=resp.http_time_ms,
                wer=None, cer=None, fmt=args.format, error=resp.error,
            ))
            continue

        if resp.duration_ms > MAX_AUDIO_DURATION_SEC * 1000:
            results.append(FileResult(
                name=path.name, ground_truth=gt, recognized="",
                duration_ms=resp.duration_ms, http_time_ms=resp.http_time_ms,
                wer=None, cer=None, fmt=args.format,
                error=f"аудио слишком длинное ({resp.duration_ms} мс > "
                      f"{MAX_AUDIO_DURATION_SEC * 1000} мс) — сервер отдал бы 413",
            ))
            continue

        results.append(FileResult(
            name=path.name, ground_truth=gt, recognized=resp.text,
            duration_ms=resp.duration_ms, http_time_ms=resp.http_time_ms,
            wer=word_error_rate(gt, resp.text),
            cer=char_error_rate(gt, resp.text), fmt=args.format,
        ))

    return results


def run_spawned_model(args: argparse.Namespace, model_id: str,
                      files: list[Path], models: list[ModelResult]) -> None:
    """Поднять сервер с моделью, прогнать файлы, напечатать отчёт, завершить."""
    stt_model_env = SUPPORTED_MODELS[model_id]
    port = args.port if args.port else find_free_port()
    server = spawn_server(args, stt_model_env, port)

    startup_started = time.perf_counter()
    try:
        health = wait_stt_loaded(server, args, model_id)
    except (RuntimeError, TimeoutError) as exc:
        print(c(C.RED, f"  ✖ Не удалось поднять модель {model_id}: {exc}"))
        server.stop()
        return
    startup_sec = time.perf_counter() - startup_started

    print(c(C.GREEN, f"  ✔ модель {model_id} загружена за {fmt_sec(startup_sec)}: "
                     f"{health.get('stt_model')}, device={health.get('device')}"))

    started = time.perf_counter()
    results = run_files_on_server(args, server.base_url, files)
    elapsed_sec = time.perf_counter() - started

    model_result = ModelResult(
        model_id=model_id, stt_model_env=stt_model_env,
        device=args.device, base_url=server.base_url, health=health,
        startup_sec=startup_sec, elapsed_sec=elapsed_sec, files=results,
    )
    models.append(model_result)
    print_model_report(model_result, args.verbose)

    if args.keep_running:
        print(c(C.YELLOW, f"  Сервер модели {model_id} продолжает работать: "
                          f"{server.base_url} (лог: {server.log_path})"))
    else:
        server.stop()


def run_against_existing(args: argparse.Namespace,
                         files: list[Path]) -> list[ModelResult]:
    """Прогон против уже запущенного speech-service (--server-url)."""
    base_url = args.server_url
    health = fetch_health(base_url)
    if health is None:
        raise SystemExit(f"Нет ответа от сервера {base_url} (GET /health). "
                         f"Убедитесь, что сервис запущен.")
    if not health.get("stt_loaded"):
        raise SystemExit(f"STT не загружен на {base_url}: {health}")

    model_id = str(health.get("stt_model", "unknown"))
    print(c(C.GREEN, f"Сервер {base_url} → модель {model_id}, "
                     f"device={health.get('device')}"))

    started = time.perf_counter()
    results = run_files_on_server(args, base_url, files)
    elapsed_sec = time.perf_counter() - started

    model_result = ModelResult(
        model_id=model_id, stt_model_env=model_id,
        device=str(health.get("device", "?")),
        base_url=base_url, health=health, startup_sec=0.0,
        elapsed_sec=elapsed_sec, files=results,
    )
    print_model_report(model_result, args.verbose)
    return [model_result]


def save_json(results: list[ModelResult], path: Path) -> None:
    """Сохранить подробные результаты в JSON."""
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "models": [
            {
                "model_id": r.model_id,
                "stt_model_env": r.stt_model_env,
                "device": r.device,
                "base_url": r.base_url,
                "startup_sec": round(r.startup_sec, 2),
                "elapsed_sec": round(r.elapsed_sec, 2),
                "mean_wer": r.mean_wer(),
                "mean_cer": r.mean_cer(),
                "exact_count": r.exact_count(),
                "files": [
                    {
                        "name": f.name,
                        "ground_truth": f.ground_truth,
                        "recognized": f.recognized,
                        "duration_ms": f.duration_ms,
                        "http_time_ms": round(f.http_time_ms, 1),
                        "wer": f.wer,
                        "cer": f.cer,
                        "fmt": f.fmt,
                        "error": f.error,
                    }
                    for f in r.files
                ],
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(c(C.CYAN, f"Результаты сохранены в {path}"))
# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_models(value: str) -> list[str]:
    """Разобрать список моделей через запятую и проверить поддержку."""
    parts = [p.strip().lower() for p in value.split(",") if p.strip()]
    unknown = [p for p in parts if p not in SUPPORTED_MODELS]
    if unknown:
        raise SystemExit(
            f"Неизвестные модели: {', '.join(unknown)}. "
            f"Доступны: {', '.join(SUPPORTED_MODELS)}."
        )
    if not parts:
        raise SystemExit("Список --models пуст.")
    return parts


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="test_stt_models.py",
        description="Тестирование распознавания речи speech-service "
                    "на разных моделях GigaAM (WER/CER по аудио из папки audio).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  uv run python test_stt_models.py\n"
            "  uv run python test_stt_models.py --models ctc --verbose\n"
            "  uv run python test_stt_models.py "
            "--server-url http://localhost:8001\n"
        ),
    )
    parser.add_argument(
        "--audio-dir", type=Path, default=None,
        help="Папка с аудио и эталонными .txt (по умолчанию "
             "<repo>/speech-service/audio).",
    )
    parser.add_argument(
        "--models", default=DEFAULT_MODELS,
        help=f"Модели GigaAM через запятую: {', '.join(SUPPORTED_MODELS)} "
             f"(по умолчанию '{DEFAULT_MODELS}').",
    )
    parser.add_argument(
        "--format", default=DEFAULT_FORMAT,
        choices=list(AUDIO_FORMATS),
        help=f"Формат отправки аудио на сервер (по умолчанию '{DEFAULT_FORMAT}'): "
             f"wav — несжатый PCM16; ulaw — G.711 μ-law 8 кГц "
             f"(телефонный трафик GoIP); alaw — G.711 A-law 8 кГц.",
    )
    parser.add_argument(
        "--server-url", default=None,
        help="URL уже запущенного speech-service, напр. http://localhost:8001. "
             "В этом режиме сервер не поднимается, --models игнорируются.",
    )
    parser.add_argument(
        "--device", default=None,
        help="Устройство: cpu | cuda:0 (по умолчанию STT_DEVICE из env или cpu).",
    )
    parser.add_argument(
        "--workdir", type=Path, default=None,
        help="Корень speech-service (где лежит app.main). "
             "По умолчанию — папка этого скрипта.",
    )
    parser.add_argument(
        "--port", type=int, default=0,
        help="Порт для поднимаемых серверов (0 — свободный порт автоматом).",
    )
    parser.add_argument(
        "--startup-timeout", type=float, default=900.0,
        help="Сколько ждать загрузку модели (сек), по умолчанию 900.",
    )
    parser.add_argument(
        "--timeout", type=float, default=180.0,
        help="Таймаут одного POST /transcribe (сек), по умолчанию 180.",
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Ограничить число аудиофайлов (0 — все).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Печатать эталон и распознанный текст для каждого файла.",
    )
    parser.add_argument(
        "--json", type=Path, default=None, metavar="PATH",
        help="Сохранить подробный отчёт в JSON.",
    )
    parser.add_argument(
        "--keep-running", action="store_true",
        help="Не завершать поднятый сервер после теста.",
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Отключить цвета в выводе.",
    )
    return parser


def main() -> None:
    global NO_COLOR

    parser = build_arg_parser()
    args = parser.parse_args()
    NO_COLOR = args.no_color

    args.workdir = (args.workdir or BASE_DIR).resolve()
    args.audio_dir = (args.audio_dir or default_audio_dir()).resolve()
    args.device = args.device or default_device()

    files = discover_audio(args.audio_dir, args.limit)
    if not files:
        raise SystemExit(
            f"В папке {args.audio_dir} не найдено аудиофайлов "
            f"({', '.join(AUDIO_EXTS)}). Добавьте аудио и повторите."
        )

    print(c(C.BOLD, "=== Тест STT: GigaAM на аудио из папки audio ==="))
    print(c(C.DIM, f"  папка аудио: {args.audio_dir} · файлов: {len(files)} · "
                   f"формат: {args.format}"))
    if args.format != "wav":
        print(c(C.YELLOW, f"  ⚠ телефонный режим: аудио конвертируется в "
                          f"G.711 {args.format.upper()} 8 кГц "
                          f"(как трафик GoIP)"))
    if args.server_url:
        print(c(C.DIM, f"  сервер: {args.server_url} (без авто-запуска)"))
    else:
        models = parse_models(args.models)
        print(c(C.DIM, f"  модели: {', '.join(models)} · "
                       f"устройство: {args.device}"))

    try:
        if args.server_url:
            results = run_against_existing(args, files)
        else:
            models = parse_models(args.models)
            print()
            results: list[ModelResult] = []
            for model_id in models:
                run_spawned_model(args, model_id, files, results)
    except KeyboardInterrupt:
        print(c(C.YELLOW, "\nПрервано пользователем (Ctrl+C)."))
        return

    if results:
        print_summary(results)
        if args.json:
            save_json(results, args.json)


if __name__ == "__main__":
    main()