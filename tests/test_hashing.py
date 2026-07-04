"""hashing.py MUST byte-match verify_audit.py's sha() — the whole gate depends on it."""
import hashlib
import json

from cedx.hashing import canon, hex_of, sha, sha_bytes


def _gate_sha(o):
    return "sha256:" + hashlib.sha256(
        json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def test_sha_matches_gate():
    for s in [{"b": 1, "a": "café"}, {"z": [3, 2, 1], "n": None},
              {"x": {"y": 1.5}}, {"amount": 4650.0, "owner": "q.abate"}]:
        assert sha(s) == _gate_sha(s)


def test_key_order_irrelevant():
    assert sha({"a": 1, "b": 2}) == sha({"b": 2, "a": 1})


def test_hex_of():
    assert hex_of("sha256:abc123") == "abc123"


def test_sha_bytes_prefix():
    assert sha_bytes(b"hi").startswith("sha256:") and len(hex_of(sha_bytes(b"hi"))) == 64


def test_canon_is_compact():
    assert canon({"a": 1, "b": 2}) == b'{"a":1,"b":2}'
