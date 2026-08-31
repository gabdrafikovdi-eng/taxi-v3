"""FastAPI-приложение speech-service.

STT: GigaAM (v2/v3/multilingual) через единый ASR-протокол;
TTS: edge-tts; VAD: Silero.

Production-ручки:
* ``POST /api/v1/transcribe`` — одна production-модель (``STT_MODEL``);
* ``POST /api/v1/transcribe/stream`` — псевдо-потоковая (по фразе за POST);
* ``POST /api/v1/benchmark/transcribe`` — исследовательская: все модели
  последовательно, одна за другой (load → infer → unload);
* ``POST /api/v1/synthesize`` — TTS;
* ``GET /health`` — статус.
"""

from __future__ import annotations

import asyncio
import io
import tempfile
import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.audio import converter
from app.config import settings
from app.logging import get_logger, setup_logging
from app.stt.benchmark import BenchmarkRunner
from app.stt.client import STTClient
from app.stt.factory import STTModelFactory, pick_stt_device
from app.stt.registry import BENCHMARK_MODEL_KEYS, canonical_model_key
from app.stt.vad import VAD
from app.tts.client import TTSClient

setup_logging()
logger = get_logger(__name__)


class SynthesizeRequest(BaseModel):
    text: str
    speaker: str | None = Field(
        default=None, description="Голос TTS (например, ru-RU-DmitryNeural)"
    )


class ModelState:
    """Состояние сервиса: загруженные модели и production-выбор."""

    def __init__(self) -> None:
        self.stt: STTClient | None = None
        self.stt_factory: STTModelFactory | None = None
        self.tts: TTSClient | None = None
        self.vad: VAD | None = None
        try:
            self.stt_model_name = canonical_model_key(settings.STT_MODEL)
        except ValueError:
            # Невалидная модель не роняет startup — ошибка будет в логах,
            # health вернёт сырое имя.
            self.stt_model_name = settings.STT_MODEL
        self.stt_device: str = "cpu"
        self.gpu_available: bool = False


# Сериализация benchmark-запросов: нельзя запускать несколько моделей
# одновременно на машине с 8 GB unified memory.
_benchmark_lock = asyncio.Lock()

# Сериализация ленивой перезагрузки production-модели (после benchmark-выгрузки):
# без неё параллельные запросы загрузили бы модель дважды.
_stt_reload_lock = threading.Lock()


def _load_stt(models: ModelState) -> None:
    """Загрузить production-модель и factory (для benchmark) на выбранном device."""
    try:
        device = pick_stt_device(settings.STT_DEVICE, settings.STT_FALLBACK_TO_CPU)
    except Exception:
        logger.exception("stt_device_selection_failed", stt_model=settings.STT_MODEL)
        return
    models.stt_device = device

    try:
        factory = STTModelFactory(model_key=settings.STT_MODEL, device=device)
    except ValueError as exc:
        logger.error(
            "stt_model_load_failed",
            stt_model=settings.STT_MODEL,
            device=device,
            error=str(exc),
        )
        return

    try:
        adapter, _ = factory.load()
    except Exception:
        logger.exception(
            "stt_model_load_failed", stt_model=settings.STT_MODEL, device=device
        )
        return

    models.stt_factory = factory
    models.stt = STTClient(adapter)
    models.stt_model_name = adapter.name


def _load_vad(models: ModelState) -> None:
    try:
        from silero_vad import load_silero_vad
    except Exception:
        logger.exception("vad_import_failed")
        return

    started = time.perf_counter()
    try:
        model = load_silero_vad()
    except Exception:
        logger.exception("vad_load_failed")
        return

    models.vad = VAD(model)
    logger.info(
        "vad_loaded",
        model_name="silero-vad",
        device="cpu",
        load_time_sec=round(time.perf_counter() - started, 2),
    )


def _load_tts(models: ModelState) -> None:
    """Инициализация edge-tts клиента. Не требует загрузки тяжёлых моделей."""
    logger.info("Initializing edge-tts client (no local model download required)...")
    models.tts = TTSClient(default_voice=settings.TTS_VOICE)
    logger.info(
        "tts_loaded",
        model_name="edge-tts",
        device="cloud",
        load_time_sec=0.01,
    )


