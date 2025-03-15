import panel as pn
import polars as pl
import plotly.express as px
import plotly.graph_objects as go

import requests
import os
from datetime import datetime

from dotenv import load_dotenv
import param

# Load environment variables
load_dotenv()

# Panel extensions
pn.extension("plotly", "tabulator", "modal", sizing_mode="stretch_width")

pn.extension(raw_css=["""
    /* Make checkboxes significantly larger and more visible */
    .tabulator .tabulator-cell input[type="checkbox"],
    .tabulator .tabulator-header-contents input[type="checkbox"] {
        width: 24px !important;
        height: 24px !important;
        transform: scale(1.5) !important;
        cursor: pointer !important;
        display: block !important;
        margin: 0 auto !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    /* Add a clear border to separate the checkbox column from other columns */
    .tabulator .tabulator-cell.tabulator-row-handle,
    .tabulator .tabulator-header .tabulator-col.tabulator-row-handle {
        border-right: 2px solid #999 !important; 
        background-color: #f8f8f8 !important; /* Subtle background difference */
        padding: 10px 15px !important;
        min-width: 40px !important;
    }

    /* Style for the checkbox cell when selected */
    .tabulator .tabulator-row.tabulator-selected .tabulator-cell.tabulator-row-handle {
        background-color: #e0e8ff !important; /* Different background when selected */
    }

    /* Add a visible border to make checkboxes stand out */
    .tabulator input[type="checkbox"] {
        border: 2px solid #666 !important;
        border-radius: 3px !important;
        background-color: white !important;
    }
"""])

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
        cell_data = get_redash_query_results(CYCLE_QUERY_ID, params)
        if not cell_data.is_empty():
            # List of columns that should be normalized (containing capacity or energy)
            normalize_columns = [col for col in cell_data.columns if
                                 any(term in col.lower() for term in ['_capacity', '_energy'])]

            # Create expressions for normalization
            norm_expressions = []
            for col in normalize_columns:
                # 1. Regular cycle normalization (using cycle 1 as reference)
                first_cycle_val = cell_data.filter(pl.col('regular_cycle_number') == 1)[col].item()
                norm_expressions.append(
                    (pl.col(col) / first_cycle_val).alias(f'{col}_norm_reg')
                )

                # 2. 95th percentile normalization
                p95_val = cell_data[col].quantile(0.95)
                norm_expressions.append(
                    (pl.col(col) / p95_val).alias(f'{col}_norm_p95')
                )

            # Apply normalizations for this cell
            if norm_expressions:
                cell_data = cell_data.with_columns(norm_expressions)

            all_results.append(cell_data)

    cycle_data = pl.concat(all_results) if all_results else pl.DataFrame()
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
            styles={
                '_selector': {'padding': '12px'},  # Adds padding to checkbox column
                '*': {'padding': '4px'}  # Adds padding to all other cells
            },

            header_align="left",
            theme="bootstrap4",
            layout="fit_data_table",
            show_index=False,
            frozen_rows = [-2, -1],
            height=600,
            theme_classes=["table-bordered", "thead-dark"],
        )

        # Add a load button
        self.load_button = pn.widgets.Button(
            name="Load Cycle Data",
            button_type="primary",
            width=200
        )

        # Initialize handlers and table
        self.setup_event_handlers()
        self.update_table_data()

    def setup_event_handlers(self):
        for widget in self.filter_widgets.values():
            widget.param.watch(self.update_table_data, "value")
        self.data_table.param.watch(self.on_cell_selection, "selection")
        self.column_selector.param.watch(self.update_table_data, "value")

        # Add button click handler
        self.load_button.on_click(self.trigger_selection_update)

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

    def trigger_selection_update(self, event):
        """Explicit method to trigger parameter updates when button is clicked"""
        if self.selected_cell_ids:
            print(f"Loading data for {len(self.selected_cell_ids)} selected cells...")
            self.param.trigger('selected_cell_ids')
            self.param.trigger('selected_data')
        else:
            print("No cells selected")

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
        # Create a row with the button and selection indicator for below the table
        action_row = pn.Row(
            self.load_button,
            self.selection_indicator,
            align="center"
        )

        # Stack the table and action row in a column with scrollbars
        main_content = pn.Column(
            pn.pane.Markdown("### Cell Data", styles={"margin-bottom": "10px"}),
            pn.Column(
                self.data_table,
                max_height=650,  # Set maximum height
                scroll=True,  # Enable scrolling
                width_policy='max',
                styles={'overflow-y': 'auto', 'overflow-x': 'auto'}
            ),
            action_row,
            sizing_mode="stretch_width"
        )

        return pn.Row(sidebar, main_content)


