# Évaluation et métriques du pipeline RAG

Ce document décrit les métriques, seuils et le comportement de l'agent RAG (Retrieve → Generate → Evaluate) utilisé dans ce projet.
Il explique aussi où trouver les logs, comment lire les résultats et comment ajuster les seuils.

## Vue d'ensemble du pipeline

Étapes principales :
- retrieve : récupération des documents via Qdrant (vecteurs + métadonnées)
- grade_documents : évaluation initiale de la pertinence (score top1)
- generate : génération LLM (OpenAI) en s'appuyant explicitement sur les documents récupérés
- evaluate_response : quality gate post-generation
- fallback / human_review : chemins alternatifs quand la quality gate échoue

Le graphe est implémenté dans `agents/graph.py` (StateGraph). L'API qui appelle le graphe est `router/chatbot.py`.

## Mécaniques d'évaluation (evaluate_response)

L'objectif du `evaluate_response` est d'empêcher la livraison d'une réponse non-ancrée ou hallucinée. Il calcule plusieurs indicateurs :

- avg_score
  - Moyenne des scores retournés par le retriever pour les sources utilisées.
  - Calcul : `avg_score = sum(scores) / len(scores)`.
- confidence
  - Valeur dérivée utilisée pour décider si la réponse est suffisamment fiable.
  - Calcul : `confidence = avg_score * 0.8`.
- cites_ok
  - Booléen indiquant si la génération cite explicitement au moins un ID de source OU si un chevauchement textuel satisfaisant a été détecté.
  - Détecte la présence d'IDs (par ex. `[...]`) dans le texte généré.
  - Ou teste un `overlap_ratio` (voir dessous).
- overlap_ratio
  - Proportion de documents dont un extrait (snippet) apparaît dans la génération.
  - Calcul simplifié : nombre de docs dont le snippet (ex. 200 premiers caractères) est présent dans la génération divisé par le nombre total de documents.
- hallucination
  - Détecte la présence d'années (ex. 1999, 2025) ou de montants (ex. 1,000.00 $ / 1 000 €) dans la génération qui ne figurent pas dans les documents récupérés.
  - Heuristique simple : si une date/montant présent dans la génération n'est pas trouvé dans la concaténation des documents, on marque `hallucination=True`.

### Décision (actuelle)

- `quality_pass` = True si :
  - pas d'hallucination
  - `confidence >= 0.35`
  - ET (`cites_ok` == True OR `overlap_ratio >= 0.35`)

- `escalate` = True si la réponse échoue et que `confidence < 0.25` ou `hallucination == True`.

Si `quality_pass` est True → la réponse est renvoyée.
Si `quality_pass` est False et `escalate` True → on route vers `human_review` (message d'escalade et snapshot pour réviseurs humains).
Si `quality_pass` est False et `escalate` False → fallback (message d'absence d'information).

Les seuils ci-dessus sont conservateurs et destinés à limiter le risque d'hallucination. Ils peuvent être ajustés après observation.

## Logs & artefacts

Les fichiers produits par la pipeline :

- `logs/metrics.jsonl`
  - Format JSON Lines. Chaque ligne contient : timestamp, question, avg_score, confidence, cites_ok, overlap_ratio (si présent), hallucination, quality_pass, escalate, num_sources.
  - Utilisé pour monitorer le taux de succès et pour l'analyse post-mortem.

- `logs/llm_responses.jsonl`
  - Contient un enregistrement par génération LLM avec : timestamp, question, response_lang, detected_ids (IDs trouvés dans la génération), generation_trunc (extrait), num_sources.
  - Utile pour vérifier si le LLM respectait l'instruction de citer les sources.

- `snapshots/for_review/<id>.json`
  - Snapshot complet (question, documents, sources, generation, metrics) écrit quand `quality_pass == False`. Destiné à la revue humaine et à la constitution d'un dataset de « bad-cases ».

- Console logs
  - Le router ajoute une ligne console : `[chatbot] chosen_mode=... confidence=... response_lang=... sources_filter=...` ce qui facilite le traçage en live.

## Où vérifier si le LLM a cité des IDs

1. `logs/llm_responses.jsonl` : cherche la dernière ligne correspondant à ta question et regarde `detected_ids`.
2. Si `detected_ids` contient des IDs, mais que `metrics.jsonl` indique `cites_ok: false`, regarde `overlap_ratio` et la logique d'évaluation (peut être que la forme de citation n'était pas identique aux IDs stockés).
3. Inspecte le snapshot (si créé) dans `snapshots/for_review` — il contient la génération complète et les documents.

