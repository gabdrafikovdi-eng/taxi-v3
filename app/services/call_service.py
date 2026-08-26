from app.core.exceptions import CallSessionNotFoundError
from app.models.call_session import CallChannel, CallSession, HandledBy
from app.repositories.call_session_repo import CallSessionRepository


class CallSessionService:
    def __init__(self, call_session_repo: CallSessionRepository):
        self._call_repo = call_session_repo

    async def start_call(
        self,
        external_id: str,
        caller_phone: str,
        channel: CallChannel,
        handled_by: HandledBy,
    ) -> CallSession:

        call_session = CallSession(
            channel=channel,
            handled_by=handled_by,
            external_call_id=external_id,
            caller_phone=caller_phone,
        )

        external = await self._call_repo.get_by_external_id(external_id)

        if external is not None:
            return external

        await self._call_repo.add(call_session=call_session)
        await self._call_repo.session.commit()

        return call_session

    async def get_call(self, call_session_id: str) -> CallSession:
        call_session = await self._call_repo.get_by_id(call_session_id=call_session_id)

        if call_session is None:
            raise CallSessionNotFoundError(call_session_id=call_session_id)

        return call_session

    async def end_call(self, call_session_id: str) -> CallSession:
        call_session = await self._call_repo.get_by_id(call_session_id)
        if call_session is None:
            raise CallSessionNotFoundError(call_session_id=call_session_id)

        if not call_session.is_active:
            return call_session

        await self._call_repo.end_call(call_session=call_session)
        await self._call_repo.session.commit()

        return call_session
