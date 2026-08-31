"""HTTP-клиент backend (контракт API, см. README — раздел «Интеграция с backend»).

Контракт (ожидаемый от backend, пока backend его не экспонирует):

    POST /api/v1/calls                 {"external_id", "caller_phone"}
       -> 201 {"call_session_id": "<uuid>"}
    GET  /api/v1/calls/{id}/greeting   -> 200 {"text": "..."} | 404
    POST /api/v1/calls/{id}/messages   {"text"} -> 200 {"response": "..."}
    POST /api/v1/calls/{id}/end        -> 204

Таймауты + retry (2 попытки) на сетевые ошибки и 5xx. 4xx — BackendError.
"""

from __future__ import annotations

import asyncio
import contextlib

import aiohttp

from app.backend.base import BackendError
from app.logging import jwarning

_RETRIES = 2
_RETRY_BACKOFF_SEC = 0.5


class HTTPBackendClient:
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        ok_statuses: tuple[int, ...] = (200,),
    ) -> tuple[int, dict | bytes | None]:
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(_RETRIES + 1):
            try:
                async with self._ensure_session().request(
                    method, url, json=json_body, timeout=self._timeout
                ) as resp:
                    if resp.status in ok_statuses:
                        if resp.status == 204:
                            return resp.status, None
                        if resp.content_type == "application/json":
                            return resp.status, await resp.json()
                        return resp.status, await resp.read()
                    body = (await resp.text())[:200]
                    if 400 <= resp.status < 500 and resp.status != 429:
                        raise BackendError(
                            f"backend {method} {path} -> {resp.status}: {body}"
                        )
                    last_error = BackendError(
                        f"backend {method} {path} -> {resp.status}: {body}"
                    )
            except BackendError:
                raise
            except (asyncio.TimeoutError, aiohttp.ClientError) as exc:
                last_error = BackendError(f"backend unavailable: {exc!r}")
            jwarning(
                "backend_request_attempt_failed",
                method=method,
                path=path,
                attempt=attempt + 1,
            )
            await asyncio.sleep(_RETRY_BACKOFF_SEC * (attempt + 1))
        raise last_error or BackendError("backend request failed")

    async def start_call(self, external_id: str, caller_phone: str | None) -> str:
        _status, data = await self._request(
            "POST",
            "/api/v1/calls",
            json_body={"external_id": external_id, "caller_phone": caller_phone},
            ok_statuses=(200, 201),
        )
        if not isinstance(data, dict) or not data.get("call_session_id"):
            raise BackendError(f"malformed start_call response: {data!r}")
        return str(data["call_session_id"])

    async def greeting(self, call_session_id: str) -> str | None:
        try:
            _status, data = await self._request(
                "GET", f"/api/v1/calls/{call_session_id}/greeting"
            )
        except BackendError as exc:
            if "404" in str(exc):
                return None
            raise
        if not isinstance(data, dict):
            return None
        return str(data["text"]) if data.get("text") else None

    async def handle_message(self, call_session_id: str, text: str) -> str:
        _status, data = await self._request(
            "POST",
            f"/api/v1/calls/{call_session_id}/messages",
            json_body={"text": text},
        )
        if not isinstance(data, dict) or "response" not in data:
            raise BackendError(f"malformed message response: {data!r}")
        return str(data["response"])

    async def end_call(self, call_session_id: str) -> None:
        await self._request(
            "POST",
            f"/api/v1/calls/{call_session_id}/end",
            ok_statuses=(200, 202, 204),
        )


async def close_quietly(client: HTTPBackendClient) -> None:
    with contextlib.suppress(Exception):
        await client.close()