Exemple PowerShell pour tail :

```powershell
Get-Content .\logs\llm_responses.jsonl -Tail 20
Get-Content .\logs\metrics.jsonl -Tail 20
Get-Content .\snapshots\for_review\ -Filter *.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { Get-Content $_ }
```

## Comportement de l'agent (routing)

- Si `grade_documents` renvoie `not_relevant` → on va directement à `fallback`.
- Si `grade_documents` renvoie `relevant` → on appelle `generate`.
- Après `generate`, `evaluate_response` valide la réponse.
  - Si validée : sortie finale.
  - Si rejetée et `escalate` True : `human_review` (message d'escalade et snapshot écrit).
  - Si rejetée et `escalate` False : `fallback` (message standard du service).

## Conseils pratiques & debugging

1. Si l'UI renvoie une réponse en anglais alors que la génération LLM est en français :
   - Vérifie `logs/llm_responses.jsonl` pour confirmer la langue de la génération.
   - Vérifie `router/chatbot.py` : le router prend maintenant la sortie d'`evaluate_response` comme source de vérité pour `response_lang` et `confidence`. Assure-toi qu'il n'y a pas d'anciennes réponses en cache (Redis/local cache). Le cache key inclut `sources_filter` désormais.

2. Si le LLM n'extrait pas d'IDs dans sa génération :
   - Le prompt inclut un bloc `ID + excerpt` et une instruction d'ancrage. Tu peux :
     - baisser la température (cf. `config.OPENAI_TEMPERATURE`) à 0.0–0.2
     - demander une sortie JSON structurée (ex: `{"answer":"...","cited_ids": ["id1"]}`) dans le prompt si tu veux un parsing plus robuste.

3. Pour tester le pipeline localement :

```powershell
# Test direct du graphe (contourne l'API)
python - <<'PY'
from agents.graph import app
payload = {"question":"Carte bancaire bloquée et transaction en panne", "collection":"knowledge_base_main", "sources_filter":["cfpb","enron","synth"]}
for output in app.stream(payload):
    print(output)
PY
```

4. Pour ignorer le cache temporairement :
   - Soit flush Redis, soit modifier localement `router/chatbot.py` pour accepter un param `no_cache` (optionnel).

## Ajustement des seuils (recommandation)

- Commencer par observer 100–200 requêtes réelles et retenir : taux de `quality_pass`, taux d'`escalate`, exemples de snapshots.
- Ajuster :
  - `confidence` threshold (actuellement 0.35). Si trop de rejets → descendre progressivement à 0.30 → 0.25.
  - `overlap_ratio` threshold (actuellement 0.35). Si le modèle paraphrase beaucoup, augmente la tolérance de détection (ex. identifier matching via fuzzy matching au lieu de `in` strict).
  - Si le modèle n'obéit pas à la consigne de citation, privilégier une sortie JSON structurée.

## Exemples de patterns à analyser

- `cites_ok == False` et `overlap_ratio` faible : la génération n'utilise pas de phrases identiques aux snippets — peut être paraphrase. Envisager une vérification rapproche (fuzzy) plutôt que `in`.
- `hallucination == True` : la génération inclut une date/montant absent des docs — la réponse doit être rejetée.
- `escalate == True` : cas qui doivent absolument aller en revue humaine (threshold très bas de confiance ou hallucination détectée).

## Annexes — fichiers et fonctions utiles

- `agents/graph.py` : implémentation du graphe, des nœuds `generate` & `evaluate_response`.
- `router/chatbot.py` : endpoint REST qui appelle le graphe et choisit la réponse finale (gère cache + sources_filter).
- `scripts/vector_store/retrieve.py` : wrapper autour de Qdrant (vérifier le champ `id`, `score`, `content`, `metadata.source`).

---

Si tu veux, je peux :
- ajouter un endpoint debug pour récupérer le dernier snapshot ou metrics pour une question donnée ;
- ajouter un petit script d'analyse qui agrège `logs/metrics.jsonl` et produit un rapport (taux de pass/fail, histogramme des confidences) ;
- ajouter un mécanisme de `fuzzy overlap` si tu veux détecter paraphrases plutôt que `in` strict.

Dis-moi quelle option tu préfères et je l'ajoute dans un prochain patch.