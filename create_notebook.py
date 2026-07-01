import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"# TP Data Integration & Applications — ST2DLDI\n"
"**Dataset :** Accidents corporels de la circulation routière — France 2024 (data.gouv.fr)  \n"
"**Architecture :** Medallion (Bronze → Silver → Gold)"
))

cells.append(nbf.v4.new_markdown_cell("## Partie 1 — Data Profiling & Data Quality"))

cells.append(nbf.v4.new_markdown_cell("### Chargement des données (couche Bronze)"))

cells.append(nbf.v4.new_code_cell(
"import pandas as pd\n"
"import numpy as np\n"
"\n"
"caract    = pd.read_csv('data/caract-2024.csv',    sep=';', encoding='latin1', low_memory=False)\n"
"lieux     = pd.read_csv('data/lieux-2024.csv',     sep=';', encoding='latin1', low_memory=False)\n"
"usagers   = pd.read_csv('data/usagers-2024.csv',   sep=';', encoding='latin1', low_memory=False)\n"
"vehicules = pd.read_csv('data/vehicules-2024.csv',  sep=';', encoding='latin1', low_memory=False)\n"
"\n"
"tables = {\n"
"    'caracteristiques': caract,\n"
"    'lieux':            lieux,\n"
"    'usagers':          usagers,\n"
"    'vehicules':        vehicules,\n"
"}\n"
"\n"
"for name, df in tables.items():\n"
"    print(f'  {name:<20} {len(df):>7} lignes  {df.shape[1]} colonnes')"
))

cells.append(nbf.v4.new_markdown_cell("### Exploration rapide des données"))

cells.append(nbf.v4.new_code_cell(
"#premières lignes de chaque table\n"
"caract.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"lieux.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"usagers.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"vehicules.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"#statistiques descriptives\n"
"caract.describe()"
))

cells.append(nbf.v4.new_code_cell(
"usagers.describe()"
))

cells.append(nbf.v4.new_markdown_cell("### A. Structure des tables"))

cells.append(nbf.v4.new_code_cell(
"for name, df in tables.items():\n"
"    print(f'--- {name.upper()} ---')\n"
"    for col, dtype in df.dtypes.items():\n"
"        print(f'  {col:<30} {str(dtype)}')\n"
"    print()"
))

cells.append(nbf.v4.new_markdown_cell(
"### A. Semantic meaning — signification des colonnes\n\n"
"**Source :** \"Description des bases de donnees annuelles des accidents corporels de la circulation "
"routiere - Annees de 2005 a 2024\" (ONISR, data.gouv.fr, ressource id 8ef4c2a3-91a0-4d98-ae3a-989bde87b62a). "
"Les codes ci-dessous sont verifies contre ce document (pages 4 a 13, liste complete des champs). "
"Liste non exhaustive : quelques colonnes cles par table pour montrer la comprehension du schema.\n\n"
"**Table caracteristiques** (1 ligne = 1 accident)\n\n"
"| Colonne | Signification |\n"
"|---|---|\n"
"| Num_Acc | Identifiant unique de l'accident |\n"
"| lum | Conditions d'eclairage (1=plein jour, 2=crepuscule, 3=nuit sans eclairage, ...) |\n"
"| atm | Conditions meteorologiques (1=normale, 2=pluie, 3=neige, ...) |\n"
"| col | Type de collision (1=frontal, 2=arriere, 3=cote, ...) |\n\n"
"**Table lieux** (caracteristiques de la route)\n\n"
"| Colonne | Signification |\n"
"|---|---|\n"
"| catr | Categorie de route (1=autoroute, 2=nationale, 3=departementale, ...) |\n"
"| surf | Etat de la surface (1=normale, 2=mouillee, 3=flaques, ...) |\n"
"| vma | Vitesse maximale autorisee |\n\n"
"**Table usagers** (1 ligne = 1 personne impliquee)\n\n"
"| Colonne | Signification |\n"
"|---|---|\n"
"| catu | Categorie d'usager (1=conducteur, 2=passager, 3=pieton) |\n"
"| grav | Gravite (1=indemne, 2=tue, 3=blesse hospitalise, 4=blesse leger) |\n"
"| secu1 | Equipement de securite (1=ceinture, 2=casque, 3=dispositif enfants, ...) |\n\n"
"**Table vehicules** (1 ligne = 1 vehicule implique)\n\n"
"| Colonne | Signification |\n"
"|---|---|\n"
"| catv | Categorie de vehicule (1=bicyclette, 2=cyclomoteur, 7=voiture, ...) |\n"
"| choc | Point de choc initial (1=avant, 2=avant droit, 3=avant gauche, ...) |\n"
"| motor | Type de motorisation (1=hydrocarbures, 2=hybride, 3=electrique, ...) |"
))

