# Passation : Fraudster +1 (état au 18 novembre 2026)

À lire en entier avant toute action. Ce fichier remplace les passations précédentes. Il sert à reprendre le travail
dans une nouvelle session sans tout réexpliquer, en particulier pour **rédiger le chapitre de thèse**.

---

## 1. Règles de travail (à respecter sans exception)

- **Répondre en français.** L'auteur vérifie tout : ne jamais donner un chiffre qui n'a pas été lu dans un fichier
  ou calculé. Chaque chiffre vient d'un fichier du dépôt ou d'une source vérifiée, avec sa référence.
- Dans les textes de la thèse et du site : **« nous »**, jamais « vous / tu ».
- **Aucune valeur choisie à la main sans le dire.** Chaque valeur est sourcée, mesurée, ou déclarée comme hypothèse
  et testée sur une plage.
- La règle des 10 000 € est **« notre premier seuil »** (point de départ de nos travaux précédents), jamais « la règle
  actuelle » ou « la règle d'aujourd'hui ».
- Sur le site : la règle principale s'appelle **« Revision 2 »** (identifiant interne `rev5`) ; ne jamais montrer
  « revision 4/5 » ; ne pas mentionner les encadrants. La page d'accueil montre volontairement le cas favorable
  (monde 1).
- **Pousser ou fusionner seulement avec l'accord explicite de l'auteur**, après avoir résumé les changements.
  Fusion dans `main` par avance rapide quand c'est possible.
- Commits sous le nom de l'auteur, **sans ligne « Co-Authored-By » ni lien de session**.
- Aucune donnée personnelle de l'auteur dans des requêtes à des services extérieurs.
- Toute nouvelle expérience : plan écrit **avant** le calcul (voir les `preregistration_*.md`), règle gelée, nouveaux
  mondes, résultats lus tels quels même défavorables.

## 2. Le sujet en une page

- **Contexte.** Les arnaques crypto augmentent (Chainalysis 2026 : au moins 14 Md$ reçus en 2025, 17 Md$ attendus).
  L'argent volé finit souvent sur des exchanges centralisés, seul endroit où un compte porte une identité vérifiée.
  Sur la chaîne, tout le monde peut tracer ; dans l'exchange, seul l'exchange voit, et c'est là qu'on blanchit.
- **Point de départ.** Une autorité publie une liste noire d'adresses d'arnaque (la **graine**, et sa date τ).
- **Problème.** Parmi les comptes d'exchange qui reçoivent l'argent de la graine, lesquels appartiennent au fraudeur
  ou à ses complices (le « +1 » = le fraudeur potentiel), lesquels sont innocents (victimes remboursées, vendeurs
  P2P, commerces, propriétaires) ?
- **Entrée / sortie.** Entrée : une adresse blacklistée et sa date. Sortie : un grade par compte : G1 surveiller,
  G2 un analyste ouvre un dossier, G3 dossier solide (seul grade qui autorise à agir).
- **Questions de recherche.** Q1 : peut-on tirer d'une liste noire assez d'indices pour désigner des fraudeurs
  potentiels, mieux que notre premier seuil ? Q2 : que gagne-t-on quand les exchanges partagent sans révéler leurs
  clients ? Q3 : comment simuler le cycle de blanchiment dans les exchanges sans leurs données privées, pour pouvoir
  le remplacer un jour par des données réelles ?
- **Traçage.** FIFO dans chaque compte (Anderson et al., « Bitcoin Redux », WEIS 2018 ; arrêt Clayton, 1816).
  On reste au « +1 » : premier compte d'exchange atteint (le portefeuille collecteur du fraudeur ne compte pas comme
  une étape).
- **Grades** (valeurs dans `py/rules.json`, entrée `rev5`, vue `V3`) :
  - G1 = X ≥ 100 € ET (part ≥ 1 % OU X ≥ 10 000 € OU destination commune) ;
  - G2 = G1 ET pas victime ET (part ≥ 20 % OU X ≥ 10 000 € OU destination commune) ET (concentration ≥ 50 % OU
    ≥ 90 % repassé en 24 h) ;
  - G3 = G2 ET (même personne sur ≥ 2 exchanges OU seconde fraude ≥ 5 % OU destination commune).
