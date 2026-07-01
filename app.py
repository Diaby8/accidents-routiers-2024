import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Accidents Routiers 2024 — Dashboard", layout="wide")

DOMTOM_DEP = {"971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988"}
GRAV_LABELS = {1: "Indemne", 2: "Tue", 3: "Blesse hospitalise", 4: "Blesse leger"}
METEO_LABELS = {
    1: "Normale", 2: "Pluie legere", 3: "Pluie forte", 4: "Neige/grele",
    5: "Brouillard/fumee", 6: "Vent fort/tempete", 7: "Temps eblouissant",
    8: "Temps couvert", 9: "Autre",
}
CATR_LABELS = {
    1: "Autoroute", 2: "Route nationale", 3: "Route departementale",
    4: "Voie communale", 5: "Hors reseau public", 6: "Parc de stationnement",
    7: "Route de metropole urbaine", 9: "Autre",
}
TRANCHE_ORDER = ["Matin", "Apres-midi", "Soir", "Nuit", "Inconnu"]


@st.cache_data
def load_bronze():
    caract = pd.read_csv("data/caract-2024.csv", sep=";", encoding="latin1", low_memory=False)
    lieux = pd.read_csv("data/lieux-2024.csv", sep=";", encoding="latin1", low_memory=False)
    usagers = pd.read_csv("data/usagers-2024.csv", sep=";", encoding="latin1", low_memory=False)
    vehicules = pd.read_csv("data/vehicules-2024.csv", sep=";", encoding="latin1", low_memory=False)
    return caract, lieux, usagers, vehicules


@st.cache_data
def load_gold():
    fait = pd.read_csv("data/gold_fait_accidents.csv")
    dim_lieu = pd.read_csv("data/gold_dim_lieu.csv")
    return fait, dim_lieu


caract, lieux, usagers, vehicules = load_bronze()
fait, dim_lieu = load_gold()
tables = {"caracteristiques": caract, "lieux": lieux, "usagers": usagers, "vehicules": vehicules}

st.title("Accidents Routiers 2024 — Dashboard")
st.caption("TP Data Integration & Applications — ST2DLDI — Architecture Medallion (Bronze -> Silver -> Gold -> BI)")

tab_profiling, tab_quality, tab_map, tab_bi = st.tabs(
    ["Profiling", "Data Quality", "Cartographie", "Analyses BI"]
)

