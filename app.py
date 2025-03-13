import panel as pn
import polars as pl
import plotly.express as px
import requests
import os
from datetime import datetime

from dotenv import load_dotenv
import param

# Load environment variables
load_dotenv()

# Panel extensions
pn.extension("plotly", "tabulator", sizing_mode="stretch_width")
print("Panel extensions loaded")

# Redash API configuration
REDASH_URL = os.getenv("REDASH_URL", "http://192.168.80.30:8080")
REDASH_API_KEY = os.getenv("REDASH_API_KEY", "FJBeHB2jfkXiNIClff27R2rdoO6W4UuGflX8EfJ4")
CELL_QUERY_ID = os.getenv("CELL_QUERY_ID", "24")
CYCLE_QUERY_ID = os.getenv("CYCLE_QUERY_ID", "28")

# Cache for query results
query_cache = {}


# Fetch Redash query results
def get_redash_query_results(query_id, params=None, cache_ttl=300):
    """Fetch results from a Redash query with caching."""
    cache_key = f"{query_id}_{str(params)}"

    # Check cache
    if cache_key in query_cache:
        cached_result, timestamp = query_cache[cache_key]
        if (datetime.now() - timestamp).total_seconds() < cache_ttl:
            return cached_result

    try:
        api_url = f"{REDASH_URL}/api/queries/{query_id}/results"
        headers = {"Authorization": f"Key {REDASH_API_KEY}", "Content-Type": "application/json"}
        response = requests.post(api_url, headers=headers, json={"parameters": params or {}})
        response.raise_for_status()

        query_result = response.json()
        if "query_result" in query_result and "data" in query_result["query_result"]:
            df = pl.DataFrame(query_result["query_result"]["data"]["rows"])
            query_cache[cache_key] = (df, datetime.now())
            return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Redash: {e}")

    return pl.DataFrame()


# Load initial data
def load_initial_data():
    df = get_redash_query_results(CELL_QUERY_ID)
    if not df.is_empty() and "regular_cycles" in df.columns:
        df = df.filter(pl.col("regular_cycles") > 20)
    return df


def get_cycle_data(cell_ids=None):
    """Get cycle data for specific cell IDs from the materialized view using Polars."""
    if not cell_ids:
        return pl.DataFrame()

    all_results = []
    for cell_id in cell_ids:
        params = {"cell_ids": str(cell_id)}
        df = get_redash_query_results(CYCLE_QUERY_ID, params)
        if not df.is_empty():
            all_results.append(df)

    return pl.concat(all_results) if all_results else pl.DataFrame()


def create_filter_widgets(df):
    """Dynamically generate filter widgets based on available columns, handling NaN values."""
    filter_widgets = {}
    for column in ["design_name", "experiment_group", "layer_types", "test_status", "test_year"]:
        if column in df.columns:
            options = df[column].drop_nulls().unique().to_list()
            options = sorted([str(opt) for opt in options])  # Ensure all values are strings
            options = [""] + options  # Add empty option for 'no filter'
            filter_widgets[column] = pn.widgets.Select(name=column.replace("_", " ").title(), options=options)
    return filter_widgets


def apply_filters(data, filters):
    """Apply filter widget selections to the Polars dataframe."""
    filtered_data = data.clone()
    for key, widget in filters.items():
        if widget.value:
            filtered_data = filtered_data.filter(pl.col(key) == widget.value)
    return filtered_data


