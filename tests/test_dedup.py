"""SUPERSEDED_VERSION: same id, keep highest version, mark older superseded."""
from cedx.contracts import CanonicalRecord, SourceFormat
from cedx.intake import IntakeItem
from cedx.normalize.dedup import dedup


def item(rid, v):
    return IntakeItem(CanonicalRecord(id=rid, version=v, source_format=SourceFormat.feed,
                                      source_version_hash="sha256:x"), False)


def test_dedup_keeps_latest():
    r = dedup([item("A", 1), item("A", 2), item("B", 1)])
    assert {i.record.id for i in r.active} == {"A", "B"}
    active_a = next(i for i in r.active if i.record.id == "A")
    assert active_a.record.version == 2
    assert len(r.superseded) == 1 and r.superseded[0].record.version == 1


def test_dedup_no_duplicates():
    r = dedup([item("A", 1), item("B", 1)])
    assert len(r.active) == 2 and r.superseded == []
