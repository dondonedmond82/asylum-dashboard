import panel as pn
import pandas as pd
import hvplot.pandas
import os
import warnings

# ----------------------------------------
# Setup
# ----------------------------------------
warnings.filterwarnings("ignore")
pn.extension('tabulator', 'echarts')

# Load Data
file_path = "asylum_seekers_final.csv"
df = pd.read_csv(file_path)

# Clean up dataframe
df = df.drop(columns=["Unnamed: 0"], errors="ignore")
df["Year"] = df["Year"].astype(str)

# ----------------------------------------
# Filters
# ----------------------------------------
years = sorted(df["Year"].unique())
countries = sorted(df["Country / territory of asylum/residence"].unique())
origins = sorted(df["Origin"].unique())
procedures = sorted(df["RSD procedure type / level"].unique())

year_filter = pn.widgets.Select(name="Year", options=["All"] + years)
country_filter = pn.widgets.Select(name="Country of Asylum", options=["All"] + countries)
origin_filter = pn.widgets.Select(name="Origin", options=["All"] + origins)
procedure_filter = pn.widgets.Select(name="Procedure Type", options=["All"] + procedures)

# ----------------------------------------
# Helper: Apply filters
# ----------------------------------------
def filter_data():
    data = df.copy()
    if year_filter.value != "All":
        data = data[data["Year"] == year_filter.value]
    if country_filter.value != "All":
        data = data[data["Country / territory of asylum/residence"] == country_filter.value]
    if origin_filter.value != "All":
        data = data[data["Origin"] == origin_filter.value]
    if procedure_filter.value != "All":
        data = data[data["RSD procedure type / level"] == procedure_filter.value]
    return data

# ----------------------------------------
# KPIs
# ----------------------------------------
def kpi_cards():
    data = filter_data()
    total_applied = int(data["Applied during year"].sum())
    total_decisions = int(data["Total decisions"].sum())
    recognized = int(data["decisions_recognized"].sum())
    rejected = int(data["Rejected"].sum())
    pending_start = int(data["Total pending start-year"].sum())
    pending_end = int(data["Total pending end-year"].sum())

    recognition_rate = (recognized / total_decisions * 100) if total_decisions else 0
    rejection_rate = (rejected / total_decisions * 100) if total_decisions else 0
    pending_change = pending_end - pending_start

    return pn.Row(
        pn.indicators.Number(name="Total Applications", value=total_applied, format="{value:,}"),
        pn.indicators.Number(name="Recognition Rate", value=recognition_rate, format="{value:.1f}%"),
        pn.indicators.Number(name="Rejection Rate", value=rejection_rate, format="{value:.1f}%"),
        pn.indicators.Number(name="Pending Change", value=pending_change, format="{value:,}")
    )

# ----------------------------------------
# Visualizations
# ----------------------------------------

x = 1080
y = 380

y_bar = 510

@pn.depends(year_filter, country_filter, origin_filter, procedure_filter)
def trend_applications(*events):
    data = filter_data()
    return data.groupby("Year")["Applied during year"].sum().hvplot.line(title="Applications Over Time", width=x, height=y)

@pn.depends(year_filter, country_filter, origin_filter, procedure_filter)
def trend_decisions(*events):
    data = filter_data()
    grouped = data.groupby("Year")[["decisions_recognized", "Rejected", "Otherwise closed"]].sum()
    return grouped.hvplot.line(title="Decisions Breakdown Over Time", width=x, height=y)

@pn.depends(year_filter, country_filter, origin_filter, procedure_filter)
def top_countries(*events):
    data = filter_data()
    agg = data.groupby("Country / territory of asylum/residence")[["Applied during year"]].sum()
    return agg.sort_values("Applied during year", ascending=False).head(10).hvplot.bar(title="Top 10 Countries by Applications", width=x, height=y_bar, rot=30)

@pn.depends(year_filter, country_filter, origin_filter, procedure_filter)
def top_origins(*events):
    data = filter_data()
    agg = data.groupby("Origin")[["Applied during year"]].sum()
    return agg.sort_values("Applied during year", ascending=False).head(10).hvplot.bar(title="Top 10 Origins by Applications", width=x, height=y_bar, rot=30)

# ----------------------------------------
# Export
# ----------------------------------------
def exporting(event=None):
    filename = "AsylumData_filtered.xlsx"
    filter_data().to_excel(filename, index=False)
    os.system(filename)

export_button = pn.widgets.Button(name="Export Data", button_type="primary")
export_button.on_click(exporting)

# ----------------------------------------
# Tabs
# ----------------------------------------
summary_tab = pn.Column(
    "## 📊 Executive Summary",
    kpi_cards,
    pn.Row(trend_decisions),
    pn.Row(trend_applications)
)

analysis_tab = pn.Column(
    "## 🌍 Country & Origin Insights",
    pn.Row(top_countries),
    pn.Row(top_origins)
)

# ----------------------------------------
# Template
# ----------------------------------------
template = pn.template.FastListTemplate(
    title="Asylum Seekers Dashboard",
    sidebar=[pn.pane.Markdown("## Filters"), year_filter, country_filter, origin_filter, procedure_filter, export_button],
    main=[pn.Tabs(("Summary", summary_tab), ("Analysis", analysis_tab))],
    header_background="orange",
    accent_base_color="orange",
    site="Stakeholder Data Insights",
    logo="logo.png"
)

template.servable()
