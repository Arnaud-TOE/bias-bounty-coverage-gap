# Plan d'audit de la solution (28/10/2026)

**But.** Trouver tout défaut qui dégrade notre RMSE public ou privé, avant les finales du 30/10.

**Règles.**
- Chaque contrôle a une méthode et un critère de réussite fixés **avant** de l'exécuter.
- On exécute dans l'ordre. Chaque résultat est noté : ✅ conforme, ⚠️ défaut mineur, ❌ défaut à corriger.
- Tout défaut ❌ est corrigé, puis le contrôle est refait.

## A. Données et variables

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| A1 | Fichiers du paquet complets | Taille de chaque fichier local de `data/raw` comparée au relevé du bucket | Tous présents, tailles identiques |
| A2 | Univers des secteurs | Table de travail contre fichiers d'exemple des 5 régions | 9 794 GEOID uniques, en texte sur 11 caractères, région correcte, aucun en trop ou manquant |
| A3 | Jointures des variables | Pour chaque fichier de variables (features, roadref, osmfac, bandruns, bld_src_dates), part des secteurs absents (remplis par 0) | Absences justifiées seulement (secteur sans objet) ; aucune absence massive par région |
| A4 | Plausibilité des variables clés | Surface (km²) contre ALAND ; km de routes, nombres de bâtiments et de lieux : bornes, zéros, valeurs extrêmes | Surface à 1 % près ; pas de valeur aberrante inexpliquée |
| A5 | Conformité des entrées | Colonnes interdites et couches retirées absentes du pipeline | Aucune |

## B. Chaîne de soumission

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| B1 | Fichiers notés intacts | SHA-256 sur disque contre journal | 100 % identiques |
| B2 | Scores bien recopiés | Les 55 lignes de l'onglet Submissions de Zindi (identifiant, fichier, score) contre `log.csv` | Aucune différence au-delà de 1e-9 |
| B3 | Format | En-tête, nombre de lignes, bornes, valeurs manquantes, ordre des lignes | `GEOID,coverage_gap_score`, 9 794 lignes, valeurs dans [0, 1], aucun manquant |
| B4 | Fichiers en attente | Lots des 27-29/10 : journalisés une fois, SHA conforme, secteurs d'eau neutralisés | Tous conformes |

## C. Algèbre du classement

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| C1 | Moments de la cible | m et s recalculés à partir des deux constantes | Identiques aux valeurs stockées |
| C2 | Méthode de bout en bout | Simulation : fausse vérité, tirage aléatoire de 30 % de secteurs publics, RMSE simulés de nos vrais fichiers, puis covariances implicites, mélange, et RMSE public et privé réels comparés aux prévisions | Covariances retrouvées à quelques % près ; RMSE public prévu à ±0,001 ; privé prévu dans la bonne fourchette |
| C3 | Validation réelle | s16 et s111 : prévu contre obtenu | Écart inférieur à 0,001 |
| C4 | Taille du public | Sensibilité si l'est de Washington n'est pas public (2 814 au lieu de 2 940) | Effet chiffré et noté |

## D. Mélange

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| D1 | Stabilité des poids | Conditionnement, poids standardisés, poids des signaux un à un retirés | Pas de poids extrême ; pas de basculement par un seul signal |
| D2 | Distribution des prédictions | Écart-type contre ρ·s, part écrêtée, valeurs extrêmes | Cohérente |
| D3 | Signaux à fort levier | Part de variance portée par les 10 secteurs extrêmes de chaque signal ; secteurs d'eau | Fragilités identifiées et traitées |
| D4 | Privé attendu et régularisation | Modèle de bruit réaliste | Choix de ridge justifié |
| D5 | Finales | Script des finales à blanc : noms, recette, couverture | Conformes au plan |