cells.append(nbf.v4.new_markdown_cell("### B. Valeurs manquantes"))

cells.append(nbf.v4.new_code_cell(
"for name, df in tables.items():\n"
"    print(f'--- {name.upper()} ---')\n"
"    missing = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)\n"
"    missing = missing[missing > 0]\n"
"    if missing.empty:\n"
"        print('  aucune valeur manquante')\n"
"    else:\n"
"        for col, pct in missing.items():\n"
"            flag = ' CRITIQUE' if pct > 20 else ''\n"
"            print(f'  {col:<30} {pct:.1f}%{flag}')\n"
"    print()"
))

cells.append(nbf.v4.new_markdown_cell("### C. Cohérence et validité"))

cells.append(nbf.v4.new_code_cell(
"#separation Metropole / DOM-TOM par code departement\n"
"#(un seuil de latitude est peu fiable : Saint-Pierre-et-Miquelon, dep 975, a une latitude\n"
"# dans la plage metropolitaine 41-52, et le sud de la Corse, dep 2B, peut descendre sous 41)\n"
"DOMTOM_DEP = {'971', '972', '973', '974', '975', '976', '977', '978', '986', '987', '988'}\n"
"hors_metro = caract['dep'].astype(str).isin(DOMTOM_DEP).sum()\n"
"print(f'Coordonnees hors France metro (DOM-TOM) : {hors_metro}')\n"
"\n"
"#valeurs negatives\n"
"for col in ['grav', 'sexe', 'place']:\n"
"    neg = (usagers[col] < 0).sum()\n"
"    if neg > 0:\n"
"        print(f'usagers.{col} : {neg} valeurs negatives (-1 = non renseigne)')\n"
"\n"
"#ages (derives depuis an_nais)\n"
"age = 2024 - usagers['an_nais']\n"
"ages_negatifs = (age < 0).sum()\n"
"ages_aberrants = (age > 110).sum()\n"
"print(f'Ages negatifs : {ages_negatifs}')\n"
"print(f'Ages > 110 ans (aberrants) : {ages_aberrants}')\n"
"\n"
"#doublons\n"
"print()\n"
"for name, df in tables.items():\n"
"    dup = df.duplicated().sum()\n"
"    print(f'  {name:<20} {dup} doublon(s)')"
))

cells.append(nbf.v4.new_markdown_cell("### C. Anomalies catégorielles"))

cells.append(nbf.v4.new_code_cell(
"#valeurs attendues par colonne categorielle\n"
"categories_attendues = {\n"
"    'grav':   [1, 2, 3, 4],\n"
"    'sexe':   [1, 2],\n"
"    'catu':   [1, 2, 3, 4],\n"
"    'trajet': [0, 1, 2, 3, 4, 5, 9],\n"
"}\n"
"\n"
"for col, valides in categories_attendues.items():\n"
"    valeurs_uniques = usagers[col].dropna().unique()\n"
"    inattendues = [v for v in valeurs_uniques if v not in valides]\n"
"    if inattendues:\n"
"        print(f'usagers.{col} : valeurs inattendues -> {inattendues}')\n"
"    else:\n"
"        print(f'usagers.{col} : OK (valeurs = {sorted(valeurs_uniques.tolist())})')\n"
"\n"
"print()\n"
"#verification colonne lum et atm dans caract\n"
"for col, valides in {'lum': [1,2,3,4,5], 'atm': [1,2,3,4,5,6,7,8,9]}.items():\n"
"    vals = caract[col].dropna().unique()\n"
"    inattendues = [v for v in vals if v not in valides]\n"
"    if inattendues:\n"
"        print(f'caract.{col} : valeurs inattendues -> {inattendues}')\n"
"    else:\n"
"        print(f'caract.{col} : OK')"
))

