import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
"# TP Data Integration & Applications — ST2DLDI\n"
"**Dataset:** Road traffic injury accidents — France 2024 (data.gouv.fr)  \n"
"**Architecture:** Medallion (Bronze → Silver → Gold)  \n"
"**Data Quality Summary dashboard (Streamlit):** "
"https://accidents-routiers-2024-hasbwsxbbqcebewpwlwl9n.streamlit.app/"
))

cells.append(nbf.v4.new_markdown_cell("## Part 1 — Data Profiling & Data Quality"))

cells.append(nbf.v4.new_markdown_cell("### Data loading (Bronze layer)"))

cells.append(nbf.v4.new_code_cell(
"import pandas as pd\n"
"import numpy as np\n"
"\n"
"characteristics = pd.read_csv('data/caract-2024.csv',    sep=';', encoding='latin1', low_memory=False)\n"
"locations       = pd.read_csv('data/lieux-2024.csv',     sep=';', encoding='latin1', low_memory=False)\n"
"users           = pd.read_csv('data/usagers-2024.csv',   sep=';', encoding='latin1', low_memory=False)\n"
"vehicles        = pd.read_csv('data/vehicules-2024.csv', sep=';', encoding='latin1', low_memory=False)\n"
"\n"
"tables = {\n"
"    'characteristics': characteristics,\n"
"    'locations':       locations,\n"
"    'users':           users,\n"
"    'vehicles':        vehicles,\n"
"}\n"
"\n"
"for name, df in tables.items():\n"
"    print(f'  {name:<20} {len(df):>7} rows  {df.shape[1]} columns')"
))

cells.append(nbf.v4.new_markdown_cell("### Quick data exploration"))

cells.append(nbf.v4.new_code_cell(
"#first rows of each table\n"
"characteristics.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"locations.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"users.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"vehicles.head(3)"
))

cells.append(nbf.v4.new_code_cell(
"#descriptive statistics\n"
"characteristics.describe()"
))

cells.append(nbf.v4.new_code_cell(
"users.describe()"
))

cells.append(nbf.v4.new_markdown_cell("### A. Table structure"))

cells.append(nbf.v4.new_code_cell(
"for name, df in tables.items():\n"
"    print(f'--- {name.upper()} ---')\n"
"    for col, dtype in df.dtypes.items():\n"
"        print(f'  {col:<30} {str(dtype)}')\n"
"    print()"
))

cells.append(nbf.v4.new_markdown_cell("### A. Primary keys"))

cells.append(nbf.v4.new_code_cell(
"#candidate primary key per table\n"
"key_candidates = {\n"
"    'characteristics': 'Num_Acc',\n"
"    'locations':       'Num_Acc',\n"
"    'vehicles':        'id_vehicule',\n"
"    'users':           'id_usager',\n"
"}\n"
"for name, key in key_candidates.items():\n"
"    df = tables[name]\n"
"    is_unique = df[key].is_unique\n"
"    print(f'{name:<20} key={key:<12} rows={len(df):>7} distinct={df[key].nunique():>7} unique={is_unique}')\n"
"\n"
"dup_locations = locations['Num_Acc'].value_counts()\n"
"multi_location_accidents = (dup_locations > 1).sum()\n"
"print(f'\\nAccidents with more than one row in locations: {multi_location_accidents}')"
))

cells.append(nbf.v4.new_markdown_cell(
"`characteristics.Num_Acc`, `vehicles.id_vehicule` and `users.id_usager` are each a clean "
"single-column primary key (one row per accident / vehicle / user, matching the source "
"documentation). `locations.Num_Acc` is **not** unique: 15,645 accidents have more than one "
"row in `locations` (e.g. one row per named road meeting at a complex intersection). This "
"means `locations` has no natural single-column primary key at the raw (Bronze) grain, and a "
"naive join from `fact_accidents` to a location dimension on `Num_Acc` would fan out rows for "
"those accidents. This is addressed in the Gold layer (Part 2B) by keeping only the first "
"location row per accident when building `dim_location`."
))

