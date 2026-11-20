import pytest
from conftest import FakeEmbedder, make_chunks
from ragconf.retrieve import HybridRetriever, rrf


class StubDense:
    def __init__(self, ranking):
        self.ranking = ranking

    def search(self, query, n, where=None):
        return [(i, 1.0 - 0.1 * k) for k, i in enumerate(self.ranking)][:n]


def test_rrf_prefers_documents_ranked_high_in_both_lists():
    fused = rrf([["a", "b", "c"], ["b", "a", "d"]])
    assert fused["a"] == pytest.approx(fused["b"])
    assert fused["a"] > fused["c"] and fused["b"] > fused["d"]
    assert max(rrf([["x"], ["y", "x"]]).items(), key=lambda kv: kv[1])[0] == "x"


def test_hybrid_combines_lexical_and_dense():
    chunks = make_chunks()
    r = HybridRetriever(chunks, StubDense(["L2::3", "L1::1"]))
    hits = r.search("délai de réponse trente jours accès information", top_k=3)
    assert hits[0].chunk.chunk_id == "L2::3"  # premier en dense ET en lexical
    assert hits[0].bm25 is not None and hits[0].dense is not None


def test_abrogated_texts_excluded_by_default_but_reachable_explicitly():
    chunks = make_chunks()
    r = HybridRetriever(chunks, StubDense(["L3::4", "L1::1"]))
    ids = [h.chunk.chunk_id for h in r.search("registre papier des déclarations", top_k=5)]
    assert "L3::4" not in ids
    ids = [h.chunk.chunk_id for h in r.search("registre papier des déclarations", top_k=5, filters={"statut": "abrogé"})]
    assert ids == ["L3::4"]


def test_filters_by_domain_and_doc():
    chunks = make_chunks()
    r = HybridRetriever(chunks, StubDense(["L1::1", "L2::3", "L1::2"]))
    hits = r.search("information", top_k=5, filters={"domaine": "acces_information"})
    assert {h.chunk.doc_id for h in hits} == {"L2"}
    assert r.search("information", filters={"doc_id": "inconnu"}) == []


def test_chroma_dense_integration(tmp_path):
    pytest.importorskip("chromadb")
    from ragconf.index import ChromaDense, build_index, load_chunks

    chunks = make_chunks()
    emb = FakeEmbedder()
    build_index(chunks, emb, tmp_path)
    loaded = load_chunks(tmp_path)
    assert [c.chunk_id for c in loaded] == [c.chunk_id for c in chunks]

    r = HybridRetriever(loaded, ChromaDense(tmp_path, emb))
    hits = r.search("durée de conservation des données finalité", top_k=2)
    assert hits[0].chunk.chunk_id == "L1::2"
    # filtre « where » côté Chroma + exclusion des abrogés
    assert all(h.chunk.statut != "abrogé" for h in r.search("registre papier déclarations", top_k=5))
    only = r.search("information", top_k=5, filters={"domaine": "acces_information"})
    assert {h.chunk.doc_id for h in only} == {"L2"}


def test_bm25_returns_only_documents_sharing_a_query_term():
    from ragconf.retrieve import BM25Index

    chunks = make_chunks()
    idx = BM25Index([c.chunk_id for c in chunks], [c.text for c in chunks])
    assert [i for i, _ in idx.search("trente jours", 10)] == ["L2::3"]
    assert idx.search("xylophone", 10) == []
