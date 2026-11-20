from conftest import FakeLLM, make_chunks
from fastapi.testclient import TestClient
from ragconf import api
from ragconf.pipeline import RAGPipeline
from ragconf.retrieve import HybridRetriever


class StubDense:
    def search(self, query, n, where=None):
        return []


def client(llm):
    pipe = RAGPipeline(HybridRetriever(make_chunks(), StubDense()), llm, top_k=3)
    api.get_pipeline = lambda: pipe  # remplace le chargement réel (modèles, index)
    return TestClient(api.app)


def test_health_and_documents():
    c = client(FakeLLM("x"))
    assert c.get("/health").json() == {"status": "ok"}
    assert {d["doc_id"] for d in c.get("/documents").json()} == {"L1", "L2", "L3"}


def test_ask_endpoint():
    c = client(FakeLLM("Réponse sous trente jours [S1]."))
    r = c.post("/ask", json={"question": "délai de réponse accès information"})
    assert r.status_code == 200 and not r.json()["refused"] and r.json()["sources"][0]["ref"] == "S1"
    assert c.post("/ask", json={"question": "  "}).status_code == 400


def test_compliance_endpoint_and_validation():
    responses = lambda s, u: (
        '[{"exigence": "Informer la personne concernée de la finalité", "source": "S1"}]'
        if "VÉRIFIABLES" in s
        else '{"verdict": "conforme", "justification": "ok", "preuves": ["D1"]}'
    )
    c = client(FakeLLM(responses))
    doc = "Nous informons la personne concernée de la finalité de la collecte.".encode()
    r = c.post("/compliance", files={"file": ("doc.txt", doc)}, data={"ref": "L1"})
    assert r.status_code == 200
    assert r.json()["findings"][0]["verdict"] == "conforme"
    assert c.post("/compliance", files={"file": ("doc.txt", doc)}, data={"ref": "nope"}).status_code == 404
    assert c.post("/compliance", files={"file": ("doc.exe", b"x")}, data={"ref": "L1"}).status_code == 415
