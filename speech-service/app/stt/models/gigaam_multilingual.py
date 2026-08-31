"""Адаптер для multilingual-моделей GigaAM (``multilingual_ctc``,
``multilingual_large_ctc``).

''language'' в реестр не передаётся: API gigaam не использует параметр
``lang`` в ``transcribe``, поэтому передача была бы бесполезной.
Настройка ``STT_LANGUAGE`` остаётся метаданными конфигурации.
"""

from __future__ import annotations

from app.stt.models.base import GigaAMBaseAdapter


class GigaAMMultilingualAdapter(GigaAMBaseAdapter):
    """Адаптер multilingual-моделей GigaAM."""

    family = "multilingual"