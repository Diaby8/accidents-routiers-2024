import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Data Quality Summary — Accidents Routiers 2024", layout="wide")


@st.cache_data
def load_data():
    caract = pd.read_csv("data/caract-2024.csv", sep=";", encoding="latin1", low_memory=False)
    lieux = pd.read_csv("data/lieux-2024.csv", sep=";", encoding="latin1", low_memory=False)
    usagers = pd.read_csv("data/usagers-2024.csv", sep=";", encoding="latin1", low_memory=False)
    vehicules = pd.read_csv("data/vehicules-2024.csv", sep=";", encoding="latin1", low_memory=False)
    return caract, lieux, usagers, vehicules


caract, lieux, usagers, vehicules = load_data()
tables = {"caracteristiques": caract, "lieux": lieux, "usagers": usagers, "vehicules": vehicules}

st.title("Data Quality Summary")
st.caption("TP Data Integration & Applications — ST2DLDI — Partie 1.D")

# --- métriques calculées en direct sur les données Bronze ---
DOMTOM_DEP = {"971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988"}
hors_metro = int(caract["dep"].astype(str).isin(DOMTOM_DEP).sum())

neg_sexe = int((usagers["sexe"] < 0).sum())
neg_place = int((usagers["place"] < 0).sum())

age = 2024 - usagers["an_nais"]
ages_negatifs = int((age < 0).sum())
ages_aberrants = int((age > 110).sum())

doublons = {name: int(df.duplicated().sum()) for name, df in tables.items()}

missing_pct = {}
for name, df in tables.items():
    pct = (df.isnull().sum() / len(df) * 100)
    missing_pct[name] = pct[pct > 0].sort_values(ascending=False)

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Lignes hors metropole (DOM-TOM)", f"{hors_metro:,}")
col2.metric("Doublons (lieux)", doublons["lieux"])
col3.metric("Valeurs -1 (sexe)", f"{neg_sexe:,}")
col4.metric("Ages negatifs / aberrants", ages_negatifs + ages_aberrants)

st.divider()

st.subheader("Quality report")
quality_report = pd.DataFrame([
    {"Probleme": "100% vide", "Colonne": "lieux.lartpc", "Action": "Supprimer"},
    {"Probleme": "99% vide", "Colonne": "vehicules.occutc", "Action": "Supprimer"},
    {"Probleme": "91.6% vide", "Colonne": "lieux.v2", "Action": "Supprimer"},
    {"Probleme": "19% vide", "Colonne": "lieux.voie", "Action": "Imputer 'Inconnu'"},
    {"Probleme": "4.2% vide", "Colonne": "caract.adr", "Action": "Imputer 'Inconnu'"},
    {"Probleme": "Hors metropole", "Colonne": "lat/long", "Action": "Separer DOM-TOM"},
    {"Probleme": "Valeurs -1", "Colonne": "sexe, place, col", "Action": "Remplacer par NaN"},
    {"Probleme": "Doublons", "Colonne": "lieux", "Action": "Supprimer (2 lignes)"},
])
st.dataframe(quality_report, use_container_width=True, hide_index=True)

with st.expander("Detail : % de valeurs manquantes par table"):
    for name, pct in missing_pct.items():
        st.write(f"**{name}**")
        if pct.empty:
            st.write("aucune valeur manquante")
        else:
            st.dataframe(pct.rename("% manquant").round(1), use_container_width=True)

st.subheader("Impact analysis")
st.markdown(
    "- **Colonnes vides** : inutilisables, a exclure avant tout traitement.\n"
    "- **Valeurs -1** dans `grav` et `sexe` : faussent les moyennes et distributions.\n"
    "- **Coordonnees hors metro** : biaiseraient toute analyse geographique ou cartographique.\n"
    "- **Doublons** dans `lieux` : gonfleraient les comptages sur certaines routes.\n"
    "- **Ages** : aucune anomalie detectee (0 age negatif, 0 age > 110 ans)."
)

st.divider()
st.subheader("Cartographie des accidents")


@st.cache_data
def build_map_data(caract, usagers):
    df = caract.copy()
    df["lat"] = pd.to_numeric(df["lat"].str.replace(",", "."), errors="coerce")
    df["long"] = pd.to_numeric(df["long"].str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["lat", "long"])
    df["zone"] = np.where(df["dep"].astype(str).isin(DOMTOM_DEP), "DOM-TOM", "Metropole")

    gravite_max = usagers.groupby("Num_Acc")["grav"].max().reset_index()
    gravite_max.columns = ["Num_Acc", "gravite_max"]
    df = df.merge(gravite_max, on="Num_Acc", how="left")

    grav_labels = {1: "Indemne", 2: "Blesse hospitalise", 3: "Blesse leger", 4: "Tue"}
    df["gravite_label"] = df["gravite_max"].map(grav_labels)

    meteo_labels = {
        1: "Normale", 2: "Pluie legere", 3: "Pluie forte", 4: "Neige/grele",
        5: "Brouillard/fumee", 6: "Vent fort/tempete", 7: "Temps eblouissant",
        8: "Temps couvert", 9: "Autre",
    }
    df["meteo_label"] = df["atm"].map(meteo_labels).fillna("Inconnu")
    return df


map_data = build_map_data(caract, usagers)

inclure_domtom = st.checkbox(
    f"Inclure les DOM-TOM ({(map_data['zone'] == 'DOM-TOM').sum():,} accidents)",
    value=True,
)
zones = ["Metropole", "DOM-TOM"] if inclure_domtom else ["Metropole"]

col_a, col_b = st.columns(2)
gravites = col_a.multiselect(
    "Gravite", options=sorted(map_data["gravite_label"].dropna().unique()),
    default=list(map_data["gravite_label"].dropna().unique()),
)
meteos = col_b.multiselect(
    "Meteo", options=sorted(map_data["meteo_label"].dropna().unique()),
    default=list(map_data["meteo_label"].dropna().unique()),
)

filtered = map_data[
    map_data["zone"].isin(zones)
    & map_data["gravite_label"].isin(gravites)
    & map_data["meteo_label"].isin(meteos)
]
st.caption(
    f"{len(filtered):,} accidents affiches "
    f"({(filtered['zone'] == 'Metropole').sum():,} metropole, "
    f"{(filtered['zone'] == 'DOM-TOM').sum():,} DOM-TOM)"
)

fig = px.scatter_map(
    filtered,
    lat="lat", lon="long", color="gravite_label",
    hover_data=["meteo_label", "dep", "zone"],
    zoom=1.5 if inclure_domtom else 4.5, height=550,
    color_discrete_map={
        "Indemne": "green", "Blesse leger": "gold",
        "Blesse hospitalise": "orange", "Tue": "red",
    },
)
fig.update_layout(map_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig, use_container_width=True)
