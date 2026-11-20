"""Interface en ligne de commande : ingest | ask | compliance | eval."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from .config import settings


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="ragconf", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ingest", help="extraction, découpage et indexation du corpus")

    a = sub.add_parser("ask", help="poser une question")
    a.add_argument("question")
    a.add_argument("--domaine")
    a.add_argument("--doc", help="limiter à un doc_id")

    c = sub.add_parser("compliance", help="vérifier un document (PDF ou TXT) par rapport à un texte de référence")
    c.add_argument("fichier", type=Path)
    c.add_argument("--ref", required=True, help="doc_id du texte de référence")
    c.add_argument("--max", type=int, default=20, help="nombre maximal d'exigences")

    e = sub.add_parser("eval", help="évaluer sur le jeu de questions")
    e.add_argument("--file", type=Path, default=settings.eval_file)
    e.add_argument("--out", type=Path, default=settings.index_dir.parent / "eval" / "resultats.jsonl")

    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.cmd == "ingest":
        from .index import Embedder, build_index
        from .ingest import build_chunks

        chunks = build_chunks(settings)
        if not chunks:
            raise SystemExit("Aucun passage produit : vérifiez data/inventaire.csv et data/raw/.")
        build_index(chunks, Embedder(settings.embedding_model), settings.index_dir)
        print(f"{len(chunks)} passages indexés dans {settings.index_dir}")
        return

    from .pipeline import load_pipeline

    pipe = load_pipeline(settings)

    if args.cmd == "ask":
        ans = pipe.ask(args.question, {"domaine": args.domaine, "doc_id": args.doc})
        print(ans.answer)
        if ans.refused:
            print(f"\n[refus : {ans.reason}]")
        for i, h in enumerate(ans.sources, start=1):
            print(f"  [S{i}] {h.chunk.label()}")

    elif args.cmd == "compliance":
        from .compliance import check_document, extract_requirements, findings_to_markdown
        from .extract import clean_pages, extract_pages

        ref_chunks = [c for c in pipe.retriever.chunks.values() if c.doc_id == args.ref]
        if not ref_chunks:
            raise SystemExit(f"doc_id inconnu : {args.ref}")
        pages = clean_pages(extract_pages(args.fichier))
        reqs = extract_requirements(ref_chunks, pipe.llm, args.max)
        findings = check_document("\n\n".join(pages), reqs, pipe.llm)
        print(findings_to_markdown(findings, ref_chunks[0].titre))

    elif args.cmd == "eval":
        from .evaluate import evaluate, load_questions

        report = evaluate(pipe, load_questions(args.file), args.out)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"Détail : {args.out}")


if __name__ == "__main__":
    main()
