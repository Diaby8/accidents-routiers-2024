import pandas as pd
import numpy as np

#chargement des 4 fichiers
caract    = pd.read_csv("data/caract-2024.csv",    sep=";", encoding="latin1", low_memory=False)
lieux     = pd.read_csv("data/lieux-2024.csv",     sep=";", encoding="latin1", low_memory=False)
usagers   = pd.read_csv("data/usagers-2024.csv",   sep=";", encoding="latin1", low_memory=False)
vehicules = pd.read_csv("data/vehicules-2024.csv",  sep=";", encoding="latin1", low_memory=False)

tables = {
    "caracteristiques": caract,
    "lieux":            lieux,
    "usagers":          usagers,
    "vehicules":        vehicules,
}

#A. structure
print("=" * 60)
print("A. STRUCTURE DES TABLES")
print("=" * 60)

for name, df in tables.items():
    print(f"\n--- {name.upper()} ---")
    print(f"  Lignes : {df.shape[0]:,}   Colonnes : {df.shape[1]}")
    for col, dtype in df.dtypes.items():
        print(f"    {col:<30} {str(dtype)}")

#B. valeurs manquantes
print("\n" + "=" * 60)
print("B. VALEURS MANQUANTES (%)")
print("=" * 60)

for name, df in tables.items():
    print(f"\n--- {name.upper()} ---")
    missing = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
    missing = missing[missing > 0]
    if missing.empty:
        print("  aucune valeur manquante")
    else:
        for col, pct in missing.items():
            flag = " <<<" if pct > 20 else ""
            print(f"  {col:<30} {pct:.1f}%{flag}")

#C. cohérence et validité
print("\n" + "=" * 60)
print("C. COHERENCE ET VALIDITE")
print("=" * 60)

#coordonnées GPS (lat/long doivent être numériques et dans les bornes France métro)
print("\n-- Coordonnées GPS --")
caract["lat_f"]  = pd.to_numeric(caract["lat"].str.replace(",", "."), errors="coerce")
caract["long_f"] = pd.to_numeric(caract["long"].str.replace(",", "."), errors="coerce")

lat_invalid  = caract[(caract["lat_f"]  < 41) | (caract["lat_f"]  > 52)].shape[0]
long_invalid = caract[(caract["long_f"] < -6) | (caract["long_f"] > 10)].shape[0]
lat_null     = caract["lat_f"].isnull().sum()
print(f"  lat hors France métro : {lat_invalid}")
print(f"  long hors France métro : {long_invalid}")
print(f"  lat non parseable     : {lat_null}")

#année de naissance aberrante (avant 1900 ou dans le futur)
print("\n-- Année de naissance (usagers) --")
an_invalid = usagers[(usagers["an_nais"] < 1900) | (usagers["an_nais"] > 2024)].shape[0]
print(f"  valeurs aberrantes : {an_invalid}")

#valeurs négatives là où ça n'a pas de sens
print("\n-- Valeurs négatives --")
for col in ["lum", "agg", "int", "atm", "col"]:
    neg = (caract[col] < 0).sum()
    if neg > 0:
        print(f"  caract.{col} : {neg} négatifs")

for col in ["grav", "sexe", "catu", "place"]:
    neg = (usagers[col] < 0).sum()
    if neg > 0:
        print(f"  usagers.{col} : {neg} négatifs")

#doublons
print("\n-- Doublons --")
for name, df in tables.items():
    dup = df.duplicated().sum()
    print(f"  {name:<20} {dup} doublon(s)")

#D. résumé qualité
print("\n" + "=" * 60)
print("D. RESUME QUALITE")
print("=" * 60)
print("""
  Problèmes identifiés :
  - lieux.lartpc     : 100% vide -> à supprimer
  - vehicules.occutc : 99% vide  -> à supprimer
  - lieux.v2         : 91.6% vide -> à supprimer ou ignorer
  - lieux.voie       : 19% vide  -> imputation ou suppression de ligne
  - caract.adr       : 4.2% vide -> imputation "Inconnu"
  - coordonnées GPS  : voir résultats ci-dessus
  - doublons         : voir résultats ci-dessus

  Impact analytique :
  - les colonnes à 99-100% vides ne peuvent pas être utilisées
  - les coordonnées invalides bloquent toute carte ou analyse géo
  - les doublons fausseraient les comptages d'accidents
""")
