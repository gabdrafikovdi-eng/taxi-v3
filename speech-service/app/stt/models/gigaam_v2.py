"""Адаптер для GigaAM v2 (``v2_ctc``, ``v2_rnnt``).

Модели v2 существуют и в gigaam==0.1.0 (PyPI), и в gigaam==0.2.0 (master),
поэтому ``min_gigaam_version`` для них = (0, 1).
"""

from __future__ import annotations

from app.stt.models.base import GigaAMBaseAdapter


class GigaAMV2Adapter(GigaAMBaseAdapter):
    """Адаптер моделей семейства GigaAM v2."""

    family = "v2"