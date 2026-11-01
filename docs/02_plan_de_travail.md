# Plan de travail : Bias Bounty Mapping Equity Challenge

*Rédigé le 16 octobre 2026. Clôture le 31 octobre 2026. Ce plan repose sur [01_analyse_challenge.md](01_analyse_challenge.md).*

## 0. Objectifs, avec franchise

| Objectif | Cible réaliste | Remarque |
|---|---|---|
| **Classement principal** | **meilleur RMSE conforme** : < 0,0775 (meilleur score public conforme connu, vigohan), visé ≤ 0,072 | Les rangs 1 à 4 affichent un RMSE de **0**, obtenu en reconstruisant la cible avec les couches retirées. C'est **interdit** depuis le 28 septembre et il est presque certain que la revue de code du top 10 l'écartera. **Le seul moyen d'égaler 0 serait de tricher : je ne le ferai pas.** Notre vraie concurrence, ce sont les scores obtenus après le 2 octobre (≈ 0,0775 et moins). |
| **Best Bias Discovery** (1 000 $) | une découverte **nouvelle**, chiffrée et reproductible | Environ 55 candidatures existent déjà : la nouveauté est le critère décisif (voir la phase 4). |
| **Best Documentation** (500 $) | la documentation la plus claire et la plus reproductible | Pipeline en une commande, déterministe, avec un journal de soumissions vérifiable. |

Pour atteindre RMSE ≈ 0,072, il faut une corrélation ρ ≈ 0,59 avec la vérité (σ = 0,089) ; vigohan obtient 0,50. **Rien ne garantit la 1re place**, mais le plan maximise nos chances sans risquer de disqualification.

## 1. Principes non négociables

1. **Conformité.**
   - Le pipeline de scoring ne lit **que** : Overture (2026-08-19.0), ACS B25001, les tables de strates autorisées, les géométries de secteurs et la SampleSubmission.
   - Un **garde-fou dans le code** refuse tout chemin contenant `tiger`, `microsoft`, `msft-footprint`, `hifld`, `cbp`, `usfs_BuildingCount`, `usfs_HUCount` ou `carbonplan_buildings`.
   - Les données externes du Bias Discovery vivent dans `discovery/` et ne sont **jamais importées** par `src/`.
2. **Le leaderboard comme instrument, pas comme oracle.**
   - On s'en sert uniquement pour mesurer des **paramètres globaux** : moments de la cible, covariances des signaux, poids du mélange, 5 décalages régionaux. **≤ 20 paramètres au total.**
   - **Aucun sondage** au niveau du secteur ni de petits groupes.
   - Avant chaque soumission, on **pré-enregistre le RMSE attendu**. Une amélioration n'est acceptée que si elle dépasse le bruit (≥ 0,001), selon le principe du « Ladder ».
3. **Pas de données issues des autres participants.** On n'utilise ni leurs moyennes de groupe publiées ni le scorecard des lignes à RMSE 0 : on re-mesure tout nous-mêmes.
4. **Reproductibilité.**
   - Dépendances figées, seeds fixées, aucun appel réseau autre que le bucket public.
   - Hash SHA-256 de chaque CSV soumis.
   - Exécution complète depuis un environnement vierge **avant** la fin.
5. **Traçabilité.** Chaque décision est notée dans `docs/decisions.md` et chaque soumission dans `submissions/log.csv` (identifiant Zindi, fichier, SHA-256, RMSE prédit et obtenu, date).

## 2. Environnement et organisation

- **Machine :** cette machine (i7-10870H, 16 Go de RAM, RTX 3060 Laptop 6 Go, 89 Go libres) suffit. **Pas besoin de la RTX 4090** : il n'y a ni entraînement profond ni GPU nécessaire (justification dans la section 8 de l'analyse).
- **Python 3.13** dans un `.venv` local, avec des versions figées (`requirements.txt`) : duckdb (spatial, httpfs), pandas, pyarrow, numpy, scipy, statsmodels, scikit-learn, lightgbm, geopandas, matplotlib.
- **Données :** téléchargement local via `pip install awscli` puis `aws s3 sync --no-sign-request` (environ 6,2 Go), avec vérification des tailles d'octets par rapport au listing du bucket et `data/MANIFEST.sha256`.
- **Versionnage :** `git init` local. Un dépôt GitHub public (utile pour les jurys) n'est créé **qu'avec votre accord** (décision D3).

