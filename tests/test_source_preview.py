"""Public-text intake is a preview, never an implicit corpus update."""
import json
from pathlib import Path

import pytest

from rag import build_corpus as corpus
from tools.preview_rag_source import preview


@pytest.fixture
def source_files(tmp_path):
    source = {"id": "nci-preview-fixture", "title": "Offline fixture", "url": "https://www.cancer.gov/test",
              "license": corpus.NCI_LICENSE, "license_url": corpus.NCI_LICENSE_URL,
              "scope": "Synthetic parser test only"}
    declaration = tmp_path / "candidate.json"
    declaration.write_text(json.dumps(source), encoding="utf-8")
    payload = tmp_path / "source.html"
    payload.write_text("<main><h2>Overview</h2><p>" + "Synthetic educational passage for parser regression. " * 30
                       + "</p><script>untrusted script text</script></main>", encoding="utf-8")
    return declaration, payload


def test_preview_extracts_provenance_without_changing_active_sources(source_files, tmp_path):
    before = corpus.OUTPUT.read_bytes(), corpus.LOCK.read_bytes()
    out = tmp_path / "preview"
    result = preview(*source_files, out)
    assert result["status"] == "REVIEW_REQUIRED" and result["active_corpus_changed"] is False
    chunks = [json.loads(line) for line in (out / "chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert chunks and all(c["source_id"] == "nci-preview-fixture" for c in chunks)
    assert "untrusted script text" not in (out / "chunks.jsonl").read_text(encoding="utf-8")
    assert (corpus.OUTPUT.read_bytes(), corpus.LOCK.read_bytes()) == before
    with pytest.raises(ValueError, match="already exists"):
        preview(*source_files, out)


@pytest.mark.parametrize("field,value", [("id", "../escape"), ("license", "CC BY-NC 4.0"),
                                          ("url", "https://unapproved.invalid/article")])
def test_invalid_declarations_leave_no_preview(source_files, tmp_path, field, value):
    declaration, payload = source_files
    source = json.loads(declaration.read_text(encoding="utf-8")); source[field] = value
    declaration.write_text(json.dumps(source), encoding="utf-8")
    output = tmp_path / "failed"
    with pytest.raises(ValueError):
        preview(declaration, payload, output)
    assert not output.exists()


def test_active_rag_directories_cannot_be_preview_targets(source_files):
    with pytest.raises(ValueError, match="outside active"):
        preview(*source_files, corpus.DATA / "must-not-create-preview")
