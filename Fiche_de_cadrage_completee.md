# Fiche de suivi des projets agents IA

Master • Présentation de l’avancement et plan de correction

Groupe : 3   Projet n° : 19   Date : 20/11/2026

Intitulé du projet : Assistant documentaire RAG pour la conformité des documents publics

Membres : Joshua-Phil-Lilan BAYONNE-MANGA, Djamila HACHIMI SOBA

Jalon examiné : cadrage, corpus et pipeline d’ingestion   Prochain point :evaluation et metrique

> Légende : evaluation et metrique= information que seul le groupe connaît. \*\*\[prevu]\*\* = à confirmer sur la machine du groupe avant la séance. Les statuts utilisés sont : \*démontré\*, \*commencé\*, \*prévu\*, \*bloqué\*.

## Utilisation de la fiche

Avant chaque point, chaque groupe complète les réponses et rassemble les preuves. Présenter en 10 minutes : bilan, démonstration, résultats et blocages. Prévoir ensuite 5 minutes de questions. Chaque membre explique sa contribution et un choix technique.

Pour chaque rubrique, distinguer ce qui est prévu, commencé, démontré ou bloqué. Une fonction est démontrée lorsqu’un scénario reproductible et son résultat peuvent être vérifiés. Justifier toute question sans objet. Si un élément manque, indiquer la correction et son échéance.

## Bilan et périmètre

**1. Quel problème métier traitez-vous, pour quel utilisateur et avec quel résultat attendu ?**

Preuve à présenter : Un cas d’usage précis et un critère de réussite mesurable.

Réponse du groupe :

* **Problème** : vérifier qu’un document ou une pratique respecte des textes réglementaires oblige à retrouver les bons articles dans des textes dispersés, parfois modifiés, puis à les citer correctement. Un LLM seul peut inventer un article ou citer une version abrogée, ce qui rend sa réponse inutilisable en conformité.
* **Utilisateurs** : agent administratif ou juriste (questions sur un texte, vérification avant diffusion) ; responsable conformité (contrôle d’un document par rapport à une liste d’exigences) ; citoyen ou entreprise (consulter ses obligations).
* **Résultat attendu** : des réponses fondées uniquement sur un corpus de textes officiels marocains, avec citation de la source (texte, article, page), un rapport de conformité par exigence, et un refus explicite quand le corpus ne contient pas la preuve.
* **Critères de réussite (cibles indicatives, à ajuster après les premiers tests)** : fidélité ≥ 85 % ; pertinence de la réponse ≥ 80 % ; rappel du contexte ≥ 80 % ; exactitude des citations ≥ 90 % ; refus approprié sur les questions hors corpus ≥ 80 %.

**2. Quel périmètre MVP avez-vous retenu et quelles fonctions avez-vous reportées ?**

Preuve à présenter : Liste des fonctions incluses et exclues, validée par le groupe.

Réponse du groupe :

* **Inclus (MVP)** : corpus de 7 textes réglementaires publics ; pipeline d’ingestion (extraction, nettoyage, découpage par article, indexation) ; recherche hybride (sémantique + BM25) avec reranking optionnel ; génération avec citations et garde-fous ; module de vérification de conformité d’un document par rapport à un texte de référence ; API et interface web de démonstration ; jeu d’évaluation et rapport de résultats.
* **Exclu / reporté** : avis juridique ou décision officielle de conformité ; documents confidentiels ; couverture exhaustive de la réglementation marocaine ; fine-tuning d’un modèle ; mise en production à grande échelle, authentification avancée ; mise à jour automatique du corpus depuis le Bulletin officiel ; corpus en arabe (le code gère l’arabe, mais le corpus actuel est en français).

**3. Qu’aviez-vous prévu depuis le dernier point et qu’avez-vous réellement terminé ?**

Preuve à présenter : Fonctions terminées, en cours et bloquées, avec preuve pour chacune.

