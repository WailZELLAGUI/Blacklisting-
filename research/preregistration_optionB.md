# Option B : générateur corrigé, une seule recalibration, un seul test final

Brouillon du 17 novembre 2026, rédigé avant tout calcul de l'option B, à valider par nos encadrants avant de lancer.
Une fois validé, rien ici ne sera modifié après avoir vu les résultats. Une correction éventuelle sera notée en bas,
avec sa date.

## 1. Pourquoi

Le générateur par défaut paie les innocents en plus de ce que la fraude a volé : 83 % des fraudes envoient plus que
leur butin (médiane 1,23 fois). L'erreur joue contre nous (corrigée, la précision de G2 monte de 1 à 5 points et son
rappel baisse de 2 à 3 points, dans tous les cas vérifiés), mais nos chiffres principaux ne doivent pas venir d'un
générateur incohérent. Ce plan corrige le générateur, refait **une seule fois** la recherche des seuils, et teste
**une seule fois**. C'est la dernière recalibration : les mondes de test actuels ont trop servi pour en justifier une
autre.

## 2. Le générateur final

- **Correction par défaut** (`budget_cap = "all"`) : si une fraude envoie plus que son montant, tous ses paiements
  (impliqués, innocents, routes non tracées, sorties fixes des mules « couverture ») sont réduits dans la même
  proportion. La fraude envoie alors exactement son montant et garde sa répartition. C'est une correction d'erreur ;
  la répartition gardée est celle du générateur fautif, la plus prudente pour la précision.
- Tous les autres réglages par défaut restent ceux des mondes de test actuels (`TEST3_CFG`, horizon 365 jours, dates
  d'alerte ScamSniffer).
- `test_budget.py` doit passer sur tous les mondes de calibration et de test avant toute lecture des résultats.

## 3. Les mondes que la zone doit couvrir

Aucune hypothèse incertaine n'est choisie : la zone de seuils doit tenir dans chacun des 12 mondes suivants.

| N° | Taille des fraudes | Part vers les exchanges | Autre réglage |
|---|---|---|---|
| 1 | médiane 30 000 € (actuelle) | 50 % | — |
| 2 | médiane 30 000 € | 30 % | — |
| 3 | médiane 30 000 € | 86 % | — |
| 4 | montants de l'échantillon réel (1 448 graines de phishing) | 50 % | — |
| 5 | échantillon réel | 30 % | — |
| 6 | échantillon réel | 86 % | — |
| 7 | échantillon réel | 50 % | P2P explicite : 10 % de la fraude, 2 à 10 acheteurs |
| 8 | échantillon réel | 50 % | autres innocents payés en proportion de la fraude (version B) |
| 9 | échantillon réel | 50 % | activité des clients a = 0,5 (réglage actuel : a = 1,5) |
| 10 | échantillon réel | 50 % | activité des clients a = 2 |
| 11 | échantillon réel | 50 % | 30 % des dépôts viennent d'autres clients |
| 12 | échantillon réel | 30 % | P2P explicite à 10 % (2 à 10 acheteurs) **et** activité des clients a = 0,5 : plusieurs difficultés cumulées |

Les mondes 1 à 6 croisent les deux hypothèses qui pèsent le plus (taille des fraudes, part vers les exchanges). Les
mondes 7 à 11 font varier une hypothèse à la fois autour du cas le plus difficile (échantillon réel, 50 %). Le monde 12
cumule plusieurs difficultés. Un plan complet (192 combinaisons) serait trop long ; les autres interactions ne sont
pas testées, et ce choix est déclaré ici.

**À trancher avec nos encadrants avant le calcul : le P2P à 10 % est-il un monde plausible ou un point de rupture ?**
Aucune source ne donne cette valeur, et c'est probablement le monde qui fera échouer la contrainte.

- **Choix 1 (proposé par défaut)** : les mondes 7 et 12 restent dans l'ensemble. La règle est calibrée pour résister à
  ce P2P, au prix d'un rappel peut-être plus bas.
- **Choix 2** : le P2P sort de l'ensemble. Le monde 7 est retiré, le monde 12 est gardé sans P2P (échantillon réel,
  30 %, activité × 0,5), et le P2P reste un point de rupture (section 5).

- **Choix 3** : les mondes 7 et 12 restent dans l'ensemble, mais pour la contrainte de G2 on utilise la définition
  complémentaire fixée le 16 novembre 2026 (voir section 4). Comme le générateur par défaut contient déjà des
  acheteurs P2P (la moitié des fraudes revendent en P2P), cette définition et la limite qui l'accompagne s'appliquent
  dans **tous** les réglages, pas seulement aux mondes 7 et 12.

Le choix retenu est écrit ici avant tout calcul : **choix 3**, confirmé le 17 novembre 2026.

## 4. La recherche des seuils (calibration)

- **Mondes de calibration** : 17000–17019, dans chacun des réglages de la section 3.
- **Grille** : la même que la zone robuste du 14 novembre (`experiments17b.GRID`, 30 720 combinaisons) : part σ₂,
  concentration κ, part repassée π, fenêtre δ, lien ET/OU, σ_dom, route du montant. Les seuils de G1 et de G3
  (100 €, 1 %, 5 %) ne changent pas.
