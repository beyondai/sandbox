import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

cells.append(nbf.v4.new_markdown_cell(
    "# Riot Churn - EDA\n\n"
    "Train table only (`modeling/datasets/churn_train.csv`), per "
    "`modeling/01-data.md`. Feature cutoff day 120, label day 180 "
    "(60-day horizon)."
))

cells.append(nbf.v4.new_code_cell(
    "import pandas as pd\n"
    "df = pd.read_csv('../modeling/datasets/churn_train.csv')\n"
    "print('shape:', df.shape)\n"
    "df.head()"
))

cells.append(nbf.v4.new_markdown_cell("## Nulls"))
cells.append(nbf.v4.new_code_cell(
    "df.isna().mean().sort_values(ascending=False)"
))

cells.append(nbf.v4.new_markdown_cell("## Target balance"))
cells.append(nbf.v4.new_code_cell(
    "df['label'].value_counts(normalize=True)"
))

cells.append(nbf.v4.new_markdown_cell("## Numeric feature distributions"))
cells.append(nbf.v4.new_code_cell(
    "numeric_cols = ['tenure_at_scoring','active_days','total_games',"
    "'total_wins','total_party_games','total_minutes','win_rate',"
    "'days_since_last_active','activity_trend','total_spend',"
    "'purchase_count','distinct_item_types','days_since_last_purchase']\n"
    "df[numeric_cols].describe().T.assign(skew=df[numeric_cols].skew())"
))

cells.append(nbf.v4.new_code_cell(
    "import matplotlib.pyplot as plt\n"
    "fig, axes = plt.subplots(3, 5, figsize=(18, 10))\n"
    "for ax, col in zip(axes.flat, numeric_cols):\n"
    "    ax.hist(df[col], bins=30)\n"
    "    ax.set_title(col, fontsize=9)\n"
    "for ax in axes.flat[len(numeric_cols):]:\n"
    "    ax.axis('off')\n"
    "plt.tight_layout()\n"
    "plt.show()"
))

cells.append(nbf.v4.new_markdown_cell("## Categorical distributions"))
cells.append(nbf.v4.new_code_cell(
    "for c in ['region', 'platform', 'acquisition_source']:\n"
    "    print(c)\n"
    "    print(df[c].value_counts(dropna=False))\n"
    "    print()"
))

cells.append(nbf.v4.new_markdown_cell(
    "## Label rate by category\n\n"
    "Quick check for any categorical with an obviously different churn "
    "rate - informs the features step."
))
cells.append(nbf.v4.new_code_cell(
    "for c in ['region', 'platform', 'acquisition_source']:\n"
    "    print(c)\n"
    "    print(df.groupby(c, dropna=False)['label'].mean())\n"
    "    print()"
))

nb['cells'] = cells
with open('eda.ipynb', 'w') as f:
    nbf.write(nb, f)
print('wrote eda.ipynb')