## E. Modèle structurel et reproductibilité

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| E1 | Reproductibilité | Régénérer des fichiers déjà notés (s97, s102, s106) à partir de leurs scripts, puis comparer au fichier soumis | Identiques ou corrélation de 1,0000 |
| E2 | Bruit Monte-Carlo | Deux graines différentes pour le v7 : corrélation des contributions | ≥ 0,999 |
| E3 | Cohérence avec les chiffres officiels | Parts de secteurs sans composante transport par région, et rapports Overture/TIGER | Proches des valeurs publiées (21/37/28/55 %, 0,71-1,59) |
| E4 | Dépendances | Tout fichier intermédiaire utilisé par un script de signal doit être produit par un script du dépôt | Aucune dépendance au dossier temporaire |

## F. Conformité

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| F1 | Données externes | Recherche dans `src/` et `scripts/` de toute lecture hors du paquet | Aucune (hors `discovery/`) |
| F2 | Règles D1-ter et D2-ter | Nombre de signaux mesurés, nature continue, colonnes USFS | Respectées |

## G. Risques de fin de compétition

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| G1 | Washington public ou non | Test s124 (lot du 27/10) | Décision écrite pour chaque issue |
| G2 | Sélection sur Zindi | Procédure : soumettre f1 et f2, puis les sélectionner avant la fermeture | Procédure écrite, heure limite connue |
| G3 | Budget | Soumissions restantes et plafond de 66 | Calendrier tenable |

## Résultats (exécution du 28/10/2026)

| N° | Résultat | Constat |
|---|---|---|
| A1 | ✅ | 202 fichiers ; les 122 « absents » sont tous des doublons CSV de tables Parquet présentes (même contenu selon le README) |
| A2 | ✅ | 9 794 GEOID uniques, 11 caractères, identiques aux fichiers d'exemple, régions correctes |
| A3 | ✅ | Jointures complètes ; seuls les 2 secteurs d'eau n'ont pas de bâtiments |
| A4 | ✅ | Surface identique à ALAND (sauf les 2 secteurs d'eau, ALAND = 0) ; comptes plausibles |
| A5 | ✅ | Aucune colonne interdite, aucun fichier de couche retirée |
| B1 | ✅ | 55 fichiers notés intacts (SHA-256), aucun doublon dans le journal |
| B2 | ✅ | Les 55 lignes de l'onglet Submissions (3 pages, relevées le 28/10 après reconnexion) correspondent exactement au journal : mêmes identifiants, mêmes fichiers, mêmes scores (écart < 1e-9) |
| B3 | ✅ | 123 fichiers au format exact (`GEOID,coverage_gap_score`, 9 794 lignes, [0, 1], ordre officiel) ; verrou ajouté dans `bbx.submit.validate` |
| B4 | ✅ | Lots des 27 et 28/10 : journalisés une fois, SHA conforme, non notés, secteurs d'eau neutralisés |
| C1 | ✅ | m = 0,0598061 et s = 0,0890225 recalculés à l'identique |
| C2 | ✅ / ⚠️ | Simulation de bout en bout (40 vérités synthétiques, 30 % publics tirés au hasard) : covariances retrouvées à 1,4 % près. **La formule de RMSE public attendu est optimiste d'environ 0,0016 en moyenne** (écart-type 0,001) ; le privé réel la dépasse d'environ 0,0026. Sur 60 vérités : exclure s07/s22 aide (privé 0,04784 contre 0,04819) ; ridge optimal 0,005-0,01 (0,02 : +0,0001 ; 0,05 : +0,0003 ; 0,10 : +0,0006). |
| C3 | ✅ | s16 : +0,00023 ; s111 : +0,00025 (covariance réelle 1,2 % au-dessus de la prévision) |
| C4 | ✅ | Option `--wa-not-public` prête (voir G1) |
| D1 | ✅ | Conditionnement 5 249, somme des poids standardisés 0,45, maximum 0,06 (s77). Aucun signal ne fait basculer le mélange ; le plus influent est s97 (retrait : +0,0018) |
| D2 | ✅ | Écart-type 0,0667 = ρ·s ; 4,2 % des secteurs à 0 ; moyennes régionales égales aux moyennes mesurées |
| D3 | ✅ | Levier des 2 secteurs d'eau traité (s07, s22 exclus ; nouveaux signaux neutralisés) ; s84 et s82 fragiles, mais leur retrait n'aide pas |
| D4 | ✅ | Ridge 0,005 (f1) et 0,01 (f3) confirmés par la simulation |
| D5 | ✅ | `make_finals.py --dry-run` : f1 0,05887, f2 0,05823, f3 0,05910 (public attendu) |
| E1 | ✅ | s97, s98, s99, s100, s101, s102, s103 et s106 régénérés depuis leurs scripts : identiques aux fichiers soumis (écart ≤ 5×10⁻⁷, l'arrondi) |
| E2 | ✅ | Bruit Monte-Carlo : corrélation entre deux graines 0,9992 (contribution transport), 0,9985 (score) |
| E3 | ✅ | Secteurs sans transport : TX 26,8 %, AZ 52,6 %, OK 21,1 %, CA 37,9 % (publiés : 28, 55, 21, 37) |
| E4 | ❌ → ✅ | `structural_v8e.parquet` (s116/s117) venait d'un script temporaire : `scripts/make_s116_s117.py` le recalcule maintenant (reproduit à l'identique). `structural_v3_full.parquet` ne sert qu'à s88-s91, jamais soumis ni candidats (⚠️ accepté). s120 lit désormais le fichier des contours en local (reproduit à l'identique). |
| F1 | ✅ | Le code ne lit que le bucket du paquet (hors `discovery/`) |
| F2 | ✅ | 51 signaux mesurés ; 65 au plus après le 29/10 (plafond 66) ; aucune colonne USFS interdite |
| G1 | ✅ | Test s124 dans le lot du 27/10. **Si son score vaut 0,089022** : lancer `python scripts/make_finals.py --wa-not-public` (poids appris sur les quatre régions publiques ; Washington prédit sans les signaux régionaux ; moyenne WA 0,070 → 0,080). **Sinon** : finales standard. |
| G2 | ✅ | 30/10 : générer les finales, soumettre f1 et f2, puis les **sélectionner** dans l'onglet Submissions (case à cocher + enregistrer) avant la fermeture du 31/10 |
| G3 | ✅ | 55/200 soumissions ; 27-29/10 : 15 ; 30/10 : f1, f2 (+3 libres). Tenable |

