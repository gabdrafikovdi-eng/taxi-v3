#!/usr/bin/env python3
"""Парсер улиц и номеров домов с сайта Ростелекома для села Аскарово.

Не зависит от внешних библиотек (только stdlib: urllib + html.parser).
Обходит все 17 страниц /addresses и собирает адреса формата
    "Улица ул., <номер>"
в словарь {улица: {номер: [url, ...]}}.
"""
from __future__ import annotations

import html.parser
import json
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://selo-askarovo.rt-internet.ru"
FIRST_PAGE = 1
LAST_PAGE = 17  # всего 17 страниц с улицами/номерами домов


class AddressParser(html.parser.HTMLParser):
    """Извлекает из HTML все ссылки с классом ``cities-item``.

    Внутри такой ссылки лежит текст вида "40 лет Октября ул., 11",
    а в href — /tarifs/ulica-<name>-<номер>.
    """

    def __init__(self) -> None:
        super().__init__()
        self._capture = False
        self._buf: list[str] = []
        self.items: list[tuple[str, str]] = []  # (href, text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            classes = dict(attrs).get("class", "") or ""
            if "cities-item" in classes.split():
                self._capture = True
                self._buf = []
                self._href = dict(attrs).get("href", "") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture:
            text = " ".join("".join(self._buf).split())
            if text:
                self.items.append((self._href, text))
            self._capture = False

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buf.append(data)


def fetch(url: str, retries: int = 3) -> str:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Не удалось загрузить {url}: {last_err}")


def split_address(text: str) -> tuple[str, str]:
    """Разбивает "Улица ул., номер" / "Искра переулок, 1" на (улица, номер).

    Улица — это всё до последней запятой (там же и тип улицы: «ул.»,
    «переулок» и т.п.), номер — всё после неё. В номерах домов запятых нет.
    """
    street, sep, num = text.rpartition(",")
    if not sep:
        return text.strip(), ""
    return street.strip(), num.strip()


def main() -> int:
    addresses: dict[str, dict[str, list[str]]] = {}
    for page in range(FIRST_PAGE, LAST_PAGE + 1):
        url = f"{BASE}/addresses" if page == 1 else f"{BASE}/addresses/{page}"
        print(f"[{page}/{LAST_PAGE}] {url} ...", file=sys.stderr)
        raw = fetch(url)
        parser = AddressParser()
        parser.feed(raw)
        print(f"    найдено записей: {len(parser.items)}", file=sys.stderr)
        for href, text in parser.items:
            street, num = split_address(text)
            addresses.setdefault(street, {}).setdefault(num, []).append(href)
        time.sleep(0.3)  # вежливая пауза между запросами

    # --- Результат ---
    streets = sorted(addresses)
    print(f"\nВсего улиц: {len(streets)}", file=sys.stderr)
    print("=" * 60)
    for street in streets:
        nums = sorted(addresses[street])
        print(f"{street}  ({len(nums)} домов)")
        for n in nums:
            urls = addresses[street][n]
            print(f"    {n}")

    # --- Сохраняем JSON рядом со скриптом ---
    out_dir = Path(__file__).resolve().parent
    out = out_dir / "askarovo_streets.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(
            {"total_streets": len(streets), "addresses": addresses},
            fh, ensure_ascii=False, indent=2,
        )
    print(f"\nСохранено: {out}", file=sys.stderr)

    # --- Плоский список "улица, номер" ---
    flat = out_dir / "askarovo_flat.txt"
    with open(flat, "w", encoding="utf-8") as fh:
        for street in streets:
            for n in sorted(addresses[street]):
                fh.write(f"{street}, {n}\n")
    print(f"Сохранено: {flat}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
