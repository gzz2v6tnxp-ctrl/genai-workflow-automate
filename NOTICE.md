# NOTICE — Data sources & attributions

Ce fichier liste les jeux de données utilisés (ou envisagés) pour le projet **genai-workflow-automate**, leur licence/conditions d'usage connues et le texte d’attribution à afficher dans le README / la page projet / la documentation.

> **Important** : avant toute utilisation commerciale, vérifie toujours la page officielle du dataset pour confirmer la licence et les éventuelles restrictions. Les informations ci-dessous correspondent aux statuts publics généralement indiqués par les fournisseurs au moment de création de ce NOTICE.

---

## 1) CFPB Consumer Complaint Database

* **Source / URL** : Consumer Financial Protection Bureau — Consumer Complaint Database
  `https://www.consumerfinance.gov/data-research/consumer-complaints/`
* **Format** : CSV (disponible aussi via API / JSON)
* **Langue** : Anglais
* **Licence / Usage (statut courant)** : Données du gouvernement fédéral américain — généralement **domaine public** (public domain). Utilisation libre pour démonstration, recherche et usage commercial sans restriction de copyright.
  *(Vérifier la page officielle du CFPB avant un usage commercial critique.)*
* **Texte d'attribution à inclure** (README / NOTICE / page projet) :

  > Data: *CFPB Consumer Complaint Database* — Consumer Financial Protection Bureau. Source: [https://www.consumerfinance.gov/data-research/consumer-complaints/](https://www.consumerfinance.gov/data-research/consumer-complaints/). Licence: données du domaine public (US federal government data). Modifications: extrait nettoyé/anonymisé pour usage de démonstration.

---

## 2) Enron Email Dataset

* **Source / URL** : Enron Email Dataset (diffusé publiquement — distribution CMU / archives publiques)
  Exemple : `https://www.cs.cmu.edu/~enron/` (vérifier le miroir / dépôt exact utilisé)
* **Format** : fichiers texte (.txt / .eml) organisés par utilisateur / dossier (archive tar.gz)
* **Langue** : Anglais
* **Licence / Usage (statut courant)** : Données rendues publiques dans le cadre d’enquêtes et diffusées pour la recherche ; **usage public pour la recherche et la démonstration**. Vérifier la page source du dépôt choisi pour d’éventuelles notes complémentaires.
* **Texte d'attribution à inclure** (README / NOTICE / page projet) :

  > Data: *Enron Email Dataset* — Enron email archive (distributed for research). Source: [https://www.cs.cmu.edu/~enron/](https://www.cs.cmu.edu/~enron/) (ou le miroir utilisé). Licence/usage: donnée publiée pour la recherche; vérifier la source pour conditions précises. Modifications: subset nettoyé/anonymisé pour usage de démonstration.

---

## 3) Zenodo — Bank card chatbot dataset (exemple francophone)

> Section ajoutée pour préparation future — nous n’explorons pas encore ce dataset mais la mention est incluse pour conformité et attribution.

* **Source / URL** : Zenodo (ex. dataset "bank card chatbot" ou titre équivalent)
  Exemple de lien : `https://zenodo.org/record/XXXXXX` (remplacer par le DOI exact lors de l'utilisation)
* **Format** : `.xlsx` / CSV / Parquet selon l'archive (vérifier le fichier exact sur Zenodo)
* **Langue** : Français (selon l’archive mentionnée)
* **Licence / Usage** : **CC BY 4.0 (Attribution)** — permet la copie, modification, distribution et usage commercial à condition d’attribuer correctement l’auteur et d’indiquer les modifications apportées.
* **Texte d'attribution à inclure** (README / NOTICE / page projet) :

  > Data: *[Nom exact du dataset sur Zenodo]* — Auteur / Institution. Source: `https://zenodo.org/record/XXXXXX`. Licence: CC BY 4.0. Modifications: subset nettoyé/anonymisé / synthétisé pour usage de démonstration.

**Remarques spécifiques CC BY 4.0 :**

* Tu dois créditer l’auteur et fournir un lien vers la source (DOI/URL).
* Indiquer si des modifications ont été faites (cleaning, anonymization, augmentation, etc.).
* Le dataset peut être utilisé commercialement sous réserve de l’attribution.

---

## Notes générales & conformité

* **Anonymisation / PII** : Les extraits utilisés pour la démonstration doivent être **nettoyés et anonymisés** (adresses email réécrites, numéros masqués, noms sensibles remplacés) avant toute mise en ligne publique.
* **Dérivés** : Si tu publies un dataset dérivé (nettoyé / enrichi), indique explicitement dans le README : *“Derived from [original dataset name] — cleaned/anonymized.”*
* **Licences croisées** : Si tu combines plusieurs jeux de données, vérifie la compatibilité des licences pour un usage commercial (ex. certains datasets NC/Non-Commercial interdiront la commercialisation).
* **Références & date d’accès** : Pour chaque dataset que tu publies ou mentionnes, fournis le lien exact (DOI / page officielle) et la date d’accès (ex : “accessed 2025-10-13”).


*Fichier généré automatiquement pour le projet genai-workflow-automate — date d’édition : 2025-10-13*
