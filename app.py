import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Accidents Routiers 2024 — France metropolitaine", layout="wide")

GRAV_LABELS = {1: "Indemne", 2: "Tue", 3: "Blesse hospitalise", 4: "Blesse leger"}
GRAV_COLORS = {"Indemne": "#2ca02c", "Blesse leger": "#f1c40f", "Blesse hospitalise": "#e67e22", "Tue": "#c0392b"}
METEO_LABELS = {
    1: "Normale", 2: "Pluie legere", 3: "Pluie forte", 4: "Neige/grele",
    5: "Brouillard/fumee", 6: "Vent fort/tempete", 7: "Temps eblouissant",
    8: "Temps couvert", 9: "Autre",
}
TRANCHE_ORDER = ["Matin", "Apres-midi", "Soir", "Nuit"]


@st.cache_data
def load_data():
    df = pd.read_csv("data/silver_caract.csv", low_memory=False)
    df["gravite_label"] = df["gravite_max"].map(GRAV_LABELS)
    df["meteo_label"] = df["atm"].map(METEO_LABELS).fillna("Inconnu")
    df["dep"] = df["dep"].astype(str)
    return df


data = load_data()

st.title("Accidents corporels de la route — France metropolitaine, 2024")
st.caption(
    "Source : ONISR / data.gouv.fr — fichier BAAC. "
    f"{len(data):,} accidents corporels apres nettoyage (couche Silver)."
)

# --------------------------------------------------------------- filtres
st.sidebar.header("Filtres")
gravites = st.sidebar.multiselect(
    "Gravite", options=["Tue", "Blesse hospitalise", "Blesse leger"],
    default=["Tue", "Blesse hospitalise", "Blesse leger"],
)
tranches = st.sidebar.multiselect(
    "Tranche horaire", options=TRANCHE_ORDER, default=TRANCHE_ORDER,
)
meteos = st.sidebar.multiselect(
    "Meteo", options=sorted(data["meteo_label"].unique()), default=sorted(data["meteo_label"].unique()),
)

df = data[
    data["gravite_label"].isin(gravites)
    & data["tranche_horaire"].isin(tranches)
    & data["meteo_label"].isin(meteos)
]

if df.empty:
    st.warning("Aucun accident ne correspond aux filtres selectionnes.")
    st.stop()

# --------------------------------------------------------------- KPIs
k1, k2, k3, k4 = st.columns(4)
k1.metric("Accidents (filtre)", f"{len(df):,}")
k2.metric("Dont mortels", f"{(df['gravite_label'] == 'Tue').mean() * 100:.1f} %")
k3.metric("Tranche la plus a risque", df["tranche_horaire"].value_counts().idxmax())
k4.metric("Departement le plus touche", df["dep"].value_counts().idxmax())

st.divider()

# --------------------------------------------------------------- carte
st.subheader("Repartition geographique")
fig_map = px.scatter_map(
    df, lat="lat", lon="long", color="gravite_label",
    color_discrete_map=GRAV_COLORS,
    hover_data={"dep": True, "meteo_label": True, "tranche_horaire": True, "lat": False, "long": False},
    zoom=4.6, center={"lat": 46.6, "lon": 2.4}, height=520,
)
fig_map.update_layout(map_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# --------------------------------------------------------------- analyses croisees
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Gravite par tranche horaire")
    cross_h = pd.crosstab(df["tranche_horaire"], df["gravite_label"]).reindex(TRANCHE_ORDER)
    fig_h = px.bar(
        cross_h, barmode="stack", color_discrete_map=GRAV_COLORS,
        labels={"value": "Nombre d'accidents", "tranche_horaire": ""},
    )
    fig_h.update_layout(height=380, margin={"t": 10}, legend_title="Gravite")
    st.plotly_chart(fig_h, use_container_width=True)

with col_right:
    st.subheader("Gravite selon la meteo")
    cross_m = pd.crosstab(df["meteo_label"], df["gravite_label"])
    cross_m = cross_m.loc[cross_m.sum(axis=1).sort_values(ascending=False).index]
    fig_m = px.bar(
        cross_m, barmode="stack", color_discrete_map=GRAV_COLORS,
        labels={"value": "Nombre d'accidents", "meteo_label": ""},
    )
    fig_m.update_layout(height=380, margin={"t": 10}, legend_title="Gravite")
    st.plotly_chart(fig_m, use_container_width=True)

st.subheader("Top 10 des departements les plus touches")
top_dep = df["dep"].value_counts().head(10).sort_values()
fig_dep = px.bar(
    top_dep, orientation="h", labels={"value": "Nombre d'accidents", "index": "Departement"},
)
fig_dep.update_layout(showlegend=False, height=380, margin={"t": 10})
st.plotly_chart(fig_dep, use_container_width=True)
