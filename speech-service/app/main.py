"""FastAPI-приложение speech-service: STT (GigaAM) + TTS (edge-tts) + VAD (Silero)."""

from __future__ import annotations

import asyncio
import io
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
from app.stt.client import STTClient
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
    def __init__(self) -> None:
        self.stt: STTClient | None = None
        self.tts: TTSClient | None = None
        self.vad: VAD | None = None
        self.stt_model_name: str = settings.STT_MODEL
        self.stt_device: str = "cpu"
        self.gpu_available: bool = False


def _gigaam_model_id() -> str:
    name = settings.STT_MODEL.lower().replace("-", "_").removeprefix("gigaam_")
    for key in ("rnnt", "ctc", "ssl"):
        if key in name:
            return key
    return name or "rnnt"


def _pick_stt_device() -> str:
    device = settings.STT_DEVICE.strip().lower()
    cuda_available = torch.cuda.is_available()
    if device == "cpu":
        return device
    if device.startswith("cuda") and cuda_available:
        return device
    if settings.STT_FALLBACK_TO_CPU:
        logger.warning(
            "stt_device_unavailable_fallback_to_cpu",
            requested=device,
            cuda_available=cuda_available,
        )
        return "cpu"
    raise RuntimeError(
        f"STT device '{device}' is unavailable and STT_FALLBACK_TO_CPU is disabled"
    )


def _load_stt(models: ModelState) -> None:
    try:
        import gigaam
    except Exception:
        logger.exception("gigaam_import_failed", stt_model=settings.STT_MODEL)
        return

    device = _pick_stt_device()
    model_id = _gigaam_model_id()
    started = time.perf_counter()
    try:
        model = gigaam.load_model(
            model_id,
            fp16_encoder=device != "cpu",
            use_flash=False,
            device=device,
        )
    except Exception:
        logger.exception("stt_load_failed", stt_model=settings.STT_MODEL, device=device)
        return

    models.stt_device = device
    models.stt = STTClient(model, device)
    logger.info(
        "stt_loaded",
        model_name=settings.STT_MODEL,
        device=device,
        load_time_sec=round(time.perf_counter() - started, 2),
    )


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
    """Инициализация edge-tts клиента. Не требует загрузки тяжелых моделей."""
    logger.info("Initializing edge-tts client (no local model download required)...")
    models.tts = TTSClient(default_voice="ru-RU-DmitryNeural")
    logger.info(
        "tts_loaded",
        model_name="edge-tts",
        device="cloud",
        load_time_sec=0.01,
    )


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
    logger.info("service_shutdown_complete")


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
    if models is None or models.stt is None or models.vad is None:
        raise HTTPException(status_code=503, detail="STT/VAD models not loaded")
    return models.stt, models.vad


def _require_tts(request: Request) -> TTSClient:
    models: ModelState | None = getattr(request.app.state, "models", None)
    if models is None or models.tts is None:
        raise HTTPException(status_code=503, detail="TTS client not initialized")
    return models.tts


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


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    models: ModelState | None = getattr(request.app.state, "models", None)
    return JSONResponse(
        {
            "status": "ok",
            "stt_loaded": models is not None and models.stt is not None,
            "tts_loaded": models is not None and models.tts is not None,
            "gpu_available": models.gpu_available if models is not None else False,
            "stt_model": models.stt_model_name
            if models is not None
            else settings.STT_MODEL,
            "device": models.stt_device if models is not None else "cpu",
        }
    )


@app.post("/api/v1/transcribe")
async def transcribe(request: Request, audio: UploadFile = File(...)) -> JSONResponse:
    stt, vad = _require_models(request)
    raw = await audio.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty audio")

    content_type = (audio.content_type or "").lower()
    if "mulaw" in content_type:
        pcm_bytes, sample_rate = converter.mulaw_to_pcm16(raw)
    elif "alaw" in content_type:
        pcm_bytes, sample_rate = converter.alaw_to_pcm16(raw)
    else:
        pcm_bytes, sample_rate = _wav_to_pcm16(raw)

    duration_ms = converter.duration_ms(pcm_bytes, sample_rate)
    if duration_ms == 0:
        raise HTTPException(status_code=400, detail="Empty audio")
    if duration_ms > settings.MAX_AUDIO_DURATION_SEC * 1000:
        raise HTTPException(status_code=413, detail="Audio too long")

    if vad.is_speech(pcm_bytes, sample_rate):
        text = await asyncio.to_thread(stt.transcribe, pcm_bytes, sample_rate)
    else:
        text = ""

    logger.info(
        "transcribe_finished",
        content_type=content_type,
        duration_ms=duration_ms,
        text_length=len(text),
    )
    return JSONResponse(
        {"text": text, "duration_ms": duration_ms, "sample_rate": sample_rate}
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

    text = await asyncio.to_thread(stt.transcribe, pcm, sample_rate)
    logger.info("stream_transcribed", text_length=len(text))
    return JSONResponse({"text": text, "is_final": True})
