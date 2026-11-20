from ragconf.chunking import chunk_document, normalize_label, split_articles, split_long

TEXT = """Loi n° 99-99 relative aux tests
Vu la Constitution.
Article premier
Les définitions suivantes s'appliquent.
Article 2
Le responsable renvoie à l'article 5 de la présente loi
sans qu'il s'agisse d'un nouvel article.
Article 3 bis
Disposition particulière.
المادة 4
نص عربي.
"""


def test_split_articles_labels():
    labels = [l for l, _, _ in split_articles(TEXT)]
    assert labels == [None, "1", "2", "3 bis", "4"]


def test_midline_reference_does_not_split():
    labels = [l for l, _, _ in split_articles(TEXT)]
    assert "5" not in labels


def test_normalize_label():
    assert normalize_label("1er") == "1"
    assert normalize_label("Premier") == "1"
    assert normalize_label("12  BIS") == "12 bis"
    assert normalize_label("3 – 1") == "3-1"


def test_no_articles_falls_back_to_single_chunk():
    chunks = chunk_document(["Un rapport sans articles. Texte libre."], {"doc_id": "R1", "titre": "Rapport"})
    assert len(chunks) == 1 and chunks[0].article is None


def test_pages_are_tracked():
    pages = ["Article 1\nTexte un.", "Article 2\nTexte deux.", "Suite de l'article 2 sur la page trois."]
    chunks = chunk_document(pages, {"doc_id": "D", "titre": "T"})
    assert [(c.article, c.page) for c in chunks] == [("1", 1), ("2", 2)]


def test_long_article_is_split_with_overlap():
    sentence = "Le responsable du traitement met en œuvre des mesures techniques adaptées. "
    body = "Article 9\n" + sentence * 60
    chunks = chunk_document([body], {"doc_id": "D", "titre": "T"}, max_chars=500, overlap=100)
    assert len(chunks) > 3
    assert all(len(c.text) <= 500 + 100 for c in chunks)
    assert all(c.article == "9" for c in chunks)
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_split_long_hard_cut_on_giant_sentence():
    pieces = split_long("x" * 2500, 1000, 0)
    assert all(len(p) <= 1000 for p in pieces) and "".join(pieces) == "x" * 2500
