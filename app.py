import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ------------------------------------------------------------
# Page configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Cyprus Solution Landscape Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = Path("cyprus_master_dataset_v3.xlsx")
TRANSLATIONS_FILE = Path("translations.csv")

# ------------------------------------------------------------
# Responsive CSS
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
            padding-top: 0.8rem;
        }

        h1 {
            font-size: 1.55rem !important;
            line-height: 1.25 !important;
        }

        h2, h3 {
            font-size: 1.15rem !important;
        }

        .stAlert {
            font-size: 0.85rem;
        }

        [data-testid="stSidebar"] {
            min-width: 260px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_excel(DATA_FILE)

@st.cache_data
def load_translations():
    return pd.read_csv(TRANSLATIONS_FILE)

df = load_data()
translations = load_translations()

# ------------------------------------------------------------
# Language
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
# Labels and colours
# ------------------------------------------------------------
community_label = {
    "GC": tr("gc"),
    "TC": tr("tc")
}

community_reverse = {v: k for k, v in community_label.items()}

solution_order = [
    "bbf_support",
    "unitary_state_support",
    "two_states_support",
    "status_quo_support"
]

solution_label = {k: tr(k) for k in solution_order}
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

# Requested colour scheme:
# In distribution view: In favour = light green, Tolerate = dark green, Reject/Against = red.
response_colors = {
    tr("in_favor"): "lightgreen",
    tr("tolerate"): "darkgreen",
    tr("against"): "red"
}

# In binary view: Accepted = light green, Rejected = red.
binary_colors = {
    tr("accepted"): "lightgreen",
    tr("rejected"): "red"
}

# Cross-solution colours:
# BBF = green, Unitary = orange, Two States = red, Status Quo = pink.
solution_colors = {
    tr("bbf_support"): "green",
    tr("unitary_state_support"): "orange",
    tr("two_states_support"): "red",
    tr("status_quo_support"): "pink"
}

# ------------------------------------------------------------
# Derived accepted/rejected data
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

st.markdown(
    f"""
    **{tr("method_data_label")}:** {tr("method_data_text")}  
    **{tr("method_measure_label")}:** {tr("method_measure_text")}  
    **{tr("method_derived_label")}:** {tr("method_derived_text")}  
    **{tr("method_note_label")}:** {tr("method_note_text")}
    """
)

# ------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------
st.sidebar.header(tr("controls"))

display_mode = st.sidebar.radio(
    tr("display"),
    [tr("desktop"), tr("mobile")],
    index=0,
    help=tr("display_help")
)

community_options = [tr("both"), tr("gc"), tr("tc")]
selected_community_label = st.sidebar.selectbox(
    tr("community"),
    community_options,
    index=0
)

solution_options = [solution_label[k] for k in solution_order]
selected_solution_label = st.sidebar.selectbox(
    tr("solution"),
    solution_options,
    index=0
)

view_mode = st.sidebar.radio(
    tr("view_mode"),
    [tr("accepted_rejected"), tr("full_distribution")],
    index=0
)

selected_variable = solution_reverse[selected_solution_label]

if selected_community_label == tr("both"):
    selected_community = "Both"
else:
    selected_community = community_reverse[selected_community_label]

mobile_mode = display_mode == tr("mobile")

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def prepare_distribution_data(data):
    out = data.copy()
    out["community_label"] = out["community"].map(community_label)
    out["response_category_label"] = out["response_category"].map(response_label)
    out["solution_label"] = out["variable"].map(solution_label)
    return out

def prepare_binary_data(data):
    out = data.copy()
    out["community_label"] = out["community"].map(community_label)
    out["solution_label"] = out["variable"].map(solution_label)
    return out

def chart_height():
    return 430 if mobile_mode else 520

def show_distribution_chart(data):
    data = prepare_distribution_data(data)

    fig = px.line(
        data,
        x="year",
        y="percent",
        color="response_category_label",
        markers=True,
        color_discrete_map=response_colors,
        labels={
            "year": tr("year"),
            "percent": tr("percent"),
            "response_category_label": tr("category")
        },
        title=None
    )

    fig.update_yaxes(range=[0, 100])
    fig.update_layout(
        height=chart_height(),
        legend_title_text=tr("category"),
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

def show_binary_chart(data):
    data = prepare_binary_data(data)
    melted = data.melt(
        id_vars=["year", "community", "community_label", "variable", "solution_label"],
        value_vars=["accepted", "rejected"],
        var_name="category",
        value_name="percent"
    )
    melted["category_label"] = melted["category"].map(binary_label)

    fig = px.line(
        melted,
        x="year",
        y="percent",
        color="category_label",
        markers=True,
        color_discrete_map=binary_colors,
        labels={
            "year": tr("year"),
            "percent": tr("percent"),
            "category_label": tr("category")
        },
        title=None
    )

    fig.update_yaxes(range=[0, 100])
    fig.update_layout(
        height=chart_height(),
        legend_title_text=tr("category"),
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# Filter selected solution
# ------------------------------------------------------------
df_filt = df[df["variable"] == selected_variable].copy()
df_bin_filt = df_binary[df_binary["variable"] == selected_variable].copy()

if selected_community != "Both":
    df_filt = df_filt[df_filt["community"] == selected_community]
    df_bin_filt = df_bin_filt[df_bin_filt["community"] == selected_community]

# ------------------------------------------------------------
# Main visual
# ------------------------------------------------------------
st.subheader(selected_solution_label)

if view_mode == tr("accepted_rejected"):
    st.info(tr("accepted_info"))

if selected_community == "Both":
    if mobile_mode:
        tab_gc, tab_tc = st.tabs([tr("gc"), tr("tc")])
        with tab_gc:
            if view_mode == tr("full_distribution"):
                show_distribution_chart(df_filt[df_filt["community"] == "GC"])
            else:
                show_binary_chart(df_bin_filt[df_bin_filt["community"] == "GC"])

        with tab_tc:
            if view_mode == tr("full_distribution"):
                show_distribution_chart(df_filt[df_filt["community"] == "TC"])
            else:
                show_binary_chart(df_bin_filt[df_bin_filt["community"] == "TC"])

    else:
        if view_mode == tr("full_distribution"):
            plot_data = prepare_distribution_data(df_filt)

            fig = px.line(
                plot_data,
                x="year",
                y="percent",
                color="response_category_label",
                facet_col="community_label",
                markers=True,
                color_discrete_map=response_colors,
                labels={
                    "year": tr("year"),
                    "percent": tr("percent"),
                    "response_category_label": tr("category"),
                    "community_label": tr("community")
                },
                title=None
            )

            fig.update_yaxes(range=[0, 100])
            fig.update_layout(
                height=520,
                legend_title_text=tr("category"),
                margin=dict(l=20, r=20, t=30, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            plot_data = prepare_binary_data(df_bin_filt)
            melted = plot_data.melt(
                id_vars=["year", "community", "community_label", "variable", "solution_label"],
                value_vars=["accepted", "rejected"],
                var_name="category",
                value_name="percent"
            )
            melted["category_label"] = melted["category"].map(binary_label)

            fig = px.line(
                melted,
                x="year",
                y="percent",
                color="category_label",
                markers=True,
                facet_col="community_label",
                color_discrete_map=binary_colors,
                labels={
                    "year": tr("year"),
                    "percent": tr("percent"),
                    "category_label": tr("category"),
                    "community_label": tr("community")
                },
                title=None
            )

            fig.update_yaxes(range=[0, 100])
            fig.update_layout(
                height=520,
                legend_title_text=tr("category"),
                margin=dict(l=20, r=20, t=30, b=20)
            )

            st.plotly_chart(fig, use_container_width=True)
else:
    if view_mode == tr("full_distribution"):
        show_distribution_chart(df_filt)
    else:
        show_binary_chart(df_bin_filt)

# ------------------------------------------------------------
# Cross-solution comparison
# ------------------------------------------------------------
st.divider()
st.subheader(tr("compare_solutions"))

df_compare = df_binary.copy()

if selected_community != "Both":
    df_compare = df_compare[df_compare["community"] == selected_community]

df_compare = prepare_binary_data(df_compare)

if selected_community == "Both" and mobile_mode:
    tab_gc2, tab_tc2 = st.tabs([tr("gc"), tr("tc")])
    for tab, comm in [(tab_gc2, "GC"), (tab_tc2, "TC")]:
        with tab:
            sub = df_compare[df_compare["community"] == comm]

            fig2 = px.line(
                sub,
                x="year",
                y="accepted",
                color="solution_label",
                markers=True,
                color_discrete_map=solution_colors,
                labels={
                    "year": tr("year"),
                    "accepted": tr("accepted"),
                    "solution_label": tr("solution")
                },
                title=None
            )

            fig2.update_yaxes(range=[0, 100])
            fig2.update_layout(
                height=430,
                legend_title_text=tr("solution"),
                margin=dict(l=20, r=20, t=30, b=20)
            )

            st.plotly_chart(fig2, use_container_width=True)
else:
    fig2 = px.line(
        df_compare,
        x="year",
        y="accepted",
        color="solution_label",
        markers=True,
        facet_col="community_label" if selected_community == "Both" else None,
        color_discrete_map=solution_colors,
        labels={
            "year": tr("year"),
            "accepted": tr("accepted"),
            "solution_label": tr("solution"),
            "community_label": tr("community")
        },
        title=None
    )

    fig2.update_yaxes(range=[0, 100])
    fig2.update_layout(
        height=chart_height(),
        legend_title_text=tr("solution"),
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig2, use_container_width=True)

# ------------------------------------------------------------
# Joint acceptance
# ------------------------------------------------------------
st.divider()
st.subheader(tr("maximum_possible_agreement"))
st.caption(tr("joint_acceptance_note"))

joint = (
    df_binary
    .pivot_table(index=["year", "variable"], columns="community", values="accepted", aggfunc="first")
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
        color_discrete_map=solution_colors,
        labels={
            "year": tr("year"),
            "joint_acceptance": tr("joint_acceptance"),
            "solution_label": tr("solution")
        },
        title=None
    )

    fig3.update_yaxes(range=[0, 100])
    fig3.update_layout(
        height=chart_height(),
        legend_title_text=tr("solution"),
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig3, use_container_width=True)

# ------------------------------------------------------------
# Data table and download
# ------------------------------------------------------------
st.divider()

with st.expander(tr("data_table")):
    table = df.copy()
    table["community_display"] = table["community"].map(community_label)
    table["solution_display"] = table["variable"].map(solution_label)
    table["response_display"] = table["response_category"].map(response_label)

    st.dataframe(table, use_container_width=True)

    st.download_button(
        label=tr("download_filtered"),
        data=table.to_csv(index=False).encode("utf-8-sig"),
        file_name="cyprus_solution_landscape_data.csv",
        mime="text/csv"
    )

# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------
st.caption(tr("footer"))
