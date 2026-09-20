import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_DIR = Path(__file__).resolve().parent.parent
MODELING_DIR = PROJECT_DIR / "modeling"

st.set_page_config(page_title="ML Project Dashboard", layout="wide")
st.title("ML Project Dashboard")

# --- Data (EDA) ---
data_json = MODELING_DIR / "01-data.json"
if data_json.exists():
    d = json.loads(data_json.read_text())
    st.header("Data (EDA)")

    shape = d["shape"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", shape["rows"])
    c2.metric("Columns", shape["columns"])
    c3.metric("Memory (MB)", shape["memory_mb"])

    target = d["target"]
    st.subheader(f"Target: {target['column']}")
    if target.get("class_balance"):
        balance_df = pd.DataFrame(
            {"class": list(target["class_balance"].keys()),
             "share": list(target["class_balance"].values())}
        )
        st.plotly_chart(px.bar(balance_df, x="class", y="share",
                                title="Class balance"), use_container_width=True)

    if d.get("numeric_distributions"):
        st.subheader("Numeric feature distributions")
        num_df = pd.DataFrame(d["numeric_distributions"]).T
        st.dataframe(num_df, use_container_width=True)
        st.plotly_chart(
            px.bar(num_df.reset_index(), x="index", y="skew", title="Skew by feature"),
            use_container_width=True,
        )

    if d.get("categorical_distributions"):
        st.subheader("Categorical features")
        for col, info in d["categorical_distributions"].items():
            vals = info["top_values"]
            cat_df = pd.DataFrame({"category": list(vals.keys()), "share": list(vals.values())})
            st.plotly_chart(px.pie(cat_df, names="category", values="share",
                                    title=col), use_container_width=True)

    if d.get("quality_flags"):
        st.subheader("Quality flags")
        for flag in d["quality_flags"]:
            st.warning(flag)
else:
    st.info("Run ml-modeling-data to populate this section.")

# --- Model comparison (optional, multiagent path only) ---
candidates_dir = MODELING_DIR / "train-candidates"
if candidates_dir.exists():
    st.header("Model Comparison")
    rows = []
    for candidate_dir in sorted(candidates_dir.iterdir()):
        metrics_file = candidate_dir / "metrics.json"
        if metrics_file.exists():
            m = json.loads(metrics_file.read_text())
            rows.append(m)
    if rows:
        cmp_df = pd.DataFrame(rows)
        st.dataframe(cmp_df, use_container_width=True)
        metric_col = "f1" if "f1" in cmp_df.columns else cmp_df.columns[-1]
        st.plotly_chart(
            px.bar(cmp_df, x="model", y=metric_col, title=f"Candidates by {metric_col}"),
            use_container_width=True,
        )

# --- Final Results ---
eval_json = MODELING_DIR / "04-evaluate.json"
if eval_json.exists():
    e = json.loads(eval_json.read_text())
    st.header("Final Results")
    st.subheader(f"Verdict: {e.get('verdict', 'n/a')}")

    metrics = e.get("metrics", {})
    baseline = e.get("baseline_metrics", {})
    if metrics:
        cols = st.columns(len(metrics))
        for col, (name, value) in zip(cols, metrics.items()):
            delta = None
            if name in baseline:
                delta = round(value - baseline[name], 4)
            col.metric(name, value, delta)

    gap = e.get("overfit_gap")
    if gap:
        st.write(f"Overfit gap (train vs. test): {gap}")
    if e.get("success_bar"):
        st.write(f"Success bar: {e['success_bar']}")
else:
    st.info("Run ml-modeling-evaluate to populate this section.")
