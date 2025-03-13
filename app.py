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
    """Fetch results from a Redash query with caching"""
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
    """
    Get cycle data for specific cell IDs from the materialized view using Polars.
    """
    if not cell_ids:
        return pl.DataFrame()

    all_results = []
    for cell_id in cell_ids:
        # Get data for a single cell
        params = {"cell_ids": str(cell_id)}
        df = get_redash_query_results(CYCLE_QUERY_ID, params)
        if not df.is_empty():
            all_results.append(df)

    # Combine all results
    return pl.concat(all_results) if all_results else pl.DataFrame()


# Create filter widgets dynamically based on data
def create_filter_widgets(df):
    """Dynamically generate filter widgets based on available columns, handling NaN values"""
    filter_widgets = {}

    for column in ["design_name", "experiment_group", "layer_types", "test_status", "test_year"]:
        if column in df.columns:
            # Convert to list and filter out None (NaN) values before sorting
            options = df[column].drop_nulls().unique().to_list()
            options = sorted([str(opt) for opt in options])  # Ensure all values are strings
            options = [""] + options  # Add empty option for 'no filter'

            filter_widgets[column] = pn.widgets.Select(name=column.replace("_", " ").title(), options=options)

    return filter_widgets


# Apply filters to data
def apply_filters(data, filters):
    filtered_data = data.clone()
    for key, widget in filters.items():
        if widget.value:
            filtered_data = filtered_data.filter(pl.col(key) == widget.value)
    return filtered_data