def _release_stt_for_benchmark(models: ModelState) -> bool:
    """Выгрузить production-модель на время benchmark (если включено настройкой).

    Benchmark сам загружает модели по одной (load → infer → unload); держать
    параллельно ещё и production-модель на машине с 8 GB unified memory
    расточительно. Production-ручки позже перезагрузят модель лениво
    (``_reload_stt``). Обычный startup при этом не меняется.

    :return: True, если модель была выгружена.
    """
    if not settings.STT_BENCHMARK_RELEASES_PRODUCTION or models.stt is None:
        return False
    stt, models.stt = models.stt, None
    unload = getattr(stt.model, "unload", None)
    if callable(unload):
        unload()
    logger.info("stt_production_released_for_benchmark", model=stt.model_name)
    return True


def _reload_stt(models: ModelState) -> STTClient | None:
    """Лениво перезагрузить production-модель (после benchmark-выгрузки).

    Потокобезопасно: повторная проверка под блокировкой исключает двойную
    загрузку при параллельных production-запросах.
    """
    with _stt_reload_lock:
        if models.stt is not None:
            return models.stt
        factory = models.stt_factory
        if factory is None:
            return None
        try:
            adapter, load_time_ms = factory.load()
        except Exception:
            logger.exception(
                "stt_model_load_failed",
                stt_model=models.stt_model_name,
                reason="lazy_reload_after_benchmark",
            )
            return None
        models.stt = STTClient(adapter)
        models.stt_model_name = adapter.name
        logger.info(
            "stt_production_reloaded",
            model=adapter.name,
            load_time_ms=round(load_time_ms, 1),
            reason="lazy_reload_after_benchmark",
        )
        return models.stt


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    models = ModelState()
    models.gpu_available = torch.cuda.is_available()

    await asyncio.to_thread(_load_stt, models)
    await asyncio.to_thread(_load_vad, models)
    await asyncio.to_thread(_load_tts, models)

    app.state.models = models
    logger.info(
        "service_startup_complete",
        stt_loaded=models.stt is not None,
        vad_loaded=models.vad is not None,
        tts_loaded=models.tts is not None,
        gpu_available=models.gpu_available,
        stt_device=models.stt_device,
        stt_model=models.stt_model_name,
    )
    yield
    app.state.models = None
# ---------------------------------------------------------------------------
# Middleware / исключения / вспомогательные функции
# ---------------------------------------------------------------------------


app = FastAPI(title="speech-service", version="0.1.0", lifespan=lifespan)


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    started = time.perf_counter()
    response = await call_next(request)
    logger.info(
        "request_finished",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
    )
    return response


