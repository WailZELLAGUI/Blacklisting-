# Balayage du volume P2P et de la taille des fraudes : grille fixée avant tout calcul

Rédigé le 16 novembre 2026, avant de lancer le moindre calcul de ce balayage. Rien ici ne sera modifié après avoir vu
les résultats. Si une erreur de code oblige à relancer, la correction sera notée en bas de ce fichier, avec sa date.

## 1. La question

Notre précision de G2 (94,2 %) dépend de deux hypothèses sans source quantitative :

- la taille des fraudes, posée à la main (médiane 30 000 €) ;
- l'argent qu'une fraude revend à des acheteurs P2P innocents.

Nous mesurons comment la précision et le rappel de la règle **gelée** varient avec ces deux hypothèses. Ce balayage
ne choisit rien : aucun seuil n'est réglé, et aucune version du générateur n'est retenue à partir de ces résultats.

## 2. Ce qui ne change pas

- La règle : Revision 2 du site (rev5 interne, V3, avec protocole), seuils de `rules.json`, sans route fan-out.
- Le jugement : τ + 90 jours, dates d'alerte ScamSniffer (`blacklist_model = "alert"`).
- Les autres réglages des mondes de test : `TEST3_CFG` et les réglages sourcés (horizon 365 jours).
- La définition du rappel : les comptes impliqués qui reçoivent au moins un paiement tracé.

## 3. Les nouveaux mondes

Les mondes 15000–15019 ont servi à tous les tests de résistance. Ce balayage utilise **20 nouveaux mondes,
16000–16019**, jamais générés jusqu'ici.

Les mondes 17000–17019 (calibration) et 18000–18019 (test final) sont réservés pour une éventuelle nouvelle
calibration, une seule, déclarée comme nouvelle révision. Ils ne sont pas générés dans ce balayage.

## 4. Les facteurs balayés

| Facteur | Valeurs | Pourquoi ces valeurs |
|---|---|---|
| Taille des fraudes F | (a) loi log-normale actuelle, médiane 30 000 €, σ 1,2 ; (b) tirée au hasard parmi les 1 448 montants réels envoyés par nos graines de phishing (BigQuery), sans plancher | (a) le réglage actuel ; (b) la distribution réelle de notre échantillon, avec sa queue lourde, au lieu d'une loi ajustée |
| Volume P2P v : part de F revendue en P2P, par fraude qui revend | 0, 5, 10, 20, 30 % | de « pas de P2P » à un tiers de la fraude ; aucune source ne donne de valeur |
| Nombre d'acheteurs P2P par fraude qui revend | (i) 1 ; (ii) 2 à 10, uniforme (réglage actuel) | un seul acheteur reçoit tout le volume (cas dur) ou le volume est partagé |
| Montants des autres innocents (complices payés, appâts, loyers) | (A) fixes en euros (réglage actuel) ; (B) proportionnels à F (× F / 30 000) | les deux versions du générateur |

Tout le reste du P2P est inchangé : la moitié des fraudes revendent en P2P (`p_p2p = 0,5`), et chaque acheteur
revend lui-même en quelques heures avec une probabilité de 1/2. Le volume v × F est partagé entre les acheteurs
avec les mêmes poids aléatoires que les paiements aux relais.

**D'où vient l'argent du P2P.** Le volume v × F est **retiré** de l'argent que la fraude envoie à ses relais : le
budget des relais devient F × (part des relais) − v × F, sans descendre sous zéro (v × F est alors plafonné à ce
budget). Une fraude ne paie donc jamais plus qu'elle n'a. Les acheteurs P2P sont des clients des exchanges
participants, comme aujourd'hui : leur argent n'est pas réduit par la part allant vers les exchanges (50 %), qui ne
s'applique qu'au budget restant des relais.

**Version B et loyers.** En version B, les montants des appâts et des complices payés sont multipliés par F / 30 000.
Le loyer reste fixe (500 à 1 500 € par mois) : un loyer ne grandit pas avec la fraude.

**Appariement.** Dans les cases du balayage, le P2P tire ses nombres dans son propre flux aléatoire. Deux cases de même
taille de fraude et de même version ont donc les mêmes fraudes, les mêmes relais et les mêmes autres innocents ; elles
ne diffèrent que par le P2P.

Grille complète : 2 tailles × 5 volumes × 2 nombres d'acheteurs × 2 versions = 40 cases (à v = 0, le nombre
d'acheteurs ne joue pas : 32 cases distinctes), dans le monde où 50 % de l'argent va vers les exchanges.

**Case de référence.** Tous les réglages par défaut (P2P actuel : 300 à 3 000 € fixes par acheteur, hors budget ;
F log-normale ; version A), sur les nouveaux mondes 16000–16019. Elle sépare l'effet des nouveaux mondes de celui des
facteurs ; nous attendons une précision de G2 proche de 94 %, sans en faire une condition.

**Contrôles**, chacun sur la case « F réel, v = 20 %, un acheteur, version A » sauf indication :

