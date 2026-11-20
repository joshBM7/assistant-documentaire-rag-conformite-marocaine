# Assistant documentaire RAG – conformité des documents publics

Projet EMSI — Joshua-Phil-Lilan BAYONNE-MANGA · Djamila HACHIMI SOBA

Implémentation de l'architecture décrite dans le document « Dataset · Cahier des charges · Périmètre et architecture ».

```
Sources PDF -> extraction/OCR -> nettoyage -> chunking par article -> embeddings -> ChromaDB + BM25
Question -> recherche hybride (RRF) [+ reranking] -> LLM avec citations [S#] -> garde-fous -> réponse sourcée
Document soumis + texte de référence -> exigences -> verdict par exigence (conforme / non conforme / non déterminé)
```

## Structure

| Fichier | Rôle |
|---|---|
| `ragconf/extract.py` | Extraction PDF (PyMuPDF), OCR de secours (Tesseract), nettoyage |
| `ragconf/chunking.py` | Découpage par article (FR et AR), pages d'origine, passages longs avec chevauchement |
| `ragconf/ingest.py` | Lecture de `data/inventaire.csv` et production des passages |
| `ragconf/index.py` | Embeddings multilingues + index ChromaDB |
| `ragconf/retrieve.py` | BM25 + dense, fusion RRF, filtres (domaine, statut…), reranking optionnel |
| `ragconf/pipeline.py` | Prompt, génération, application des garde-fous |
| `ragconf/guardrails.py` | Citations obligatoires, article inventé détecté, refus par défaut |
| `ragconf/compliance.py` | Extraction d'exigences et vérification d'un document |
| `ragconf/evaluate.py` | Métriques de récupération, citations, refus ; export compatible RAGAS |
| `ragconf/api.py`, `app.py` | API FastAPI et interface Streamlit |

## Installation

```bash
python -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # puis renseigner ANTHROPIC_API_KEY
```

L'OCR nécessite Tesseract avec les langues `fra` et `ara` (inclus dans l'image Docker). Sans Tesseract, les PDF natifs fonctionnent normalement.

## Utilisation

1. **Corpus** : placer les textes officiels dans `data/raw/<doc_id>.pdf` et décrire chaque document dans `data/inventaire.csv`
   (colonnes obligatoires : `doc_id, titre, type, statut, langue, domaine`). Vérifier le statut (en vigueur / abrogé) de chaque texte sur la source officielle.
2. **Indexation** : `python -m ragconf.cli ingest`
3. **Question** : `python -m ragconf.cli ask "Quel est le délai de réponse à une demande d'accès à l'information ?" --domaine acces_information`
4. **Conformité** : `python -m ragconf.cli compliance mon_document.pdf --ref loi_09_08`
5. **API + interface** :
   ```bash
   uvicorn ragconf.api:app --port 8000
   streamlit run app.py
   ```
   ou `docker compose up --build`.
6. **Évaluation** : copier `data/eval/questions.template.jsonl` vers `data/eval/questions.jsonl`, le remplir (50 à 100 questions, catégories `factuelle`, `synthese`, `conformite`, `sans_reponse`), puis `python -m ragconf.cli eval`.
   `data/eval/resultats.jsonl` contient `question / answer / contexts / ground_truth`, utilisables directement avec RAGAS (fidélité, pertinence).

## Tests

```bash
pytest -q
```
Les tests utilisent un faux embedder et un faux LLM : ils ne téléchargent aucun modèle et n'appellent aucune API.

## Réglages (variables d'environnement)

`EMBEDDING_MODEL` (défaut `intfloat/multilingual-e5-small`, alternative `BAAI/bge-m3`), `RERANKER_MODEL` (vide = désactivé, ex. `BAAI/bge-reranker-v2-m3`), `LLM_MODEL`, `TOP_K`, `CANDIDATES`, `CHUNK_MAX_CHARS`, `CHUNK_OVERLAP`.

## Limites connues

- Les garde-fous vérifient les citations `[S#]` et les numéros d'articles mentionnés, mais ne garantissent pas que chaque phrase soit fidèle à sa source : relire un échantillon et mesurer la fidélité avec RAGAS.
- Le contrôle de conformité repère les extraits du document par recherche lexicale (BM25) ; un document qui reformule fortement une exigence peut recevoir « non déterminé ».
- Le découpage par article suppose que chaque article commence en début de ligne (`Article N`, `المادة N`). Tableaux et annexes sont découpés par paragraphes.
- Aucune donnée du corpus n'est fournie : les textes doivent être téléchargés depuis les sources officielles.
- Aide à la décision uniquement, pas un avis juridique.