cells.append(nbf.v4.new_markdown_cell(
"### A. Semantic meaning of columns\n\n"
"**Source:** \"Description des bases de donnees annuelles des accidents corporels de la circulation "
"routiere - Annees de 2005 a 2024\" (ONISR, data.gouv.fr, resource id 8ef4c2a3-91a0-4d98-ae3a-989bde87b62a). "
"The codes below are verified against this document (pages 4-13, full field list). "
"Non-exhaustive list: a few key columns per table to demonstrate understanding of the schema.\n\n"
"**Characteristics table** (1 row = 1 accident)\n\n"
"| Column | Meaning |\n"
"|---|---|\n"
"| Num_Acc | Unique accident identifier |\n"
"| lum | Lighting conditions (1=daylight, 2=dusk/dawn, 3=night without public lighting, ...) |\n"
"| atm | Weather conditions (1=normal, 2=rain, 3=snow, ...) |\n"
"| col | Collision type (1=head-on, 2=rear-end, 3=side, ...) |\n\n"
"**Locations table** (road characteristics)\n\n"
"| Column | Meaning |\n"
"|---|---|\n"
"| catr | Road category (1=motorway, 2=national road, 3=departmental road, ...) |\n"
"| surf | Road surface condition (1=normal, 2=wet, 3=puddles, ...) |\n"
"| vma | Maximum authorized speed |\n\n"
"**Users table** (1 row = 1 person involved)\n\n"
"| Column | Meaning |\n"
"|---|---|\n"
"| catu | User category (1=driver, 2=passenger, 3=pedestrian) |\n"
"| grav | Injury severity (1=uninjured, 2=killed, 3=hospitalized injury, 4=slight injury) |\n"
"| secu1 | Safety equipment (1=seatbelt, 2=helmet, 3=child restraint, ...) |\n\n"
"**Vehicles table** (1 row = 1 vehicle involved)\n\n"
"| Column | Meaning |\n"
"|---|---|\n"
"| catv | Vehicle category (1=bicycle, 2=moped, 7=car, ...) |\n"
"| choc | Initial impact point (1=front, 2=front right, 3=front left, ...) |\n"
"| motor | Engine type (1=fossil fuel, 2=hybrid, 3=electric, ...) |"
))

cells.append(nbf.v4.new_markdown_cell("### B. Missing values"))

cells.append(nbf.v4.new_code_cell(
"for name, df in tables.items():\n"
"    print(f'--- {name.upper()} ---')\n"
"    missing = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)\n"
"    missing = missing[missing > 0]\n"
"    if missing.empty:\n"
"        print('  no missing values')\n"
"    else:\n"
"        for col, pct in missing.items():\n"
"            flag = ' CRITICAL' if pct > 20 else ''\n"
"            print(f'  {col:<30} {pct:.1f}%{flag}')\n"
"    print()"
))

cells.append(nbf.v4.new_markdown_cell("### C. Consistency and validity"))

cells.append(nbf.v4.new_code_cell(
"#split Metropole / DOM-TOM by department code\n"
"#(a latitude threshold is unreliable: Saint-Pierre-et-Miquelon, dep 975, has a latitude\n"
"# within the mainland range 41-52, and southern Corsica, dep 2B, can fall below 41)\n"
"DOMTOM_DEP = {'971', '972', '973', '974', '975', '976', '977', '978', '986', '987', '988'}\n"
"outside_mainland = characteristics['dep'].astype(str).isin(DOMTOM_DEP).sum()\n"
"print(f'Coordinates outside mainland France (DOM-TOM): {outside_mainland}')\n"
"\n"
"#negative (placeholder) values\n"
"for col in ['grav', 'sexe', 'place']:\n"
"    neg = (users[col] < 0).sum()\n"
"    if neg > 0:\n"
"        print(f'users.{col}: {neg} negative values (-1 = not specified)')\n"
"\n"
"#ages (derived from an_nais). Reference year is read from the data itself\n"
"#(not hardcoded) so this check still works if the dataset is swapped for another year.\n"
"reference_year = int(characteristics['an'].mode()[0])\n"
"age = reference_year - users['an_nais']\n"
"negative_ages = (age < 0).sum()\n"
"outlier_ages = (age > 110).sum()\n"
"print(f'Negative ages: {negative_ages}')\n"
"print(f'Ages > 110 years (outliers): {outlier_ages}')\n"
"\n"
"#duplicates\n"
"print()\n"
"for name, df in tables.items():\n"
"    dup = df.duplicated().sum()\n"
"    print(f'  {name:<20} {dup} duplicate(s)')\n"
"\n"
"#swapped lat/long values: for each department, a genuine accident location should sit\n"
"#close to the department's median position. If swapping lat and long would place a row\n"
"#much closer to its own department's median, that row's coordinates are almost certainly\n"
"#swapped. This is data-driven (no hardcoded real-world coordinates), so it generalizes\n"
"#to any year of this dataset.\n"
"coords = characteristics.dropna(subset=['lat', 'long']).copy()\n"
"coords['lat_num']  = pd.to_numeric(coords['lat'].astype(str).str.replace(',', '.'),  errors='coerce')\n"
"coords['long_num'] = pd.to_numeric(coords['long'].astype(str).str.replace(',', '.'), errors='coerce')\n"
"coords = coords.dropna(subset=['lat_num', 'long_num'])\n"
"dept_median = coords.groupby('dep')[['lat_num', 'long_num']].transform('median')\n"
"dist_normal  = np.sqrt((coords['lat_num']  - dept_median['lat_num'])**2 + (coords['long_num'] - dept_median['long_num'])**2)\n"
"dist_swapped = np.sqrt((coords['long_num'] - dept_median['lat_num'])**2 + (coords['lat_num']  - dept_median['long_num'])**2)\n"
"swapped_coords = ((dist_swapped < dist_normal) & (dist_normal > 1.0)).sum()\n"
"print(f'Likely swapped lat/long values: {swapped_coords}')"
))

