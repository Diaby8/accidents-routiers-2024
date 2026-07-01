import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Data Quality Summary — Road Accidents France 2024", layout="wide")

DOMTOM_DEP = {"971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988"}
ZONE_COLORS = {"Metropole": "#3498db", "DOM-TOM": "#e74c3c"}


@st.cache_data
def load_bronze():
    characteristics = pd.read_csv("data/caract-2024.csv", sep=";", encoding="latin1", low_memory=False)
    locations = pd.read_csv("data/lieux-2024.csv", sep=";", encoding="latin1", low_memory=False)
    users = pd.read_csv("data/usagers-2024.csv", sep=";", encoding="latin1", low_memory=False)
    vehicles = pd.read_csv("data/vehicules-2024.csv", sep=";", encoding="latin1", low_memory=False)
    return characteristics, locations, users, vehicles


characteristics, locations, users, vehicles = load_bronze()
tables = {
    "characteristics": characteristics, "locations": locations,
    "users": users, "vehicles": vehicles,
}

st.title("Data Quality Summary")
st.caption(
    "TP Data Integration & Applications — ST2DLDI — Part 1.D — "
    "Road traffic injury accidents, France 2024 (raw Bronze data, ONISR / data.gouv.fr)"
)

# --------------------------------------------------------------- live metrics on Bronze data
is_domtom = characteristics["dep"].astype(str).isin(DOMTOM_DEP)
outside_mainland = int(is_domtom.sum())

age = 2024 - users["an_nais"]
negative_ages = int((age < 0).sum())
outlier_ages = int((age > 110).sum())

neg_sexe = int((users["sexe"] < 0).sum())
neg_place = int((users["place"] < 0).sum())

duplicates = {name: int(df.duplicated().sum()) for name, df in tables.items()}

missing_pct = {}
for name, df in tables.items():
    pct = (df.isnull().sum() / len(df) * 100)
    missing_pct[name] = pct[pct > 0].sort_values(ascending=False)

worst_missing = pd.concat(
    [pct.rename(name) for name, pct in missing_pct.items() if not pct.empty]
).sort_values(ascending=False)

# --------------------------------------------------------------- KPIs
st.subheader("Key indicators")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Rows loaded (Bronze, 4 files)", f"{sum(len(df) for df in tables.values()):,}")
k2.metric("Points outside mainland France", f"{outside_mainland:,}", help="Classified by department code (971-978, 986-988)")
k3.metric("Duplicate rows (locations)", duplicates["locations"])
k4.metric("Age anomalies", negative_ages + outlier_ages, help="Negative ages + ages over 110, derived from birth year")

k5, k6, k7, k8 = st.columns(4)
k5.metric("Placeholder -1 values (sexe)", f"{neg_sexe:,}")
k6.metric("Placeholder -1 values (place)", neg_place)
k7.metric("Worst missing rate", f"{worst_missing.iloc[0]:.0f}%", help=f"{worst_missing.index[0]}")
k8.metric("Columns with missing data", int((worst_missing > 0).sum()))

st.divider()

# --------------------------------------------------------------- quality report
st.subheader("Quality report")
quality_report = pd.DataFrame([
    {"Issue": "100% empty", "Column": "locations.lartpc", "Action": "Drop"},
    {"Issue": "99% empty", "Column": "vehicles.occutc", "Action": "Drop"},
    {"Issue": "91.6% empty", "Column": "locations.v2", "Action": "Drop"},
    {"Issue": "19% empty", "Column": "locations.voie", "Action": "Impute 'Unknown'"},
    {"Issue": "4.2% empty", "Column": "characteristics.adr", "Action": "Impute 'Unknown'"},
    {"Issue": "Outside mainland France", "Column": "dep", "Action": "Split off DOM-TOM (by department code)"},
    {"Issue": "Placeholder -1 values", "Column": "sexe, place, col", "Action": "Replace with NaN"},
    {"Issue": "Duplicates", "Column": "locations", "Action": "Drop (2 rows)"},
])
st.dataframe(quality_report, use_container_width=True, hide_index=True)

with st.expander("Detail: % missing values per table"):
    for name, pct in missing_pct.items():
        st.write(f"**{name}**")
        if pct.empty:
            st.write("no missing values")
        else:
            st.dataframe(pct.rename("% missing").round(1), use_container_width=True)

st.subheader("Impact analysis")
st.markdown(
    "- **Empty columns**: unusable, must be excluded before any processing.\n"
    "- **Placeholder -1 values** in `grav` and `sexe`: bias averages and distributions.\n"
    "- **Coordinates outside mainland France**: would bias any geographic or map-based analysis.\n"
    "- **Duplicates** in `locations`: would inflate counts on certain roads.\n"
    "- **Ages**: no anomaly detected (0 negative age, 0 age above 110)."
)

st.divider()

# --------------------------------------------------------------- map: geographic outliers
st.subheader("Geographic distribution — spotting points outside expected bounds")
st.caption(
    "Every point below is a real accident location. Points classified as DOM-TOM are not data "
    "errors (overseas French territories), but they must be identified and separated so they "
    "don't distort a mainland-France analysis."
)


@st.cache_data
def build_map_data(characteristics):
    df = characteristics.copy()
    df["lat"] = pd.to_numeric(df["lat"].str.replace(",", "."), errors="coerce")
    df["long"] = pd.to_numeric(df["long"].str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["lat", "long"])
    df["zone"] = df["dep"].astype(str).isin(DOMTOM_DEP).map({True: "DOM-TOM", False: "Metropole"})
    return df


map_data = build_map_data(characteristics)

zone_counts = map_data["zone"].value_counts()
c1, c2 = st.columns(2)
c1.metric("Mainland France points", f"{zone_counts.get('Metropole', 0):,}")
c2.metric("DOM-TOM points", f"{zone_counts.get('DOM-TOM', 0):,}")

show_zones = st.multiselect("Show zone(s)", options=["Metropole", "DOM-TOM"], default=["Metropole", "DOM-TOM"])
filtered = map_data[map_data["zone"].isin(show_zones)]
st.caption(f"{len(filtered):,} points displayed")

fig_map = px.scatter_map(
    filtered,
    lat="lat", lon="long", color="zone",
    color_discrete_map=ZONE_COLORS,
    hover_data={"dep": True, "lat": False, "long": False},
    zoom=1.5, height=520,
)
fig_map.update_layout(map_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig_map, use_container_width=True)
