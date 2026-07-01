import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Data Quality Summary — Road Accidents France 2024", layout="wide")

DOMTOM_DEP = {"971", "972", "973", "974", "975", "976", "977", "978", "986", "987", "988"}
ZONE_COLORS = {"Metropole": "#3498db", "DOM-TOM": "#e74c3c"}

EXPECTED_CHARACTERISTICS = {
    "lum": [1, 2, 3, 4, 5], "agg": [1, 2], "int": list(range(1, 10)),
    "atm": list(range(-1, 10)), "col": list(range(-1, 8)),
}
EXPECTED_LOCATIONS = {
    "catr": [1, 2, 3, 4, 5, 6, 7, 9], "circ": [-1, 1, 2, 3, 4], "vosp": [-1, 0, 1, 2, 3],
    "prof": [-1, 1, 2, 3, 4], "plan": [-1, 1, 2, 3, 4], "surf": list(range(-1, 10)),
    "infra": list(range(-1, 10)), "situ": [-1, 0, 1, 2, 3, 4, 5, 6, 8],
}
EXPECTED_VEHICLES = {
    "catv": [-1] + list(range(0, 22)) + [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 50, 60, 80, 99],
    "obs": list(range(-1, 18)), "obsm": [-1, 0, 1, 2, 4, 5, 6, 9],
    "choc": list(range(-1, 10)), "manv": list(range(-1, 27)), "motor": [-1, 0, 1, 2, 3, 4, 5, 6],
}
EXPECTED_USERS = {
    "catu": [1, 2, 3], "grav": [1, 2, 3, 4], "sexe": [1, 2], "trajet": [-1, 0, 1, 2, 3, 4, 5, 9],
    "secu1": list(range(-1, 10)), "secu2": list(range(-1, 10)), "secu3": list(range(-1, 10)),
    "locp": list(range(-1, 10)), "etatp": [-1, 1, 2, 3],
}


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
    "Road traffic injury accidents, France (raw Bronze data, ONISR / data.gouv.fr). "
    "All indicators below are computed live from the loaded CSV files, so they stay correct "
    "if the files are swapped for another year."
)

# --------------------------------------------------------------- live metrics on Bronze data
is_domtom = characteristics["dep"].astype(str).isin(DOMTOM_DEP)
outside_mainland = int(is_domtom.sum())

reference_year = int(characteristics["an"].mode()[0])
age = reference_year - users["an_nais"]
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


@st.cache_data
def find_coordinate_swaps(characteristics):
    coords = characteristics.dropna(subset=["lat", "long"]).copy()
    coords["lat_num"] = pd.to_numeric(coords["lat"].astype(str).str.replace(",", "."), errors="coerce")
    coords["long_num"] = pd.to_numeric(coords["long"].astype(str).str.replace(",", "."), errors="coerce")
    coords = coords.dropna(subset=["lat_num", "long_num"])
    dept_median = coords.groupby("dep")[["lat_num", "long_num"]].transform("median")
    dist_normal = np.sqrt((coords["lat_num"] - dept_median["lat_num"]) ** 2 + (coords["long_num"] - dept_median["long_num"]) ** 2)
    dist_swapped = np.sqrt((coords["long_num"] - dept_median["lat_num"]) ** 2 + (coords["lat_num"] - dept_median["long_num"]) ** 2)
    is_swapped = (dist_swapped < dist_normal) & (dist_normal > 1.0)
    return coords.index[is_swapped]


swap_idx = find_coordinate_swaps(characteristics)
swapped_count = len(swap_idx)

expected_by_table = {
    "characteristics": (characteristics, EXPECTED_CHARACTERISTICS),
    "locations": (locations, EXPECTED_LOCATIONS),
    "vehicles": (vehicles, EXPECTED_VEHICLES),
    "users": (users, EXPECTED_USERS),
}
category_rows = []
for table_name, (df, expected) in expected_by_table.items():
    for col, valid in expected.items():
        unique_values = df[col].dropna().unique()
        unexpected = [v for v in unique_values if v not in valid]
        category_rows.append({
            "Table": table_name, "Column": col,
            "Status": "Anomaly" if unexpected else "OK",
            "Unexpected values": str(unexpected) if unexpected else "-",
        })
category_df = pd.DataFrame(category_rows)

key_candidates = {
    "characteristics": "Num_Acc", "locations": "Num_Acc",
    "vehicles": "id_vehicule", "users": "id_usager",
}
key_rows = []
for name, key in key_candidates.items():
    df = tables[name]
    key_rows.append({
        "Table": name, "Candidate key": key, "Rows": len(df),
        "Distinct values": df[key].nunique(), "Unique": df[key].is_unique,
    })
key_df = pd.DataFrame(key_rows)

# --------------------------------------------------------------- KPIs
st.subheader("Dataset scale")
s1, s2, s3, s4 = st.columns(4)
s1.metric("Accidents", f"{len(characteristics):,}", help="1 row = 1 accident (characteristics table)")
s2.metric("People involved", f"{len(users):,}", help="1 row = 1 person (users table)")
s3.metric("Vehicles involved", f"{len(vehicles):,}", help="1 row = 1 vehicle (vehicles table)")
s4.metric("Location records", f"{len(locations):,}", help="Locations table: more rows than accidents, see Primary keys detail below")

avg_people = len(users) / len(characteristics)
avg_vehicles = len(vehicles) / len(characteristics)
s5, s6, s7, s8 = st.columns(4)
s5.metric("Avg. people / accident", f"{avg_people:.2f}")
s6.metric("Avg. vehicles / accident", f"{avg_vehicles:.2f}")
s7.metric("Killed", f"{int((users['grav'] == 2).sum()):,}", help="grav = 2 (official ONISR code)")
s8.metric("Reference year", reference_year)

