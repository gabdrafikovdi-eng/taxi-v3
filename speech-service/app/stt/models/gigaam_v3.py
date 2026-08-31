"""Адаптер для GigaAM v3 (``v3_ctc``, ``v3_rnnt``, ``v3_e2e_ctc``,
``v3_e2e_rnnt``).

Модели v3 появились только в gigaam 0.2.0 (GitHub master). PyPI-релиз
0.1.0 их не знает — при попытке загрузки бросается понятная ошибка.
"""

from __future__ import annotations

from app.stt.models.base import GigaAMBaseAdapter


class GigaAMV3Adapter(GigaAMBaseAdapter):
    """Адаптер моделей семейства GigaAM v3."""

    family = "v3"