cells.append(nbf.v4.new_markdown_cell("### C. Categorical anomalies"))

cells.append(nbf.v4.new_markdown_cell(
"Every enumerated column across the 4 tables is checked against the official ONISR codebook "
"(same source as Part A), not just a hand-picked subset. `-1` is accepted everywhere as the "
"dataset-wide 'not specified' placeholder, even on columns where the PDF doesn't spell it out "
"explicitly, since it is used consistently across the file."
))

cells.append(nbf.v4.new_code_cell(
"#expected values per categorical column, one dict per table, built from the official codebook\n"
"expected_characteristics = {\n"
"    'lum': [1,2,3,4,5], 'agg': [1,2], 'int': [1,2,3,4,5,6,7,8,9],\n"
"    'atm': [-1,1,2,3,4,5,6,7,8,9], 'col': [-1,1,2,3,4,5,6,7],\n"
"}\n"
"expected_locations = {\n"
"    'catr': [1,2,3,4,5,6,7,9], 'circ': [-1,1,2,3,4], 'vosp': [-1,0,1,2,3],\n"
"    'prof': [-1,1,2,3,4], 'plan': [-1,1,2,3,4], 'surf': [-1,1,2,3,4,5,6,7,8,9],\n"
"    'infra': [-1,0,1,2,3,4,5,6,7,8,9], 'situ': [-1,0,1,2,3,4,5,6,8],\n"
"}\n"
"expected_vehicles = {\n"
"    'catv': [-1,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,\n"
"             30,31,32,33,34,35,36,37,38,39,40,41,42,43,50,60,80,99],\n"
"    'obs': list(range(-1,18)), 'obsm': [-1,0,1,2,4,5,6,9],\n"
"    'choc': list(range(-1,10)), 'manv': list(range(-1,27)), 'motor': [-1,0,1,2,3,4,5,6],\n"
"}\n"
"expected_users = {\n"
"    'catu': [1,2,3], 'grav': [1,2,3,4], 'sexe': [1,2], 'trajet': [-1,0,1,2,3,4,5,9],\n"
"    'secu1': list(range(-1,10)), 'secu2': list(range(-1,10)), 'secu3': list(range(-1,10)),\n"
"    'locp': list(range(-1,10)), 'etatp': [-1,1,2,3],\n"
"}\n"
"\n"
"expected_by_table = {\n"
"    'characteristics': (characteristics, expected_characteristics),\n"
"    'locations':       (locations, expected_locations),\n"
"    'vehicles':        (vehicles, expected_vehicles),\n"
"    'users':           (users, expected_users),\n"
"}\n"
"\n"
"checked, flagged = 0, 0\n"
"for table_name, (df, expected) in expected_by_table.items():\n"
"    for col, valid in expected.items():\n"
"        checked += 1\n"
"        unique_values = df[col].dropna().unique()\n"
"        unexpected = [v for v in unique_values if v not in valid]\n"
"        if unexpected:\n"
"            flagged += 1\n"
"            print(f'{table_name}.{col}: unexpected values -> {unexpected}')\n"
"print(f'\\n{checked} categorical columns checked across 4 tables, {flagged} with anomalies')"
))

