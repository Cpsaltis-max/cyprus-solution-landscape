import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Cyprus Solution Landscape Dashboard",
    page_icon="📊",
    layout="wide"
)

DATA_FILE = Path("cyprus_master_dataset_v3.xlsx")
TRANSLATIONS_FILE = Path("translations.csv")

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    required = {
        "year", "community", "theme", "variable", "question_text",
        "response_category", "percent", "source_file"
    }
    missing = required.difference(df.columns)
    if missing:
        st.error(f"Missing required columns in data file: {missing}")
        st.stop()
    return df

@st.cache_data
def load_translations():
    tr = pd.read_csv(TRANSLATIONS_FILE)
    return tr

df = load_data()
translations = load_translations()

# ------------------------------------------------------------
# Language support
# ------------------------------------------------------------
language = st.sidebar.selectbox(
    "Language / Γλώσσα / Dil",
    ["English", "Greek", "Turkish"]
)

def tr(key: str) -> str:
    row = translations.loc[translations["key"] == key]
    if row.empty:
        return key
    value = row.iloc[0].get(language, key)
    return key if pd.isna(value) else str(value)

# ------------------------------------------------------------
# Stable mappings
# ------------------------------------------------------------
community_label = {
    "GC": tr("gc"),
    "TC": tr("tc")
}

community_reverse = {v: k for k, v in community_label.items()}

solution_keys = [
    "bbf_support",
    "unitary_state_support",
    "two_states_support",
    "status_quo_support"
]

solution_label = {k: tr(k) for k in solution_keys}
solution_reverse = {v: k for k, v in solution_label.items()}

response_label = {
    "against": tr("against"),
    "tolerate": tr("tolerate"),
    "in_favor": tr("in_favor")
}

binary_label = {
    "accepted": tr("accepted"),
    "rejected": tr("rejected")
}

# ------------------------------------------------------------
# Derived accepted / rejected data
# ------------------------------------------------------------
accepted = (
    df[df["response_category"].isin(["in_favor", "tolerate"])]
    .groupby(["year", "community", "variable"], as_index=False)["percent"]
    .sum()
    .rename(columns={"percent": "accepted"})
)

rejected = (
    df[df["response_category"] == "against"]
    [["year", "community", "variable", "percent"]]
    .rename(columns={"percent": "rejected"})
)

df_binary = pd.merge(
    accepted,
    rejected,
    on=["year", "community", "variable"],
    how="inner"
)

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.title(tr("app_title"))
st.caption(tr("app_subtitle"))

# ------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------
st.sidebar.header("Controls")

community_options = [tr("both"), tr("gc"), tr("tc")]
selected_community_label = st.sidebar.selectbox(
    tr("community"),
    community_options
)

solution_options = [solution_label[k] for k in solution_keys]
selected_solution_label = st.sidebar.selectbox(
    tr("solution"),
    solution_options
)

view_mode = st.sidebar.radio(
    tr("view_mode"),
    [tr("full_distribution"), tr("accepted_rejected")]
)

selected_variable = solution_reverse[selected_solution_label]

if selected_community_label == tr("both"):
    selected_community = "Both"
else:
    selected_community = community_reverse[selected_community_label]

# ------------------------------------------------------------
# Filtering
# ------------------------------------------------------------
df_filt = df[df["variable"] == selected_variable].copy()
df_bin_filt = df_binary[df_binary["variable"] == selected_variable].copy()

if selected_community != "Both":
    df_filt = df_filt[df_filt["community"] == selected_community]
    df_bin_filt = df_bin_filt[df_bin_filt["community"] == selected_community]

# Add translated display labels
df_filt["community_label"] = df_filt["community"].map(community_label)
df_filt["response_category_label"] = df_filt["response_category"].map(response_label)
df_filt["solution_label"] = df_filt["variable"].map(solution_label)

