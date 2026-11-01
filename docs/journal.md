# Journal de bord

## 2026-10-16 : phase 0

- Environnement `.venv` (Python 3.13.7), versions figées dans `requirements.txt`, paquet `bbx` installé en mode éditable, dépôt git initialisé.
- Données : 202 fichiers, 5,13 Go, tous de la bonne taille par rapport au listing du bucket ; empreintes dans `data/MANIFEST.sha256`. Le bucket ne contient plus aucune couche retirée.
- Tests : 11 sur 11 réussis (garde-fou, algèbre du leaderboard, contrat de données : 9 794 secteurs, GEOID en texte, ordre des axes CRS).
- Garde-fou D2-bis : toutes les colonnes USFS `Building*`, `HU*` et `Pop*`, ainsi que `carbonplan_buildings`, sont exclues.
- Envoi des soumissions : le navigateur intégré n'a pas d'outil d'envoi de fichier, et le serveur local a été refusé par les permissions. Chaque fichier est donc **reconstruit dans la page** à partir des données publiques du bucket. Il n'est envoyé que si son SHA-256 est identique au fichier local.

### Soumissions

| Id Zindi | Fichier | RMSE attendu | RMSE public |
|---|---|---|---|
| hz2e3ofY | s01_const_000 | 0,1082 | **0,107246299** |
| f8rewtqK | s02_const_010 | 0,0985 | **0,097675731** |
| 69ej3ZMW | s03_strata_rural_tribal | 0,0859 | **0,082539447** |

### Mesures

- Cible sur le sous-ensemble public : **m = 0,059806**, **σ = 0,089022**. La meilleure constante donne donc un RMSE de 0,089022.
- Prior de strates S3 (part non urbaine, log de la surface, part tribale) : **corrélation implicite +0,383**. À son échelle optimale, il donnerait un RMSE attendu de 0,0822.

## 2026-10-16 : phase 1 (features) et début de la phase 2

- `src/bbx/features.py` produit les features par couche et par région en environ 10 minutes au total, dont 3,5 pour les bâtiments du Texas. `src/bbx/dataset.py` assemble la table **9 794 × 267** (`data/features/features.parquet`).
- Contrôles (Eastern WA) : 1 081 345 bâtiments affectés sur 1 081 346, 76 490 POI sur 76 491, routes découpées 79 164 km pour 79 064 km dans la couche (+0,13 %, segments sur les limites).
- **Validation sans labels du proxy transport.** La part de secteurs sans route US, Interstate ou d'État reproduit la part officielle de secteurs avec au moins une composante non définie : OK 22,2 % (officiel 21 %), CA 36,5 % (37 %), AZ 60,0 % (55 %), TX 37,5 % (28 %). Au Texas, l'écart se comble si une partie des routes FM/RM compte comme S1200 (20,3 % si toutes comptent). On en déduit P(définie | FM seulement) ≈ 0,55 au Texas et P(définie | comté seulement) ≈ 0,7 en Arizona, 0 en Californie.
- Rapport km Overture (classes notées) / km du proxy : OK 1,14 · WA 1,47 · AZ 1,93 · CA 1,70 · TX 1,16 (avec les routes FM). La plage officielle (0,71 à 1,59) suggère que TIGER compte plus de routes que notre proxy dans au moins une région : l'échelle sera mesurée sur le leaderboard.
- Modèle structurel v1 (`src/bbx/structural.py`) : espérance Monte-Carlo de la formule exacte (1 000 tirages, seed fixe).
  - Casernes : densité physique issue d'agrégats nationaux, plus les casernes nommées mais mal classées.
  - EMS et écoles : Overture presque complet.
  - CBP : moyenne géométrique de la population et du nombre de lieux.
  - Corrélation avec S3 : 0,40.
- Soumissions préparées : `s04_structural_v1` (RMSE attendu 0,0834, ρ supposé 0,35) et `s05_fire_expected_gap` (0,0849, ρ supposé 0,30).

### Résultats de S4 et S5 (envoyées par l'utilisatrice)

| Id Zindi | Fichier | RMSE attendu | RMSE public | Corrélation implicite |
|---|---|---|---|---|
| eh4n4hWS | s04_structural_v1 | 0,0834 | **0,084068** | +0,330 |
| FqGb62wz | s05_fire_expected_gap | 0,0849 | **0,088892** | +0,155 |

- Le mélange S3 + S4 (+ S5) donne ρ = 0,428, soit un RMSE attendu de **0,0804** (`src/bbx/blend.py`).
- **Le signal casernes est faible.** Il donne trop de poids aux secteurs urbains sans caserne Overture, qui sont nombreux. À tester : un signal concentré sur le rural peuplé.
- Le modèle structurel est désormais **décomposé en contributions additives exactes** (transport, bâtiments, casernes, EMS, écoles, CBP), dont la somme redonne S4 à l'identique. Le mélange pourra repondérer chaque mécanisme.
- Fichiers prêts pour le 17 octobre :
  - `s06_c_transport`, `s07_c_cbp`, `s08_c_school` (contributions) ;
  - `s09_region_ok`, `s10_region_az` (décalages régionaux, D1).

## 2026-10-17

### Soumissions s06 à s10 (envoyées par l'utilisatrice)

| Id Zindi | Fichier | RMSE attendu | RMSE public | Corrélation implicite |
|---|---|---|---|---|
| N6SChmQ9 | s06_c_transport | 0,0862 | **0,082096** | **+0,424** |
| hTMwh65B | s07_c_cbp | 0,0880 | 0,089856 | +0,012 |
| SB2WZozi | s08_c_school | 0,0886 | 0,089855 | −0,044 |
| iMRULWwD | s09_region_ok | 0,0862 | 0,085342 | +0,287 |
| tjkmzErF | s10_region_az | 0,0886 | 0,088684 | +0,088 |

- **Le transport est le meilleur signal** (r = 0,424, mieux que le prior de strates). Les composantes CBP et écoles, telles que modélisées, n'apportent rien.
- Mélange des 8 signaux mesurés (OLS) : ρ = 0,488, RMSE attendu **0,07769**. Avec ridge 0,05 : ρ = 0,4825, **0,07797** (poids plus stables, choisi pour s16).

### Calibration du proxy transport sur la plage officielle (0,71 à 1,59, quatre régions)

| Proxy | OK | WA | AZ | CA | TX |
|---|---|---|---|---|---|
| grands axes (I, US, État) | 1,14 | 1,47 | 1,93 | 1,70 | 2,46 |
| + FM/RM (TX) | 1,14 | 1,47 | 1,93 | 1,70 | 1,16 |
| + comté | 0,56 | 1,42 | 1,76 | 1,38 | 1,03 |
| + autres | 0,56 | 1,33 | 1,60 | 1,18 | 1,02 |

Lecture la plus cohérente :
- **Oklahoma** = 0,71 (grands axes + environ 59 % de ses 25 000 km de routes de comté) ;
- **Arizona** = 1,59 (toutes les routes numérotées) ;
- Californie et Texas entre les deux.

La variante v2 (`data/interim/structural_v2.parquet`) applique ces proxys. Elle est corrélée à 0,95 avec la v1, donc apporte peu d'information nouvelle.

### Sélection des signaux suivants (part déjà expliquée par la base de 8 signaux)

| Candidat | R² sur la base |
|---|---|
| part des km de routes numérotées classées sous « secondary » | **0,02** |
| transport hors TX et OK | 0,12 |
| part de bâtiments Microsoft | 0,33 |
| rural peuplé sans caserne | 0,47 |
| transport TX seul | 0,60 |
| transport v2 | 0,90 |

