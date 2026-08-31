"""Одноразовая утилита: конвертация speech-service/audio/*.ogg в G.711 µ-law
для Asterisk Playback (self-loop тест). Использует venv speech-service.

Usage:  speech-service/.venv/bin/python make_test_sound.py
"""

import sys

import torch
import torchaudio

BASE = "/Users/dimgalin/MyProjectsVSCode/taxi-v3"


def load_ogg_8k(path: str) -> torch.Tensor:
    wav, sr = torchaudio.load(path)
    if wav.shape[0] > 1:
        wav = wav.mean(0, keepdim=True)
    if sr != 8000:
        wav = torchaudio.functional.resample(wav, sr, 8000)
    return (wav * 3.0).clamp(-1, 1)


def main() -> None:
    silence = torch.zeros(1, 8000)
    parts: list[torch.Tensor] = []
    # 8 c тишины (пока играет greeting), фраза, затем 15 c паузы:
    # STT на CPU ~6-7 c и TTS-ответ успевают проиграться до hangup
    parts.append(torch.zeros(1, 8000 * 8))
    parts.append(load_ogg_8k(f"{BASE}/speech-service/audio/05.ogg"))
    parts.append(torch.zeros(1, 8000 * 15))
    long = torch.cat(parts, dim=1)
    pcm = (long[0].numpy() * 32767).astype("int16")
    pcm.tofile(f"{BASE}/telephony-service/voice8k.pcm")
    print("total_sec:", len(pcm) / 8000)

    sys.path.insert(0, f"{BASE}/telephony-service")
    from app import g711  # noqa: E402

    pcm_bytes = open(f"{BASE}/telephony-service/voice8k.pcm", "rb").read()  # noqa: PTH123
    ulaw = g711.ulaw_encode(pcm_bytes)
    open(f"{BASE}/telephony-service/voice.ulaw", "wb").write(ulaw)  # noqa: PTH123
    print("ulaw_bytes:", len(ulaw))


if __name__ == "__main__":
    main()