| Contrôle | Valeurs | Pourquoi |
|---|---|---|
| Part d'argent vers les exchanges | 30 % et 86 % (en plus de 50 %), sur la case « F réel, v = 10 %, 2 à 10 acheteurs, version A » | les trois mondes |
| Fréquence des fraudes qui revendent en P2P | 10 %, 25 % (en plus de 50 %) et 100 % | la fréquence décide autant que le volume, et elle n'a pas de source |
| Probabilité qu'un acheteur revende vite | 0 et 1 (en plus de 1/2) | sans revente rapide, l'acheteur ne passe pas le test de comportement |
| Acheteur présent sur deux plateformes | même personne, deux comptes sur deux exchanges, moitié du volume sur chacun, dans 5 % et 10 % des fraudes (en plus du P2P de la case) | le seul cas connu qui fait tomber G3 ; sans ce contrôle, le balayage ne le teste pas |

## 5. Ce qui est mesuré

Pour G1, G2 ou plus, G3, et la règle des 10 000 € (X ≥ 10 000 €), dans chaque case :

- la précision, avec son intervalle à 95 % et sa borne basse à 5 % (bootstrap sur les 20 mondes, 4 000 tirages) ;
- la part des comptes impliqués trouvés ;
- les fausses alertes par fraude, sous deux dénominateurs : toutes les fraudes générées, et les fraudes qui atteignent
  au moins un compte candidat (X ≥ 100 €) ;
- les fausses alertes par rôle d'innocent ;
- les effectifs : nombre de vraies et de fausses alertes, de fraudes générées et de fraudes qui atteignent un compte.
  Une case avec moins de 100 alertes G2 sur les 20 mondes est marquée « trop peu d'alertes » : sa borne basse n'est
  pas lue comme un point de rupture.

**Deux définitions de la précision, fixées maintenant :**

1. **Principale.** Un acheteur P2P est innocent : s'il est signalé, c'est une fausse alerte.
2. **Complémentaire.** Un acheteur P2P signalé par G2 n'est compté ni comme une bonne ni comme une fausse alerte :
   G2 signifie « un analyste ouvre un dossier », et un acheteur qui convertit l'argent d'une arnaque peut mériter
   d'être regardé. Le rappel ne change pas. G3 et la règle des 10 000 € sont donnés sous la définition principale.

## 6. Comment les résultats seront lus

- **Point de rupture de G2** : pour chaque taille de fraude, nombre d'acheteurs et version, le plus grand volume v pour
  lequel la borne basse à 5 % de la précision de G2 reste au moins à 90 % (définition principale).
- **Comparaison à la règle des 10 000 €**, case par case : précision et comptes trouvés.
- **G3** : la même lecture, avec le même seuil de 90 %.

Le message de la thèse suivra ces résultats tels qu'ils sortent, y compris s'ils sont défavorables.

**Après ce balayage.** Si une nouvelle calibration a lieu (une seule, déclarée comme nouvelle révision), elle se fera
sur les mondes 17000–17019, et la zone robuste devra tenir dans l'ensemble de cases suivant, fixé maintenant :
F log-normale et F réel ; v = 0 % et v = 10 % ; 2 à 10 acheteurs ; versions A et B ; 30 %, 50 % et 86 % d'argent
vers les exchanges. Le test final se fera une seule fois sur les mondes 18000–18019. Aucune version du générateur n'est
choisie entre-temps : les deux restent dans l'ensemble.

## 7. Fichiers

- `sim.py` : nouvelles options `p2p_volume` (part v ; `None` garde le réglage actuel), `p2p_buyers` (1, ou `None`
  pour 2 à 10), `p2p_fast` (probabilité de revente rapide, 1/2 par défaut), `p2p_two_platforms` (part des fraudes
  avec un acheteur sur deux plateformes, 0 par défaut), `F_source` (`"lognormal"` ou `"real"`), en plus de
  `innocent_amounts` (`"fixed"` ou `"fraud"`, loyer toujours fixe).
  Avec les valeurs par défaut, les mondes restent identiques à ceux d'avant, ce qui sera vérifié avant le balayage.
- `experiments21.py` : le balayage ; sorties dans `results13/` (`exp21_raw.csv`, `exp21_summary.csv`,
  `exp21_roles.csv`).

## Historique

- 16 novembre 2026, avant tout calcul : ajouts après relecture par l'autre session (origine de l'argent P2P, case de
  référence, contrôles de fréquence, de revente rapide et d'acheteur sur deux plateformes, dénominateurs et effectifs,
  loyer fixe en version B, appariement, suite prévue).

## Corrections après coup

- 16 novembre 2026, avant tout calcul : erreur de calcul dans la section 4. À v = 0, le nombre d'acheteurs ne joue pas
  dans 2 tailles × 2 versions = 4 paires de cases, donc la grille compte 40 − 4 = **36** cases distinctes (et non 32).
  La grille elle-même ne change pas.
