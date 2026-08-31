"""Состояния звонка и валидируемая машина состояний."""

from __future__ import annotations

from enum import StrEnum

from app.logging import jwarning


class CallState(StrEnum):
    RINGING = "RINGING"
    CONNECTED = "CONNECTED"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ENDING = "ENDING"
    ENDED = "ENDED"
    FAILED = "FAILED"


# Допустимые переходы. ENDED/FAILED — терминальные.
TRANSITIONS: dict[CallState, frozenset[CallState]] = {
    CallState.RINGING: frozenset(
        {CallState.CONNECTED, CallState.ENDING, CallState.ENDED, CallState.FAILED}
    ),
    CallState.CONNECTED: frozenset(
        {
            CallState.LISTENING,
            CallState.PROCESSING,
            CallState.SPEAKING,
            CallState.ENDING,
            CallState.ENDED,
            CallState.FAILED,
        }
    ),
    CallState.LISTENING: frozenset(
        {
            CallState.PROCESSING,
            CallState.SPEAKING,
            CallState.ENDING,
            CallState.ENDED,
            CallState.FAILED,
        }
    ),
    CallState.PROCESSING: frozenset(
        {
            CallState.SPEAKING,
            CallState.LISTENING,
            CallState.ENDING,
            CallState.ENDED,
            CallState.FAILED,
        }
    ),
    CallState.SPEAKING: frozenset(
        {CallState.LISTENING, CallState.ENDING, CallState.ENDED, CallState.FAILED}
    ),
    CallState.ENDING: frozenset({CallState.ENDED, CallState.FAILED}),
    CallState.ENDED: frozenset(),
    CallState.FAILED: frozenset(),
}


class CallStateMachine:
    """Машина состояний звонка.

    Невалидный переход не бросает исключение (устойчивость к дубликатам
    событий/гонкам) — логируется и игнорируется, возвращается ``False``.
    """

    def __init__(self, initial: CallState = CallState.RINGING) -> None:
        self._state = initial

    @property
    def current(self) -> CallState:
        return self._state

    def can(self, new_state: CallState) -> bool:
        return new_state in TRANSITIONS[self._state]

    def transition(self, new_state: CallState) -> bool:
        if self._state == new_state:
            return True
        if not self.can(new_state):
            jwarning(
                "call_state_invalid_transition",
                current=self._state.value,
                requested=new_state.value,
            )
            return False
        self._state = new_state
        return True

    def is_terminal(self) -> bool:
        return self._state in (CallState.ENDED, CallState.FAILED)

    def is_active(self) -> bool:
        return not self.is_terminal() and self._state != CallState.ENDING
