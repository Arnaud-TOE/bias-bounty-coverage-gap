# Bias Bounty Mapping Equity Challenge : analyse complète

*État au 16 octobre 2026, 16 h 40 (heure locale). Clôture le 31 octobre 2026, soit 15 jours restants.*
*Sources : onglets Info, Data, Chat (4 pages, environ 95 fils), Leaderboard et Submissions du compte connecté ; README Source Cooperative ; notebook tutoriel ; dépôts publics des participants ; recherche web (voir la section 9).*

---

## 1. Ce qui est demandé

- **Tâche :** prédire un `coverage_gap_score` compris entre 0 et 1 pour **9 794 secteurs de recensement** (le texte de la page Info, qui parle de 9 379, n'est plus à jour).

| Région | Risque | Secteurs notés |
|---|---|---|
| south-central-tx | chaleur, sécheresse | 6 003 |
| maricopa-az (+1 secteur NM) | chaleur, sécheresse | 1 593 |
| eastern-ok (terres tribales) | sécheresse, chaleur | 1 192 |
| northern-ca | feux de forêt | 591 |
| **eastern-wa** (ajoutée le 28 septembre) | feux, sécheresse | 415 |

- **Métrique :** RMSE. Le classement public porte sur environ 30 % des secteurs, le classement privé sur les 70 % restants. Il faut **choisir 2 soumissions finales**.
- **Limites réelles :** **5 soumissions par jour et 200 au total** (et non 10 et 300 comme l'indique la page Info). Le compteur affiche **0/200 utilisées**.
- **Format :** `GEOID,coverage_gap_score`, avec le GEOID **en texte** (zéro initial de l'Arizona, code 04). Des colonnes de composantes optionnelles sont acceptées, mais une cellule vide entraîne le rejet du fichier.

### Définition de la cible, calculée par les organisateurs (README + page Info)

`score = moyenne des composantes DÉFINIES` parmi :

1. **Transport :** `1 − min(1, km Overture[motorway, trunk, primary, secondary] / km TIGER[S1100, S1200])`. La composante n'est pas définie s'il n'y a pas de route nommée de ce type dans TIGER. Elle n'est pas comparable d'une région à l'autre (ratio de 0,71 à 1,59).
2. **Bâtiments :** `1 − min(1, nombre de bâtiments Overture / nombre d'empreintes Microsoft)`. Le nombre de logements ACS sert uniquement de contrôle.
3. **POI :** moyenne de deux moitiés.
   - **Moitié HIFLD** = moyenne des types définis parmi :
     - casernes de pompiers (`categories.primary == fire_department`) ;
     - EMS (`ambulance_and_ems_services`) ;
     - écoles (`elementary_school`, `middle_school`, `high_school`, `school`, `private_school`, `public_school`).

     Pour chaque type : `1 − min(1, O/H)`. Les hôpitaux sont exclus, car Overture en compte environ 12 fois plus que HIFLD. **Les EMS sont presque à 1:1 : ce sont les casernes de pompiers qui portent la composante.**
   - **Moitié CBP** : comparaison de tous les lieux Overture avec les établissements recensés par CBP.

- Proportion de secteurs avec au moins une composante non définie : OK 21 %, CA 37 %, TX 28 %, AZ 55 %.
- Les secteurs dont les trois composantes sont non définies sont retirés de la liste.

## 2. Le point décisif : il n'y a pas de labels

- **25 septembre :** les couches de référence (TIGER, Microsoft Buildings, HIFLD, CBP) sont retirées du bucket.
- **28 septembre, règle officielle :** il est **interdit de reconstruire, inférer ou approximer la cible** à partir de ces couches, y compris depuis une autre source publique.
- **8 octobre, staff :**
  - « *No tract-level training or validation labels will be released.* »
  - Les features dérivées des données fournies (attributs Overture, colonnes autorisées des tables de strates) sont permises.
  - Les valeurs calculées avant le retrait des couches sont également interdites.
- **Conséquence :** c'est un problème d'**estimation sans labels**. Le **seul signal supervisé** est le RMSE public, avec 5 lectures par jour.
- **Pas d'entraînement supervisé possible.** Il faut un modèle **structurel** de la formule, alimenté par des estimations indirectes, puis **calibré avec quelques paramètres globaux** lus sur le leaderboard.

## 3. Le leaderboard : ce qu'il montre vraiment

> **Correction du 18/10 (vérifiée sur les 259 lignes du classement).** Zindi a **recalculé toutes les soumissions avec le RMSE corrigé**. Les scores affichés sont désormais tous des RMSE. Preuves :
> - les comptes du staff (meganomaly, soumission vieille de 23 jours ; aaronchase96, 18 jours, donc avant la correction) affichent 0,107246 (fichier tout à zéro en RMSE), et non 0,059806 ;
> - Hunter_Toledo affiche 0,0799, et non ses 0,05639 de l'ancien calcul ; loGan7 affiche 0,0825, et non 0,0554 ;
> - de nombreuses lignes affichent 0,089022 (meilleure constante) ou 0,097676 (constante 0,10).
>
> Ce qui suit dans cette section, sur les « scores de l'ancien calcul » encore affichés, était vrai vers le 10 octobre mais **ne l'est plus**. Au 18/10 :
> - rangs 1 à 10 : reconstruction (RMSE de 0 à 0,011) ;
> - **rangs 11 à 72 : RMSE réels de 0,0564 à 0,0768**, soit une corrélation d'environ 0,77 avec la vérité pour le 11e ;
> - nous (Arnaud_TOE) : 79e sur 259 avec 0,078204.

| Rang | Score public | Interprétation |
|---|---|---|
| 1 à 4 (Juliuss, lcodecorn, bertholdt, aluha501) | **0** | reconstruction exacte avec les couches retirées (bertholdt l'écrit lui-même : « Exact Geometric Reconstruction ») |
| 5 à 10 | 0,00009 à 0,0108 | idem, reconstruction approchée |
| 11 à 50 | 0,0572 à 0,0733 | **surtout des scores de l'ancien calcul** (voir ci-dessous) |

**Le calcul du score a changé le 2 octobre vers 00 h 00 UTC.** Avant cette date, le scorer se comportait comme une MAE ; il calcule désormais un vrai RMSE.

| Fichier | Avant le 2 octobre | Après le 2 octobre |
|---|---|---|
| Fichier tout à zéro | 0,0598 | 0,1072 |
| Un même fichier (cas cité dans le Chat) | 0,0429 | 0,0794 |

- Le leaderboard affiche **le meilleur score historique** de chaque participant, donc beaucoup de scores de l'ancien calcul.
- **Question encore ouverte :** tout sera-t-il recalculé pour le classement privé, et les soumissions faites avec les couches retirées seront-elles écartées ? Plusieurs participants l'ont demandé, sans réponse à ce jour. Il est très probable que les 10 premiers soient disqualifiés lors de la revue de code.

**Ce que l'on sait du nouveau calcul (sous-ensemble public, valeurs publiées par d'autres participants, à re-mesurer nous-mêmes) :**
- moyenne de la cible ≈ **0,0598**, écart-type ≈ **0,0890**, distribution très asymétrique (la plupart des secteurs sont proches de 0, avec une longue traîne) ;
- RMSE(c) = √(σ² + (m − c)²) : la **meilleure constante donne 0,0890** et le fichier tout à zéro 0,1072.

**Meilleurs scores conformes connus après correction :**

| Participant | Approche | RMSE public |
|---|---|---|
| vigohan | modèle de « gap attendu » + mélange de 5 signaux par corrélations implicites | **0,077475** (et 0,0796) |
| Hunter_Toledo | 3 niveaux : rural × peuplé × zéro caserne | 0,0853 |
| saierror | — | ≈ 0,093 |

D'autres équipes peuvent faire mieux sans que cela se voie, car leur meilleur score affiché date de l'ancien calcul.

**Moyennes de groupe mesurées par sondage du leaderboard (publiées par argszero_reg et Hunter_Toledo) :**
- **par région :** OK 0,1285 · WA 0,0848 · CA 0,0671 · TX 0,0488 · AZ 0,0406 ;
- **par profil de secteur :** « rural, peuplé, sans caserne Overture » 0,131 (783 secteurs) · rural autre 0,097 · urbain 0,048 ;
- **terres tribales :** 0,077 contre 0,058 hors terres tribales.

**Corrélations implicites avec la vérité (vigohan) :**
- prior « strates rural/tribal » : +0,37 ;
- modèle structurel : +0,34 ;
- part de bâtiments d'origine Microsoft : +0,29 ;
- part de routes sans nom : +0,22 ;
- POI seuls : +0,12 ;
- probabilité qu'une composante soit non définie : −0,21 ;
- **mélange : +0,50**, soit un RMSE ≈ 0,0775.

**Lecture :** le score est d'abord un signal de ruralité et d'absence de caserne de pompiers.

> ⚠️ **Le « Scoring Rubric » de chaque ligne du leaderboard est le Bias Scorecard de la soumission.** Pour les lignes à RMSE 0, il révèle les rapports de disparité de la **vraie** cible (rural/urbain 2,34×, tribal 2,88×, etc.). Ces valeurs viennent de soumissions reconstruites avec les couches interdites : **nous ne les utiliserons pas** pour calibrer quoi que ce soit.

## 4. Questions de conformité encore ouvertes (aucune réponse du staff)

| Sujet | Risque | Position recommandée |
|---|---|---|
| Colonnes de strates `usfs_BuildingCount_sum`, `usfs_HUCount_sum`, `carbonplan_buildings` (calculées à partir des empreintes Microsoft) | élevé : proche de la référence « bâtiments » | **les exclure** de la soumission principale ; garder éventuellement une variante pour comparaison |
| Bâtiments Overture d'origine Microsoft (attribut `sources`) | faible : ce sont des données Overture fournies | autorisé (le staff autorise explicitement les « attributs Overture ») |
| Attributs `routes` d'Overture (réseau US:I, US:US, routes d'État) comme proxy des grands axes | faible à moyen | autorisé : données fournies ; à documenter clairement |
| Calibrer quelques **constantes globales** à partir du RMSE public | faible si le nombre de paramètres reste petit | ≤ ~15 paramètres globaux ou régionaux, tous journalisés ; **aucun sondage au niveau du secteur ni de petits groupes** |
| Moyennes de groupe publiées par d'autres participants, scorecards des soumissions reconstruites | moyen à élevé | **ne pas utiliser** ; tout re-mesurer avec nos propres soumissions |
| Couches retirées utilisées pour le Bias Discovery | autorisé par le staff le 8 octobre, « comme preuve de comparaison » | possible, mais **strictement isolé** du pipeline de scoring |

## 5. Règles et exigences à respecter

- **Outils :** langages et outils open source uniquement ; **AutoML interdit** ; aucune API payante dans le pipeline ; modèles pré-entraînés autorisés s'ils sont ouverts.
- **Assistants de code (LLM) :** autorisés pour écrire, déboguer et documenter, **à condition de ne pas être nécessaires pour exécuter ou reproduire la solution**.
- **Reproductibilité :** seeds fixées, résultats déterministes, pas de packages personnalisés. Le **top 10 doit envoyer son code sous 48 h**, et Zindi peut demander le code à tout moment (délai de 24 h).
- **Comptes et partage :** un seul compte, partage privé de code interdit, licence des données CC-BY-SA 4.0.
- **Prix spéciaux :** formulaire Google (connexion Google obligatoire), **PDF de 10 Mo maximum**. **Date limite : mercredi 4 novembre 2026 à 23 h 59 GMT**, indiquée sur le formulaire d'envoi et signalée par l'utilisatrice le 18/10 ; la page Info ne la mentionne pas. Un fil du Chat signale que le formulaire ne permet de cocher qu'**un seul prix**, donc il faudra probablement **deux envois**. Il faut préciser :
  - votre pseudo Zindi ;
  - les identifiants des soumissions associées.

  En cas d'égalité, **la candidature la plus ancienne l'emporte** : il faut donc envoyer tôt.

  Lien : https://docs.google.com/forms/d/e/1FAIpQLScaX0u6IaSaSj8BZqGxhqoq7sw_Bq_sfjj6Ma-R41E3aik0aA/viewform
- **Best Bias Discovery** (Impact 30 % · Nouveauté 25 % · Preuves 25 % · Reproductibilité 20 %) :
  - mettre en évidence un motif **hors** des 5 métriques et strates du scorecard ;
  - citer les secteurs concernés et chiffrer la disparité ;
  - expliquer les conséquences concrètes pour les secours, l'évacuation ou l'aide d'urgence ;
  - les données publiques externes sont autorisées si elles sont ouvertes, documentées (URL et date) et reproductibles.
- **Best Documentation :** méthodologie la plus claire et reproductible :
  - les sources ;
  - le calcul de chaque composante ;
  - les cas limites (population nulle, secteurs surtout en eau, secteurs sans données Overture) ;
  - les pondérations alternatives et leur justification.

## 6. Données (Source Cooperative, accès public sans identifiants)

- `reference/<région>/` : Overture `buildings`, `roads` (classes carrossables), `roads-unfiltered`, `rail`, `infrastructure`, `pois` ; ACS B25001 ; `sample-submission`. Environ 4,5 Go au total.
- `strata/` : table jointe de 232 colonnes. Elle couvre :
  - SVI, CVI, RUCA/RUCC/NCHS, terres tribales ;
  - sécheresse : USDM, SPI/PMDI ;
  - chaleur : EPHT, NASA, CDC WONDER ;
  - feux : USFS, CarbonPlan, MTBS, NIFC, FPA-FOD, USGS ;
  - stations météo NOAA.

  Il existe une version nationale de 85 396 secteurs et des versions par région. Environ 1,7 Go.
- **Overture 2026-08-19.0 uniquement.** CRS84 (lon/lat) : utiliser `always_xy := true` ou `ST_FlipCoordinates` dans DuckDB.
- **Champs utiles :**
  - `sources[]` (jeu de données d'origine, `update_time`) ;
  - `names.primary`, `categories.primary` / `alternate`, `confidence` ;
  - `routes[].network` / `ref` pour les routes ;
  - `class` pour les routes.
- Les POI Overture ne contiennent **aucun enregistrement OpenStreetMap**. Ils viennent de Meta, Foursquare, Microsoft, AllThePlaces, etc. Les routes viennent à 99,9 % d'OpenStreetMap.

## 7. Prix spéciaux : concurrence déjà déclarée (environ 55 candidatures publiques)

Thèmes **déjà pris**, à éviter ou à dépasser nettement :
- casernes absentes ou mal classées (terres tribales, Choctaw, « fire-station line », VFD classés `fire_protection_service`) ;
- routes sans nom, routes « fantômes » issues de l'import TIGER 2007-2011 ;
- provenance des bâtiments (IA ou OSM), précision géométrique ;
- colonias, mobile homes ;
- faux hôpitaux, urgences de Paradise, mauvaise localisation d'établissements, taxonomie EMS, dialyse pédiatrique ;
- absence d'adresses ;
- feux passés (MTBS), « l'eau » (Shivoo29), passages à gué au Texas ;
- petites villes, comté d'Osage, Tulsa, stations météo GHCN ;
- strates intersectionnelles SVI ;
- critiques de la formule elle-même (composante unilatérale, jointure LEFT, modèle de données TIGER, pondération par composantes définies).

Pistes **apparemment libres** (à confirmer par un audit de nouveauté), voir le plan :
- (A) **connectivité du réseau** : routes coupées, impasses, communautés à une seule sortie, invisibles pour une métrique de longueur ;
- (B) **structures fantômes après incendie** : bâtiments détruits toujours sur la carte, vérifiables avec CAL FIRE DINS ;
- (C) **refuges contre la chaleur** à Maricopa (Heat Relief Network) ;
- (D) **établissements à évacuer en priorité** (maisons de retraite CMS) dans les zones de feu et de chaleur.

## 8. Faut-il un entraînement ? GPU ? Modèle pré-entraîné ?

- **Il n'y a pas d'entraînement supervisé à faire**, puisqu'aucun label n'existe.
  - Les seules estimations sont **statistiques** :
    - GLM de Poisson pour le nombre attendu de casernes ou d'écoles ;
    - modèle log-normal du « gap attendu » ;
    - mélange linéaire calibré sur le leaderboard.
  - Éventuellement, un petit LightGBM sur des **cibles intermédiaires internes**, par exemple le nombre de POI dans des secteurs où la carte semble complète. Tout cela tourne sur **CPU, en quelques secondes ou minutes**.
- **Machines :**
  - **Cette machine** (i7-10870H 8 cœurs / 16 threads, 16 Go de RAM, RTX 3060 Laptop 6 Go, 89 Go libres) **suffit**. Le goulot d'étranglement est l'agrégation spatiale avec DuckDB (CPU et disque), pas le GPU.
  - **La RTX 4090 n'est pas nécessaire.** Elle n'apporterait rien de mesurable, et un deep learning sans labels sur environ 9 800 lignes surapprendrait du bruit.
- **Pas de modèle pré-entraîné ni d'apprentissage from scratch.**
  - Une expression régulière sur `names.primary` (par exemple « Volunteer Fire Department ») suffit pour repérer les casernes mal classées.
  - Un modèle de NLP n'apporterait rien et compliquerait la reproductibilité exigée par la revue de code.

## 9. Recherche : ce qui est utile

- **Estimation de complétude sans référence :**
  - Barrington-Leigh & Millard-Ball (2017, *PLOS ONE*), méthode MRP sur les routes ;
  - Herfort et al. (2023, *Nature Communications*), modèle de complétude des bâtiments OSM et ses inégalités ;
  - travaux OST/osmcross (complétude des POI à partir d'indicateurs intrinsèques) ;
  - Kontur (densité de routes prédite par la population).
- **Qualité Overture et OSM :**
  - casernes US : environ 30 000 réelles contre environ 17 000 dans OSM en 2022 ;
  - POI Overture : couverture d'environ 72 %, comme OSM, sur un échantillon validé au Québec ;
  - `confidence` mesure une probabilité d'existence, pas la précision de localisation ;
  - empreintes Microsoft : les petits bâtiments sont moins bien détectés (Heris et al. 2020).
- **Leaderboard comme oracle :**
  - Blum & Hardt (2015), « The Ladder » : n'accepter une amélioration que si elle dépasse le bruit ;
  - Whitehill (2017), attaque par oracle : nous **n'utiliserons pas** de sondage au niveau du secteur.
- **Apprentissage à partir d'agrégats :** Zhang et al. (NeurIPS 2020), apprentissage à partir d'observations agrégées. C'est le cadre théorique de la régression à partir de moyennes de groupe.

Sources :
- [Herfort et al. 2023](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10326063/)
- [Barrington-Leigh & Millard-Ball 2017](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5552279/)
- [HeiGIT : complétude OSM avec Overture](https://heigit.org/?p=33507)
- [OST : complétude des POI par ML](https://eprints.ost.ch/940)
- [Kontur : complétude des routes](https://www.kontur.io/?p=7351)
- [OSM US : couverture des casernes](https://openstreetmap.us/news/2022/09/12months_Emergency_Preparedness/)
- [Wiki OSM : HIFLD Emergency](https://wiki.openstreetmap.org/wiki/HIFLD/Emergency)
- [Overture POI UK (arXiv 2310.18415)](https://arxiv.org/pdf/2310.18415)
- [Étude TRB POI Overture/OSM/Google](https://trid.trb.org/View/2713825)
- [Heris et al. 2020 (empreintes Microsoft)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7324622)
- [The Ladder (Blum & Hardt 2015)](https://arxiv.org/pdf/1502.04585)
- [Climbing a shaky ladder](https://arxiv.org/pdf/1706.02733)
- [Whitehill 2017](https://arxiv.org/pdf/1707.01825)
- [Attack RMSE Leaderboard](https://ar5iv.labs.arxiv.org/html/1802.04947)
- [Learning from Aggregate Observations](https://papers.nips.cc/paper_files/paper/2020/file/5b0fa0e4c041548bb6289e15d865a696-Paper.pdf)
- [État des bias bounties (arXiv 2510.02036)](https://arxiv.org/pdf/2510.02036)
- [CAL FIRE DINS](https://catalog.data.gov/dataset/cal-fire-damage-inspection-dins-data)
- [Heat Relief Network (MAG)](https://azmag.gov/Newsroom/MAG-News/heat-relief-network-map-provides-life-saving-information)
- [Maisons de retraite californiennes et feux (PreventionWeb)](https://www.preventionweb.net/news/are-california-nursing-homes-adequately-prepared-wildfire-related-emergencies)
- [Dépôt vigohan](https://github.com/vigohan95/zindi-bias-bounty)
- [Dépôt Teddythebotbuilder](https://github.com/teddywasserman/overture-coverage-equity)
- [README des données](https://data.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge/README.md)
- [Guide du Bias Score](https://zindi.world/learn/what-is-the-bias-score-a-guide-to-zindi-s-new-bias-scorecard)