```
Bias_Challenge/
  docs/            analyse, plan, decisions.md, journal
  data/raw/        reference/ strata/ boundaries/   (ignoré par git)
  data/features/   features.parquet (9 794 lignes) + dictionnaire
  src/bbx/         config, io (garde-fou), features_*, components_*, montecarlo, leaderboard_algebra, blend, submit
  scripts/         run_all.ps1 / run_all.sh  (pipeline en une commande)
  tests/           tests unitaires (formule, axes CRS, GEOID, cas limites)
  submissions/     CSV + log.csv
  discovery/       analyse Bias Discovery (données externes isolées)
  writeup/         documentation.md -> PDF (≤ 10 Mo), figures/
```

## 3. Phases et calendrier

### Phase 0 : mise en place (ven. 16 oct., J0)

- Créer le `.venv`, installer et figer les dépendances, `git init`, créer la structure et le garde-fou de conformité.
- Télécharger `reference/`, `strata/` et `boundaries/`, puis vérifier les tailles.
- **Test d'axe CRS :** calculer la longueur d'un segment connu pour vérifier `always_xy` / `ST_FlipCoordinates`.
- **Soumissions S1-S3** (si vous les approuvez) :
  - S1 fichier tout à zéro ;
  - S2 constante 0,06 ;

  Ces deux soumissions donnent **m** et **σ** de la cible publique.
  - S3 : un prior issu des seules strates.
- **Livrable :** environnement reproductible, données vérifiées, m et σ mesurés par nous-mêmes.

### Phase 1 : table de features (sam. 17 oct., J1)

Calcul DuckDB par secteur, en jointure spatiale exacte sur les polygones des secteurs :