cells.append(nbf.v4.new_markdown_cell(
"### D. Quality summary\n\n"
"An interactive version of this Data Quality Summary (live KPIs, quality report, categorical "
"anomaly checks, primary keys, and a map of geographic outliers) is deployed as a Streamlit "
"app: https://accidents-routiers-2024-hasbwsxbbqcebewpwlwl9n.streamlit.app/\n\n"
"| Issue | Column | Action |\n"
"|---|---|---|\n"
"| 100% empty | locations.lartpc | Drop |\n"
"| 99% empty | vehicles.occutc | Drop |\n"
"| 91.6% empty | locations.v2 | Drop |\n"
"| 19% empty | locations.voie | Impute 'Unknown' |\n"
"| 4.2% empty | characteristics.adr | Impute 'Unknown' |\n"
"| Outside mainland France | dep | Split off DOM-TOM (by department code) |\n"
"| Placeholder -1 values | sexe, place, col | Replace with NaN |\n"
"| Duplicates | locations | Drop (2 rows) |\n"
"| Swapped lat/long values | lat, long | Swap back (detected vs department median) |\n\n"
"### D. Impact analysis\n\n"
"- Empty columns: unusable, must be excluded before any processing\n"
"- Placeholder -1 values in `grav` and `sexe`: bias averages and distributions\n"
"- Coordinates outside mainland France: would bias any geographic or map-based analysis\n"
"- Duplicates in `locations`: would inflate counts on certain roads\n"
"- Swapped lat/long values: place accidents in the middle of the ocean, nowhere near "
"their real department; would break any map or distance-based analysis"
))

cells.append(nbf.v4.new_markdown_cell("## Part 2A — Transformations (Silver layer)"))