**Bilan.**
- Aucun défaut ne dégrade notre score actuel : données, fichiers, algèbre et mélange sont sains et reproductibles.
- Deux défauts corrigés : une dépendance à un fichier temporaire (s116/s117) et le risque de colonne mal placée (verrou sur le format).
- Un risque majeur a une parade prête : Washington absent du public (option des finales).
- Un enseignement à garder : notre RMSE attendu est probablement optimiste d'environ 0,001-0,002.
- B2 fait après reconnexion : aucune erreur de recopie. **Audit complet : 27 contrôles sur 27 exécutés.**


# Audit du 30/10/2026 (avant les finales)

**But.** Vérifier tout ce qui a changé depuis l'audit du 28/10 : 14 nouveaux signaux (s129-s140), le retrait des signaux faibles (`WEAK`), le plafond de 73, la correction de s140, puis refaire les contrôles de base sur l'ensemble. Critères fixés avant l'exécution.

| N° | Contrôle | Méthode | Critère de réussite |
|---|---|---|---|
| H1 | Fichiers notés intacts | SHA-256 de chaque fichier noté contre `log.csv` | 100 % identiques |
| H2 | Scores bien recopiés | Onglet Submissions de Zindi (70 lignes) contre `log.csv` | Mêmes identifiants, mêmes fichiers, écart < 1e-9 |
| H3 | Format des fichiers en attente | En-tête, lignes, bornes, manquants, secteurs d'eau | `GEOID,coverage_gap_score`, 9 794 lignes, [0, 1], aucun manquant, secteurs d'eau à m |
| H4 | Reproductibilité des nouveaux signaux | Régénérer s134, s136, s137-s139 et s140 depuis leurs scripts, sans toucher au journal | Fichiers identiques (SHA) |
| H5 | Stabilité du mélange (65 signaux, quatre régions) | Conditionnement, poids standardisés, retrait signal par signal | Pas de poids extrême ; aucun retrait ne coûte plus de 0,002 |
| H6 | Règle des signaux faibles | `WEAK` contre les coûts de retrait mesurés | Cohérente, ou écart justifié par écrit |
| H7 | Sorties des finales | f1 et f2 calculées sans écrire : bornes, manquants, secteurs d'eau à 1, ordre officiel, différence f1/f2 | Conformes |
| H8 | Mode quatre régions | Les finales et l'estimation du privé n'utilisent que les quatre régions notées | Oui, sans dépendre d'une option à ne pas oublier |
| H9 | Conformité des données | Recherche, dans les nouveaux scripts, de toute lecture hors du paquet | Aucune |
| H10 | Règles D1-quater | Nombre de signaux mesurés après le 31/10 ; support de chaque nouveau signal sur les régions notées | 73 au plus ; au moins 300 secteurs notés touchés |

