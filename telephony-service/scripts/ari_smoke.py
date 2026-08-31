"""Проверка ARI-соединения с Asterisk (smoke test).

Usage:
    python scripts/ari_smoke.py            # из каталога telephony-service
    ASTERISK_ARI_URL=http://localhost:8088 python scripts/ari_smoke.py
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp  # noqa: E402

from app.config import settings  # noqa: E402


async def main() -> None:
    auth = aiohttp.BasicAuth(settings.ASTERISK_ARI_USERNAME, settings.ASTERISK_ARI_PASSWORD)
    base = settings.ASTERISK_ARI_URL.rstrip("/")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{base}/ari/asterisk/info",
                params={"only": "system"},
                auth=auth,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                data = await resp.json()
                version = data.get("system", {}).get("version", "?")
                print(f"ARI OK: Asterisk {version}")
        except Exception as exc:  # noqa: BLE001
            print(f"ARI FAIL: {exc!r}")
            sys.exit(1)
        try:
            async with session.get(
                f"{base}/ari/applications", auth=auth
            ) as resp:
                apps = await resp.json()
                names = [a.get("name") for a in apps]
                print(f"Stasis applications: {names}")
                if settings.ASTERISK_ARI_APP not in names:
                    print(
                        f"WARNING: приложение '{settings.ASTERISK_ARI_APP}' "
                        "не зарегистрировано (telephony-service не подключён?)"
                    )
        except Exception as exc:  # noqa: BLE001
            print(f"ARI applications FAIL: {exc!r}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