- **Protocole de partage.** OPRF (RFC 9497) : pseudonyme calculé avec la clé d'une autorité, sans qu'elle voie
  l'identité ; même personne + même affaire = même pseudonyme partout ; seulement pour les comptes G1. Précédent :
  Beacon Network (TRM Labs, août 2025, avec Binance, Coinbase, Kraken, OKX…) ; cadre : AMLR (UE) 2024/1624, art. 75.

## 3. Ce qui a été fait (dans l'ordre, pour le récit du chapitre)

1. Seuil de 10 000 € (nos travaux précédents) → trois grades.
2. Calibration sur des mondes difficiles, zone de valeurs stables (première version calibrée sur des mondes faciles :
   la précision tombait à 88 % ; leçon de méthode).
3. Tests de résistance (15-16 novembre) : innocents à grosse part, innocents sur deux plateformes, destination
   commune. Résultat important : l'indice « même personne » de G3 peut être déclenché par un vendeur P2P innocent
   présent sur deux plateformes ; les parades fondées sur le comportement échouent contre lui.
4. Taille des fraudes : notre échantillon réel (1 448 adresses de phishing, Ethereum, liste ScamSniffer, juillet 2022
   à février 2023) a une médiane de 1 874 €, contre 30 000 € posés à la main.
5. **Erreur trouvée dans le générateur** : dans 83 % des fraudes, les innocents étaient payés en plus du butin.
   Corrigée (`budget_cap="all"`) : une fraude n'envoie jamais plus qu'elle n'a volé. Elle jouait contre nous.
6. **Option B** (plan : `preregistration_optionB.md`) : générateur corrigé, une seule recalibration sur 12 mondes
   fixés à l'avance, plancher de rappel (2 × notre premier seuil), limite sur les acheteurs P2P, règle de repli.
   Résultat : aucune règle ne passe toutes les conditions ; **la règle actuelle est gardée**, aucun seuil ne change.
   Test final unique sur les mondes 18000-18019.
7. Les 12 réglages du test final ne sont pas tirés sur les mêmes fraudes ; les calculs suivants utilisent
   `streams="paired"` (mêmes fraudes dans chaque réglage), testé par `tests/test_paired.py`.
8. Points de rupture refaits sur le générateur corrigé, mondes 43000-43019 (appariés) ; balayages vitesse et nombre de
   mules sur 44000-44009.