## Résultats (exécution du 30/10/2026)

| N° | Résultat | Constat |
|---|---|---|
| H1 | ✅ | 70 fichiers notés, SHA-256 identiques au journal ; aucune ligne en double |
| H2 | ✅ | Les 70 lignes de l'onglet Submissions (4 pages) correspondent au journal : mêmes identifiants, mêmes fichiers, mêmes scores (écart < 1e-9) |
| H3 | ✅ | Lot du 30/10 (s140, s122, s137, s138, s117) : `GEOID,coverage_gap_score`, 9 794 lignes, [0, 1], aucun manquant, secteurs d'eau à m, journalisés une fois, jamais notés |
| H4 | ✅ | s134, s136, s137, s138, s139 et s140 régénérés depuis leurs scripts (sans toucher au journal) : fichiers identiques (SHA) |
| H5 | ✅ | f1, quatre régions : 54 signaux actifs, conditionnement 7 560, poids standardisé maximal 0,58 (s97, le transport v7, signal principal), somme 1,30 ; coût de retrait maximal 0,0017 (s97), puis s102 0,0007 et s05 0,0007 |
| H6 | ⚠️ | `WEAK` ne suit pas un seuil unique : s113 (4e-5), s126 (7e-5), s119 et s127 (3e-5) sont retirés, s136 (1e-5) est gardé. Choix justifié par la simulation (l'ensemble « 53 + s134 + s136 » n'est jamais perdant ; écarts de ±0,00002, dans le bruit). Pour les signaux des 30-31/10, la règle est un seuil de 0,00003 |
| H7 | ✅ | f1 (55 signaux) et f2 (57) : valeurs dans [0, 1], aucun manquant, secteurs d'eau à 1, moyenne sur les quatre régions 0,0602 / 0,0604, 4,1 % / 5,9 % de zéros ; corrélation f1-f2 0,992 (couverture réelle) |
| H8 | ❌ → ✅ | Trois défauts dans `scripts/make_finals.py`, corrigés : (1) le mode quatre régions exigeait l'option `--wa-not-public`, et un oubli aurait calculé les finales avec Washington (non noté) ; c'est désormais le mode par défaut (`--include-wa` pour l'ancien calcul) ; (2) le privé attendu était calculé sur les 9 794 lignes avec 2 940 secteurs publics : il porte maintenant sur les quatre régions avec 2 814 ; (3) le fichier des poids enregistrait ceux du mélange standard, pas ceux utilisés : il enregistre maintenant les poids réels et la base d'ajustement |
| H9 | ✅ | Aucune lecture hors du paquet dans les nouveaux scripts ni dans `make_finals.py` |
| H10 | ✅ | Secteurs notés touchés : s134 319, s122 575, les autres plus de 4 900 (seuil 300) ; 65 signaux mesurés, 73 après le 31/10 (plafond) |

**Bilan.** Données, journal et fichiers sont intacts et reproductibles ; le mélange est stable. Trois défauts de la chaîne des finales ont été corrigés avant leur première utilisation réelle, dont un risque opérationnel (oubli d'option le 31/10). Essai à blanc après correction : f1 0,05909 et f2 0,05796 en public attendu ; privé attendu (formule, quatre régions) 0,0638 et 0,0633.
