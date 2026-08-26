"""Unit-тесты бизнес-логики CallSessionService (start_call / get_call / end_call).

Сервис тестируется в изоляции от реальной БД: репозиторий CallSessionRepository
и его асинхронная сессия замоканы через unittest.mock (аналогично
tests/test_order_service.py).

Внимание. Для сценариев end_call намеренно эмулируется поведение реального
репозитория: CallSessionRepository.end_call() выставляет ended_at = now(),
поэтому в этих тестах задаётся side_effect, повторяющий это поведение.

==================================================================
КАК ЗАПУСКАТЬ
==================================================================
    .venv/bin/python -m pytest tests/test_call_service.py -v
==================================================================
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import CallSessionNotFoundError
from app.models.call_session import CallChannel, CallSession, HandledBy
from app.repositories.call_session_repo import CallSessionRepository
from app.services.call_service import CallSessionService

# ---------------------------------------------------------------------------
# Хелперы и фикстуры
# ---------------------------------------------------------------------------


def build_call_session(**overrides) -> CallSession:
    """CallSession с заполненными полями; любые поля можно переопределить."""
    session = CallSession(
        id=uuid4(),
        channel=CallChannel.PHONE,
        handled_by=HandledBy.BOT,
        external_call_id="ext-1",
        caller_phone="+79000000000",
    )
    for name, value in overrides.items():
        setattr(session, name, value)
    return session


@pytest.fixture
def call_repo() -> AsyncMock:
    """Мок CallSessionRepository с мок-асинхронной сессией (для commit)."""
    repo = AsyncMock(spec=CallSessionRepository)
    repo.session = AsyncMock()
    return repo


@pytest.fixture
def svc(call_repo: AsyncMock) -> CallSessionService:
    """CallSessionService с замоканным репозиторием."""
    return CallSessionService(call_session_repo=call_repo)


def simulate_repo_end_call(call_repo: AsyncMock) -> None:
    """Повторяет поведение реального CallSessionRepository.end_call()."""

    def _set_ended_at(call_session: CallSession) -> None:
        call_session.ended_at = datetime.now(UTC)
    call_repo.end_call.side_effect = _set_ended_at

# ---------------------------------------------------------------------------
# START_CALL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_call_creates_session_and_commits(svc, call_repo) -> None:
    """start_call: создаёт новую сессию и коммитит её."""
    call_repo.get_by_external_id.return_value = None

    result = await svc.start_call(
        external_id="ext-1",
        caller_phone="+79000000000",
        channel=CallChannel.PHONE,
        handled_by=HandledBy.BOT,
    )

    assert isinstance(result, CallSession)
    assert result.external_call_id == "ext-1"
    call_repo.add.assert_awaited_once_with(call_session=result)
    call_repo.session.commit.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("channel", [CallChannel.PHONE, CallChannel.CONSOLE])
async def test_start_call_saves_channel(svc, call_repo, channel) -> None:
    """start_call: сохраняет канал вызова (PHONE/CONSOLE)."""
    call_repo.get_by_external_id.return_value = None

    result = await svc.start_call(
        external_id="ext-1",
        caller_phone="+79000000000",
        channel=channel,
        handled_by=HandledBy.BOT,
    )

    assert result.channel == channel
    call_repo.add.assert_awaited_once_with(call_session=result)


@pytest.mark.asyncio
async def test_start_call_saves_external_call_id(svc, call_repo) -> None:
    """start_call: сохраняет external_call_id в сессии."""
    call_repo.get_by_external_id.return_value = None

    result = await svc.start_call(
        external_id="call-id-42",
        caller_phone="+79000000000",
        channel=CallChannel.CONSOLE,
        handled_by=HandledBy.BOT,
    )

    assert result.external_call_id == "call-id-42"
    # В репозиторий уходит именно сохранённый объект сессии.
    call_repo.add.assert_awaited_once_with(call_session=result)


@pytest.mark.asyncio
async def test_start_call_duplicate_external_id_returns_existing(
    svc, call_repo
) -> None:
    """start_call: повторный external_call_id возвращает существующую сессию,
    новую не создаёт."""
    existing = build_call_session(external_call_id="ext-1")
    call_repo.get_by_external_id.return_value = existing

    result = await svc.start_call(
        external_id="ext-1",
        caller_phone="+79991112233",
        channel=CallChannel.PHONE,
        handled_by=HandledBy.BOT,
    )

    assert result is existing
    call_repo.add.assert_not_called()
    call_repo.session.commit.assert_not_awaited()


# ---------------------------------------------------------------------------
# GET_CALL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_call_raises_when_no_session(svc, call_repo) -> None:
    """get_call: сессии нет -> CallSessionNotFoundError."""
    call_repo.get_by_id.return_value = None

    with pytest.raises(CallSessionNotFoundError):
        await svc.get_call(call_session_id=uuid4())


@pytest.mark.asyncio
async def test_get_call_returns_session(svc, call_repo) -> None:
    """get_call: существующая сессия возвращается."""
    existing = build_call_session()
    call_repo.get_by_id.return_value = existing

    result = await svc.get_call(call_session_id=existing.id)

    assert result is existing
    call_repo.get_by_id.assert_awaited_once_with(call_session_id=existing.id)


# ---------------------------------------------------------------------------
# END_CALL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_end_call_sets_ended_at(svc, call_repo) -> None:
    """end_call: устанавливает ended_at на активной сессии."""
    active = build_call_session()  # ended_at=None -> активна
    call_repo.get_by_id.return_value = active
    simulate_repo_end_call(call_repo)

    result = await svc.end_call(call_session_id=active.id)

    assert result.ended_at is not None
    call_repo.end_call.assert_awaited_once_with(call_session=active)
    call_repo.session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_end_call_deactivates_session(svc, call_repo) -> None:
    """end_call: is_active становится False."""
    active = build_call_session()
    call_repo.get_by_id.return_value = active
    simulate_repo_end_call(call_repo)

    result = await svc.end_call(call_session_id=active.id)

    assert result.is_active is False


@pytest.mark.asyncio
async def test_end_call_twice_is_safe(svc, call_repo) -> None:
    """end_call: повторный вызов безопасен — не трогает repo/commit повторно."""
    active = build_call_session()
    call_repo.get_by_id.return_value = active
    simulate_repo_end_call(call_repo)

    first = await svc.end_call(call_session_id=active.id)
    second = await svc.end_call(call_session_id=active.id)

    assert first.ended_at is not None
    assert second is first
    assert second.is_active is False
    # Второй вызов не должен ничего менять в БД.
    call_repo.end_call.assert_awaited_once()
    call_repo.session.commit.assert_awaited_once()