Réponse du groupe :

|Fonction|Statut|Preuve|
|-|-|-|
|Cahier des charges, périmètre, architecture|Démontré|Document Word « Dataset · Cahier des charges · Périmètre et architecture »|
|Collecte du corpus (7 textes)|Démontré|7 PDF dans `data/raw/`, `data/inventaire.csv`|
|Extraction, nettoyage, découpage, indexation|Démontré|Sortie de `python -m ragconf.cli ingest` : 649 passages indexés|
|Chaîne de question-réponse (recherche, génération, garde-fous)|Commencé|Code et tests unitaires ; pas encore démontrée sur le corpus réel avec le LLM \[À VÉRIFIER]|
|Module de conformité|Commencé|Code et tests unitaires ; pas encore testé sur un document réel|
|API FastAPI et interface Streamlit|Commencé|Code écrit ; endpoints testés par tests automatisés ; application non encore lancée de bout en bout|
|Jeu d’évaluation (50 à 100 questions)|Prévu|Modèle de fichier `data/eval/questions.template.jsonl` ; questions à rédiger|
|Mesure des métriques et comparaison à une baseline|Prévu|Code d’évaluation écrit (`ragconf/evaluate.py`) ; aucun résultat chiffré à ce jour|
|Docker|Commencé|`Dockerfile` et `docker-compose.yml` écrits, non construits ni testés|

**4. Que peut-on exécuter aujourd’hui sans intervention manuelle cachée ?**

Preuve à présenter : Démonstration de bout en bout sur un scénario reproductible.

Réponse du groupe :

* **Exécutable et démontré** : `python -m ragconf.cli ingest` lit l’inventaire, extrait et nettoie les 7 PDF, les découpe par article et construit l’index (résultat : 649 passages).
* **À démontrer avant la séance** : `python -m ragconf.cli ask "..." --doc loi\_31\_13`, qui nécessite la clé `ANTHROPIC\_API\_KEY` dans `.env` \[À VÉRIFIER].
* **Étapes manuelles à déclarer** : le téléchargement des PDF depuis les sites officiels, leur renommage (`doc\_id.pdf`) et la rédaction de `inventaire.csv` sont faits à la main. Aucun scraping automatique n’est prévu dans le MVP.

État général : retard maîtrisable (corpus et pipeline d’ingestion prêts ; validation des réponses, évaluation et démonstration de bout en bout restent à faire) \[À CONFIRMER selon le jalon exigé]

Décision ou aide attendue de l’enseignant :

1. Le projet est une chaîne RAG à étapes fixes, sans agent autonome : est-ce conforme aux attentes du module, ou faut-il ajouter une couche agentique (par exemple un routeur qui choisit entre recherche, extraction d’exigences et refus) ?
2. Quels documents réels faut-il utiliser pour tester la conformité (documents d’administration, appels d’offres, politiques de confidentialité) ?
3. Quelles métriques d’évaluation sont attendues dans le rapport final ?

## Données et architecture

**5. Quel dataset ou corpus utilisez-vous exactement et comment y accède-t-on ?**

Preuve à présenter : Nom, URL, version ou date, licence et fichiers retenus.

Réponse du groupe : corpus de 7 textes réglementaires marocains publics, décrits dans `data/inventaire.csv`.

|doc\_id (fichier)|Texte|Source|Passages|
|-|-|-|-|
|loi\_09\_08.pdf|Loi 09-08, protection des données à caractère personnel|Adala (ministère de la Justice)|118|
|loi\_31\_13.pdf|Loi 31-13, droit d’accès à l’information (dahir 1-18-15)|Adala|34|
|loi\_55\_19.pdf|Loi 55-19, simplification des procédures administratives|Adala|37|
|loi\_43\_20.pdf|Loi 43-20, services de confiance pour les transactions électroniques|Adala|90|
|loi\_05\_20.pdf|Loi 05-20, cybersécurité|Adala|58|
|decret\_2\_21\_406.pdf|Décret 2-21-406, application de la loi 05-20|Adala|25|
|decret\_2\_22\_431.pdf|Décret 2-22-431, marchés publics (BO du 9 mars 2023)|Copie hébergée par la FNBTP (source officielle : Bulletin officiel)|287|

