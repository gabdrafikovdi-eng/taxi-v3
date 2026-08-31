"""Тесты машины состояний звонка."""

from __future__ import annotations

from app.calls.state import TRANSITIONS, CallState, CallStateMachine


def test_initial_state_ringing():
    sm = CallStateMachine()
    assert sm.current == CallState.RINGING
    assert sm.is_active()


def test_happy_path():
    sm = CallStateMachine()
    assert sm.transition(CallState.CONNECTED)
    assert sm.transition(CallState.LISTENING)
    assert sm.transition(CallState.PROCESSING)
    assert sm.transition(CallState.SPEAKING)
    assert sm.transition(CallState.LISTENING)
    assert sm.transition(CallState.ENDING)
    assert sm.transition(CallState.ENDED)
    assert sm.is_terminal()
    assert not sm.is_active()


def test_invalid_transition_rejected():
    sm = CallStateMachine()
    # RINGING → LISTENING недопустим (сначала CONNECTED)
    assert not sm.transition(CallState.LISTENING)
    assert sm.current == CallState.RINGING


def test_failed_from_any_active_state():
    for start in (
        CallState.RINGING,
        CallState.CONNECTED,
        CallState.LISTENING,
        CallState.PROCESSING,
        CallState.SPEAKING,
        CallState.ENDING,
    ):
        sm = CallStateMachine(initial=start)
        assert sm.transition(CallState.FAILED)
        assert sm.is_terminal()
        # Терминальные состояния не меняются
        assert not sm.transition(CallState.LISTENING)


def test_terminal_states_have_no_transitions():
    assert TRANSITIONS[CallState.ENDED] == frozenset()
    assert TRANSITIONS[CallState.FAILED] == frozenset()


def test_same_state_transition_is_noop_true():
    sm = CallStateMachine()
    assert sm.transition(CallState.RINGING)
    assert sm.current == CallState.RINGING