cells.append(nbf.v4.new_markdown_cell(
"### D. Résumé qualité\n\n"
"| Problème | Colonne | Action |\n"
"|---|---|---|\n"
"| 100% vide | lieux.lartpc | Supprimer |\n"
"| 99% vide | vehicules.occutc | Supprimer |\n"
"| 91.6% vide | lieux.v2 | Supprimer |\n"
"| 19% vide | lieux.voie | Imputer 'Inconnu' |\n"
"| 4.2% vide | caract.adr | Imputer 'Inconnu' |\n"
"| Hors métropole | dep | Séparer DOM-TOM (par code departement) |\n"
"| Valeurs -1 | sexe, place, col | Remplacer par NaN |\n"
"| Doublons | lieux | Supprimer (2 lignes) |\n\n"
"### D. Impact analysis\n\n"
"- Colonnes vides : inutilisables, a exclure avant tout traitement\n"
"- Valeurs -1 dans `grav` et `sexe` : faussent les moyennes et distributions\n"
"- Coordonnees hors metro : biaiseraient toute analyse geographique ou cartographique\n"
"- Doublons dans `lieux` : gonfleraient les comptages sur certaines routes"
))

cells.append(nbf.v4.new_markdown_cell("## Partie 2A — Transformations (couche Silver)"))

cells.append(nbf.v4.new_code_cell(
"#1. suppression colonnes trop vides\n"
"lieux     = lieux.drop(columns=['lartpc', 'v2'])\n"
"vehicules = vehicules.drop(columns=['occutc'])\n"
"\n"
"#2. doublons\n"
"lieux = lieux.drop_duplicates()\n"
"\n"
"#3. conversion coordonnées GPS\n"
"caract['lat']  = pd.to_numeric(caract['lat'].str.replace(',', '.'),  errors='coerce')\n"
"caract['long'] = pd.to_numeric(caract['long'].str.replace(',', '.'), errors='coerce')\n"
"\n"
"#4. séparation métropole / DOM-TOM (par code departement, plus fiable qu'un seuil de latitude)\n"
"DOMTOM_DEP = {'971', '972', '973', '974', '975', '976', '977', '978', '986', '987', '988'}\n"
"est_domtom   = caract['dep'].astype(str).isin(DOMTOM_DEP)\n"
"dom_tom      = caract[est_domtom]\n"
"caract_metro = caract[~est_domtom].copy()\n"
"print(f'DOM-TOM mis de cote : {len(dom_tom)} lignes')\n"
"print(f'Metropole conservee : {len(caract_metro)} lignes')\n"
"\n"
"#5. remplacement des -1 par NaN\n"
"for col in ['sexe', 'place', 'trajet', 'secu1', 'secu2', 'secu3', 'locp', 'etatp']:\n"
"    usagers[col] = usagers[col].replace(-1, np.nan)\n"
"caract_metro['col'] = caract_metro['col'].replace(-1, np.nan)\n"
"\n"
"#6. imputation valeurs manquantes texte\n"
"caract_metro['adr'] = caract_metro['adr'].fillna('Inconnu')\n"
"lieux['voie']       = lieux['voie'].fillna('Inconnu')\n"
"\n"
"#7. colonne date\n"
"caract_metro['date'] = pd.to_datetime(\n"
"    caract_metro[['an', 'mois', 'jour']].rename(columns={'an': 'year', 'mois': 'month', 'jour': 'day'}),\n"
"    errors='coerce'\n"
")\n"
"\n"
"#8. enrichissement tranche horaire\n"
"caract_metro['heure'] = caract_metro['hrmn'].str[:2].astype(float, errors='ignore')\n"
"\n"
"def categorie_horaire(h):\n"
"    if pd.isna(h):   return 'Inconnu'\n"
"    if 6  <= h < 12: return 'Matin'\n"
"    if 12 <= h < 18: return 'Apres-midi'\n"
"    if 18 <= h < 22: return 'Soir'\n"
"    return 'Nuit'\n"
"\n"
"caract_metro['tranche_horaire'] = caract_metro['heure'].apply(categorie_horaire)\n"
"\n"
"#9. enrichissement gravite max par accident\n"
"gravite_max = usagers.groupby('Num_Acc')['grav'].max().reset_index()\n"
"gravite_max.columns = ['Num_Acc', 'gravite_max']\n"
"caract_metro = caract_metro.merge(gravite_max, on='Num_Acc', how='left')\n"
"\n"
"#sauvegarde Silver\n"
"caract_metro.to_csv('data/silver_caract.csv',    index=False)\n"
"lieux.to_csv(        'data/silver_lieux.csv',     index=False)\n"
"usagers.to_csv(      'data/silver_usagers.csv',   index=False)\n"
"vehicules.to_csv(    'data/silver_vehicules.csv', index=False)\n"
"print('[OK] fichiers Silver sauvegardes')"
))

