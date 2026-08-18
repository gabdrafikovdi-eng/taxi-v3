"""Runtime-загрузчик сценариев из ``docs/test_case_address.json``.

Файл со сценариями является ОСНОВНЫМ источником требований для тестов:
pytest читает его при КАЖДОМ запуске (на этапе сбора тестов). Любое
изменение JSON автоматически влияет на следующий запуск pytest — тесты не
содержат сценариев, скопированных вручную из файла.

Как запускать тесты — см. docstring в tests/test_address_scenarios.py.
"""

from __future__ import annotations

import json
from pathlib import Path

# Корень проекта: tests/.. -> taxi-v3
ROOT = Path(__file__).resolve().parent.parent

# Путь к файлу со сценариями (источник требований).
SCENARIOS_PATH = ROOT / "docs" / "test_case_address.json"


def load_scenarios() -> list[dict]:
    """Читает и возвращает список сценариев из JSON при каждом вызове."""
    with SCENARIOS_PATH.open(encoding="utf-8") as file:
        data = json.load(file)

    return data["scenarios"]


def load_scenarios_meta() -> dict:
    """Возвращает метаданные файла (test_suite/description/documentation)."""
    with SCENARIOS_PATH.open(encoding="utf-8") as file:
        return json.load(file)
