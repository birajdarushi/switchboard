"""Two-format intake + schema-drift flag + filename-fallback id for corrupt files."""
from cedx.intake import eml, load_records


def test_eml_parses_kv():
    raw = b"From: x\nSubject: y\n\nId: R1\nOwner: a\nAmount: 500\nCategory: C\n"
    d = eml.parse(raw)
    assert d["Id"] == "R1" and d["Amount"] == "500"


def test_schema_drift_flagged(tmp_path):
    (tmp_path / "feed.json").write_text("[]")
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "R9.eml").write_text(
        "From: x\nSubject: y\n\nId: R9\nOwner: a\nValue: 4750\nCategory: C\n")
    items = load_records(str(tmp_path))
    it = next(i for i in items if i.record.id == "R9")
    assert it.schema_drift and it.record.amount == 4750


def test_corrupt_pdf_gets_filename_id(tmp_path):
    (tmp_path / "feed.json").write_text("[]")
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "CAR-006.pdf").write_bytes(b"%PDF-1.4\nGARBAGE not a real pdf")
    items = load_records(str(tmp_path))
    ids = {i.record.id for i in items}
    assert "CAR-006" in ids           # filename fallback, not blank
    assert "" not in ids