# ============================================================ PROFILING
with tab_profiling:
    st.subheader("Structure des tables (couche Bronze)")
    table_choice = st.selectbox("Table", list(tables.keys()))
    df_choice = tables[table_choice]
    c1, c2 = st.columns(2)
    c1.metric("Lignes", f"{len(df_choice):,}")
    c2.metric("Colonnes", df_choice.shape[1])
    st.dataframe(
        df_choice.dtypes.astype(str).rename("Type").reset_index().rename(columns={"index": "Colonne"}),
        use_container_width=True, hide_index=True,
    )

    st.subheader("Valeurs manquantes")
    missing = (df_choice.isnull().sum() / len(df_choice) * 100).sort_values(ascending=False)
    missing = missing[missing > 0]
    if missing.empty:
        st.write("Aucune valeur manquante dans cette table.")
    else:
        fig_missing = px.bar(
            missing.round(1), orientation="h", labels={"value": "% manquant", "index": "Colonne"},
        )
        fig_missing.update_layout(showlegend=False, height=300, margin={"t": 10})
        st.plotly_chart(fig_missing, use_container_width=True)

    st.subheader("Anomalies categorielles et coherence")
    categories_attendues = {
        "usagers.grav": (usagers["grav"], [1, 2, 3, 4]),
        "usagers.sexe": (usagers["sexe"], [1, 2]),
        "usagers.catu": (usagers["catu"], [1, 2, 3]),
        "caract.lum": (caract["lum"], [1, 2, 3, 4, 5]),
        "caract.atm": (caract["atm"], [1, 2, 3, 4, 5, 6, 7, 8, 9]),
    }
    rows = []
    for label, (serie, valides) in categories_attendues.items():
        uniques = serie.dropna().unique()
        inattendues = [v for v in uniques if v not in valides]
        rows.append({
            "Colonne": label,
            "Statut": "Anomalie" if inattendues else "OK",
            "Valeurs inattendues": str(inattendues) if inattendues else "-",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    age = 2024 - usagers["an_nais"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Coords hors metropole (dep)", f"{caract['dep'].astype(str).isin(DOMTOM_DEP).sum():,}")
    k2.metric("Ages negatifs/aberrants", int((age < 0).sum()) + int((age > 110).sum()))
    k3.metric("Doublons (lieux)", int(lieux.duplicated().sum()))
    k4.metric("Valeurs -1 (usagers.sexe)", f"{int((usagers['sexe'] < 0).sum()):,}")

# ============================================================ DATA QUALITY
with tab_quality:
    st.subheader("Quality report")
    quality_report = pd.DataFrame([
        {"Probleme": "100% vide", "Colonne": "lieux.lartpc", "Action": "Supprimer"},
        {"Probleme": "99% vide", "Colonne": "vehicules.occutc", "Action": "Supprimer"},
        {"Probleme": "91.6% vide", "Colonne": "lieux.v2", "Action": "Supprimer"},
        {"Probleme": "19% vide", "Colonne": "lieux.voie", "Action": "Imputer 'Inconnu'"},
        {"Probleme": "4.2% vide", "Colonne": "caract.adr", "Action": "Imputer 'Inconnu'"},
        {"Probleme": "Hors metropole", "Colonne": "dep", "Action": "Separer DOM-TOM (par code departement)"},
        {"Probleme": "Valeurs -1", "Colonne": "sexe, place, col", "Action": "Remplacer par NaN"},
        {"Probleme": "Doublons", "Colonne": "lieux", "Action": "Supprimer (2 lignes)"},
    ])
    st.dataframe(quality_report, use_container_width=True, hide_index=True)

    st.subheader("Impact analysis")
    st.markdown(
        "- **Colonnes vides** : inutilisables, a exclure avant tout traitement.\n"
        "- **Valeurs -1** dans `grav` et `sexe` : faussent les moyennes et distributions.\n"
        "- **Coordonnees hors metro** : biaiseraient toute analyse geographique ou cartographique.\n"
        "- **Doublons** dans `lieux` : gonfleraient les comptages sur certaines routes.\n"
        "- **Ages** : aucune anomalie detectee (0 age negatif, 0 age > 110 ans)."
    )

    st.subheader("Avant / apres transformation")
    c1, c2, c3 = st.columns(3)
    c1.metric("Lignes Bronze (caract)", f"{len(caract):,}")
    c2.metric("Lignes Silver (metropole)", f"{len(fait):,}")
    c3.metric("Lignes ecartees (DOM-TOM)", f"{len(caract) - len(fait):,}")

# ============================================================ CARTOGRAPHIE
with tab_map:
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
        df["gravite_label"] = df["gravite_max"].map(GRAV_LABELS)
        df["meteo_label"] = df["atm"].map(METEO_LABELS).fillna("Inconnu")
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

    fig_map = px.scatter_map(
        filtered,
        lat="lat", lon="long", color="gravite_label",
        hover_data=["meteo_label", "dep", "zone"],
        zoom=1.5 if inclure_domtom else 4.5, height=550,
        color_discrete_map={
            "Indemne": "green", "Blesse leger": "gold",
            "Blesse hospitalise": "orange", "Tue": "red",
        },
    )
    fig_map.update_layout(map_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)

# ============================================================ ANALYSES BI
with tab_bi:
    st.subheader("Analyses BI (couche Gold)")

    fait_labeled = fait.copy()
    fait_labeled["gravite_label"] = fait_labeled["gravite_max"].map(GRAV_LABELS)
    fait_labeled["meteo_label"] = fait_labeled["meteo"].map(METEO_LABELS).fillna("Inconnu")

    row1_a, row1_b = st.columns(2)
    with row1_a:
        st.markdown("**Accidents par tranche horaire**")
        counts = fait_labeled["tranche_horaire"].value_counts().reindex(TRANCHE_ORDER).dropna()
        fig1 = px.bar(counts, labels={"value": "Nombre d'accidents", "index": "Tranche horaire"})
        fig1.update_layout(showlegend=False, height=350, margin={"t": 10})
        st.plotly_chart(fig1, use_container_width=True)

    with row1_b:
        st.markdown("**Repartition de la gravite**")
        fig2 = px.pie(fait_labeled, names="gravite_label", hole=0.4)
        fig2.update_layout(height=350, margin={"t": 10})
        st.plotly_chart(fig2, use_container_width=True)

    row2_a, row2_b = st.columns(2)
    with row2_a:
        st.markdown("**Meteo vs gravite**")
        cross = pd.crosstab(fait_labeled["meteo_label"], fait_labeled["gravite_label"])
        fig3 = px.bar(cross, barmode="stack")
        fig3.update_layout(height=350, margin={"t": 10}, xaxis_title="Meteo", yaxis_title="Nombre d'accidents")
        st.plotly_chart(fig3, use_container_width=True)

    with row2_b:
        st.markdown("**Top 10 departements par nombre d'accidents**")
        top_dep = fait_labeled["departement"].astype(str).value_counts().head(10)
        fig4 = px.bar(top_dep, labels={"value": "Nombre d'accidents", "index": "Departement"})
        fig4.update_layout(showlegend=False, height=350, margin={"t": 10})
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("**Type de route**")
    type_route = dim_lieu["type_route"].map(CATR_LABELS).value_counts()
    fig5 = px.bar(type_route, orientation="h", labels={"value": "Nombre d'accidents", "index": "Type de route"})
    fig5.update_layout(showlegend=False, height=350, margin={"t": 10})
    st.plotly_chart(fig5, use_container_width=True)