cells.append(nbf.v4.new_code_cell(
"#1. drop columns that are almost entirely empty\n"
"locations = locations.drop(columns=['lartpc', 'v2'])\n"
"vehicles  = vehicles.drop(columns=['occutc'])\n"
"\n"
"#2. duplicates\n"
"locations = locations.drop_duplicates()\n"
"\n"
"#3. convert GPS coordinates\n"
"characteristics['lat']  = pd.to_numeric(characteristics['lat'].str.replace(',', '.'),  errors='coerce')\n"
"characteristics['long'] = pd.to_numeric(characteristics['long'].str.replace(',', '.'), errors='coerce')\n"
"\n"
"#3b. fix swapped lat/long values (detected in profiling: a row is swapped if flipping\n"
"#    lat and long puts it much closer to its own department's median position)\n"
"has_coords = characteristics['lat'].notna() & characteristics['long'].notna()\n"
"dept_median = characteristics.loc[has_coords].groupby('dep')[['lat', 'long']].transform('median')\n"
"dist_normal  = np.sqrt((characteristics.loc[has_coords, 'lat']  - dept_median['lat'])**2\n"
"                       + (characteristics.loc[has_coords, 'long'] - dept_median['long'])**2)\n"
"dist_swapped = np.sqrt((characteristics.loc[has_coords, 'long'] - dept_median['lat'])**2\n"
"                       + (characteristics.loc[has_coords, 'lat']  - dept_median['long'])**2)\n"
"is_swapped = (dist_swapped < dist_normal) & (dist_normal > 1.0)\n"
"swap_idx = characteristics.loc[has_coords].index[is_swapped]\n"
"characteristics.loc[swap_idx, ['lat', 'long']] = characteristics.loc[swap_idx, ['long', 'lat']].values\n"
"print(f'Swapped lat/long values fixed: {len(swap_idx)}')\n"
"\n"
"#4. split mainland France / DOM-TOM (by department code, more reliable than a latitude threshold)\n"
"DOMTOM_DEP = {'971', '972', '973', '974', '975', '976', '977', '978', '986', '987', '988'}\n"
"is_domtom             = characteristics['dep'].astype(str).isin(DOMTOM_DEP)\n"
"domtom                = characteristics[is_domtom]\n"
"characteristics_metro = characteristics[~is_domtom].copy()\n"
"print(f'DOM-TOM set aside: {len(domtom)} rows')\n"
"print(f'Mainland France kept: {len(characteristics_metro)} rows')\n"
"\n"
"#5. replace -1 placeholders with NaN\n"
"for col in ['sexe', 'place', 'trajet', 'secu1', 'secu2', 'secu3', 'locp', 'etatp']:\n"
"    users[col] = users[col].replace(-1, np.nan)\n"
"characteristics_metro['col'] = characteristics_metro['col'].replace(-1, np.nan)\n"
"\n"
"#6. impute missing text values\n"
"characteristics_metro['adr'] = characteristics_metro['adr'].fillna('Unknown')\n"
"locations['voie']            = locations['voie'].fillna('Unknown')\n"
"\n"
"#7. date column\n"
"characteristics_metro['date'] = pd.to_datetime(\n"
"    characteristics_metro[['an', 'mois', 'jour']].rename(columns={'an': 'year', 'mois': 'month', 'jour': 'day'}),\n"
"    errors='coerce'\n"
")\n"
"\n"
"#8. time-of-day enrichment\n"
"characteristics_metro['hour'] = characteristics_metro['hrmn'].str[:2].astype(float, errors='ignore')\n"
"\n"
"def time_of_day_category(h):\n"
"    if pd.isna(h):   return 'Unknown'\n"
"    if 6  <= h < 12: return 'Morning'\n"
"    if 12 <= h < 18: return 'Afternoon'\n"
"    if 18 <= h < 22: return 'Evening'\n"
"    return 'Night'\n"
"\n"
"characteristics_metro['time_of_day'] = characteristics_metro['hour'].apply(time_of_day_category)\n"
"\n"
"#9. max severity enrichment per accident\n"
"max_severity = users.groupby('Num_Acc')['grav'].max().reset_index()\n"
"max_severity.columns = ['Num_Acc', 'max_severity']\n"
"characteristics_metro = characteristics_metro.merge(max_severity, on='Num_Acc', how='left')\n"
"\n"
"#save Silver files\n"
"characteristics_metro.to_csv('data/silver_caract.csv',    index=False)\n"
"locations.to_csv(             'data/silver_lieux.csv',     index=False)\n"
"users.to_csv(                 'data/silver_usagers.csv',   index=False)\n"
"vehicles.to_csv(               'data/silver_vehicules.csv', index=False)\n"
"print('[OK] Silver files saved')"
))

cells.append(nbf.v4.new_markdown_cell("## Part 2B — Modeling (Gold layer)"))

