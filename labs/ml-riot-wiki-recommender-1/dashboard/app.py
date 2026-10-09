import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODELING_DIR = PROJECT_DIR / "modeling"


def project_title(folder_name: str) -> str:
    name = re.sub(r"^ml-", "", folder_name)
    name = re.sub(r"-\d+$", "", name)
    return name.replace("-", " ").replace("_", " ").title()


PROJECT_NAME = project_title(PROJECT_DIR.name)

st.set_page_config(page_title=f"{PROJECT_NAME} Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.75rem; padding-bottom: 1rem;
                       padding-left: 2rem; padding-right: 2rem; max-width: 1100px;}
    h1 {font-size: 1.5rem !important; margin-bottom: 0.2rem !important;}
    h2, h3 {font-size: 1.05rem !important; margin-top: 0.3rem !important;
            margin-bottom: 0.2rem !important;}
    div[data-testid="stMetricValue"] {font-size: 1.2rem !important;}
    div[data-testid="stMetricLabel"] {font-size: 0.8rem !important;}
    div[data-testid="stVerticalBlock"] {gap: 0.5rem !important;}
    .stAlert {padding: 0.4rem 0.8rem !important;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(PROJECT_NAME)

CHART_HEIGHT = 220
CHART_MARGIN = dict(l=10, r=10, t=30, b=10)


def compact(fig):
    fig.update_layout(height=CHART_HEIGHT, margin=CHART_MARGIN, title_font_size=13)
    return fig


data_json = MODELING_DIR / "01-data.json"
eval_json = MODELING_DIR / "04-evaluate.json"
candidates_dir = MODELING_DIR / "train-candidates"

tab_names = []
if data_json.exists():
    tab_names.append("Data (EDA)")
if candidates_dir.exists():
    tab_names.append("Model Comparison")
if eval_json.exists():
    tab_names.append("Final Results")

if not tab_names:
    st.info("Run ml-modeling-data to populate this dashboard.")
else:
    tabs = st.tabs(tab_names)
    tab_map = dict(zip(tab_names, tabs))

    if "Data (EDA)" in tab_map:
        with tab_map["Data (EDA)"]:
            d = json.loads(data_json.read_text())
            shape = d["shape"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Rows", shape["rows"])
            c2.metric("Columns", shape["columns"])
            c3.metric("Memory (MB)", shape["memory_mb"])

            left, right = st.columns(2)
            target = d["target"]
            if target.get("class_balance"):
                with left:
                    st.subheader(f"Target: {target['column']}")
                    bal_df = pd.DataFrame({"class": list(target["class_balance"].keys()),
                                            "share": list(target["class_balance"].values())})
                    st.plotly_chart(compact(px.bar(bal_df, x="class", y="share")),
                                     use_container_width=True, config={"displayModeBar": False})

            if d.get("numeric_distributions"):
                with right:
                    st.subheader("Skew by feature")
                    num_df = pd.DataFrame(d["numeric_distributions"]).T.round(3)
                    st.plotly_chart(compact(px.bar(num_df.reset_index(), x="index", y="skew")),
                                     use_container_width=True, config={"displayModeBar": False})

            if d.get("numeric_distributions"):
                st.subheader("Numeric summary")
                st.dataframe(pd.DataFrame(d["numeric_distributions"]).T.round(3),
                             use_container_width=True, height=150)

            if d.get("categorical_distributions"):
                st.subheader("Categorical distributions")
                items = list(d["categorical_distributions"].items())
                PIES_PER_ROW = 4
                for row_start in range(0, len(items), PIES_PER_ROW):
                    row_items = items[row_start:row_start + PIES_PER_ROW]
                    cols = st.columns(len(row_items))
                    for col, (name, info) in zip(cols, row_items):
                        vals = info["top_values"]
                        cat_df = pd.DataFrame({"category": list(vals.keys()), "share": list(vals.values())})
                        fig = px.pie(cat_df, names="category", values="share", title=name, hole=0.35)
                        # Percent labels go inside the slices; category names move to a
                        # horizontal legend below the pie instead of plotly's default
                        # right-side legend, which overlaps the slices once a narrow
                        # column (many categories -> many columns per row) shrinks the pie.
                        fig.update_traces(textposition="inside", textinfo="percent")
                        fig.update_layout(
                            height=CHART_HEIGHT + 70,
                            margin=dict(l=10, r=10, t=30, b=10),
                            title_font_size=13,
                            legend=dict(orientation="h", yanchor="top", y=-0.05,
                                        xanchor="center", x=0.5, font=dict(size=9)),
                        )
                        with col:
                            st.plotly_chart(fig, use_container_width=True,
                                             config={"displayModeBar": False})

            if d.get("quality_flags"):
                st.caption("**Quality flags:** " + " · ".join(d["quality_flags"]))

    if "Model Comparison" in tab_map:
        with tab_map["Model Comparison"]:
            rows = []
            for candidate_dir in sorted(candidates_dir.iterdir()):
                metrics_file = candidate_dir / "metrics.json"
                if metrics_file.exists():
                    rows.append(json.loads(metrics_file.read_text()))
            if rows:
                full_df = pd.DataFrame(rows)

                # Keep only compact scalars for this view - a metrics.json
                # may also carry free-form provenance (params, notes) or
                # list-valued fields (e.g. per-fold scores) that blow up
                # the table's width and break the chart if picked up as
                # the plotted column (a long string was silently chosen
                # as the y-axis once before this filter existed).
                def _is_compact_scalar(v):
                    if isinstance(v, bool):
                        return True
                    if isinstance(v, (int, float)):
                        return True
                    if isinstance(v, str):
                        return len(v) <= 40
                    return False

                scalar_cols = [c for c in full_df.columns
                               if full_df[c].map(_is_compact_scalar).all()]
                cmp_df = full_df[scalar_cols]
                numeric_cols = [c for c in cmp_df.columns
                                if pd.api.types.is_numeric_dtype(cmp_df[c])]

                # Prefer each candidate's own declared primary_metric (set by
                # ml-modeling-train/-multiagent when more than one metric
                # variant exists, e.g. a corrected vs. original CV score),
                # then "f1", then the last numeric column found.
                metric_col = None
                if "primary_metric" in cmp_df.columns and cmp_df["primary_metric"].nunique() == 1:
                    declared = cmp_df["primary_metric"].iloc[0]
                    metric_col = declared if declared in numeric_cols else None
                if metric_col is None:
                    metric_col = "f1" if "f1" in numeric_cols else (
                        numeric_cols[-1] if numeric_cols else None
                    )

                left, right = st.columns([1, 1])
                with left:
                    st.dataframe(cmp_df.round(4), use_container_width=True, height=150)
                with right:
                    if metric_col:
                        st.plotly_chart(compact(px.bar(cmp_df, x="model", y=metric_col)),
                                         use_container_width=True, config={"displayModeBar": False})

    if "Final Results" in tab_map:
        with tab_map["Final Results"]:
            e = json.loads(eval_json.read_text())

            verdict = e.get("verdict", "")
            low = verdict.lower()
            if "clears" in low or "beat" in low or "pass" in low:
                st.success(verdict, icon="✅")
            elif "misses" in low or "fail" in low or "below" in low:
                st.error(verdict, icon="⚠️")
            elif verdict:
                st.info(verdict)

            metrics = e.get("metrics", {})
            baseline = e.get("baseline_metrics", {})
            if metrics:
                rows = []
                for name, value in metrics.items():
                    base_value = baseline.get(name)
                    delta = round(value - base_value, 4) if base_value is not None else None
                    rows.append({"Metric": name.capitalize(), "Value": value, "Baseline": base_value, "Delta": delta})
                df = pd.DataFrame(rows)

                def color_delta(val):
                    if pd.isna(val):
                        return ""
                    color = "#1a7f37" if val > 0 else ("#c62828" if val < 0 else "#666")
                    return f"color: {color}; font-weight: 600;"

                styled = (
                    df.style
                    .format({"Value": "{:.3f}", "Baseline": "{:.3f}", "Delta": "{:+.3f}"}, na_rep="—")
                    .map(color_delta, subset=["Delta"])
                )
                st.dataframe(styled, use_container_width=True, hide_index=True, height=38 * (len(rows) + 1))

            gap = e.get("overfit_gap")
            if gap and "train" in gap and "test" in gap:
                delta = round(gap["train"] - gap["test"], 4)
                st.caption(f"Overfit gap — train **{gap['train']:.3f}** → test **{gap['test']:.3f}** (Δ {delta:+.3f})")
            elif gap:
                st.caption(f"Overfit gap: {gap}")

            if e.get("success_bar"):
                st.caption(f"Success bar: {e['success_bar']}")