- **Contrainte** : borne basse à 5 % de la précision de G2 (bootstrap sur les 20 mondes) **au moins 90 %** dans
  chacun des réglages de la section 3.
- **Acheteurs P2P et précision de G2** : pour la contrainte de précision de G2, un acheteur P2P signalé n'est compté
  ni comme une bonne ni comme une fausse alerte (définition complémentaire du 16 novembre 2026, fixée avant tout
  résultat) : G2 signifie qu'un analyste ouvre un dossier, et un acheteur qui convertit l'argent d'une adresse
  blacklistée relève d'une vérification normale. Les autres innocents (victimes, clients piégés, propriétaires,
  commerces, appâts) restent des fausses alertes. G3 et la règle des 10 000 € gardent la définition principale : un
  acheteur P2P signalé est une fausse alerte, sans aucune tolérance pour G3.
- **Limite sur les acheteurs P2P** : avant la recherche, on mesure sur les mondes de calibration 17000–17019, dans
  chacun des réglages, le nombre moyen d'acheteurs P2P signalés par G2 par fraude avec la règle actuelle (Revision 2
  du site). Une combinaison n'est retenue, dans la zone comme dans la règle de repli, que si elle ne signale pas plus
  d'acheteurs P2P par fraude que la règle actuelle, dans chaque réglage (valeur moyenne sur les 20 mondes, sans borne
  de rééchantillonnage). La règle ne peut donc pas relâcher ses seuils au détriment des marchands.
- **Plancher de rappel** : dans chaque réglage, une combinaison retenue (dans la zone comme dans la règle de repli)
  doit trouver au moins **deux fois plus** de comptes impliqués que la règle des 10 000 €, sur les mêmes mondes de
  calibration.
- **Zone** : les combinaisons qui respectent la contrainte, la limite sur les acheteurs P2P et le plancher partout, et dont le rappel moyen sur tous les réglages est à
  moins de 2 points du meilleur.
- **Point retenu, dans cet ordre** :
  1. si la règle actuelle (Revision 2 du site) est dans la zone, on la garde : aucun seuil ne change ;
  2. sinon, la combinaison de la zone au meilleur rappel moyen ; à égalité, la plus proche de la règle actuelle,
     la distance étant le nombre de réglages de la grille (sur 7) qui diffèrent ; s'il reste une égalité, la première
     dans l'ordre de la grille.
- **Si aucune combinaison ne tient 90 % partout (règle de repli)** :
  - on retient la combinaison qui maximise **la plus mauvaise borne basse** de précision de G2 sur tous les réglages,
    parmi celles dont le rappel moyen sur les réglages est au plus **3 points sous celui de la règle actuelle** et
    qui respectent la limite sur les acheteurs P2P ;
    à égalité, la plus proche de la règle actuelle (même distance) ;
  - si aucune combinaison ne respecte ces conditions, la règle actuelle reste la règle finale ;
  - les **deux** règles, l'actuelle et celle de repli, sont testées sur les mondes 18000–18019 et publiées côte à côte.
    Elles sont toutes deux fixées avant le test : ce n'est pas un choix après coup ;
  - le seuil de 90 % ne bouge pas. La thèse dira qu'il n'est pas garanti dans tous les mondes plausibles, avec la
    meilleure garantie obtenue, réglage par réglage.
- **Quelle règle devient la règle finale** (fixé avant le calcul) : s'il existe une zone, la combinaison retenue dans la
  zone ; sinon, la règle de repli si elle existe ; sinon, la règle actuelle. La règle actuelle est toujours publiée à
  côté, comme comparaison. C'est la dernière révision : plus aucun seuil ne change ensuite.
- **G3** : il n'est pas contraint, mais il change avec les seuils de G2 (G3 = G2 plus un indice). Pour la règle
  retenue (et la règle de repli), si la borne basse de la précision de G3 passe sous 95 % dans un réglage de
  calibration, nous le signalons dans les résultats, avec le réglage concerné.

## 5. Le test final

- **Mondes de test** : 18000–18019, une seule fois, dans tous les réglages de la section 3, avec la ou les règles
  gelées à l'issue de la section 4.
- **Mesuré** pour G1, G2 ou plus, G3 et la règle des 10 000 € : précision avec intervalle à 95 % et borne basse à 5 %,
  comptes trouvés, argent couvert (part de l'argent reçu par les comptes impliqués candidats qui se trouve sur des
  comptes signalés), fausses alertes par fraude, fausses alertes par rôle, effectifs ; dans le temps
  (τ + 1, 7, 30, 90 jours).
- **Coût des acheteurs P2P, toujours visible** : pour G2, la précision sous les deux définitions (principale et
  complémentaire), et le nombre d'acheteurs P2P signalés par fraude, dans chaque réglage.
- **Chiffres principaux** : le réglage 1 (continuité avec nos résultats) et le réglage 4 (cohérent avec notre
  échantillon réel), côte à côte. Les autres réglages forment le tableau de robustesse, avec la même vérification de G3 (signalée sous 95 %).