# Modular class for Cycle Plots Tab
class CyclePlotsTab(param.Parameterized):
    def __init__(self, **params):
        super().__init__(**params)
        self.selected_cell_ids = []
        self.selected_cell_metadata = None
        self.cycle_data = None

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

        # New grouping widget
        self.group_by = pn.widgets.Select(
            name="Group By",
            options=["cell_id"],
            value="cell_id"
        )

        self.create_plot_settings_ui_elements()

        self.setup_event_handlers()

        self.cycle_plot_container = pn.Column("No cells selected. Please select cells in the Cell Selector tab.")

    def setup_event_handlers(self):
        """Set up event handlers for plot controls"""
        # Existing control handlers
        self.color_theme.param.watch(self.update_plots, "value")
        self.x_axis.param.watch(self.update_plots, "value")
        self.y_axis.param.watch(self.update_plots, "value")
        self.group_by.param.watch(self.update_plots, "value")

        # New control handlers
        self.plot_type.param.watch(self.update_plots, "value")

        # For series settings
        self.series_apply_button = pn.widgets.Button(name="Apply", button_type="success", width=100)
        self.series_cancel_button = pn.widgets.Button(name="Cancel", button_type="danger", width=100)

        self.series_apply_button.on_click(self.apply_series_settings)
        self.series_cancel_button.on_click(self.close_series_settings)

        # For advanced settings
        self.advanced_apply_button = pn.widgets.Button(name="Apply", button_type="success", width=100)
        self.advanced_cancel_button = pn.widgets.Button(name="Cancel", button_type="danger", width=100)

        self.advanced_apply_button.on_click(self.apply_advanced_settings)
        self.advanced_cancel_button.on_click(self.close_advanced_settings)

        # Also update the card collapsed state event handlers if needed
        self.series_settings_card.param.watch(self._update_series_settings_card, "collapsed")
        # self.advanced_settings_card.param.watch(self._update_advanced_settings_card, "collapsed")


    def open_series_settings(self, event):
        """Open the series settings modal"""
        self._update_series_settings_card()
        self.series_settings_card.open = True

    def close_series_settings(self, event):
        """Close the series settings modal without applying changes"""
        self.series_settings_card.open = False

    def apply_series_settings(self):
        # Update settings from current values
        self.series_settings = {
            'plot_type': self.plot_type.value,
            'group_by': self.group_by.value,
            'color_theme': self.color_theme.value,
            'x_axis': self.x_axis.value,
            'y_axis': self.y_axis.value
        }

        # Update the card display
        self._update_series_settings_card()

        # This is the critical line that was missing - update the plots
        self.update_plots()

        # Close the settings card
        self.close_series_settings()

    def open_advanced_settings(self, event):
        """Open the advanced settings modal"""
        # Pre-populate values from current plot if available
        if hasattr(self, 'x_axis') and self.x_axis.value:
            self.advanced_settings['x_axis_title'].value = self.x_axis.value.replace('_', ' ').title()
        if hasattr(self, 'y_axis') and self.y_axis.value:
            self.advanced_settings['y_axis_title'].value = self.y_axis.value.replace('_', ' ').title()

        self.advanced_settings_card.open = True

    def close_advanced_settings(self, event):
        """Close the advanced settings modal without applying changes"""
        self.advanced_settings_card.open = False

    def apply_advanced_settings(self, event):
        """Apply advanced settings and update the plot"""
        self.advanced_settings_card.open = False
        self.update_plots()

    def create_plot_settings_ui_elements(self):
        # Plot type control (new)
        self.plot_type = pn.widgets.Select(
            name="Plot Type",
            options=["scatter", "line", "line+markers", "bar"],
            value="line+markers"
        )

        # Buttons for advanced controls
        self.series_settings_button = pn.widgets.Button(
            name="Edit Series Settings",
            button_type="primary",
            width=150
        )

        self.advanced_settings_button = pn.widgets.Button(
            name="Advanced Plot Settings",
            button_type="primary",
            width=150
        )
        # Create modals for advanced settings
        self.series_settings_card = self._create_series_settings_card()
        self.advanced_settings_card = self._create_advanced_settings_card()
        # # Initially hide both cards
        # self.series_settings_card.layout.visibility = 'hidden'
        # self.advanced_settings_card.layout.visibility = 'hidden'

        # # Set z-index to ensure series settings appears above advanced settings
        # self.series_settings_card.layout.z_index = 2
        # self.advanced_settings_card.layout.z_index = 1

    def _create_series_settings_card(self):
        """Create a modal dialog for series-specific settings"""
        # This will be dynamically populated when opened
        self.series_settings = {}

        # Create an empty placeholder that will be filled when the modal is opened
        series_controls = pn.Column(pn.pane.Markdown("## Series Settings"))

        # Create the card
        card = pn.Card(
            series_controls,
            title="Series Settings",
            collapsed=True,
            collapsible=True,
            header_background="#e0e0e0"
        )

        # Add callback for when card is expanded
        card.param.watch(self._update_series_settings_card, "collapsed")

        return card

    def _update_series_settings_card(self):
        """Update the series settings card with current series data"""

        if event and event.new:
            return
        if not hasattr(self, 'cycle_data') or self.cycle_data.is_empty():
            return

        # Get the unique series based on the current group_by selection
        unique_groups = self.cycle_data[self.group_by.value].unique().to_list()

        # Create a control panel for each series
        series_panels = []
        for group in unique_groups:
            # Create a series-specific control set if it doesn't exist
            if str(group) not in self.series_settings:
                self.series_settings[str(group)] = {
                    'visible': pn.widgets.Checkbox(name="Visible", value=True),
                    'line_style': pn.widgets.Select(
                        name="Line Style",
                        options=["solid", "dash", "dot", "dashdot", "none"],
                        value="solid"
                    ),
                    'line_width': pn.widgets.IntSlider(name="Line Width", start=0, end=10, value=2),
                    'marker_style': pn.widgets.Select(
                        name="Marker",
                        options=["circle", "square", "diamond", "triangle-up", "cross", "x", "none"],
                        value="circle"
                    ),
                    'marker_size': pn.widgets.IntSlider(name="Marker Size", start=2, end=20, value=6),
                    'color': pn.widgets.ColorPicker(name="Color")
                }

            # Create a panel for this series
            panel = pn.Column(
                pn.pane.Markdown(f"### {group}"),
                *list(self.series_settings[str(group)].values()),
                styles={"background": "#f9f9f9", "padding": "10px", "border-radius": "5px", "margin-bottom": "10px"}
            )
            series_panels.append(panel)

            # Add buttons at the bottom
            button_row = pn.Row(
                self.series_apply_button,
                self.series_cancel_button,
                align="end"
            )

        # Update the modal content
        self.series_settings_card.content = pn.Column(
            pn.pane.Markdown("## Series Settings", styles={"text-align": "center"}),
            pn.Column(*series_panels, scroll=True, height=400)
        )

    def _create_advanced_settings_card(self):
        """Create a modal dialog for advanced plot settings"""
        # Create controls for advanced settings
        self.advanced_settings = {
            # Axis settings
            'x_axis_type': pn.widgets.Select(name="X-Axis Type", options=["linear", "log"], value="linear"),
            'y_axis_type': pn.widgets.Select(name="Y-Axis Type", options=["linear", "log"], value="linear"),
            'x_axis_min': pn.widgets.NumberInput(name="X-Axis Min", value=None),
            'x_axis_max': pn.widgets.NumberInput(name="X-Axis Max", value=None),
            'y_axis_min': pn.widgets.NumberInput(name="Y-Axis Min", value=None),
            'y_axis_max': pn.widgets.NumberInput(name="Y-Axis Max", value=None),

            # Grid settings
            'show_grid': pn.widgets.Checkbox(name="Show Grid", value=True),
            'grid_color': pn.widgets.ColorPicker(name="Grid Color", value="#e0e0e0"),

            # Title and labels
            'plot_title': pn.widgets.TextInput(name="Plot Title", placeholder="Enter plot title"),
            'x_axis_title': pn.widgets.TextInput(name="X-Axis Title"),
            'y_axis_title': pn.widgets.TextInput(name="Y-Axis Title"),
            'title_font_size': pn.widgets.IntSlider(name="Title Font Size", start=10, end=30, value=16),
            'axis_font_size': pn.widgets.IntSlider(name="Axis Font Size", start=8, end=20, value=12),

            # Legend settings
            'show_legend': pn.widgets.Checkbox(name="Show Legend", value=True),
            'legend_position': pn.widgets.Select(
                name="Legend Position",
                options=["top left", "top center", "top right", "center left",
                         "center right", "bottom left", "bottom center", "bottom right"],
                value="top right"
            ),

            # Plot size
            'plot_height': pn.widgets.IntSlider(name="Plot Height", start=300, end=1200, value=600),
            'plot_width': pn.widgets.IntSlider(name="Plot Width", start=400, end=1600, value=800)
        }

        # Organize controls into tabs
        axis_tab = pn.Column(
            pn.Row(self.advanced_settings['x_axis_type'], self.advanced_settings['y_axis_type']),
            pn.Row(self.advanced_settings['x_axis_min'], self.advanced_settings['x_axis_max']),
            pn.Row(self.advanced_settings['y_axis_min'], self.advanced_settings['y_axis_max']),
            pn.Row(self.advanced_settings['show_grid'], self.advanced_settings['grid_color'])
        )

        labels_tab = pn.Column(
            self.advanced_settings['plot_title'],
            self.advanced_settings['x_axis_title'],
            self.advanced_settings['y_axis_title'],
            pn.Row(self.advanced_settings['title_font_size'], self.advanced_settings['axis_font_size'])
        )

        legend_tab = pn.Column(
            pn.Row(self.advanced_settings['show_legend']),
            pn.Row(self.advanced_settings['legend_position'])
        )

        size_tab = pn.Column(
            pn.Row(self.advanced_settings['plot_height'], self.advanced_settings['plot_width'])
        )

        # Create tabs for the different setting categories
        settings_tabs = pn.Tabs(
            ('Axes', axis_tab),
            ('Labels', labels_tab),
            ('Legend', legend_tab),
            ('Size', size_tab)
        )

        # Create the card
        card = pn.Card(
            settings_tabs,
            title="Advanced Plot Settings",
            collapsed=True,
            collapsible=True,
            header_background="#e0e0e0"
        )

        return card

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

        if not hasattr(self, 'cycle_data') or self.cycle_data.is_empty():
            self.cycle_plot_container.append("No cycle data available. Please select cells first.")
            return
        cycle_data = self.cycle_data

        # Merge group information if available
        if self.selected_cell_metadata is not None and not self.selected_cell_metadata.is_empty():
            # Merge with cell metadata - always merge all metadata columns
            cell_metadata = self.selected_cell_metadata

            # Always merge all metadata to ensure we have all potential grouping columns available
            # First, identify which columns already exist in cycle_data to avoid duplicates
            existing_cols = set(cycle_data.columns)
            metadata_cols = [col for col in cell_metadata.columns if col != 'cell_id']

            # Select only columns from metadata that don't already exist in cycle_data
            unique_metadata_cols = [col for col in metadata_cols if col not in existing_cols]

            # If there are unique columns to merge, perform the join
            if unique_metadata_cols:
                cols_to_select = ['cell_id'] + unique_metadata_cols
                merged_df = cycle_data.join(
                    cell_metadata.select(cols_to_select),
                    on='cell_id',
                    how='left')
            else:
                merged_df = cycle_data
        else:
            merged_df = self.cycle_data

        print(merged_df.columns)
        if 'total_active_mass_g' in merged_df.columns:
            print("total Active mass found")
            # Find all columns that end with "capacity" or "energy" but don't already have "_specific_mAh_g" or "_specific_Wh_g"
            capacity_cols = [col for col in merged_df.columns
                             if col.endswith('capacity') and not col.endswith('_specific_mAh_g')]
            energy_cols = [col for col in merged_df.columns
                           if col.endswith('energy') and not col.endswith('_specific_Wh_g')]

            specific_value_exprs = []

            # Add expressions for capacity columns (convert to mAh/g)
            for col in capacity_cols:
                specific_value_exprs.append(
                    (
                        pl.when(pl.col('total_active_mass_g') > 0)
                        .then(1000 * pl.col(col) / pl.col('total_active_mass_g'))
                        .otherwise(None)
                    ).alias(f"{col}_specific_mAh_g")
                )

            # Add expressions for energy columns (convert to Wh/g)
            for col in energy_cols:
                specific_value_exprs.append(
                    (
                        pl.when(pl.col('total_active_mass_g') > 0)
                        .then(pl.col(col) / pl.col('total_active_mass_g'))
                        .otherwise(None)
                    ).alias(f"{col}_specific_Wh_g")
                )
            print("Found columns with capacity")
            if specific_value_exprs:
                print("Adding Specific capacity and energy to to cols")
                merged_df = merged_df.with_columns(specific_value_exprs)
        self.cycle_data = merged_df

        # Update axis options based on available columns
        all_numeric_cols = [col for col in self.cycle_data.columns
                        if self.cycle_data[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]]
        # Get the list of columns that come from cell_metadata
        cell_metadata_columns = set(
            self.selected_cell_metadata.columns) if self.selected_cell_metadata is not None else set()

        numeric_cols = [col for col in all_numeric_cols
                        if (col not in cell_metadata_columns)]

        # Find categorical columns
        categorical_cols = [
            col for col in cell_data.columns
            if col not in ['cell_id', 'cell_name'] and
               cell_data[col].dtype in [pl.Utf8, pl.String]
        ]

        # Ensure 'cell_id' and 'cell_name' are always first
        group_options = ["cell_id", "cell_name"] + categorical_cols

        # Update group options dynamically
        current_group = self.group_by.value
        self.group_by.options = group_options

        if current_group not in group_options:
            self.group_by.value = "cell_id"

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
        """Update plots based on the current selection and all plot settings"""
        self.cycle_plot_container.clear()

        if not hasattr(self, 'cycle_data') or self.cycle_data.is_empty():
            self.cycle_plot_container.append("No cycle data available. Please select cells first.")
            return

        # Create plotly figure
        fig = go.Figure()

        # Get unique groups for filtering
        unique_groups = self.cycle_data[self.group_by.value].unique().to_numpy()

        # Determine plot mode based on plot type
        mode_mapping = {
            "scatter": "markers",
            "line": "lines",
            "line+markers": "lines+markers",
            "bar": "markers"  # Bar will be handled separately
        }
        plot_mode = mode_mapping.get(self.plot_type.value, "lines+markers")

        # Create a trace for each group
        for group in unique_groups:
            group_str = str(group)
            group_data = self.cycle_data.filter(pl.col(self.group_by.value) == group)

            # Skip if series is set to invisible
            if group_str in self.series_settings and not self.series_settings[group_str]['visible'].value:
                continue

            # Apply series-specific settings if available
            series_props = {}
            if group_str in self.series_settings:
                settings = self.series_settings[group_str]

                # Line properties
                if settings['line_style'].value != "none":
                    series_props["line"] = {
                        "dash": settings['line_style'].value,
                        "width": settings['line_width'].value
                    }
                    if settings['color'].value:
                        series_props["line"]["color"] = settings['color'].value

                # Marker properties
                if settings['marker_style'].value != "none":
                    series_props["marker"] = {
                        "symbol": settings['marker_style'].value,
                        "size": settings['marker_size'].value
                    }
                    if settings['color'].value:
                        series_props["marker"]["color"] = settings['color'].value

            # Create the trace
            if self.plot_type.value == "bar":
                trace = go.Bar(
                    x=group_data[self.x_axis.value].to_numpy(),
                    y=group_data[self.y_axis.value].to_numpy(),
                    name=group_str,
                    **series_props
                )
            else:
                trace = go.Scatter(
                    x=group_data[self.x_axis.value].to_numpy(),
                    y=group_data[self.y_axis.value].to_numpy(),
                    mode=plot_mode,
                    name=group_str,
                    hovertemplate=(
                            f"{self.group_by.value.replace('_', ' ').title()}: {group}<br>" +
                            f"{self.x_axis.value}: %{{x}}<br>" +
                            f"{self.y_axis.value}: %{{y:.2f}}<extra></extra>"
                    ),
                    **series_props
                )

            fig.add_trace(trace)

        # Apply advanced settings
        layout_props = {
            "template": self.color_theme.value,
            "legend_title_text": self.group_by.value.replace('_', ' ').title(),
        }

        # Set axis titles (using advanced settings if available)
        layout_props["xaxis_title"] = (self.advanced_settings['x_axis_title'].value
                                       or self.x_axis.value.replace('_', ' ').title())
        layout_props["yaxis_title"] = (self.advanced_settings['y_axis_title'].value
                                       or self.y_axis.value.replace('_', ' ').title())

        # Apply other advanced settings if they have been set
        if self.advanced_settings['plot_title'].value:
            layout_props["title"] = self.advanced_settings['plot_title'].value

        if self.advanced_settings['title_font_size'].value:
            layout_props["title_font_size"] = self.advanced_settings['title_font_size'].value

        # Set axis types
        layout_props["xaxis_type"] = self.advanced_settings['x_axis_type'].value
        layout_props["yaxis_type"] = self.advanced_settings['y_axis_type'].value

        # Set axis ranges if provided
        if self.advanced_settings['x_axis_min'].value is not None:
            layout_props.setdefault("xaxis", {})
            layout_props["xaxis"]["range"] = [
                self.advanced_settings['x_axis_min'].value,
                self.advanced_settings['x_axis_max'].value or None
            ]

        if self.advanced_settings['y_axis_min'].value is not None:
            layout_props.setdefault("yaxis", {})
            layout_props["yaxis"]["range"] = [
                self.advanced_settings['y_axis_min'].value,
                self.advanced_settings['y_axis_max'].value or None
            ]

        # Grid settings
        if not self.advanced_settings['show_grid'].value:
            layout_props.setdefault("xaxis", {})
            layout_props.setdefault("yaxis", {})
            layout_props["xaxis"]["showgrid"] = False
            layout_props["yaxis"]["showgrid"] = False
        else:
            grid_color = self.advanced_settings['grid_color'].value
            layout_props.setdefault("xaxis", {})
            layout_props.setdefault("yaxis", {})
            layout_props["xaxis"]["gridcolor"] = grid_color
            layout_props["yaxis"]["gridcolor"] = grid_color

        # Legend settings
        layout_props["showlegend"] = self.advanced_settings['show_legend'].value
        if self.advanced_settings['show_legend'].value:
            legend_position = self.advanced_settings['legend_position'].value.split()
            layout_props["legend"] = {
                "y": 1.0 if legend_position[0] == "top" else 0.5 if legend_position[0] == "center" else 0.0,
                "x": 0.0 if legend_position[1] == "left" else 0.5 if legend_position[1] == "center" else 1.0,
                "yanchor": "top" if legend_position[0] == "top" else "middle" if legend_position[
                                                                                     0] == "center" else "bottom",
                "xanchor": "left" if legend_position[1] == "left" else "center" if legend_position[
                                                                                       1] == "center" else "right"
            }

        # Size settings
        layout_props["height"] = self.advanced_settings['plot_height'].value
        layout_props["width"] = self.advanced_settings['plot_width'].value

        # Update the layout
        fig.update_layout(**layout_props)

        # Add the plot to the container
        self.cycle_plot_container.append(pn.pane.Plotly(fig))

    def create_layout(self):
        """Create the layout for the cycle plots tab with enhanced controls"""
        # Basic controls sidebar
        basic_controls = pn.Column(
            pn.pane.Markdown("## Plot Settings", styles={'background': '#f0f0f0', 'padding': '10px'}),
            self.x_axis,
            self.y_axis,
            self.plot_type,
            pn.pane.Markdown("## Grouping"),
            self.group_by,
            width=300,
            sizing_mode="fixed",
            styles={'background': '#f8f9fa', 'border-right': '1px solid #ddd', 'padding': '10px'}
        )

        # Main content area with plot and cards
        main_content = pn.Column(
            self.cycle_plot_container,
            pn.Row(
                self.series_settings_card,
                # self.advanced_settings_card,
                sizing_mode='stretch_width'
            ),
            pn.Row(self.advanced_settings_card,
                # self.advanced_settings_card,
                sizing_mode='stretch_width'
            ),
            sizing_mode='stretch_both'
        )

        # Combine the layout components
        layout = pn.Row(
            basic_controls,
            main_content,
            sizing_mode='stretch_both'
        )

        return layout


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