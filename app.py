import panel as pn
import polars as pl
import plotly.express as px
import requests
import os
from sqlalchemy import create_engine

# Panel extensions
pn.extension("plotly")

# Load environment variables (if any)
REDASH_URL = os.getenv("REDASH_URL", "http://192.168.80.30:8080")
REDASH_API_KEY = os.getenv("REDASH_API_KEY", "FJBeHB2jfkXiNIClff27R2rdoO6W4UuGflX8EfJ4")
CELL_QUERY_ID = os.getenv("CELL_QUERY_ID", "24")
CYCLE_QUERY_ID = os.getenv("CYCLE_QUERY_ID", "28")


def get_redash_data(query_id):
    """Fetch data from Redash."""
    url = f"{REDASH_URL}/api/queries/{query_id}/results.json"
    headers = {"Authorization": f"Key {REDASH_API_KEY}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return pl.DataFrame(data["query_result"]["data"]["rows"])
    else:
        return pl.DataFrame()


# Fetch and cache Redash Data
def load_data():
    return get_redash_data(CELL_QUERY_ID)


cell_data = load_data()

# Sidebar: Filtering Controls
design_filter = pn.widgets.MultiSelect(name="Filter by Design", options=cell_data["design_name"].unique().to_list())
test_status_filter = pn.widgets.MultiSelect(name="Test Status", options=cell_data["test_status"].unique().to_list())


# Table for displaying filtered cells
@pn.depends(design_filter, test_status_filter)
def filter_cells(design, status):
    df = cell_data.clone()
    if design:
        df = df.filter(pl.col("design_name").is_in(design))
    if status:
        df = df.filter(pl.col("test_status").is_in(status))
    return pn.widgets.DataFrame(df.to_pandas(), width=900, height=500)


# MultiChoice widget for selecting specific cells for plotting
selected_cells = pn.widgets.MultiChoice(name="Select Cells for Plotting", options=cell_data["cell_id"].to_list())


# Plotting Function
def get_cycle_data(cell_ids):
    """Fetch cycle data for selected cells from Redash."""
    if not cell_ids:
        return pl.DataFrame()
    all_data = [get_redash_data(CYCLE_QUERY_ID).filter(pl.col("cell_id") == cid) for cid in cell_ids]
    return pl.concat(all_data) if all_data else pl.DataFrame()


@pn.depends(selected_cells.param.value)
def plot_cells(cell_ids):
    cycle_data = get_cycle_data(cell_ids)
    if cycle_data.is_empty():
        return "No data available for selected cells."

    df = cycle_data.to_pandas()
    fig = px.line(df, x="cycle_number", y="discharge_capacity", color="cell_id", title="Cycle Performance")
    return pn.pane.Plotly(fig)


# Tab Layouts
tab1 = pn.Column("## Cell Metadata", design_filter, test_status_filter, filter_cells)
tab2 = pn.Column("## Plot Cycle Data", selected_cells, plot_cells)

# Main Dashboard Layout
tabs = pn.Tabs(("Cell Metadata", tab1), ("Cycle Plotting", tab2))

pn.template.FastListTemplate(title="Battery Analytics Dashboard", main=[tabs]).servable()