class BatteryDashboard(param.Parameterized):
    selected_cell_ids = param.List(default=[], doc="Selected cell IDs")  # Ensure it's reactive
    def __init__(self, **params):
        super().__init__(**params)
        # Load data
        self.cell_data = load_initial_data()
        print(f"Loaded cell data: {self.cell_data.shape}")

        # Get all available columns from the data
        self.required_columns = ['cell_id']
        all_columns = list(self.cell_data.columns)
        optional_columns = [col for col in all_columns if col not in self.required_columns]

        # Define default columns to show
        self.default_columns = ["cell_id", "cell_name", "actual_nominal_capacity_ah", "regular_cycles",
                           "last_discharge_capacity", "discharge_capacity_retention"]

        # Create widgets
        self.filter_widgets = create_filter_widgets(self.cell_data)

        # UI Components
        self.selection_indicator = pn.pane.Markdown("**0** cells selected")
        self.selection_summary = pn.pane.Markdown("")
        self.cycle_plot_container = pn.Column("Select cells and click 'Generate Plots'")

        # Plot settings
        self.color_theme = pn.widgets.Select(
            name="Plot Theme",
            options=["plotly", "plotly_white", "plotly_dark", "ggplot2",
                     "seaborn", "simple_white", "none"],
            value="plotly"
        )

        # Create a multi-select widget for column selection
        self.column_selector = pn.widgets.MultiSelect(
            name="Select Columns to Display",
            options=optional_columns,
            value=[col for col in self.default_columns if col not in self.required_columns],
            size=6,  # Show 6 options at a time
            width=300
        )

        # Data table
        self.data_table = pn.widgets.Tabulator(
            pagination="remote",
            page_size=50,
            selectable="checkbox",
            header_align="left",
            theme = "simple",
            layout = "fit_data_table",
            show_index=False
        )

        # Plot button
        self.plot_button = pn.widgets.Button(
            name="Generate Plots",
            button_type="primary"
        )

        # Set up event handlers
        self.setup_event_handlers()

        # Initialize table
        self.update_table_data()


    def setup_event_handlers(self):
        # Connect table selection event
        self.data_table.param.watch(self.on_cell_selection,'selection')
        # Connect plot button
        self.plot_button.on_click(self.create_cycle_plots)

        # Add event handler for column selection
        self.column_selector.param.watch(self.update_table_data, 'value')

        # Connect filter widgets
        for widget in self.filter_widgets.values():
            widget.param.watch(self.update_table_data, 'value')

    def update_table_data(self, *events):
        filtered_data = apply_filters(self.cell_data, self.filter_widgets)
        selected_columns = self.column_selector.value or self.default_columns
        # Combine required columns with user-selected columns
        display_columns = self.required_columns + [col for col in selected_columns if col not in self.required_columns]

        filtered_data = filtered_data.select(display_columns)
        self.data_table.value = filtered_data.to_pandas()  # Convert to pandas
        print(f"Table updated with {len(filtered_data)} rows after filtering")

    def on_cell_selection(self, event):
        # Extract selected indices more robustly
        if hasattr(event, "new"):
            selected_indices = event.new
        elif hasattr(event, "index"):  # Common alternative in some widget libraries
            selected_indices = event.index
        elif isinstance(event, dict) and "selected" in event:
            selected_indices = event["selected"]
        else:
            # Try accessing as a property or attribute if event is an object
            selected_indices = getattr(event, "selected", None) or getattr(event, "selection", None) or []

        if not selected_indices:
            self.selected_cell_ids = []
            self.selection_indicator.object = "**0** cells selected after clicking"
            self.selection_summary.object = ""
            return
        # Get selected rows
        table_data = self.data_table.value
        try:
            selected_rows = [table_data.iloc[i] for i in selected_indices]
            self.selected_cell_ids = [row["cell_id"] for row in selected_rows]

            # Update UI
            self.selection_indicator.object = f"**{len(self.selected_cell_ids)}** cells selected"
            self.selection_summary.object = f"### Selected Cells\n\n{self.selected_cell_ids}"
        except Exception as e:
            import traceback
            error_msg = f"Error processing selection: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # For debugging
            self.selection_indicator.object = "**Error** in selection processing"
            self.selection_summary.object = f"### Selection Error\nCouldn't process selection. See logs for details."

    def create_cycle_plots(self, event):
        cell_ids = self.selected_cell_ids

        if not cell_ids:
            self.cycle_plot_container.clear()
            self.cycle_plot_container.append("No cells selected. Please select cells from the table.")
            return

        self.cycle_plot_container.clear()
        self.cycle_plot_container.append(pn.pane.Markdown("Loading cycle data..."))

        cycle_data = get_cycle_data(cell_ids)
        if cycle_data.is_empty():
            self.cycle_plot_container.clear()
            self.cycle_plot_container.append("No cycle data available for selected cells")
            return

        # Create the plot
        fig = px.line(
            cycle_data.to_pandas(),
            x="regular_cycle_number",
            y="discharge_capacity",
            color="cell_id",
            title="Cycle Performance",
            template=self.color_theme.value
        )

        fig.update_layout(
            height=600,
            legend_title_text="Cell ID",
            xaxis_title="Cycle Number",
            yaxis_title="Discharge Capacity (mAh)"
        )

        self.cycle_plot_container.clear()
        self.cycle_plot_container.append(pn.pane.Plotly(fig))

    def create_layout(self):
        # Sidebar layout
        sidebar = pn.Column(
            pn.pane.Markdown("## Filters"),
            *self.filter_widgets.values(),
            pn.pane.Markdown("## Plot Settings"),
            self.color_theme,
            self.plot_button,
            sizing_mode="fixed",
            width=300
        )

        # Main content layout (column selector above the data table)
        cell_metadata_layout = pn.Column(
            pn.pane.Markdown("## Select Columns to Display"),
            self.column_selector,  # Column selector placed above the table
            self.selection_indicator,
            self.data_table,
            self.selection_summary
        )


        # Main tabs
        tabs = pn.Tabs(
            ("Cell Metadata", cell_metadata_layout),
            ("Cycle Plots", self.cycle_plot_container)
        )

        # Main dashboard
        dashboard = pn.template.MaterialTemplate(
            title="Battery Analytics Dashboard",
            sidebar=sidebar,
            main=tabs,
            header_background="#212121"
        )

        return dashboard


# Initialize the dashboard
dashboard = BatteryDashboard()
app = dashboard.create_layout()

# Make the app servable
app.servable()

# if __name__ == "__main__":
#     print("Starting Panel app on port 8501...")
#     pn.serve(app, show=True, port=8501)