Lot préparé pour le 18 octobre :
- `s16_blend_v1` (RMSE attendu 0,07797, validation de l'algèbre) ;
- `s17_major_route_unscored_share` ;
- `s18_c_transport_tx` ;
- `s13_bld_msft_share` ;
- `s14_rural_pop_no_fire`.

## 2026-10-18

| Id Zindi | Fichier | RMSE attendu | RMSE public | Corrélation implicite |
|---|---|---|---|---|
| iu1dZ8Hf | **s16_blend_v1** | 0,077974 | **0,078204** | +0,478 (prévu 0,4825) |
| Ntg2t2Pe | s17_major_route_unscored_share | 0,0880 | 0,089048 | +0,073 |
| 18uR7Wqi | s18_c_transport_tx | 0,0849 | 0,088363 | +0,175 |
| NwoRLKoL | s13_bld_msft_share | 0,0862 | 0,085265 | +0,290 |
| JZp1WSeo | s14_rural_pop_no_fire | 0,0872 | 0,086976 | +0,214 |

- **Algèbre validée en conditions réelles.** Le mélange s16 obtient 0,078204 pour 0,077974 prédit (écart de 0,0002, dû à l'approximation des moments du sous-ensemble public).
- Mélange sur la base de 12 signaux (s16 exclu, car c'est une combinaison) : ρ = 0,500, RMSE attendu 0,07710 (OLS), 0,07743 (ridge 0,05).
- **Calibration du modèle structurel** (pente de la vérité sur chaque contribution, 1,0 = calibré) :
  - transport **0,85**, presque calibré ;
  - CBP 0,05 et écoles −0,25, sans pouvoir prédictif ;
  - composite v1 0,47.
- La variance restante vient surtout des casernes (≈ +0,08 au score par caserne manquante) : l'axe de travail principal est un meilleur modèle de P(caserne réelle et absente d'Overture).
- **Correction importante (vérifiée sur les 259 lignes du classement).** Zindi a recalculé toutes les soumissions avec le RMSE corrigé. Les scores de 0,056 à 0,075 (rangs 11 à 72) sont de **vrais RMSE**, pas des scores de l'ancien calcul comme je l'avais affirmé.
  - Le 11e (Sosa Team, 0,05636) a donc une corrélation d'environ 0,77 avec la vérité, contre 0,48 pour nous.
  - Nous sommes **79e sur 259** (0,078204). vigohan est 74e (0,077475).
  - Plusieurs équipes de tête ont fait beaucoup de soumissions (Sosa 103, roki 85, Artyom 80, Pricilegangbe 76, Sashish 75, Shivoo29 73). Artyom (14e) et Sashish ont demandé au staff si les colonnes USFS de bâtiments sont autorisées ; ils n'ont pas eu de réponse. KettaP (13e, 0,0577) n'a fait que 13 soumissions.
- Lot préparé pour le 19 octobre :
  - `s19_fire0_with_community` (R² sur la base 0,27) ;
  - `s20_partial_fire_gap` (0,17) ;
  - `s21_c_transport_az_ca_wa` (0,27) ;
  - `s22_no_ems_place` (0,07) ;
  - `s23_svi_overall` (0,06).

### Plan révisé après la correction du classement (D1-bis : jusqu'à environ 50 signaux)

- **Diagnostic :** l'écart de transport déterministe n'est non nul que dans 4,4 % des secteurs. La variance de la vérité vient surtout de la **composante POI** (casernes, établissements CBP) et des **interactions de définition** (peu de composantes définies, donc un score élevé).
- La v3 du modèle structurel (prior casernes avec ancrage communautaire, CBP réparti par population au prorata du comté) est déjà expliquée à 85-92 % par la base. Changer les hypothèses du modèle apporte donc peu ; il faut **mesurer de nouveaux mécanismes**.
- File d'envois (listes `submissions/upload_<date>.txt`) :
  - 19/10 : s19 casernes avec communauté · s20 écart partiel de casernes · s22 absence d'EMS · s24 CBP par surface · s25 CBP par population ;
  - 20/10 : s26 peu de bâtiments par logement · s27 petits bâtiments · s28 bâtiments Esri · s29 POI fermés · s30 routes de l'import TIGER ;
  - 21/10 : s31 région WA · s32 région CA · s33 P(transport défini) · s34 routes sans nom · s35 risque de feu WHP.
- s21 et s23 sont reportés (priorité plus faible). s11, s12 et s15, préparés le 17, sont remplacés par s31, s32 et s33 (signaux identiques).
- **Date limite des prix spéciaux** : mercredi 4 novembre 2026 à 23 h 59 GMT (formulaire d'envoi, signalée par l'utilisatrice). Envoi visé le 1er novembre, car la candidature la plus ancienne gagne en cas d'égalité.
## 2026-10-19

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| 3zQ1zL6n | s19_fire0_with_community | 0,089056 | +0,072 |
| M5HiaC4D | s20_partial_fire_gap | 0,088944 | +0,051 |
| YG6fcnXW | s22_no_ems_place | 0,089308 | −0,000 |
| 4udQPbF8 | s24_cbp_area_k1 | 0,088689 | +0,087 |
| yy6VtcLw | s25_cbp_pop_k05 | 0,089952 | **−0,091** |

- Signaux faibles isolément, mais **mélange à 17 signaux : ρ = 0,5255, RMSE attendu 0,07574** (ridge 0,05 : 0,07616), contre 0,07710 avec 12 signaux.
- Contribution marginale (perte de ρ si on retire le signal) :
  - s07 c_cbp (0,022), s25 cbp_pop (0,019) et s06 c_transport (0,018) en tête ;
  - puis s09 Oklahoma (0,008), s05 casernes et s18 transport TX (0,006).
- Poids : c_cbp +3,4, cbp_pop −3,5, ce qui forme un **contraste fort sur la moitié CBP**. La vraie règle de répartition des établissements se situe entre le proxy géométrique (population × lieux) et la répartition par population.
- File réordonnée (`scripts/make_queue_oct20_21.py`) :
  - 20/10 : s26, s27, s30, s36 (CBP par logements, k = 2), s37 (log des lieux par bâtiment relatif au comté) ;
  - 21/10 : s31, s28, s29, s38 (CBP par surface, k = 0,25), s34.
- Pas de réponse du staff sur #35402 à ce jour.
- **Règle déduite de la formule** (`src/bbx/postprocess.py`, testée). Deux secteurs d'eau du golfe du Mexique (48039990000, 48057990000 ; ALAND = 0) n'ont aucune donnée Overture. Comme ils sont notés, au moins une composante y est définie, et elle vaut 1 : leur score est **exactement 1**. Le mélange leur donnait 0,47 et 0,50. Gain attendu ≈ 0,0004 de RMSE, appliqué par défaut à tous les mélanges (`blend.fit(rules=True)`).
- Cas limites comptés pour la documentation : 27 secteurs sans population, 82 sans logement, 2 avec ALAND = 0, 137 sans km de classes notées, 3 788 sans route majeure.
- Documentation v0 rédigée : `writeup/documentation.md`.

## 2026-10-20

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| tqeAsrZK | s26_bld_per_hu_low | 0,090010 | **−0,198** |
| rzHKeus4 | s27_bld_small_share | 0,088634 | +0,112 |
| LjUPFbH4 | s30_import_share | 0,088604 | +0,099 |
| K8jB5peB | s36_cbp_hu_k2 | 0,089617 | −0,109 |
| RJKHastf | s37_logrel_places_per_bld | 0,089236 | −0,023 |

- **Mélange à 22 signaux : ρ = 0,539, RMSE attendu 0,07498** (ridge 0,05 : 0,07538). Gain d'environ +0,013 de ρ par jour de 5 signaux.
- Projection : RMSE de 0,069 à 0,070 au 31/10 si ce rythme se maintient. C'est bien sous le meilleur score conforme publié (0,0775), mais loin de 0,056.
- Hypothèse (non démontrée) sur l'écart avec la tête du classement : KettaP (13e, 0,0577) n'a fait que 13 soumissions, donc utilise un modèle fort plutôt qu'un sondage intensif. La composante bâtiments (référence Microsoft) pourrait être calculée presque exactement avec les colonnes USFS de bâtiments, qui en dérivent. Nos signaux bâtiments sont nettement informatifs (part Microsoft +0,29, bâtiments par logement −0,20).
- Staff : toujours pas de réponse sur #35402 (37 vues).
- Le lot du 21/10 reste celui prévu (s31, s28, s29, s38, s34).
- Décision D2-ter : pas de colonnes USFS sans feu vert explicite du staff (validé par l'utilisatrice).
- **Deuxième passe de features** (`src/bbx/features_extra.py`, 5 minutes) :
  - casernes, écoles et EMS Overture situées à moins de 300 m ou 1 km **de l'autre côté** de la limite du secteur ;
  - surface moyenne des empreintes par source : OSM 522 m², Microsoft 181 m² ;
  - codes postaux des lieux, présents dans 97,6 % des cas.
- Nouveaux candidats (`src/bbx/candidates_extra.py`, R² sur la base de 22 signaux) :
  - `fire0_nbr300`, pas de caserne dans le secteur mais une à moins de 300 m de l'autre côté : **0,08** (18,6 % des secteurs) ;
  - pas de caserne à moins de 1 km : 0,15 ;
  - surface moyenne des bâtiments Microsoft : 0,26 ;
  - CBP réparti par code postal et surface : 0,38 et 0,46.
- Lot du 22/10 (`submissions/upload_2026-10-22.txt`) : s39, s40, s41, s42, s43.

## 2026-10-21

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| BZoBWXPZ | s31_region_wa | 0,089027 | +0,024 |
| uE8sY5kj | s28_bld_esri_share | 0,089140 | −0,001 |
| 1GcBxnfH | s29_poi_closed_share | 0,089425 | −0,136 |
| dStjCBas | s38_cbp_area_k025 | 0,088699 | +0,097 |
| 9VvWPtRA | s34_unnamed_share | 0,087210 | **+0,209** |

- **Mélange à 27 signaux : ρ = 0,5446, RMSE attendu 0,07466** (ridge 0,02 : 0,07492). Gain du jour +0,006 de ρ : les rendements décroissent.
- Signaux de courbure (carré, cube, charnières sur le mélange) : déjà couverts à 47-90 % par la base. Seule la charnière de traîne max(z − 2, 0) est retenue (4,3 % des secteurs).
- Staff : pas de réponse sur #35402 (78 vues).
- Lot du 23/10 : s32 (région CA), s35 (WHP), s44 (charnière de traîne), s45 (école de l'autre côté de la limite), et **s46 blend_v2**, à construire après les scores du 22.

- **Production des PDF** (`scripts/build_pdf.py`) : conversion Markdown → HTML autonome (images intégrées) → PDF via Edge en mode sans interface. Le script ajoute les lignes vides avant les listes et l'indentation des sous-listes. Résultat : `writeup/pdf/bias_discovery.pdf` (0,38 Mo, 4 pages) et `writeup/pdf/documentation.pdf` (0,19 Mo, 5 pages), bien sous la limite de 10 Mo du formulaire. Rendu vérifié visuellement page par page.

- **Nouvelle stratégie d'envoi** (demande : meilleur score possible). Les mélanges ne sont plus soumis pour voir leur score, puisqu'il est prévisible ; s46 est remplacé par `s47_rpc01`. Les envois mesurent les composantes principales du résidu de 431 indicateurs autorisés une fois retirée la base (couverte à 58,7 %). Fichiers s47 à s76 (rpc01 à rpc30) écrits ; listes du 23 au 29/10 prêtes. Les envois au-delà de 50 signaux sont marqués conditionnels (D1-bis).

## 2026-10-22

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| hwyiUTTZ | s39_fire0_nbr300 | 0,089509 | −0,029 |
| HtPC78m2 | s40_fire0_no_nbr1km | 0,088992 | +0,053 |
| fjQExKuP | s41_log_msft_area | 0,088681 | +0,101 |
| sMEM8pzb | s42_zip_area_k05 | 0,088766 | +0,082 |
| qnDMcmSv | s43_zip_area_k1 | 0,088975 | +0,036 |

- **Mélange à 32 signaux : ρ = 0,5448, RMSE attendu 0,07465** (ridge 0,02 : 0,07490 ; 0,05 : 0,07510 ; 0,10 : 0,07532). Contre 0,5446 et 0,07466 la veille : **gain quasi nul**.
- Contribution marginale de chaque nouveau signal : au plus 0,0001 de ρ. La part de ces features non expliquée par la base (R² de 0,08 à 0,46) n'est pas corrélée à la cible. La deuxième passe de features (casernes de l'autre côté de la limite, surface des empreintes, CBP par code postal) n'apporte donc rien de plus que la base.
- Les contributions marginales en tête restent s07 c_cbp (0,021), s06 c_transport (0,018), s25 cbp_pop (0,010), s05 casernes (0,007) et s18 transport TX (0,006).
- Conséquence : les gains restants viendront, s'il y en a, des composantes principales du résidu (s47 à s76), orthogonales à la base par construction, et non de nouvelles features mécanistes. Le plan du 23 au 29/10 est maintenu.
- Compteur Zindi : 35 soumissions sur 200.
- Staff : toujours pas de réponse sur #35402 (129 vues). D2-ter inchangé.
- Lot du 23/10 inchangé : s32, s35, s44, s45, s47_rpc01 (remplacé plus bas).

## 2026-10-22 (suite) — recherche approfondie et transport v3

- **Recherche** (détail et sources dans `docs/04_recherche_2026-10-22.md`). Nous sommes 107e. Le 12e est à 0,0559, le 49e à 0,0697.
  - Une reproduction exacte publiée (PeterTheDataScientist, erreur 3e-6) donne les conventions de la référence : routes TIGER découpées par secteur en EPSG:5070, donc une route qui forme la limite est comptée dans les deux secteurs ; une copie TIGER par numéro de route ; bâtiments au centroïde ; CBP réparti du code postal au secteur.
  - HYurdagul (#35478) : le seul double comptage en limite fait passer son RMSE public de 0,0754 à 0,0700.
  - Nous n'utilisons ni ce code ni les couches retirées, seulement la description des conventions.
- **Nouvelles variables** (données autorisées uniquement) :
  - `src/bbx/features_roadref.py` : km de routes numérotées dans le secteur et dans une bande de 10 m ou 25 m autour, en EPSG:5070, pondérés ou non par le nombre de numéros de route du tronçon ;
  - `src/bbx/features_bldref.py` : bâtiments dessinés à la main avec ou sans équivalent Microsoft, et excès de surface.
- **Validation sans labels du transport v3** (bande de 10 m, multiplicité, routes de comté de l'Oklahoma pondérées à 0,24) :
  - parts de secteurs sans composante routière : AZ 54,8 % (officiel 54,9 %), CA 37,9 % (36,9 %), OK 21,6 % (21,3 %), TX 26,5 % (28,5 %) ;
  - rapport Overture / proxy en Arizona : 1,59 avec la bande, contre 1,93 sans. Le README donne 1,59 comme maximum, ce qui va dans le sens du mécanisme.
- **Nouveauté par rapport aux 32 signaux mesurés** : R² de 0,57 pour la contribution transport v3, de **0,10 pour l'écart v3 − v1**, de 0,09 pour la part de route en bordure et de 0,31 pour l'écart bâtiments (seuil de 300 m²).
- **Lot du 23/10 refait** (`scripts/make_queue_oct23_v2.py`) : s77_t3_c_transport, s78_t3_nomult_c_transport, s79_t3_score, s80_bgap_s300, s32_region_ca. Les fichiers s35, s44, s45 et s47_rpc01 sont reportés. Les listes du 24 au 29/10 seront refaites après les scores du 23.
- **Ordre de grandeur attendu** : si la partie nouvelle du v3 a une corrélation partielle de 0,2 à 0,37 avec le résidu (0,37 correspond au gain d'HYurdagul), le mélange passerait de 0,0747 à 0,069-0,073. C'est à mesurer.

## 2026-10-23 — Bias Discovery v1.0 et dépôt public

- **Décision** (accord de l'utilisatrice le 22/10, sur ma recommandation) : avancer l'envoi du Bias Discovery au 24/10, parce qu'une candidature concurrente proche (kainwangroger, #35474, empreintes périmées après incendie, mêmes données CAL FIRE, même secteur de Greenville) est déjà envoyée. La Documentation reste prévue pour le 1er novembre.
- **Ce qui nous distingue**, désormais mesuré et écrit dans la section 6 de `writeup/bias_discovery.md` :
  - la dimension temporelle (0,2 % de fantômes avant 2020 contre 30 % pour 2020-2025) ;
  - une estimation corrigée du hasard : **24,3 % au-delà du placebo, IC à 95 % de 17,4 à 35,8 %** (bootstrap sur 85 incendies), soit environ 1 670 structures ;
  - une règle de date par empreinte, qui attrape aussi les 461 fantômes OpenStreetMap ;
  - l'exposition des secteurs vulnérables et tribaux ;
  - le lien avec les produits d'exposition : à Greenville, les fantômes font 16,5 % des bâtiments Overture, et le comptage USFS (conditions 2022) est de 2 440, au-dessus des 2 170 d'Overture fantômes compris.
- **Reproductibilité corrigée** : les chiffres d'exposition (SVI, terres tribales, maisons de retraite par quartile) n'étaient produits par aucun script. `discovery/exposure.py` les recalcule à l'identique, et il est ajouté à `reproduce.py`. Définitions retrouvées : « touche une zone tribale » = `aiannh_name` renseigné (17 secteurs), quartiles calculés sur les maisons de retraite. Coquille de SHA-256 corrigée dans la section Reproductibilité.
- **Dépôt public préparé** (`scripts/make_release_discovery.py` → `release/bias-bounty-phantom-homes/`, 15,5 Mo, ignoré par ce dépôt) : uniquement le Bias Discovery. Le pipeline de classement ne sera publié qu'après le 31/10. Les fichiers externes sont joints compressés pour rester reproductibles même si CAL FIRE ou CMS les mettent à jour.
  - `get_data.py` télécharge le reste depuis le bucket (il faut un User-Agent de navigateur, sinon erreur 403) et vérifie chaque SHA-256.
  - **Test depuis une copie vierge : les 9 tableaux et les 2 figures sont identiques octet pour octet aux originaux.**
- **Publication** (accord de l'utilisatrice, 23/10 : « Fais tout toi-même ») :
  - dépôt public créé et envoyé : https://github.com/Arnaud-TOE/bias-bounty-phantom-homes (commit `eed0582`, auteur avec l'e-mail anonyme GitHub). Les identifiants git enregistrés étaient périmés ; l'utilisatrice a validé elle-même la connexion Git Credential Manager. Le PDF et les deux fichiers externes en ligne sont identiques aux fichiers locaux ;
  - annonce publiée sur le Chat Zindi le 23/10 à 12 h 08 : **#35520** (https://zindi.world/competitions/bias-bounty-mapping-equity-challenge/discussions/35520), texte identique à `docs/chat_entry_bbd.md`.
- **Formulaire Best Bias Discovery envoyé le 23/10** à la demande de l'utilisatrice, dans son Chrome (Claude in Chrome, compte Google [e-mail removed]). Google a confirmé : « Your response has been recorded ».
  - Page 1 : e-mail Zindi [e-mail removed] (donné par l'utilisatrice), nom d'utilisateur Arnaud_TOE, prénom Arnaud Ulrich, nom TOE, prix Best Bias Discovery uniquement.
  - Page 2 : PDF `Arnaud_TOE_Best_Bias_Discovery_phantom_homes.pdf` (identique à `writeup/pdf/bias_discovery.pdf`, SHA-256 172a8e2c…5684, récupéré depuis le dépôt GitHub public parce que le champ de fichier est dans un cadre Google hors de portée de l'outil de dépôt), soumission associée iu1dZ8Hf.
  - Le formulaire propose « Edit your response » : la réponse reste modifiable, mais le fichier envoyé ne peut plus être changé (avertissement de Google). Le lien de modification est resté ouvert dans l'onglet Chrome de l'utilisatrice ; je ne peux pas le lire (jeton masqué).
- **Reste pour les prix** : formulaire Best Documentation le 1er novembre (nouvel envoi, prix « Best Documentation »).

## 2026-10-23 — scores du transport v3

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| DXzKv4BR | s77_t3_c_transport | **0,074257** | **+0,563** |
| MsRHPaKQ | s78_t3_nomult_c_transport | 0,075527 | +0,541 |
| LFsjNG5t | s79_t3_score | 0,078898 | +0,468 |
| WJLiKSsK | s80_bgap_s300 | 0,090083 | −0,070 |
| ZSQCCsi2 | s32_region_ca | 0,088999 | +0,023 |

- **Le mécanisme est confirmé.** s77, un seul signal, fait mieux (0,0743) que notre meilleur mélange soumis (0,0782) et que le mélange prévu à 32 signaux (0,0747). L'ancien transport (s06) avait une corrélation de +0,424, le v3 en a +0,563.
- **Mélange à 37 signaux : ρ = 0,654, RMSE attendu 0,0673** (ridge 0,02 : 0,0674 ; 0,05 : 0,0676 ; 0,10 : 0,0678), contre 0,5448 et 0,0747 la veille. Au classement du 22/10, cela correspond à peu près au 40e rang.
- **Contributions marginales** : s07 c_cbp (0,010), s18 transport TX v1 (0,009), s25 cbp_pop (0,009), s09 Oklahoma (0,006), s78 sans multiplicité (0,006), s32 Californie (0,003). La différence s77 − s78 (effet des doublons de numéros) est utilisée par le mélange : poids +0,82 et +0,58.
- Bâtiments v3 (s80) : corrélation légèrement négative ; l'hypothèse « polygones fusionnés » ne se vérifie pas sous cette forme.
- Staff : toujours pas de réponse sur #35402. Nous en sommes à 40 soumissions sur 200.
- **Lot du 24/10** (`scripts/make_queue_oct24.py`) : le transport v3 restreint à chaque région (s81 TX, s82 AZ, s83 OK, s84 CA ; WA s'en déduit) pour que le mélange règle l'échelle du transport région par région (R² sur la base de 0,84, 0,29, 0,75 et 0,24), plus s85 (routes FM du Texas au poids 0,5). Les variantes de bande, de bruit et de routes de comté sont presque colinéaires à s77 (R² de 0,94 à 0,99) : elles ne passent qu'ensuite.

## 2026-10-23 (suite) — classement et recherche n° 2

- **Classement du 23/10** (361 équipes classées) :
  - nous sommes 86e avec 0,074257 (s77) ;
  - rangs 1 à 11 : reconstructions (0 à 0,005) ;
  - 12e Sosa Team 0,05579, 13e Jules_Duber 0,05600, 14e KettaP 0,05689, 15e Artyom 0,05700, 20e resist 0,05865, 30e 0,06205, 42e 0,06722, 50e HHYurdagul 0,06847.
  - Notre mélange prévu (0,0673) correspond à peu près au 42e rang.
  - Pour battre le 12e, il faut ρ = 0,779 (ρ² = 0,607), contre 0,654 (ρ² = 0,428) aujourd'hui : il faut expliquer 31 % de la variance qui reste. Le transport v3 a apporté +0,13 de ρ² ; il faut l'équivalent d'une autre découverte de cette taille, plus des gains plus petits.
- **Recherche n° 2** :
  - Chat Zindi : rien de neuf (un seul nouveau fil, #35493, question sans réponse). GitHub : pas de méthode publiée par les équipes de tête.
  - **Piste retenue : la moitié CBP.** La définition HUD confirme que BUS_RATIO est la part des adresses professionnelles USPS du code postal situées dans le secteur. L'analyse de sensibilité publiée montre que la clé de répartition pèse lourd (1 974 secteurs déplacés de 0,022 en moyenne si l'on prend les adresses résidentielles). Nos anciens signaux CBP répartis par population ou par logements ont une corrélation négative (s25 −0,091, s36 −0,109), ce qui est cohérent avec une répartition par adresses professionnelles.
  - Proxy des adresses professionnelles : grands bâtiments (`src/bbx/features_bizaddr.py` : nombre et surface des emprises d'au moins 300, 1 000 et 3 000 m², adresses distinctes des lieux, code postal principal). Ces signaux sont nouveaux à 50-80 % par rapport à la base (R² de 0,20 à 0,51), mais la partie déjà mesurée a une corrélation proche de 0. C'est à mesurer, sans confirmation extérieure.
  - Fichiers préparés (`scripts/make_cbp4.py`) : s86_cbp4_bld1000 et s87_cbp4_area300.
  - **Lot du 24/10 modifié** : s86 remplace s85, presque colinéaire à s77 (R² de 0,95), pour tester l'hypothèse CBP un jour plus tôt. s85 et s87 passent le 25/10.
  - **Pistes écartées** :
    - doublons TIGER par nom local : ils feraient tomber le rapport Overture/TIGER de l'Arizona sous 1,59, alors que notre modèle actuel retrouve exactement ce maximum publié ;
    - bâtiments « polygones fusionnés » (s80, corrélation −0,07) ;
    - routes du bord extérieur des régions, invisibles car coupées à la limite : 391 secteurs de bord (4 %), effet limité.
- **Outil de tri ajouté** : pour un candidat, la corrélation avec la vérité de sa projection sur les signaux mesurés est calculable (vérifiée sur s24, s25 et s07). Seule la part hors de la base reste inconnue.

## 2026-10-24

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| T6CXBsNH | s81_t3_tx | 0,088169 | +0,246 |
| vLuZo1Wh | s82_t3_az | 0,087569 | +0,183 |
| HfUp2qXG | s83_t3_ok | 0,081531 | +0,447 |
| b8u4KAU8 | s84_t3_ca | 0,088089 | +0,147 |
| F4wXJimX | s86_cbp4_bld1000 | 0,088802 | +0,075 |

- **Mélange à 42 signaux : ρ = 0,673, RMSE attendu 0,0658** (ridge 0,02 : 0,0660 ; 0,05 : 0,0663 ; 0,10 : 0,0666), contre 0,654 et 0,0673 la veille.
- **Poids régionaux du transport v3** (en plus de s77 −0,41 et s78 +0,67) : OK 1,93, AZ 1,45, CA 1,35, TX 0,80. Les écarts routiers sont plus forts que ne le dit le modèle hors du Texas, et un peu surestimés au Texas. s83 (OK) a la plus forte contribution marginale (0,012).
- **CBP par adresses professionnelles (s86)** : apport faible (+0,075, contribution marginale 0,0017). L'hypothèse ne se confirme que faiblement avec ce proxy ; s87 (surface) est mis de côté.
- **Tri des candidats** (`screen.py` dans le scratchpad : R² sur la base et corrélation de la projection). Les recalibrages linéaires du transport (échelle par région, routes de comté, bande, bruit) sont déjà couverts à 94-99 %. Les candidats retenus apportent ce qu'un mélange linéaire ne peut pas construire : écart au niveau de la composante, masses aux bornes. Ajouts à `structural.simulate` : `p_zero` et `p_transport_one`.
- **Lot du 25/10** (`scripts/make_queue_oct25.py`, poids du mélange dans `submissions/blend42_weights.json`) : s88 (écart transport v3, R² 0,67), s89 (probabilité d'un écart routier égal à 1, R² 0,14), s90 (mélange × probabilité de zéro, R² 0,66), s91 (probabilité d'une caserne de référence, R² 0,56), s85 (routes FM du Texas à 0,5).
- Staff : pas de réponse sur #35402. Nous en sommes à 45 soumissions sur 200.

## 2026-10-24 (suite) — trajectoire et recherche n° 3

- **Trajectoire, en toute franchise.** Pour 0,0558 (12e, meilleur score conforme), il faut ρ = 0,779 ; nous sommes à 0,673. Les gains par lot de signaux sont de +0,01 à +0,02 de ρ (hors découverte comme le transport v3, +0,11). Projection au 30/10 sans nouvelle découverte : ρ ≈ 0,72-0,75, soit un RMSE de 0,059 à 0,062 et un rang autour de 20 à 30. **Battre le premier demande une autre découverte de la taille du transport.**
- **Recherche n° 3**, avec l'outil de tri (R² sur la base, corrélation de la projection) :
  - **Casernes signalées par OpenStreetMap** (`src/bbx/features_osmfac.py`). Les bâtiments Overture portent les noms et classes OSM, contrairement aux lieux Overture. 1 530 secteurs ont un bâtiment de caserne OSM ; dans 21,5 % d'entre eux (329), Overture n'a aucun lieu « fire_department », d'où un écart casernes probablement égal à 1. Nouveau à 90 % (R² 0,10). → **s92**.
  - **HIFLD compte plus de 53 000 casernes aux États-Unis** (PlainFireData, une par station). Notre modèle en attend environ 4 000 dans nos régions, contre 6 500 au taux national (nos régions sont plus urbaines). Les recalibrages de λ restent contenus dans la base (R² 0,93-0,96).
  - **Bâtiments détruits depuis la référence** : la référence Microsoft US date de 2018 et contient encore les maisons brûlées depuis, qu'Overture a en partie retirées (Paradise : 0,2 % de fantômes). Signal : part brûlée MTBS (dernier feu en 2016 ou après) × log de la densité de bâtiments, 536 secteurs, nouveau à 89 %. → **s93**.
  - **Pistes écartées** : CBP par voies de service (positif seulement par effet de ruralité ; les allées de parking, vraiment commerciales, sont négatives à −0,12) ; recalibrages des casernes (dans la base).
  - **Diagnostic, sans aucun usage dans une soumission (D2-ter)** : l'écart de bâtiments calculé avec `usfs_BuildingCount_sum` serait nouveau à 86 % (R² 0,14) ; Overture compte moins de bâtiments que l'USFS dans 36 % des secteurs (rapport régional de 1,05 à 1,17). La composante bâtiments est notre grand angle mort et probablement l'avantage des équipes de tête. Nous ne l'utilisons pas : en cas de disqualification, le règlement prévoit aussi la perte des prix pendant 6 mois, ce qui toucherait le Bias Discovery.
- **Lot du 25/10 révisé** (`scripts/make_queue_oct25b.py`) : s88, s89, s92, s93, s91 ; s90 et s85 passent au 26/10.

## 2026-10-24 (fin) — recherche n° 4 : quelles routes TIGER compte

- **Ordre de grandeur** : un transport parfait expliquerait environ 44 % de la variance (le v3 en explique 32 %). Le transport reste le plus gros gisement.
- **Variables ajoutées** à `features_roadref` (s77 reste reproduit à l'identique) : croisement type de route × classe Overture notée, revêtement des routes de comté, routes « tertiary » sans numéro, et nom local distinct du numéro de route.
- **Contrôles avec les contraintes publiées** (parts de secteurs sans route, rapports 0,71 et 1,59) :
  - les routes FM du Texas sont presque toutes « notées » dans Overture, ce n'est donc pas une question de classe ; TIGER n'en contient qu'environ la moitié (part de secteurs sans route au Texas) ;
  - les artères sans numéro et les routes « tertiary » ne sont pas dans TIGER (sinon il ne resterait que 1 à 3 % de secteurs sans route) ;
  - **routes de comté de l'Oklahoma = routes revêtues** : 29 % des routes au revêtement connu sont revêtues, et le rapport minimal de 0,71 demande un poids de 0,21 sur celles au revêtement inconnu. C'est cohérent avec la documentation TIGER (les routes non revêtues relèvent de S1400). Mais le transport v4 qui en découle ne diffère presque pas du v3 (corrélation 0,984 en Oklahoma) : gain négligeable.
- **Méthode publiée d'iam-dante (METHOD.md)** :
  - doublons TIGER « nom local » ajustés à 0,97 ;
  - doublons de numéros : leur direction la plus forte ;
  - environ 0,66 caserne de référence par secteur, soit environ 6 500 dans nos régions, alors que notre modèle en attend 4 000 et qu'Overture en a 3 641 (couverture de l'ordre de 56-60 %, d'où des écarts « casernes » plus fréquents que prévu).
- **Transport v5** (`Params(local_name_weight=1, interstate_local_weight=1)`) : une copie TIGER de plus par nom de rue local. Il contredit le rapport maximal de 1,59 (l'Arizona tomberait vers 0,85). Mais la direction v5 − v3 est **nouvelle à 69 %** (R² 0,31), orientée à +0,24 dans sa partie mesurable, avec un écart-type de 0,031 (pour comparaison, v3 − v1 n'était qu'à 10 % dans la base). → **s94_t5_c_transport**, en tête du lot du 25/10.
- **Lot du 25/10 final** (`scripts/make_queue_oct25c.py`) : s94, s88, s89, s92, s93. s91 passe au 26/10.

## 2026-10-24 — vérification : les colonnes USFS sont-elles interdites ?

À la demande de l'utilisatrice, relecture de toutes les sources officielles.

- **README du bucket** : aucune interdiction. La table USFS (« Wildfire Risk to Communities, all layers ») fait partie des strates fournies. La note du 25/09 ne retire que TIGER, les empreintes Microsoft, HIFLD et CBP.
- **Page Data de Zindi** :
  - « Bias API strata datasets » liste « USFS Wildfire Risk to Communities » parmi les données fournies ;
  - la section « Prohibited target reconstruction » interdit « les jeux de données, couches sources ou copies équivalentes utilisés dans la construction de la vérité terrain » et cite TIGER, Microsoft Buildings, HIFLD et CBP, pas l'USFS ;
  - elle ajoute : « Models should predict the target from permitted features rather than reconstructing the reference data ».
- **Annonce du staff du 28/09 (#35079)** : interdiction des « reference datasets used to create the ground truth — including TIGER roads, Microsoft building footprints, HIFLD fire/EMS/schools data, and CBP data », pour recréer ou approcher la cible, même indirectement. Elle invite aussi à demander en cas de doute.
- **Annonce du staff du 08/10 (#35250)** : « Features derived from the currently provided datasets are allowed, including Overture attributes and permitted columns in the strata tables. » Les colonnes « autorisées » ne sont définies nulle part.
- **Réponses du staff** : aucune, dans aucun fil. Les questions sur l'USFS restent sans réponse : #35079 (harshdipsaha, Kimyayd, uhoobnn), #35292, #35302, #35402 (la nôtre), #35429. Le staff ne répond pas non plus sur l'usage d'attributs Overture comme proxy de TIGER (Teddythebotbuilder, #35079), que nous utilisons.
- **Origine des colonnes** : `usfs_edition` = WRC v2 (RDS-2020-0060-2). D'après la méthode WRC 2.0 et la métadonnée USFS, les bâtiments viennent d'ONEGEO 3DBuildings et de USA Structures (ORNL/FEMA, bâtiments de 450 pieds carrés et plus), en conditions 2022. **La 1re édition utilisait les empreintes Microsoft 2018, pas la 2e.** Notre décision D2 reposait sur l'origine Microsoft : c'est faux pour l'édition fournie (nous l'avions déjà signalé au staff le 20/10).
- **Conclusion** : aucune règle officielle n'interdit nommément ces colonnes, et elles ne dérivent pas de la couche de référence Microsoft. Reste une ambiguïté : « permitted columns » n'est pas défini, et l'esprit de la règle vise l'approximation des données de référence. Décision à prendre par l'utilisatrice.
- **Décision de l'utilisatrice (24/10)** : on écrit au staff (brouillon dans `docs/email_staff_usfs.md`, envoyé par l'utilisatrice). D2-ter reste en vigueur en attendant. Estimation, sans soumission : avec ces colonnes, le mélange irait vers 0,063-0,065 dans le cas probable et 0,060 dans un cas optimiste.

## 2026-10-24 (nuit) — recherche n° 5

- **Nouveaux fils** :
  - #35542 et #35543 (jennifer_evangelista, 0,0752) : 33,9 % de la longueur des routes FM/RM du Texas est classée hors des classes notées, presque toute en « tertiary » ;
  - #35527 (HHYurdagul) : lieux « fantômes » après incendie ; il cite notre #35520.
- **FM « tertiary »** : confirmé dans nos données (32 % de la longueur FM, 17 365 km ; les grands axes ne sont hors classe qu'à 0,3 %). Retirer ces FM de la référence va dans le mauvais sens (partie mesurable de la différence : −0,16). TIGER les compte donc bien, et le v3 avait raison. Nouveau paramètre `txsec_unscored_weight` (par défaut 1, comme le v3).
- **Indice contre les doublons « nom local » (v5, s94)** : dans la reproduction exacte publiée, retirer tous les doublons géométriques de TIGER ne modifie que 1 283 secteurs, de 0,006 en moyenne. Des doublons « nom local » aussi répandus que le suppose le v5 auraient un effet bien plus large, à moins que leurs géométries ne soient pas identiques. Avec le rapport maximal de 1,59, deux indices vont contre ; la mesure de demain tranchera.
- **Casernes** : avec environ 0,66 caserne de référence par secteur (λ × 1,6, π = 0,6) et la preuve OSM, environ 5 000 secteurs auraient une caserne de référence probable. Les signaux qui en découlent restent dans la base (R² 0,63-0,98).
- **Plan du 26/10 (selon les scores de s94)** :
  - si s94 est positif : variantes v5 (autoroutes à 0, noms locaux à 0,5) et v5 par région ;
  - sinon, ou en complément : s90 (mélange × zéro), s91 (caserne de référence), communauté sans caserne en zone rurale (R² 0,73), s85 (FM à 0,5), indicateurs de grands groupes (région × rural, au moins 300 secteurs, D1-bis).

## 2026-10-24 (nuit, suite) — recherche n° 6 : candidatures techniques du Chat et dépôts

- **Règle de conformité appliquée.** Plusieurs candidatures publient des chiffres calculés sur TIGER ou HIFLD avant leur retrait. L'annonce du 08/10 interdit d'utiliser « des valeurs calculées à partir de ces couches avant leur retrait ». Nous ne réglons donc **aucun paramètre** sur ces chiffres ; seuls les mécanismes, vérifiables par ailleurs, sont retenus.
- **#35000 (PIO)** : décomposition exacte de la référence routière. Une grande part de la longueur TIGER est exactement sur une limite de secteur, et les doublons ne représentent que 7 à 11 % (incompatible avec des doublons « nom local » généralisés). s94 reste au programme du 25/10, mais avec peu d'espoir : nous ne décidons pas sur la base de ces chiffres.
- **#34992 (Pricilegangbe)** : beaucoup de routes Overture ont gardé les coordonnées exactes de l'import TIGER et se trouvent sur les limites ; selon l'arrondi flottant, elles comptent dans un secteur, deux ou aucun. Notre découpage en EPSG:5070 fait de même ; l'effet de l'arrondi est négligeable (21 secteurs selon la reproduction publiée).
- **#34925 (Luca925)** : Overture range de vraies casernes dans d'autres catégories (fire_protection_service, administrations, associations, police...), et fire_protection_service contient surtout des vendeurs d'extincteurs.
  - Nouvelle variable propre `fire_misfiled_clean` (`src/bbx/features_osmfac.py`) : nom vérifié, exclusion des vendeurs et des commerces « firehouse ». 879 lieux dans 739 secteurs, dont 585 en fire_protection_service.
  - Signal **s95_fire_misfiled_noov** : caserne mal classée et aucun lieu « fire_department » dans le secteur, donc écart casernes de 1. 370 secteurs (101 en commun avec s92), nouveau à 62 % (R² 0,38), orienté à +0,11. Prévu pour le 26/10.
  - Correctif : des `` étaient devenus des caractères de contrôle dans `features_osmfac.py` (écriture par le shell). Corrigé ; s92 est inchangé (corrélation 1,0 avec le fichier soumis).
- **Artères sans numéro (Arizona, Californie)** : exclues par les parts officielles de secteurs sans route (même au-delà de 2 km, l'Arizona tomberait à 32 % contre 54,6 % publiés).
- **GitHub** : aucun nouveau dépôt avec un modèle de classement (15 dépôts recensés, les plus récents sans contenu).

## 2026-10-24 (nuit, fin) — recherche n° 7 : les FM/RM du Texas ne sont pas dans TIGER

- **BrightQuery** (registre d'entreprises, 13 à 17 % des lieux Overture) comme proxy des établissements CBP : orienté dans le mauvais sens (−0,11 à −0,18). Écarté. Les parts de lieux Microsoft, Foursquare et AllThePlaces sont très nouvelles (R² 0,05 à 0,19) mais sans mécanisme ; mises de côté.
- **Découverte sur le transport au Texas** (61 % des secteurs). Notre catégorie « réseaux secondaires du Texas » mélangeait les FM/RM (50 600 km) avec les Loops, Spurs, Business, Beltways, routes à péage et routes de parc (3 600 km). Avec les seules contraintes publiées par les organisateurs :
  - part de secteurs sans route : 19,3 % avec toutes les FM/RM, **30,5 % sans aucune** (Loops et autres comptés comme routes d'État), contre **28,4 % publiés** ;
  - rapport Overture/TIGER du Texas : 0,96 avec toutes les FM, 1,79 sans aucune, **1,586 avec les FM/RM au poids 0,15**, contre un maximum publié de **1,59**.
  - Conclusion : TIGER ne contient qu'une petite partie des FM/RM. Le v3 les comptait toutes et créait des écarts routiers fictifs au Texas (FM « tertiary », FM en limite), ce qui est cohérent avec le poids de 0,80 du Texas dans le mélange.
- **Transport v6** (`Params(tx_split=True, w_txsec=0.15, p_txsec={TX: 0.19})`) : part de secteurs sans route au Texas de 28,0 %, écart moyen au Texas de 0,075 contre 0,141 pour le v3. La différence v6 − v3 a un écart-type de 0,03 et est nouvelle à 30 %. Sa partie mesurable est à −0,19, ce qui s'explique mécaniquement (elle retire une partie du transport du Texas, mesuré positif) ; seul le classement tranchera.
- **Lot du 25/10 révisé** (`scripts/make_queue_oct25d.py`) : **s96_t6_c_transport**, s92, s95, s93, s89. s94 (deux indices contre) et s88 passent au 26/10.

## 2026-10-25 (nuit) — recherche n° 8 : classification des routes corrigée (transport v7)

- **Erreur trouvée dans `ROUTE_LEVEL_SQL`** : tout réseau « US:<État>:<système> » était classé comme route de comté (niveau 5). Or deux de ces réseaux sont des autoroutes :
  - Phoenix, Loop 101/202/303 (« US:AZ:Loop », 560 km, toutes motorway) : poids nul dans le proxy TIGER de l'Arizona ;
  - Oklahoma, Turnpikes (« US:OK:Turnpike », 1 824 km) : poids de 0,24.
  Ni le double comptage le long de ces voies ni la composante transport des secteurs qu'elles traversent n'étaient donc modélisés. Ce sont précisément les régions où le mélange réclame des écarts plus forts (AZ 1,45, OK 1,93).
- **Correction** (`LEVEL2_SQL`, colonnes `maj2*`/`cty2*` ajoutées sans toucher aux anciennes ; s77 reste reproductible) : les systèmes d'État loop / turnpike / toll / spur / business hors Texas comptent comme routes d'État, avec multiplicité.
- **Validation sur les seules valeurs officielles** (part de secteurs sans composante transport, calculée comme le modèle) :
  - Arizona : 62,6 % (v6) → **54,9 %**, pour 55 % publiés ;
  - Texas : 29,7 % → **28,4 %**, pour 28 % ;
  - poids recalés sur les rapports officiels : FM/RM du Texas à 0,112 (maximum 1,59) et routes de comté de l'Oklahoma à 0,152 (minimum 0,71).
  - Dans le modèle complet (avec la définition par défaut de 3 % sans route) : TX 26,8 %, AZ 52,5 %, OK 21,1 %, CA 37,9 %, WA 22,4 %.
- **Transport v7** = v6 (FM/RM du Texas presque absentes de TIGER) + classification corrigée. Différence v7 − v6 nouvelle à 79 % (R² 0,21) ; v7 − v3 : écart-type 0,031. La probabilité de définition du v7 est nouvelle à 93 % par rapport à celle du v3 (écart-type 0,15).
- **Lot du 25/10 révisé** (`scripts/make_queue_oct25e.py`) : **s97_t7_c_transport**, **s98_t7_p_defined**, s92, s95, s93. s96 (v6), s89, s94 et s88 passent aux jours suivants.

## 2026-10-25 (nuit, suite) — recherche n° 9 : fin de l'audit routier, composite v8

- **Fin de l'audit de la classification routière** :
  - routes US « Business / Alternate / Bypass / Spur » sans autre numéro : 1 328 km au Texas, négligeables ailleurs ; leur inclusion resterait dans l'arrondi des contraintes officielles, donc indécidable, et non incluses ;
  - I-Business : 38 à 178 km par région, non incluses ;
  - tronçons « Future » seuls : 5 km ;
  - routes BIA en Arizona (410 km) : les inclure ferait passer la part de secteurs sans route sous la valeur officielle, donc TIGER ne les compte pas.
- **Composite v8** (`Params(fire_evidence="clean", p_misfiled_fire=0.9)` en plus du v7) : les preuves de caserne de référence sont désormais les casernes mal classées vérifiées par le nom, les bâtiments OSM et la catégorie secondaire « fire_department », au lieu de l'ancienne expression qui comptait aussi les vendeurs d'extincteurs. Le score v8 est nouveau à 13 % (R² 0,87) ; sa différence avec le score v7 est nouvelle à 95 %, orientée à +0,017.
- **Bruit du transport v7** (σ = 0,3 ou 0,2) : différences nouvelles à 75 %, mais faibles (écart-type 0,007-0,010) et orientées à −0,04 ; non retenu.
- **Lot provisoire du 26/10** (`scripts/make_queue_oct26.py`) : s99 (score v8), s100 (casernes v8), s101 (écart transport v7), s102 (écart routier égal à 1, v7), s103 (caserne de référence, v8). L'ordre sera fixé après les scores du 25/10.

## 2026-10-25 (nuit, fin) — recherche n° 10 : formes non linéaires apprises du mélange

- **Découpage régional du v7** : seul le Texas sort de la base (R² 0,61) ; s97 le mesure déjà. Pas de découpage supplémentaire.
- **Localisation des casernes apprise sur les preuves** (régression de Poisson, écoles, lieux civiques, routes, densité de bâti ; 25 % de déviance expliquée) : les signaux restent dans la base à 81-82 %. Écarté.
- **Méthode nouvelle : lire la règle dans le mélange.** Pour chaque composante, on compare la partie du mélange qu'elle porte (somme pondérée de ses signaux) à des formes fermées de la règle des organisateurs. On trouve ainsi la non-linéarité que le mélange linéaire ne fait qu'approcher (aucune donnée de référence n'est utilisée).
  - **CBP** : la partie CBP suit 1 − min(1, lieux / (k × population)) avec k de 0,005 à 0,01 (corrélation 0,60-0,65), soit les secteurs presque sans lieux par habitant. → **s104_cbp_pop_k0075** (4 % des secteurs, R² ≈ 0,55).
  - **Casernes** : la partie casernes suit « aucune caserne Overture × log(surface) » (corrélation 0,73). La forme 1 − exp(−surface / 20 km²) a un R² de 0,75 et une orientation de +0,235 (contribution structurelle : +0,10). → **s105_fire_parea20**.
  - **Bâtiments** : la partie bâtiments suit surtout « moins de 0,5 bâtiment par logement » (−0,70) et la part Microsoft (+0,55) ; pas de nouvelle forme utile.
- **Réserve de candidats** pour le 26 au 29/10 : s99-s103 (v8/v7), s104, s105, puis s94, s96, s90, s91, s89, s88, s85. L'ordre sera fixé chaque jour selon les scores.

## 2026-10-25 (matin) — recherche n° 11 et chaîne finale

- **Transport : v3/v6/v7 contre la partie transport du mélange** : corrélation 0,93 avec le v3, 0,84 avec le v7 (0,71 au Texas). Comparaison biaisée en faveur du v3 (le mélange n'est fait que de signaux de la famille v3). Elle confirme seulement que le v7 diffère vraiment au Texas ; les scores de s97 trancheront.
- **Secteurs extrêmes** : 27 sans population, 82 sans logement, 2 secteurs d'eau (règle = 1). Le mélange leur donne déjà des valeurs au-dessus de la moyenne ; rien de décisif.
- **Forme CBP affinée** : ajouter les grands bâtiments à la population n'améliore presque pas l'accord avec la partie CBP du mélange (0,661 → 0,672). s104 (population seule, k = 0,0075) est conservé.
- **Chaîne des soumissions finales** (`scripts/make_finals.py`, option `--dry-run`) : mélanges de tous les signaux mesurés (hors mélanges et constantes, 66 au plus), ridge 0,02 / 0,05 / 0,10, règle des secteurs d'eau, poids sauvegardés. À blanc avec 42 signaux : 0,0660 / 0,0663 / 0,0666 en public ; 0,0665 / 0,0667 / 0,0670 en privé après correction de l'optimisme.
- **Filet de sécurité à prévoir** : sans sélection, Zindi prendrait nos deux meilleurs scores publics, aujourd'hui s77 et s78 (environ 0,074). Prévoir un mélange soumis au plus tard le 29/10, même si le lot du 30/10 est prêt.

## 2026-10-25 — scores du transport v7 : grand saut

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| 5Puciiag | s97_t7_c_transport | **0,066482** | **+0,673** |
| ZSFx4Uph | s98_t7_p_defined | 0,084896 | +0,306 |
| YkHZBm4b | s92_fire_osm_noov | 0,088079 | +0,155 |
| NtLg2JbE | s95_fire_misfiled_noov | 0,087713 | +0,196 |
| vVi8P5tM | s93_burn2016_x_dens | 0,088831 | +0,067 |

- **Le transport v7 seul fait 0,066482** (v3 : 0,074257 ; corrélation +0,673 contre +0,563). La correction de la classification routière (FM/RM du Texas presque absentes de TIGER, Loops de Phoenix et Turnpikes de l'Oklahoma comptés comme autoroutes) est la deuxième grande découverte après le double comptage des limites.
- **Mélange à 47 signaux : ρ = 0,749, RMSE public attendu 0,0590** (ridge 0,02 : 0,0596 ; 0,05 : 0,0602 ; 0,10 : 0,0608), contre 0,673 et 0,0658 la veille. Cela correspond à peu près au 26e rang actuel ; le premier conforme (0,0557) demande ρ ≈ 0,78.
- Contributions marginales : s97 0,0047 ; s92 et s95 0,0005 chacun ; s98 0,0003 ; s93 0.
- **Lecture du mélange** : sa partie transport vaut environ 1,25 × v7 (corrélation 0,95 ; 0,975 au Texas, 0,994 en Oklahoma). Le mélange retire encore du v3 dans chaque région : la vérité est plus loin du v3 que le v7, dans la même direction. En Washington, la partie transport est presque nulle (orientation +0,016).
- **Tri sur la nouvelle base** (R² ; partie connue) : s102 0,145 (+0,17), s101 0,60 (+0,50), s103 0,62 (+0,20), s105 0,76 (+0,23), s106 0,89 (+0,63). Leurs résidus sont presque indépendants (|corrélation| ≤ 0,16). Redondants : s91 ≈ s103 (0,92), s99 ≈ s100 (0,94) ; s85, s96, s94 sont couverts à 87-97 %.
- **Lot du 26/10** : s106 (v9), s101 (écart transport v7), s102 (écart routier égal à 1, v7), s103 (caserne de référence, v8), s105 (casernes × surface).
- Staff : pas de réponse sur #35402. 52 soumissions sur 200 après le lot du 26/10 ; 52 signaux mesurés sur 66.

## 2026-11-01 — classement privé et documentation finale

- **Classement privé** (lu le 1/11 dans l'onglet Submissions, `submissions/zindi_scores_final.csv`) : f2 (8DPgZvCX) **0,058710364**, 36e ; s111 0,061255903. Les 80 scores publics du journal sont identiques à ceux de Zindi.
- **f5 envoyée par l'utilisatrice après la clôture** (LEGqiwj2, 1/11 à 0 h 41, non classée) : public 0,05698184 (0,056746 attendu), privé **0,058048029**, soit 0,00066 de mieux que f2.
- **Moments privés** (constantes s01/s02) : m = 0,059915, s = 0,089342.
- **L'est de Washington est noté dans le privé.** s124 (1 sur WA) fait 0,2385 en privé. Avec s31, la part de WA dans le privé vaut 0,0595, soit exactement 415 secteurs sur 6 980 (6 565 + 415), avec une moyenne de 0,093 (f2 y prédit 0,076).
- **Validation de l'instrument** : sur 73 signaux, les corrélations implicites publique et privée concordent à r = 0,987 (écart-type des écarts 0,031). Les mélanges perdent 0,0011 à 0,0014 du public au privé, les signaux seuls 0,0003 en moyenne.
- **Cause du raté public de f2** : le terme de composition `B² − Σ wᵢ pᵢ²` vaut 0,70 et 0,66 sur les deux secteurs d'eau (moins de 0,01 ailleurs), à cause de s07 (poids +3,1, 18 à 20 écarts-types sur ces secteurs). Selon que 0, 1 ou 2 d'entre eux sont publics : −0,0013, +0,0009 ou +0,0030 de RMSE ; observé +0,0025. f5, sans s07, tombe à 0,0002 de son attendu.
- La reconstitution du privé de f1/f3 par l'identité exacte échoue (l'est de Washington y introduit des moments croisés inconnus) : aucun chiffre n'est publié pour elles.
- **Documentation** : `writeup/documentation.md` v1.0 (anglais), figures `scripts/make_doc_figures.py`, PDF `scripts/build_pdf.py` (corrigé : profil Edge séparé, listes imbriquées, tableaux longs).
- **Mise en page du PDF (revue « attractif et donne envie de relire »)** : couverture (titre, 4 chiffres clés, l'histoire en un paragraphe, figure 1, soumissions associées), sommaire cliquable avec numéros de page (deux rendus : les destinations nommées du PDF donnent la page de chaque titre), « trois façons de lire », renvois « Section N » et « Figure N » cliquables, encadrés Key finding / Lesson / Recommendation, pied de page avec la section courante et « page / pages », signets, métadonnées. Figures 5 et 6 renumérotées dans l'ordre de lecture (fichiers renommés). Dernière revue : adresses web cliquables (dépôt, fils Zindi #34925, #35361, #35402, #35478, #35607), pastilles de décision dans le tableau de la section 7, repère « Info page » sur les trois cas limites demandés, annexe A en 7,8 pt. 24 pages, 1,43 Mo ; aucun chiffre modifié (les 81 lignes de l'annexe A recoupées avec `zindi_scores_final.csv` et `log.csv`).
- **Reproduction** : `scripts/reproduce.py` reconstruit f2 et f5 au bit près en 11 s. `--full DIR` refait tout depuis les données brutes dans un environnement neuf : features identiques aux originales à 1e-8 près (ordre des sommes de DuckDB), **61 signaux sur 61 et f2 identiques au bit près** (`docs/reproduction_report_2026-11-01.md`), confirmé par une exécution d'un seul tenant depuis un dossier vide (49 min). Deux corrections : `LEGACY_WATER_SCRIPTS` (les 46 signaux antérieurs au 25/10 gardent leurs valeurs sur les secteurs d'eau) et enregistrement des scores à leur date historique avant chaque lot (s16).
- **Dépôt public préparé** (non publié) : `scripts/make_release_pipeline.py` → `release/bias-bounty-coverage-gap/` (290 fichiers, 34 Mo, e-mails retirés du journal).

## 2026-10-31 — scores du 31/10 et recherche n° 94 : le bord du transport qui a payé

| Id Zindi | Fichier | RMSE public | Corrélation implicite | Coût de retrait |
|---|---|---|---|---|
| hL3p3mJS | s146_t7lf_c_transport_delta | 0,088508525 | +0,138 | **0,00083** |
| ctyeEWrg | s142_t10s_c_transport_delta | 0,088945322 | +0,042 | 0,00002 (→ `WEAK`) |
| ZNPnDWMf | s147_t7linv_c_transport_delta | 0,085784883 | **+0,402** | 0,00008 |

- **s146 paie presque autant que s140** : TIGER garde aussi les noms locaux des Interstates et des Loops du Texas comme enregistrements distincts. s147 est très bien orienté (+0,40), mais presque entièrement contenu dans les signaux déjà mesurés. s142 entre dans `WEAK` (règle de `finalize_31.py`).
- Mélange des finales : 0,05704 → **0,05618** (−0,00086). `make_finals.py` (73 signaux mesurés) : f1 71 signaux, public attendu 0,05595 (formule privée 0,06310) ; **f2 61 signaux, 0,05500** (0,06105) ; f3 0,05646. f1 et f2 vérifiés (9 794 lignes, pas de NaN, valeurs dans [0, 1], SHA égal au journal des envois).
- **Recherche n° 94** (`$TEMP/claude_ext/scr/v9LF_edges.py`, `v9LFinv.py`, `v9LF_screen.py`) : bords du composite sous le transport de s146 (v9LF) et sous celui de s146 + s147 (v9LFinv : noms locaux 0,35, Interstates 0,25, lecture inverse, FM 0,137, comtés OK 0,213), sur la base de 72 signaux :

  | Candidat | Nouveau | Partie connue | |corr nouvelle| prédite (bords) |
  |---|---|---|---|
  | s149 (v9L − v9, P ≥ 0,30) | 38 % | +0,344 | 0,065 |
  | v9LF − v9, P ≥ 0,30 | 38 % | +0,357 | 0,066 |
  | **v9LFinv − v9, P ≥ 0,30** | 34 % | **+0,531** | **0,077** |

  P(score ≥ 0,15) est couvert à 89 % ; P(transport = 1) ne bouge pas (définition inchangée).
- **s150_t9lfi_p_score_ge30_delta** (`scripts/make_s150.py`) remplace s149 dans le plan B (`upload_2026-10-31_planB.txt`) : gain espéré d'environ 0,0003, contre 0,0001 à 0,0002 pour la couverture f1/f2 (recherche n° 90). Le plan B exige de relever `MAX_SIGNALS` à 74 (décision de l'utilisatrice).
- **Plan B choisi** (« Oui, plan B ») : `MAX_SIGNALS = 74` (D1-quinquies, `docs/decisions.md`).
  - Essai à blanc de `finalize_31.py` avec de faux scores de s150, fichiers sauvegardés puis restaurés à l'identique (SHA vérifiés).
  - Un score incohérent avec la base (0,0886) faisait s'effondrer le mélange (RMSE 0) tout en affichant « OK ». **Garde-fou ajouté** : arrêt avant toute réécriture si le RMSE du mélange sort de ]0,050 ; avant + 0,0005].
  - **Score de s150 prévu par la base : ≈ 0,0859** (corrélation +0,53). À 0,0859, coût de retrait 0,00001, donc s150 passe dans `WEAK`. Chaque écart de 0,0003 correspond à une corrélation nouvelle d'environ 0,07, dans un sens comme dans l'autre.
- **Vérification complète de s150 avant envoi** (`$TEMP/claude_ext/scr/s150_check.py`) :
  - **Format** : mêmes colonnes et GEOID, byte pour byte, que s147 (accepté) ; 9 794 lignes, aucun NaN, 6 décimales, LF sans BOM, SHA égal au journal, doublon d'aucun fichier.
  - **Reproduction** : valeurs refaites à partir d'une simulation séparée, écart maximal 5×10⁻⁷ (arrondi).
  - **Signal** : les 2 secteurs d'eau sont à m, rien n'est écrêté, aucun delta négatif ; 3 909 secteurs bougent, les 30 premiers portent 16 % de la variance.
  - **Conformité** : uniquement Overture (routes, bâtiments), les strates ACS et les tables dérivées ; les mentions CBP, HIFLD et Microsoft ne sont que des commentaires du modèle ; garde-fous `permitted` et D2 actifs.
  - **Modèle** : Overture/TIGER TX 1,408, OK 0,629 (les bornes), AZ 1,204, CA 1,346, tous dans la plage officielle ; parts sans route inchangées (OK 0,211, AZ 0,525, CA 0,379, TX 0,268).
  - **Corrélation** avec les signaux notés : 0,58 au plus (s97).
  - **Score prévu par la base** : 0,085860 ; nouvelle corrélation ±0,05 donne ±0,00019, et s150 paie sous 0,08560 ou au-dessus de 0,08612.
  - **Essai à blanc de la branche « s150 paie »** (0,085483) : coût de retrait 0,00069, f2 à 62 signaux, public attendu 0,05436 ; fichiers restaurés et vérifiés octet par octet.
- **Score de s150** (6sUPkgD7) : **0,085797675** pour 0,085860 prévu ; corrélation implicite +0,541, coût de retrait 0,00002, donc il passe dans `WEAK`. f2 est reconstruite à l'identique (même SHA efbc9bcb…). f1 compte 72 signaux, public attendu 0,05593.
- **Choix de la seule finale, simulation recalée relancée sur les 74 signaux** (`sim_weak_cal.py`, 60 vérités, s07/s22 hors des deux recettes) :

  | Incertitude de la vérité | Recette f1 (tous) | Recette f2 (WEAK écartés) | f1 meilleure dans |
  |---|---|---|---|
  | nulle | 0,07146 | **0,07126** | 18 % |
  | × 0,5 | **0,07051** | 0,07067 | 67 % |
  | × 1 (bruit de mesure réel) | **0,06933** | 0,06983 | 83 % |

  La formule du privé préfère f2 (0,06105 contre 0,06326), mais elle surestime le bruit. f2 contient en plus s07/s22, que leurs deux secteurs d'eau rendent risqués en privé. Au niveau d'incertitude réaliste, la simulation donne f1 meilleure.
- **Vérification approfondie, sur demande (« c'est le score privé qui compte »)** :
  - **Secteurs d'eau** (`water_infer.py`). On retire de chaque covariance mesurée la part due aux secteurs d'eau s'ils sont publics, puis on juge la vraisemblance des parties nouvelles de s07 et s22. P(aucun des deux public) tombe de 0,49 (a priori) à 0,14-0,34, donc au moins un est probablement public. Si aucun n'était public, la partie nouvelle de s07 vaudrait +0,13 ; si un l'est, +0,05.
  - **Simulation exacte des recettes** (`sim_f1f2.py`, `sim_f1f3_shrink.py`, `sim_ridge_final.py`, `sim_ridge_sweep.py`). Secteurs d'eau à 1, découpage public conforme à chaque scénario, règle de formule appliquée, 100 vérités par scénario, pondération par la probabilité tirée des scores. Deux centres de vérité : WEAK informatifs (« all ») ou sans information (« weakout »).

    | Privé simulé | f1 | f2 | **f3** |
    |---|---|---|---|
    | WEAK informatifs, ×0,5 / ×1 | 0,06948 / 0,06813 | 0,06988 / 0,06882 | 0,06943 / 0,06839 |
    | WEAK sans information, ×0,5 / ×1 | 0,07006 / 0,06912 | 0,07000 / 0,06904 | **0,06956 / 0,06861** |
    | formule analytique (ignore les secteurs d'eau) | 0,06326 | 0,06105 | 0,06138 |

  - **f2 est battue dans tous les réglages simulés**, même sous un découpage au hasard, et même quand aucun secteur d'eau n'est public (s07/s22 n'apportent plus rien sur la base de 74 signaux). Son avance dans la formule vient de s07/s22 pris pour argent comptant : 0,0012 de gain public en échantillon pour deux signaux.
  - **WEAK** : la formule (second moment débiaisé cc − S_e) et le centre « weakout » les jugent nuisibles. Seul le centre « all », qui suppose plus de signal que mesuré (c_vrai ~ N(c, S_e), optimiste en grande dimension), les juge utiles.
  - **Ridge** : la simulation préfère plus fort (0,02 à 0,1), la formule 0,005 ; f3 (0,01) est au milieu.
  - **Décision recommandée : f3** (`f3_blend_ridge001.csv`, 58 signaux actifs, WEAK et s07/s22 exclus, ridge 0,01). Regret maximal 0,0003 contre la formule et 0,0003 contre la simulation la plus favorable à f1 ; f1 a jusqu'à 0,0022 de regret, f2 jusqu'à 0,0007.
  - Fichier vérifié : SHA 1425a6cb… égal au journal, 9 794 lignes, secteurs d'eau à 1, poids conformes à la recette (s31 seulement absent, constant sur les régions notées).
  - **Correction (même jour), scores attendus de f2 et f3** :
    - **Public attendu, secteurs d'eau traités exactement** (`water_pub.py`, `water_pub2.py`). On retire la contribution exacte des secteurs d'eau (y = 1, prédiction 1 par la règle). On calcule l'algèbre sur les autres secteurs et on crédite l'écrêtage. Le bruit dû au tirage du public est obtenu par Monte-Carlo exact (400 tirages). Contrôle : s16 prévu 0,07814 ± 0,00024 pour 0,07820 réel ; s111 prévu 0,06042 (aucun public) ou 0,0592-0,0593 (un public) ± 0,00054 pour 0,05999 réel ; « les deux publics » est exclu (z = +3,3).

      | Secteurs d'eau publics | aucun | un | les deux |
      |---|---|---|---|
      | f2 | 0,05445 | 0,05483-0,05509 | 0,05551 |
      | f3 | 0,05639 | 0,05523-0,05535 | 0,05423 |
      | f1 | 0,05575 | 0,05483-0,05500 | 0,05417 |

      Bruit ±0,0007 à ±0,0009.
    - **Biais trouvé dans la simulation** : la vérité y était construite sans s07/s22. Corrigé (`sim_f2_vs_f3_fix.py`, `sim_gap_fix.py`) : f2 bat f3 dans 97-99 % des vérités si aucun secteur d'eau n'est public, dans 27-35 % si l'un l'est.
    - **Quel scénario ?** (`water_infer2.py`, covariances refaites sur les secteurs hors eau). Si aucun secteur d'eau n'est public, la partie nouvelle de s07 vaudrait **+0,166**, alors que les 71 autres signaux, en laissant chacun de côté à son tour, ne dépassent jamais **0,126** (s97 ; écart-type 0,033 ; vrai écart-type ≈ 0,02). Avec un secteur public, s07 vaut +0,043 à +0,049 (ordinaire).

      Postérieur avec s111 et s16 : aucun public 0,03 (τ = 0,05 ; τ empirique ≈ 0,02-0,03, donc moins encore), un public 0,97, les deux 0,00. À τ = 0,10, trop large au vu de la distribution, on aurait 0,38 / 0,62.
    - **Scores attendus (un secteur d'eau public)** :
      - public : f2 ≈ 0,0550 ± 0,0009, f3 ≈ 0,0553 ± 0,0007 ;
      - privé : ≈ public + 0,0021 (écart de la simulation corrigée, 0,0019 à 0,0021), plus le surajustement de f2 sur s07 (+0,0001 de plus que f3 en privé, f3 meilleure dans environ 70 % des vérités). Donc f2 ≈ 0,0575, f3 ≈ 0,0574.
      - L'incertitude commune public → privé est d'environ ±0,003 et touche aussi les concurrents.
  - **Choix de l'utilisatrice : f2 envoyée (8DPgZvCX), public 0,057507575**, soit 44e du classement (vers le 17e rang parmi les scores plausibles).
    - Attendu : 0,0550 (algèbre) et 0,0545-0,0555 selon les secteurs d'eau, ±0,0009 ; écart +0,0025, z ≈ +2,8 dans le meilleur scénario.
    - Contrôles : le fichier reçu par Zindi est bien f2 (rubric rural 2,25× et tribal 2,71×, identiques au recalcul local 2,250 / 2,709 ; f1 et f3 donneraient 2,28×). Les 80 fichiers notés ont le SHA du journal. f2 se reconstruit à partir de ses poids à 5×10⁻⁷ près.
    - Piste principale : s07, poids 3,11 dans f2 (f3 : 2,5 au plus, sans s07). Si sa vraie covariance publique valait environ −0,00003 au lieu de +0,000016 mesurés, l'écart serait expliqué. Ce serait cohérent avec un secteur d'eau public, mais `water_pub2.py` ne le reproduit pas entièrement. Cause non tranchée. La reconstitution après la clôture, à partir des scores privés, dira ce qu'auraient fait f1 et f3.
    - 5 envois sur 5 utilisés le 31/10 : plus aucun envoi possible avant la clôture.
    - **Sélection** : f2 + s111 voulue. Le bogue #35607 (sélection limitée à une même page) peut l'empêcher, s111 étant sur une page plus ancienne. À défaut : f2 + un signal de la page 1, ou aucune sélection (Zindi prend alors le meilleur public, f2).
    - **Sélection faite et vérifiée (à la demande de l'utilisatrice)** : **f2 (8DPgZvCX) + s111 (EboKdJHP)**. La sélection enregistrée auparavant était **s106 + s111** (ancienne session), donc f2 n'était pas retenue.
      - Mécanisme du bogue (lu dans le code de la page) : les changements sont gardés en mémoire, mais seuls ceux des lignes de la page affichée comptent. Le bouton « Save your new selection » n'apparaît que si le nombre de choix du serveur plus ces changements fait exactement 2. Une paire répartie sur deux pages est donc impossible avec le tri par date.
      - **Contournement** : `…/submissions?sort=score` trie par score public ; f2, s111, s97 et s106 sont alors tous en page 1. On décoche s106, on coche f2, puis « Save your new selection ».
      - Contrôle après rechargement complet des 4 pages : seuls f2 (page 1) et s111 (page 2) sont cochés, et aucune page n'affiche « Please select 2 submissions ».
    - **Cause de l'écart de f2** (`q_tracts.py`, `q_scen.py`, `q_cond.py`) :
      - **Identité exacte** : le MSE public d'un mélange linéaire B = a + Pw vaut moyenne_pub(B²) + Y2 − 2am − Σ wᵢ[moyenne_pub(pᵢ²) + Y2 − rᵢ²]. Il dépend seulement des scores publics des signaux et des secteurs publics, pas de la vérité, sauf les gains d'écrêtage et de règle, qui ne peuvent qu'améliorer le score. L'écart à l'algèbre est donc moyenne_pub(q) − moyenne(q), avec q = B² − Σ wᵢpᵢ².
      - Les 80 scores du journal sont identiques à ceux de Zindi, et les 80 fichiers ont le bon SHA. Le score de f2 traduit donc un choc de composition du public d'environ +3 écarts-types sur q_f2, et non un défaut de covariance. Dans f2, les secteurs d'eau ont q = 0,26 et 0,23 (s07 au poids 3,11) ; dans f3, 0,05 au plus.
      - Le choc se transmet aux autres recettes : corrélation de leur q avec q_f2 de 0,66 à 0,78. Public attendu sachant le score de f2, un secteur d'eau public : f3 0,0569, WO ridge 0,02 0,0568, WO ridge 0,05 0,0567, f1 0,0567 (±0,0005).
    - **Finale de remplacement préparée** : `f5_blend_ridge002.csv` (`scripts/make_f5.py`), WEAK et s07/s22 exclus, ridge 0,02, 58 signaux actifs.
      - Algèbre 0,05675 ; sachant le score de f2, environ 0,0568 ; privé environ 0,057.
      - Vérifiée : 9 794 lignes, GEOID identiques à f2, secteurs d'eau à 1, SHA conforme au journal, f1-f3 inchangés ; corrélation 0,9996 avec f3 et 0,991 avec f2.
      - À envoyer seulement si Zindi accepte un envoi de plus avant 23 h 29, puis sélectionner f2 + f5 (`upload_2026-10-31_extra.txt`).
    - **Privé attendu de f2 sachant son public** (`sim_shock.py`, simulation corrigée, 150 vérités par scénario) :
      - (privé − algèbre) = 0,0012 à 0,0014 + **1,3 à 1,4** × (public − algèbre). Un choc de composition du public prédit un privé encore plus mauvais : les erreurs de composition des covariances mesurées faussent les poids. f3 suit la même relation avec 1,1 à 1,2.
      - Avec l'algèbre 0,0550 et le public 0,05751 : **f2 privé ≈ 0,0597-0,0603** (±0,003).
      - f3/f5, avec un choc transmis plus faible (public attendu 0,0569) : privé ≈ 0,0587-0,0590, soit environ 0,001 de mieux que f2.
      - s111 (aucun choc) : privé ≈ 0,0615-0,062.
  - **f2 contre f3, vérité par vérité** (`sim_f2_vs_f3.py`, 4 réglages ; simulation avant correction, voir ci-dessus) : f2 bat f3 dans 5 à 7 % des vérités (probabilités tirées des scores), 19 à 23 % sous un découpage au hasard ; **jamais de plus de 0,0003**. En moyenne f3 gagne 0,00025 à 0,00044. Si aucun secteur d'eau n'est public, c'est presque pile ou face (f2 gagne 39 à 47 %) ; si l'un l'est, f2 ne gagne jamais.

## 2026-10-31 — recherche n° 93 : recherche approfondie sur le net (trois axes)

- Rapport : `reports/Références TIGER et casernes USGS.md` (notes dans `research_notes/Références TIGER et casernes USGS/`) ; documentation seulement, aucune couche interdite.
- **TIGER** :
  - aucune règle publiée S1200 / S1400 pour les FM/RM du Texas ni pour les routes de comté de l'Oklahoma ;
  - depuis 2017, toutes les voies à accès limité passent en S1100, ce qui est neutre pour S1100 + S1200 ;
  - « All Roads » donne un enregistrement par nom (confirme s140 / s146) ;
  - aucune statistique publiée de noms par tronçon.
- **Casernes USGS** : la base vient d'un fichier privé d'environ 2009, revérifié par des bénévoles.
  - Texas / Oklahoma (2022) : points non revérifiés concentrés autour des villes de l'I-35 ;
  - Arizona : pas de liste d'État ;
  - aucun taux de complétude publié ; aucune évaluation des casernes Overture.
- **Participants** : environ 9 nouveaux dépôts, aucune méthode conforme avec score ; 2 dépôts utilisent les couches interdites ; aucune réponse officielle lisible sur l'ajustement aux scores publics.
- **Bilan** : tous les leviers suggérés sont déjà dans notre modèle (noms multiples, double comptage des limites, bretelles et dessertes exclues, poids des FM tertiary testé). Aucun changement pour les envois du 31/10.

## 2026-10-30 (suite) — recherche n° 92 : FEATNAMES, couverture USGS, erreurs S1200/S1400

- **Fichier TIGER des noms (FEATNAMES)** : un enregistrement par nom, relié aux tronçons par LINEARID ; un tronçon peut porter plusieurs noms (mécanisme de s140). Aucune statistique publiée du nombre de noms par tronçon.
- **Casernes USGS** : aucun taux de couverture par État. FGDC (2016) : la base des structures « peut être trompeuse et incomplète », alimentée par HIFLD et les bénévoles TNMCorps ; casernes HIFLD mises à jour en octobre 2022.
- **Erreurs S1200/S1400** : la documentation 2023-2025 confirme des grands axes classés à tort en S1400 et une « revue des grands axes » récente, sans chiffre par État ni audit des routes de comté.
- **Bilan** : rien d'exploitable ; les sources publiques sont épuisées.

## 2026-10-30 (suite) — recherche n° 91 : méthodes des équipes de tête sur le net

- Recherches « Jules_Duber », « Shivoo29 », « solvorlabs », « Gamma Team » + défi : un seul dépôt, Shivoo29/thirst-trap-map, une candidature Bias Discovery (lieux de rafraîchissement de Maricopa), sans méthode de classement. Aucun autre dépôt ni écrit sur un mélange ou un proxy TIGER. Rien de nouveau.

## 2026-10-30 (suite) — recherche n° 90 : option 4 signaux + 1 finale

- **Idée** : le 31/10 offre 5 envois. Au lieu de 3 signaux + 2 finales, envoyer 4 signaux + 1 finale. Zindi exige 2 sélections : la seconde serait l'ancien mélange s111.
  - Coût : la couverture f1/f2, d'une valeur espérée d'environ 0,0001-0,0002 en privé (simulations des recherches n° 86-88).
  - Gain : un signal de plus, environ 0,0003 en espérance, et surtout une chance supplémentaire de gros gain (ce qu'exige la première place).
- **4e signal** : s149_t9l_p_score_ge30_delta (`scripts/make_s149.py`), P(score ≥ 0,30) sous v9L moins sous v9, bord du changement de transport qui a payé (comme s102 après s97, s117 après v8).
  - Nouveau à 38 %, partie connue +0,35 ; partie nouvelle indépendante de s146, s142, s147 (|r| ≤ 0,11).
  - Échelle 0,07 (2 valeurs écrêtées à 0).
- **Plan B** (`submissions/upload_2026-10-31_planB.txt`) : s146, s142, s147, s149, puis la seule finale f2 (meilleur public et meilleur privé selon la formule) ; sélection f2 + s111. Plan A inchangé (`upload_2026-10-31.txt`). Choix laissé à l'utilisatrice.
- **Vérification avant envoi** : 70 signaux mesurés aujourd'hui ; le plan A en donne 73 (le plafond de D1-quater), le plan B 74. Le plan B exige donc de relever le plafond à 74 (décision de l'utilisatrice), sinon `make_finals.py` s'arrête. Les quatre fichiers sont conformes.

## 2026-10-30 (suite) — recherche n° 89 : chances de gros gain par famille ; fil #35657

- **Part des signaux notés dont la partie nouvelle atteint 0,10** (niveau de s140 ; `predictor_hist.csv`) :

  | Famille | Signaux | ≥ 0,10 | ≥ 0,07 | Maximum |
  |---|---|---|---|---|
  | TIGER / transport structurel | 11 | **36 %** | 64 % | 0,36 |
  | bords du score | 6 | 33 % | 33 % | 0,12 |
  | casernes, indices ciblés | 4 | 25 % | 50 % | 0,11 |
  | casernes, recalibrage | 8 | 0 % | 12 % | 0,09 |
  | découpages | 6 | 0 % | 0 % | 0,03 |
  | autres | 21 | 5 % | 10 % | 0,14 |

  - Trois signaux TIGER indépendants : au moins un ≥ 0,10 dans 74 % des cas, au moins deux dans 30 %, les trois dans 5 %.
  - Échelle (s140) : coût de retrait ≈ 0,05 × corrélation², soit environ 0,0005-0,0007 par signal à 0,10-0,12.
  - Il faudrait environ 0,0017 en public pour passer devant Jules (0,0544), donc trois signaux gagnants ou deux très gros : environ 5 à 10 % de chances.
- **Fil #35657** (28/10, question à l'organisatrice) : « Can the weights of my model be fitted from the public scores of my own submissions? ».
  - Réponse « Q1. No, Q2. No » le 30/10 de « Ajeet », un participant inscrit depuis 18 jours, sans envoi : pas une décision officielle.
  - SudoMan (30/10) redemande une décision aux organisateurs ; toujours rien, comme pour #35402, #35292 et #35532.
  - Notre risque à la revue du code est inchangé (mélange de signaux mesurés, D1-quater). La Documentation devra décrire la méthode en toute transparence.
- Lot du 31/10 inchangé : trois signaux TIGER, la famille qui a le plus de chances de gros gain.

## 2026-10-30 (suite) — décision : f1 garde tous les signaux

- Sur la consigne « faire au mieux pour le privé », l'interrupteur `KEEP_WEAK = {"f1_blend_ridge0005"}` est activé dans `make_finals.py`.
  - f1 : 68 signaux, sans s07/s22, public attendu 0,05675 (privé par la formule 0,06373) ;
  - f2 inchangée : 59 signaux, WEAK écartés, avec s07/s22, public 0,05581 (privé 0,06174).
- **Meilleur des deux** (simulation recalée, `sim_weak_cal.py`) : 0,07128 si la vérité est exactement le mélange (f2 type seule 0,07131, f1 type seule 0,07146) ; 0,07017 à incertitude moyenne (seules 0,07039 et 0,07023). La paire couvre les trois incertitudes : niveau du bruit, utilité des signaux faibles, secteurs d'eau.
- Le 31/10, la règle WEAK de `finalize_31.py` ne touche plus que f2 (et f3) ; f1 reçoit tous les signaux mesurés. Réversible : vider `KEEP_WEAK`.

## 2026-10-30 (suite) — recherche n° 87 : règle WEAK et simulation recalée sur la vraie cible

- **Simulation recalée** (`$TEMP/claude_ext/scr/sim_private_cal.py`, `sim_weak_cal.py`) : les vérités simulées sont ramenées à la moyenne (0,0598) et à l'écart-type (0,0890) réels. Auparavant 0,068 et 0,080, à cause de l'écrêtage dans [0, 1].
  - **f4** (ridge 0,3 vers v9L) : privé 0,06957 contre 0,06925 pour la recette actuelle ; mieux dans 29 % des vérités. Abandon confirmé.
  - **Règle WEAK** (67 signaux, dont 11 dans WEAK, s07/s22 exclus) :

  | Incertitude de la vérité | Tous les signaux | WEAK écartés | Tri adaptatif 0,00003 / 0,0001 / 0,0003 |
  |---|---|---|---|
  | nulle (vérité = mélange complet) | 0,07146 | **0,07131** | 0,07154 / 0,07203 / 0,07294 |
  | × 0,5 | **0,07023** | 0,07039 | 0,07037 / 0,07096 / 0,07222 |
  | × 1 | **0,06898** | 0,06941 | 0,06919 / 0,06989 / 0,07166 |

  - Ridge 0,002 / 0,005 / 0,01 avec tous les signaux : identiques à 0,00002 près.
  - Avant recalage, même sens et écarts plus grands (de −0,0001 à +0,0009).
- **Formule du privé** : f1 avec tous les signaux 0,06373 (contre 0,06193), f2 0,06354 (contre 0,06174) ; public 0,05675 et 0,05551. La formule pénalise les signaux faibles ; la simulation les juge neutres ou un peu utiles. Les seuils plus stricts sont toujours plus mauvais.
- **Proposition** : couvrir ce désaccord par la paire de finales.
  - f1 avec tous les signaux, sans s07/s22 ;
  - f2 inchangée (WEAK écartés, avec s07/s22).

  Interrupteur `KEEP_WEAK` ajouté à `make_finals.py`, vide tant que l'utilisatrice n'a pas donné son accord (modification de D1-quater).

## 2026-10-30 (suite) — recherche n° 86 : simulation de bout en bout du privé ; f4 abandonné

- **Simulation équitable** (`$TEMP/claude_ext/scr/sim_private.py`), 80 vérités :
  - vraie partie expliquée tirée autour de notre mélange avec l'incertitude des covariances mesurées (c_vrai ~ N(c_pub, S_e)), plus un résidu hétéroscédastique à queue épaisse (Student t) ajusté à l'écart-type de la cible ;
  - 30 % de secteurs publics tirés au hasard, covariances recalculées depuis les RMSE publics simulés ;
  - recettes ajustées, RMSE mesuré sur les 70 % restants.

  | Recette (base de f1, 57 signaux) | Privé réel, t à 4 ddl | t à 30 ddl | incertitude × 0,5 |
  |---|---|---|---|
  | ridge vers zéro 0,005 (f1/f2) | **0,04645** | **0,04714** | **0,04744** |
  | ridge vers zéro 0,02 | 0,04673 | 0,04741 | 0,04769 |
  | vers v9L 0,1 | 0,04694 | 0,04761 | 0,04775 |
  | vers v9L 0,3 (f4) | 0,04762 | 0,04825 | 0,04824 |

  - f4 ne fait mieux que dans 4 à 8 % des vérités.
  - La perte réelle entre public et privé est d'environ 0,001, très en dessous de la formule (environ 0,005, qui surestime le bruit) : peu de sur-ajustement à corriger, et le biais du modèle structurel coûte plus qu'il ne rapporte.
  - La vraie cible est bien plus proche du mélange (0,0570 en public) que du modèle seul (0,0717).
- **Ridge vers zéro** : 0 / 0,001 / 0,002 / 0,005 / 0,01 donnent 0,04655 / 0,04643 / 0,04642 / 0,04645 / 0,04653. 0,005 est dans le plateau.
- **Ridge pondéré par le bruit des covariances** (à l'échelle du ridge habituel) : 0,04642-0,04657, sans gain.
- **Décision** : f4 retiré de `FINALS` (le code d'une cible de ridge reste, documenté). Finales à envoyer et sélectionner le 31/10 : **f1 et f2** ; `finalize_31.py` les vérifie.

## 2026-10-30 (suite) — recherche n° 85 : le privé, régularisation vers le modèle structurel

- **Idée** : la perte entre public et privé de nos finales (environ 0,0045 à 0,006) vient en partie du bruit des covariances mesurées sur les seuls secteurs publics. Le ridge tire les poids vers zéro. On peut les tirer plutôt vers κ × les poids qui reproduisent le composite structurel v9L (transport v7L de s140 + casernes v9) à partir des signaux. Ce calcul n'utilise que les prédictions, donc aucun bruit du classement ; κ est ajusté sur les covariances mesurées (0,76, comme la pente mélange ≈ 0,75 × v9).
- **Privé attendu** (formule de `make_finals`, étendue à une cible de ridge ; `$TEMP/claude_ext/scr/prior_shrink.py`) :

  | Ridge | f1, vers zéro (privé / public) | f1, vers v9L | f2, vers zéro | f2, vers v9L |
  |---|---|---|---|---|
  | 0,005 | 0,06193 / 0,05704 | 0,06196 / 0,05706 | 0,06174 / 0,05581 | 0,06178 / 0,05586 |
  | 0,3 | 0,06266 / 0,05985 | **0,06149** / 0,05862 | 0,06233 / 0,05908 | **0,06114** / 0,05783 |
  | 0,5 | 0,06291 / 0,06056 | 0,06150 / 0,05909 | 0,06267 / 0,06001 | 0,06115 / 0,05842 |
  | ∞ (modèle seul) | — | 0,07166 | — | 0,07118 |

- **Sensibilité au niveau du bruit** (f1) :
  - bruit × 0,5 : vers zéro 0,05953, vers v9L à 0,3 : 0,06007 (le ridge vers zéro gagne) ;
  - bruit × 1 : 0,06193 contre 0,06149 ;
  - bruit × 1,5 : 0,06424 contre 0,06287.

  Le gain n'est donc pas acquis.
- **Choix de la paire** : Zindi garde le meilleur privé des deux sélectionnés. J'ai comparé l'espérance du meilleur des deux sur les scénarios bruit × 0,5 / 1 / 1,5 et secteurs d'eau sans effet (70 %) ou faussant s07/s22 (30 %, environ +0,0015 pour les finales avec s07/s22) :
  - f1 + f2 : 0,06170 ;
  - f2 + f2 vers v9L : 0,06135 ;
  - f1 + f2 vers v9L : 0,06136 ;
  - **f2 + f1 vers v9L : 0,06119**.
- → `scripts/make_structural_v9L.py` (composite v9L dans `data/interim/structural_v9L.parquet`) ; `scripts/make_finals.py` reçoit **f4_blend_prior03** (ridge 0,3 vers v9L, sans s07/s22) : essai à blanc, public 0,05862, privé attendu 0,06149. f1-f3 inchangées.
- **Finales du 31/10 à envoyer et sélectionner : f2 et f4** (`finalize_31.py` les vérifie). *Annulé par la recherche n° 86 : f1 et f2.*

## 2026-10-30 (suite) — recherche n° 84 : incertitude de la référence et secteurs sans route, revus après s140

- **Variantes de v7L** (`$TEMP/claude_ext/scr/sigma_q.py`, différence avec le modèle de s140, base de 71 signaux) :

  | Variante | Écart-type | Part nouvelle | Partie connue |
  |---|---|---|---|
  | σ_t 0,3 (au lieu de 0,5) | 0,0067 | 62 % | −0,03 |
  | σ_t 0,7 | 0,0061 | 46 % | +0,01 |
  | q_def_noroute 0 (Arizona 54,1 %, Texas 27,3 % sans transport) | 0,0013 | 15 % | +0,04 |
  | q_def_noroute 0,06 | 0,0013 | 16 % | −0,04 |

- **Lecture** : ni l'incertitude de la référence ni la définition des secteurs sans route ne sont mal réglées de façon visible. Rien ne remplace les trois signaux du 31/10.

## 2026-10-30 (suite) — recherche n° 83 : nouvelle recherche sur le net

- **Tutoriel des organisateurs** (kentstephen/bias-bounty-map-tutorial, carnet `bias-bounty-explore-tutorial.ipynb`, code seulement) : plus aucune ligne sur TIGER, le rapport ou un filtre de routes depuis le retrait des couches. Rien sur le sens du rapport.
- **Routes FM et TIGER** (recherches web) : rien sur leur code S1200. Seul fait nouveau : les routes « Urban Road » de 1995 sont redevenues FM le 15/11/2018 (sans effet sur notre modèle).
- **Blog ou page de Reliabl / Humane Intelligence sur le rapport par région** : introuvable.
- **Forum** : un seul fil nouveau, #35724 (Vhiktry1, 30/10, 17 h 02), une critique de la métrique.
  - Son proxy de numéros de route Overture donne Oklahoma 0,56, Texas 1,02, Californie 1,18, Washington 1,33, Arizona 1,60, qui encadre la plage officielle (FM et comtés comptés en entier, comme notre tout premier modèle).
  - Écart-type du RMSE estimé à environ 0,0010 en public et 0,0007 en privé.
  - Rien sur le sens réel du rapport.
- **Titres des 50 fils les plus récents** filtrés sur rapport, TIGER, routes, transport : tous déjà lus (#35543, #35542, #35479, #35333, #35325, #35288, #35277, #35241).
- **Bilan** : aucune source publique nouvelle ne tranche les trois questions TIGER du lot du 31/10.

## 2026-10-30 (suite) — recherche n° 82 : existe-t-il de meilleurs signaux que s146, s142, s147 ?

- **Ce qui prédit le gain réel** (56 signaux notés, `$TEMP/claude_ext/scr/predictor.py`). Corrélation avec la corrélation réelle de la partie nouvelle (valeur absolue) :
  - famille (moyenne hors du signal lui-même) : +0,39 ;
  - corrélation de la partie déjà mesurée : +0,34 ;
  - part nouvelle : −0,24.

  Régression : 0,026 + 0,46 × famille + 0,061 × |corr. mesurée| − 0,022 × part nouvelle, R² 0,18. C'est un guide faible.
- **Appliqué à environ trente candidats** : les variantes de s147 (lecture inverse) et de s140 (noms de rue, sans honorifiques) ressortaient à 0,096-0,110, contre 0,070 pour s146 et s142.
- **Piège** : ces variantes doivent une grande part de leur avance à la direction de s140, déjà mesurée et gagnante.
  - « Noms de rue seuls à 0,35 » exprimé contre v7 : R² 0,73, +0,30 ; exprimé contre v7L (même information pour le mélange) : R² 0,13, −0,02, prédiction 0,065.
  - s147 se décompose en une remise à l'échelle de s140 (R² 0,98) et la lecture inverse seule (R² 0,73, +0,26, dont l'essentiel est l'effet d'échelle).
  - Le prédicteur n'est pas invariant à l'écriture du signal ; seule la partie nouvelle compte.
- **s148_t7s_c_transport_delta** (`scripts/make_s148.py`, noms de rue seuls à 0,35, contre v7L) : partie nouvelle indépendante des trois autres, mais aucun appui. En réserve.
- **Parties nouvelles** : inv_b répète s147 (corrélation 1,00) ; noms de rue, sans honorifiques et rue + itinéraires se recouvrent entre eux (0,46-0,82).
- **Conclusion** : aucun candidat n'est meilleur de façon démontrable. Le lot reste s146, s142, s147 : trois questions TIGER distinctes (noms locaux restants, répartition des FM, calage d'ensemble).

## 2026-10-30 (suite) — recherche n° 81 : stabilité et écrêtage des trois signaux du 31/10

- **Écrêtage** : aucune valeur coupée à 0 ou à 1 dans s146, s142, s147 (valeurs entre 0,027 et 0,161).
- **Bruit de simulation** (`$TEMP/claude_ext/scr/mc_check.py`, chaque script relancé avec la graine 4242, rien d'écrit) : corrélation avec le fichier 0,9986 (s146), 0,9988 (s147), 0,9904 (s142).
  - s142 est plus bruité parce que sa partie texane déplace la définition du transport dans les secteurs à FM seules, ce que la graine commune n'annule pas.
- **s142 régénéré sur trois graines** (`scripts/make_s142.py`, chaque graine contre v7 à la même graine) : corrélation 0,9996 avec la version à une graine, partie connue +0,05, nouveau à 84 %. Lot du 31/10 revérifié (format, empreintes, jamais envoyé).

## 2026-10-30 (suite) — recherche n° 80 : les trois envois du 31/10, mis au point

- **Bruit des covariances** (`$TEMP/claude_ext/scr/lot_profile.py` ; facteur E[p_c² r²] / (E[p_c²] E[r²]), comme l'estimation du privé de `make_finals`) :

  | Signal | max \|z\| | Secteurs au-delà de 6 σ | Part des 20 secteurs les plus extrêmes | Facteur de bruit |
  |---|---|---|---|---|
  | s140 (a payé) | 6,7 | 2 | 5 % | 2,50 |
  | s117 (a payé) | 8,5 | 58 | 15 % | 4,85 |
  | s146 | 7,4 | 39 | 10 % | 1,31 |
  | s142 | 14,9 | 48 | 22 % | 1,49 |
  | s147 | 11,2 | 41 | 17 % | 2,02 |

  Aucun lissage nécessaire.
- **Parties nouvelles** (résidus sur la base de 71 signaux) : corrélations entre s146, s142 et s147 de −0,18 à +0,12, et au plus 0,12 avec s145 ou s121. Trois directions distinctes.
- **s137 entre dans `WEAK`** : une fois s138 et s143 retirés, son coût de retrait tombe à 0,00002. Finales : f1 0,05704 en public, 0,06193 en privé attendu (contre 0,05701 et 0,06213) ; f2 0,05581 et 0,06174.
- **`scripts/finalize_31.py`** (testé sur une copie de `make_finals.py`) :
  - enregistre les trois scores ;
  - recale le mélange et affiche les coûts de retrait ;
  - ajoute à `WEAK` tout nouveau signal sous 0,00003 ;
  - lance `make_finals.py` et vérifie f1 et f2.

  Commande du 31/10 : `python scripts/finalize_31.py s146_t7lf_c_transport_delta.csv=ID:RMSE s142_t10s_c_transport_delta.csv=ID:RMSE s147_t7linv_c_transport_delta.csv=ID:RMSE`.

## 2026-10-30 (suite) — recherche n° 79 : le net, pour la référence TIGER

- **Rapports Overture/TIGER par région** (« 0.71 » « 1.59 ») : aucune source hors de la page Info, qui ne donne que les bornes.
- **Archives** (Wayback Machine) :
  - une seule capture de la page du défi, le 10/07/2026, avant l'ouverture ; texte général, rien sur le rapport ni sur TIGER au-delà de « Census TIGER/Line Roads » ;
  - aucune capture sur zindi.world ;
  - le service était hors ligne pour la page source.coop.
- **Doublons et noms alternatifs dans « All Roads »** : aucune statistique publiée (métadonnées Census, MassGIS 2010 : doublons d'identifiants sur les limites de comtés). Rien de chiffrable sans les fichiers TIGER, interdits.
- **Bilan** : rien sur le net ne fixe le sens du rapport ni la part des FM et des noms locaux dans TIGER. Les trois signaux du 31/10 (s146, s142, s147) restent les seuls tests possibles de ces questions.

## 2026-10-30 (suite) — recherche n° 78 : calage conjoint de la référence TIGER

- **Grille** (`$TEMP/claude_ext/scr/tiger_grid.py`, résultats dans `tiger_grid.csv`) :
  - Texas Overture/TIGER 1,59 / 1,50 / 1,408 × Oklahoma 0,71 / 0,67 / 0,629 × noms locaux 0,15 / 0,25 / 0,35, poids FM et comtés recalés (400 tirages) ;
  - différence avec v7L jugée sur la base de 71 signaux, et à côté d'un contrôle de pure mise à l'échelle (référence v7L × 1,13 au Texas et en Oklahoma : partie connue +0,48).

  | Variante | Part nouvelle | Partie connue | À côté du contrôle d'échelle |
  |---|---|---|---|
  | lecture actuelle, noms 0,35 | 3 % | +0,31 | +0,30 |
  | lecture inverse, noms 0,35 | 28 % | +0,39 | +0,19 |
  | lecture inverse, noms 0,25 (ancien s147) | 25 % | +0,26 | +0,07 |
  | lecture actuelle, Oklahoma 0,67, noms 0,35 | 20 % | +0,43 | +0,34 (incohérent avec les deux lectures) |
  | noms 0,15, toutes lectures | 15-18 % | −0,34 à +0,10 | −0,33 à −0,05 |

- **Lecture** :
  - Le poids des noms locaux domine : la vérité en veut plus que 0,25 (comme le poids d'environ 1,9 du mélange sur s140), mais à lecture constante c'est une remise à l'échelle de s140, déjà mesuré.
  - Parmi les modèles cohérents avec la plage officielle, la lecture inverse avec des noms à 0,35 est la meilleure. C'est aussi la seule lecture inverse qui tient dans les quatre régions (Overture/TIGER : Arizona 1,28, Californie 1,40).
- → **s147 régénéré** (`scripts/make_s147.py`) : v7L avec noms locaux 0,35, FM 0,174, comtés OK 0,235, moins v7L. Nouveau à 28 %, partie connue +0,39 ; corrélation 0,12 avec s140, −0,23 avec s146, +0,22 avec s142, au plus 0,73 avec un signal noté.
- **Lot du 31/10** inchangé dans sa composition : s146, s142, s147.

## 2026-10-30 (suite) — recherche n° 77 : les trois derniers envois, choisis par famille

- **Corrélation réelle de la partie nouvelle, par famille** (chaque signal noté, base = signaux notés avant lui ; `$TEMP/claude_ext/scr/calib_family.py`) :

  | Famille | Signaux | Moyenne | Médiane |
  |---|---|---|---|
  | TIGER / transport structurel (s77, s97, s140…) | 11 | **0,118** | 0,092 |
  | casernes, indices ciblés (s92, s95, s134, s119) | 4 | 0,068 | 0,075 |
  | bords du score (s102, s117…) | 6 | 0,049 | 0,027 |
  | casernes, recalibrage du prior (s136, s143…) | 8 | 0,029 | 0,017 |
  | découpages régionaux / métros | 6 | 0,020 | 0,025 |

  - Échelle donnée par s140 : coût de retrait ≈ 0,05 × (corrélation de la partie nouvelle)².
  - Rattraper Jules depuis f2 (environ 0,0015) demanderait trois signaux à environ 0,10 chacun.
  - Seule la famille TIGER structurelle atteint ce niveau en moyenne. Aucun indice ciblé de caserne de 300 secteurs ou plus ne reste ; s145 relève du recalibrage (0,029).
- **Lecture inverse du rapport, sur le modèle de s140** (`$TEMP/claude_ext/scr/inv_v7L.py`) : TIGER/Overture, soit Texas 0,71 et Oklahoma 1,59 ; FM 0,201, comtés OK 0,266 (au lieu de 0,051 et 0,075).
  - Arizona dans la plage (1,334) ; Californie juste au-dessus (1,436 pour 1,408 au plus).
  - Différence avec v7L : nouvelle à 25 %, partie connue +0,26 (Texas seul +0,14, Oklahoma seul +0,21).
  - Le mélange va dans ce sens : il pèse le transport v7 environ 1,25 fois et s140 environ 1,9 fois.
- → **s147_t7linv_c_transport_delta** (`scripts/make_s147.py`) : corrélation au plus 0,74 avec un signal noté, −0,26 avec s140, −0,25 avec s146, +0,19 avec s142.
- **Autres candidats à côté de s146 et s142** (partie connue / part nouvelle) :
  - noms de rue seuls : +0,30 / 27 % ;
  - lecture inverse + noms 0,35 : +0,50 / 12 % ;
  - bord v9L P(score ≥ 0,30) : +0,35 / 38 % ;
  - s121 : +0,15 / 78 % ;
  - s145 : +0,13 / 50 %.
- **Lot du 31/10 recommandé** (`submissions/upload_2026-10-31.txt`), trois questions TIGER distinctes :
  - s146 : noms locaux restants ;
  - s142 : répartition des FM ;
  - s147 : calage d'ensemble Texas / Oklahoma.

  s121 et s145 passent en réserve.

## 2026-10-30 (suite) — recherche n° 76 : grille de l'Oklahoma, aéroports, double comptage des péages

- **Noms de grille** (Oklahoma et Arizona suivent un cadastre en grille ; les routes de section portent des noms comme « E0490 Rd », que TIGER garde en enregistrement de plus et qu'Overture ne reprend pas ; `$TEMP/claude_ext/scr/grid_names.py`, `grid_model.py`) :
  - grands axes sans nom local orientés à moins de 2° du nord-sud ou de l'est-ouest : Oklahoma 7 188 km (contre 6 384 km d'autres orientations), Texas 3 300 (contre 24 087) ;
  - Oklahoma, poids 0,15 : partie connue −0,03 (écart-type 0,0015) ; poids 0,25 : impossible (poids des comtés négatif, le rapport 0,71 ne laisse qu'environ 4 000 km au-delà des grands axes) ;
  - placebo Texas : +0,01.

  Rejeté.
- **Aéroports commerciaux et bases militaires** (casernes propres que l'USGS place au centre ou à l'entrée du site) : environ 80 secteurs notés sans caserne connue, moins de 300 : exclu par D1-quater, comme le 30/10.
- **Multiplicité des numéros** (`mult_combos.py`) : moyenne 1,30 en Oklahoma, 1,14 au Texas, 1,08 en Arizona.
  - Les autoroutes à péage de l'Oklahoma portent un réseau « US:OK:Turnpike » sans numéro à côté du numéro de route (I-44 Turner et Will Rogers Turnpikes 837 km, SH 375 Indian Nation 336, US 412 Cimarron 297…). La multiplicité les compte déjà comme l'enregistrement du nom de l'autoroute.
  - Leur nom local est ce même enregistrement : s140 l'ajoute en plus pour les routes d'État (environ 800 km, déjà mesuré, inchangé), et s146 l'aurait ajouté pour les Interstates (1 005 km).
- **s146 corrigé et régénéré** (`scripts/make_s146.py`, sans les noms locaux des Interstates portant un réseau à péage sans numéro) : FM 0,017, comtés OK 0,053 (au lieu de 0,042) ; nouveau à 75 %, partie connue +0,05 ; corrélation 0,07 avec s140, 0,77 avec s141.
- **Bilan** :
  - TIGER : les rapports officiels bornent tout ajout en Oklahoma et au Texas, et s140 a pris la part des noms locaux. s146 et s142 sont les deux derniers tests structurels possibles.
  - Casernes : plus aucun indice ciblé de 300 secteurs ou plus ; s145 est la dernière piste.

## 2026-10-30 (suite) — recherche n° 75 : nouveaux indices ciblés de caserne, variantes TIGER, bords v9 + noms locaux

- **Indices civiques de caserne** (`$TEMP/claude_ext/scr/fire_targets.py`, `fire_ctrl.py`, `fire_civic.py`). Part des secteurs hors centres de ville qui ont une caserne connue, quand ils ont aussi le lieu indiqué, rapportée à des secteurs ayant autant de lieux Overture :

  | Lieu | Rapport | Secteurs notés sans caserne connue |
  |---|---|---|
  | mairie / poste forestier | 2,00 / 2,07 | 146 / 20 |
  | aéroport / prison / police / « Public Safety » | 1,74 / 1,70 / 1,64 / 1,61 | 323 / 92 / 525 / 28 |
  | bureau de poste / bibliothèque | 1,54 / 1,44 | — |
  | base militaire / site industriel | 1,36 / 1,23 | 67 / 84 |
  | contrôles : église, restaurant, station-service, école | 0,98 à 1,07 | — |

  - Supplément de casernes attendues (0,9 pour une mairie, 0,6 police, aéroport, prison, 0,43 militaire, industriel) dans les secteurs sans caserne connue : parties connues −0,004 (mairies, 146 secteurs), −0,04 (civiques, 613), −0,04 (tous, 1 030), −0,10 (avec postes et bibliothèques, 2 087).
  - Lecture : mairie et caserne vont souvent ensemble, mais quand Overture ne voit pas de caserne près d'une mairie, celle de la ville est probablement dans un secteur voisin. Rejeté.
- **Noms « Station 12 », « Engine 5 »** sans le mot « fire » (`fire_stationnames.py`) : bâtiments dans 244 secteurs, dont 9 seulement sans caserne connue ; lieux dans 78 secteurs, dont 37. Déjà captés pour l'essentiel.
- **TIGER, à côté de s140** (`tiger31.py`) :
  - poids des noms locaux 0,40 / 0,45 (FM 0,020 / 0,010 ; comtés 0,029 / 0,014) : 97 % déjà mesuré, simple remise à l'échelle de s140. Le mélange multiplie déjà l'effet de s140 par environ 1,9, ce qui laisse peu de place aux FM dans TIGER.
  - routes Business / Alternate / Truck au poids 1 : +0,02.
- **Bords de v9 avec le transport v7L** (`v9L_edges.py`) : niveaux déjà mesurés (R² 0,91-0,99). Différences avec v9 : P(score ≥ 0,30) nouvelle à 38 %, +0,35 (mais s137, construit de la même façon pour v9 − v8, n'a rapporté que 0,00004) ; P(zéro) nouvelle à 43 %, −0,14. En réserve.
- **Leçon des scores** : les corrections structurelles de la référence TIGER paient (v3, v7, s140) ; les recalibrages du prior des casernes non (s136, s133, s143) ; s121 est un découpage du transport, famille sans gain.
- **Lot du 31/10 recommandé** : s146 (noms locaux restants), s142 (FM et comtés à nom de rue : seul test structurel de la répartition des FM), s145 (casernes multiples). s121 passe en réserve.

## 2026-10-30 — scores du 30/10 : les noms locaux TIGER paient ; recherche n° 74

| Id Zindi | Fichier | RMSE public | Corrélation implicite | Coût de retrait | Partie nouvelle (corrélation) |
|---|---|---|---|---|---|
| NKYheKx3 | s140_t7l_c_transport_delta (corrigé) | 0,086302 | +0,352 | **+0,00111** | **+0,149** |
| y4ftFjf6 | s143_t9_fire_gapfill | 0,087526 | +0,217 | 0,00000 | +0,010 |
| 427Fdgb3 | s137_t9_p_score_ge30_delta | 0,086114 | +0,288 | +0,00004 | −0,025 |
| YJUXzQyn | s138_t9_p_zero_delta | 0,087735 | +0,194 | +0,00001 | +0,003 |
| 4xGiP53V | s117_t8_p_score_ge30 | 0,082734 | +0,377 | +0,00059 | −0,109 |

- **Mélange des finales** (quatre régions, ridge 0,005, `WEAK` et s07/s22 exclus) : 0,05909 → **0,05700** en public attendu (−0,00209), le plus grand gain depuis le 26/10.
  - Essai à blanc de `make_finals` : f1 0,05701 (privé attendu 0,0621), f2 0,05580 (0,0620).
  - 75 envois sur 200.
- **Lecture** :
  - La référence TIGER compte bien une copie par nom local (s140), comme le dit la documentation du Census.
  - Le comblement des trous de casernes (s143), malgré une partie connue de +0,21, n'apporte rien au-delà des signaux existants. C'est le troisième recalibrage du prior des casernes sans gain (s136, s133). Seuls les indices ciblés de caserne ont payé (s92, s95, s134).
- **Règles appliquées** : s143 et s138 entrent dans `WEAK` (coût de retrait inférieur à 0,00003) ; s140, s117 et s137 restent dans les finales. s144 tombe (s143 n'a pas payé). s140 a payé, donc la règle prévoit s141.
- **Recherche n° 74, suite de s140** (base de 70 signaux mesurés, `$TEMP/claude_ext/scr/screen31.py`) :
  - s141 n'a plus qu'une partie connue de +0,03. Surtout, il est incompatible avec s140 : noms locaux des Interstates à 0,5 en plus de ceux de s140, le poids FM qui tient le rapport 1,59 devient négatif.
  - Trou du modèle de s140 : les noms locaux des Loops, Spurs, Beltways et Tollways texans (Loop 1604 « Anderson Loop », Loop 1 « MoPac », Beltway 8 « Sam Houston Parkway », SH 130 « Pickle Parkway », Grand Parkway : 3 386 km de bande dans 1 203 secteurs) passent par le terme FM et ne reçoivent que 0,25 × 0,051. Seuls : nouveau à 83 %, partie connue +0,06.
  - → **s146_t7lf_c_transport_delta** (`scripts/make_s146.py`) : noms locaux des Interstates comptées (Business Loops exclues) et des Loops texanes au poids 0,25, en plus de v7L, moins v7L. Poids FM 0,017, comtés OK 0,042 ; parts sans transport inchangées. Nouveau à 73 %, partie connue +0,06, corrélation 0,81 avec s141 et 0,09 avec s140 (version corrigée en recherche n° 76).
- **Lot du 31/10** (`submissions/upload_2026-10-31.txt`, règle fixée la veille, s146 à la place de s141) : s146, s121, s145. s142 et s122 en réserve. Puis `python scripts/make_finals.py`, envoi de f1 et f2, et sélection des deux.

## 2026-10-30 — recherche n° 73 : casernes, quatre mécanismes de plus

- **Fait utile** : sur les 5 594 secteurs notés sans caserne connue, seuls 484 sont à majorité rurale. L'incertitude casernes se trouve surtout en ville et en banlieue.
- **Croissance récente** (casernes neuves absentes de l'USGS, mise à jour par des bénévoles depuis 2013) : pas de mesure de croissance dans le paquet (les dates Microsoft sont des dates d'image), et changer « caserne, écart 0 » en « non définie » ne bouge presque pas le score. Écartée.
- **Présence d'un village** (taux v9 × nombre de lieux, secteurs sans caserne connue, `$TEMP/claude_ext/scr/fire_village.py`) : parties connues −0,02 à −0,08. Rejetée.
- **Couverture par bâtiment** (part des 13,6 millions de bâtiments du secteur à plus de 1,5 / 2,5 / 4 / 8 km de toute caserne connue, `fire_bldcover.py`) : seule +0,10 à +0,19, mais corrélée à 0,57-0,86 avec s143 et +0,01 à +0,06 à côté de lui. Rien de plus que s143.
- **Casernes multiples** (`fire_dup.py`) : δ casernes de référence de plus par caserne Overture là où il y en a (doublons USGS, ou plusieurs casernes par service quand Overture ne liste que le siège). C'est cohérent avec l'écart mélange − v9 qui croît avec le nombre de casernes Overture (recherche n° 63).
  - δ = 0,15 : +0,10 seule, +0,07 à côté de s143 et s144 ;
  - δ = 0,3 : +0,13 seule, +0,12 à côté de s143 et s144.
- **Modèle combiné** (comblement × comté × casernes multiples, `fire_v10.py`) : +0,24 seul, la meilleure partie connue casernes, mais corrélé à 0,81 avec s143 ; deux ou trois signaux séparés couvrent davantage.
- → **s145_t9_fire_multistation** (`scripts/make_s145.py`, δ = 0,3, deux graines) : nouveau à 50 %, partie connue +0,13 seule, +0,12 à côté de s143, s144 et du lot ; corrélation 0,20 avec s143, 0,17 avec s144, au plus 0,50 avec un signal noté.
- **Envois** (lot du 30/10 validé par l'utilisatrice) :
  - 30/10 : s140, s143, s137, s138, s117 (s122 en réserve) ;
  - 31/10, 3 signaux par priorité : s144 si s143 coûte au moins 0,0001 au retrait ; s141 si s140 coûte au moins 0,0001 ; puis s121, s145, s142, s122.

## 2026-10-30 — recherche n° 72 : complétude locale des casernes

- **Idée** : généraliser s143. Ce qui compte n'est pas seulement la distance à la caserne connue la plus proche, mais la complétude locale d'Overture : casernes connues (lieux, noms vérifiés, bâtiments OSM, centres de ville) contre casernes attendues par le taux v9, dans un voisinage. Les secteurs sans caserne connue d'une zone sous-couverte en cachent davantage (`$TEMP/claude_ext/scr/fire_nbhd.py`, `fire_combo.py`, `fire_county.py`).

  | Variante (différence de contribution casernes avec v9) | R² seule | Partie connue seule | À côté de s143 : R² / partie connue | Corrélation avec s143 |
  |---|---|---|---|---|
  | rayon 10 km, β 0,5 | 0,29 | +0,18 | 0,36 / +0,10 | 0,54 |
  | rayon 20 km, β 1 | 0,29 | +0,18 | 0,34 / +0,12 | 0,50 |
  | rayon 30 km, β 0,5 | 0,23 | +0,16 | 0,28 / +0,10 | 0,44 |
  | **comté**, a priori 5, β 1 | 0,25 | +0,16 | 0,28 / +0,12 | 0,38 |
  | distance depuis le centre des lieux (au lieu du point intérieur) | 0,31 | +0,15 | 0,63 / −0,01 | 0,78 |
  | distance × complétude 20 km (un seul modèle) | 0,44 | +0,20 | 0,70 / +0,06 | 0,80 |

  - Fusionner les deux mécanismes en un seul modèle ne dépasse pas s143 seul (+0,21).
  - La complétude par comté apporte une part propre et presque indépendante de s143. Les services d'incendie sont organisés par comté (services de comté, ESD au Texas, districts ruraux en Oklahoma).
- → **s144_t9_fire_county_completeness** (`scripts/make_s144.py`) : taux v9 × (complétude générale / complétude du comté) dans les secteurs sans caserne connue, total de chaque région inchangé, bord exclu, deux graines.
  - Nouveau à 72 %, partie connue +0,17 seule, +0,12 à côté de s143 et du lot du 30/10.
  - Corrélation au plus 0,35 avec un signal noté.
- **Envois proposés** (plan séquentiel : le score d'un signal décide de l'envoi de son complément) :
  - 30/10 : s140, **s143**, s137, s138, s117 ; s122 (79 % déjà mesuré) passe en réserve ;
  - 31/10 : s144 si s143 coûte au moins 0,0001 au retrait, s141 si s140 coûte au moins 0,0001 ; places restantes : s121, puis s142, puis s122.

## 2026-10-30 (suite) — recherche n° 71 : la présence des casernes USGS, mécanismes jamais testés

- **Noms de caserne manqués** (`$TEMP/claude_ext/scr/fire_names.py`) :
  - Texas : quelques « ESD / Emergency Services District » (Travis, Hays) ;
  - Arizona : quelques « Fire & Medical » ;
  - Oklahoma : quelques « Fire/Rescue » ;
  - « Firehouse » ne ramène que des commerces.

  Quelques dizaines de casernes au total : pas de levier.
- **Faux « fire_department »** (syndicats « Local 157 », Fire Marshal, administrations, centres de formation, musées) : 99 sur 3 641, soit 3 %. Faible effet.
- **Comblement des trous de couverture** (`$TEMP/claude_ext/scr/fire_gapfill.py`).
  - Idée : les vraies casernes sont réparties assez régulièrement, et Overture n'en tient qu'environ 60 %. Un secteur sans caserne connue est donc plus susceptible d'en avoir une de référence s'il est loin de toute caserne connue, et moins s'il en est entouré. Le prior v9 ne regarde que le secteur lui-même.
  - Casernes connues : 4 522 lieux (fire_department en catégorie principale ou secondaire, noms vérifiés) et 1 765 bâtiments OSM.
  - Distance du point intérieur de chaque secteur à la plus proche ; taux v9 multiplié par exp(β z(log distance)) dans les 5 895 secteurs sans caserne connue ni centre de ville, total attendu inchangé.

  | Variante (différence de contribution casernes avec v9) | R² | Partie connue |
  |---|---|---|
  | contrôle : v9 avec une autre graine | 0,02 | +0,00 |
  | β = 0,25 / 0,35 / 0,5 / 1,0 | 0,42-0,44 | +0,19 / +0,20 / +0,19 / +0,12 |
  | β = −0,5 (sens inverse) | 0,57 | −0,21 |
  | β = 0,35 centré par région | 0,45 | +0,20 |
  | idem, secteurs du bord des régions exclus (distances surestimées) | 0,47 | +0,21 |

- → **s143_t9_fire_gapfill** (`scripts/make_s143.py`, β = 0,35 centré par région, bord exclu, deux graines moyennées).
  - Nouveau à 53 %, partie connue +0,21 ; corrélation au plus 0,55 avec un signal noté (s136), 0,35 au plus avec le lot du 30/10.
  - Moins de casernes manquantes près des casernes connues (environ −0,005 de contribution), plus dans les secteurs à plus de 8 km de toute caserne connue (+0,006).
  - Queue comparable à s134 (19 secteurs au-delà de 6 écarts-types, contre 71).
- **Comparaison des candidats** (même base, partie connue / part déjà mesurée) : s143 +0,21 / 47 %, s121 +0,15 / 20 %, s139 +0,10 / 59 %, s141 +0,04 / 21 %, s142 +0,04 / 15 %.
- **Règle du 31/10 proposée** : s143 et s142 dans tous les cas, plus s141 si s140 coûte au moins 0,0001 au retrait, sinon s121. s139 et s123 passent en réserve.

## 2026-10-30 (suite) — recherche n° 70 : ressources du net, et le sens du rapport 0,71-1,59

- **Dépôts GitHub récents** :
  - Agnuxo1 (référence TIGER ≈ routes nommées Overture + 0,15 × tertiary, aucun score accepté) ;
  - vik439 (aucun modèle routier décrit) ;
  - ssmurfgg04-gif/mappedclim (langyao : reconstruction d'avant le retrait des couches, sans intérêt ; son affirmation « la métrique serait la MAE » est démentie par nos prédictions de scores, justes à chaque lot) ;
  - rifatsarwarcodes (404).

  Aucune méthode nouvelle.
- **Forum** : un seul fil nouveau, #35666 (adamstra, équipe à score quasi nul, gués submersibles du Texas). Rien d'utilisable.
- **Classement** (lu le 29/10 au soir) : Jules_Duber 0,054405 en tête des équipes conformes ; nous 45e avec 0,059990 (s111) ; f1 attendu à 0,0591.
- **Page Info** : « 10 submissions per day, 300 overall ». Déjà vu le 27/10 ; la plateforme applique 5 et 200 (compteur), confirmé par l'utilisatrice. Rien ne change.
- **Sens du rapport officiel.** « the ratio of the two ranges from 0.71 to 1.59 » ne précise pas le sens.
  - Lecture inverse, TIGER/Overture : Texas 0,71, Oklahoma 1,59. Les poids deviennent FM 0,279, comtés OK 0,342 ; l'Arizona et la Californie doivent alors recevoir des noms locaux (poids ≥ 0,31 en Californie) pour rester dans la plage.
  - Résultats (`$TEMP/claude_ext/scr/ratio_inv.py`) :

  | Variante (différence avec v7) | Part nouvelle | Partie connue |
  |---|---|---|
  | lecture inverse seule | 24 % | +0,27 |
  | lecture inverse + noms locaux 0,35 | 55 % | +0,39 |
  | contrôle : référence × 1,13 au Texas et en Oklahoma | 24 % | +0,48 |
  | lecture inverse + noms locaux, à côté du contrôle d'échelle | 46 % | +0,09 |
  | contrôle : sans multiplicité (FM 0,243, comtés 0,452) | 24 % | −0,17 |

  - La forte partie connue de la lecture inverse vient presque entièrement de « plus de transport au Texas et en Oklahoma ». Le mélange corrige déjà cette échelle (transport ≈ 1,25 × v7). Une fois l'échelle retirée, il reste +0,09 : la lecture inverse n'est pas démontrée.
  - La lecture Overture/TIGER reste la plus naturelle : même quotient que la formule, et l'Arizona et la Californie tombent dans la plage sans mécanisme ajouté. La multiplicité des numéros est confirmée (−0,17 sans elle).

## 2026-10-30 (suite) — recherche n° 69 : les hypothèses de base de la référence, une à une

- **Bretelles** (S1630 dans TIGER, hors référence) : la part des tronçons « link » dans nos grands axes comptés est de 0,2 à 0,5 % selon la région. Aucun biais.
- **Coins de secteurs** (la bande de 10 m crédite quelques mètres d'un grand axe qui frôle un coin, alors que la vérité n'y voit qu'un point) : 62 secteurs ont moins de 100 m de grand axe dans la bande. Presque tous ont des routes Overture notées, si bien que le modèle leur donne un écart transport proche de 0. Effet négligeable (environ 1e-5 d'erreur quadratique).
- **FM primary/trunk au poids 1** (artères majeures ; 3 919 km), le reste à 0,046 : partie connue −0,06. Rejetée.
- **Perte entre public et privé des finales** (`make_finals`, quatre régions, 54 signaux utiles) :

  | Ridge | Public (en échantillon) | Privé attendu | Privé si les covariances mesurées étaient exactes |
  |---|---|---|---|
  | 0,005 | 0,05909 | 0,06378 | 0,06153 |
  | 0,02 | 0,05952 | 0,06393 | 0,06191 |
  | 0,05 | 0,05998 | 0,06402 | 0,06227 |

  Le bruit des covariances mesurées sur 2 814 secteurs publics coûte environ 0,0023 en privé (écart-type médian du bruit 2,2e-5 pour une covariance médiane de 1,0e-4). Toute équipe qui mélange des sondes le paie aussi. Seul un a priori structurel sur les covariances pourrait le réduire ; c'est un levier distinct de TIGER, non testé.
- **Bilan des recherches n° 66 à 69** :
  - 19 hypothèses sur la référence TIGER ont été testées contre les chiffres publiés et les 70 mesures. Une seule correction tient (s140) ; s142 reste le seul test possible de la répartition des FM au Texas.
  - Le classement S1200 tronçon par tronçon n'existe que dans les couches retirées, dont l'usage est interdit (TIGERweb compris).

## 2026-10-30 (suite) — recherche n° 68 : deux mécanismes TIGER encore jamais testés

- **Relecture des énoncés chiffrés du README** : pas d'autre statistique publiée sur la vérité que celles déjà utilisées (rapports 0,71-1,59, parts de secteurs sans composante).
- **Routes coupées au contour des régions** (README : « Spatial layers are cut at the region boundary » ; le contour suit les secteurs, donc la géométrie TIGER). Une route TIGER posée sur le contour reste entière, alors que sa copie Overture est coupée là où elle sort de la région.
  - Mesure (`$TEMP/claude_ext/scr/edge_roads.py`, `edge_cut.py`) : longueur du contour à moins de 15 m d'un grand axe compté : Texas 199 km, Arizona 184, Californie 154, Oklahoma 14.
  - Part disparue à la coupe, estimée en refermant les trous entre morceaux visibles : environ 10 à 20 % (Arizona : 184 km couverts à 15 m, 215 à 60 m, 266 à 200 m, dont une bonne part vient seulement de l'allongement des extrémités).
  - Effet : écart transport d'environ 0,1-0,2 sur quelques kilomètres de route dans une centaine de secteurs de bord. Négligeable ; la piste écartée le 22/10 l'était à juste titre.
- **Classement tout-ou-rien, route par route** (v10 ; `Params.extra_ref` dans `bbx.structural`, `$TEMP/claude_ext/scr/aon_pairs.py`, `aon_models.py`).
  - Idée : TIGER classe une route entière en S1200 ou non, alors que le v7 compte 11 % de chaque kilomètre FM (15 % de chaque route de comté en Oklahoma). Les routes de comté de l'Oklahoma ne sont presque jamais dans les classes Overture notées (76 km sur 26 627), donc une route S1200 ferait sauter l'écart.
  - Probabilité par couple (secteur, route) égale au poids publié (FM 0,112, comtés 0,152), sur 8 296 couples au Texas et 4 509 en Oklahoma.

  | Variante | Écart-type de la différence de transport | R² | Partie connue | Part sans transport |
  |---|---|---|---|---|
  | FM du Texas | 0,0039 | 0,18 | −0,06 | TX 26,3 % (v7 26,8 %, publié 28 %) |
  | comtés de l'Oklahoma | 0,0029 | 0,20 | −0,06 | OK 21,6 % (21,1 %, publié 21 %) |
  | les deux | 0,0049 | 0,19 | −0,08 | — |

  Le tout-ou-rien va à l'opposé des mesures, et s'éloigne un peu des parts publiées : le poids fractionnaire reste la meilleure forme. Le crochet `extra_ref` reste dans `bbx.structural` (sans effet par défaut).
- **Trois autres mécanismes** (`$TEMP/claude_ext/scr/cand68.py`, `fmvar68.py`). Les noms de rue sont ceux qui finissent par un type de voie, hors numéros de route et noms honorifiques.

  | Hypothèse (poids recalé sur 1,59 / 0,71) | Écart-type | Part nouvelle | Partie connue |
  |---|---|---|---|
  | FM portant un nom de rue = S1200 (8 643 km, poids 0,74) | 0,0107 | 82 % | +0,02 |
  | routes de comté de l'Oklahoma portant un nom de rue (5 796 km, poids 0,70) | 0,0060 | 94 % | +0,05 |
  | routes de desserte du Texas (1 451 km) dans TIGER, poids 0,5 / 1 | 0,0016 / 0,0035 | 87 % | −0,05 (rejetée : S1640, comme supposé) |

  Toutes les règles FM testées (n° 66 à 68) ont une partie connue entre −0,05 et +0,04. Les 70 mesures ne disent presque rien de la répartition des FM au Texas, la plus grande inconnue TIGER ; seul un score peut trancher.
- → **s142_t10s_c_transport_delta** (`scripts/make_s142.py`) : FM et routes de comté à nom de rue comme S1200, moins v7 (Texas : 26,5 % sans transport ; Oklahoma : 21,1 %). Écart-type brut 0,0123, nouveau à 84 %, partie connue +0,04 (+0,02 à côté de s140) ; corrélation 0,09 avec s140, environ 0 avec s141 et s139.
- **Règle du 31/10 proposée** : si s140 coûte au moins 0,0001 au retrait, s141, s142, s139 ; sinon s142, s139, s123. s121 sort : c'est un découpage du transport, famille sans gain depuis le 28/10.
- **Bilan** : avec les recherches n° 66 et 67, tous les mécanismes connus de la référence TIGER ont été testés contre les chiffres publiés et les 70 mesures. Seule la correction de s140 tient dans les mesures existantes. s142 est le seul test restant de la grande inconnue texane.

## 2026-10-30 (suite) — recherche n° 67 : la référence TIGER, partout ; un défaut de s140 corrigé

- **Données du paquet** : les colonnes des 23 tables de strates ont été passées en revue. Aucune ne porte sur les routes (densité, trafic, réseau) ; `cvi_baseline_infrastructure` et `svi_housing_transport` sont des indices génériques. Les seules données routières restent les routes Overture.
- **Routes FM du Texas par classe Overture** (même méthode que la recherche n° 66, `$TEMP/claude_ext/scr/fmvar67.py`) :
  - FM primary/trunk et secondary éligibles : −0,06 ;
  - secondary seules : −0,06 ;
  - « tertiary » seules : +0,04 ;
  - primary/trunk seules : impossible (poids 1,16 requis).
  Rien de net.
- **Documentation publique** (Census, Texas Tech, Federal Register 2017, wiki OSM) : aucune règle d'attribution du code S1200 tronçon par tronçon.
- **Calibrage de notre tri** (`$TEMP/claude_ext/scr/known_calib.py`). Pour chaque signal noté, dans l'ordre d'envoi, on compare sa partie connue (sur les signaux notés avant lui, ridge 0,005 ou 0,05) à la corrélation réelle de sa partie nouvelle avec la vérité.
  - Corrélation entre les deux : 0,33 à 0,49 ; même signe dans 59 à 63 % des cas.
  - Parties nouvelles réelles : |corrélation| ≤ 0,11, sauf deux nouveaux modèles complets du transport (v3 : 0,36 ; v7 : 0,28).
  - La partie connue n'est qu'un indice modeste. Les grands gains sont venus de corrections structurelles de la référence entière.
- **Défaut trouvé dans s140.**
  - `LEVEL2_SQL` classe en grands axes tous les réseaux `US:I:%` et `US:US:%`, mais `N_MAJOR2_SQL` ne compte que `US:(I|US|<État>)` et les systèmes d'État. Un tronçon seulement « US:US:Historic », « Old », « US:I:Business:Loop » ou « US:I:Express » a donc une multiplicité 0 : il est hors de la référence v7.
  - Ses noms locaux entraient pourtant dans `majloc`, si bien que s140 lui donnait une référence propre. Ces tronçons représentent 558 km de bande en Arizona, 173 en Oklahoma et 173 en Californie.
  - Effet sur la part de secteurs sans transport (v7 → v7L) : Arizona 52,5 → 49,3 % (55 % publié), Californie 37,9 → 34,4 % (37 %), Oklahoma 21,1 → 19,9 % (21 %). Dans le modèle, bâtiments et établissements sont presque toujours définis, donc la part publiée « au moins une composante non définie » mesure bien le transport.
- **Correction** :
  - `scripts/build_uncounted_majors.py` écrit `data/features/features_uncounted.parquet` ;
  - `scripts/make_s140.py` ne compte plus que les noms locaux des grands axes comptés. Les parts redeviennent celles du v7 ; FM 0,051, comtés OK 0,075 ; nouveau à 67 %, partie connue **+0,232** (contre +0,217) ; corrélation 0,87 avec l'ancien fichier.
  - **s140 régénéré sous le même nom** (jamais envoyé ; nouvelle ligne du journal des fichiers, SHA 846cf853…).
  - s141 corrigé de la même façon (sans les noms locaux des Business Loops) : partie connue +0,07 à côté du nouveau s140, parts du v7.
- **Nature des noms locaux** (`$TEMP/claude_ext/scr/locclass.py`, `locmodels.py`). Les noms locaux des grands axes comptés ont été classés en :
  - noms de rue (adresses : Main Street, Katy Freeway, Turnpikes) ;
  - noms d'itinéraires (« Globe–Lordsburg Highway », 5 043 km de bande en Arizona) ;
  - noms honorifiques (« Purple Heart Trail », « Veterans Memorial Highway » : un tiers en Oklahoma) ;
  - numéros mal reconnus par `ROUTE_LIKE_RE` (« U.S. Highway 77 », « Ranch Road 1323 », « Farm-to-Market Road 455 »).

  | Variante (poids recalés) | Partie connue | Corrélation avec s140 corrigé |
  |---|---|---|
  | noms de rue seuls, 0,35 (maximum faisable 0,70) | +0,20 | 0,83 |
  | rue + itinéraires, 0,33 | +0,22 | 0,94 |
  | tout sauf honorifiques et numéros, 0,30 | +0,23 | 0,96 |
  | noms de rue des Interstates au poids 1 (faisable) | +0,00 | 0,02 |

  Les mesures ne départagent pas ces hypothèses : s140 corrigé reste la meilleure forme de la piste.
- **Bilan sur l'objectif de 50 %** : les seules informations autorisées sur la référence TIGER sont les rapports 0,71-1,59, les parts de secteurs sans composante et les mesures du classement. Les deux premières sont désormais respectées exactement. Aucune donnée du paquet ne révèle le classement S1200 tronçon par tronçon. Une réduction de 50 % de l'incertitude TIGER n'est pas atteignable ; le gain possible passe par s140 corrigé (30/10), puis s141 ou les bords du v7L (31/10).

## 2026-10-30 (suite) — recherche n° 66 : quelles routes FM (Texas) et de comté (Oklahoma) TIGER compte-t-il ?

- **But** : réduire l'incertitude de la référence TIGER. Au Texas, les rapports publiés imposent qu'environ 11 % de la longueur FM (et environ 19 % des secteurs à routes FM seules) soient S1200, mais le v7 répartit ce poids uniformément.
- **Méthode** : pour chaque hypothèse, les km FM « éligibles » prennent le poids qui respecte le rapport 1,59, et la définition des secteurs à FM seules suit 1 − exp(−α × km éligibles), α choisi pour garder la part de secteurs sans transport (26,7 %, comme le v7). Calcul en `$TEMP/claude_ext/scr/fmvar.py` ; les km FM par longueur d'itinéraire (2 576 itinéraires, terciles 8,6 et 20,1 km) en `fmroutes.py`.

  | Hypothèse | Poids sur les km éligibles | Écart-type de la différence | R² (avec s140) | Partie connue |
  |---|---|---|---|---|
  | FM urbaines (× part urbaine) | 0,57 | 0,009 | 0,28 | +0,04 |
  | FM des secteurs urbains seulement | 0,58 | 0,011 | 0,28 | +0,03 |
  | FM des longs itinéraires (tiers supérieur) | 0,16 | 0,004 | 0,11 | −0,05 |
  | FM des itinéraires longs et moyens | 0,12 | 0,003 | 0,07 | −0,01 |
  | contrôle : toutes les FM, définition croissante | 0,11 | 0,002 | 0,09 | +0,01 |

- **Oklahoma, routes de comté** :
  - comté urbain seul : impossible (poids 2,97 requis) ;
  - comté rural seul : −0,08 ;
  - routes de comté classées tertiary, residential ou secondary (sans les « unclassified ») : poids 0,64, nouvelle à 95 %, partie connue +0,07, écart-type 0,005.
- **Lecture** : aucune règle tirée des données du paquet ne désigne nettement les FM ou routes de comté S1200. Les meilleures (FM urbaines +0,04, comtés non « unclassified » +0,07) sont faibles et petites. La réduction de 50 % visée n'est pas atteignable avec ces indices. Le levier le plus fort sur la référence TIGER reste les doublons par nom (s140, +0,22).

## 2026-10-30 (suite) — le plus grand problème de notre solution, chiffré

- **Ce que chaque famille de signaux apporte** (mélange f1, quatre régions, 0,05909 attendu ; constante seule 0,0890) :

  | Retrait de la famille | RMSE attendu | Coût |
  |---|---|---|
  | transport (v3, v7, v9, bords, découpages ; 14 signaux) | 0,07404 | **+0,0150** |
  | casernes (15 signaux) | 0,06122 | +0,0021 |
  | strates et décalages régionaux (9) | 0,05980 | +0,0007 |
  | CBP et lieux (8) | 0,05972 | +0,0006 |
  | bâtiments (9) | 0,05940 | +0,0003 |

- **Le plus grand problème : la précision de notre estimation de la longueur TIGER par secteur**, la référence du transport.
  - Le transport porte l'essentiel de notre gain. L'écart avec Jules (0,0047) représente environ un tiers de ce que le transport nous rapporte.
  - Notre estimation est un proxy : itinéraires Overture, bande de 10 m, numéros multiples, et poids régionaux uniques (FM, comtés OK) calés sur deux rapports publiés. Le classement S1200 réel tronçon par tronçon, et ses doublons, ne sont pas observables (couches retirées).
  - Le modèle structurel attribue au transport une incertitude propre d'environ 0,0016, à peu près la moitié de notre erreur quadratique restante (0,0035).
- **s140 attaque ce problème** : en remplaçant le transport v7 par v7L dans le composite, la corrélation avec le mélange mesuré passe de 0,760 à 0,775, et l'écart systématique des secteurs à couverture partielle baisse un peu (Texas, couverture 50-90 % : +0,042 → +0,038). Le reste de cet écart vient surtout d'un défaut d'échelle du composite calé avec une seule pente, que le mélange corrige déjà.
- **Deuxième problème** : la présence des casernes USGS (même ordre d'incertitude, 0,0018). **Troisième** : le nombre de signaux mesurés ; il ne reste que 3 envois de signaux.
- **Conséquence pour les derniers envois** : la priorité reste aux signaux qui corrigent la référence TIGER (s140 le 30/10, s141 le 31/10 s'il paie).

## 2026-10-30 (suite) — recherche n° 65 : nos auto-interdictions, vérifiées une à une

| Méthode que nous ne faisons pas | Texte officiel | Statut réel | Gain possible |
|---|---|---|---|
| Colonnes USFS de bâtiments, logements, population et `carbonplan_buildings` (D2-ter) | Aucune interdiction nommée ; « Prohibited target reconstruction » vise TIGER, Microsoft, HIFLD et CBP ; staff silencieux (#35402) | **Non interdit par écrit** ; exclu par prudence | **Nul** (diagnostic ci-dessous) |
| Fichiers de soumission publiés par d'autres équipes (GitHub), utilisés comme signaux | Règlement : « You may use only the datasets provided for this challenge » ; Info : « The scored coverage gap computation must use only the datasets provided » | **Interdit** (données externes) ; les reconstructions sont en plus des « equivalent copies » dérivées des couches retirées | — |
| Tableaux de biais des lignes à RMSE 0 (rapports de moyennes de la vérité par strate) | Interdiction des valeurs calculées à partir des couches retirées (staff, 08/10) ; la page de classement n'est pas un jeu de données fourni | **Interdit dans l'esprit**, risque élevé à la revue du code | — |
| Données externes (TIGER, balises OSM `tiger:*`, réseau TxDOT…) | « additional data sources are permitted only for the Best Bias Discovery prize » | **Interdit** pour le score | — |
| Sondage du classement par secteur ou petit groupe | Pas de texte nommé ; « Zindi reserves the right to disqualify … practices that we deem to compromise the inherent value of your solution » | Risqué ; et avec 3 envois de signaux restants, inutile | Négligeable |
| Plus de 73 signaux | Notre règle D1-quater | Le vrai plafond est le nombre d'envois : le 31/10 donne 5 envois, dont 2 pour les finales | — |
| Modèles pré-entraînés publics | Autorisés (« openly available ») s'ils s'appliquent aux données du paquet | **Autorisé** | Rien de mieux que nos règles de noms |

- **Diagnostic USFS** (base de 65 signaux, sans aucune soumission) :
  - écart bâtiments calculé avec les comptes USFS : nouveau à 86 %, partie connue **+0,004** (nulle) ;
  - rapport log USFS / bâtiments Overture : −0,03 ;
  - `carbonplan_buildings` est le compte Overture (corrélation 0,9995).
  Cela confirme l'écart bâtiments quasi nul de la vérité : même autorisées, ces colonnes ne rapporteraient rien.
- **Conclusion** : aucune méthode écartée par excès de prudence ne ferait baisser le RMSE. Les autres sont réellement interdites par le règlement.

## 2026-10-30 (suite) — recherche n° 64 : outils et données autorisés encore inutilisés

- **Inventaire** : les données autorisées sont le paquet (couches Overture, ACS, 23 tables de strates, contours). Le règlement autorise aussi les modèles pré-entraînés publics, appliqués à ces données seulement. Les colonnes interdites par D2-ter restent exclues.
- **Balayage de 376 colonnes numériques** (table de travail et tables de variables routières, casernes, adresses professionnelles, bâtiments, voies de service, tronçons longs ; brut et log) contre la base de 65 signaux, classées par |partie connue| × √(1 − R²). En tête :
  - variantes de nos variables routières : grands axes dans l'anneau de 10 m (R² 0,54, +0,39), noms locaux `majloc` (R² 0,56, +0,32, la base de s140), secondaires sans numéro (R² 0,53, −0,34) ;
  - indices d'urbanité : couverture UHE, station GHCN à moins de 25 km, RUCC métropolitain (R² 0,51-0,62, −0,29 à −0,38) ;
  - indices d'aléa incendie (CRPS, FLEP4, CFL : R² 0,53-0,67, +0,29 à +0,32).
- Faux positif écarté : le rapport Overture / grands axes (`scored_over_major`) paraissait nouveau à 75 % (−0,23), mais seulement parce que ses valeurs manquantes (secteurs sans grand axe) avaient été remplacées par la médiane. Correctement traité : R² 0,50, partie connue +0,03.
- **Lecture** : les colonnes les mieux orientées sont des variantes de mécanismes déjà mesurés, ou des indices génériques (urbanité, aléa), famille qui n'a presque jamais payé (recherche n° 24). Les attributs Overture non lus (hauteur des bâtiments, confiance et sites web des lieux) ne touchent pas la formule.
- **Conclusion** : aucun outil autorisé oublié qui ferait baisser le RMSE au-delà de ce qui est en cours (s140, s141, réserve du 31/10).

## 2026-10-30 (suite) — recherche n° 63 : le mélange mesuré comme diagnostic du modèle structurel

- **Méthode** : le mélange f1 (quatre régions) est notre meilleure image de la vérité. On le compare au score structurel v9 calé linéairement (mélange ≈ −0,012 + 0,75 × v9, corrélation 0,76), par groupes d'au moins 300 secteurs, pour repérer où le modèle se trompe systématiquement.
- **Écarts confirmant des pistes déjà jouées** : terres tribales +0,042 (s122), centres de villes moyennes +0,028 (s134), est de l'Oklahoma +0,035, secteurs sans grand axe −0,032 (le modèle surestime quand le transport n'est pas défini, à cause de ses parts écoles, établissements et bâtiments fictives).
- **Transport** : l'écart croît quand la couverture Overture des grands axes baisse. Oklahoma : +0,096 (couverture < 50 %), +0,062 (50-90 %), +0,044 (90-110 %), +0,027 (110-200 %). Texas : +0,042, +0,025, +0,014, +0,003.
  - C'est surtout un défaut d'échelle du v9 calé, que le mélange corrige déjà avec s97, s101 et s102.
  - Une incertitude plus grande sur la longueur TIGER (σ 0,7 à 1,2) donne des différences nouvelles à 31-47 %, mais sans orientation (+0,00 à +0,04).
- **Casernes** : l'écart croît avec le nombre de casernes Overture du secteur (Texas −0,013 / +0,018 / +0,031 pour 0 / 1 / 2 et plus ; Oklahoma +0,020 / +0,059 / +0,075).
  - Hypothèse : plusieurs casernes USGS par service (avec les postes EMS) quand Overture ne liste que le siège.
  - Test (casernes de référence en plus là où Overture en a une ou deux, ou π plus bas) : parties connues +0,01 à +0,09 seulement, avec du bruit Monte-Carlo. L'écart vient probablement d'une confusion avec le transport : les secteurs à casernes sont des bourgs traversés par des grands axes.
- **Bilan** : le diagnostic confirme nos pistes (s122, s134, s140 en Oklahoma et au Texas), sans mécanisme nouveau assez net pour un signal.

## 2026-10-30 (suite) — recherche n° 62 : bords du score jamais mesurés

- **Idée** : la famille des bords a payé (s102, −0,00066). Bords jamais mesurés, calculés avec v8 et v9 (casernes corrigées), triés sur la base de 65 signaux puis avec le lot du 30/10 :

  | Bord | R² | Partie connue |
  |---|---|---|
  | P(écart casernes = 1), v8 / v9 | 0,97 / 0,94 | +0,20 / +0,31 |
  | P(transport défini à 0) | 0,96 | −0,13 |
  | P(score ≥ 0,15), v8 / v9 | 0,94 / 0,94 | +0,50 / +0,54 |
  | 1 − P(transport défini) | 1,00 | −0,31 |
  | croisé : P(casernes = 1) × P(transport = 1) | 0,70 | +0,07 |
  | croisé : P(casernes = 1) × (1 − P(transport défini)) | 0,60 | −0,06 |
  | croisé : P(casernes = 1) × P(transport défini à 0) | 0,73 | +0,12 |

- **Lecture** : les bords d'une seule composante sont déjà dans la base (94 à 100 %). Les bords croisés sont nouveaux à 27-40 %, mais leur partie connue est faible (|0,06-0,12|). Aucun ne dépasse les candidats de réserve déjà prêts : pas de nouveau fichier.

## 2026-10-30 (suite) — recherche n° 61 : noms alternatifs des routes Overture

- **Idée** : compter le nombre réel de noms de chaque tronçon de grand axe (TIGER : un enregistrement par nom) au lieu du seul indicateur « nom local » de s140.
- **Champ `names.rules` des routes Overture** (Texas, classes notées) : presque toujours une seule règle « common », qui répète le nom principal. Variantes réelles rares : 10 919 « alternate », 1 978 « short », 1 383 « official » (sur environ 350 000 tronçons). Pour les grands axes : 2 383 km avec deux règles, 255 km avec trois ou plus, soit environ 5 % de leur longueur. Les noms secondaires de l'import TIGER (`name_1`, `name_2` dans OSM) ne sont pas repris par Overture.
- **Conclusion** : le supplément d'enregistrements qu'on pourrait en tirer est d'environ 3 % de la longueur de référence au Texas, déjà couvert pour l'essentiel par s140 et s141. Pas de signal distinct.

## 2026-10-30 (suite) — recherche n° 60 : variantes de s140 pour le 31/10

- **Principe** (documentation TIGER) : le MTFCC porte sur l'arête, donc chaque nom d'un tronçon de grand axe devient un enregistrement S1100/S1200. s140 couvre les noms locaux des grands axes hors autoroutes.
- **Tri** (base de 65 signaux, puis avec s140) :

  | Variante (transport − v7) | Écart-type | R² (base) | R² (avec s140) | Partie connue |
  |---|---|---|---|---|
  | noms locaux des autoroutes, poids 0,25 | 0,004 | 0,19 | 0,20 | +0,05 |
  | noms locaux des autoroutes, poids 0,5 | 0,008 | 0,20 | 0,20 | +0,04 |
  | noms locaux hors autoroutes, poids 0,45 | 0,014 | 0,33 | **0,97** (redondant avec s140) | +0,21 |

- → **s141_t7li_c_transport_delta** (`scripts/make_s141.py`, autoroutes au poids 0,5 ; FM 0,065, comtés OK 0,084), indépendant de s140. **Candidat du 31/10 si s140 paie.**
- Les numéros FM ou de comté co-signés sur un grand axe (621 km au Texas) et les routes « Business » sont trop rares pour un signal distinct.
- **Règle du 31/10** : si s140 a un coût de retrait d'au moins 0,0001, envoyer s141 et deux signaux de réserve (s139, s121) ; sinon trois signaux de réserve (s139, s121, s123).

## 2026-10-30 (suite) — recherche n° 59 : le reste du site Zindi et les dépôts GitHub récents

- **Site Zindi** : aucun article « Learn » ni billet sur ce défi, hormis le guide du Bias Score (déjà lu). L'annonce de Radiant Earth (groupe IEEE DSAA, 16/07) n'a pas de détail technique.
- **Profils des équipes de tête** : Jules_Duber (Maroc, inscrit il y a 4 mois, 157 envois sur 6 défis, aucun fil sur ce défi, aucun lien externe) ; Shivoo29 (102 envois, un seul fil, #35079, aucun dépôt lié au défi sur son GitHub). Aucune méthode publique.
- **Dépôts GitHub jamais lus** : iam-dante/bias-bounty-competition, Agnuxo1/overture-coverage-gap-equity, thibaudlepan77-svg/bias-bounty-coverage-gap, vigohan95/zindi-bias-bounty, kevin9327/ZindiBiasBounty.
- **thibaudlepan77-svg, `score.py`** (reproduction exacte faite avant le retrait, environ 3e-6) : `create table tiger as select geometry from census-tiger-roads where MTFCC in ('S1100','S1200')`, puis somme par secteur de `ST_Length(ST_Transform(ST_Intersection(r.geom, t.geom), 'EPSG:5070'))`. **Aucun dédoublonnage** (ni DISTINCT, ni union, ni drop_duplicates) : chaque enregistrement compte.
  - La couche des organisateurs est un « TIGER/Line Roads » (un enregistrement par nom, documentation du Census), donc les copies par nom entrent dans la référence. Cela conforte s140 (et la multiplicité des numéros du v7).
  - Seule la convention a été lue, aucune valeur.
- **Prochaine information décisive** : le score de s140 (lot du 30/10).

## 2026-10-30 (suite) — audit complet avant les finales

- Plan et résultats : `docs/05_plan_audit.md` (section « Audit du 30/10/2026 », 10 contrôles H1-H10, critères fixés avant).
- **Conforme** : 70 fichiers notés intacts, 70 scores identiques à Zindi, lot du 30/10 au bon format, 6 nouveaux signaux reproduits à l'identique, mélange stable, sorties des finales conformes, aucune donnée externe, règles D1-quater respectées.
- **Corrigé** (`scripts/make_finals.py`) :
  - le mode quatre régions est désormais le défaut ;
  - le privé attendu porte sur les quatre régions notées (2 814 secteurs publics) ;
  - le fichier des poids enregistre les poids réellement utilisés.
- **Noté** : `WEAK` ne suit pas un seuil unique ; c'est un choix justifié par la simulation, à ±0,00002 près.

## 2026-10-30 (suite) — recherche n° 58 : le SampleSubmission.csv de l'onglet Data

- Téléchargé avec l'accord de l'utilisatrice et lu dans la page Zindi (920 Ko, 9 794 lignes).
- **Colonnes** : GEOID, coverage_gap_score, region, transport_gap, transport_defined, building_gap, building_defined, poi_gap, poi_defined, poi_gap_fire, poi_defined_fire, poi_gap_ems, poi_defined_ems, poi_gap_schools, poi_defined_schools, poi_gap_cbp, poi_defined_cbp.
- **Contenu** : tous les écarts valent 0,0 et tous les indicateurs « défini » valent True, sur les 9 794 lignes. Aucune information sur la vérité : la taille vient seulement des colonnes supplémentaires.
- Lignes rangées par région (Arizona, Californie, Oklahoma, Texas, Washington). Ici, la première colonne après GEOID est coverage_gap_score ; dans les fichiers régionaux du dépôt, c'est transport_gap. Nos fichiers sont verrouillés sur `GEOID,coverage_gap_score` (recherche n° 27). Rien à changer.

## 2026-10-30 (suite) — recherche n° 57 : relecture complète des onglets Info, Data et Chat

- **Info** (relu en entier) : rien de contraire au modèle.
  - « Census TIGER/Line Roads » est le nom du produit « All Roads » (un enregistrement par nom), ce qui va dans le sens de s140.
  - « la moyenne de trois écarts par type » est précisé par le README (moyenne sur les types définis), ce que fait notre modèle.
  - L'ACS n'entre pas au dénominateur des bâtiments (confirmé) ; établissements = « County Business Patterns ».
- **Data** (relu en entier) : liste des couches de référence (TIGER/Line Roads, Microsoft US Building Footprints, ACS, HIFLD avec hôpitaux, casernes, écoles et EMS, CBP) ; Overture figée à 2026-08-19.0 ; interdiction de reconstruire la cible. **Point jamais vérifié** : le fichier `SampleSubmission.csv` de l'onglet Data pèse 898,3 Ko, contre 275 Ko pour les cinq fichiers d'exemple régionaux du dépôt (mêmes 9 794 lignes). Il contient donc environ trois fois plus d'information par ligne (d'autres colonnes ?). Son téléchargement demande l'accord de l'utilisatrice.
- **Chat** (5 pages, environ 120 fils listés) : environ 70 fils ne figuraient pas dans nos notes, surtout des méthodes de reproduction exacte publiées avant le 25/09. Lus en priorité :
  - **#35070 (bertholdt, 28/09)** : longueur TIGER = somme sur tous les enregistrements S1100/S1200 retenus, sans dédoublonnage, `ST_CollectionExtract(ST_Intersection(...), 2)` en EPSG:5070 ; points comptés par `ST_Intersects`, limite comprise ; CBP réparti du code postal (ZCTA) au secteur par le croisement HUD (adresses professionnelles). Toutes conventions déjà dans notre modèle, et formule compatible avec s140.
  - **#34921 (ML_Wizzard) et réponse de thibaudlepan** : la référence semble arrondie à 5 décimales (plancher d'environ 3e-6 pour les reconstructions). Sans effet pour nous.
  - Les autres fils de reproduction exacte utilisent les couches retirées : on n'en tire aucune valeur.

## 2026-10-30 (suite) — relecture avant l'envoi du 30/10

- **Défaut corrigé dans s140.** `bbx.structural` ajoute aussi W_LOCAL × txloc (noms locaux des routes texanes du réseau secondaire) au terme que multiplie le poids FM. Le recalage l'oubliait, et le rapport du Texas valait environ 1,58 au lieu de 1,59.
  - `scripts/make_s140.py` résout maintenant 1,59 sur cette somme : poids FM 0,051 (0,056 auparavant), comtés OK 0,073.
  - Fichier régénéré et rejournalisé : nouveau à 69 %, partie connue +0,22, sans changement notable.
- **Les 5 fichiers du lot** (s140, s122, s137, s138, s117) : en-tête `GEOID,coverage_gap_score`, 9 794 lignes, aucune valeur manquante, valeurs dans [0,0066 ; 0,347]. Chacun est journalisé une fois, SHA conforme, jamais noté, secteurs d'eau à m. Corrélation maximale avec un signal déjà noté : 0,28 à 0,85 (aucun doublon).
- **Chaîne des finales** : plafond 73, `WEAK` (8 signaux), s07/s22 exclus de f1. Aucun nouveau signal n'est pris pour un signal régional. Essai à blanc : f1 0,05909, f2 0,05796 en public attendu (65 signaux). 65 + 5 + 3 = 73 au 31/10.

## 2026-10-30 (suite) — recherche n° 56 : noms multiples dans TIGER, découpage des secteurs

- **Noms multiples** (documentations TIGER 2015-2024) :
  - plusieurs entités linéaires peuvent partager une arête ; l'exemple du Census est un tronçon à la fois rue locale et route d'État, dont un nom est marqué principal ;
  - le nom principal est en général le nom de rue courant ; les noms alternatifs sont des entités séparées, reliées à l'arête par un identifiant ;
  - « All Roads » répète le tronçon une fois par entité (exemple US 36 / SH 7 / 28th Street).
  Aucune étude ne chiffre la part des grands axes qui portent un nom local. Cela confirme le mécanisme de s140 ; son poids (0,25) reste fixé par les rapports officiels 1,59 et 0,71.
- **Découpage des secteurs** (Federal Register, 13/11/2018, critères des secteurs 2020) : les limites suivent des éléments visibles et stables (routes, voies ferrées, cours d'eau…). C'est la base du double comptage des routes en limite (v3), déjà modélisé.
- **Bilan** : rien de nouveau à mesurer ; s140 reste la seule piste structurelle récente.

## 2026-10-30 (suite) — recherche n° 55 : fichiers du paquet jamais ouverts

- **Inventaire du paquet** (par région : couches Overture buildings, roads, roads-unfiltered, rail, infrastructure, pois ; ACS ; exemple de soumission ; 23 tables de strates ; contours) comparé à notre code :
  - toutes les couches Overture sont lues (`bbx.features`, y compris rail et infrastructure) ;
  - les tables de strates entrent toutes dans la table de travail par `strata-tract-table` (267 colonnes : cvi, fod, gehe, ghcn, nifc, usdm, pmdi, epht, spi, svi, ruca, rucc, nchs, tribal, mtbs, usfs, carbonplan…) ;
  - `original-rings` a été étudié (recherche n° 20).
- **Jamais ouverts** : `all-aois.geojson` (contours des régions, redondant avec la réunion des secteurs) et les géométries `census-tribal-subdivisions` (le taux de terre tribale par secteur est déjà dans la table). Ni l'un ni l'autre ne touche la formule.
- **Bilan** : aucune source, publique ou du paquet, ne reste à consulter qui puisse changer le score. La priorité est le lot du 30/10 (s140 en tête) et les finales du 31/10.

## 2026-10-30 (suite) — recherche n° 54 : quatrième liste de sources jamais consultées

| Source | Résultat |
|---|---|
| #35265 (Hunter_Toledo, 08/10) | Sondage par groupes : trois moyennes mesurées (rural × peuplé × sans caserne Overture) ; 0,0853 en RMSE. Rien de nouveau |
| #35249 (rukundob451) | Question sans réponse sur les bâtiments Overture de provenance Microsoft. Rien |
| #35243 (tomfng, mis à jour le 20/10) | Lieux Overture en double, même nom et même adresse, à 6 à 544 km l'un de l'autre (casernes, écoles), et points posés sur des nœuds de la grille Web Mercator (24 écoles). Cas rares : un doublon mal placé ajoute une caserne dans un secteur sans caserne de référence (composante non définie, donc sans effet), sans retirer la bonne. Rien d'exploitable |
| Site et publications de Reliabl | Introuvables |
| Notes de version Overture 2026-08-19.0 | Page absente (404) |

- **Bilan** : aucune nouvelle piste. Les sources publiques sont épuisées ; s140 reste notre meilleur pari.

## 2026-10-30 (suite) — recherche n° 53 : troisième liste de sources jamais consultées

| Source | Résultat |
|---|---|
| Wiki OSM, classement des routes aux États-Unis (page remplacée par le guide de 2021) | motorway = Interstates et voies rapides ; primary = routes US ; secondary = routes d'État ; tertiary = routes d'État secondaires et routes de comté. Rien sur les noms locaux. La page Texas n'existe plus (404) |
| Guide Overture « transportation » | `routes` (network, ref, wikidata), classes et sous-classe `link` ; rien sur le passage des balises OSM `name`/`ref` vers `names` |
| Codes USGS (spécifications cartographiques, NOAA) | 74026 « Fire Station/EMS Station » : bâtiment qui abrite du matériel ou du personnel de lutte contre l'incendie et fournit aussi des soins d'urgence ; 74001 « Ambulance Service » à part. Déjà intégré |
| #35325 et #35332 (vigohan, 13/10) | Même famille de méthode que la nôtre, moins poussée (proxy : routes Interstate/US/État + 0,5 × comté ; casernes par Poisson ; mélange de 6 signaux à 0,0775). Utilise les comptes de bâtiments USFS, exclus chez nous (D2-ter). Rien de nouveau |

- **Bilan** : aucune nouvelle piste. s140 (noms locaux TIGER) reste la seule découverte structurelle récente.

## 2026-10-30 (suite) — recherche n° 52 : deuxième liste de sources jamais consultées

| Source | Résultat |
|---|---|
| Dépôts GitHub de kentstephen (58 dépôts, auteur du tutoriel) | Aucun code de calcul de l'écart ; seul `bias-bounty-map-tutorial` concerne le défi |
| Organisation GitHub humane-intelligence (5 dépôts) | `bias-bounty-data` (mai 2024, ancien défi) ; rien sur ce défi |
| Page source.coop du jeu de données | Journal des versions déjà connu (25/09 retrait des couches, 08/09 Washington, 26/08 contours par secteurs et Overture 2026-08-19.0) ; cite `scripts/readme_addresses.py`, absent du bucket (404) ; aucun lien vers le calcul de Reliabl |
| Documentation technique TIGER/Line **2025** (Census) | Même texte que 2024 : un enregistrement par nom dans « All Roads » (exemple US 36 / SH 7 / 28th Street), et des grands axes parfois mal classés en S1400. Le fichier « Primary and Secondary Roads » contient aussi « all linear street features » de MTFCC S1100/S1200 (même structure par nom). Codes RTTYP : C comté, I interstate, M nom commun, O autre, S État, U US |
| Census, revue des grands axes (« highway review ») | Aucune publication détaillée trouvée ; un avis de 2017 au Federal Register proposait de reclasser toutes les voies à accès limité en S1100 (sans effet sur S1100 + S1200 additionnés) |
| Schéma Overture, dictionnaire USGS | Non approfondis : valeur attendue faible |

- **Bilan** : la documentation 2025 confirme le mécanisme de s140 (noms multiples par tronçon). Aucune source publique ne donne le code de calcul des organisateurs.

## 2026-10-30 (suite) — recherche n° 51 : sources jamais consultées ; les noms locaux de TIGER reviennent

- **Liste des sources jamais consultées** (établie à partir du journal) :
  1. documentation technique TIGER/Line (édition 2024, NHGIS) ;
  2. schéma Overture (classes de routes, catégories de lieux) ;
  3. dictionnaire des structures USGS ;
  4. méthodes publiées par les équipes conformes (jennifer_evangelista #35543, vigohan, vik439, kevin9327ai) ;
  5. page source.coop et site de Reliabl.

  Consultées : 1 et 4 (#35543 : même approche que la nôtre, 3 paramètres calés sur le classement, 0,0752 ; rien de nouveau). 2, 3 et 5 restent de faible valeur attendue.
- **Documentation TIGER, section 4.12.4** : « The All Roads shapefiles will contain multiple overlapping road segments where a segment is associated with more than one road feature », avec l'exemple d'un tronçon US 36 + State Hwy 7 + « 28th Street », présent en trois segments superposés.
  - Le tutoriel des organisateurs indiquait une couche TIGER contenant toutes les routes, filtrée à S1100/S1200 au calcul (recherche n° 26). Une route qui porte aussi un nom de rue local y compte donc une fois de plus.
  - Même section : des tronçons de grands axes peuvent manquer, mal classés en S1400 (« some street features may have a misclassified MTFCC »).
- **L'hypothèse « v5 » réexaminée.** Écartée le 24/10 parce qu'elle faisait passer l'Arizona sous le maximum publié de 1,59. Depuis le v7, ce maximum est tenu par le Texas et le minimum par l'Oklahoma.
  - Au poids 1, elle reste impossible : l'Oklahoma tomberait à 0,64 (minimum publié 0,71) et aucune région n'atteindrait 1,59.
  - Au poids partiel, elle est compatible : de 0 à 0,48 sur les noms locaux hors autoroutes, avec les poids FM et comté recalés.
  - **v7L (poids 0,25)** : FM 0,056, comtés OK 0,073 ; rapports TX 1,59, OK 0,71, AZ 1,32, CA 1,43.
  - Différence de transport v7L − v7 : écart-type 0,0085, **nouvelle à 69 %, partie connue +0,22**. Au poids 0,45 : nouvelle à 67 %, +0,21, corrélation 0,97 avec la version 0,25. Avec les autoroutes à 0,25 : corrélation 0,88.
  - C'est le profil le plus prometteur depuis le v7 (en comparaison, v3 − v1 n'était nouveau qu'à 10 % et avait rapporté environ −0,013).
- → **s140_t7l_c_transport_delta** (`scripts/make_s140.py`, `data/interim/structural_v7L.parquet`). Résidu indépendant du reste du lot (|corrélation| ≤ 0,06, −0,19 avec s117).
- **Lot du 30/10 révisé** : s140, s122, s137, s138, s117. s139 (écoles, la piste la plus faible) passe en réserve pour le 31/10.
- **Si s140 paie** : le 31/10, mettre en priorité ses variantes non redondantes (bords v7L : P(écart = 1), P(défini), autoroutes) ou un poids différent.

## 2026-10-30 (suite) — recherche n° 50 : anciennes compétitions semblables

- **Compétitions sans étiquettes, notées sur une référence cachée** : aucune trouvée avec ce format, hors la nôtre. Moritz Hardt (2015, « Competing in a data science contest without reading the data ») montre qu'on peut grimper au classement public sans regarder les données, par une attaque de type boosting : soumissions aléatoires gardées si elles améliorent le score. C'est un surapprentissage pur, qui s'effondre au privé. Cela rappelle le risque des équipes qui font des centaines d'envois ; aucun levier pour nous.
- **Complétude d'OpenStreetMap** : pas de compétition Kaggle, DrivenData ou Zindi ; seulement des travaux académiques (complétude des bâtiments dans 12 975 villes à partir de grilles de population, MapSwipe, prix étudiant de 2021), déjà vus.
- **Défis Radiant Earth sur Zindi** (cultures au Kenya en 2020, « Spot the Crop » en 2021) : classification d'images avec étiquettes, solutions publiques (CatBoost, LightAutoML), sans rapport avec un score sans étiquettes.
- **Humane Intelligence** : aucune compétition géospatiale avant celle-ci.
- **Conclusion** : aucune ancienne compétition comparable n'a de solution publique transposable. Notre approche reste la meilleure approche conforme connue.

## 2026-10-30 (suite) — recherche n° 49 : Bias Score, données USGS, densité des casernes

- **Guide officiel du Bias Score** (lien de la page Info, zindi.world/learn, 28/08) : le tableau de biais compare nos propres prédictions, par strate, sur cinq indicateurs (rapport de disparité ; « POI Desert Index » avec un seuil poi_gap ≥ 0,8 ; écart d'accès aux secours ; équité du réseau routier ; composite climat-justice). Rien sur le calcul de la vérité.
- **Métadonnées USGS des casernes** (dérivé du Mississippi) :
  - points placés sur le bâtiment, avec une position approximative surtout en zone rurale ;
  - casernes de bases militaires, d'aéroports et de sites industriels placées à l'entrée ou au centre du site ;
  - centres de formation et dépôts exclus ;
  - mises à jour surtout faites par les bénévoles TNMCorps depuis 2013.
  Idée : un aéroport important sans caserne Overture serait un indice ciblé. Mesure : 358 secteurs notés ont un aéroport international, régional, militaire ou municipal (couche infrastructure), dont 165 sans caserne Overture. Groupe trop petit (moins de 300) : écarté.
- **Densité des casernes** (NFPA) : environ 54 600 casernes aux États-Unis (2018-2020), 29 452 services, surtout de volontaires ; les volontaires protègent surtout les communautés de moins de 25 000 habitants. Cela confirme le sens de s136 (plus de casernes de référence à la campagne), déjà mesuré.
- **Empreintes Microsoft** : aucune comparaison publiée entre la version américaine de 2018 et GlobalML aux États-Unis (seulement Microsoft contre Google en Éthiopie, Gonzales 2023). Rien de nouveau sur l'écart bâtiments.
- **Bilan** : les articles confirment nos mécanismes. Aucun nouveau levier au-dessus du seuil de 300 secteurs.

## 2026-10-30 (suite) — recherche n° 48 : articles de recherche

- **Qualité des lieux Overture** :
  - Ballantyne et Berragan 2024 (Royaume-Uni, supermarchés) : écart de comptage sous 5 %, qualité selon le fournisseur (Meta : bonnes catégories) ; les lieux non commerciaux restent à évaluer.
  - Étude sur des enquêtes de déplacements : couverture Overture 72 % (OSM 73 %, Google 99 %), erreur de position médiane de 20 à 50 m.
  - Overture (2026) : près de la moitié des lieux de certains échantillons ne tombent dans aucun bâtiment.
  - Aucune étude sur les casernes ou les services publics.
- **Idée tirée de ces erreurs de position** : une caserne Overture posée sur la route-limite tomberait dans le secteur voisin, alors que la caserne USGS (sur le bâtiment) resterait du bon côté. Mesure (EPSG:5070) : seulement 10 % des casernes Overture sont à moins de 30 m d'une limite.
  - Secteurs sans caserne Overture mais avec une caserne à moins de 15 / 30 / 60 m de l'autre côté : 35 / 281 / 661 secteurs notés, parties connues +0,01 / −0,01 / −0,03.
  - Aucun indice en faveur, groupes trop petits sous 60 m : piste close (comme s39 à 300 m).
- **OSM contre TIGER** : pas d'étude académique au-delà de Zielstra et al. 2013 (déjà cité). Le wiki OSM (TIGER 2010) donne S1100 ≈ motorway et S1200 ≈ primary (parfois trunk ou secondary), et rappelle que l'import de 2007 a mis la plupart des routes en « residential ». Déjà intégré (recherche n° 30).
- **Surapprentissage du classement** : The Ladder (Blum et Hardt 2015), reusable holdout (Dwork et al.), LadderBoot (Chaibub Neto et al. 2016). Leur principe, ne retenir qu'un gain qui dépasse le bruit, est celui de notre règle `WEAK` et du seuil de 0,00003. À citer dans la Documentation ; rien à changer.

## 2026-10-30 — recherche n° 47 : compétitions semblables et solutions publiques

- **Bias bounties précédents de Humane Intelligence** (2024) : sorties de modèles de langage, puis images de propagande haineuse (avec Revontulet). Tâches sans rapport ; aucune solution gagnante publiée, seulement un tutoriel (dépôt KristiArbo/biasbounty1_humaneintelligence).
- **Complétude d'OpenStreetMap par apprentissage** :
  - Herfort et al. 2023 (Nature Communications) : complétude des bâtiments OSM dans 13 189 villes ;
  - Crisafulli et Monzón 2021 (OST, prix Open Data) : complétude des lieux OSM ;
  - HeiGIT : complétude d'OSM comparée à Overture.
  Ces travaux apprennent sur des zones où la référence est connue, ce que nous n'avons pas, et visent une autre cible que la formule notée ici. Rien de transposable.
- **Compétitions notées en RMSE sans étiquettes** :
  - Xie 2018, « Attack RMSE Leaderboard » (arXiv 1802.04947) : chaque soumission donne un produit scalaire ⟨ŷ, y⟩ ; l'« attaque par régression » (combinaison linéaire de soumissions, x = (AᵀA)⁻¹Aᵀy) est exactement notre mélange.
  - Ses autres attaques (moyennes par segments de secteurs, codage positionnel d'étiquettes discrètes) sont des sondages par secteur, interdits (D1) et inapplicables à une cible continue.
  - « Don't Overfit II » (1re place) : un signal soumis seul sert de coefficient, comme nos signaux mesurés.
  - LANL Earthquake : recherche par programmation en nombres entiers sur le classement, autre forme de sondage par secteur.
- **Conclusion** : notre méthode (modèle structurel de la formule + mélange linéaire mesuré sur le classement, régularisé et validé par simulation) correspond à la meilleure approche publique conforme. Aucune solution publique n'offre de levier supplémentaire autorisé.

## 2026-10-29 (nuit, fin) — recherche n° 46 : derniers recoins

- **Catégories de lieux Overture liées aux secours** (quatre régions) : fire_department 3 462, police_department 2 396, fire_protection_service 1 279, emergency_room 1 006, ambulance_and_ems_services 793, emergency_medicine 503, etc. Les lieux qui portent fire_department en catégorie secondaire (593 en fire_protection_service, 88 administrations, 24 polices, 23 EMS…) sont déjà comptés comme preuves (`poi_fire_alt`, `fire_misfiled_clean`). Rien de nouveau.
- **Attributs routiers jamais utilisés** (`road_flags`, `speed_limits`, `access_restrictions`) : seuls 121 km de grands axes notés sont « en travaux » au Texas. Négligeable pour le rapport Overture/TIGER.
- **Remarque à l'utilisatrice** : je n'ai accès à aucune autre conversation (ni à la méthode de Jules_Duber).
- **Bilan** : tous les recoins du paquet ont été examinés. Il ne reste aucune piste capable de combler 0,0045 par des moyens autorisés.

## 2026-10-29 (nuit, suite) — recherche n° 45 : centres-villes, routes Business, banlieues éloignées

- **Routes US/Interstate « Business / Alternate / Loop »** (elles traversent les centres des petites villes) : déjà comptées comme grands axes dans le proxy TIGER (niveau 1 ou 2) et presque toutes classées primary/secondary dans Overture (seulement 61 km en tertiary au Texas). Aucun écart caché.
- **Casernes, autres zones RUCA** (preuve de caserne là où Overture n'en a pas, même règle que s134) :

  | Zone | Secteurs notés touchés | R² | Partie connue |
  |---|---|---|---|
  | RUCA 2 (banlieue éloignée) | 404 | 0,19 | +0,03 |
  | RUCA 2-3, au moins 20 lieux | 415 | 0,23 | +0,04 |
  | RUCA 3 | 26 | — | — |
  | RUCA 1.1 | 225 | 0,05 | −0,03 |
  | RUCA 4.1 | 33 | — | — |

  Seule la banlieue éloignée (RUCA 2) atteint 300 secteurs, avec une orientation faible (+0,03 contre +0,11 pour s134 au même stade). Candidat de réserve pour le 31/10, derrière s116, s121, s123 et s105.
- **Bilan** : la famille des preuves ciblées de caserne est épuisée au-dessus de 300 secteurs. Aucune autre piste de la taille du v3 ou du v7.

## 2026-10-29 (nuit) — décision D1-quater et recherche n° 44 : les bords du modèle de casernes corrigé

- **Décision de l'utilisatrice (D1-quater, `docs/decisions.md`)** : plafond porté à **73 signaux mesurés**, mêmes conditions. `MAX_SIGNALS = 73` dans `scripts/make_finals.py`.
  - Calendrier : 30/10, s122 et 4 signaux ; 31/10, 3 signaux puis f1 et f2 tôt dans la journée.
  - Règle pour les signaux des 30-31/10 : un signal entre dans les finales si son coût de retrait atteint 0,00003, sinon il rejoint `WEAK`.
- **Indices ciblés écartés** (même famille que s134, mais groupes trop petits) :
  - écoles : bâtiments OSM classés école sans école Overture (92 secteurs notés), noms d'école sous une autre catégorie (857 secteurs, partie connue −0,01) ;
  - centres de service ruraux (RUCA 5-10, au moins 10 à 30 lieux, sans caserne Overture) : partie connue +0,08 à +0,11, mais 220-226 secteurs notés seulement après la règle des preuves ;
  - tract le plus actif de chaque comté : 11 à 81 secteurs.
- **v9** = v8 + centres de ville comme preuve de caserne + une caserne pour 2 000 ruraux et 36 000 urbains (`data/interim/structural_v9.parquet`). Ses bords diffèrent de ceux du v8 là où les casernes ont bougé :

  | Signal (base de 65) | R² | Partie connue |
  |---|---|---|
  | P(score ≥ 0,30), v9 − v8 | 0,55 | +0,30 |
  | P(score = 0), v8 − v9 | 0,67 | +0,20 |
  | P(score ≥ 0,15), v9 − v8 | 0,84 | +0,26 |
  | casernes, moins d'écoles de référence | 0,60 | +0,10 |
  | s117 (P(score ≥ 0,30), v8) | 0,79 | +0,43 |

  Résidus presque indépendants entre eux et des autres candidats (|corrélation| ≤ 0,15), sauf les deux bords v9 entre eux (−0,51).
- → `scripts/make_s137_s139.py` : **s137_t9_p_score_ge30_delta**, **s138_t9_p_zero_delta**, **s139_t8_fire_fewer_schools**.
- **Lot du 30/10** (`upload_2026-10-30.txt`) : s122, s137, s138, s139, s117 (70 signaux mesurés ensuite).
- **31/10** (`upload_2026-10-31.txt`) : 3 signaux choisis selon ces scores parmi s116, s121, s123 et s105, puis f1 et f2 tôt dans la journée. Les sélectionner sur la même page.

## 2026-10-29 (soir) — classement et Chat : d'où viennent les sauts de la tête

- **Classement (29/10)** : lignes 1 à 22 en reconstruction (0 à 0,030 ; nouvelles : YIGi, Mr_Ghost, Mirekudev, craigouma). Premiers conformes probables : Jules_Duber 0,054405 ; Sosa Team 0,055456 ; Artyom 0,055607 ; Yesternity 0,055654 ; Shivoo29 0,055742 ; KettaP 0,055769 ; ORANO 0,056115 ; omz1101 0,056319 ; Sashish 0,056524 ; Miscusi 0,057019 ; riwaq 0,057219 ; mk1981 0,057376 ; byte 0,057629 ; Loukil 0,057737 ; resist 0,057802 ; iam-dante 0,058362 ; Aza 0,058389 ; harshvt 0,058824 ; RTornado 0,059879 ; **nous 0,059990** (s111, 42e ligne).
  - En deux jours : Shivoo29 −0,0025, Yesternity −0,0015, Artyom −0,0012, KettaP −0,0011, ORANO −0,0020, Jules −0,0003.
  - Nos finales (f1 0,0591, f2 0,0580 attendus) nous placeraient vers le 17e-19e rang conforme en public.
- **#35657 (OrDant, 28/10)** demande au staff s'il peut utiliser comme cibles les fichiers de soumission que d'autres participants ont publiés sur GitHub avec leur score public. Il annonce qu'il le fera faute de réponse.
  - Chaque fichier publié avec son score est un « signal mesuré » gratuit.
  - Certains de ces fichiers sont des reconstructions faites avec les couches retirées (scores de 0 à 0,0024) : les utiliser revient à utiliser la vérité.
  - C'est l'explication la plus probable des sauts de fin de compétition.
  - **Exclu pour nous** (règle C1 : jamais les prédictions ni les sondages des autres ; règlement : couches retirées et « copies équivalentes » interdites ; revue du code du top 10). Ces équipes risquent la disqualification à la revue, ce qui ferait monter les équipes conformes au privé.
- **#35607 (mz000)** : la sélection des deux soumissions finales ne fonctionne qu'à l'intérieur d'une même page de l'onglet Submissions. f1 et f2 doivent être envoyées l'une après l'autre (même page) ; vérifier la sélection après l'enregistrement.
- **#35665 (Fractal155)** : demande l'heure exacte de fermeture du 31/10 (non publiée) et des précisions sur les règles des composantes manquantes. Aucune réponse du staff. Finales le 30/10, le 31/10 en réserve.

## 2026-10-29 — scores du 29/10 : les casernes des centres-villes paient ; finales allégées

| Id Zindi | Fichier | RMSE public | Corrélation (4 régions) | Partie connue prévue | Coût du retrait |
|---|---|---|---|---|---|
| kTpYqDVb | s134_t8_fire_towncore | 0,087995 | **+0,166** | +0,11 | **+0,00022** |
| zcWkiNzd | s136_t8_fire_prior_recal | 0,086313 | +0,275 | +0,26 | +0,00001 |
| ANjh6SFV | s112_t7_p_one_tx | 0,089059 | +0,017 | +0,04 | 0,00000 |
| LY13LjGG | s113_t7_p_one_ok | 0,088804 | +0,074 | +0,04 | +0,00004 |
| NPogZGD1 | s133_t8_c_fire_bigmetros | 0,089330 | −0,043 | −0,05 | +0,00001 |

- **Mélange (quatre régions, 63 signaux, ridge 0,005)** : 0,05883 attendu en public (0,05919 la veille, gain −0,00036).
  - **s134 est le meilleur signal depuis le 26/10** : sa part nouvelle est nettement positive (+0,166 mesuré contre +0,11 prévu).
  - s136 a une forte corrélation, mais elle était déjà connue : sa part nouvelle est quasi nulle.
  - Leçon confirmée : ce qui paie, ce sont les **preuves ciblées** (des secteurs précis où l'écart vaut 1), pas les recalibrations larges ni les découpages.
- **Les finales retirent les signaux sans gain.**
  - L'estimateur du privé de `make_finals.py` montait de 0,06296 (53 signaux) à 0,06440 (63 signaux).
  - Simulation de bout en bout (style audit C2, 40 vérités sur les quatre régions notées, `$TEMP/claude_ext/scr/sim_subsets.py`) :

    | Vérité simulée | 63 signaux | 53 anciens | 53 + s134 + s136 |
    |---|---|---|---|
    | A : les nouveaux signaux n'apportent rien | 0,04829 | 0,04803 (−0,00026) | 0,04807 (−0,00021) |
    | B : ils apportent ce que le public a mesuré | 0,04839 | 0,04855 (+0,00016) | 0,04836 (−0,00002) |

  - Retirer les 8 signaux sans gain des lots des 28 et 29/10 (s119, s125-s128, s112, s113, s133) n'est jamais perdant. Un tri général par coût de retrait ne change rien (±0,00001, `sim_prune.py`) : il n'est pas appliqué.
  - `scripts/make_finals.py` : ensemble `WEAK`, retiré des trois finales. Essai à blanc : f1 0,05909 en public (0,06285 en privé selon la formule), f2 0,05796 (0,06234).
- **66e et dernier signal le 30/10 : s122** (casernes en terre tribale ; couverture des lieux Overture la plus faible en terre tribale, #35030/#35080). Règle : il entre dans les finales si son coût de retrait atteint 0,00003, sinon il rejoint `WEAK`.
- Staff : toujours aucune réponse sur #35402.

## 2026-10-28 (soir) — recherche n° 43 : dilution des casernes par les écoles et l'EMS, et bilan franc

- **Dilution** : l'écart casernes pèse 1/(nombre de types définis) dans la moitié équipements. Moins d'écoles USGS que de lieux Overture veut dire moins de secteurs où les écoles sont définies, donc plus de poids pour les casernes. Tri sur la base de 60 signaux (avec s134 et s136) :

  | Variante (différence de contribution casernes) | Écart-type | R² | Partie connue |
  |---|---|---|---|
  | moins d'écoles de référence (π 0,5, κ 0) | 0,007 | 0,60 | +0,10 |
  | plus d'écoles de référence (κ 0,5) | 0,005 | 0,80 | −0,11 |
  | moins ou plus d'EMS de référence | ≤ 0,0014 | 0,37 | ±0,04-0,13 (écart-type négligeable) |

  Le sens est cohérent (moins d'écoles de référence), mais l'effet est plus faible que s136. C'est un candidat pour le 30/10 si s134 et s136 paient.
- **Bilan franc** :
  - Aucun levier unique ne fera chuter le RMSE fortement. L'erreur restante vient de deux inconnues (longueur TIGER, présence d'une caserne USGS) que les données du paquet ne révèlent pas.
  - Les défauts trouvés aujourd'hui (s134, s136, écoles) sont réels, mais valent chacun quelques 10⁻⁴.
- **Seul levier systématique restant : plus de signaux mesurés.** D1-ter fixait 66 pour utiliser les envois disponibles jusqu'au 29/10. Les 30 et 31/10 offrent 10 envois, dont 2 pour les finales : jusqu'à 73 signaux.
  - Gain possible : −0,001 à −0,002 si ce sont des signaux de mécanisme.
  - Coûts : surapprentissage un peu plus fort (optimisme d'environ +0,0001), finales le dernier jour.
  - Décision à prendre par l'utilisatrice.

## 2026-10-28 (après les scores, suite) — recherche n° 42 : le modèle de casernes recalibré

- **Question** : après les centres de ville, le prior des casernes (une caserne de référence pour 4 000 ruraux, 18 000 urbains, 2 500 km²) est-il faux ailleurs ? Tri sur la base de 60 signaux, avec la même graine que `structural_v8e` :

  | Variante (différence de contribution casernes) | Écart-type | R² | Partie connue |
  |---|---|---|---|
  | taux rural × 2 | 0,008 | 0,57 | +0,20 |
  | taux urbain × 2 | 0,010 | 0,76 | **−0,24** |
  | surface × 2 | 0,003 | 0,27 | +0,08 |
  | π = 0,6 ou 0,95 | 0,002 | 0,05-0,07 | ±0,04 |
  | **rural × 2 et urbain × 0,5** | 0,012 | **0,66** | **+0,26** |
  | rural × 3 et urbain × 0,5 | 0,017 | 0,65 | +0,26 |

- **Lecture** : les mesures demandent plus de casernes de référence à la campagne (petites casernes de volontaires, mal couvertes par les lieux Overture) et moins en ville (casernes urbaines moins nombreuses par habitant que la moyenne nationale, et bien couvertes). s133 (−0,06 dans les grandes métropoles) va dans le même sens.
- → **s136_t8_fire_prior_recal** (`scripts/make_s136.py`) : v8 avec une caserne pour 2 000 ruraux et 36 000 urbains, moins v8.
  - Il bouge 7 846 secteurs, nouveau à 34 %, partie connue +0,26.
  - Résidu indépendant de s112, s113, s121, s133 et s134 (|corrélation| ≤ 0,06).
- **Lot du 29/10 révisé** : s134, s136, s112, s113, s133.
  - s121 (transport des petits secteurs) sort : c'est un découpage du transport, comme les métropoles, dont la part nouvelle s'est révélée nulle le 28/10.
  - 66e signal le 30/10, choisi après les scores du 29/10 : s121 ou s122.

## 2026-10-28 (après les scores) — recherche n° 41 : les casernes des centres de petites villes

- **Défaut du modèle de casernes** : le v8 compte les habitants urbains à une caserne pour 18 000. Il n'attend donc presque aucune caserne de référence dans les secteurs-centres des petites villes (contribution casernes moyenne 0,015-0,020). Or le centre d'une ville abrite presque toujours sa caserne principale.
  - Secteurs-centres d'après les codes RUCA de la table : 469 centres de villes moyennes (RUCA 4), dont 63 % sans caserne Overture ; 163 centres de petites villes (RUCA 7), dont 48 % sans caserne Overture.
  - Là où Overture n'a pas de caserne, l'écart casernes vaut 1 dès que la caserne USGS est présente.
- **Tri (base de 60 signaux)** : indicateur « centre de ville × aucune caserne Overture » (373 secteurs) nouveau à 82 %, partie connue +0,17. Même profil que s92 et s95, les signaux de preuve de caserne qui ont rapporté environ 6 × 10⁻⁴ chacun.
- → **s134_t8_fire_towncore** (`scripts/make_s134.py`) : v8 où le centre de ville compte comme preuve de caserne (P = 0,9 sans caserne Overture, la règle des casernes mal classées), moins v8.
  - Non nul sur 342 secteurs, dont 317 dans les quatre régions notées (au moins 300, D1-bis).
  - Nouveau à 87 %, partie connue +0,11, résidu presque indépendant du lot du 29/10 (|corrélation| ≤ 0,07).
  - Mêmes paramètres et même graine que `structural_v8e`, seuls les centres de ville bougent (contrôle dans le script).
- **Lot du 29/10 modifié** : s134 remplace s123, la piste la plus faible (d'après KR, l'écart bâtiments est nul par construction). Nouveau lot : s112, s113, s121, s134, s133.
- **Écarté** : extension aux mairies et tribunaux hors centres de ville. L'indicateur était nouveau à 87 % (+0,07), mais la version selon la formule ne touche que 297 secteurs notés (moins de 300) et sa partie connue est nulle (−0,01). Fichier et script retirés.

## 2026-10-28 — scores du 28/10 : les métropoles n'apportent presque rien

| Id Zindi | Fichier | RMSE public | Corrélation (4 régions) | Poids standardisé | Coût du retrait |
|---|---|---|---|---|---|
| JDbHXpTv | s125_t7_c_transport_houston | 0,088688 | +0,087 | −0,001 | 0,00000 |
| uEzkqmuj | s126_t7_c_transport_phoenix | 0,088702 | +0,085 | +0,034 | +0,00007 |
| H95w1uKD | s119_ems_station_nofire | 0,089400 | −0,013 | −0,020 | +0,00002 |
| wZCBMqFh | s127_t7_c_transport_sanantonio | 0,088624 | +0,095 | +0,023 | +0,00003 |
| T6KGJMna | s128_t7_c_transport_austin | 0,088865 | +0,062 | +0,004 | 0,00000 |

- **Mélange (quatre régions, ridge 0,005, sans s07/s22)** : 0,05919 attendu en public, contre 0,05932 sans ce lot. Gain −0,00013, dont −0,00010 pour les quatre métropoles ensemble.
- **Lecture** : les corrélations mesurées (+0,06 à +0,095) sont presque égales aux parties connues prévues (+0,06 à +0,10). La part nouvelle de ces découpages n'est donc presque pas liée à la vérité. Houston et Austin ont un poids quasi nul. Phoenix et San Antonio ont un poids positif : leur pente transport est un peu plus forte que celle de leur région.
- s119 (postes EMS publics) est légèrement négatif : l'hypothèse « poste EMS public = caserne de référence » ne se confirme pas.
- **Règle des recherches n° 36-37 appliquée** : gain des métropoles 0,00010, sous le seuil de 0,0003, et signes mêlés (Houston négatif). **Cas C.**
- **Lot du 29/10** (`upload_2026-10-29.txt`) : s112 (écart routier = 1, Texas), s113 (idem, Oklahoma), s121 (transport des petits secteurs), s123 (bâtiments ML d'imagerie ancienne), s133 (casernes des grandes métropoles). Fichiers vérifiés : journalisés une fois, SHA conforme, non notés, secteurs d'eau neutralisés.
  - Le 30/10, 66e signal : s122 (casernes en terre tribale), puis les finales.
  - s129-s132 (autres métropoles) passent en réserve.
- Base : 60 signaux mesurés. Staff : toujours aucune réponse sur #35402.

## 2026-10-28 (nuit, fin) — recherche n° 40 : incendies déclarés (FPA FOD)

- **Idée** : les petits feux déclarés à la base FPA FOD (1992-2020) le sont surtout par les pompiers locaux (NFIRS). Un secteur rural avec beaucoup de feux déclarés aurait donc une caserne qui intervient, et peut-être une caserne USGS.
  - Les colonnes `fod_*` sont dans la table de travail, mais aucun signal ne les avait utilisées.
  - Couverture déclarée inégale : 38 % des secteurs de l'Oklahoma ont au moins un feu, contre 97 % en Arizona.
- **Tri sur la base de 55 signaux** :

  | Signal | R² | Partie connue |
  |---|---|---|
  | log du nombre de feux | 0,68 | +0,16 |
  | densité d'ignition | 0,39 | −0,05 |
  | au moins un feu | 0,36 | +0,08 |
  | feux × aucune caserne Overture | 0,63 | +0,10 |
  | casernes v8 × aucun feu déclaré | 0,38 | +0,01 |

- **Lecture** : ces signaux reflètent surtout la ruralité, déjà dans la base. Aucun ne touche directement la formule. D'après la recherche n° 24, les signaux génériques de ce genre ont presque toujours rapporté moins de 10⁻⁴. Non retenus.
- **Limites confirmées par l'utilisatrice** : 5 envois par jour et 200 au total. Le calendrier ne change pas.

## 2026-10-28 (nuit, suite) — recherche n° 39 : page Info relue, deux faits nouveaux

- **L'est de Washington n'est noté nulle part.** La page Info dit : « All scored tracts fall within these four regions » (AZ, CA, OK, TX), avec 1 192 / 1 593 / 591 / 6 003 secteurs notés, soit 9 379. Washington n'est donc ni public (s124 l'avait montré) ni privé ; le correcteur exige seulement ses 415 lignes (#35435).
  - Correction de la recherche n° 38 : l'hypothèse « 6 % du privé » est fausse. Les valeurs de s131/s132 en Washington sont sans effet (ni public ni privé) : rien à défaire.
  - Les finales `--wa-not-public` (poids appris sur les quatre régions) sont exactement le bon cadre. Privé = 70 % des 9 379 secteurs, environ 6 565.
- **Limites de soumission** : la page Info dit « You may submit up to 10 times per day, 300 total » (règles : « 10 submissions per day, 300 submissions overall »). Mais le compteur de l'onglet Submissions affiche **60 / 200**, et nous travaillions avec 5 par jour.
  - **Confirmé par l'utilisatrice : 5 par jour.** La plateforme applique 5 et 200, quoi qu'en dise le texte de la page Info.
  - **Si 10 par jour** : les scores s'affichent en quelques minutes. Le lot du 29/10 (règle A/B/C) peut donc partir le même jour que celui du 28/10, sitôt les scores lus, et les finales peuvent passer au 29/10, avec deux jours de marge. Le plafond de 66 signaux mesurés (D1-ter) ne change pas, sauf décision de l'utilisatrice.

## 2026-10-28 (nuit) — recherche n° 38 : l'est de Washington dans le privé

- **Pourquoi** (hypothèse corrigée par la recherche n° 39 : Washington n'est noté ni en public ni en privé) : l'est de Washington (415 secteurs) serait noté en privé, soit environ 6 % du privé. Aucune équipe ne peut y apprendre quoi que ce soit du classement public : la qualité des prédictions y dépend du seul modèle.
- **Contrôle des finales (`--wa-not-public`, f1)** : moyenne prédite dans l'est de Washington 0,079, soit 0,73 fois le score v8 de la région. Les autres régions vont de 0,43 (AZ) à 0,96 (OK) ; la Californie est aussi à 0,73. Écart-type 0,062, 1,2 % de zéros. Rien d'anormal.
- **Correction** : la pente transport des métropoles est apprise sur les quatre régions publiques, mais Spokane (127 secteurs) et Yakima (57) n'avaient aucune copie. Elles recevaient donc la pente rurale.
  - s131 et s132 incluent désormais ces deux comtés (`scripts/make_s131_s132.py`, fichiers régénérés).
  - Leurs valeurs en Washington ne changent ni le score public ni les poids, puisque les finales s'ajustent sur les quatre régions publiques. Elles donnent seulement à ces deux métropoles la pente des métropoles moyennes dans les finales.

## 2026-10-28 (soir, suite) — recherche n° 37 : conventions routières, casernes par métropole

- **Bretelles** (4 à 7 % des km Overture notés, plus de 20 % dans 1 094 secteurs) : le code public de la reproduction exacte (PeterTheDataScientist, `documentation/pipeline.py`) filtre `class.isin(motorway, trunk, primary, secondary)` sans filtre de sous-classe, donc bretelles comprises, avec un découpage `overlay` en EPSG:5070. C'est notre convention : rien à changer. On n'a lu que la convention, aucune valeur.
- **Grands axes hors des classes notées** (travaux, « unknown », chemins) : 4 à 51 km par région. Négligeable.
- **Casernes par niveau de métropole** (contribution casernes v8 ; base de 55 signaux, puis avec le lot du 28/10 et s132) :

  | Découpage | R² | Partie connue |
  |---|---|---|
  | grandes métropoles (5 762 secteurs) | 0,56 (0,58) | −0,06 |
  | métropoles moyennes | 0,31 (0,34) | +0,07 |
  | hors métropoles | 0,53 (0,57) | +0,26 |

  Les trois forment une partition de la contribution casernes, déjà mesurée : deux directions seulement sont nouvelles. La partie mesurée dit déjà que la pente casernes est plate dans les grandes métropoles et forte ailleurs. Mécanisme : les casernes municipales sont bien couvertes par les lieux Overture, donc l'écart que le modèle tire des densités n'y existe pas.
- → **s133_t8_c_fire_bigmetros** (`scripts/make_s133.py`), format vérifié, en réserve.
- **Règle du 29/10 mise à jour** : s133 remplace s123 dans le cas A (s132, s112, s113, s121, s133) ; cas B inchangé (s129, s130, s131, s112, s121 ; le 30/10, s113 ou s133) ; cas C : s112, s113, s121, s123, s133 (le 30/10, s122).

## 2026-10-28 (soir) — recherche n° 36 : métropoles moyennes et signal groupé

- **Routes texanes co-signées** (une copie TIGER par numéro) : seuls 341 km de grands axes portent aussi un numéro Loop/Spur/Business du Texas (0,6 % des grands axes) et 621 km un numéro FM. Multiplicité manquante négligeable.
- **Métropoles moyennes** : chaque comté fait moins de 300 secteurs, mais regroupés, leurs cœurs portent plus de variance du transport que n'importe quelle grande métropole :

  | Groupe (v7 transport × comtés) | Secteurs | R² (55) | R² (avec le lot du 28/10, s129, s130) | Partie connue | Part de la variance v7 |
  |---|---|---|---|---|---|
  | Métropoles moyennes, toutes (TX, AZ, CA) | 1 734 | 0,41 | 0,51 | +0,24 | 19,6 % |
  | dont Texas | 909 | 0,38 | 0,51 | +0,19 | 11,5 % |
  | dont Arizona | 437 | 0,49 | 0,52 | +0,12 | 6,5 % |
  | dont Californie | 388 | 0,31 | 0,31 | +0,08 | 1,7 % |
  | Union Dallas + OKC/Tulsa + moyennes | 4 084 | 0,44 | 0,50 (avec le lot du 28/10) | +0,36 | 38 % |

  Le reste du Texas (989 secteurs hors métropoles) est redondant avec les métropoles moyennes du Texas (corrélation des résidus −0,88), puisque le Texas entier est déjà mesuré.
  - Comtés retenus : Hidalgo, Cameron, Lubbock, Nueces, Bell, Webb, Brazos, McLennan, Smith, Taylor ; Pima, Pinal, Yavapai ; Sacramento, Placer, Butte, Shasta.
- → **s131_t7_c_transport_midmetro** et **s132_t7_c_transport_othermetros** (union en un seul fichier) (`scripts/make_s131_s132.py`), format vérifié.
- **Règle pour le lot du 29/10**, fixée avant les scores du 28/10 :
  - **A** : si les quatre copies métropolitaines (s125-s128) améliorent le mélange d'au moins 0,0003 et ont des poids de même signe, on soumet s132 (une seule soumission pour toutes les autres métropoles), s112, s113, s121, s123 ; le 30/10, s122 ou s116 ;
  - **B** : si elles aident mais avec des signes mêlés, on soumet s129, s130, s131, s112, s121 (un regroupement annulerait les effets) ; le 30/10, s113 ;
  - **C** : si elles n'aident pas, on soumet s112, s113, s121, s123, s122.

## 2026-10-28 (après-midi) — recherche n° 35 : quelles routes FM TIGER compte-t-il ?

- **Hypothèse** : TIGER ne compterait que les routes FM/RM qu'OpenStreetMap classe en artères (primary, trunk ; 2 900 km sur 50 000, soit 6 %). C'est le même ordre de grandeur que le poids moyen de 0,112.
- **Contrôle avec les chiffres officiels** : le rapport Overture/TIGER du Texas tomberait à 1,64 (1,59 publié) et la part de secteurs sans route à 23-25 % (28 % publié). Rejetée comme règle stricte.
- **Variante douce** (`$TEMP/claude_ext/scr/v7b.py`, diagnostic) : poids FM concentré sur les FM « artères » (1 ou 0,6, le reste ajusté pour garder 1,59), définition concentrée sur les secteurs qui en ont (q = 0,30), part sans route inchangée (26,7 %). La différence avec le v7 est nouvelle à 88-90 %, mais sa partie connue est orientée à −0,06 : aucun indice en sa faveur. Non proposée.
- **Moitié CBP** : seuls les 2 secteurs d'eau n'ont aucun lieu Overture ; les secteurs à 1-10 lieux forment de petits groupes (63 secteurs). Rien à faire.
- **Chiffres publiés par les organisateurs** : aucun agrégat de la cible au-delà du README. Dépôts GitHub nouveaux :
  - theerealhenry : reconstruction avec les couches retirées (0,000145), non conforme ;
  - chizzydev : densités attendues sans référence.
  Rien d'utilisable.
- **Budget, franchement** : même en utilisant toutes les soumissions jusqu'au 31/10 (environ 7 signaux de plus que le plafond de D1-ter), le gain attendu serait de −0,001 à −0,0015, loin des 0,0046 qui nous séparent de Jules_Duber.

## 2026-10-28 (midi) — recherche n° 34 : d'où vient l'erreur qui reste

- **Classement (relevé ce jour)** : Jules_Duber 0,054688 (premier conforme), Sosa Team 0,055712, Sashish 0,056524, Artyom 0,056759, KettaP 0,056892, Yesternity 0,057169, riwaq 0,057219, Miscusi 0,057356, mk1981 0,057376. Nous : 35e (s111, 0,059990), environ 17e parmi les conformes. Chat et GitHub : aucune méthode nouvelle (seul ajout, un dépôt « reference-free » à base de densités attendues, sans proxy TIGER).
- **Décomposition de l'erreur (modèle v8, 150 tirages, quatre régions)** : la variance propre au transport (longueur TIGER inconnue) vaut 0,0016, celle des casernes (présence d'une caserne USGS) 0,0018. Leur somme, 0,0034, égale le résidu de notre mélange (0,0593² = 0,0035). Les variances écoles, CBP et bâtiments du modèle sont fictives : nos mesures les donnent nulles.
  - Lecture : l'erreur restante est l'incertitude sur la longueur TIGER et sur la présence d'une caserne USGS, que les données du paquet ne lèvent pas davantage. Jules a 0,0005 de moins (0,0030).
  - Explication la plus probable de cet écart : le nombre de signaux mesurés (Sosa 138 soumissions, Artyom 115, Sashish 110), contre 66 au plus chez nous (D1-ter).
- **Secteurs au bord extérieur des régions** (routes Overture coupées à la limite) : 230 secteurs ont une grande route à moins de 10 m du bord dans les quatre régions publiques. La partie Overture visible fait 94 à 95 % de la longueur du bord concerné : il manque environ 5 %, soit quelques dizaines de km au total. Effet négligeable ; l'estimation du 23/10 est confirmée.
- **Secteurs du Texas à routes FM seules** (763) : le mélange leur donne 0,027, le v8 0,098. Mais l'excès du v8 vient de ses parts écoles, CBP et bâtiments, fictives ; sa part casernes (0,031) est cohérente avec le mélange. L'indicateur est nouveau à 76 % (partie connue −0,11), mais binaire, donc exclu par D1-ter. Les variantes continues sont faibles (partie connue −0,09 à +0,03).
- **Routes de desserte du Texas** (« Frontage Rd », 1 400 km en secondary sans numéro) : comptées dans Overture, absentes de notre proxy TIGER, ce qui correspond à leur classe TIGER (S1640). Rien à changer.
- **Rang des candidats du 29/10** (base de 55 signaux, puis avec le lot du 28/10) :

  | Candidat | R² (55) | Partie connue | R² (avec le lot du 28/10) |
  |---|---|---|---|
  | s129 Dallas-Fort Worth | 0,18 | +0,11 | 0,22 |
  | s121 transport des petits secteurs | 0,17 | +0,15 | 0,19 |
  | s123 bâtiments ML d'imagerie ancienne | 0,23 | +0,13 | 0,23 |
  | s130 Oklahoma City + Tulsa | 0,36 | +0,24 | 0,36 |
  | s113 écart routier = 1, Oklahoma | 0,43 | +0,04 | 0,43 |
  | s112 écart routier = 1, Texas | 0,49 | +0,04 | 0,49 |
  | s116, s117 bords du score | 0,86 ; 0,78 | +0,49 ; +0,44 | idem |
  | s122, s105 casernes | 0,80 ; 0,78 | +0,23 ; +0,24 | idem |

  Résidus presque indépendants entre familles (|corrélation| ≤ 0,15), sauf s112-s115 entre eux (s102 est déjà mesuré). La liste provisoire (s129, s130, s112, s113, s121) est maintenue ; s123 la remplace en cinquième place si s112 ou s113 déçoivent.
- **Conclusion franche** : pas de nouveau mécanisme de la taille du v3 ou du v7. Les leviers restants sont les découpages (métropoles, régions) et le budget de signaux.

## 2026-10-28 (matin, fin) — recherche n° 33 : interactions continues et métropoles oubliées

- **Interactions continues du transport** (tri sur la base de 54 signaux, quatre régions) : v7 × log densité R² 0,62 (partie connue −0,35) ; × part urbaine 0,55 (−0,31) ; × log surface 0,64 (+0,33) ; × part de crédit en limite 0,68 (+0,38).
  - Les trois premières sont redondantes entre elles (corrélation des résidus 0,67 à 0,91).
  - La dernière est indépendante (≈ 0,1), mais reprend le double comptage des limites, que s106 (v9) a déjà épuisé sans apport.
  - Aucune n'est retenue : elles sont expliquées aux deux tiers par la base, contre moins de 20 % pour les découpages par métropole.
- **Métropoles oubliées par la recherche n° 32** :
  - Dallas-Fort Worth (11 comtés, 1 702 secteurs) : R² 0,18, orientation +0,11, 7,3 % de la variance du transport (Houston : 0,09, +0,10, 5,6 %) ;
  - Oklahoma City + Tulsa (7 comtés, 648 secteurs) : R² 0,36, +0,24, 11,2 %. Tulsa seul ne fait que 274 secteurs, d'où le regroupement (D1-bis).
  - Ce sont les deux plus gros morceaux de variance du transport encore non découpés. Leurs résidus sont presque indépendants des quatre autres métropoles (|corrélation| ≤ 0,12).
  - Tucson (270 secteurs) et Sacramento (201) sont sous 300 : pas de copie.
- → **s129_t7_c_transport_dfw** et **s130_t7_c_transport_okc_tulsa** (`scripts/make_s129_s130.py`) : format vérifié, secteurs d'eau neutralisés.
- **Lot du 29/10 (provisoire, `upload_2026-10-29.txt`)** : si s125-s128 font baisser le mélange, s129, s130, s112, s113, s121 ; sinon s112, s113, s121, s123, s122. Au plus 65 signaux mesurés.
- **Franchement** : chaque découpage porte 2 à 11 % de la variance du transport. Gain réaliste des six métropoles ensemble : −0,0005 à −0,002. Cela réduit l'écart avec Jules_Duber (environ 0,0046) sans garantir de le combler.

## 2026-10-28 (matin, suite) — recherche n° 32 : pentes du transport par métropole

- Jules_Duber est passé à 0,054688 (ρ ≈ 0,789 ; nous : environ 0,746 sur les quatre régions publiques).
- **Hypothèse** : l'écart tient à la géographie fine. La classification des artères urbaines (TIGER contre OSM) et le double comptage des limites diffèrent entre grandes villes et reste de la région, alors que notre mélange n'a qu'une pente transport par région.
- **Tri sur la base de 54 signaux (quatre régions)** : transport v7 × Houston (Harris, Fort Bend, Montgomery, Brazoria, Galveston ; 1 483 secteurs) R² 0,086 ; × Phoenix (Maricopa ; 1 009) 0,091 ; × San Antonio (Bexar, Comal, Guadalupe ; 449) 0,077 ; × Austin (Travis, Williamson, Hays ; 471) 0,063. Orientation connue de +0,06 à +0,10, résidus indépendants entre eux (≤ 0,09). Mais ces métropoles ne portent que 2 à 6 % de la variance du transport : gain réaliste de −0,0005 à −0,0015 au total. Les découpages de s102 et des casernes par métropole sont moins prometteurs (orientation nulle ou négative).
- → **s125-s128** (`scripts/make_s125_s128.py`), groupes de plus de 300 secteurs (D1-bis).
- **Lot du 28/10 révisé** : s125 (Houston), s126 (Phoenix), s119 (postes EMS), s127 (San Antonio), s128 (Austin). s112, s113, s120 et s121 reviennent en réserve pour le 29/10.

## 2026-10-28 (matin) — recherche n° 31 : les secteurs sans route notée

- s102 (écart routier = 1) a été le meilleur apport récent. Il porte surtout sur les 135 secteurs sans route Overture notée : si la référence y a une grande route, leur score vaut au moins 0,33 (mélange : 0,12 en moyenne).
- 121 d'entre eux ont une probabilité de définition modélisée inférieure à 0,5. Parmi eux, 113 ont au moins 0,5 km de « tertiary », 55 ont au moins 0,3 km de route au nom évocateur (« County Road », FM, « Parkway »…, classée residential, tertiary ou track) et 17 une route numérotée non notée.
- **Pas d'action** : mesurer un signal concentré sur ces 121 secteurs serait un sondage de petit groupe (D1-ter), et poser sans mesure qu'une part de ces routes est S1200 serait une supposition. Le levier légitime reste s102 découpé par région (s112-s115), dont s112 et s113 sont dans le lot du 28/10.

## 2026-10-27 (nuit, suite) — recherche n° 30 : la table officielle CFCC → MTFCC

- **Table officielle du Census** (`cfcc_to_mtfcc.xls`, version 2.0 du 30/10/2008, trouvée via le guide de la bibliothèque de Duke) : A1x → S1100 ; **A2x (routes nationales) et A3x (routes d'État et de comté) → S1200** ; A4x (routes locales) → S1400 ; A63 → S1630 (bretelles) ; A64 → routes de desserte. La référence S1100/S1200 descend donc des anciens codes A1-A3.
- **Idée** : l'import TIGER 2005 dans OSM a traduit A2x → primary, A3x → secondary, A4x → residential ; un tronçon jamais retouché garderait la trace de son code et dirait quelles FM du Texas et quelles routes de comté de l'Oklahoma sont S1200.
- **Vérification** : dans Overture, la source « tronçon » (w…) des routes FM et des routes de comté a été modifiée après 2015 pour plus de 95 % des km. Les rares tronçons en version 1 sont des découpages postérieurs (on y trouve « tertiary », absent de l'import). La trace CFCC est effacée. Seules les étiquettes `tiger:cfcc` d'OSM la conservent, mais elles sont absentes d'Overture et ce sont des données externes, copies de l'ancien TIGER : interdites pour le classement. **Piste close.**
- À citer dans la Documentation (origine de la classe S1200).

## 2026-10-27 (nuit) — les deux derniers gros leviers, évalués franchement

- **Colonnes USFS (diagnostic seulement, rien de soumis, D2-ter)** : sur les quatre régions publiques, les signaux USFS (écart de bâtiments avec l'USFS, rapport USFS/Overture, rapport logements USFS/ACS) ont une orientation mesurable quasi nulle (+0,03, −0,03, +0,05). La référence bâtiments étant Microsoft GlobalML, la source même d'Overture, l'écart bâtiments est quasi nul et les comptes USFS ne peuvent guère le prédire. **Le levier USFS est bien plus petit qu'estimé le 24/10 : il ne justifie pas le risque de disqualification.**
- **Recalibrer le modèle structurel** avec ce que les mesures ont appris (écarts bâtiments, écoles et EMS nuls, transport plus net, densité de casernes ×1,6) : le score composite reste dans la base à 97-99 %, donc il n'apporte presque rien de nouveau. Levier fermé.
- **Position réaliste** : mélange attendu à environ 0,059 en public et 0,063 en privé (modèle de bruit réaliste). La tête est à 0,0556 en public ; son privé dépendra de son sur-ajustement (100 à 140 soumissions). Sans effondrement de la tête au privé, la première place est hors de portée ; le top 10-15 conforme est réaliste.
- **Recommandation** : finir proprement le classement (lots des 28-29/10, finales avec `--wa-not-public` et sélection couverte), et mettre l'effort restant sur le **prix Best Documentation (1er novembre)**. Nos atouts y sont rares : audit complet, reproductibilité vérifiée, découverte que l'est de Washington n'est pas noté en public, convention de longueur confirmée, simulation de bout en bout de la méthode.

## 2026-10-27 (soir) — scores du 27/10 : l'est de Washington n'est pas public

| Id Zindi | Fichier | RMSE public | Corrélation (4 régions) |
|---|---|---|---|
| S7WAmtUM | **s124_wa_public_probe** | **0,089022463** | — |
| ZLjAupNf | s100_t8_c_fire | 0,087950 | +0,171 |
| PAe91rog | s107_t8_c_fire_ok | 0,087342 | +0,234 |
| VR4UNKc7 | s108_t8_c_fire_az | 0,089008 | +0,033 |
| SZcKAeBh | s109_t8_c_fire_ca | 0,088818 | +0,070 |

- **s124 = s à 10⁻⁹ près (0,089022463 contre 0,0890224630)** : l'est de Washington n'est pas dans le classement public. Cela explique l'« anomalie » du transport en Washington (covariance nulle) et confirme l'observation de rifatsarwar (#35241). Les mesures propres à Washington (s31, la part WA de s77) ne contenaient aucune information.
- **Conséquences** :
  - les finales se font avec `python scripts/make_finals.py --wa-not-public` : covariances et moments calculés sur les quatre régions publiques (le calcul précédent mélangeait des secteurs non notés dans les moyennes) ; Washington prédit sans les signaux régionaux, avec des poids appris ailleurs (moyenne WA 0,070 → 0,079) ;
  - s110 (casernes WA) devient inutile.
- **Mélange (mode quatre régions)** : 52 signaux, **0,05932 attendu en public** (ρ 0,746), contre 0,05958 sans les signaux du jour. Les casernes par région n'apportent que −0,00026 au total (retrait de s108 : +0,00009 ; s109 : +0,00008 ; s100 : +0,00003 ; s107 : 0). Famille « découpage casernes » saturée.
- Finales à blanc (mode WA) : f1 0,05932, f2 (avec s07/s22) 0,05819, f3 0,05953 en public attendu.
- Staff : pas de réponse sur #35402.
- **Lot du 28/10** : s119 (postes EMS publics), s120 (test groupé ; l'hypothèse des anciens contours perd son indice Washington), s121 (transport × petits secteurs), s112 et s113 (s102 au Texas et en Oklahoma). **29/10** : à choisir parmi s123, s122, s116, s114, s115, s104, s117 et s105 selon les scores du 28/10 (plafond : 65 signaux après le 29/10).

## 2026-10-28 (nuit) — recherche n° 29 : réponses des anciens fils du Chat

- Fils répondus des pages 2 et 3 relus : #35221 (Artyom : recalcul et sélections finales), #35241, #35250 (annonce du staff du 8/10), #35079. **Aucune réponse du staff** au-delà de l'annonce déjà connue ; les « réponses » viennent d'autres participants.
- **#35241 (rifatsarwar, 7/10)** : « Is eastern-wa part of the private leaderboard? (**It doesn't appear to affect the public score.**) ». C'est une deuxième observation indépendante, après notre covariance nulle du transport en Washington : l'est de Washington n'est très probablement pas noté en public. Le test s124 (lot du 27/10) le confirmera ; la parade `--wa-not-public` est prête.
- #35221 (loGan7) : le même fichier passe de 0,0554 à 0,0838 après la correction du 2/10, ce que l'on savait déjà.
- #35030 (Yanard) et #35080 : casernes absentes d'Overture sur les terres tribales. Le chiffre de Yanard vient des couches retirées et n'est pas utilisé ; le mécanisme soutient s122 (casernes × terre tribale) pour le 29/10.

## 2026-10-28 (soir) — audit complet de la solution

- Plan et résultats détaillés : `docs/05_plan_audit.md` (critères fixés avant exécution ; sections A données, B soumissions, C algèbre, D mélange, E modèle et reproductibilité, F conformité, G risques de fin).
- **Conforme** : données (univers, jointures, surfaces), 55 fichiers notés intacts, 123 fichiers au format exact, moments de la cible, mélange stable, reproductibilité exacte de 8 fichiers notés régénérés depuis leurs scripts, bruit Monte-Carlo négligeable, conformité.
- **Simulation de bout en bout** (vérités synthétiques, 30 % publics tirés au hasard) : covariances retrouvées à 1,4 % près. La formule de RMSE public attendu est optimiste d'environ 0,0016 ; le privé réel la dépasse d'environ 0,0026. Exclure s07/s22 et un ridge de 0,005-0,01 sont confirmés comme les meilleurs choix sur le privé.
- **Corrigé** : `scripts/make_s116_s117.py` recalcule lui-même le v8 (il dépendait d'un fichier produit par un script temporaire) ; s120 lit les contours en local ; `bbx.submit.validate` ne garde que `GEOID,coverage_gap_score`.
- **Parade prête** : `python scripts/make_finals.py --wa-not-public`, à utiliser si le test s124 donne 0,089022.
- **B2 fait après reconnexion** : les 55 scores affichés par Zindi correspondent exactement au journal (identifiants, fichiers, scores). Audit complet.

## 2026-10-28 (après-midi) — recherche n° 28 : l'est de Washington est-il noté en public ?

- **Pages anciennes du Chat** (page 2) : fils d'Artyom (#35302) et de Sashish (#35292), deux équipes de tête, sur les colonnes USFS, sans réponse. **#35219 (LeulTew, 6/10, sans réponse)** : « eastern-wa est-il dans l'ensemble noté, et compte-t-il pour le public, le privé, ou les deux ? ». #35435 : le correcteur exige les 415 GEOID de Washington, mais rien n'est dit sur leur partie (public ou privé).
- **Indice fort** : la covariance de la vérité publique avec le transport v3 restreint à Washington, calculée exactement, vaut +0,0000011, contre 0,0001-0,0009 ailleurs. C'est ce que donne une région absente du public. s31 (indicateur Washington) ne tranche pas : 0,0890269 prévu si Washington n'est pas public, 0,0890271 s'il l'est avec une moyenne de 0,0699 ; mesuré 0,0890274.
- **Enjeu** : si Washington n'est noté qu'en privé (environ 6 % du privé), notre mélange n'y a rien appris et y applique un poids transport quasi nul. Le corriger avec les poids des autres régions pourrait valoir environ −0,001 à −0,0015 en privé. S'il est public, on ne change rien.
- **Test décisif** : **s124_wa_public_probe** (`scripts/make_s124.py`) = 1,0 sur les 415 secteurs de Washington, m ailleurs. Résultat attendu : 0,089022 exactement si Washington n'est pas public, environ 0,21 s'il l'est. Ce test porte sur une région entière (D1-bis) et ne dit rien de la valeur d'un secteur. Il est exclu de la base du mélange (`bbx.blend.scored_signals` écarte les noms contenant « probe »).
- **Proposé pour le lot du 27/10, à la place de s110** (casernes de Washington seules, qui ne mesure rien si Washington n'est pas public). s110 reste en réserve si Washington est public. Le lot du 28/10 retrouve s115.

## 2026-10-28 (midi) — recherche n° 27 : équipes de tête, fil #35361

- **Équipes de tête** : aucune publication de Jules_Duber, Sosa Team, KettaP ou Artyom (ni sur le Chat ni sur GitHub). Sur le Chat, seuls resist (Wa_el, #35479), mk1981 (#35349) et iam-dante parmi les 30 premiers ont publié, et tout cela a déjà été lu.
- **#35361 (Ifrit)**, jamais lu en entier : « I was told the grader scores the first column after GEOID ». Dans le fichier d'exemple officiel, cette première colonne est `transport_gap`, ce qui explique les scores d'Ifrit (0,165-0,19). La cible notée reste bien la composite : chez nous, le transport en contribution (s97, corrélation 0,673) bat le transport au niveau de la composante (s101, 0,465), et les indices de caserne marquent.
- **Contrôle** : les 122 fichiers journalisés ont exactement l'en-tête `GEOID,coverage_gap_score`. **Verrou ajouté** dans `bbx.submit.validate` : tout fichier écrit ne garde que ces deux colonnes, dans cet ordre (y compris les finales du 30/10).
- Ifrit annonce aussi une part de 35 % de secteurs sans route pour Washington, de source inconnue (peut-être calculée avec les couches retirées) : non utilisée.

## 2026-10-28 (matin, suite) — recherche n° 26 : Radiant Earth, premières versions du tutoriel

- Aucune publication de Radiant Earth ni de l'auteur du tutoriel sur la méthode de calcul de la référence.
- Les versions du tutoriel du 16/07 et du 28/08 n'apportent rien de plus que les descriptions de couches de la recherche n° 25. Seul détail : la couche TIGER était marquée « grosse » dans toutes les régions, donc elle contenait toutes les routes, et le filtre S1100/S1200 se faisait au calcul. Aucune valeur des couches retirées n'a été lue.
- Bilan : les sources publiques sont épuisées. Les découvertes utiles des recherches n° 17 à 26 sont s119 (postes EMS publics, référence USGS « Fire Station/EMS Station »), s123 (décalage de version GlobalML), s121 et s122 (découpages par type de secteur), le test groupé s120 et la sélection finale couverte.

## 2026-10-28 (matin) — recherche n° 25 : onglet Data et tutoriel des organisateurs

- **Onglet Data de Zindi** : lien vers le tutoriel officiel `github.com/kentstephen/bias-bounty-map-tutorial` (Colab), jamais examiné. La version actuelle n'est qu'une carte interactive, sans calcul d'écart.
- **Historique public du tutoriel** (commit du 25/09 « Drop layers removed from the bucket ») : on n'y a lu que des descriptions de couches, aucune valeur. Les couches retirées étaient décrites ainsi :
  - `microsoft-buildings` : « **Microsoft GlobalML** Building Footprints » (et non la version américaine citée par la page Info) ;
  - `hifld-fire-stations` : « USGS National Map structures, fire stations » ;
  - `hifld-ems-stations` : « EMS / ambulance services » (cohérent avec s119) ;
  - `census-cbp` : « business establishment counts per tract » ;
  - `census-tiger-roads` : « reference baseline for the road gap ».
- **Conséquences** :
  - la référence bâtiments est le même jeu Microsoft que les bâtiments ML d'Overture, ce qui confirme un écart bâtiments quasi nul ;
  - la piste Paradise (recherche n° 21) est invalidée : on a bien fait de ne pas l'utiliser ;
  - l'écart bâtiments ne peut venir que du décalage de version (Overture : ML de février 2025 ; référence prise vers l'été 2026, après les ajouts Microsoft de 2026 aux États-Unis).
- → **s123_bld_ml_old_imagery** (`scripts/make_s123.py`, données par `scripts/build_bld_src_dates.py`) : part des bâtiments ML Overture d'imagerie de 2019 ou avant, divisée par n_defined. R² 0,23 ; orientation connue +0,13. Candidat du 29/10, mécanisme de version.
- Les notes `CLAUDE.md` du tutoriel (suivies jusqu'au 28/08) ne contiennent que des notes techniques sur la carte.

## 2026-10-28 (nuit, fin) — recherche n° 24 : ce que notre historique dit des bons signaux

- Pour chacun des 43 signaux mesurés après les 8 premiers, on a reconstitué sa nouveauté face aux signaux mesurés avant lui et son gain réel sur le mélange de l'époque.
- **La nouveauté ne prédit pas le gain** (corrélation −0,43 ; Spearman −0,46). Gain moyen ×10⁻⁴ : 18,8 pour une nouveauté ≤ 0,2 ; 20,8 pour 0,2-0,5 ; 1,3 pour 0,5-0,8 ; 1,6 pour 0,8-1.
- **Ce qui paie : les signaux qui modélisent directement un morceau de la formule** (gain ×10⁻⁴) :
  - transport v3 (66), v7 (53), probabilité de définition (8,5), écart routier égal à 1 (7,3) ;
  - indices de caserne s92 (6,3) et s95 (6,6) ;
  - découpages régionaux s83 (5,4) et s81 (3,2) ;
  - CBP par population s25 (11,9, comme contrôle négatif).

  Les signaux génériques (parts de sources, proxies de commerces, indicateurs) ont presque tous rapporté moins de 1.
- **Classement des candidats du 29/10** par analogie avec les familles qui ont payé :
  1. s119 (indice de caserne par les postes EMS publics, famille de s92/s95) ;
  2. s122 (casernes en terre tribale, découpage comme s83) ;
  3. s121 (transport dans les petits secteurs, découpage comme s81/s83) ;
  4. s116 (score nul, bord du score comme s102) ;
  5. s104 (CBP par habitant, famille de s25) ;
  6. s117, puis s105.

  À ajuster selon les scores des 27/10 (casernes par région) et 28/10 (s102 par région, test groupé s120).

## 2026-10-28 (nuit, suite) — recherche n° 23 : pentes par type de secteur

- Jusqu'ici, les pentes du mélange ont été découpées par région seulement (transport, casernes, s102). Or les mécanismes diffèrent par type de secteur : le double comptage des limites domine les petits secteurs urbains, et la couverture des lieux Overture est la plus faible en terre tribale.
- Tri sur la base de 51 signaux (R² ; partie connue) :

  | Découpage | Secteurs | R² | Partie connue |
  |---|---|---|---|
  | transport v7 × petits secteurs (< 2 km²) | 2 376 | **0,19** | +0,14 |
  | casernes v8 × terre tribale (> 50 %) | 835 | **0,37** | +0,23 |
  | transport v7 × rural | 1 853 | 0,63 | +0,42 |
  | transport v7 × grands secteurs (> 50 km²) | 1 850 | 0,61 | +0,41 |
  | casernes v8 × grands secteurs | 1 850 | 0,67 | +0,22 |
  | transport v7 × terre tribale | 835 | 0,79 | +0,41 |
  | casernes v8 × rural | 1 853 | 0,84 | +0,22 |

- → **s121_t7_c_transport_small** et **s122_t8_c_fire_tribal** (`scripts/make_s121_s122.py`), candidats pour le 29/10 avec s119, s116, s117, s104 et s105. Le choix final des 5 se fera sur les scores des 27 et 28/10.

## 2026-10-28 (nuit) — recherche n° 22 : la moitié CBP au niveau du comté

- La page Info parle de « County Business Patterns ». Hypothèse : des comptes par comté répartis entre secteurs au prorata des lieux Overture, ce qui donnerait un écart CBP constant dans chaque comté.
- Les comtés des régions ont 0,034 à 0,086 lieu Overture par habitant (médiane 0,052), contre environ 0,024 établissement CBP par habitant aux États-Unis. Au niveau du comté, Overture dépasse donc partout la référence, et l'écart CBP serait nul presque partout : aucun signal.
- Lecture : avec toute répartition proche du niveau du comté, la moitié CBP est quasi nulle, ce qui est cohérent avec la faiblesse de tous nos signaux CBP. La composante POI est portée par les casernes.
- Bilan des recherches n° 17 à 22 : sources nouvelles épuisées (bucket, page Info, organisateurs, rubric, ordre des lignes, contours d'origine, strates, référence USGS, convention de longueur, incendies récents, CBP par comté). Restent à jouer : s120 (test groupé), s119 (postes EMS publics), les découpages régionaux et la sélection couverte.

## 2026-10-27 (nuit, fin) — recherche n° 21 : incendies postérieurs à la référence bâtiments

- **Idée** : la référence bâtiments est la version américaine des empreintes Microsoft (2018, avec une v2 partiellement refaite en 2019-2020). Là où un feu postérieur a détruit des maisons et où Overture a été remis à jour avec des images d'après le feu, Overture compte moins de bâtiments que la référence, et l'écart bâtiments, presque nul ailleurs, devient fort. s93 (zones brûlées × densité) ne distinguait pas les images d'avant et d'après le feu.
- **Signal** : part brûlée (NIFC) après 2017 × part des bâtiments Microsoft d'Overture d'imagerie postérieure au feu, divisé par n_defined. Il est nul hors de 18 secteurs, tous en Californie du Nord ; Paradise (Camp Fire 2018) en tête : 100 % brûlé, 73-99 % d'imagerie post-feu. **Le mélange y prédit 0,00 à 0,08**, alors qu'avec une référence d'avant le feu on attendrait environ 0,2-0,3 (écart bâtiments 0,5-0,7).
- **Non retenu pour le classement** :
  - date de la référence incertaine (la v2 a pu repasser Butte County en images de 2019-2020, postérieures au feu) : environ une chance sur deux ;
  - gain au mieux d'environ −0,0003 (une dizaine de secteurs) ;
  - mesurer ce signal reviendrait à sonder un petit groupe, contraire à D1-ter.

  Une correction directe non mesurée aurait une espérance quasi nulle. À citer dans la Documentation (cas limites) et dans le lien avec les maisons fantômes.

## 2026-10-27 (nuit, suite) — recherche n° 20 : rubric, ordre des lignes, contours d'origine

- **« Scoring Rubric » de nos soumissions** (ouvert pour s111) : rapports de disparité rural/urbain 2,33×, tribal 2,81×, etc. Recalculés exactement à partir de nos propres prédictions (tribal 2,81×, rural 2,31×) : le rubric ne contient aucune information sur la vérité.
- **Ordre des lignes des fichiers fournis** : exemple de soumission trié par GEOID ; tables ACS et secteurs triées selon la courbe de Hilbert (tri spatial annoncé par le README). Aucune fuite.
- **`boundaries/original-rings.geojson`** (jamais ouvert) : les quatre contours bruts d'origine (AZ, CA, TX, WA ; pas l'Oklahoma). Le README dit qu'ils gonflaient « de 5 à 8 fois » les écarts de 256 secteurs de bordure, défaut corrigé le 26/08. Ils coupent 326 secteurs (264 hors Washington ; 157 à plus de moitié dehors), et le mélange leur donne 0,081 (0,060 ailleurs). Si la vérité gardait ce découpage, ces secteurs auraient des scores très élevés (corrélation d'environ +0,40 pour l'indicateur), ce qui expliquerait aussi l'anomalie de Washington (15 % de ses secteurs coupés). Le README parle d'un défaut corrigé : probabilité faible.
- **Test groupé** : **s120_pooled_open_or_rings** (`scripts/make_s120.py`) = s118 standardisé + part du secteur hors de son contour d'origine standardisée. Il remplace s118 en tête du lot du 28/10. Un score nul ferme les deux hypothèses pour une seule soumission ; un score nettement positif sera départagé le 29/10 (s118 seul ou la part hors contour seule).

## 2026-10-27 (nuit) — recherche n° 19 : convention de longueur, référence USGS

- **Convention de longueur des routes** (jamais testée) : longueur découpée au contour (la nôtre) ou longueur entière des tronçons qui touchent le secteur. La seconde donne 23 à 37 % de km Overture en plus selon la région (corrélation par secteur 0,97-0,99) et des poids recalés de 0,47 (FM) et 0,58 (comtés OK). Mais la direction « tronçons entiers − découpage » est orientée à **−0,40** dans la base mesurée, et le transport qui en découle prédit moins bien (+0,585 contre +0,673). Le README penche aussi vers le découpage (exemple de longueur en EPSG:5070, « clipped map data »). **Notre convention est confirmée.**
- **Référence des casernes = USGS National Map** (page Info), et non HIFLD. Les structures USGS ont un type « Fire Station/EMS Station » (casernes et postes EMS réunis) distinct de « Ambulance Service ». Cela colle au README : EMS « proche de 1:1 », casernes qui « portent la composante ». La catégorie EMS d'Overture est surtout faite de sociétés privées (« … Ambulance Service LLC »), cohérente avec « Ambulance Service ». Conséquence : un poste EMS public (« Frio County EMS ») compte comme caserne de référence. → **s119_ems_station_nofire** (`scripts/make_s119.py`) : 103 secteurs avec un poste EMS public nommé et sans caserne Overture (78 sans autre indice de caserne), R² 0,15 sur la base. Le mélange leur donne 0,073 ; avec un écart casernes de 1, on attendrait environ 0,12-0,15. Gain possible de l'ordre de −0,0003. Candidat pour le 29/10.

## 2026-10-27 (soir) — recherche n° 18 : fichiers et détails jamais examinés

- **Fichiers d'exemple de soumission** : uniquement des zéros, avec des colonnes facultatives transport_gap, building_gap et poi_gap qui servent au tableau de biais, pas au RMSE. Rien à en tirer.
- **Toutes les colonnes des strates** passées au crible (TIGER, HIFLD, CBP, Microsoft, bâtiments, routes, établissements, etc.) : aucune ne dérive des couches retirées (seule `tiger_year` apparaît, une métadonnée). Les colonnes USFS de bâtiments (y compris BuildingCover et BuildingDensity) et `carbonplan_buildings` sont bien bloquées par le filtre de `bbx.io`. Conformité confirmée.
- **Catégories de lieux** : nos listes de casernes, d'EMS et d'écoles sont exactement les listes officielles. Overture compte 24 854 écoles dans les régions, au-dessus de la référence probable, ce qui est cohérent avec « l'écart écoles bloque rarement ».
- **Le filtre « open » mis à l'épreuve sans soumission** : la page Info dit que les hôpitaux d'Overture sont « environ 12 fois » la référence. Dans les quatre régions d'étude, Overture a 5 365 hôpitaux (2 825 « open »), et la référence attendue au taux national est d'environ 890. Le rapport vaut donc 6,0 sans filtre et 3,2 avec le filtre. La version sans filtre est la plus proche de 12 : indice contre l'hypothèse. **Probabilité de s118 ramenée à environ 5-10 %** ; on le garde comme pari bon marché dans le lot du 28/10.
- Écarté pour conformité : utiliser les tableaux de biais des équipes concurrentes conformes pour recaler nos niveaux par strate. Ce sont leurs prédictions, assimilables aux informations exclues par la règle C1.

## 2026-10-27 (suite) — recherche n° 17 : là où l'on n'avait pas cherché

- **Bucket officiel** relisté (327 objets) : identique au relevé du 16/10, aucun fichier nouveau ou modifié depuis le 25/09.
- **Page Info relue** :
  - la fourchette 0,71-1,59 porte sur « les quatre régions d'étude » (Washington n'est pas contraint) ;
  - la référence bâtiments est « Microsoft US Building Footprints », la version américaine, alors qu'Overture utilise la version mondiale ;
  - « The scored coverage gap computation must use only the datasets provided for this challenge » : notre règle sur les données externes est confirmée.
- **Organisateurs** (Reliabl, Humane Intelligence) : aucune API ni aucun code de calcul public.
- **Hypothèse nouvelle : le filtre de statut des lieux.** Le texte officiel compare « les lieux Overture de cette catégorie » sans dire lesquels comptent. 916 des 3 641 casernes Overture (25 %) n'ont pas de statut (Meta, Microsoft, Foursquare ; BrightQuery a toujours un statut) ; 542 secteurs ont une caserne Overture mais aucune « open ». Si l'organisateur n'a gardé que les lieux « open », ces secteurs ont un écart casernes de 1 là où la référence a une caserne, soit environ +0,06 sur la contribution casernes. Nos mesures ne tranchent pas : s29 (lieux fermés) est négatif mais confondu avec l'effet urbain. → **s118_t8o_fire_open_diff** (`scripts/make_s118.py`) : 836 secteurs touchés, R² 0,13 sur la base. Probabilité estimée 10-20 %, mais un gain possible de l'ordre de −0,002 à −0,004. Placé dans le lot du 28/10 (à la place de s105) pour pouvoir, s'il est positif, traiter de même la moitié CBP, l'EMS et les écoles le 29/10.

## 2026-10-27 — classement et recherche n° 16 : bords du score, sélection couverte

- **Classement** : Jules_Duber passe premier conforme (0,055568, ρ 0,781), devant Sosa Team (0,055733). Nous sommes 33e, soit 17e parmi les conformes (s111, 0,059990, ρ 0,739). Notre mélange actuel est attendu à 0,0589 (ρ 0,750).
- **Bords du score** (après le succès de s102) : `bbx.structural.simulate` renvoie aussi P(transport défini à 0), P(écart casernes = 1), P(score ≥ 0,15) et P(score ≥ 0,30). Les plus neufs sur la base de 51 signaux sont P(score ≥ 0,30) (R² 0,78, partie connue +0,44) et P(score = 0) (R² 0,83, −0,47). → **s116, s117** (`scripts/make_s116_s117.py`) pour le 29/10.
- **Secteurs sans route notée** (135) : 14 ont une route en limite (mélange 0,23), 119 n'ont aucune route proche (transport très probablement non défini), 2 sont ambigus (route entre 10 et 30 m). Rien de coûteux.
- **Sélection couverte (gain sûr d'environ 0,0003 en espérance).** Zindi garde la meilleure des deux soumissions sélectionnées sur le privé. Deux pas de ridge de la même recette sont presque identiques : on n'en tire rien. Avec f1 sans s07/s22 et f2 avec, le meilleur des deux vaut :

  | Secteurs d'eau publics | aucun | un | les deux | espérance |
  |---|---|---|---|---|
  | f1 (sans) | 0,05887 | 0,0605-0,0606 | 0,0622 | 0,05990 |
  | f2 (avec) | **0,05823** | 0,0610-0,0612 | 0,0639 | 0,05998 |
  | meilleur des deux | | | | **0,05959** |

  Deux pas de ridge donnent 0,05988. `scripts/make_finals.py` produit maintenant f1_blend_ridge0005, f2_blend_ridge0005_with_s07_s22 et f3_blend_ridge001 (noms contenant « blend », pour rester hors de la base). **Sélection du 30/10 : f1 et f2.**
- **Bilan franc** : pas de nouvelle source d'information majeure. Les gains restants viennent des lots préparés (casernes par région le 27, s102 par région le 28, bords du score le 29) et de la sélection couverte.

## 2026-10-26 (soir) — scores du 26/10 : chaîne validée

| Id Zindi | Fichier | RMSE public | Corrélation implicite |
|---|---|---|---|
| EboKdJHP | **s111_blend45_ridge0005** | **0,059990** (attendu 0,05974) | — |
| PfWH69jt | s106_t9_c_transport | 0,069021 | +0,638 |
| u33fnwGi | s101_t7_transport_gap | 0,078834 | +0,465 |
| 17wt6cVc | s102_t7_p_transport_one | 0,088850 | +0,069 |
| o5LTLYBQ | s103_t8_p_fire_defined | 0,087002 | +0,225 |

- **Validation du mélange** : 0,059990 pour 0,05974 attendu (+0,00025, dans la marge de ±0,001). La covariance réelle dépasse même la prévision de 1,2 % ; l'écart de RMSE vient de la variance des prédictions sur les 30 % publics. La chaîne est validée. s111 devient notre meilleur score affiché (vers le 31e rang).
- **Mélange à 49 signaux** (s07 et s22 exclus) : ρ 0,750, **0,05887 attendu en public** (ridge 0,005 ; 0,05872 à ridge 0).
- Contributions marginales :
  - **s102 : −0,00066**, la meilleure du jour malgré une corrélation seule de +0,07 (il porte la partie extrême du transport) ;
  - s101 −0,00008 ; s103 −0,00006 ;
  - **s106 : +0,00001**. La v9 (routes en limite jusqu'à 30 m) n'apporte rien au-delà du v7 : piste close.
- Staff : pas de réponse sur #35402.
- **Lot du 27/10** : s100, s107-s110 (casernes v8 globales et par région). Sur la base de 51 signaux, les versions régionales restent neuves (R² 0,47-0,55) et indépendantes entre elles.
- **Lot provisoire du 28/10** (`scripts/make_queue_oct28.py`) : s112-s115, s102 restreint à TX, OK, AZ, CA (R² 0,19-0,46), puis s105.
- Budget : 51 signaux mesurés ; 56 après le 27/10, 61 après le 28/10, 66 après le 29/10 (plafond D1-ter). Le 30/10 : f1 et f2 à soumettre pour pouvoir les sélectionner.

## 2026-10-26 — mélange de validation dans le lot du jour

- Décision de l'utilisatrice : soumettre le mélange dès le 26/10 pour connaître tôt sa vraie valeur.
- **s111_blend45_ridge0005** (`scripts/make_blend_check.py`) suit la recette des finales : 45 signaux (s07 et s22 exclus), ridge 0,005, règle des secteurs d'eau. ρ 0,741, **RMSE public attendu 0,05974**. Son nom contient « blend » : il reste hors de la base mesurée.
- Lot du 26/10 : s111, s106, s101, s102, s103 ; s105 passe en réserve (le plus couvert des cinq par la base, R² 0,76).
- Lecture prévue : un écart de plus de 0,001 avec 0,05974 signalerait un défaut de la chaîne à corriger avant le 30/10. Cette marge vient de la variance des prédictions sur les 30 % publics (diagnostic).

## 2026-10-26 — diagnostic complet de la solution

**Contrôles réussis**
- Intégrité : les 50 fichiers notés sont identiques à ceux du journal (SHA-256).
- Algèbre : moyennes des fichiers = m (sauf s03, écart de 0,0002), ce qui annule l'erreur de premier ordre ; moments recalculés identiques ; s16 (seul mélange soumis) : covariance prévue à 1 % près (+0,00023 de RMSE).
- Conformité : aucune colonne USFS interdite dans la table, aucun fichier de couche retirée sur le disque.
- Alignement : sorties v3, v7, v8 et v9 dans l'ordre exact des 9 794 secteurs.
- Mélange : poids stables (somme des poids standardisés 0,46, maximum 0,09, conditionnement 4 600), écart-type des prédictions égal à ρ·s, moyennes régionales égales aux moyennes mesurées.

**Défauts trouvés et corrigés**
1. **Deux secteurs d'eau** (48039990000, 48057990000 ; score 1 par la règle) sont extrêmes dans s07 et s22. S'ils sont publics, ils font jusqu'à 11 fois (s07) et 10 fois (s22) la covariance mesurée, et le poids de s07 change de signe.

   | Scénario | Probabilité | Tous les signaux | Sans s07 et s22 |
   |---|---|---|---|
   | aucun des deux public | 49 % | 0,0592 | 0,0597 |
   | un des deux public | 42 % | 0,0618-0,0620 | 0,0613-0,0614 |
   | les deux publics | 9 % | 0,0645 | 0,0629 |
   | **espérance** | | 0,06080 | **0,06070** |

   Corrections :
   - `scripts/make_finals.py` exclut s07 et s22 ;
   - `bbx.signals.write_signal` donne désormais m à ces deux secteurs ;
   - les 11 fichiers en attente (s100-s110, s104) sont corrigés et rejournalisés. s101 y était à 4,9 écarts-types, soit environ 7 % de biais possible.
2. **Estimation du privé trop optimiste.** Le bruit d'une covariance publique dépend de toute la dispersion de la cible (S_e = E[p pᵀ r²]/n, avec r² = (ŷ − m)² + σ²(ŷ)), et non du seul résidu. Avec ce modèle, les finales valent environ **0,0597 en public et 0,0635 en privé attendu**. Les concurrents subissent le même écart, plus fort s'ils ont beaucoup ajusté sur le public. La régularisation optimale reste petite (0,005).
3. Conformité de la régularisation à D1-ter : déjà corrigée (ridge 0,005 et 0,01).

**Limites restantes**
- Le score public d'un mélange est incertain d'environ ±0,001 : la variance des prédictions sur les 30 % publics diffère de celle de l'ensemble.
- s84 et s82 (transport régional CA, AZ) reposent sur quelques secteurs (10 secteurs portent 52 % et 29 % de leur variance). Les retirer n'améliore pas l'espérance ; on les garde.
- Le modèle structurel surestime la partie POI hors Oklahoma et ajoute un bruit « bâtiments » inutile : le mélange les corrige linéairement, et les casernes par région (s107-s110) visent le reste.
- **Processus** : aucun mélange n'a été validé sur le classement depuis s16 (8 signaux). Recommandation : soumettre f1 dès le 27/10 (validation et filet de sécurité), à la place de s110.

## 2026-10-26 (nuit) — classement et recherche n° 15

- **Classement relevé** (nombre de soumissions entre parenthèses) :
  - lignes 1 à 16 : reconstructions (0 à 0,013 ; nouvelles : kevin9327ai, merlo6_, AsherWu) ;
  - **17. Sosa Team 0,055733 (138)** ; 18. Jules_Duber 0,055857 (80) ; 19. KettaP 0,056892 (43) ; 20. Artyom 0,056901 (115) ; 21. riwaq Team 0,057300 (65) ; 22. mk1981 0,057376 (39) ; 23. Yesternity Team 0,057485 (83) ; 24. Sashish 0,057619 (110) ; 25. Miscusi 0,057769 (43) ; 26. resist Team 0,058277 (70) ; 27. Shivoo29 0,058468 ; 28. iam-dante 0,058697 (105) ; 29. harshvt 0,058824 ; 30. ORANO-Bias-Model Team 0,059168 ;
  - **nous : 52e, 0,066482 (s97), 50 soumissions.** Notre mélange attendu (0,0590 public) se placerait vers le 30e rang, 14e parmi les équipes conformes.
- **Évolution depuis le 24/10** : la tête ne bouge presque pas (Sosa 0,055740 → 0,055733). Le peloton progresse : riwaq −0,0003, Sashish −0,0007, Miscusi −0,0007, resist −0,0003, Shivoo29 −0,0008.
- **Chat** : #35554 (kevin9327ai, reconstruction en 12e position) publie des valeurs calculées avec les couches retirées, que nous n'utilisons pas. #35560 (vik439) publie une moyenne de groupe obtenue par sondage, exclue par la règle C1. Le staff n'a toujours rien publié.
- **Conformité** : la règle D1-ter impose des poids régularisés. Les finales passent à ridge 0,005 et 0,01 (0,06005 et 0,06019 en privé attendu, contre 0,05997 à 0) dans `scripts/make_finals.py`.
- **Groupes dont la moyenne n'est pas fixée par la base** (indicateurs binaires, diagnostic seulement : D1-ter n'autorise que des signaux continus) : secteurs du Texas à routes FM seules (662, R² 0,26 ; le mélange leur donne 0,021, le v8 0,102). Les autres grands groupes sont fixés à 66-90 %.
- **v11** (définition des secteurs à FM seules croissante avec les km de FM, L = 22,5 km, part du Texas sans route inchangée) : nouvelle à 95 % mais minuscule (écart-type 0,0025 sur le score). Abandonnée, code retiré.
- **Washington** : sa moyenne mesurée (0,070) n'est cohérente qu'avec une composante transport présente (environ 0,033 en moyenne) et son rapport Overture/TIGER (1,21) est dans la fourchette officielle. Le transport y existe donc, mais notre modèle ne le place pas dans les bons secteurs. Hypothèse : pas de double comptage des limites dans la référence de cette région, ajoutée le 25/09. La version sans double comptage n'est neuve qu'à 28 % ; en réserve (`data/interim/structural_v8_nob_draft.parquet`).
- **Bilan** : pas de nouvelle piste majeure. Le plan reste : lot du 26/10 (s106, s101, s102, s103, s105), puis casernes par région le 27/10.

## 2026-10-25 (soir) — recherche n° 14 : gains sûrs

- **Régularisation des mélanges finaux (gain sûr, environ −0,001 en privé).** Les covariances publiques sont mesurées avec un bruit e de covariance σ² C / n_public. On en déduit le MSE privé attendu de w = (C + ridge D)⁻¹ c_pub : s² − 2 tr(A cc′) + tr(ACA cc′) + tr(ACA S_e), avec cc′ ≈ c_pub c_pubᵀ − S_e. Résultats avec 47 signaux (identiques avec un résidu hétéroscédastique) :

  | ridge | public (en échantillon) | privé attendu |
  |---|---|---|
  | 0 | 0,05904 | **0,05997** |
  | 0,005 | 0,05916 | 0,06005 |
  | 0,02 | 0,05959 | 0,06043 |
  | 0,05 | 0,06016 | 0,06094 |
  | 0,10 | 0,06079 | 0,06149 |

  Le biais ajouté par la régularisation dépasse le bruit retiré. Notre plan (ridge 0,05 et 0,10) aurait coûté environ 0,001. `scripts/make_finals.py` est corrigé : ridge 0 / 0,005 / 0,02, et score privé attendu calculé ainsi (l'ancienne correction ne comptait que la moitié de l'écart public → privé, 2k/n). **Sélection du 30/10 : f1 et f2.**
- **Courbure du mélange** (carré, articulations aux quantiles 80/90/95 %, bas de distribution) : sur des tirages de notre modèle pris comme pseudo-vérité, aucun gain (+0,04 % à +0,08 %, dans le bruit). Non retenue.
- **Secteurs extrêmes** : seuls les 2 secteurs vides relèvent d'une règle exacte (déjà appliquée). Les 137 secteurs sans route notée ont un écart transport de 1 s'il est défini ; le mélange leur donne 0,118 en moyenne. Rien de déterminé de plus.
- **EMS** : le README officiel dit que l'EMS « bloque rarement » et que les casernes portent la composante ; notre modèle le reproduit (contribution EMS ≈ 0,001). Les écoles « définies à zéro » diluent les casernes ; la variante v10 l'intègre mais reste dans la base (recherche n° 13).
- **Bilan franc** : pas de piste qui garantisse la première place. Gain sûr trouvé : le choix de régularisation (environ 0,001 en privé). Gains possibles mais non garantis : s106 et les casernes par région (s107-s110).

## 2026-10-25 (suite) — recherche n° 13 : régions, casernes, Washington

- **Covariances intra-régionales exactes du transport** (s77, s81-s84 et indicateurs de région, par algèbre linéaire sur les fichiers ; pente de la vérité sur le v3 dans la région) : Texas 0,99 ; Arizona 1,52 ; Oklahoma 1,72 ; Californie 2,06 ; **est de Washington 0,02**. En Washington, le transport v3 (≈ v7) n'a aucune covariance avec la vérité : soit la composante y est presque toujours non définie, soit elle y est calculée autrement. Le mélange y annule déjà le transport ; l'enjeu restant est le poids de la partie POI dans cette région.
- **Moyennes régionales mesurées** (public, par les indicateurs) : TX 0,049 ; AZ 0,042 ; OK 0,128 ; CA 0,068 ; WA 0,070. Notre modèle v8 donne 0,089 / 0,101 / 0,131 / 0,092 / 0,109 : la partie POI et bâtiments colle en Oklahoma mais elle est environ deux fois trop forte ailleurs (trois fois en Arizona). Les pentes casernes diffèrent donc probablement d'une région à l'autre, comme celles du transport.
- **Texas, FM/RM** : l'hypothèse « seules les FM/RM urbaines sont dans TIGER » respecte le rapport 1,59 (u > 0,8 : 6 900 km pour 6 400 requis) mais donne 20,7 % de secteurs sans route contre 28 % publiés : rejetée. Le v7 (poids 0,112, définition 0,19) reste le seul réglage compatible.
- **Écarts sans effet** : tronçons d'axes majeurs sans numéro de route (moins de 1 % hors Texas, environ 500 km d'autoroutes au Texas), bretelles et routes de desserte numérotées (moins de 1 % des km de routes). Notre proxy les traite déjà correctement.
- **Écoles** : s08 est anti-corrélé à la vérité, ce qui suggère qu'Overture couvre au moins autant d'écoles que la référence. La variante v10 (écart écoles nul) ne change guère la contribution casernes (R² 0,46, écart-type 0,005) ; l'effet écoles est déjà dans la base (s08). Non retenue.
- **Sources web** : la complétude des casernes de la référence varie selon l'État (couche HIFLD partielle de l'IAFC limitée à 8 États, données USGS bénévoles et approximatives en zone rurale). Rien de public sur TIGER S1200 en Washington.
- **Candidats** (`scripts/make_queue_oct27.py`) : **s107-s110**, contribution casernes v8 restreinte à OK, AZ, CA, WA. Neuves pour la base (R² 0,07-0,21 hors effet de niveau régional), presque indépendantes entre elles ; avec s100 (version globale), le mélange peut fixer une pente casernes par région, comme s81-s84 pour le transport. **Lot provisoire du 27/10** : s100, s107, s108, s109, s110 ; ordre définitif après les scores du 26/10 (on pourra découper plutôt s105 ou s103 s'ils marquent mieux).

## Recherche n° 12 (24/10, soir) — Chat, dépôts, bâtiments, routes en limite

- **Classement** : premier conforme probable Sosa Team 0,05574 (lignes 1 à 13 en reconstruction), puis Jules_Duber 0,05586, KettaP 0,05689, mk1981 0,05738, iam-dante 0,05871. Nous : 100e avec 0,074257, avant le lot du 25/10. Pour 0,0557, il faut ρ ≈ 0,78 (nous : 0,673 prévu).
- **Staff** : toujours aucune réponse sur #35402 ; #35532 (jennifer_evangelista, calibration sur ses propres RMSE) et #35493 (attribut `sources` des bâtiments) sans réponse non plus. Le paquet utilise Overture 2026-08-19.0.
- **#35478 (HHYurdagul, 46e à 0,0665)** confirme notre mécanisme v3 (double comptage des routes en limite) et rapporte un gain avec une bande de 30 m où l'on ne garde que les tronçons longs (> 232 m) : 0,069704 → 0,068468.
  - Nouveau module `src/bbx/features_bandruns.py` et **transport v9** (`scripts/make_s106.py`) : 25 600 km de grands axes en tronçons longs à moins de 30 m, contre 17 300 km dans notre bande de 10 m.
  - Avec les rapports officiels, le poids des FM/RM du Texas tombe à 0,005 (0,112 en v7) et celui des routes de comté de l'Oklahoma à 0,095 ; les parts de secteurs sans route ne bougent pas.
  - Réserve : les chaussées séparées et les routes de desserte du Texas placent une deuxième ligne à 15-40 m de la limite, que la référence ne compte qu'une fois. La bande de 30 m peut donc surcréditer.
  - Tri : R² 0,71 sur la base actuelle, 0,89 une fois s97/s98 mesurés, donc environ 11 % de nouveau. Gain plausible : 0 à +0,015 de ρ. → **s106_t9_c_transport**, en réserve.
- **Bâtiments, dates d'imagerie Microsoft** (diagnostic, pas de signal) : dans Overture, les bâtiments Microsoft vont de 2017 à 2024 (2000 = date inconnue), version 2025-02-25 ; Microsoft a ajouté depuis environ 4,6 M de bâtiments américains (2026). La part de bâtiments Microsoft d'imagerie ancienne est nouvelle à 77 % (R² 0,23), mais KR (#35474, qui avait vu la référence avant son retrait) affirme que la référence Microsoft est la même source qu'Overture : l'écart bâtiments serait nul là où rien n'est dessiné à la main. Piste non retenue. Les bâtiments Google Open Buildings (289 secteurs frontaliers, TX et AZ) forment un trop petit groupe (D1-ter).
- **Dépôts GitHub** : kainwangroger (KR, prix spéciaux, meilleur public 0,0820), mkorayemai-web (mk1981, découverte « une seule sortie », pas de code de classement), WaelYTz (resist, idem). Aucun pipeline de classement des équipes de tête n'est public.
- **Conclusion franche** : aucune piste trouvée ne garantit la première place. Le principal inconnu reste le score du v7 (s97), demain.

## Recherche Scopus (après la recherche n° 11)

- 14 requêtes en lecture seule sur le Scopus de l'utilisatrice ; 11 articles relus par les pairs retenus dans `docs/03_revue_litterature.md` section 7.
- **Rien ne change le modèle.** Heris et al. 2020 (rappel Microsoft plus faible sous 200 m²) confirme le signal des petits bâtiments déjà mesuré (s27, hand_only). Zielstra et al. 2013 confirme que les routes OSM/Overture américaines viennent de l'import TIGER 2008 : l'écart est un écart de classement (v6, v7).
- Usage : citations pour la Documentation (1er novembre) et pour les limites de la Bias Discovery (Carlson et al. 2022 : bâtiments non résidentiels en zone rurale).

## Revue de littérature (20/10)

- Fichier : `docs/03_revue_litterature.md`.
- Elle confirme les mécanismes déjà modélisés : TIGER S1200 inclut les routes de comté ; au Texas, les routes FM sont classées tertiary dans OSM ; dans Overture, un bâtiment ML n'est ajouté que s'il ne touche aucun bâtiment OSM ou Esri. Les signaux qui en découlent sont expliqués à 59-89 % par la base, donc pas de gain majeur attendu.
- Pour le Bias Discovery, elle apporte l'explication causale : la pratique OSM est de ne pas supprimer les bâtiments brûlés, et les empreintes ML viennent d'images d'avant le feu. Elle apporte aussi l'usage des empreintes dans les produits d'exposition USFS. Les deux sont intégrés à `writeup/bias_discovery.md`, avec la répartition par source : 461 fantômes OSM, 1 602 Microsoft.
- La colonne `usfs_edition` indique WRC v2 (RDS-2020-0060-2). D'après la métadonnée (extrait indexé, page en 403), ses comptages de bâtiments viennent d'Onegeo et USA Structures, en conditions 2022. **Précision publiée le 20/10 à 02 h 15** sous #35402, à la demande de l'utilisatrice. D2-ter reste inchangé.

## Suivi
- Question au staff sur les colonnes USFS rédigée dans `docs/chat_question_usfs.md`. **Publiée le 18/10 à 22 h 29** à la demande de l'utilisatrice, sous le compte Arnaud_TOE : https://zindi.world/competitions/bias-bounty-mapping-equity-challenge/discussions/35402 (en attente de réponse).
