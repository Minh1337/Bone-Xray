"""Offline readiness, port-ownership and health-identity regression tests."""
import hashlib
import json
import socket
import threading
import time
from urllib.request import ProxyHandler, build_opener

from fastapi.testclient import TestClient

from rag.demo_api import create_app
from tools import chatbot_doctor as doctor, run_chatbot as runner


def test_doctor_hides_key_and_handles_bare_env_value(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    (tmp_path / ".env").write_text("OPENROUTER_API_KEY=sentinel-not-a-real-key\nOPENROUTER_MODEL\n", encoding="utf-8")
    result = doctor.inspect_workspace(tmp_path, module_available=lambda _: True)
    assert "sentinel-not-a-real-key" not in json.dumps(result)
    assert next(c for c in result["checks"] if c["name"] == "provider_config")["status"] == "ERROR"
    assert not (tmp_path / "data").exists()


def test_doctor_detects_changed_vectors_without_rebuilding(tmp_path):
    for name, value in (("rag/data/corpus.jsonl", b"corpus"), ("rag/data/source_lock.json", b"lock"),
                        ("rag/index/vectors.npy", b"vectors")):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    manifest = {k: hashlib.sha256(v).hexdigest() for k,v in (
        ("corpus_sha256", b"corpus"), ("source_lock_sha256", b"lock"), ("vectors_sha256", b"vectors"))}
    (tmp_path / "rag/index/manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "rag/index/vectors.npy").write_bytes(b"changed")
    report = doctor.inspect_workspace(tmp_path, module_available=lambda _: True)
    assert next(c for c in report["checks"] if c["name"] == "rag_index")["status"] == "WARN"
    assert (tmp_path / "rag/index/vectors.npy").read_bytes() == b"changed"


def test_health_is_local_liveness_without_provider_or_model_calls():
    def forbidden(*_a, **_k):
        raise AssertionError("Health must not load models")
    with TestClient(create_app(forbidden, forbidden), base_url="http://127.0.0.1:8765") as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"app": "bonescope-chatbot", "status": "ok", "version": "0.2", "answer_ready": False}
    assert response.headers["cache-control"] == "no-store"


def test_foreign_occupied_port_is_preserved(monkeypatch, capsys):
    monkeypatch.setattr(runner, "inspect_workspace", lambda: {"status": "PASS", "checks": []})
    monkeypatch.setattr(runner, "existing_bonescope", lambda _: False)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0)); listener.listen()
        port = listener.getsockname()[1]
        assert runner.main(["--port", str(port)]) == 2
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass
    assert "No process was stopped" in capsys.readouterr().out


def test_existing_chatbot_is_reported_without_starting_another(monkeypatch, capsys):
    monkeypatch.setattr(runner, "inspect_workspace", lambda: {"status": "PASS", "checks": []})
    monkeypatch.setattr(runner, "existing_bonescope", lambda _: True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0)); listener.listen()
        assert runner.main(["--port", str(listener.getsockname()[1])]) == 0
    assert "already running" in capsys.readouterr().out


def test_dependency_failures_stop_before_startup(monkeypatch):
    monkeypatch.setattr(runner, "inspect_workspace", lambda: {"status": "ERROR", "checks": []})
    assert runner.main([]) == 1


def test_real_launcher_reserves_loopback_serves_health_and_stops(monkeypatch, capsys):
    import uvicorn
    servers, result = [], []
    class RecordingServer(uvicorn.Server):
        def __init__(self, config):
            super().__init__(config)
            servers.append(self)
    monkeypatch.setattr(uvicorn, "Server", RecordingServer)
    monkeypatch.setattr(runner, "inspect_workspace", lambda: {"status": "PASS", "checks": []})
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    worker = threading.Thread(target=lambda: result.append(runner.main(["--port", str(port)])), daemon=True)
    worker.start()
    try:
        deadline = time.monotonic() + 8
        while not servers or not servers[0].started:
            assert time.monotonic() < deadline and worker.is_alive()
            time.sleep(.05)
        with build_opener(ProxyHandler({})).open(f"http://127.0.0.1:{port}/api/health", timeout=2) as response:
            assert json.load(response)["app"] == "bonescope-chatbot"
        assert runner.existing_bonescope(port)
        assert f"BoneScope ready at http://127.0.0.1:{port}/" in capsys.readouterr().out
    finally:
        if servers:
            servers[0].should_exit = True
        worker.join(timeout=8)
    assert not worker.is_alive() and result == [0]
