"""Declarative alias->canonical mapping (SCHEMA_DRIFT trigger)."""
from cedx.normalize.field_map import canonical_key, is_drifted


def test_canonical_key():
    assert canonical_key("Amount") == "amount"
    assert canonical_key("Value") == "amount"
    assert canonical_key("owner") == "owner"
    assert canonical_key("totally_unknown") is None


def test_is_drifted():
    assert is_drifted("Value")            # alias -> drift
    assert not is_drifted("Amount")       # primary (case-insensitive) -> no drift
    assert not is_drifted("amount")
    assert not is_drifted("unknown_field")