- **Points de rupture** : les balayages précédents (P2P, acheteur sur deux plateformes, destination commune) seront
  refaits sur le générateur corrigé avec la règle finale, sur de nouveaux mondes (20000–20019), après le test final.

## 6. Ensuite

- `test_budget.py` est copié dans `tests/` du dépôt du site.
- Le site, l'affiche, la présentation et la thèse sont mis à jour **une seule fois**, avec les chiffres du test final.
- En attendant, les limites mentionnent : « dans notre générateur, les innocents étaient payés en plus du butin ;
  corrigé, la précision de G2 augmente de 1 à 5 points et le rappel baisse de 2 à 3 points ».

## Historique

- 17 novembre 2026, avant tout calcul : ajouts après relecture par l'autre session (monde 12, règle de repli testée à
  côté de la règle actuelle, vérification déclarée de G3, distance entre règles, question du P2P à trancher).
- 17 novembre 2026, avant tout calcul : choix 3 retenu pour le P2P ; coût des acheteurs P2P rapporté à part.
- 17 novembre 2026, avant tout calcul : choix 3 et limite sur les acheteurs P2P appliqués dans tous les réglages, et à
  la règle de repli (relecture par l'autre session).
- 17 novembre 2026, avant tout calcul : plancher de rappel (deux fois la règle des 10 000 €, par réglage) ; désignation
  de la règle finale ; activité des clients écrite comme le réglage a du balayage du 17 novembre ; définition de
  l'argent couvert ; choix 3 confirmé par Wail Zellagui.

## Corrections après coup

- 17 novembre 2026, après le test final, avant tout calcul des points de rupture : les mondes 20000–20019 prévus en
  section 5 ne sont pas nouveaux (les mondes 20000–20009 ont servi aux balayages de experiments7 et experiments18s,
  avec d'autres réglages). Les points de rupture sont refaits sur les mondes 41000–41019, jamais générés. Rien d'autre
  ne change.
- 17 novembre 2026, après le test final, diagnostic qui ne change aucune règle (experiments29.py,
  results18/diag_world12.csv) : le monde 12 (échantillon réel, 30 %, P2P 10 %, activité 0,5) donne à G2 une meilleure
  précision (86,6 %) que le monde 5 (échantillon réel, 30 % ; 80,5 %), alors qu'il contient les mêmes difficultés et
  d'autres en plus. Cause : le générateur tire les fraudes dans le même flux aléatoire que l'activité des clients et le
  plan P2P ; à numéro de monde égal, les mondes 5 et 12 ne contiennent donc pas les mêmes fraudes. Chaque ajout seul,
  sur les mêmes mondes 18000–18019, ne remonte pas la précision (5 + P2P : 80,1 % ; 5 + activité : 79,5 %). Sur 20
  autres mondes (42000–42019), l'écart tombe à 80,4 % contre 83,1 %, intervalles qui se chevauchent. Nous ne
  présentons donc pas le monde 12 comme le pire cas ; le pire monde mesuré est le monde 5.
- 18 novembre 2026, avant de refaire les points de rupture et les balayages (aucun chiffre de ces calculs n'a été lu) :
  le diagnostic du monde 12 montre que les 12 réglages du test final ne sont pas tirés sur les mêmes fraudes. Le test
  final reste gelé tel quel ; nous écrivons dans les résultats qu'un écart de quelques points entre deux mondes peut
  venir du tirage. Avant les calculs suivants, le générateur reçoit l'option `streams="paired"` : les paramètres de
  chaque fraude (montant volé, schéma, nombre de relais, dates) viennent de leur propre flux, le reste de chaque fraude
  d'un flux à elle. Le test tests/test_paired.py vérifie qu'à réglages égaux sur la fraude, chaque fraude garde son
  montant, son schéma, ses relais et ses dates. `streams="shared"` (défaut) redonne exactement tous les résultats
  antérieurs, dont ce test final. Mondes : la section 5 prévoyait 20000–20019 ; ils ont été remplacés par 41000–41019 (correction
  précédente, mondes déjà utilisés), dont le premier passage (générateur non apparié) a été arrêté sans lecture ; les points de rupture sont faits sur 43000–43019 et les balayages de vitesse et
  de nombre de mules sur les mêmes 10 mondes 44000–44009 pour chaque réglage, tous en `streams="paired"`. Les mondes
  42000–42019 ont servi au diagnostic du monde 12.
- 18 novembre 2026, même note : le simulateur du site garde les réglages par défaut du test final gelé
  (`budget_cap="all"`, `streams="shared"`), pour que « créer un monde » corresponde aux résultats affichés. Le monde
  2027 du site change donc par rapport au 16 novembre (correction du budget active), et data/world_default.json est
  régénéré. Les balayages appariés n'utilisent que 10 mondes (44000–44009), comme les balayages précédents : leurs
  intervalles sont plus larges que ceux des tableaux sur 20 mondes, ce que le site écrit sous ces figures.