# Modular class for Cell Selector Tab
class CellSelectorTab(param.Parameterized):
    selected_cell_ids = param.List(default=[], doc="Selected cell IDs")

    def __init__(self, cell_data, **params):
        super().__init__(**params)
        self.cell_data = cell_data
        self.required_columns = ["cell_id"]
        self.optional_columns = [col for col in cell_data.columns if col not in self.required_columns]
        self.default_columns = ["cell_id", "cell_name", "actual_nominal_capacity_ah", "regular_cycles",
                                "last_discharge_capacity", "discharge_capacity_retention"]

        self.filter_widgets = create_filter_widgets(self.cell_data)
        self.selection_indicator = pn.pane.Markdown("**0** cells selected")
        self.column_selector = pn.widgets.MultiSelect(
            name="Select Columns to Display",
            options=self.optional_columns,
            value=[col for col in self.default_columns if col not in self.required_columns],
            size=6,
            width=300
        )
        self.data_table = pn.widgets.Tabulator(
            pagination="remote",
            page_size=50,
            selectable="checkbox",
            header_align="left",
            theme="simple",
            layout="fit_data_table",
            show_index=False,
        )

        # Initialize handlers and table
        self.setup_event_handlers()
        self.update_table_data()

    def setup_event_handlers(self):
        for widget in self.filter_widgets.values():
            widget.param.watch(self.update_table_data, "value")
        self.data_table.param.watch(self.on_cell_selection, "selection")
        self.column_selector.param.watch(self.update_table_data, "value")

    def update_table_data(self, *events):
        filtered_data = apply_filters(self.cell_data, self.filter_widgets)
        selected_columns = self.column_selector.value or self.default_columns
        display_columns = self.required_columns + [col for col in selected_columns if col not in self.required_columns]
        filtered_data = filtered_data.select(display_columns)
        self.data_table.value = filtered_data.to_pandas()
        print(f"Table updated with {len(filtered_data)} rows after filtering")

    def on_cell_selection(self, event):
        selected_indices = event.new if hasattr(event, "new") else []
        if not selected_indices:
            self.selected_cell_ids = []
            self.selection_indicator.object = "**0** cells selected"
            return
        table_data = self.data_table.value
        selected_rows = [table_data.iloc[i]["cell_id"] for i in selected_indices]
        self.selected_cell_ids = selected_rows
        self.selection_indicator.object = f"**{len(self.selected_cell_ids)}** cells selected"

    def create_layout(self):
        sidebar = pn.Column(
            pn.pane.Markdown("## Filters"),
            *self.filter_widgets.values(),
            pn.pane.Markdown("## Display Settings"),
            self.column_selector,
            self.selection_indicator,
            width=300,
            sizing_mode="fixed",
        )
        return pn.Row(sidebar, self.data_table)


# Modular class for Cycle Plots Tab
class CyclePlotsTab(param.Parameterized):
    selected_cell_ids = param.List()

    def __init__(self, **params):
        super().__init__(**params)
        self.color_theme = pn.widgets.Select(
            name="Color Theme",
            options=["plotly", "plotly_white", "plotly_dark", "ggplot2",
                     "seaborn", "simple_white", "none"],
            value="plotly"
        )
        self.cycle_plot_container = pn.Column("No cells selected. Please select cells in the Cell Selector tab.")

    @param.depends("selected_cell_ids", watch=True)
    def update_cycle_plots(self):
        self.cycle_plot_container.clear()
        if not self.selected_cell_ids:
            self.cycle_plot_container.append(
                "No cells selected. Please select cells in the Cell Selector tab."
            )
            return

        self.cycle_plot_container.append(pn.pane.Markdown("Loading cycle data..."))
        cycle_data = get_cycle_data(self.selected_cell_ids)

        if cycle_data.is_empty():
            self.cycle_plot_container.clear()
            self.cycle_plot_container.append(
                "No cycle data available for the selected cells."
            )
            return

        fig = px.line(
            cycle_data.to_pandas(),
            x="regular_cycle_number",
            y="discharge_capacity",
            color="cell_id",
            title="Cycle Performance",
            template=self.color_theme.value,
        )
        fig.update_layout(
            height=600,
            legend_title_text="Cell ID",
            xaxis_title="Cycle Number",
            yaxis_title="Discharge Capacity (mAh)",
        )
        self.cycle_plot_container.clear()
        self.cycle_plot_container.append(pn.pane.Plotly(fig))

    def create_layout(self):
        sidebar = pn.Column(
            pn.pane.Markdown("## Plot Settings"),
            self.color_theme,
            width=300,
            sizing_mode="fixed",
        )
        main = pn.Column(self.cycle_plot_container)
        return pn.Row(sidebar, main)


# Main Dashboard
class BatteryDashboard(param.Parameterized):
    def __init__(self, **params):
        super().__init__(**params)
        self.cell_data = load_initial_data()
        self.cell_selector_tab = CellSelectorTab(self.cell_data)
        self.cycle_plots_tab = CyclePlotsTab()
        self.link_tabs()

    def link_tabs(self):
        self.cycle_plots_tab.param.set_param(
            selected_cell_ids=self.cell_selector_tab.selected_cell_ids
        )
        self.cell_selector_tab.param.watch(
            lambda event: self.cycle_plots_tab.param.set_param(selected_cell_ids=event.new),
            "selected_cell_ids"
        )

    def create_layout(self):
        cell_selector_page = self.cell_selector_tab.create_layout()
        cycle_plots_page = self.cycle_plots_tab.create_layout()

        tabs = pn.Tabs(
            ("Cell Selector", cell_selector_page),
            ("Cycle Plots", cycle_plots_page),
        )
        return pn.template.MaterialTemplate(
            title="Battery Analytics Dashboard",
            main=tabs,
            header_background="#212121",
        )


# Initialize and run the dashboard
dashboard = BatteryDashboard()
app = dashboard.create_layout()

app.servable()