app.middleware("http")(log_requests)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.warning(
        "http_error",
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception", path=request.url.path, method=request.method
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def _require_models(request: Request) -> tuple[STTClient, VAD]:
    models: ModelState | None = getattr(request.app.state, "models", None)
    if models is None or models.vad is None:
        raise HTTPException(status_code=503, detail="STT/VAD models not loaded")
    stt = models.stt
    if stt is None:
        # Модель выгружена benchmark'ом (STT_BENCHMARK_RELEASES_PRODUCTION) —
        # лениво перезагружаем при первом же production-запросе.
        stt = _reload_stt(models)
    if stt is None:
        raise HTTPException(status_code=503, detail="STT/VAD models not loaded")
    return stt, models.vad


def _require_tts(request: Request) -> TTSClient:
    models: ModelState | None = getattr(request.app.state, "models", None)
    if models is None or models.tts is None:
        raise HTTPException(status_code=503, detail="TTS client not initialized")
    return models.tts


def _require_benchmark(request: Request) -> tuple[STTModelFactory, VAD]:
    """Factory и VAD для benchmark-ручки."""
    models: ModelState | None = getattr(request.app.state, "models", None)
    if models is None or models.vad is None or models.stt_factory is None:
        raise HTTPException(status_code=503, detail="STT/VAD models not loaded")
    return models.stt_factory, models.vad


def _decode_pcm16(audio_bytes: bytes, content_type: str | None) -> tuple[bytes, int]:
    """Декодировать вход (G.711 µ-law/A-law или WAV) в PCM16 16 кГц.

    :return: ``(pcm_bytes, sample_rate)``.
    """
    content_type = (content_type or "").lower()
    if "mulaw" in content_type:
        return converter.mulaw_to_pcm16(audio_bytes)
    if "alaw" in content_type:
        return converter.alaw_to_pcm16(audio_bytes)
    return _wav_to_pcm16(audio_bytes)


def _wav_to_pcm16(audio_bytes: bytes) -> tuple[bytes, int]:
    try:
        with io.BytesIO(audio_bytes) as sock:
            data, sample_rate = sf.read(sock, dtype="int16", always_2d=False)
    except sf.LibsndfileError as exc:
        raise HTTPException(status_code=400, detail="Invalid audio file") from exc

    if data.ndim > 1:
        data = np.mean(data, axis=1).astype(np.int16)
    pcm = data.astype(np.int16).tobytes()
    if sample_rate != converter.TARGET_SAMPLE_RATE:
        pcm = converter.resample(pcm, sample_rate, converter.TARGET_SAMPLE_RATE)
        sample_rate = converter.TARGET_SAMPLE_RATE
    return pcm, int(sample_rate)
# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    models: ModelState | None = getattr(request.app.state, "models", None)
    return JSONResponse(
        {
            "status": "ok",
            "stt_loaded": models is not None and models.stt is not None,
            "stt_reloadable": models is not None
            and models.stt is None
            and models.stt_factory is not None,
            "tts_loaded": models is not None and models.tts is not None,
            "gpu_available": models.gpu_available if models is not None else False,
            "stt_model": models.stt_model_name
            if models is not None
            else settings.STT_MODEL,
            "device": models.stt_device if models is not None else "cpu",
            # Список моделей benchmark — статический из реестра, ничего не грузит.
            "available_benchmark_models": list(BENCHMARK_MODEL_KEYS),
        }
    )


@app.post("/api/v1/transcribe")
async def transcribe(request: Request, audio: UploadFile = File(...)) -> JSONResponse:
    stt, vad = _require_models(request)
    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio")

    pcm_bytes, sample_rate = _decode_pcm16(raw, audio.content_type)

    duration_ms = converter.duration_ms(pcm_bytes, sample_rate)
    if duration_ms == 0:
        raise HTTPException(status_code=400, detail="Empty audio")
    if duration_ms > settings.MAX_AUDIO_DURATION_SEC * 1000:
        raise HTTPException(status_code=413, detail="Audio too long")

    text = ""
    inference_time_ms = 0.0
    if vad.is_speech(pcm_bytes, sample_rate):
        text, inference_time_ms = await asyncio.to_thread(
            stt.transcribe, pcm_bytes, sample_rate
        )

    logger.info(
        "transcribe_finished",
        content_type=(audio.content_type or "").lower(),
        duration_ms=duration_ms,
        text_length=len(text),
        model=stt.model_name,
        inference_time_ms=round(inference_time_ms, 1),
    )
    return JSONResponse(
        {
            "text": text,
            "duration_ms": duration_ms,
            "sample_rate": sample_rate,
            "model": stt.model_name,
            "inference_time_ms": round(inference_time_ms, 1),
        }
    )


@app.post("/api/v1/benchmark/transcribe")
async def benchmark_transcribe(
    request: Request, audio: UploadFile = File(...)
) -> JSONResponse:
    factory, vad = _require_benchmark(request)
    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio")

    pcm_bytes, sample_rate = _decode_pcm16(raw, audio.content_type)

    duration_ms = converter.duration_ms(pcm_bytes, sample_rate)
    if duration_ms == 0:
        raise HTTPException(status_code=400, detail="Empty audio")
    if duration_ms > settings.MAX_AUDIO_DURATION_SEC * 1000:
        raise HTTPException(status_code=413, detail="Audio too long")

    # VAD выполняется ОДИН раз на входном аудио — для честного сравнения
    # все модели получают один и тот же сигнал.
    speech_detected = vad.is_speech(pcm_bytes, sample_rate)
    if not speech_detected:
        logger.info(
            "benchmark_finished",
            model_count=0,
            success_count=0,
            speech_detected=False,
        )
        return JSONResponse(
            {
                "duration_ms": duration_ms,
                "sample_rate": sample_rate,
                "speech_detected": False,
                "results": [],
            }
        )

    # µ-law/A-law вход декодируется в PCM 8 кГц. Production-ручка ресемплирует
    # его до 16 кГц внутри STTClient.transcribe; benchmark обязан сделать то же
    # самое ПЕРЕД упаковкой в WAV, иначе модели получат 8 кГц-семплы в
    # WAV-заголовке 16 кГц (речь ускорена в 2 раза → мусорные транскрипции).
    if sample_rate != converter.TARGET_SAMPLE_RATE:
        pcm_bytes = converter.resample(
            pcm_bytes, sample_rate, converter.TARGET_SAMPLE_RATE
        )
        sample_rate = converter.TARGET_SAMPLE_RATE

    sample_count = len(pcm_bytes) // 2
    wav_bytes = converter.to_wav(pcm_bytes, converter.TARGET_SAMPLE_RATE)

    # Опционально выгружаем production-модель: benchmark сам грузит модели
    # по одной, лишние ~0.5-1 GB в памяти на M2 (8 GB) не нужны
    # (STT_BENCHMARK_RELEASES_PRODUCTION, по умолчанию выключено).
    models_state: ModelState | None = getattr(request.app.state, "models", None)
    if models_state is not None:
        await asyncio.to_thread(_release_stt_for_benchmark, models_state)

    # Модели загружаются/выгружаются ПОСЛЕДОВАТЕЛЬНО; конкуретная работа
    # блокируется asyncio.Lock(), чтобы не упереться в память (M2, 8 GB).
    runner = BenchmarkRunner(factory)
    async with _benchmark_lock:
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="benchmark_") as tmp:
            tmp.write(wav_bytes)
            tmp.flush()
            results = await asyncio.to_thread(
                runner.run, tmp.name, sample_count
            )

    return JSONResponse(
        {
            "duration_ms": duration_ms,
            "sample_rate": sample_rate,
            "speech_detected": True,
            "results": [result.to_dict() for result in results],
        }
    )