cells.append(nbf.v4.new_markdown_cell("## Partie 2B — Modélisation (couche Gold)"))

cells.append(nbf.v4.new_code_cell(
"caract_s    = pd.read_csv('data/silver_caract.csv',    low_memory=False)\n"
"lieux_s     = pd.read_csv('data/silver_lieux.csv',     low_memory=False)\n"
"usagers_s   = pd.read_csv('data/silver_usagers.csv',   low_memory=False)\n"
"vehicules_s = pd.read_csv('data/silver_vehicules.csv', low_memory=False)\n"
"\n"
"#table de faits\n"
"fait_accidents = caract_s[[\n"
"    'Num_Acc', 'date', 'tranche_horaire', 'gravite_max',\n"
"    'atm', 'col', 'lum', 'agg', 'dep'\n"
"]].rename(columns={\n"
"    'atm': 'meteo', 'col': 'type_collision',\n"
"    'lum': 'eclairage', 'agg': 'en_agglomeration', 'dep': 'departement'\n"
"})\n"
"\n"
"#dimension lieu\n"
"dim_lieu = lieux_s[[\n"
"    'Num_Acc', 'catr', 'surf', 'infra', 'situ', 'vma', 'prof', 'plan'\n"
"]].rename(columns={\n"
"    'catr': 'type_route', 'surf': 'etat_surface', 'infra': 'infrastructure',\n"
"    'situ': 'situation', 'vma': 'vitesse_max', 'prof': 'profil_route', 'plan': 'trace_plan'\n"
"})\n"
"\n"
"#dimension vehicule\n"
"dim_vehicule = vehicules_s[[\n"
"    'Num_Acc', 'id_vehicule', 'catv', 'manv', 'obs', 'obsm', 'choc', 'motor'\n"
"]].rename(columns={\n"
"    'catv': 'type_vehicule', 'manv': 'manoeuvre', 'obs': 'obstacle_fixe',\n"
"    'obsm': 'obstacle_mobile', 'choc': 'point_choc', 'motor': 'motorisation'\n"
"})\n"
"\n"
"#dimension usager\n"
"dim_usager = usagers_s[[\n"
"    'Num_Acc', 'id_usager', 'catu', 'grav', 'sexe', 'an_nais', 'trajet', 'secu1'\n"
"]].rename(columns={\n"
"    'catu': 'categorie_usager', 'grav': 'gravite', 'an_nais': 'annee_naissance',\n"
"    'trajet': 'motif_trajet', 'secu1': 'equipement_securite'\n"
"})\n"
"\n"
"#sauvegarde Gold\n"
"fait_accidents.to_csv('data/gold_fait_accidents.csv', index=False)\n"
"dim_lieu.to_csv(      'data/gold_dim_lieu.csv',       index=False)\n"
"dim_vehicule.to_csv(  'data/gold_dim_vehicule.csv',   index=False)\n"
"dim_usager.to_csv(    'data/gold_dim_usager.csv',     index=False)\n"
"\n"
"print(f'fait_accidents : {len(fait_accidents)} lignes')\n"
"print(f'dim_lieu       : {len(dim_lieu)} lignes')\n"
"print(f'dim_vehicule   : {len(dim_vehicule)} lignes')\n"
"print(f'dim_usager     : {len(dim_usager)} lignes')\n"
"print('[OK] fichiers Gold sauvegardes')"
))

