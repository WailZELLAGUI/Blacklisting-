# Balayage de l'activité normale des clients : grille fixée avant tout calcul

Rédigé le 17 novembre 2026, avant de lancer le moindre calcul de ce balayage. Rien ici ne sera modifié après avoir vu
les résultats. Une correction éventuelle sera notée en bas, avec sa date.

## 1. La question

L'activité normale des clients d'exchange est posée à la main : un montant typique de dépôt d'environ 300 € et un dépôt
toutes les 50 heures environ (0,02 par heure), multipliés par 1,5 dans les mondes de test. Aucune source publique ne la
mesure, et nos données on-chain ne peuvent pas la mesurer (un compte d'exchange reçoit aussi des virements bancaires
et des transferts internes, invisibles sur la chaîne).

Cette activité joue dans deux sens :

- **pour le rappel**, une mule recrutée parmi d'anciens clients actifs a une concentration plus faible, donc elle est
  plus difficile à trouver ;
- **pour la précision**, un innocent plus actif a lui aussi une concentration plus faible, donc il est plus facile à
  écarter.

Nous mesurons comment la règle **gelée** réagit quand cette activité change. Ce balayage ne choisit rien.

## 2. Ce qui ne change pas

- La règle : Revision 2 du site (rev5 interne, V3, avec protocole), seuils de `rules.json`, sans route fan-out.
- Le jugement : τ + 90 jours, dates d'alerte ScamSniffer.
- Les autres réglages : ceux des mondes de test (`TEST3_CFG`, horizon 365 jours), fraudes de taille actuelle
  (médiane 30 000 €), P2P actuel.
- La définition du rappel : les comptes impliqués qui reçoivent au moins un paiement tracé.

## 3. Les nouveaux mondes

**20 nouveaux mondes, 19000–19019**, jamais générés. Les mondes 17000–17019 et 18000–18019 restent réservés à la
seule nouvelle calibration autorisée.

## 4. Les facteurs balayés

| Facteur | Valeurs | Ce que ça change |
|---|---|---|
| Activité normale a (multiplie à la fois le montant typique et la fréquence des dépôts, comme le × 1,5 actuel) | 0,5 ; 1 ; 1,5 (réglage actuel des mondes de test) ; 2 | les clients ordinaires, les anciens clients recrutés comme mules (y compris T7) et les commerces, qui utilisent les mêmes réglages |
| Paiements entre clients (`user_transfers`) | 0 (actuel) ; 0,3 | une part des dépôts vient d'un autre client, qui a le retrait correspondant |

Grille : 4 × 2 = 8 cases. La case « a = 1,5, paiements 0 » est la référence : elle doit redonner, sur les nouveaux
mondes, une précision de G2 proche de 94 %, sans en faire une condition.

## 5. Ce qui est mesuré

Pour G1, G2 ou plus, G3 et la règle des 10 000 € (X ≥ 10 000 €), dans chaque case :

- la précision, avec son intervalle à 95 % et sa borne basse à 5 % (bootstrap sur les 20 mondes, 4 000 tirages) ;
- la part des comptes impliqués trouvés ;
- les fausses alertes par fraude (sur toutes les fraudes, et sur celles qui atteignent un compte candidat) ;
- les fausses alertes de G2 et de G3 par rôle d'innocent ;
- les effectifs : vraies et fausses alertes, fraudes. Une case avec moins de 100 alertes G2 est marquée
  « trop peu d'alertes ».

## 6. Comment les résultats seront lus

- Pour G2 et pour G3 : la borne basse à 5 % de la précision reste-t-elle au moins à 90 % pour chaque valeur de a ?
- Le sens de l'effet : quand a baisse, de combien la précision baisse-t-elle, et de combien le rappel monte-t-il ?
- G3 est lu avec autant d'attention que G2, puisque c'est le seul grade qui autorise à agir.

Le message de la thèse suivra ces résultats tels qu'ils sortent, y compris s'ils sont défavorables. La mise à jour du
site, de l'affiche et de la présentation (« six hypothèses ») se fera seulement après ce balayage.

## 7. Fichiers

- `sim.py` : réglages existants `legit_amount_scale` et `legit_rate_scale` (mis tous deux à a), option
  `user_transfers` du 17 novembre 2026 (0 par défaut, mondes inchangés, vérifié sur le monde 15000).
- `experiments23.py` : le balayage ; sorties dans `results15/` (`exp23_raw.csv`, `exp23_summary.csv`,
  `exp23_roles.csv`).

## Corrections après coup

(aucune)