@app.post("/api/v1/synthesize")
async def synthesize(request: Request, payload: SynthesizeRequest) -> Response:
    tts = _require_tts(request)
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    # Прямой await, так как edge-tts клиент асинхронный
    wav_bytes = await tts.synthesize(payload.text, payload.speaker)

    if not wav_bytes:
        raise HTTPException(
            status_code=500, detail="TTS synthesis returned empty audio"
        )

    return Response(content=wav_bytes, media_type="audio/wav")


@app.post("/api/v1/transcribe/stream")
async def transcribe_stream(
    request: Request,
    audio: UploadFile = File(...),
    sample_rate: int = Query(default=16000),
    silence_threshold_ms: int = Query(default=800),
) -> JSONResponse:
    stt, vad = _require_models(request)
    raw = await audio.read()
    if not raw:
        return JSONResponse({"text": "", "is_final": True})

    pcm = raw
    if sample_rate != converter.TARGET_SAMPLE_RATE:
        pcm = converter.resample(raw, sample_rate, converter.TARGET_SAMPLE_RATE)
        sample_rate = converter.TARGET_SAMPLE_RATE

    if not vad.is_speech(pcm, sample_rate):
        return JSONResponse({"text": "", "is_final": True})

    text, _ = await asyncio.to_thread(stt.transcribe, pcm, sample_rate)

    logger.info("stream_transcribed", text_length=len(text), model=stt.model_name)
    return JSONResponse({"text": text, "is_final": True})
    logger.info("service_shutdown_complete")