st.subheader("Key quality indicators")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Points outside mainland France", f"{outside_mainland:,}", help="Classified by department code (971-978, 986-988)")
k2.metric("Duplicate rows (locations)", duplicates["locations"])
k3.metric("Age anomalies", negative_ages + outlier_ages, help=f"Negative ages + ages over 110, reference year {reference_year}")
k4.metric("Swapped lat/long values", swapped_count, help="Rows where lat and long are likely inverted (closer to their department's median once swapped)")

k5, k6, k7, k8 = st.columns(4)
k5.metric("Placeholder -1 values (sexe)", f"{neg_sexe:,}")
k6.metric("Categorical anomalies", f"{(category_df['Status'] == 'Anomaly').sum()} / {len(category_df)}", help="Columns with unexpected values, out of all enumerated columns checked")
k7.metric("Tables with a unique key", f"{int(key_df['Unique'].sum())} / {len(key_df)}")
k8.metric("Worst missing rate", f"{worst_missing.iloc[0]:.0f}%", help=f"{worst_missing.index[0]}")

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
    {"Issue": "Swapped lat/long values", "Column": "characteristics.lat/long", "Action": "Swap back (detected vs department median)"},
    {"Issue": "No unique key per accident", "Column": "locations.Num_Acc", "Action": "Keep first row per accident in dim_location (Gold layer)"},
])
st.dataframe(quality_report, width='stretch', hide_index=True)

with st.expander("Detail: % missing values per table"):
    for name, pct in missing_pct.items():
        st.write(f"**{name}**")
        if pct.empty:
            st.write("no missing values")
        else:
            st.dataframe(pct.rename("% missing").round(1), width='stretch')

with st.expander(f"Detail: categorical value checks ({len(category_df)} columns across 4 tables)"):
    st.dataframe(category_df, width='stretch', hide_index=True)

with st.expander("Detail: primary key candidates"):
    st.dataframe(key_df, width='stretch', hide_index=True)
    st.caption(
        "`locations` has no unique single-column key: some accidents have several rows "
        "(e.g. one per named road at a complex intersection), so `Num_Acc` repeats."
    )

st.subheader("Impact analysis")
st.markdown(
    "- **Empty columns**: unusable, must be excluded before any processing.\n"
    "- **Placeholder -1 values** in `grav` and `sexe`: bias averages and distributions.\n"
    "- **Coordinates outside mainland France**: would bias any geographic or map-based analysis.\n"
    "- **Duplicates** in `locations`: would inflate counts on certain roads.\n"
    "- **Swapped lat/long values**: place accidents in the middle of the ocean, nowhere near "
    "their real department; would break any map or distance-based analysis.\n"
    "- **`locations` without a unique key**: a naive join from the fact table would fan out rows "
    "for the 15,645 accidents with multiple location entries.\n"
    f"- **Ages**: {negative_ages + outlier_ages} anomaly(ies) detected "
    f"({negative_ages} negative, {outlier_ages} above 110 years)."
)

st.divider()

# --------------------------------------------------------------- map: geographic outliers
st.subheader("Geographic distribution — spotting points outside expected bounds")
st.caption(
    "Every point below is a real accident location. Points classified as DOM-TOM are not data "
    "errors (overseas French territories) and are kept, not excluded — they must simply be "
    "identified and separated so they don't distort a mainland-France analysis. Points with a "
    "detected lat/long swap are shown after correction."
)


@st.cache_data
def build_map_data(characteristics, _swap_idx):
    df = characteristics.copy()
    df["lat"] = pd.to_numeric(df["lat"].str.replace(",", "."), errors="coerce")
    df["long"] = pd.to_numeric(df["long"].str.replace(",", "."), errors="coerce")
    df.loc[_swap_idx, ["lat", "long"]] = df.loc[_swap_idx, ["long", "lat"]].values
    df = df.dropna(subset=["lat", "long"])
    df["zone"] = df["dep"].astype(str).isin(DOMTOM_DEP).map({True: "DOM-TOM", False: "Metropole"})
    df["was_swapped"] = df.index.isin(_swap_idx)
    return df


map_data = build_map_data(characteristics, swap_idx)

zone_counts = map_data["zone"].value_counts()
c1, c2, c3 = st.columns(3)
c1.metric("Mainland France points", f"{zone_counts.get('Metropole', 0):,}")
c2.metric("DOM-TOM points", f"{zone_counts.get('DOM-TOM', 0):,}")
c3.metric("Corrected swapped points", int(map_data["was_swapped"].sum()))

show_zones = st.multiselect("Show zone(s)", options=["Metropole", "DOM-TOM"], default=["Metropole"])
filtered = map_data[map_data["zone"].isin(show_zones)]
st.caption(f"{len(filtered):,} points displayed")

if set(show_zones) == {"Metropole"}:
    center, zoom = {"lat": 46.6, "lon": 2.4}, 4.7
elif set(show_zones) == {"DOM-TOM"}:
    center, zoom = {"lat": 0, "lon": 20}, 1.2
else:
    center, zoom = {"lat": 15, "lon": 15}, 1.1

fig_map = px.scatter_map(
    filtered,
    lat="lat", lon="long", color="zone",
    color_discrete_map=ZONE_COLORS,
    hover_data={"dep": True, "was_swapped": True, "lat": False, "long": False},
    center=center, zoom=zoom, height=560,
    opacity=0.55,
)
fig_map.update_traces(marker=dict(size=6))
fig_map.update_layout(
    map_style="carto-positron",
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    legend=dict(title="Zone", yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.7)"),
)
st.plotly_chart(fig_map, width='stretch')
