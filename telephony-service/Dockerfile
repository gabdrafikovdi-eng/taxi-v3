FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# ffmpeg — декодирование TTS-потока speech-service (edge-tts отдаёт MP3)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/telephony

COPY app ./app
COPY scripts ./scripts

RUN pip install --no-cache-dir \
        "aiohttp>=3.9.0" \
        "pydantic>=2.7.0" \
        "pydantic-settings>=2.3.0" \
    && useradd --system --uid 1000 --home-dir /srv/telephony telephony \
    && chown -R telephony:telephony /srv/telephony

USER telephony

EXPOSE 8090

CMD ["python", "-m", "app.main"]
