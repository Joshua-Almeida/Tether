from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import main as mainmod


def test_health_empty_index(monkeypatch):
    monkeypatch.setattr(mainmod, "chunk_count", lambda: 0)
    monkeypatch.setattr(mainmod, "listed_sources", lambda: ["rfc791"])
    client = TestClient(mainmod.app)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["index_ready"] is False
    assert body["chunk_count"] == 0
    assert "rfc791" in body["sources"]


def test_ask_409_when_index_empty(monkeypatch):
    monkeypatch.setattr(mainmod, "chunk_count", lambda: 0)
    monkeypatch.setattr(mainmod, "settings", SimpleNamespace(llm_configured=True))
    client = TestClient(mainmod.app)
    response = client.post("/api/ask", json={"question": "Who won the 2018 FIFA World Cup?"})
    assert response.status_code == 409
    assert "empty" in response.json()["detail"].lower()


def test_ask_503_without_keys(monkeypatch):
    monkeypatch.setattr(mainmod, "settings", SimpleNamespace(llm_configured=False))
    client = TestClient(mainmod.app)
    response = client.post("/api/ask", json={"question": "How many bits is the IPv4 version field?"})
    assert response.status_code == 503


def test_compare_409_when_index_empty(monkeypatch):
    monkeypatch.setattr(mainmod, "chunk_count", lambda: 0)
    monkeypatch.setattr(mainmod, "settings", SimpleNamespace(llm_configured=True))
    client = TestClient(mainmod.app)
    response = client.post("/api/compare", json={"question": "Who won the 2018 FIFA World Cup?"})
    assert response.status_code == 409


def test_eval_retrieval_409_when_index_empty(monkeypatch):
    monkeypatch.setattr(mainmod, "chunk_count", lambda: 0)
    client = TestClient(mainmod.app)
    response = client.get("/api/eval/retrieval")
    assert response.status_code == 409


def test_corpus_lists_rfc_titles():
    client = TestClient(mainmod.app)
    response = client.get("/api/corpus")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["sources"]}
    assert ids == {"rfc791", "rfc793", "rfc3986", "rfc9110"}


def test_health_reports_retrieve_mode(monkeypatch):
    monkeypatch.setattr(mainmod, "chunk_count", lambda: 12)
    monkeypatch.setattr(mainmod, "listed_sources", lambda: ["rfc791"])
    monkeypatch.setattr(mainmod, "retrieve_method", lambda: "hybrid")
    monkeypatch.setattr(
        mainmod,
        "settings",
        SimpleNamespace(llm_configured=True, rewrite_max=1),
    )
    client = TestClient(mainmod.app)
    body = client.get("/api/health").json()
    assert body["retrieve_mode"] == "hybrid"
    assert body["rewrite_max"] == 1
    assert body["index_ready"] is True