* **Accès** : portail Adala (adala.justice.gov.ma, recherche par titre du dahir) ; Bulletin officiel sur sgg.gov.ma pour recouper.
* **URL exactes et dates de publication** : \[À COMPLÉTER dans `inventaire.csv`, colonnes `url` et `date\_publication`].
* **Licence** : conditions de réutilisation non encore relevées sur chaque source \[À COMPLÉTER].
* **Version** : le statut « en vigueur » de chaque texte a été renseigné dans l’inventaire mais n’a pas encore été vérifié contre d’éventuels textes modificatifs \[À VÉRIFIER].

**6. Les données couvrent-elles réellement le problème posé ? Que simulez-vous ?**

Preuve à présenter : Variables utiles, labels, limites et distinction entre réel et synthétique.

Réponse du groupe :

* **Réel** : tous les textes du corpus sont des documents officiels réels. Aucune donnée synthétique dans le corpus.
* **Variables utiles** : pour chaque passage, texte, document, article, page, domaine, type, statut, langue.
* **Labels** : aucun à ce jour. Le jeu d’évaluation (questions, réponses attendues, articles sources) reste à construire manuellement.
* **Couverture** : 7 textes ne couvrent qu’une partie de la réglementation (données personnelles, accès à l’information, simplification administrative, confiance numérique, cybersécurité, marchés publics). Une question hors de ces domaines doit être refusée.
* **Documents à vérifier (module de conformité)** : pas encore choisis. Si des documents de test sont rédigés par le groupe, ils seront déclarés comme synthétiques.

**7. Comment avez-vous nettoyé, annoté et séparé les données sans fuite ?**

Preuve à présenter : Pipeline, exemples avant/après, splits et règles anti-doublons.

Réponse du groupe :

* **Pipeline** : extraction PyMuPDF (OCR Tesseract français/arabe en secours si une page n’a pas de texte) → suppression des en-têtes, pieds de page répétés et numéros de page → correction des césures → découpage par article (un passage par article, redécoupage avec chevauchement si l’article dépasse 1 800 caractères) → rattachement des métadonnées de l’inventaire.
* **Anti-doublons** : identifiant unique par passage (`doc\_id::numéro de section-numéro de morceau`), vérifié par test automatisé.
* **Exemples avant/après** : \[À COMPLÉTER : extrait d’un PDF et passage correspondant dans `data/index/chunks.jsonl`].
* **Séparation sans fuite** : il n’y a pas d’entraînement, donc pas de split classique. Règle prévue pour l’évaluation : les questions sont rédigées à part, divisées en un lot de réglage (environ 30 %) pour ajuster le prompt et les paramètres, et un lot de test (environ 70 %) qui n’est utilisé qu’à la fin.
* **Point à contrôler** : le décret 2-21-406 produit 25 passages pour 25 pages ; vérifier que ses articles sont bien reconnus avec `check\_chunks.py` \[À VÉRIFIER].

**8. Quelle insuffisance des données risque de fausser votre conclusion ?**

Preuve à présenter : Biais identifié et mesure concrète pour en réduire l’effet.

Réponse du groupe :

* **Biais principal** : un jeu d’évaluation écrit à partir des mêmes 7 textes donnera des résultats trop optimistes, parce que les questions facilement retrouvables par recherche lexicale surreprésentent les cas faciles.
* **Mesures** : inclure des questions de synthèse (plusieurs articles), des questions de conformité et des questions sans réponse dans le corpus ; comparer recherche hybride, BM25 seul et recherche sémantique seule ; relire manuellement un échantillon de réponses.
* **Autres insuffisances** : un seul texte (le décret des marchés publics) vient d’une copie tierce ; le statut des textes (en vigueur ou abrogé) n’est pas vérifié ; corpus uniquement en français.

