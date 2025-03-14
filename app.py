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


def get_cycle_data(cell_ids=None, cell_metadata=None):
    """Get cycle data and join with cell metadata."""
    if not cell_ids:
        return pl.DataFrame()

    all_results = []
    for cell_id in cell_ids:
        params = {"cell_ids": str(cell_id)}
        df = get_redash_query_results(CYCLE_QUERY_ID, params)
        if not df.is_empty():
            all_results.append(df)

    cycle_data = pl.concat(all_results) if all_results else pl.DataFrame()

    # Join with cell metadata if provided
    if cell_metadata is not None and not cycle_data.is_empty():
        # Convert cell_metadata to Polars if it's not already
        if not isinstance(cell_metadata, pl.DataFrame):
            cell_metadata = pl.from_pandas(cell_metadata)

        # Get only columns from metadata that aren't in cycle_data
        meta_cols = [col for col in cell_metadata.columns if col != "cell_id" and col not in cycle_data.columns]

        # Join the data
        if meta_cols:
            cycle_data = cycle_data.join(
                cell_metadata.select(["cell_id"] + meta_cols),
                on="cell_id",
                how="left"
            )

    return cycle_data


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
    selected_data = param.Parameter(default=None, doc="Full data for selected rows")

    def __init__(self, cell_data, **params):
        super().__init__(**params)
        self.cell_data = cell_data  # Store the original full dataset

        # Filtered and displayed data
        self.filtered_cell_data = cell_data

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
        # Apply row filters to get filtered rows (all columns)
        self.filtered_cell_data = apply_filters(self.cell_data, self.filter_widgets)

        # Get selected columns for display
        selected_columns = self.column_selector.value or []
        display_columns = self.required_columns + [col for col in selected_columns if col not in self.required_columns]

        # Create display DataFrame with filtered rows and selected columns
        display_df = self.filtered_cell_data.select(display_columns).to_pandas()

        # Update the table view with column-filtered data
        self.data_table.value = display_df

        # Clear selection when filters change
        self.data_table.selection = []
        self.selected_cell_ids = []
        self.selected_data = None
        self.selection_indicator.object = "**0** cells selected"

        print(f"Table updated with {len(display_df)} rows after filtering")

    def on_cell_selection(self, event):
        selected_indices = event.new if hasattr(event, "new") else []
        if not selected_indices:
            self.selected_cell_ids = []
            self.selected_data = None
            self.selection_indicator.object = "**0** cells selected"

        # Get the selected cell_ids from the displayed table
        selected_rows = self.data_table.value.iloc[selected_indices]
        selected_cell_ids = selected_rows['cell_id'].tolist()
        self.selected_cell_ids = selected_cell_ids

        # Then filter the full dataset based on these cell_ids
        self.selected_data = self.filtered_cell_data.filter(
            pl.col("cell_id").is_in(selected_cell_ids)
        )

        self.selection_indicator.object = f"**{len(self.selected_cell_ids)}** cells selected"

        print(f"Updated selected_cell_ids: {self.selected_cell_ids}")
        print(f"Selected data shape: {self.selected_data.shape if self.selected_data is not None else 'None'}")

        # Explicitly print before triggering
        print("About to trigger parameter updates")
        self.param.trigger('selected_cell_ids')
        self.param.trigger('selected_data')
        print("Parameter updates triggered")

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
    def __init__(self, **params):
        super().__init__(**params)
        self.selected_cell_ids = []
        self.selected_cell_metadata = None

        self.color_theme = pn.widgets.Select(
            name="Color Theme",
            options=["plotly", "plotly_white", "plotly_dark", "ggplot2",
                     "seaborn", "simple_white", "none"],
            value="plotly"
        )

        self.x_axis = pn.widgets.Select(
            name="X-Axis",
            options=["regular_cycle_number"],
            value="regular_cycle_number"
        )

        self.y_axis = pn.widgets.Select(
            name="Y-Axis",
            options=["discharge_capacity", "charge_capacity",
                     "coulombic_efficiency", "energy_efficiency"],
            value="discharge_capacity"
        )

        self.cycle_plot_container = pn.Column("No cells selected. Please select cells in the Cell Selector tab.")

        # Set up event handlers
        self.color_theme.param.watch(self.update_plots, "value")
        self.x_axis.param.watch(self.update_plots, "value")
        self.y_axis.param.watch(self.update_plots, "value")

    def update_selection(self, cell_ids, cell_data):
        """Update the selected cell IDs and data."""
        self.selected_cell_ids = cell_ids
        self.selected_cell_metadata = cell_data
        if not cell_ids:
            self.cycle_plot_container.append("No cells selected. Please select cells in the Cell Selector tab.")
            return

        self.cycle_plot_container.append(pn.pane.Markdown("Loading cycle data..."))
        self.cycle_data = get_cycle_data(cell_ids)

        if self.cycle_data.is_empty():
            self.cycle_plot_container.clear()
            self.cycle_plot_container.append("No cycle data available for the selected cells.")
            return

        # Update axis options based on available columns
        numeric_cols = [col for col in self.cycle_data.columns
                        if self.cycle_data[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]]

        # Keep current selection if possible
        current_x = self.x_axis.value if self.x_axis.value in numeric_cols else "regular_cycle_number"
        current_y = self.y_axis.value if self.y_axis.value in numeric_cols else "discharge_capacity"

        self.x_axis.options = numeric_cols
        self.x_axis.value = current_x

        self.y_axis.options = numeric_cols
        self.y_axis.value = current_y

        # Now update the plots with the loaded data
        self.update_plots()

    def update_plots(self, event=None):
        """Update plots based on the current selection and plot settings."""
        self.cycle_plot_container.clear()

        if not hasattr(self, 'cycle_data') or self.cycle_data.is_empty():
            self.cycle_plot_container.append("No cycle data available. Please select cells first.")
            return

        # Create plotly figure using the already loaded cycle data
        fig = px.line(
            self.cycle_data.to_pandas(),
            x=self.x_axis.value,
            y=self.y_axis.value,
            color="cell_id",
            title=f"{self.y_axis.value} vs {self.x_axis.value}",
            template=self.color_theme.value,
            hover_data=["cycle_number"]
        )

        # Add custom hover info if cell metadata is available
        if hasattr(self, 'cell_metadata') and self.selected_cell_metadata is not None and not self.selected_cell_metadata.is_empty():
            if "experiment_group" in self.cell_metadata.columns:
                # Create a mapping of cell_id to experiment_group
                cell_info = {}
                for row in self.cell_metadata.iter_rows(named=True):
                    cell_id = row["cell_id"]
                    exp_group = row.get("experiment_group", "Unknown")
                    cell_info[cell_id] = exp_group

                # Add custom hover text
                for i, cell_id in enumerate(sorted(self.selected_cell_ids)):
                    if i < len(fig.data):  # Ensure we don't go out of bounds
                        exp_group = cell_info.get(cell_id, "Unknown")
                        fig.data[i].hovertemplate = (
                                f"Cell ID: {cell_id}<br>" +
                                f"Experiment: {exp_group}<br>" +
                                f"{self.x_axis.value}: %{{x}}<br>" +
                                f"{self.y_axis.value}: %{{y:.2f}}"
                        )

        fig.update_layout(
            height=600,
            legend_title_text="Cell ID",
            xaxis_title=self.x_axis.value.replace('_', ' ').title(),
            yaxis_title=self.y_axis.value.replace('_', ' ').title(),
        )

        self.cycle_plot_container.append(pn.pane.Plotly(fig))

    def create_layout(self):
        sidebar = pn.Column(
            pn.pane.Markdown("## Plot Settings", styles={'background': '#f0f0f0', 'padding': '10px'}),
            self.x_axis,
            self.y_axis,
            self.color_theme,
            pn.layout.Divider(),
            pn.pane.Markdown("### Plot Options", styles={'padding': '10px'}),
            pn.layout.Accordion(
                ('Appearance', pn.Column(
                    pn.widgets.Switch(name="Show Legend", value=True, width=150),
                    pn.widgets.ColorPicker(name="Plot Line Color", value="#1f77b4"),
                    pn.widgets.IntSlider(name="Line Width", start=1, end=5, value=2),
                )),
                ('Grid Lines', pn.Column(
                    pn.widgets.Switch(name="X-Axis Grid", value=True, width=150),
                    pn.widgets.Switch(name="Y-Axis Grid", value=True, width=150),
                )),
            ),
            width=300,
            sizing_mode="fixed",
            styles={'background': '#f8f9fa', 'border-right': '1px solid #ddd', 'padding': '10px'}
        )
        main = pn.Column(self.cycle_plot_container, sizing_mode='stretch_both')
        return pn.Row(sidebar, main, sizing_mode='stretch_both')


# Main Dashboard
class BatteryDashboard(param.Parameterized):
    def __init__(self, **params):
        super().__init__(**params)
        self.cell_data = load_initial_data()
        self.cell_selector_tab = CellSelectorTab(self.cell_data)
        self.cycle_plots_tab = CyclePlotsTab()

        # Link tab interactions
        self.cell_selector_tab.param.watch(self.on_selection_change, ["selected_cell_ids", "selected_data"])

    def on_selection_change(self, event):
        # Only update if both selected_cell_ids and selected_data are available
        if hasattr(self.cell_selector_tab, "selected_cell_ids") and hasattr(self.cell_selector_tab, "selected_data"):
            if self.cell_selector_tab.selected_data is not None:
                self.cycle_plots_tab.update_selection(
                    self.cell_selector_tab.selected_cell_ids,
                    self.cell_selector_tab.selected_data
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