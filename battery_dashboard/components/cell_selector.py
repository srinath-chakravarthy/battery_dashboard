# Modular class for Cell Selector Tab
import panel as pn
import polars as pl
import param
import re
from ..data.loaders import get_redash_query_results


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

class CellSelectorTab(param.Parameterized):
    selected_cell_ids = param.List(default=[], doc="Selected cell IDs")
    selected_data = param.Parameter(default=None, doc="Full data for selected rows")
    search_query = param.String(default="", doc="Search query")


    def __init__(self, cell_data, **params):
        super().__init__(**params)
        self.cell_data = cell_data  # Store the original full dataset

        # Filtered and displayed data
        self.filtered_cell_data = cell_data

        self.required_columns = ["cell_id"]
        self.optional_columns = [col for col in cell_data.columns if col not in self.required_columns]
        self.default_columns = ["cell_id", "cell_name", "actual_nominal_capacity_ah", "regular_cycles",
                                "last_discharge_capacity", "discharge_capacity_retention"]

        # Create search bar
        self.search_input = pn.widgets.TextInput(
            name="Search",
            placeholder="Enter search terms (column:value or free text)",
            width=400
        )
        self.search_button = pn.widgets.Button(
            name="Search",
            button_type="primary",
            width=100
        )
        self.clear_search_button = pn.widgets.Button(
            name="Clear",
            button_type="default",
            width=100
        )
        self.search_info = pn.pane.Markdown("", styles={"color": "blue", "font-style": "italic"})

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

        # Add search event handlers
        self.search_button.on_click(self.on_search)
        self.clear_search_button.on_click(self.clear_search)
        self.search_input.param.watch(self.on_search_enter, "value_input")

    def on_search_enter(self, event):
        """Handle pressing Enter in the search box"""
        if event.new and event.new.endswith('\n'):
            # Remove the newline character
            self.search_input.value = event.new.rstrip('\n')
            self.on_search(None)

    def on_search(self, event):
        """Execute the search query"""
        query = self.search_input.value.strip()
        self.search_query = query
        self.update_table_data()

    def clear_search(self, event):
        """Clear the search query and reset the table"""
        self.search_input.value = ""
        self.search_query = ""
        self.search_info.object = ""
        self.update_table_data()

    def apply_search_query(self, df):
        """Apply the search query to the dataframe"""
        if not self.search_query:
            return df

        # Parse the search query
        # Support both specific column searches (column:value) and free text search
        query = self.search_query.lower()

        # Check for column:value pattern
        column_search_pattern = r'(\w+):\s*([\w.%<>=]+)'
        column_searches = re.findall(column_search_pattern, query)

        filtered_df = df
        search_applied = False

        # Handle column-specific searches
        for col_name, search_value in column_searches:
            # Remove these matches from the query for later free text search
            query = query.replace(f"{col_name}:{search_value}", "").strip()

            # Find the actual column name (case-insensitive match)
            actual_col = next((c for c in df.columns if c.lower() == col_name.lower()), None)

            if actual_col is None:
                self.search_info.object = f"⚠️ Column '{col_name}' not found"
                continue

            # Check for comparison operators
            if any(op in search_value for op in ['>', '<', '=']):
                try:
                    # Process numeric comparisons
                    if '>=' in search_value:
                        val = float(search_value.replace('>=', '').strip())
                        filtered_df = filtered_df.filter(pl.col(actual_col) >= val)
                    elif '<=' in search_value:
                        val = float(search_value.replace('<=', '').strip())
                        filtered_df = filtered_df.filter(pl.col(actual_col) <= val)
                    elif '>' in search_value:
                        val = float(search_value.replace('>', '').strip())
                        filtered_df = filtered_df.filter(pl.col(actual_col) > val)
                    elif '<' in search_value:
                        val = float(search_value.replace('<', '').strip())
                        filtered_df = filtered_df.filter(pl.col(actual_col) < val)
                    elif '=' in search_value:
                        val_str = search_value.replace('=', '').strip()
                        # Try to convert to number if it looks numeric
                        try:
                            val = float(val_str)
                            filtered_df = filtered_df.filter(pl.col(actual_col) == val)
                        except ValueError:
                            # It's a string
                            filtered_df = filtered_df.filter(
                                pl.col(actual_col).cast(pl.Utf8).str.contains(val_str, literal=True))
                    search_applied = True
                except ValueError:
                    self.search_info.object = f"⚠️ Invalid numeric value in '{search_value}'"
            else:
                # Simple text match
                filtered_df = filtered_df.filter(
                    pl.col(actual_col).cast(pl.Utf8).str.contains(search_value, literal=True))
                search_applied = True

        # Apply free text search across all string columns if query still has content
        query = query.strip()
        if query:
            # Build a combined filter for all string columns
            string_filters = []
            for col in df.columns:
                # Only search string-compatible columns
                try:
                    # Create a filter for this column
                    string_filters.append(pl.col(col).cast(pl.Utf8).str.contains(query))
                except:
                    # Skip columns that can't be converted to string for searching
                    continue

            if string_filters:
                # Combine all column filters with OR
                combined_filter = string_filters[0]
                for filter_expr in string_filters[1:]:
                    combined_filter = combined_filter | filter_expr

                filtered_df = filtered_df.filter(combined_filter)
                search_applied = True

        if search_applied:
            rows_found = len(filtered_df)
            total_rows = len(df)
            self.search_info.object = f"Found {rows_found} of {total_rows} cells matching search criteria"

        return filtered_df

    def update_table_data(self, *events):
        # Apply row filters to get filtered rows (all columns)
        self.filtered_cell_data = apply_filters(self.cell_data, self.filter_widgets)

        # Apply search query
        self.filtered_cell_data = self.apply_search_query(self.filtered_cell_data)

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
            self.selection_indicator.object = f"**Fetching data for {len(self.selected_cell_ids)} cells...**"

            print(f"Loading data for {len(self.selected_cell_ids)} selected cells...")
            self.param.trigger('selected_cell_ids')
            self.param.trigger('selected_data')
        else:
            print("No cells selected")

    def create_layout(self):
        # Create search components in a horizontal row
        search_row = pn.Row(
            self.search_input,
            self.search_button,
            self.clear_search_button,
            styles={"margin-bottom": "10px"}
        )

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
            search_row,
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

