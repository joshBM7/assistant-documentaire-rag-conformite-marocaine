import pytest
from conftest import FakeLLM, make_chunks
from ragconf.compliance import check_document, extract_json, extract_requirements, findings_to_markdown, Requirement
from ragconf.evaluate import evaluate, summarize
from ragconf.pipeline import RAGPipeline
from ragconf.retrieve import HybridRetriever


def test_extract_json_variants():
    assert extract_json('```json\n[{"a": 1}]\n```') == [{"a": 1}]
    assert extract_json('Voici : {"verdict": "conforme", "preuves": ["D1"]} merci') == {"verdict": "conforme", "preuves": ["D1"]}
    assert extract_json('{"x": [1, 2]}') == {"x": [1, 2]}  # objet contenant un tableau
    with pytest.raises(ValueError):
        extract_json("pas de json")


def test_extract_requirements_maps_sources_and_dedups():
    llm = FakeLLM('[{"exigence": "Informer la personne concernée", "source": "S1"},'
                  '{"exigence": "informer la personne concernée", "source": "S1"},'
                  '{"exigence": "Source invalide", "source": "S9"},'
                  '{"exigence": "Limiter la durée de conservation", "source": "S2"}]')
    reqs = extract_requirements(make_chunks()[:2], llm)
    assert [r.id for r in reqs] == ["E1", "E2"]
    assert reqs[1].source_chunk_id == "L1::2" and "art. 2" in reqs[1].source_label


DOC = """Politique de confidentialité

Nous informons chaque personne concernée de la finalité de la collecte de ses données lors de l'inscription.

Les données sont conservées sans limite de durée."""


def reqs():
    return [
        Requirement("E1", "Informer la personne concernée de la finalité de la collecte", "Loi L1, art. 1", "L1::1"),
        Requirement("E2", "Limiter la durée de conservation des données", "Loi L1, art. 2", "L1::2"),
        Requirement("E3", "Désigner un délégué xylophone", "Loi L1, art. 9", "L1::9"),
    ]


def test_check_document_verdicts_and_guards():
    def llm(system, user):
        if "finalité" in user.split("Extraits")[0]:
            return '{"verdict": "conforme", "justification": "Information prévue.", "preuves": ["D2"]}'
        return '{"verdict": "conforme", "justification": "Probable.", "preuves": []}'  # sans preuve -> rétrogradé

    f = check_document(DOC, reqs(), FakeLLM(llm))
    assert f[0].verdict == "conforme" and f[0].preuves
    assert f[1].verdict == "non_determine" and "aucune preuve" in f[1].justification
    assert f[2].verdict == "non_determine" and "Aucun passage" in f[2].justification  # rien de pertinent, pas d'appel LLM


def test_check_document_handles_garbage_llm_output():
    f = check_document(DOC, reqs()[:1], FakeLLM("désolé, pas de json"))
    assert f[0].verdict == "non_determine"


def test_markdown_report():
    f = check_document(DOC, reqs(), FakeLLM('{"verdict": "non_conforme", "justification": "Pas de limite.", "preuves": ["D3"]}'))
    md = findings_to_markdown(f, "Loi L1")
    assert "non conformes : 2" in md and "E1 ❌" in md and "ne remplace pas un avis juridique" in md


class StubDense:
    def search(self, query, n, where=None):
        return []


def test_evaluate_metrics():
    llm = FakeLLM(lambda s, u: "INSUFFISANT" if "hors sujet" in u else "Réponse [S1].")
    pipe = RAGPipeline(HybridRetriever(make_chunks(), StubDense()), llm, top_k=1)
    qs = [
        {"id": "a", "categorie": "factuelle", "question": "délai de réponse accès information", "sources": [{"doc_id": "L2", "article": 5}]},
        {"id": "b", "categorie": "factuelle", "question": "durée de conservation finalité", "sources": [{"doc_id": "L2", "article": 5}]},
        {"id": "c", "categorie": "sans_reponse", "question": "hors sujet délai conservation", "sources": []},
    ]
    rep = evaluate(pipe, qs)
    assert rep["categories"]["factuelle"]["n"] == 2
    assert rep["global"]["retrieval_hit"] == 0.5  # a trouvé L2/5, b non
    assert rep["global"]["citation_ok"] == 0.5
    assert rep["global"]["refus_correct"] == 1.0


def test_summarize_empty_groups_do_not_crash():
    assert summarize([])["global"]["retrieval_hit"] is None