df_bin_filt["community_label"] = df_bin_filt["community"].map(community_label)
df_bin_filt["solution_label"] = df_bin_filt["variable"].map(solution_label)

# ------------------------------------------------------------
# Main chart
# ------------------------------------------------------------
if view_mode == tr("full_distribution"):
    st.subheader(f"{tr('distribution_title')}: {selected_solution_label}")

    fig = px.area(
        df_filt,
        x="year",
        y="percent",
        color="response_category_label",
        facet_col="community_label" if selected_community == "Both" else None,
        labels={
            "year": tr("year"),
            "percent": tr("percent"),
            "response_category_label": tr("category"),
            "community_label": tr("community")
        },
        title=None
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(legend_title_text=tr("category"))
    st.plotly_chart(fig, use_container_width=True)

else:
    st.subheader(f"{tr('accepted_rejected_title')}: {selected_solution_label}")

    df_melt = df_bin_filt.melt(
        id_vars=["year", "community", "community_label", "variable", "solution_label"],
        value_vars=["accepted", "rejected"],
        var_name="category",
        value_name="percent"
    )
    df_melt["category_label"] = df_melt["category"].map(binary_label)

    fig = px.line(
        df_melt,
        x="year",
        y="percent",
        color="category_label",
        markers=True,
        facet_col="community_label" if selected_community == "Both" else None,
        labels={
            "year": tr("year"),
            "percent": tr("percent"),
            "category_label": tr("category"),
            "community_label": tr("community")
        },
        title=None
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(legend_title_text=tr("category"))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# Cross-solution comparison: accepted
# ------------------------------------------------------------
st.divider()
st.subheader(tr("compare_solutions"))

df_compare = df_binary.copy()

if selected_community != "Both":
    df_compare = df_compare[df_compare["community"] == selected_community]

df_compare["community_label"] = df_compare["community"].map(community_label)
df_compare["solution_label"] = df_compare["variable"].map(solution_label)

fig2 = px.line(
    df_compare,
    x="year",
    y="accepted",
    color="solution_label",
    markers=True,
    facet_col="community_label" if selected_community == "Both" else None,
    labels={
        "year": tr("year"),
        "accepted": tr("accepted"),
        "solution_label": tr("solution"),
        "community_label": tr("community")
    },
    title=None
)
fig2.update_yaxes(range=[0, 100])
fig2.update_layout(legend_title_text=tr("solution"))
st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------
# Joint acceptance index
# ------------------------------------------------------------
st.divider()
st.subheader(tr("joint_acceptance"))
st.caption(tr("joint_acceptance_note"))

joint = (
    df_binary
    .pivot_table(
        index=["year", "variable"],
        columns="community",
        values="accepted",
        aggfunc="first"
    )
    .reset_index()
)

if {"GC", "TC"}.issubset(joint.columns):
    joint["joint_acceptance"] = joint[["GC", "TC"]].min(axis=1)
    joint["solution_label"] = joint["variable"].map(solution_label)

    fig3 = px.line(
        joint,
        x="year",
        y="joint_acceptance",
        color="solution_label",
        markers=True,
        labels={
            "year": tr("year"),
            "joint_acceptance": tr("joint_acceptance"),
            "solution_label": tr("solution")
        },
        title=None
    )
    fig3.update_yaxes(range=[0, 100])
    fig3.update_layout(legend_title_text=tr("solution"))
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Joint acceptance requires both GC and TC data.")

# ------------------------------------------------------------
# Data table and download
# ------------------------------------------------------------
st.divider()
with st.expander(tr("data_table")):
    table = df_filt.copy()
    table["community"] = table["community"].map(community_label)
    table["variable"] = table["variable"].map(solution_label)
    table["response_category"] = table["response_category"].map(response_label)
    st.dataframe(table, use_container_width=True)

    csv = table.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label=tr("download_filtered"),
        data=csv,
        file_name="filtered_solution_landscape_data.csv",
        mime="text/csv"
    )