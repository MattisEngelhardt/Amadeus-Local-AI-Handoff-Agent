from amadeus.core.inbox import (
    compute_content_digest,
    detect_duplicate,
    register_file_input,
    register_text_input,
    store_raw_input,
)
from amadeus.models.state import ProjectState


def _make_state():
    return ProjectState(project_name="test", display_name="Test", main_goal="Goal")


def test_compute_content_digest():
    d1 = compute_content_digest("hello")
    d2 = compute_content_digest("hello")
    d3 = compute_content_digest("world")
    assert d1 == d2
    assert d1 != d3


def test_register_text_input():
    state = _make_state()
    state, record = register_text_input(state, "Build an API")
    assert len(state.raw_inputs) == 1
    assert record.kind == "text"
    assert record.content_digest != ""
    assert not record.is_duplicate


def test_duplicate_detection():
    state = _make_state()
    state, r1 = register_text_input(state, "Build an API")
    state, r2 = register_text_input(state, "Build an API")
    assert not r1.is_duplicate
    assert r2.is_duplicate
    assert r2.duplicate_of == r1.input_id


def test_detect_duplicate_returns_none_for_new():
    state = _make_state()
    assert detect_duplicate(state, "abc123") is None


def test_register_file_input(tmp_path):
    state = _make_state()
    f = tmp_path / "notes.txt"
    f.write_text("Some notes", encoding="utf-8")
    state, record = register_file_input(state, f)
    assert record.kind == "file"
    assert record.file_path == str(f)
    assert record.content_digest != ""


def test_file_duplicate_detection(tmp_path):
    state = _make_state()
    f = tmp_path / "notes.txt"
    f.write_text("Same content", encoding="utf-8")
    state, r1 = register_file_input(state, f)
    state, r2 = register_file_input(state, f)
    assert r2.is_duplicate
    assert r2.duplicate_of == r1.input_id


def test_store_raw_input_text(tmp_path):
    state = _make_state()
    state, record = register_text_input(state, "Build something")
    dest = store_raw_input(record, tmp_path)
    assert dest.exists()
    content = dest.read_text(encoding="utf-8")
    assert "Build something" in content


def test_store_raw_input_file(tmp_path):
    state = _make_state()
    f = tmp_path / "source.txt"
    f.write_text("File content", encoding="utf-8")
    state, record = register_file_input(state, f)
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    dest = store_raw_input(record, project_dir, source_file=f)
    assert dest.exists()
