"""Append-only, tamper-evident event log (probe-append-only backbone)."""
from cedx.audit.log import EventLog, verify_chain


def _events(n=4):
    log = EventLog()
    for i in range(n):
        log.append("system", f"action_{i}", "ts", f"REC-{i}")
    return [e.model_dump(mode="json") for e in log.events]


def test_seq_is_strict():
    assert [e["seq"] for e in _events()] == [0, 1, 2, 3]


def test_clean_chain_verifies():
    assert verify_chain(_events())[0]


def test_mutation_detected():
    ev = _events()
    ev[1]["action"] = "TAMPERED"
    ok, bad = verify_chain(ev)
    assert not ok and bad == 1


def test_deletion_detected():
    ev = [e for e in _events() if e["seq"] != 1]
    assert not verify_chain(ev)[0]
