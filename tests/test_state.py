"""Tests voor AlertState: begrenzing, atomaire opslag en herladen."""

import json

from state import AlertState


def test_remember_and_is_seen():
    state = AlertState(max_seen_ids=10, history_size=5)
    assert not state.is_seen("a")
    state.remember("a")
    assert state.is_seen("a")
    state.remember("a")  # dubbel onthouden is een no-op
    assert len(state.seen_order) == 1


def test_seen_ids_bounded_by_max():
    state = AlertState(max_seen_ids=3, history_size=5)
    for alert_id in "abcde":
        state.remember(alert_id)
    assert len(state.seen_ids) == 3
    assert not state.is_seen("a")  # oudste eruit
    assert state.is_seen("e")


def test_history_bounded_by_size():
    state = AlertState(max_seen_ids=10, history_size=2)
    for n in range(4):
        state.add_history({"n": n})
    assert [h["n"] for h in state.history] == [3, 2]


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "state.json")
    state = AlertState(max_seen_ids=10, history_size=5)
    state.remember("a")
    state.remember("b")
    state.add_history({"titel": "test"})
    state.save(path)

    # Atomair: geen achtergebleven .tmp-bestand.
    assert not (tmp_path / "state.json.tmp").exists()

    reloaded = AlertState(max_seen_ids=10, history_size=5)
    reloaded.load(path)
    assert reloaded.is_seen("a") and reloaded.is_seen("b")
    assert reloaded.history == [{"titel": "test"}]


def test_load_corrupt_state_starts_empty(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{kapot")
    state = AlertState(max_seen_ids=10, history_size=5)
    state.load(str(path))
    assert not state.seen_ids
    assert state.history == []


def test_load_trims_history_to_current_size(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"seen_ids": [], "history": [{"n": n} for n in range(10)]}))
    state = AlertState(max_seen_ids=10, history_size=3)
    state.load(str(path))
    assert len(state.history) == 3
