import pandas as pd
import numpy as np

caract    = pd.read_csv("data/caract-2024.csv",    sep=";", encoding="latin1", low_memory=False)
lieux     = pd.read_csv("data/lieux-2024.csv",     sep=";", encoding="latin1", low_memory=False)
usagers   = pd.read_csv("data/usagers-2024.csv",   sep=";", encoding="latin1", low_memory=False)
vehicules = pd.read_csv("data/vehicules-2024.csv",  sep=";", encoding="latin1", low_memory=False)

print("Lignes avant nettoyage:")
print(f"  caract    : {len(caract)}")
print(f"  lieux     : {len(lieux)}")
print(f"  usagers   : {len(usagers)}")
print(f"  vehicules : {len(vehicules)}")

#1. supprimer les colonnes trop vides pour être utiles
lieux     = lieux.drop(columns=["lartpc", "v2"])
vehicules = vehicules.drop(columns=["occutc"])
print("\n[OK] colonnes vides supprimées : lartpc, v2, occutc")

#2. supprimer les doublons
lieux = lieux.drop_duplicates()
print(f"[OK] doublons supprimés dans lieux")

#3. convertir les coordonnées GPS (virgule -> point)
caract["lat"]  = pd.to_numeric(caract["lat"].str.replace(",", "."),  errors="coerce")
caract["long"] = pd.to_numeric(caract["long"].str.replace(",", "."), errors="coerce")
print("[OK] coordonnées GPS converties en float")

#4. séparer métropole et DOM-TOM (pas des erreurs, juste un scope différent)
dom_tom = caract[(caract["lat"] < 41) | (caract["lat"] > 52)]
caract_metro = caract[(caract["lat"] >= 41) & (caract["lat"] <= 52)].copy()
print(f"[OK] {len(dom_tom)} lignes DOM-TOM mises de côté (scope : France métropolitaine)")
print(f"     {len(caract_metro)} accidents en métropole conservés")

#5. corriger les valeurs négatives codées (-1 = non renseigné)
#   dans ce dataset, -1 signifie "non renseigné", on les remplace par NaN
cols_code_negatif = {
    "usagers":  ["sexe", "place", "trajet", "secu1", "secu2", "secu3", "locp", "etatp"],
    "caract":   ["col"],
}
for col in cols_code_negatif["usagers"]:
    usagers[col] = usagers[col].replace(-1, np.nan)

caract_metro["col"] = caract_metro["col"].replace(-1, np.nan)
print("[OK] valeurs -1 remplacées par NaN (non renseigné)")

#6. imputer les valeurs manquantes restantes
caract_metro["adr"] = caract_metro["adr"].fillna("Inconnu")
lieux["voie"]       = lieux["voie"].fillna("Inconnu")
print("[OK] valeurs manquantes imputées : adr et voie -> 'Inconnu'")

#7. construire une colonne date propre
caract_metro["date"] = pd.to_datetime(
    caract_metro[["an", "mois", "jour"]].rename(columns={"an": "year", "mois": "month", "jour": "day"}),
    errors="coerce"
)
print("[OK] colonne date créée")

#8. enrichissement : catégorie horaire (matin / apres-midi / soir / nuit)
caract_metro["heure"] = caract_metro["hrmn"].str[:2].astype(float, errors="ignore")

def categorie_horaire(h):
    if pd.isna(h):   return "Inconnu"
    if 6  <= h < 12: return "Matin"
    if 12 <= h < 18: return "Après-midi"
    if 18 <= h < 22: return "Soir"
    return "Nuit"

caract_metro["tranche_horaire"] = caract_metro["heure"].apply(categorie_horaire)
print("[OK] colonne tranche_horaire créée")

#9. enrichissement : gravité max par accident
gravite_max = usagers.groupby("Num_Acc")["grav"].max().reset_index()
gravite_max.columns = ["Num_Acc", "gravite_max"]
caract_metro = caract_metro.merge(gravite_max, on="Num_Acc", how="left")
print("[OK] colonne gravite_max ajoutée (gravité la plus sévère par accident)")

print("\nLignes après nettoyage (scope métropole):")
print(f"  caract_metro : {len(caract_metro)}")
print(f"  lieux        : {len(lieux)}")
print(f"  usagers      : {len(usagers)}")
print(f"  vehicules    : {len(vehicules)}")

#sauvegarde de la couche Silver
caract_metro.to_csv("data/silver_caract.csv",    index=False)
lieux.to_csv(        "data/silver_lieux.csv",     index=False)
usagers.to_csv(      "data/silver_usagers.csv",   index=False)
vehicules.to_csv(    "data/silver_vehicules.csv", index=False)
print("\n[OK] fichiers Silver sauvegardés dans data/")
