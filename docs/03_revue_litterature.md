# Revue de littérature ciblée : ce qui aide vraiment (20/10/2026)

*Objectif : trouver dans la littérature et la documentation officielle ce qui peut améliorer (1) notre score, (2) le Bias Discovery, (3) la documentation. Chaque point se termine par sa conséquence concrète pour nous.*

## 1. Comment sont construites les références (classement)

| Référence | Ce que dit la documentation | Conséquence pour nous |
|---|---|---|
| **TIGER S1100 / S1200** | S1100 = autoroutes à accès limité (Interstate ou gérées par l'État), avec échangeurs. S1200 = artères principales sans accès limité, « usually in the U.S. Highway, State Highway, **and/or County Highway** system », souvent avec un numéro de route. | Confirme notre proxy « routes numérotées » **y compris une partie des routes de comté**. C'est cohérent avec notre calibration de l'Oklahoma (environ 59 % des 25 000 km de routes de comté) et de l'Arizona (toutes les routes numérotées). |
| **Empreintes Microsoft US** | Version 1.1 du 13 juillet 2018. Réseau de neurones sur imagerie Bing **de dates variées** ; qualité moindre en zone urbaine dense. | La référence « bâtiments » est antérieure à tous les feux de 2019 à 2025. Elle confirme l'argument du Bias Discovery : la composante bâtiments ne voit pas les destructions récentes. |
| **USGS National Map Structures** (casernes, EMS, écoles) | Données venant de partenaires des États et du gouvernement fédéral, complétées par des bénévoles TNMCorps ; mises à jour continues. | La complétude dépend de l'État et du comté. Elle explique une partie des **écarts régionaux** du terme casernes, déjà captés par nos indicateurs de région. |
| **CBP** | Publié par comté et par code postal (ZBP), pas par secteur. Le passage code postal → secteur se fait typiquement par le croisement HUD-USPS (`BUS_RATIO`, part des **adresses d'entreprises** d'un code postal dans un secteur) ou par recouvrement de surface ZCTA → secteur. | Notre hypothèse « répartition par population » est contredite par le classement (corrélation −0,09). Les répartitions par surface et par code postal sont testées (s24, s42, s43). Le croisement HUD donnerait des établissements proches de la distribution des lieux, donc des écarts CBP rares. |

## 2. Comment Overture fusionne ses sources

- **Bâtiments** (notes de publication Overture) :
  - priorité OSM > Esri Community Maps > Google haute précision > Microsoft ML > Google basse précision ;
  - une empreinte ML n'est ajoutée que **si elle ne touche aucun bâtiment OSM ou Esri** ;
  - conséquence : là où OSM dessine de grands polygones fusionnés (en moyenne 522 m² contre 181 m² pour Microsoft dans nos données), Overture compte **moins** de structures que la référence Microsoft, d'où un écart de composante bâtiments.
- **Routes** :
  - la `class` d'Overture reprend le tag OSM `highway` et les `routes` reprennent les relations de route ;
  - au Texas, la convention OSM classe les routes **Farm-to-Market en tertiary**, donc hors des classes comptées par la métrique, alors que TIGER les compte probablement en S1200 (réseau de l'État) ;
  - c'est le mécanisme principal de l'écart transport au Texas, déjà dans notre modèle.
- **Lieux** : sources commerciales (Meta, Microsoft, Foursquare, BrightQuery…), sans OSM. La catégorie `categories.primary` n'est pas la vérité terrain (casernes mal classées, hôpitaux 12 fois plus nombreux que dans HIFLD).
- **Signaux testés à partir de ces lectures** (part des routes FM en tertiary, bâtiments OSM fusionnés) : déjà expliqués à 59-89 % par notre base. La littérature **confirme** nos mécanismes, mais ne débloque pas de signal majeur nouveau.

## 3. Estimer la complétude sans référence

- Trois familles de méthodes :
  - **comparaison à une référence** (impossible ici) ;
  - **indicateurs intrinsèques** : historique d'édition, courbes de saturation ;
  - **modèles statistiques à covariables** : densité, socio-économie, gradient urbain-rural. Herfort et al. 2023 (*Nature Communications*) utilisent un GAM sur 13 189 agglomérations.
- Limite connue : ces modèles transfèrent mal entre régions et le long du gradient urbain-rural. Cela justifie nos **effets régionaux** et nos signaux par région.
- Barrington-Leigh et Millard-Ball (2017) : la complétude des routes OSM se modélise par régression multiniveau et post-stratification, ce qui conforte l'idée de régulariser les poids par groupe.
- Utiliser le leaderboard comme oracle :
  - Blum et Hardt (2015, « The Ladder ») : n'accepter qu'une amélioration qui dépasse le bruit ;
  - Whitehill (2017) : risques d'extraction de labels par oracle.

  Ces travaux encadrent notre règle D1-bis : poids globaux seulement, ridge, pas de sondage par secteur.
- Apprentissage à partir d'agrégats (Zhang et al., NeurIPS 2020) : la régression sur des moyennes de groupe est consistante. C'est le fondement théorique de notre mélange calibré sur covariances.

## 4. Bias Discovery : la carte après un désastre

- **Les pratiques OSM créent le retard.** Dans un fil récent sur les incendies de Los Angeles (2025), on conseille aux contributeurs de **ne pas supprimer** les bâtiments brûlés, mais de les re-taguer avec un préfixe de cycle de vie (`destroyed:building`), et souvent d'attendre que l'imagerie soit mise à jour. Tant que personne ne le fait, et tant que les empreintes Microsoft proviennent d'images antérieures au feu, la carte reste figée.

  C'est exactement le mécanisme de nos fantômes. Il donne à la candidature une explication causale et une piste de remédiation :
  1. re-taguer les bâtiments à partir des données d'inspection DINS ;
  2. dater les sources ML.
- **Les produits d'exposition utilisent ces empreintes.** USFS Wildfire Risk to Communities construit ses comptages de bâtiments, de logements et d'exposition à partir d'empreintes de bâtiments (Microsoft v1.1 en première édition ; la 2e édition annonce des entrées « conditions 2022 », point à confirmer). Ces produits servent à planifier l'exposition et à attribuer des aides comme le Community Wildfire Defense Grant.

  Des empreintes figées surestiment donc l'exposition dans les zones brûlées récemment. C'est une conséquence concrète et documentée à citer.
- **Données CAL FIRE DINS** : inspection structure par structure. CAL FIRE précise que les cartes sont en cours lors des incidents et que tout n'est pas inspecté, une limite déjà mentionnée dans notre candidature.
- **Nouveauté** : aucune étude trouvée ne mesure combien de temps les bâtiments détruits restent sur une carte ouverte après un feu. Notre mesure (30 % pour les feux de 2020 à 2025, 0,2 % avant) semble **inédite**.

## 5. Documentation : standards à suivre

- *Datasheets for Datasets* (Gebru et al.) : motivation, composition, collecte, prétraitement, maintenance. Nous en ferons un **datasheet de la table de features**.
- *Model Cards* (Mitchell et al. 2019) : usage visé, évaluation, limites. Nous en ferons une **model card du mélange** : ρ mesuré, RMSE attendu contre observé, limites.
- Checklists de reproductibilité (NeurIPS ; Pineau et al. 2020) : seeds, versions, temps de calcul, matériel, scripts. Nous avons déjà tout cela ; il faut le présenter sous forme de checklist cochée.
- Guide Zindi « documentation guideline » et « how to ensure success when submitting your code for review » (liens sur la page Info) : à suivre pour la revue de code du top 10.

## 6. Point important : les colonnes USFS de bâtiments

- La colonne `usfs_edition` de nos strates indique **« WRC v2 (RDS-2020-0016-2 / RDS-2020-0060-2 / RDS-2024-0030) »**.
- D'après un extrait indexé de la métadonnée RDS-2020-0060-2 (la page complète renvoie une erreur 403), la v2 met à jour ses entrées « to 2022 conditions » avec des empreintes **Onegeo et USA Structures**. Si c'est exact, ces colonnes **ne dérivent pas** des empreintes Microsoft retirées, contrairement à ce que dit notre message sur le Chat (#35402).
- **À faire :** préciser ce point au staff, par une courte réponse sous notre message, pour que la décision repose sur une information exacte. C'est une publication, donc soumise à l'accord de l'utilisatrice. Notre règle D2-ter reste inchangée : pas d'usage sans feu vert explicite.

## 7. Compléments Scopus (24/10/2026) : articles relus par les pairs

Recherche faite en lecture seule sur Scopus (titre, résumé, mots-clés), 14 requêtes. **Aucun article ne change le modèle** : tous confirment des mécanismes déjà mesurés. Ils servent à appuyer la Documentation et la Bias Discovery par des sources relues.

| Référence | Ce qu'elle établit | Usage chez nous |
|---|---|---|
| Zielstra, Hochmair & Neis (2013), *Transactions in GIS* 17(3), 315–334 | TIGER/Line 2005 importé dans OSM début 2008 ; dans presque tous les États, OSM a moins de routes motorisées que TIGER, plus de chemins piétons | Les routes d'Overture (issues d'OSM) partagent la géométrie de TIGER : l'écart vient du classement et du balisage, pas du tracé (v6, v7) |
| Li, Maha Gamage, Cao, …, Siebeneck (2025), *Transactions in GIS* 29(4), e70077 | OSM contre TIGER, par comté, États-Unis contigus : complétude et précision meilleures dans les comtés métropolitains que ruraux | Gradient rural du transport ; section Documentation 2 |
| Heris, Foks, Bagstad, Troy & Ancona (2020), *Scientific Data* 7, 207 | Empreintes Microsoft US : précision élevée ; rappel élevé au-dessus de 200 m², plus faible pour les petits bâtiments | La référence rate les petits bâtiments, donc O/R > 1 là où OSM a des petits bâtiments dessinés à la main : déjà mesuré (s27, `features_bldref` hand_only) |
| Carlson, Helmers, Hawbaker, Mockrin & Radeloff (2022), *Ecological Applications* 32(5), e2597 | WUI des États-Unis à partir de 125 M de bâtiments Microsoft ; grands écarts avec les cartes issues du recensement, dus aux bâtiments non résidentiels en zone rurale | Appui direct à la limite « bâtiment ≠ logement » de la Bias Discovery |
| Gevaert, Buunk & van den Homberg (2024), *IEEE JSTARS* 17, 12579–12590 | Audit de biais de quatre jeux de bâtiments (Google, Microsoft, Overture, OSM) en Tanzanie et aux Philippines ; les biais varient selon le jeu et le pays | Précédent méthodologique pour la Bias Discovery |
| Herfort, Lautenbach, Porto de Albuquerque, Anderson & Zipf (2023), *Nature Communications* 14, 3985 | Complétude et inégalités des bâtiments OSM dans les villes du monde | Cadre général des inégalités de couverture |
| Haklay (2010), *Environment and Planning B* 37(4), 682–703 | Première comparaison OSM contre une référence officielle (Ordnance Survey) | Méthode de base des écarts O/R |
| Bourbonnais, Bastien, Brosseau & Morency (2026), *Transportation Research Procedia* 97, 666–675 | 1 034 lieux validés (Québec) : couverture Google 99,2 %, rôle d'évaluation 92,1 %, OSM 72,8 %, Overture 72,4 % ; erreur médiane de position 20–50 m | Les lieux proches des limites de tract comptent (`intersects`) ; Overture n'est pas plus complet qu'OSM |
| Rahman, Oliver, Buehler, …, Kim (2025), *Transportation Research Part A* 195, 104429 | En Virginie, les POI ponctuels d'OSM sous-estiment l'accessibilité et faussent les indices d'inégalité par rapport à Google | Le manque de POI est systématique, pas aléatoire |
| Ballantyne & Berragan (2024), *Environment and Planning B* 51(8) | Lieux Overture au Royaume-Uni validés contre les supermarchés Geolytix | Validation externe d'Overture Places |
| Dwork, Feldman, Hardt, Pitassi, Reingold & Roth (2015), *Science* 349(6248), 636–638 | Réutiliser un jeu de test de façon adaptative crée du sur-apprentissage | Justifie la limite de 66 signaux (D1-ter) et la correction d'optimisme de `make_finals.py`, avec *The Ladder* (Blum & Hardt 2015) |

Recherches sans résultat utile : classement TIGER/MTFCC et Functional Class (1 seul article, hors sujet), complétude des casernes de pompiers dans les POI, County Business Patterns contre POI (0 résultat).

## Sources

- [Métadonnées TIGER Primary/Secondary Roads (TTU)](https://www.depts.ttu.edu/geospatial/center/Data/TxStateLayers/Tx_Transportation/_Metadata/Tx_Roads_Detail_TIGER_Metadata.html)
- [TIGER/Line Primary and Secondary Roads (data.gov)](https://catalog.data.gov/dataset/tiger-line-shapefile-2022-state-guam-primary-and-secondary-roads)
- [USGS National Map Structures Content](https://www.usgs.gov/ngp-standards-and-specifications/national-map-structures-content)
- [Métadonnées Structures (Wisconsin)](https://geodata.wisc.edu/catalog/41EB859C-AB4A-49FB-B03F-F54DE3200B05/metadata)
- [ScienceBase Structures](https://sciencebase.gov/catalog/item/4f70b240e4b058caae3f8e1b)
- [HUD USPS ZIP crosswalk](https://huduser.gov/portal/node/7785)
- [Cityscape : utiliser le crosswalk HUD](https://www.huduser.gov/PORTAL/periodicals/cityscpe/vol20num2/ch16.pdf)
- [zippeR : conversion des codes postaux](https://brieger.esalq.usp.br/CRAN/web/packages/zippeR/vignettes/converting-zips.html)
- [Métadonnées Microsoft US Building Footprints v1.1 (Cornell CUGIR)](https://geodiscovery.uwm.edu/catalog/cugir-009081/metadata)
- [Notes de publication Overture, décembre 2023](https://overturemaps.org/overture-december-2023-release-notes/)
- [Webinaire Overture (sources des bâtiments)](https://project.linuxfoundation.org/hubfs/Overture%20Maps/OMF%20Webinar.pdf)
- [Overture : segments de transport](https://docs.overturemaps.org/schema/concepts/by-theme/transportation/segments)
- [Overture : routes](https://docs.overturemaps.org/schema/concepts/by-theme/transportation/roads)
- [Wiki OSM : Texas](https://wiki.openstreetmap.org/wiki/Texas/Map_features)
- [Wiki OSM : US Roadway Classification Guidelines](https://wiki.openstreetmap.org/wiki/United_States_Roadway_Classification_Guidelines)
- [Imports OSM en Oklahoma (Murray)](https://wiki.openstreetmap.org/wiki/Oklahoma/Import/Murray)
- [Herfort et al. 2023](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10326063/)
- [Complétude OSM avec MapSwipe (HeiGIT)](https://heigit.org/assessing-completeness-of-openstreetmap-building-footprints-using-mapswipe/)
- [Méthodes intrinsèques (SotM 2026)](https://pretalx.com/sotm2026-osm-science/talk/KYSVEE/)
- [GFZ : complétude des bâtiments](https://gfzpublic.gfz-potsdam.de/pubman/item/item_5017501_1/component/file_5017516/5017501.pdf)
- [Fil OSM : bâtiments détruits par les feux de Los Angeles](https://community.openstreetmap.org/t/los-angeles-researcher-removing-buildings-destroyed-by-wildfires/125976)
- [Aide OSM : que tagger après un incendie](https://help.openstreetmap.org/questions/76552/what-do-we-mark-after-a-fire-emergency-on-openstreetmap)
- [Liste Tagging OSM (2020)](https://lists.openstreetmap.org/pipermail/tagging/2020-September/055532.html)
- [Carte CAL FIRE du Camp Fire](https://wildfiretoday.com/cal-fire-releases-map-showing-status-of-structures-affected-by-camp-fire/)
- [USFS Wildfire Risk to Communities, métadonnées v2](https://www.fs.usda.gov/rds/archive/products/RDS-2020-0060-2/_metadata_RDS-2020-0060-2.html)
- [USFS Building Count (Ag Data Commons)](https://agdatacommons.nal.usda.gov/articles/dataset/Wildfire_Risk_to_Communities_Building_Count_Image_Service_/27365748)
- [Méthodes CWDG (USFS)](https://www.fs.usda.gov/sites/default/files/2022-08/CWDG-Risk-Dataset-Methods.pdf)
- [Revue cartographie WUI (UNL)](https://run.unl.pt/bitstreams/8e8d8b0f-e30c-4a39-a26e-7ca2595ea19e/download)
- [Cartes de données et de modèles (arXiv 2108.07374)](https://arxiv.org/pdf/2108.07374)
- [Reproductibilité en ML (arXiv 2406.14325)](https://arxiv.org/pdf/2406.14325)
- [The Ladder](https://arxiv.org/pdf/1502.04585)
- [Whitehill 2017](https://arxiv.org/pdf/1707.01825)
- [Learning from Aggregate Observations](https://papers.nips.cc/paper_files/paper/2020/file/5b0fa0e4c041548bb6289e15d865a696-Paper.pdf)
- [Barrington-Leigh & Millard-Ball 2017](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5552279/)