Mondes déjà utilisés (ne plus jamais s'en servir pour choisir une valeur) : 14000, 15000, 16000, 17000, 18000,
41000 (arrêté avant lecture), 42000 (diagnostic), 43000, 44000.

## 4. Résultats à citer (et où les lire)

Tout est lu par le site dans `data/thesis.json` (test final, clé `option_b`, `main_E`, `curve`) et
`data/stress.json` (points de rupture). Les fichiers sources sont dans `research/optionB/` et `research/results/`.

- **Monde 1** (médiane 30 000 €, 50 % vers les exchanges) : G2 95,3 % de précision, 41,5 % des comptes trouvés,
  0,06 fausse alerte par fraude ; G3 99,8 % / 31,9 % ; notre premier seuil 81,0 % / 13,7 % ; un exchange seul (sans
  protocole) : G2 94,2 % / 26,1 %.
- **Monde 4** (montants de l'échantillon) : G2 84,7 % / 15,8 %, 0,10 fausse alerte par fraude ; G3 99,1 % / 12,1 % ;
  premier seuil 70,3 % / 4,8 %.
- **12 mondes** : G2 trouve 1,9 à 4,6 fois plus de comptes que notre premier seuil, avec une meilleure précision
  dans les 12 ; précision de G2 de 80,5 % (monde 5, borne basse 77,4 %) à 95,9 % ; au moins 90,1 % si les acheteurs
  P2P comptent comme dossiers à vérifier ; G3 ≥ 98,2 % partout.
- **Six hypothèses sans source publique** (et ce qu'elles font bouger, page Résultats) : les innocents font baisser la
  précision, pas les comptes trouvés ; le comportement des mules fait baisser les comptes trouvés, la précision reste
  ≥ 92 % ; seule la taille des fraudes fait baisser les deux.
- **Données réelles** (BigQuery, phishing Ethereum 2022-2023) : 87,2 M€ envoyés, 8,2 M€ vers 1 011 adresses de dépôt
  en deux étapes ; 428 G1, 98 G2, 14 G3 ; « repayé par une autre arnaque dans les 90 jours » : G3 36 % (8 comptes,
  intervalle 7-75 %) contre 12 % pour les non-signalés : un indice, pas un résultat.
- Mise en liste ScamSniffer : médiane 6,1 jours après le premier argent ; 66 % de l'argent part après la mise en
  liste (`research/realdata/measure_tau.py`). Gel Tether : 26,2 jours, 84 % déjà parti.

## 5. Où se trouve quoi

- Dépôt : `WailZELLAGUI/Blacklisting-` (site GitHub Pages sur `main`). Code du simulateur : `py/`. Recherche :
  `research/` (scripts, résultats, plans écrits avant calcul, `README.md` détaillé). Tests : `tests/` (voir
  `tests/README.md`).
- Présentation (anglais, 37 diapositives, à jour) : https://claude.ai/artifact/MtzaBQGcpQffGgAbiSC4pS
- Affiche (français, A3, 2 pages) : https://claude.ai/artifact/VvmgkpQdppsuSTnEjHkGR1

## 6. En cours

- Branche `table6-p2p-note` (vérifiée, à jour avec `main`, non fusionnée) : note expliquant l'écart 90,6 % / 84,7 %
  (le monde 4 garde les acheteurs P2P de base), source du 66 %.
- Affiche : remplacer « la règle d'aujourd'hui » par « notre premier seuil » ; activité des clients ≈ 450 € par dépôt
  (pas 300 €) ; note sous le tableau D (même explication que la branche ci-dessus) ; ajouter dans chaque carte
  d'hypothèse l'effet sur la précision et sur les comptes trouvés.
- Sources non lues dans l'original (vérifiées par la presse seulement) : chiffres Chainalysis 2026 et 2025, Beacon
  Network. De mémoire, non vérifié : recommandation 16 du GAFI (« travel rule »).
- Écarts jamais expliqués : 1 011 contre 1 034 adresses de dépôt ; 798 contre 690 comptes dans le contrôle à 90 jours.
- Questions pour les encadrants : la cible de 90 % (ou plutôt un nombre de fausses alertes par fraude ?) ; une parade
  pour G3 (confirmer la même personne sans additionner les montants) ; une plateforme partenaire pour mesurer les six
  hypothèses ; la variante fan-out ; la présentation des limites en points de rupture.

## 7. Pour la rédaction du chapitre

Plan suggéré, qui suit les trois questions (la présentation suit déjà cet ordre) :

1. Introduction : arnaques, rôle des exchanges, angle mort, liste noire comme point de départ, « +1 ».
2. Problème formel : notation (graines, τ, paires candidates, y inconnu, grades emboîtés), objectif (rappel sous
   contrainte de précision).
3. Méthode : traçage FIFO, variables, G1, G2, G3 et la justification de chaque valeur.
4. Collaboration : précédents, protocole OPRF, exemple, gain mesuré.
5. Évaluation : simulateur (réglages et sources), correction du générateur, option B (plan, recherche, test final),
   12 mondes, dans le temps.
6. Limites : six hypothèses, points de rupture, données réelles (ce qu'elles montrent et ne montrent pas).
7. Conclusion et perspectives : plateforme partenaire, parade pour G3, données internes.

Décisions à demander à l'auteur avant d'écrire : la langue du chapitre (français ou anglais) et le format (LaTeX,
Word, document Claude). Ne jamais recopier un chiffre de mémoire : relire `data/thesis.json`, `data/stress.json` ou
le fichier de `research/` correspondant.
