"""
Автономный тест STT-сервиса через микрофон с использованием Silero VAD.
Полная имитация телефонного звонка: детекция начала/конца речи, конвертация в G.711 mu-law, отправка на сервер.
Оптимизировано для macOS: запись 48 кГц, внутренний ресемплинг до 16 кГц для стабильной работы Silero VAD.
"""

from __future__ import annotations

import argparse
import io
import sys
import threading
import time
from pathlib import Path

import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import torch
from silero_vad import load_silero_vad

SERVER_URL = "http://localhost:8001/api/v1/transcribe"
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
    """Конвертирует float32 аудио в G.711 mu-law 8000 Гц."""
    audio_int16 = (audio_array * 32767).astype(np.int16).flatten()
    sf.write(str(DEBUG_WAV_PATH), audio_int16, original_sr, subtype="PCM_16")

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


def send_to_server(ulaw_bytes: bytes, use_wav: bool = False) -> dict:
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

        response = requests.post(SERVER_URL, files=files, timeout=30.0)
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
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

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
    print(f"Частота записи: {REC_SAMPLE_RATE} Гц (оптимизировано для macOS)")
    print(f"Порог срабатывания: {args.threshold}")
    print(f"🎤 Устройство: [{device}] {info['name']}")
    print("Загрузка модели Silero VAD...")

    vad_model = load_silero_vad()
    vad_model.eval()

    print("✅ Модель загружена. Нажмите Ctrl+C для выхода.")
    print("=" * 60)

    is_speaking = False
    silence_chunks = 0
    buffer = []
    buffer_to_process = []
    ready_to_process = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        nonlocal is_speaking, silence_chunks, buffer, buffer_to_process

        if status:
            print(f"⚠️ Статус потока: {status}")

        # 1. Берем оригинальные данные 48 кГц для сохранения
        original_chunk = indata.flatten().astype(np.float32)

        # 2. Ресемплим до 16 кГц для VAD (простая интерполяция, для VAD этого достаточно)
        x_old = np.linspace(0.0, 1.0, num=len(original_chunk), endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=CHUNK_SAMPLES_16K, endpoint=False)
        chunk_16k = np.interp(x_new, x_old, original_chunk)

        # 3. Проверяем VAD окнами по 512 сэмплов
        has_voice = False
        for i in range(0, len(chunk_16k), VAD_WINDOW_SAMPLES):
            window = chunk_16k[i : i + VAD_WINDOW_SAMPLES]
            if len(window) < VAD_WINDOW_SAMPLES:
                window = np.pad(
                    window, (0, VAD_WINDOW_SAMPLES - len(window)), mode="constant"
                )

            tensor = torch.from_numpy(window).float()
            with torch.no_grad():
                prob = vad_model(tensor, VAD_SAMPLE_RATE).item()

            if prob >= args.threshold:
                has_voice = True
                break  # Достаточно одного окна с речью в этом блоке

        # 4. Логика конечного автомата
        if has_voice:
            if not is_speaking:
                print("\n🔴 ОБНАРУЖЕНА РЕЧЬ...")
                is_speaking = True
                buffer = []
                silence_chunks = 0
                vad_model.reset_states()

            buffer.append(original_chunk)
            silence_chunks = 0
        else:
            if is_speaking:
                silence_chunks += 1
                buffer.append(
                    original_chunk
                )  # Сохраняем хвост тишины, чтобы не обрезать слово

                if silence_chunks >= max_silence_chunks:
                    if len(buffer) < min_speech_chunks:
                        print("⚠️ Слишком короткий звук (шум), игнорируем...")
                        is_speaking = False
                        buffer = []
                        silence_chunks = 0
                        return

                    print("⏸️ ПАУЗА. Отправка на распознавание...")
                    is_speaking = False
                    buffer_to_process = buffer.copy()
                    buffer = []
                    silence_chunks = 0
                    ready_to_process.set()

    try:
        # ИСПРАВЛЕНО: float32 вместо float30
        with sd.InputStream(
            samplerate=REC_SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=device,
            blocksize=CHUNK_SAMPLES_48K,
            callback=audio_callback,
        ):
            print("🟢 Ожидание речи... (скажи что-нибудь в микрофон)")
            while True:
                if ready_to_process.is_set():
                    ready_to_process.clear()

                    if not buffer_to_process:
                        continue

                    audio_array = np.concatenate(buffer_to_process, axis=0)

                    print("⚙️ Конвертация и отправка...")
                    ulaw_bytes = convert_to_telephony_format(
                        audio_array, original_sr=REC_SAMPLE_RATE
                    )
                    result = send_to_server(ulaw_bytes, use_wav=args.use_wav)

                    print("\n" + "=" * 50)
                    print(f'🗣️  Текст: "{result.get("text", "ПУСТО")}"')
                    print(
                        f"⏱️  Длительность аудио: {result.get('duration_ms', 0)} мс | HTTP: {result.get('http_time_ms', 0)} мс"
                    )
                    print("=" * 50)
                    print("🟢 Ожидание следующей фразы...")

                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n👋 Завершение работы.")
        sys.exit(0)


if __name__ == "__main__":
    main()
