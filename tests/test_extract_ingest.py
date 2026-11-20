import pymupdf
from ragconf.config import Settings
from ragconf.extract import clean_pages, extract_pages
from ragconf.ingest import build_chunks


def make_pdf(path, pages):
    doc = pymupdf.open()
    for t in pages:
        page = doc.new_page()
        page.insert_text((72, 72), t, fontsize=11)
    doc.save(path)
    doc.close()


def test_clean_pages_removes_headers_footers_and_numbers():
    pages = [f"Bulletin Officiel n° {6000 + i}\nArticle {i}\nContenu de l'article {i}.\n{i}" for i in range(1, 6)]
    out = clean_pages(pages)
    assert all("Bulletin Officiel" not in p for p in out)
    assert all(p.splitlines()[0].startswith("Article") for p in out)
    assert not any(p.rstrip().endswith(f"\n{i}") for i, p in enumerate(out, 1))


def test_clean_pages_dehyphenates():
    assert "traitement" in clean_pages(["Le trai-\ntement des données"])[0]


def test_pdf_to_chunks_end_to_end(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    make_pdf(str(raw / "loi_test.pdf"), ["Article 1\nPremier texte de la loi test.", "Article 2\nSecond texte de la loi test."])
    (raw / "autre.txt").write_text("Article 1\nTexte brut.", encoding="utf-8")
    inv = tmp_path / "inventaire.csv"
    inv.write_text(
        "doc_id,titre,type,statut,langue,domaine\n"
        "loi_test,Loi test,loi,En vigueur,fr,test\n"
        "autre,Autre,loi,abrogé,fr,test\n"
        "absent,Absent,loi,en vigueur,fr,test\n",
        encoding="utf-8",
    )
    cfg = Settings(raw_dir=raw, inventaire=inv, index_dir=tmp_path / "idx")
    chunks = build_chunks(cfg)
    assert {c.doc_id for c in chunks} == {"loi_test", "autre"}  # « absent » ignoré avec avertissement
    lt = [c for c in chunks if c.doc_id == "loi_test"]
    assert [(c.article, c.page) for c in lt] == [("1", 1), ("2", 2)]
    assert lt[0].statut == "en vigueur"  # normalisé en minuscules
    assert extract_pages(raw / "autre.txt") == ["Article 1\nTexte brut."]
