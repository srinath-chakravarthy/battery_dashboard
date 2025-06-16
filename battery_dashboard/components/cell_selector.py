# battery_dashboard/components/cell_selector.py
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
        # Add to the end of your __init__ method:
        self.update_load_button_state()  # Initialize button state

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

    def format_table_data(self, df):
        """Format table data with status indicators and better presentation"""
        formatted_df = df.copy()

        # Add status dots for visual indicators
        if 'test_status' in formatted_df.columns:
            status_map = {
                'Active': '<span class="status-dot status-active"></span>Active',
                'Testing': '<span class="status-dot status-testing"></span>Testing',
                'Degraded': '<span class="status-dot status-degraded"></span>Degraded',
                'Failed': '<span class="status-dot status-degraded"></span>Failed'
            }
            formatted_df['Status'] = formatted_df['test_status'].map(status_map).fillna(formatted_df['test_status'])
            formatted_df = formatted_df.drop('test_status', axis=1)

        # Format numeric columns
        numeric_columns = {
            'actual_nominal_capacity_ah': lambda x: f"{x:.2f} Ah",
            'last_discharge_capacity': lambda x: f"{x:.2f} Ah",
            'discharge_capacity_retention': lambda x: f"{x:.1f}%",
            'total_cycles': lambda x: f"{int(x):,}",
            'regular_cycles': lambda x: f"{int(x):,}"
        }

        for col, formatter in numeric_columns.items():
            if col in formatted_df.columns:
                formatted_df[col] = formatted_df[col].apply(formatter)

        # Rename columns for better display
        column_renames = {
            'cell_id': 'Cell ID',
            'cell_name': 'Cell Name',
            'actual_nominal_capacity_ah': 'Capacity (Ah)',
            'regular_cycles': 'Cycles',
            'last_discharge_capacity': 'Last Capacity',
            'discharge_capacity_retention': 'Retention (%)'
        }

        formatted_df = formatted_df.rename(columns=column_renames)

        return formatted_df

    def configure_table_columns(self):
        """Configure table column widths and formatting"""
        column_config = {
            "Cell ID": {"width": 100, "frozen": True},
            "Cell Name": {"width": 150},
            "Capacity (Ah)": {"width": 120, "align": "center"},
            "Cycles": {"width": 80, "align": "center"},
            "Retention (%)": {"width": 100, "align": "center"},
            "Status": {"width": 100, "align": "center", "formatter": "html"}
        }

        return column_config

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

        formatted_df = self.format_table_data(display_df)
        self.data_table.value = formatted_df

        # Update the table view with column-filtered data
        self.data_table.value = display_df

        # Clear selection when filters change
        self.data_table.selection = []
        self.selected_cell_ids = []
        self.selected_data = None
        self.selection_indicator.object = "**0** cells selected"

        print(f"Table updated with {len(display_df)} rows after filtering")

    def create_selection_buttons(self):
        """Create the select all and clear selection buttons"""
        self.select_all_button = pn.widgets.Button(
            name="Select All",
            button_type="primary",
            width=120,
            icon="check-square",
            styles={"margin-right": "10px"}
        )

        self.clear_selection_button = pn.widgets.Button(
            name="Clear Selection",
            button_type="default",
            width=120,
            icon="square",
            styles={"margin-right": "10px"}
        )

        # Add event handlers
        self.select_all_button.on_click(self.select_all_cells)
        self.clear_selection_button.on_click(self.clear_selection)

        return pn.Row(
            self.select_all_button,
            self.clear_selection_button,
            align="center",
            styles={"margin-bottom": "10px"}
        )

    def select_all_cells(self, event):
        """Select all cells in the current filtered dataset"""
        if self.data_table.value is not None and not self.data_table.value.empty:
            # Get all indices
            all_indices = list(range(len(self.data_table.value)))
            self.data_table.selection = all_indices
            # The on_cell_selection handler will take care of updating selected_cell_ids

    def clear_selection(self, event):
        """Clear the current selection"""
        self.data_table.selection = []
        # The on_cell_selection handler will take care of updating selected_cell_ids

    def update_load_button_state(self):
        """Update the load button state based on selection"""
        if self.selected_cell_ids:
            self.load_button.disabled = False
            count = len(self.selected_cell_ids)
            button_text = f"Load Cycle Data ({count})"

            # Add a warning for large selections
            if count > 20:
                button_text += " ⚠️"
                self.load_button.tooltip = f"Loading {count} cells may take some time"
            else:
                self.load_button.tooltip = ""

            self.load_button.name = button_text
        else:
            self.load_button.disabled = True
            self.load_button.name = "Load Cycle Data"
            self.load_button.tooltip = "Select cells first"

    def update_selection_statistics(self):
        """Update the statistics card with information about selected cells"""
        if not self.selected_cell_ids or self.selected_data is None or self.selected_data.is_empty():
            self.stats_content.clear()
            self.stats_content.append(
                pn.pane.Markdown("### Select cells to view statistics", styles={"color": "#666"})
            )
            return

        self.stats_content.clear()

        # Get basic counts
        num_cells = len(self.selected_cell_ids)

        # Create basic statistics
        stats_md = f"### {num_cells} Cells Selected\n\n"

        # Calculate statistical summaries for key numeric columns
        key_metrics = ["actual_nominal_capacity_ah", "last_discharge_capacity",
                       "discharge_capacity_retention", "total_cycles"]

        summary_stats = []

        for metric in key_metrics:
            if metric in self.selected_data.columns:
                # Calculate statistics
                try:
                    metric_data = self.selected_data.select(pl.col(metric))
                    if not metric_data.is_empty():
                        mean_val = metric_data.mean().item()
                        min_val = metric_data.min().item()
                        max_val = metric_data.max().item()
                        std_val = metric_data.std().item()

                        # Format the metric name for display
                        display_name = metric.replace("_", " ").title()

                        # Add to summary stats
                        summary_stats.append(f"**{display_name}**")
                        summary_stats.append(f"- Mean: {mean_val:.2f}")
                        summary_stats.append(f"- Min: {min_val:.2f}")
                        summary_stats.append(f"- Max: {max_val:.2f}")
                        summary_stats.append(f"- Std Dev: {std_val:.2f}")
                        summary_stats.append("")
                except Exception as e:
                    print(f"Error calculating stats for {metric}: {str(e)}")

        if summary_stats:
            stats_md += "\n".join(summary_stats)
        else:
            stats_md += "No numeric data available for statistics."

        self.stats_content.append(pn.pane.Markdown(stats_md))

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

        # Update statistics and button state
        self.update_selection_statistics()
        self.update_load_button_state()

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

    def create_statistics_card(self):
        """Create a card to display summary statistics for selected cells"""
        # Create placeholder for stats content
        self.stats_content = pn.Column(
            pn.pane.Markdown("### Select cells to view statistics", styles={"color": "#666"})
        )

        # Create the card
        stats_card = pn.Card(
            self.stats_content,
            title="Selection Statistics",
            collapsed=False,
            collapsible=True,
            header_background="#3b82f6",
            header_color="white",
            margin=(0, 0, 10, 0),
            styles={"box-shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"}
        )

        return stats_card

    def create_modern_search_bar(self):
        """Create a modern search bar with icon"""
        search_container = pn.Row(
            pn.pane.HTML("""
                <div class="search-container">
                    <div class="search-input" style="flex: 1;">
                    </div>
                </div>
            """, height=0, margin=0),
            self.search_input,
            self.search_button,
            self.clear_search_button,
            css_classes=["search-container"],
            margin=(0, 0, 16, 0)
        )

        # Add custom CSS class to search input
        self.search_input.css_classes = ["search-input"]

        return search_container

    def create_modern_filters_sidebar(self):
        """Create modern sidebar with filters"""
        # Filter sections
        filter_sections = []

        # Quick search section
        quick_search = pn.Column(
            pn.pane.HTML('<div class="sidebar-title">🔍 Quick Search</div>'),
            pn.widgets.TextInput(
                placeholder="Quick search cells...",
                css_classes=["search-input"],
                width=250
            ),
            css_classes=["sidebar-section"]
        )

        # Filters section
        filters_content = []
        for name, widget in self.filter_widgets.items():
            widget.width = 250
            filters_content.append(widget)

        filters_section = pn.Column(
            pn.pane.HTML('<div class="sidebar-title">⚙️ Filters</div>'),
            *filters_content,
            css_classes=["sidebar-section"]
        )

        # Display settings section
        display_section = pn.Column(
            pn.pane.HTML('<div class="sidebar-title">👁️ Display Settings</div>'),
            self.column_selector,
            css_classes=["sidebar-section"]
        )

        # Statistics section
        stats_section = pn.Column(
            pn.pane.HTML('<div class="sidebar-title">📊 Selection Statistics</div>'),
            self.create_modern_statistics_card(),
            css_classes=["sidebar-section"]
        )

        sidebar = pn.Column(
            quick_search,
            filters_section,
            display_section,
            stats_section,
            width=300,
            css_classes=["sidebar"],
            sizing_mode="fixed"
        )

        return sidebar

    def create_modern_statistics_card(self):
        """Create modern statistics display"""
        self.stats_container = pn.Column()

        # Default stats when no selection
        default_stats = pn.pane.HTML("""
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">0</div>
                    <div class="stat-label">Selected</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">-</div>
                    <div class="stat-label">Avg Capacity</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">-</div>
                    <div class="stat-label">Avg Retention</div>
                </div>
            </div>
        """)

        self.stats_container.append(default_stats)
        return self.stats_container

    def create_modern_selection_controls(self):
        """Create modern selection control buttons"""
        return pn.Row(
            pn.widgets.Button(
                name="Select All",
                button_type="default",
                icon="check-square",
                width=120,
                css_classes=["selection-btn"]
            ),
            pn.widgets.Button(
                name="Clear Selection",
                button_type="default",
                icon="square",
                width=120,
                css_classes=["selection-btn"]
            ),
            pn.pane.HTML('<div class="selection-count">12 cells selected</div>'),
            css_classes=["selection-controls"]
        )

    def create_modern_table(self):
        """Create modern data table"""
        self.data_table = pn.widgets.Tabulator(
            pagination="remote",
            page_size=50,
            selectable="checkbox",
            header_align="left",
            layout="fit_data_table",
            show_index=False,
            height=600,
            css_classes=["modern-table"],
            configuration={
                "columnDefaults": {
                    "vertAlign": "middle",
                    "headerSort": True,
                    "resizable": True
                },
                "layout": "fitDataFill",
                "responsiveLayout": "hide",
                "placeholder": "No data available",
                "movableColumns": True,
                "selectable": True,
                "selectableRangeMode": "click"
            }
        )
        return self.data_table

    def create_modern_action_bar(self):
        """Create modern action bar with load button"""
        self.load_button.css_classes = ["load-button"]
        self.load_button.width = 200

        action_bar = pn.Row(
            self.load_button,
            pn.Spacer(),
            pn.pane.HTML('<div class="selection-count">Ready to load cycle data</div>'),
            margin=(16, 0, 0, 0),
            align="center"
        )

        return action_bar

    def update_modern_statistics(self):
        """Update statistics with modern styling"""
        if not self.selected_cell_ids or self.selected_data is None or self.selected_data.is_empty():
            stats_html = """
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">0</div>
                        <div class="stat-label">Selected</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Avg Capacity</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Avg Retention</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">-</div>
                        <div class="stat-label">Range</div>
                    </div>
                </div>
            """
        else:
            num_cells = len(self.selected_cell_ids)

            # Calculate statistics
            avg_capacity = "-"
            avg_retention = "-"
            capacity_range = "-"

            if "actual_nominal_capacity_ah" in self.selected_data.columns:
                avg_capacity = f"{self.selected_data['actual_nominal_capacity_ah'].mean():.2f} Ah"
                min_cap = self.selected_data['actual_nominal_capacity_ah'].min()
                max_cap = self.selected_data['actual_nominal_capacity_ah'].max()
                capacity_range = f"{min_cap:.1f} - {max_cap:.1f}"

            if "discharge_capacity_retention" in self.selected_data.columns:
                avg_retention = f"{self.selected_data['discharge_capacity_retention'].mean():.1f}%"

            stats_html = f"""
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{num_cells}</div>
                        <div class="stat-label">Selected</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{avg_capacity}</div>
                        <div class="stat-label">Avg Capacity</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{avg_retention}</div>
                        <div class="stat-label">Avg Retention</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{capacity_range}</div>
                        <div class="stat-label">Range</div>
                    </div>
                </div>
            """

        self.stats_container.clear()
        self.stats_container.append(pn.pane.HTML(stats_html))

    def create_modern_layout(self):
        """Create the modern layout matching the screenshot"""
        # Create components
        search_bar = self.create_modern_search_bar()
        selection_controls = self.create_modern_selection_controls()
        modern_table = self.create_modern_table()
        action_bar = self.create_modern_action_bar()
        sidebar = self.create_modern_filters_sidebar()

        # Main content area
        main_content = pn.Column(
            search_bar,
            selection_controls,
            modern_table,
            action_bar,
            css_classes=["main-content"],
            sizing_mode="stretch_width",
            margin=(20, 20, 20, 0)
        )

        # Full layout
        layout = pn.Row(
            sidebar,
            main_content,
            sizing_mode="stretch_both"
        )

        return layout

    def create_layout(self):
        return self.create_modern_layout()
        # # Create search components in a horizontal row
        # search_row = pn.Row(
        #     self.search_input,
        #     self.search_button,
        #     self.clear_search_button,
        #     styles={"margin-bottom": "10px"}
        # )
        # # Create selection buttons row
        # selection_buttons = self.create_selection_buttons()
        #
        # # Create the statistics card
        # stats_card = self.create_statistics_card()
        #
        # sidebar = pn.Column(
        #     pn.pane.Markdown("## Filters"),
        #     *self.filter_widgets.values(),
        #     pn.pane.Markdown("## Display Settings"),
        #     self.column_selector,
        #     stats_card,
        #     self.selection_indicator,
        #     width=300,
        #     sizing_mode="fixed",
        # )
        # # Create a row with the button and selection indicator for below the table
        # action_row = pn.Row(
        #     self.load_button,
        #     self.selection_indicator,
        #     align="center"
        # )
        #
        # # Stack the table and action row in a column with scrollbars
        # main_content = pn.Column(
        #     pn.pane.Markdown("### Cell Data", styles={"margin-bottom": "10px"}),
        #     search_row,
        #     selection_buttons,
        #     pn.Column(
        #         self.data_table,
        #         max_height=650,  # Set maximum height
        #         scroll=True,  # Enable scrolling
        #         width_policy='max',
        #         styles={'overflow-y': 'auto', 'overflow-x': 'auto'}
        #     ),
        #     action_row,
        #     sizing_mode="stretch_width"
        # )
        #
        # return pn.Row(sidebar, main_content)