**9. Quels composants fonctionnent et comment échangent-ils les données ?**

Preuve à présenter : Schéma d’architecture à jour et exemple de requête API.

Réponse du groupe :

* **Schéma** : figure 1 du document « Dataset · Cahier des charges · Périmètre et architecture » (ingestion → requête → évaluation). Les composants effectivement utilisés sont : PyMuPDF, ChromaDB, rank-bm25, sentence-transformers (`intfloat/multilingual-e5-small`), API Anthropic, FastAPI, Streamlit. LangChain et Qdrant, cités comme options dans le document, n’ont pas été retenus \[À METTRE À JOUR dans le document].
* **Ce qui fonctionne (démontré)** : ingestion et indexation.
* **Flux** : `ingest` écrit `chunks.jsonl` et l’index Chroma ; à chaque question, la recherche hybride fusionne les résultats sémantiques et BM25 (fusion RRF), le LLM reçoit les passages numérotés \[S1], \[S2]…, puis les garde-fous valident la réponse.
* **Exemple de requête API** (après `uvicorn ragconf.api:app --port 8000`) :

```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \\
  -d '{"question": "Quel est le délai de réponse à une demande d’accès à l’information ?", "doc\_id": "loi\_31\_13"}'
```

Réponse : JSON avec `answer`, `refused`, `reason`, `cited` et la liste `sources` (référence S#, document, article, page, extrait, score). Cette API a été testée avec des composants factices, pas encore lancée sur le corpus réel \[À VÉRIFIER].

**10. Pourquoi avez-vous choisi ces frameworks plutôt qu’une solution plus simple ?**

Preuve à présenter : Justification liée au besoin, aux compétences et aux ressources.

Réponse du groupe :

* **Pas de framework d’orchestration (LangChain, LlamaIndex)** : le code est écrit directement (quelques centaines de lignes) pour garder le contrôle des citations et des garde-fous, qui sont le cœur du besoin, et limiter les dépendances.
* **ChromaDB** : base vectorielle embarquée, sans serveur, adaptée à quelques milliers de passages sur un portable.
* **BM25 en complément** : les textes juridiques contiennent des termes exacts (numéros d’articles, intitulés) que la recherche sémantique seule retrouve mal.
* **`multilingual-e5-small`** : modèle multilingue léger (français et arabe), utilisable sans GPU. Alternative plus lourde prévue : BGE-M3.
* **FastAPI et Streamlit** : API simple et interface de démonstration rapide à produire.
* **API Anthropic pour le LLM** : pas de GPU local nécessaire ; changer de modèle ne demande que de modifier `LLM\_MODEL`.

**11. Comment gérez-vous l’état, la mémoire, les erreurs et les reprises ?**

Preuve à présenter : Modèle d’état, journal d’une exécution et exemple d’échec traité.

Réponse du groupe :

* **État et mémoire** : chaque question est traitée indépendamment, sans mémoire de conversation. L’état persistant se limite à `data/index/` (passages et index vectoriel), reconstruit à chaque `ingest`.
* **Erreurs traitées** : fichier source absent (avertissement, document ignoré) ; colonne manquante dans l’inventaire (erreur explicite) ; échec de l’OCR (avertissement, page conservée telle quelle) ; réponse du LLM non exploitable en JSON dans le module de conformité (verdict « non déterminé ») ; document soumis de format ou de taille non accepté (HTTP 415 ou 413) ; texte de référence inconnu (HTTP 404).
* **Reprise** : pas de reprise partielle ; en cas d’échec de l’ingestion, on relance `ingest`, qui reconstruit tout.
* **Journal d’une exécution** : le journal INFO de `ingest` donne pages et passages par document \[À COMPLÉTER : coller la sortie]. Le journal des requêtes n’est pas encore implémenté.

Correction prioritaire sur les données ou la conception : vérifier le découpage du décret 2-21-406 ; ajouter un journal des requêtes et des décisions de refus ; aligner le document d’architecture avec les choix réellement faits.

## Fonctionnement des agents et protocole

**12. Quelle décision l’agent prend-il et quels outils appelle-t-il ?**

Preuve à présenter : Trace d’un scénario avec entrées, décisions, appels et sorties.

Réponse du groupe :

* **Précision** : le système n’est pas un agent autonome. C’est une chaîne à étapes fixes dont le LLM prend deux types de décisions encadrées : répondre ou refuser (jeton « INSUFFISANT »), et rendre un verdict par exigence (conforme, non conforme, non déterminé).
* **Outils appelés** : recherche hybride (Chroma + BM25, reranking optionnel) et API du LLM. Aucun autre outil, aucune action externe.
* **Trace d’un scénario** : \[À COMPLÉTER : coller la sortie de `python -m ragconf.cli ask "Quel est le délai de réponse à une demande d’accès à l’information ?" --doc loi\_31\_13`, avec la question, les sources S1…S5 et la réponse].

**13. Quel résultat obtenez-vous avec des règles ou une chaîne sans agent ?**

Preuve à présenter : Comparaison sur les mêmes cas, avec le même budget de calcul.

Réponse du groupe : la solution est elle-même une chaîne sans agent. La comparaison prévue porte sur les mêmes questions du jeu de test : (a) LLM seul sans récupération, (b) BM25 seul, (c) recherche sémantique seule, (d) recherche hybride, (e) hybride avec reranking. Statut : prévu, aucun résultat à ce jour.

**14. Si plusieurs agents collaborent, quel rôle distinct remplit chacun ?**

Preuve à présenter : Rôles, échanges et comparaison avec un agent unique. Sinon expliquer l’absence de multi-agents.

Réponse du groupe : pas de multi-agents. Les tâches sont séquentielles et partagent le même contexte (passages retrouvés) ; plusieurs agents ajouteraient des appels au LLM, de la latence et du coût sans gain démontré. Le même LLM est appelé avec trois consignes différentes (répondre avec citations, extraire des exigences, juger une exigence), ce qui sépare les rôles sans multiplier les agents.

**15. Comment vérifiez-vous une sortie du LLM avant de l’utiliser ?**

Preuve à présenter : Validation du format, contrôle des sources, test métier et cas d’abstention.

Réponse du groupe :

* **Questions** : une réponse est refusée si elle ne contient aucune citation \[S#], si elle cite un extrait inexistant, si elle mentionne un numéro d’article absent du contexte fourni, ou si le modèle répond « INSUFFISANT ». Si aucun passage n’est retrouvé, le LLM n’est même pas appelé.
* **Conformité** : la sortie doit être un JSON valide ; un verdict hors liste devient « non déterminé » ; un verdict « conforme » sans preuve extraite du document est rétrogradé en « non déterminé ».
* **Limite** : ces contrôles ne garantissent pas que chaque phrase soit fidèle à sa source ; c’est ce que doivent mesurer RAGAS et la relecture d’un échantillon.
* **Preuve** : tests automatisés des garde-fous et du module de conformité.

**16. Quelles actions exigent une validation humaine et quelles limites imposez-vous ?**

Preuve à présenter : Permissions, plafond d’appels, coût maximal et scénario d’action refusée.

Réponse du groupe :

* **Permissions** : le système ne fait que lire le corpus et interroger le LLM ; il n’exécute aucune action sur des systèmes externes. La décision de conformité reste à l’humain (mention « aide à la décision, pas un avis juridique » dans l’interface et dans les rapports).
* **Limites en place** : 5 passages par question ; 15 exigences par défaut dans l’API (20 en ligne de commande, 30 au maximum) ; longueur de réponse limitée ; fichiers limités à 15 Mo et aux formats PDF et TXT.
* **Non implémenté** : plafond global d’appels ou de coût par session.
* **Scénario d’action refusée** : un fichier `.exe` est rejeté (HTTP 415) ; une question hors corpus reçoit un refus argumenté.

**17. Quels tests prouvent que les fonctions annoncées marchent réellement ?**

Preuve à présenter : Tests automatisés, résultat daté et anomalies encore ouvertes.

Réponse du groupe :

* **Tests** : 36 tests (`pytest -q`) couvrant le découpage par article, le nettoyage et l’ingestion d’un PDF de bout en bout, la recherche hybride (y compris avec ChromaDB), les garde-fous, la chaîne de réponse, le module de conformité, le calcul des métriques et les endpoints de l’API. Résultat du 20/11/2026 : 36 réussis \[À VÉRIFIER : relancer `pytest -q` sur la machine du groupe].
* **Anomalies ouvertes** : les tests utilisent un faux modèle d’embeddings et un faux LLM ; ils prouvent la logique, pas la qualité des réponses sur le corpus réel.

**18. Quels indicateurs avez-vous choisis et pourquoi conviennent-ils au projet ?**

Preuve à présenter : Définition des métriques, baseline et protocole de mesure.

Réponse du groupe :

|Indicateur|Définition|Pourquoi|
|-|-|-|
|Rappel de récupération (hit)|L’article attendu figure parmi les passages retrouvés|Sans le bon article, aucune réponse fiable|
|Exactitude des citations|Au moins une citation renvoie à l’article attendu|Traçabilité exigée en conformité|
|Refus correct|Question hors corpus refusée|Éviter les réponses inventées|
|Faux refus|Question avec réponse refusée à tort|Mesure l’utilité du système|
|Fidélité et pertinence (RAGAS)|Réponse appuyée par les passages ; réponse adaptée à la question|Qualité de la génération|

* **Baseline** : LLM seul sans récupération ; BM25 seul ; recherche sémantique seule.
* **Protocole** : 50 à 100 questions (factuelles, de synthèse, de conformité, sans réponse) rédigées par le groupe, lot de réglage et lot de test séparés, commande `python -m ragconf.cli eval`.

Correction prioritaire sur l’agent ou les tests : construire le jeu d’évaluation, tester le système avec le vrai LLM, définir la baseline.

## Résultats et déploiement

**19. Quels résultats chiffrés obtenez-vous sur un jeu de test distinct ?**

Preuve à présenter : Tableau baseline/solution, taille du test, latence et coût par scénario.

Réponse du groupe : aucun résultat chiffré à ce jour. Le jeu de test n’est pas encore construit. Voir le tableau « Résultats à comparer » ci-dessous.

**20. Quels sont vos trois échecs les plus importants et comment les expliquez-vous ?**

Preuve à présenter : Entrées, sorties observées, causes probables et correction envisagée.

Réponse du groupe : aucun échec mesuré sur un jeu de test. Les trois défauts trouvés pendant le développement grâce aux tests, et corrigés :

1. **Recherche lexicale sur petit corpus** : avec l’algorithme BM25 de départ, un document court recevait des scores négatifs ou nuls et n’était jamais retrouvé. Cause : calcul de l’IDF sur très peu de documents. Correction : passage à BM25Plus et filtre sur les mots communs avec la requête.
2. **Nettoyage trop agressif** : sur des pages courtes, les lignes « Article N » étaient prises pour des en-têtes répétés et supprimées. Correction : exclusion des lignes d’article du nettoyage et zone d’en-tête réduite.
3. **OCR** : l’ingestion plantait si Tesseract n’avait pas la langue demandée. Correction : l’échec de l’OCR est signalé en avertissement sans interrompre l’ingestion.

Les échecs sur le jeu de test (entrée, sortie observée, cause) seront ajoutés après l’évaluation.

**21. Quelles entrées difficiles ou hostiles avez-vous testées ?**

Preuve à présenter : Données manquantes, outil indisponible, prompt malveillant, réponse non sourcée.

Réponse du groupe :

* **Testées (tests automatisés)** : réponse du LLM sans citation ; citation d’un extrait inexistant ; article inventé ; réponse du LLM qui n’est pas du JSON ; document sans passage pertinent ; fichier au mauvais format ; texte de référence inconnu ; question vide ; fichier source manquant à l’ingestion.
* **Non testées** : injection de consignes (prompt injection) dans un document soumis ; indisponibilité de l’API du LLM ; PDF scanné de mauvaise qualité sur le corpus réel \[À FAIRE].

**22. Un autre groupe peut-il installer et lancer votre application ?**

Preuve à présenter : README vérifié, dépendances fixées et commande de lancement.

Réponse du groupe :

* **Disponible** : `README.md` (installation, commandes `ingest`, `ask`, `compliance`, `eval`, `pytest`) et `requirements.txt`.
* **Non fait** : les versions des dépendances ne sont pas fixées (minimum de version seulement) ; le README n’a pas été vérifié sur une autre machine ; Docker n’a pas été testé.
* **Correction prévue** : fixer les versions (`pip freeze`) et faire tester l’installation par un autre groupe.
* **Commande de lancement** : `uvicorn ragconf.api:app --port 8000` puis `streamlit run app.py`.

**23. Quelle version est déployée et quel parcours avez-vous validé ?**

Preuve à présenter : Commit ou version, environnement, démonstration et résultat du test de bout en bout.

Réponse du groupe : aucune version déployée. Exécution locale sous Windows, Python 3.12. Commit ou dépôt GitHub : \[À COMPLÉTER]. Parcours validé : ingestion et indexation du corpus (649 passages). Le parcours question → réponse citée reste à valider \[À VÉRIFIER].

**24. Comment protégez-vous les secrets, les accès et les données ?**

Preuve à présenter : Configuration sans secrets, contrôle d’accès et politique de journalisation.

Réponse du groupe :

* **Secrets** : la clé `ANTHROPIC\_API\_KEY` est dans `.env`, exclu du dépôt par `.gitignore` ; `.env.example` ne contient que des valeurs fictives.
* **Données** : le corpus est public. Un document soumis pour contrôle est écrit dans un fichier temporaire le temps du traitement puis supprimé ; il est cependant envoyé au LLM via l’API.
* **Accès** : aucune authentification sur l’API ; à ajouter avant toute exposition hors machine locale.
* **Journalisation** : journal INFO de l’ingestion ; pas de journal des requêtes pour l’instant (à ajouter, sans enregistrer le contenu des documents soumis).

### Résultats à comparer

|Indicateur|Baseline|Solution|Jeu ou scénario|
|-|-|-|-|
|Rappel de récupération (hit)|\[à mesurer : BM25 seul / sémantique seule]|\[à mesurer : hybride]|`questions.jsonl` (à construire)|
|Exactitude des citations|\[à mesurer : sans objet pour LLM seul]|\[à mesurer]|`questions.jsonl` (à construire)|
|Fidélité (RAGAS)|\[à mesurer : LLM seul]|\[à mesurer : RAG complet]|`questions.jsonl` (à construire)|
|Refus correct (hors corpus)|\[à mesurer : LLM seul]|\[à mesurer]|questions `sans\_reponse`|
|Latence et coût|\[à mesurer]|\[à mesurer]|par question et par rapport de conformité|

Pour un projet industriel, démontrer en simulation et expliquer les limites du passage au réel. Pour un projet informatique, montrer les droits accordés aux outils et les actions qui exigent une validation humaine. (Projet informatique : l’outil est en lecture seule, voir question 16.)

## Contributions et corrections

**25. Quelle contribution chaque membre peut-il présenter et expliquer ?**

Preuve à présenter : Tâches, commits, résultats et revue croisée. Chaque membre explique au moins un choix technique.

Réponse du groupe : \[À COMPLÉTER : répartition réelle]. Pistes de tâches à attribuer : collecte et vérification du corpus et de l’inventaire ; pipeline d’ingestion (découpage par article) ; recherche hybride et garde-fous ; module de conformité ; API et interface ; jeu d’évaluation et métriques. Pour chaque membre, préparer un choix technique à expliquer (par exemple : découpage par article, fusion RRF, refus par défaut, rétrogradation d’un « conforme » sans preuve).

**26. Quel blocage menace le prochain jalon et de quelle aide avez-vous besoin ?**

Preuve à présenter : Cause précise, tentatives déjà faites et décision attendue.

Réponse du groupe : pas de blocage technique à ce jour. Points de vigilance : disponibilité de la clé API du LLM et son coût pendant l’évaluation ; choix des documents réels pour tester la conformité ; temps nécessaire pour rédiger 50 à 100 questions de référence. Aide attendue : voir « Décision ou aide attendue de l’enseignant ».

**27. Quelle affirmation ou fonctionnalité devez-vous corriger après cette revue ?**

Preuve à présenter : Écart entre prévu et observé, cause et preuve de correction attendue.

Réponse du groupe :

* Le document d’architecture annonce la journalisation des requêtes : elle n’est pas implémentée.
* Il cite LangChain et Qdrant comme options : le code utilise ChromaDB sans framework d’orchestration.
* L’affirmation que le système est « un agent » doit être précisée : c’est une chaîne RAG à étapes fixes.
* Preuve de correction : document mis à jour et journal des requêtes ajouté.

**28. Quelles sont vos trois prochaines actions prioritaires ?**

Preuve à présenter : Action observable, responsable nommé, échéance et test d’acceptation.

Réponse du groupe : voir le plan de correction ci-dessous.

**29. Faut-il réduire le périmètre ou revoir le choix des données ou des outils ?**

Preuve à présenter : Décision argumentée et effet sur le planning et les livrables.

Réponse du groupe : pas de réduction du périmètre à ce stade. Si le temps manque, on abandonnera en premier le reranking et le support de l’arabe, et on limitera le module de conformité à deux textes de référence. \[À CONFIRMER après la séance avec l’enseignant]

**30. Quelle preuve présenterez-vous lors du prochain point d’avancement ?**

Preuve à présenter : Jalon vérifiable et scénario exact qui permettra de le valider.

Réponse du groupe : un tableau de résultats sur le jeu de test (rappel de récupération, exactitude des citations, refus correct, fidélité, latence et coût) comparant au moins le LLM seul, BM25 seul et la recherche hybride, plus une démonstration de bout en bout : question → réponse citée, question hors corpus → refus, document soumis → rapport de conformité.

### Plan de correction à valider

|Action prioritaire|Responsable|Échéance|Preuve de correction|
|-|-|-|-|
|1. Valider `ask` sur le corpus réel (10 questions du corpus et 3 hors corpus) et vérifier le découpage du décret 2-21-406|BAYONNE|27/11|Sorties collées dans le rapport ; au moins 3 refus corrects sur 3 questions hors corpus|
|2. Construire le jeu d’évaluation (50 questions minimum) et lancer `eval` avec baselines|BAYONNE|27/11|`resultats.jsonl` et tableau de métriques|
|3. Tester le module de conformité sur un document réel, ajouter le journal des requêtes et fixer les versions des dépendances|HACHIMI|30/11|Rapport de conformité généré ; journal visible ; installation réussie par un autre groupe|

Décision de la revue : \[poursuivre / corriger avant le prochain jalon / réduire le périmètre]

Commentaire de l’enseignant : \[à compléter]