cells.append(nbf.v4.new_markdown_cell(
"## Partie 2C — Diagramme Medallion Architecture\n\n"
"![Medallion Architecture](medallion_drawio.png)"
))

cells.append(nbf.v4.new_markdown_cell(
"## Justification des choix de conception\n\n"
"### 1. Suppression des colonnes quasi vides\n"
"Les colonnes `lartpc` (100% vide), `v2` (91.6% vide) et `occutc` (99% vide) ont ete supprimees. "
"Une colonne avec presque aucune donnee n'apporte aucune information exploitable.\n\n"
"### 2. Traitement des DOM-TOM\n"
"Les 3 344 accidents dont le code departement est 971-978 ou 986-988 correspondent aux "
"territoires d'outre-mer. Ce ne sont pas des erreurs. La separation se fait sur le code "
"departement plutot que sur un seuil de latitude (moins fiable : Saint-Pierre-et-Miquelon, "
"dep 975, a une latitude dans la plage metropolitaine, et le sud de la Corse peut descendre "
"sous 41 degres). Nous avons mis ces lignes de cote pour limiter l'analyse a la France "
"metropolitaine, tout en les conservant pour une etude ulterieure.\n\n"
"### 3. Remplacement des -1 par NaN\n"
"Dans ce dataset, -1 signifie 'non renseigne'. Le laisser tel quel fausserait les calculs "
"statistiques. NaN est la convention standard pour une valeur inconnue en pandas.\n\n"
"### 4. Imputation 'Inconnu' sur les champs texte\n"
"Plutot que supprimer une ligne entiere a cause d'une adresse manquante, on conserve l'accident "
"et on impute 'Inconnu'. Les autres informations (date, gravite, meteo) restent exploitables.\n\n"
"### 5. Enrichissement\n"
"- `tranche_horaire` : regroupe l'heure en 4 categories (Matin/Apres-midi/Soir/Nuit).\n"
"- `gravite_max` : gravite la plus severe parmi tous les usagers d'un accident.\n\n"
"### 6. Choix du modele en etoile (Star Schema)\n"
"Trois modeles etaient envisageables :\n"
"- **Table plate** : tout dans une seule table, doublons massifs, inexploitable\n"
"- **Modele en flocon (Snowflake)** : plus normalise mais complexe, justifie pour de tres grands datasets\n"
"- **Modele en etoile (Star Schema)** : choix retenu\n\n"
"Le modele en etoile est adapte car un accident implique plusieurs vehicules et plusieurs usagers. "
"Il est performant pour les analyses BI, correspond a la suggestion du TP ('fact table + dimensions'), "
"et reste simple a maintenir. La cle de jointure `Num_Acc` relie toutes les tables."
))

nb.cells = cells

with open("accidents_routiers_2024.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("[OK] notebook cree : accidents_routiers_2024.ipynb")