- **Routes :**
  - km par `class` ;
  - km portant une référence `routes` (US:I, US:US, route d'État, comté) ;
  - km de classes notées motorway / trunk / primary / secondary ;
  - part de km sans nom, part « ère de l'import » (`update_time` < 2012) ;
  - connectivité : composantes, impasses (utile aussi pour la piste A du Bias Discovery).
- **Bâtiments :** nombre total, nombre par source (OSM, Microsoft, Esri, USGS) et surface.
- **POI :**
  - comptes **exacts selon la taxonomie des organisateurs** (fire_department, ambulance_and_ems_services, 6 catégories d'écoles) ;
  - total des lieux ;
  - noms évoquant une caserne (« Fire », « VFD », « Fire Protection District ») **mal classés** ;
  - `confidence` moyenne, sources.
- **Strates :** population, surface terrestre, part urbaine, RUCA, terres tribales, SVI/CVI, risques, logements ACS.
- **Contrôles :** 9 794 lignes, GEOID en texte, aucun NaN non expliqué, totaux par région cohérents avec le README, tests unitaires réussis.
- **Soumissions :** S4-S8, des signaux simples (région, ruralité, absence de caserne Overture, densité de lieux, part Microsoft) pour mesurer leur covariance avec la vérité.

### Phase 2 : modèle structurel du score (dim. 18 → mer. 21 oct., J2-J5)

Idée : **reproduire exactement la formule des organisateurs**, en remplaçant chaque quantité de référence inconnue par une **distribution** estimée uniquement à partir des données autorisées. La prédiction est ensuite **l'espérance du score**, estimée par Monte-Carlo avec une seed fixe sur environ 2 000 tirages par secteur. C'est la prédiction optimale pour le RMSE sous ces hypothèses.

| Composante | Modèle de la référence inconnue | Paramètres |
|---|---|---|
| **Transport** | km TIGER S1100+S1200 ≈ log-normal autour des km portant une référence de route (Interstate, US, État, plus une fraction des routes de comté). « Non définie » quand ces km valent 0, avec une probabilité. | σ_T, poids des routes de comté, P(définie) |
| **Casernes** (composante principale) | Nombre réel H ~ Poisson(λ), avec λ = f(surface, population, ruralité, région) ajusté par un **GLM sur les secteurs où Overture semble complet** (urbains, cartographiés par OSM), plus un facteur u de stations absentes. Une caserne mal classée détectée par son nom relève fortement P(H ≥ 1 et O = 0). | coefficients du GLM (calculés en interne), u_fire |
| **Écoles / EMS** | même schéma (les EMS pèsent peu) | u_school, u_ems |
| **CBP** | établissements ≈ log-normal autour de k·population et de (lieux Overture)/ρ | k, ρ, σ_C |
| **Bâtiments** | empreintes Microsoft ≈ log-normal autour du nombre de bâtiments Overture d'origine Microsoft, ajusté selon la part OSM (sans les colonnes USFS ni CarbonPlan) | σ_B |
| **Composite** | appliquer la formule exacte à chaque tirage (moyenne des composantes définies, POI = moyenne de deux moitiés, HIFLD = moyenne des types définis), puis faire la moyenne | — |

- Chaque version du modèle et chaque composante isolée sont soumises **une seule fois**, avec un RMSE prédit. On en déduit leur corrélation implicite r_i avec la vérité.
- **Contrôles internes, sans labels :**
  - proportions de composantes non définies attendues par région, comparées aux chiffres publiés par les organisateurs (21 / 37 / 28 / 55 %) ;
  - ratios Overture / proxy de transport par région, comparés à la plage de 0,71 à 1,59 annoncée.
- **Soumissions :** environ 18 sur quatre jours.

### Phase 3 : assemblage et calibration (jeu. 22 → lun. 26 oct., J6-J10)

- **Algèbre du leaderboard.** Pour une soumission p, on a RMSE² = Var(p) + σ² − 2·Cov(p, y) + (p̄ − m)². Chaque soumission donne donc **Cov(s_i, y)** exactement, sur le sous-ensemble public.
- **Mélange optimal :** w = (Σ_ss + λI)⁻¹ Σ_sy. Il porte sur ≤ 15 signaux (composantes structurelles, région, strates), avec un ridge pour limiter le surapprentissage du public. L'optimisme estimé est d'environ 0,0002 de RMSE pour 15 paramètres et n ≈ 2 940, donc négligeable.
- **Calibration non linéaire légère :** mélange dans l'espace logit ou racine carrée, puis troncature à [0, 1]. Elle n'est retenue que si le gain prédit est confirmé.
- **Robustesse :** stabilité des poids par bootstrap, régions laissées de côté à tour de rôle, et sensibilité de chaque paramètre structurel.
- **Soumissions :** environ 22. Chacune est pré-enregistrée et acceptée selon le principe du Ladder.
- **Livrable :** 2 candidats finaux :
  - **F1**, le meilleur RMSE public conforme ;
  - **F2**, une version plus prudente (moins de paramètres, plus de régularisation) pour se protéger côté privé.

### Phase 4 : Best Bias Discovery (en parallèle, sam. 18 → lun. 26 oct.)

1. **Audit de nouveauté (J3).** Lire les environ 55 candidatures publiques et dresser un tableau « thème → déjà pris / partiellement / libre ».
2. **Faisabilité en une demi-journée par piste (J4-J5).** Chaque piste est notée selon la grille du jury : Impact 30 · Nouveauté 25 · Preuves 25 · Reproductibilité 20.
   - **A. Coupures de connectivité** : le réseau Overture est « assez long » mais cassé (segments manquants, impasses, communautés à une seule sortie). Une métrique de longueur ne voit pas ce que voit un calcul d'itinéraire d'évacuation. Le cœur repose sur les données du challenge ; une validation par échantillon est possible.
   - **B. Structures fantômes après incendie** : bâtiments détruits (Camp Fire / Paradise, North Complex, feux de l'est de Washington) toujours présents dans Overture, comparés aux données CAL FIRE DINS (open data). Conséquence : surestimation de la population à évacuer, mauvaise planification de l'aide.
   - **C. Refuges contre la chaleur invisibles** à Maricopa : les sites du Heat Relief Network sont-ils dans Overture, selon le SVI ? Le scorecard affiche une « chaleur 0,62× », ce qui laisse penser que la chaleur est bien couverte. À faire seulement si les données sont téléchargeables et sous licence ouverte.
   - **D. Établissements à évacuer en priorité** (maisons de retraite, centres de soins CMS) dans les zones de feu et de chaleur.
3. **Validation de la piste (fin J5).** On garde **une** piste principale, avec éventuellement une seconde courte en annexe.
4. **Analyse (J6-J9) :**
   - secteurs nommés ;
   - disparités chiffrées avec intervalles de bootstrap ;
   - régressions avec effets fixes par région ou comté ;
   - vérifications de robustesse ;
   - 2 à 3 figures ;
   - conséquences concrètes (secours, évacuation, aide), propres aux lieux étudiés.
5. **Rédaction (J9-J10)** : script `discovery/reproduce.py` en une commande, sources externes avec URL, date de récupération, licence et SHA-256.

### Phase 5 : Best Documentation (mer. 24 → mar. 27 oct.)

Le writeup reprend **point par point** ce que demande la page Info :
1. sources, avec URL, date, version Overture et SHA-256 ;
2. calcul de chaque composante (formules et code) ;
3. **cas limites** (population nulle, secteurs surtout en eau, secteurs sans données Overture, `ALAND = 0`, GEOID) : traitement et effectifs ;
4. **pondérations alternatives** testées, chacune avec son RMSE et la raison de son rejet ;
5. journal complet des soumissions, avec prédit contre observé ;
6. réflexion sur le Bias Scorecard de nos soumissions ;
7. annexe de conformité (ce qui n'a **jamais** été lu) ;
8. reproduction : `scripts/run_all` puis comparaison des SHA-256, plus le temps d'exécution et le matériel.

Le PDF de 10 Mo maximum est généré depuis le HTML (impression headless d'Edge). Un dépôt de code est joint si D3 est validée.

> **Mise à jour du 18/10.** Selon le formulaire d'envoi des deux prix spéciaux, les candidatures Best Bias Discovery et Best Documentation **ferment le mercredi 4 novembre 2026 à 23 h 59 GMT**. Le classement principal ferme toujours le 31 octobre.
> - Les deux documents pourront citer les 2 soumissions finales et le classement privé du 31 octobre.
> - À égalité, la candidature la plus ancienne gagne : je vise un envoi **le dimanche 1er novembre**, avec les lundi 2 et mardi 3 en marge de sécurité. Je n'attends pas le 4.

### Plan de fin de compétition (mis à jour le 21/10, « meilleur score possible »)

- **Plus aucun mélange soumis « pour voir »** : le score d'un mélange de signaux mesurés se prédit à environ 0,0002 près (s16 : 0,07797 prévu, 0,07820 obtenu).
- **Les envois servent uniquement à mesurer des directions nouvelles.** Au-delà des signaux mécanistes en file, on mesure les **composantes principales du résidu** (`src/bbx/residual_pcs.py`) de 431 indicateurs autorisés, une fois retiré ce que la base couvre déjà (59 % de la variance des indicateurs). Les 30 composantes en couvrent 62 % de plus, soit environ 84 % au total.
- Calendrier (listes `submissions/upload_<date>.txt`) :
  - 22/10 : s39 à s43 ;
  - 23/10 : s32, s35, s44, s45, rpc01 ;
  - 24/10 → 29/10 : rpc02 à rpc30 (limite portée à 66 signaux, décision D1-ter du 21/10).
- **30/10 : soumission des candidats finaux.** Mélange de tous les signaux mesurés avec la règle de formule, ridge 0,02 / 0,05 / 0,10. On sélectionne sur Zindi un candidat équilibré (ridge 0,05) et un plus prudent (0,10), et non celui qui maximise le public : le classement final porte sur les 70 % privés.
- **31/10 : réserve** (incident, reconnexion, nouvelle information du staff sur les colonnes USFS).

### Phase 6 : gel et remise (mer. 28 → sam. 31 oct. pour le classement ; formulaires d'ici le 1er nov., au plus tard le 4 nov. à 23 h 59 GMT)

- **Mer. 28 :** gel du code, réexécution complète depuis un `.venv` vierge, comparaison bit à bit avec les soumissions retenues.
- **Jeu. 29 :** **vous** envoyez les formulaires, Bias Discovery et Documentation (probablement deux envois). Je prépare les PDF et les textes. Envoyer tôt compte en cas d'égalité.
- **Ven. 30 :** sélection des **2 soumissions finales** (F1 et F2), toutes deux postérieures au 2 octobre.
- **Sam. 31 :** marge de sécurité, sans changement sauf incident.

## 4. Budget de soumissions (5 par jour, environ 73 disponibles)

| Usage | Nombre |
|---|---|
| Mesure des moments de la cible (m, σ) | 2 |
| Signaux simples et strates | 6 |
| Composantes et versions du modèle structurel | 18 |
| Mélanges, calibration, robustesse | 22 |
| Réserve (incidents, dernières vérifications) | 10 |
| **Total prévu** | **58** |

Chaque soumission est **un envoi de formulaire sur Zindi** : j'ai besoin de **votre accord explicite pour chaque envoi**, ou c'est vous qui envoyez le CSV que je prépare. Je fournirai à chaque fois le fichier, le RMSE prédit et la raison de l'envoi.

## 5. Risques et parades

| Risque | Parade |
|---|---|
| Le staff juge les colonnes USFS ou CarbonPlan, ou les attributs `routes`, non conformes | F1 sans colonnes USFS ni CarbonPlan ; garde-fou dans le code ; justification écrite dans l'annexe de conformité |
| Le classement privé n'est pas recalculé, et les scores de l'ancien calcul restent affichés | Hors de notre contrôle. On optimise le vrai RMSE et on choisit des finales postérieures au 2 octobre |
| Surapprentissage du public (30 %) | ≤ 20 paramètres, ridge, F2 prudente, Ladder |
| Erreurs silencieuses de CRS ou de GEOID | tests unitaires (segment de longueur connue, GEOID de Maricopa) |
| Manque de temps | phases parallèles ; le Bias Discovery a une validation fixée à J5 ; réserve de 10 soumissions |
| Formulaire Google (connexion requise, un seul prix par envoi) | deux envois ; PDF prêts le 28 |
| Revue de code du top 10 (48 h) | dépôt prêt dès le 28 : README, `run_all`, versions figées, données en une commande |

## 6. Décisions à valider (mes recommandations)

- **D1. Usage du leaderboard.** Calibration limitée à ≤ 20 paramètres globaux ou régionaux, sans sondage de petits groupes. *Recommandé.*
- **D2. Colonnes `usfs_BuildingCount_sum`, `usfs_HUCount_sum`, `carbonplan_buildings`.** Exclues de F1 et F2. *Recommandé* (le risque de disqualification l'emporte sur le gain).
- **D3. Dépôt GitHub public pour les jurys.** *Recommandé* (environ 20 % de la note de reproductibilité). Il faut votre compte et votre accord avant publication.
- **D4. Question au staff sur le Chat** (colonnes USFS, recalcul final). Optionnel : beaucoup l'ont déjà posée sans réponse. Je peux rédiger le message ; vous décidez de le publier.

## 7. Ce que je fais seul, et ce qui vous revient

- **Je fais :** tout le code, les données, les features, les modèles, l'algèbre du leaderboard, les analyses, les figures, la documentation, les PDF et les tests de reproduction.
- **Vous faites ou validez :**
  - chaque envoi de soumission (accord ou clic) ;
  - les formulaires Google (connexion à votre compte) ;
  - la publication du dépôt GitHub ou d'un message sur le Chat ;
  - le choix final des 2 soumissions (je recommande, vous confirmez).

## 8. Indicateurs de réussite

- J1 : table de features complète et tests réussis.
- J5 : modèle structurel avec ρ ≥ 0,40 (RMSE ≤ 0,0815).
- J10 : mélange avec ρ ≥ 0,55 (RMSE ≤ 0,0740), puis ≤ 0,072 visé.
- J10 : Bias Discovery rédigé, reproduit en une commande.
- J11 : documentation au format PDF ; J12 : reproduction bit à bit vérifiée.
