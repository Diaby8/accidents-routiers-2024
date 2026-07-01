import pandas as pd

#chargement des fichiers Silver (déjà nettoyés)
caract    = pd.read_csv("data/silver_caract.csv",    low_memory=False)
lieux     = pd.read_csv("data/silver_lieux.csv",     low_memory=False)
usagers   = pd.read_csv("data/silver_usagers.csv",   low_memory=False)
vehicules = pd.read_csv("data/silver_vehicules.csv", low_memory=False)

#────────────────────────────────────────────
#TABLE DE FAITS : un accident = une ligne
#on garde les infos globales de l'accident
#────────────────────────────────────────────
fait_accidents = caract[[
    "Num_Acc",
    "date",
    "tranche_horaire",
    "gravite_max",
    "atm",       #conditions météo
    "col",       #type de collision
    "lum",       #conditions d'éclairage
    "agg",       #en agglomération ou non
    "dep",       #département
]].copy()

#renommer pour que ce soit lisible
fait_accidents = fait_accidents.rename(columns={
    "atm": "meteo",
    "col": "type_collision",
    "lum": "eclairage",
    "agg": "en_agglomeration",
    "dep": "departement",
})

print("FAIT_ACCIDENTS")
print(f"  {len(fait_accidents)} lignes, {len(fait_accidents.columns)} colonnes")
print(f"  colonnes : {list(fait_accidents.columns)}\n")

#────────────────────────────────────────────
#DIM_LIEU : infos sur la route et le lieu
#────────────────────────────────────────────
dim_lieu = lieux[[
    "Num_Acc",
    "catr",      #catégorie de route (autoroute, nationale, etc.)
    "surf",      #état de la surface (sèche, mouillée, etc.)
    "infra",     #infrastructure (tunnel, pont, etc.)
    "situ",      #situation (sur chaussée, trottoir, etc.)
    "vma",       #vitesse max autorisée
    "prof",      #profil de la route (plat, pente, etc.)
    "plan",      #tracé en plan (rectiligne, courbe, etc.)
]].copy()

dim_lieu = dim_lieu.rename(columns={
    "catr": "type_route",
    "surf": "etat_surface",
    "infra": "infrastructure",
    "situ": "situation",
    "vma":  "vitesse_max",
    "prof": "profil_route",
    "plan": "trace_plan",
})

print("DIM_LIEU")
print(f"  {len(dim_lieu)} lignes, {len(dim_lieu.columns)} colonnes")
print(f"  colonnes : {list(dim_lieu.columns)}\n")

#────────────────────────────────────────────
#DIM_VEHICULE : infos sur les véhicules impliqués
#────────────────────────────────────────────
dim_vehicule = vehicules[[
    "Num_Acc",
    "id_vehicule",
    "catv",      #catégorie de véhicule (voiture, moto, camion, etc.)
    "manv",      #manœuvre avant l'accident
    "obs",       #obstacle fixe heurté
    "obsm",      #obstacle mobile heurté
    "choc",      #point de choc initial
    "motor",     #type de motorisation
]].copy()

dim_vehicule = dim_vehicule.rename(columns={
    "catv":  "type_vehicule",
    "manv":  "manoeuvre",
    "obs":   "obstacle_fixe",
    "obsm":  "obstacle_mobile",
    "choc":  "point_choc",
    "motor": "motorisation",
})

print("DIM_VEHICULE")
print(f"  {len(dim_vehicule)} lignes, {len(dim_vehicule.columns)} colonnes")
print(f"  colonnes : {list(dim_vehicule.columns)}\n")

#────────────────────────────────────────────
#DIM_USAGER : infos sur les personnes impliquées
#────────────────────────────────────────────
dim_usager = usagers[[
    "Num_Acc",
    "id_usager",
    "catu",      #catégorie usager (conducteur, passager, piéton)
    "grav",      #gravité des blessures
    "sexe",
    "an_nais",   #année de naissance
    "trajet",    #motif du déplacement
    "secu1",     #équipement de sécurité (ceinture, casque, etc.)
]].copy()

dim_usager = dim_usager.rename(columns={
    "catu":   "categorie_usager",
    "grav":   "gravite",
    "an_nais":"annee_naissance",
    "trajet": "motif_trajet",
    "secu1":  "equipement_securite",
})

print("DIM_USAGER")
print(f"  {len(dim_usager)} lignes, {len(dim_usager.columns)} colonnes")
print(f"  colonnes : {list(dim_usager.columns)}\n")

#────────────────────────────────────────────
#SAUVEGARDE couche Gold
#────────────────────────────────────────────
fait_accidents.to_csv("data/gold_fait_accidents.csv", index=False)
dim_lieu.to_csv(      "data/gold_dim_lieu.csv",       index=False)
dim_vehicule.to_csv(  "data/gold_dim_vehicule.csv",   index=False)
dim_usager.to_csv(    "data/gold_dim_usager.csv",     index=False)

print("[OK] fichiers Gold sauvegardés dans data/")