cells.append(nbf.v4.new_code_cell(
"characteristics_s = pd.read_csv('data/silver_caract.csv',    low_memory=False)\n"
"locations_s       = pd.read_csv('data/silver_lieux.csv',     low_memory=False)\n"
"users_s           = pd.read_csv('data/silver_usagers.csv',   low_memory=False)\n"
"vehicles_s        = pd.read_csv('data/silver_vehicules.csv', low_memory=False)\n"
"\n"
"#fact table\n"
"fact_accidents = characteristics_s[[\n"
"    'Num_Acc', 'date', 'time_of_day', 'max_severity',\n"
"    'atm', 'col', 'lum', 'agg', 'dep'\n"
"]].rename(columns={\n"
"    'atm': 'weather', 'col': 'collision_type',\n"
"    'lum': 'lighting', 'agg': 'urban_area', 'dep': 'department'\n"
"})\n"
"\n"
"#location dimension\n"
"#Num_Acc is not a unique key in locations_s (some accidents have several rows, e.g. one per\n"
"#named road at a complex intersection - see Part A, Primary keys). Keeping only the first\n"
"#row per accident enforces a clean one-row-per-accident grain for the dimension and avoids\n"
"#fan-out when joined to fact_accidents.\n"
"locations_s = locations_s.drop_duplicates(subset='Num_Acc', keep='first')\n"
"dim_location = locations_s[[\n"
"    'Num_Acc', 'catr', 'surf', 'infra', 'situ', 'vma', 'prof', 'plan'\n"
"]].rename(columns={\n"
"    'catr': 'road_type', 'surf': 'road_surface', 'infra': 'infrastructure',\n"
"    'situ': 'situation', 'vma': 'speed_limit', 'prof': 'road_profile', 'plan': 'road_layout'\n"
"})\n"
"\n"
"#vehicle dimension\n"
"dim_vehicle = vehicles_s[[\n"
"    'Num_Acc', 'id_vehicule', 'catv', 'manv', 'obs', 'obsm', 'choc', 'motor'\n"
"]].rename(columns={\n"
"    'catv': 'vehicle_type', 'manv': 'maneuver', 'obs': 'fixed_obstacle',\n"
"    'obsm': 'moving_obstacle', 'choc': 'impact_point', 'motor': 'engine_type'\n"
"})\n"
"\n"
"#user dimension\n"
"dim_user = users_s[[\n"
"    'Num_Acc', 'id_usager', 'catu', 'grav', 'sexe', 'an_nais', 'trajet', 'secu1'\n"
"]].rename(columns={\n"
"    'catu': 'user_category', 'grav': 'severity', 'sexe': 'sex', 'an_nais': 'birth_year',\n"
"    'trajet': 'trip_purpose', 'secu1': 'safety_equipment'\n"
"})\n"
"\n"
"#save Gold files\n"
"fact_accidents.to_csv('data/gold_fait_accidents.csv', index=False)\n"
"dim_location.to_csv(  'data/gold_dim_lieu.csv',       index=False)\n"
"dim_vehicle.to_csv(   'data/gold_dim_vehicule.csv',   index=False)\n"
"dim_user.to_csv(      'data/gold_dim_usager.csv',     index=False)\n"
"\n"
"print(f'fact_accidents : {len(fact_accidents)} rows')\n"
"print(f'dim_location   : {len(dim_location)} rows')\n"
"print(f'dim_vehicle    : {len(dim_vehicle)} rows')\n"
"print(f'dim_user       : {len(dim_user)} rows')\n"
"print('[OK] Gold files saved')"
))

cells.append(nbf.v4.new_markdown_cell(
"## Part 2C — Medallion Architecture Diagram\n\n"
"![Medallion Architecture](medallion_drawio.png)"
))

cells.append(nbf.v4.new_markdown_cell(
"## Justification of design choices\n\n"
"### 1. Dropping near-empty columns\n"
"Columns `lartpc` (100% empty), `v2` (91.6% empty) and `occutc` (99% empty) were dropped. "
"A column with almost no data carries no usable information.\n\n"
"### 2. Handling DOM-TOM\n"
"The 3,344 accidents whose department code is 971-978 or 986-988 correspond to overseas "
"territories. These are not errors. The split is done on the department code rather than a "
"latitude threshold (less reliable: Saint-Pierre-et-Miquelon, dep 975, has a latitude within "
"the mainland range, and southern Corsica can fall below 41 degrees). These rows were set "
"aside to scope the analysis to mainland France, while keeping them available for a future "
"study.\n\n"
"### 3. Replacing -1 with NaN\n"
"In this dataset, -1 means 'not specified'. Leaving it as-is would bias statistical "
"computations. NaN is the standard pandas convention for an unknown value.\n\n"
"### 4. Imputing 'Unknown' on missing text fields\n"
"Rather than dropping an entire row because of a missing address, we keep the accident and "
"impute 'Unknown'. The other fields (date, severity, weather) remain usable.\n\n"
"### 5. Enrichment\n"
"- `time_of_day`: buckets the accident hour into 4 categories (Morning/Afternoon/Evening/Night).\n"
"- `max_severity`: the most severe outcome among all users involved in an accident.\n\n"
"### 6. Choice of a star schema (Gold layer)\n"
"Three models were considered:\n"
"- **Flat table**: everything in a single table, massive duplication, unusable\n"
"- **Snowflake schema**: more normalized but more complex, justified only for very large datasets\n"
"- **Star schema**: the option chosen\n\n"
"A star schema fits because an accident involves multiple vehicles and multiple users. "
"It performs well for BI analysis, matches what the assignment suggests ('fact table + "
"dimensions'), and stays simple to maintain. The `Num_Acc` join key links every table."
))

nb.cells = cells

with open("accidents_routiers_2024.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("[OK] notebook created: accidents_routiers_2024.ipynb")
