from conftest import FakeLLM, make_chunks
from ragconf.guardrails import REFUSAL_MESSAGE, check_answer
from ragconf.pipeline import RAGPipeline, build_user_prompt
from ragconf.retrieve import Hit, HybridRetriever


def hits():
    return [Hit(c, 1.0) for c in make_chunks()[:3]]


def test_valid_cited_answer_passes():
    g = check_answer("Le responsable doit informer la personne [S1]. Le délai est limité [S2].", hits())
    assert not g.refused and g.cited == [1, 2]


def test_refusal_token():
    assert check_answer("INSUFFISANT", hits()).refused
    assert check_answer("  insuffisant : rien dans les extraits", hits()).refused


def test_no_citation_is_refused():
    assert check_answer("Le délai est de trente jours.", hits()).refused


def test_out_of_range_citation_is_refused():
    assert check_answer("Voir [S9].", hits()).refused
    assert check_answer("Voir [S0].", hits()).refused


def test_invented_article_is_refused():
    g = check_answer("Selon l'article 42, le délai est de 30 jours [S3].", hits())
    assert g.refused and "42" in g.reason


def test_article_present_in_context_is_accepted():
    assert not check_answer("L'article 5 prévoit un délai de trente jours [S3].", hits()).refused


class StubDense:
    def search(self, query, n, where=None):
        return []


def make_pipeline(llm):
    return RAGPipeline(HybridRetriever(make_chunks(), StubDense()), llm, top_k=3)


def test_pipeline_answers_with_sources():
    llm = FakeLLM("Une réponse est due sous trente jours [S1].")
    ans = make_pipeline(llm).ask("délai de réponse à une demande d'accès à l'information")
    assert not ans.refused and ans.cited == [1]
    assert ans.sources[0].chunk.doc_id == "L2"
    d = ans.to_dict()
    assert d["sources"][0]["ref"] == "S1" and "art. 5" in d["sources"][0]["label"]
    assert "[S1]" in llm.calls[0][1]  # extraits numérotés dans le prompt


def test_pipeline_refuses_without_calling_llm_when_nothing_retrieved():
    llm = FakeLLM("ne doit pas être appelé")
    ans = make_pipeline(llm).ask("zzzz qqqq")
    assert ans.refused and ans.answer == REFUSAL_MESSAGE and llm.calls == []


def test_pipeline_converts_uncited_answer_to_refusal():
    ans = make_pipeline(FakeLLM("Réponse sans citation.")).ask("délai de réponse accès information")
    assert ans.refused and ans.answer == REFUSAL_MESSAGE and ans.sources


def test_prompt_contains_labels():
    p = build_user_prompt("Q ?", hits())
    assert "[S1] (Loi L1, art. 1, p. 1)" in p and p.endswith("Question : Q ?")
