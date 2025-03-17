# battery_dashboard/components/cycle_plots.py
import panel as pn
import polars as pl
import param
import holoviews as hv
import hvplot.polars
from bokeh.palettes import Category10, Category20
from bokeh.models import HoverTool, CrosshairTool, Span, Band
from ..data.loaders import get_cycle_data
import pandas as pd

# Configure HoloViews to use Bokeh
hv.extension('bokeh')


class CyclePlotsTab(param.Parameterized):
    """Enhanced cycle plots tab with HvPlot and Bokeh backend."""

    # Parameters for reactive updates
    selected_cell_ids = param.List(default=[], doc="Selected cell IDs")
    selected_cell_metadata = param.Parameter(default=None, doc="Full data for selected rows")
    current_plot = param.Parameter(default=None, doc="Current plot object")

    # Active tab selection for analysis types
    active_tab = param.Selector(default="basic", objects=["basic", "analysis", "model"],
                                doc="Currently active analysis tab")

    # Analysis method selection
    analysis_method = param.Selector(
        default="capacity_retention",
        objects=["capacity_retention", "coulombic_efficiency", "knee_point", "differential_capacity"],
        doc="Analysis method to apply to the data"
    )

    # Plot configuration parameters
    plot_type = param.Selector(
        default="line",
        objects=["line", "scatter", "area", "step", "bar"],
        doc="Type of plot to display"
    )

    x_axis = param.Selector(
        default="regular_cycle_number",
        objects=["regular_cycle_number"],
        doc="X-axis column"
    )

    y_axis = param.Selector(
        default="discharge_capacity",
        objects=["discharge_capacity"],
        doc="Y-axis column"
    )

    y_axis_secondary = param.Selector(
        default=None,
        objects=[None],
        doc="Secondary Y-axis column"
    )

    group_by = param.Selector(
        default="cell_id",
        objects=["cell_id"],
        doc="Column to group data by"
    )

    color_theme = param.Selector(
        default="default",
        objects=["default", "Category10", "Category20", "viridis", "plasma", "inferno", "magma", "cividis"],
        doc="Color theme for plot"
    )

    # Chart sizing
    plot_height = param.Integer(default=600, bounds=(300, 1200), doc="Plot height in pixels")
    plot_width = param.Integer(default=800, bounds=(400, 2000), doc="Plot width in pixels")

    # Advanced options
    use_datashader = param.Boolean(default=True, doc="Use datashader for rendering large datasets")
    show_grid = param.Boolean(default=True, doc="Show grid lines")
    show_legend = param.Boolean(default=True, doc="Show legend")
    legend_position = param.Selector(
        default="right",
        objects=["right", "left", "top", "bottom", "top_left", "top_right", "bottom_left", "bottom_right"],
        doc="Legend position"
    )

    def __init__(self, **params):
        super().__init__(**params)
        self.cycle_data = None
        self.groups = []
        self.group_colors = {}

        # Create UI elements for the plot controls
        self.create_plot_controls()
        print("After creation:")
        print("Advanced button exists:", hasattr(self, 'advanced_settings_button'))
        print("Series button exists:", hasattr(self, 'series_settings_button'))

        # Plot container
        self.plot_container = pn.Column(
            pn.pane.Markdown("No cells selected. Please select cells in the Cell Selector tab.")
        )

        # Analysis results container
        self.analysis_container = pn.Column(
            pn.pane.Markdown("Select an analysis method and click 'Run Analysis'")
        )

        # Create the modal cards for advanced settings
        self.create_settings_cards()

        # Print button info after settings cards
        print("After settings cards:")
        print("Advanced button exists:", hasattr(self, 'advanced_settings_button'))
        print("Series button exists:", hasattr(self, 'series_settings_button'))
        # Set up event handlers
        self.setup_event_handlers()
        # Print button info after handlers
        print("After handlers:")
        print("Advanced button exists:", hasattr(self, 'advanced_settings_button'))
        print("Series button exists:", hasattr(self, 'series_settings_button'))



    # Method to update groups and colors
    def update_groups_and_colors(self):
        # Only compute groups if they're not already set or grouping column changed
        needs_group_update = (
                not self.groups or
                self._last_group_by != self.group_by or
                self._last_data_id != id(self.cycle_data)
        )

        if needs_group_update and not self.cycle_data.is_empty():
            # Store the current grouping for future comparison
            self._last_group_by = self.group_by
            self._last_data_id = id(self.cycle_data)

            # Get unique groups
            self.groups = self.cycle_data[self.group_by].unique().to_list()

            # Reset color mapping
            self.group_colors = {}

        # Update colors if needed
        if self.groups and (needs_group_update or self._last_color_theme != self.color_theme):
            self._last_color_theme = self.color_theme

            # Get color palette
            if self.color_theme == 'Category10':
                cmap = Category10[10]
            elif self.color_theme == 'Category20':
                cmap = Category20[20]
            else:
                cmap = self.color_theme if self.color_theme != 'default' else Category10[10]

            # Assign colors to groups
            for i, group in enumerate(self.groups):
                group_str = str(group)
                # Only set color if it isn't already customized via series settings
                if group_str not in self.group_colors:
                    if isinstance(cmap, list):
                        self.group_colors[group_str] = cmap[i % len(cmap)]
                    else:
                        # Default fallback
                        self.group_colors[group_str] = Category10[10][i % 10]

    def create_plot_controls(self):
        """Create the UI elements for plot controls"""
        # Basic controls (will always be visible in sidebar)
        self.axis_settings_pane = pn.Column(
            pn.pane.Markdown("## Plot Settings", styles={"margin-bottom": "5px"}),
            pn.widgets.Select.from_param(self.param.x_axis, name="X-Axis", width=200),
            pn.widgets.Select.from_param(self.param.y_axis, name="Y-Axis", width=200),
            pn.widgets.Select.from_param(self.param.y_axis_secondary, name="Secondary Y-Axis", width=200),
            pn.widgets.Select.from_param(self.param.plot_type, name="Plot Type", width=200),
            pn.pane.Markdown("## Grouping", styles={"margin-bottom": "5px"}),
            pn.widgets.Select.from_param(self.param.group_by, name="Group By", width=200),
            width=250
        )

        # Advanced settings buttons
        self.advanced_settings_button = pn.widgets.Button(
            name="Advanced Plot Settings",
            button_type="primary",
            width=200,
            icon="gear"
        )

        self.series_settings_button = pn.widgets.Button(
            name="Series Settings",
            button_type="primary",
            width=200,
            icon="palette"
        )

        # Export/Download buttons
        self.export_png_button = pn.widgets.Button(
            name="Export as PNG",
            button_type="success",
            width=150,
            icon="download"
        )

        self.export_svg_button = pn.widgets.Button(
            name="Export as SVG",
            button_type="success",
            width=150,
            icon="download"
        )

        # Action buttons container
        self.action_buttons = pn.Column(
            pn.pane.Markdown("## Actions", styles={"margin-bottom": "5px"}),
            pn.Row(self.advanced_settings_button, margin=(0, 0, 5, 0)),
            pn.Row(self.series_settings_button, margin=(0, 0, 5, 0)),
            pn.pane.Markdown("## Export", styles={"margin-bottom": "5px"}),
            pn.Row(self.export_png_button, self.export_svg_button),
            width=250
        )

    def setup_event_handlers(self):
        """Set up event handlers for the UI elements"""
        # Watch parameters for updating the plot
        self.param.watch(self.update_plot, ["plot_type", "x_axis", "y_axis",
                                            "y_axis_secondary", "group_by",
                                            "color_theme", "show_grid",
                                            "show_legend", "legend_position",
                                            "plot_height", "plot_width",
                                            "use_datashader"])

        print("Advanced button:", id(self.advanced_settings_button))
        print("Series button:", id(self.series_settings_button))
        print("Advanced button in _callbacks:", hasattr(self.advanced_settings_button, '_callbacks'))
        print("Series button in _callbacks:", hasattr(self.series_settings_button, '_callbacks'))

        # Button click handlers
        self.advanced_settings_button.on_click(self.open_advanced_settings)

        self.series_settings_button.on_click(self.open_series_settings)

        self.export_png_button.on_click(self.export_png)
        self.export_svg_button.on_click(self.export_svg)


    def create_settings_cards(self):
        """Create the modal cards for advanced settings"""
        # Advanced settings card
        self.advanced_settings_widgets = {
            'plot_title': pn.widgets.TextInput(name="Plot Title", placeholder="Enter plot title", width=250),
            'x_axis_label': pn.widgets.TextInput(name="X-Axis Label", width=250),
            'y_axis_label': pn.widgets.TextInput(name="Y-Axis Label", width=250),
            'y_axis_secondary_label': pn.widgets.TextInput(name="Secondary Y-Axis Label", width=250),
            'x_axis_type': pn.widgets.Select(name="X-Axis Type", options=["linear", "log"], value="linear", width=200),
            'y_axis_type': pn.widgets.Select(name="Y-Axis Type", options=["linear", "log"], value="linear", width=200),
            'y_axis_secondary_type': pn.widgets.Select(name="Secondary Y-Axis Type", options=["linear", "log"],
                                                       value="linear", width=200),
            'x_axis_min': pn.widgets.NumberInput(name="X-Axis Min", value=None, step=0.5,width=120),
            'x_axis_max': pn.widgets.NumberInput(name="X-Axis Max", value=None, step=0.5,width=120),
            'y_axis_min': pn.widgets.NumberInput(name="Y-Axis Min", value=None, step=0.1,width=120),
            'y_axis_max': pn.widgets.NumberInput(name="Y-Axis Max", value=None, step=0.1,width=120),
            'y_axis_secondary_min': pn.widgets.NumberInput(name="Secondary Y-Axis Min", step=0.1,value=None, width=120),
            'y_axis_secondary_max': pn.widgets.NumberInput(name="Secondary Y-Axis Max", step=0.1,value=None, width=120),
            'show_grid': pn.widgets.Checkbox.from_param(self.param.show_grid),
            'grid_color': pn.widgets.ColorPicker(name="Grid Color", value="#e0e0e0", width=100),
            'background_color': pn.widgets.ColorPicker(name="Background Color", value="#ffffff", width=100),
            'show_legend': pn.widgets.Checkbox.from_param(self.param.show_legend),
            'legend_position': pn.widgets.Select.from_param(self.param.legend_position, width=200),
            'plot_height': pn.widgets.IntSlider.from_param(self.param.plot_height, width=200),
            'plot_width': pn.widgets.IntSlider.from_param(self.param.plot_width, width=200),
            'use_datashader': pn.widgets.Checkbox.from_param(self.param.use_datashader),
            'tools': pn.widgets.MultiChoice(
                name="Interactive Tools",
                options=["pan", "wheel_zoom", "box_zoom", "box_select", "lasso_select", "crosshair", "hover", "reset"],
                value=["pan", "wheel_zoom", "box_zoom", "reset", "hover"],
                width=250
            )
        }

        # Organize into tabs for the advanced settings
        advanced_axes_tab = pn.Column(
            pn.Row(self.advanced_settings_widgets['x_axis_label'], self.advanced_settings_widgets['x_axis_type']),
            pn.Row(self.advanced_settings_widgets['x_axis_min'], self.advanced_settings_widgets['x_axis_max']),
            pn.Row(self.advanced_settings_widgets['y_axis_label'], self.advanced_settings_widgets['y_axis_type']),
            pn.Row(self.advanced_settings_widgets['y_axis_min'], self.advanced_settings_widgets['y_axis_max']),
            pn.Row(self.advanced_settings_widgets['y_axis_secondary_label'],
                   self.advanced_settings_widgets['y_axis_secondary_type']),
            pn.Row(self.advanced_settings_widgets['y_axis_secondary_min'],
                   self.advanced_settings_widgets['y_axis_secondary_max'])
        )

        advanced_appearance_tab = pn.Column(
            pn.Row(self.advanced_settings_widgets['plot_title']),
            pn.Row(self.advanced_settings_widgets['show_grid'], self.advanced_settings_widgets['grid_color']),
            pn.Row(pn.pane.Markdown("Background:"), self.advanced_settings_widgets['background_color']),
            pn.Row(self.advanced_settings_widgets['show_legend'], self.advanced_settings_widgets['legend_position']),
            pn.Row(self.advanced_settings_widgets['plot_height'], self.advanced_settings_widgets['plot_width'])
        )

        advanced_interaction_tab = pn.Column(
            pn.Row(self.advanced_settings_widgets['use_datashader']),
            pn.Row(self.advanced_settings_widgets['tools'])
        )

        # Apply and cancel buttons
        self.advanced_apply_button = pn.widgets.Button(name="Apply", button_type="success", width=100)
        self.advanced_cancel_button = pn.widgets.Button(name="Cancel", button_type="danger", width=100)
        self.advanced_apply_button.on_click(self.apply_advanced_settings)
        self.advanced_cancel_button.on_click(self.close_advanced_settings)

        # Create tabs for advanced settings
        advanced_settings_tabs = pn.Tabs(
            ('Axes', advanced_axes_tab),
            ('Appearance', advanced_appearance_tab),
            ('Interaction', advanced_interaction_tab)
        )

        # Create the modal
        self.advanced_settings_card = pn.Card(
            pn.Column(
                advanced_settings_tabs,
                pn.Row(self.advanced_apply_button, self.advanced_cancel_button, align='end')
            ),
            title="Advanced Plot Settings",
            collapsed=True,
            collapsible=True,
            header_background="#3498db",
            header_color="white"
        )

        # Series settings card will be created dynamically when opened
        self.series_settings_card = pn.Card(
            pn.pane.Markdown("Series settings will appear here..."),
            title="Series Settings",
            collapsed=True,
            collapsible=True,
            header_background="#3498db",
            header_color="white"
        )

        # Store original series settings
        self.series_settings = {}

    def update_selection(self, cell_ids, cell_data):
        """Update the selected cell IDs and data."""
        self.selected_cell_ids = cell_ids
        self.selected_cell_metadata = cell_data

        if not cell_ids:
            self.cycle_data = None
            self.plot_container.clear()
            self.plot_container.append(pn.pane.Markdown(
                "No cells selected. Please select cells in the Cell Selector tab.",
                styles={"color": "#666", "font-style": "italic"}
            ))
            return

        # Show loading indicator
        self.plot_container.clear()
        self.plot_container.append(pn.indicators.Progress(active=True, value=50, width=400))
        self.plot_container.append(pn.pane.Markdown("Loading cycle data...", styles={"color": "#333"}))

        # Fetch cycle data
        self.cycle_data = get_cycle_data(cell_ids)
        # print(self.cycle_data.shape)
        # print(self.cycle_data.head())

        if self.cycle_data is None or self.cycle_data.is_empty():
            self.plot_container.clear()
            self.plot_container.append(pn.pane.Markdown(
                "No cycle data available for the selected cells.",
                styles={"color": "red", "font-weight": "bold"}
            ))
            return

        # Merge with cell metadata if available
        if self.selected_cell_metadata is not None and not self.selected_cell_metadata.is_empty():
            # Identify which columns already exist in cycle_data to avoid duplicates
            existing_cols = set(self.cycle_data.columns)
            metadata_cols = [col for col in self.selected_cell_metadata.columns if col != 'cell_id']

            # Select only columns from metadata that don't already exist in cycle_data
            unique_metadata_cols = [col for col in metadata_cols if col not in existing_cols]

            # If there are unique columns to merge, perform the join
            if unique_metadata_cols:
                cols_to_select = ['cell_id'] + unique_metadata_cols
                self.cycle_data = self.cycle_data.join(
                    self.selected_cell_metadata.select(cols_to_select),
                    on='cell_id',
                    how='left'
                )

        # Add specific capacity metrics if active mass is available
        if 'total_active_mass_g' in self.cycle_data.columns:
            # Find capacity and energy columns
            capacity_cols = [col for col in self.cycle_data.columns
                             if 'capacity' in col.lower() and not '_specific_mAh_g' in col]
            energy_cols = [col for col in self.cycle_data.columns
                           if 'energy' in col.lower() and not '_specific_Wh_g' in col]

            # Create specific capacity and energy expressions
            specific_exprs = []

            # Add expressions for capacity columns (convert to mAh/g)
            for col in capacity_cols:
                specific_exprs.append(
                    (
                        pl.when(pl.col('total_active_mass_g') > 0)
                        .then(1000 * pl.col(col) / pl.col('total_active_mass_g'))
                        .otherwise(None)
                    ).alias(f"{col}_specific_mAh_g")
                )

            # Add expressions for energy columns (convert to Wh/g)
            for col in energy_cols:
                specific_exprs.append(
                    (
                        pl.when(pl.col('total_active_mass_g') > 0)
                        .then(pl.col(col) / pl.col('total_active_mass_g'))
                        .otherwise(None)
                    ).alias(f"{col}_specific_Wh_g")
                )

            # Apply the expressions to add the new columns
            if specific_exprs:
                self.cycle_data = self.cycle_data.with_columns(specific_exprs)

        # Update available columns for dropdown selectors
        self.update_column_options()

        # Generate the initial plot
        self.update_plot()

    def update_column_options(self):
        """Update the available column options for dropdown selectors"""
        if self.cycle_data is None or self.cycle_data.is_empty():
            return

        # Get all numeric columns for axes
        numeric_cols = [col for col in self.cycle_data.columns
                        if self.cycle_data[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]]

        # Get categorical columns for grouping
        categorical_cols = [
            col for col in self.cycle_data.columns
            if (col not in ['cell_id', 'cell_name'] and
                self.cycle_data[col].dtype in [pl.Utf8, pl.String]) or
               col in ['cell_id', 'cell_name']
        ]

        # Ensure 'cell_id' and 'cell_name' are always first in group options
        if 'cell_id' in self.cycle_data.columns and 'cell_id' not in categorical_cols:
            categorical_cols = ['cell_id'] + categorical_cols
        if 'cell_name' in self.cycle_data.columns and 'cell_name' not in categorical_cols:
            categorical_cols = ['cell_name'] + categorical_cols

        # Update options for selectors
        self.param.x_axis.objects = sorted(numeric_cols)
        self.param.y_axis.objects = sorted(numeric_cols)

        # For secondary y-axis, add None option
        secondary_options = [None] + sorted(numeric_cols)
        self.param.y_axis_secondary.objects = secondary_options

        # Update grouping options
        self.param.group_by.objects = sorted(categorical_cols)

        # Try to keep current selections if possible
        if self.x_axis not in numeric_cols:
            self.x_axis = 'regular_cycle_number' if 'regular_cycle_number' in numeric_cols else numeric_cols[0]

        if self.y_axis not in numeric_cols:
            capacity_cols = [col for col in numeric_cols if 'discharge_capacity' in col]
            self.y_axis = capacity_cols[0] if capacity_cols else numeric_cols[0]

        if self.group_by not in categorical_cols:
            self.group_by = 'cell_id' if 'cell_id' in categorical_cols else categorical_cols[0]

    def create_hover_tool(self, tooltips=None):
        """Create a custom hover tool with the given tooltips"""
        if tooltips is None:
            # Default tooltips
            tooltips = [
                ('Group', '@{' + self.group_by + '}'),
                ('Cycle', '@{' + self.x_axis + '}{0}'),
                (self.y_axis, '@{' + self.y_axis + '}{0.00}')
            ]

            # Add secondary y-axis if it exists
            if self.y_axis_secondary is not None:
                tooltips.append((self.y_axis_secondary, '@{' + self.y_axis_secondary + '}{0.00}'))

        return HoverTool(tooltips=tooltips)


    def update_plot(self, event=None):
        """Update the plot based on current settings"""
        self.plot_container.clear()

        if self.cycle_data is None or self.cycle_data.is_empty():
            self.plot_container.append(pn.pane.Markdown(
                "No cycle data available. Please select cells in the Cell Selector tab.",
                styles={"color": "#666", "font-style": "italic"}
            ))
            return

        # Get color palette based on theme
        if self.color_theme == 'Category10':
            cmap = Category10[10]
        elif self.color_theme == 'Category20':
            cmap = Category20[20]
        else:
            cmap = self.color_theme if self.color_theme != 'default' else None

        # Update groups and colors first
        self.update_groups_and_colors()
        # Get advanced settings
        adv = self.advanced_settings_widgets

        # Create base plot kwargs
        plot_kwargs = {
            'x': self.x_axis,
            'y': self.y_axis,
            'by': self.group_by,
            'kind': self.plot_type,
            'height': self.plot_height,
            'width': self.plot_width,
            'cmap': cmap,
            'grid': self.show_grid,
            'legend': self.show_legend,
            'logx': adv['x_axis_type'].value == 'log',
            'logy': adv['y_axis_type'].value == 'log'
        }

        # Set axis labels
        plot_kwargs['xlabel'] = adv['x_axis_label'].value or self.x_axis.replace('_', ' ').title()
        plot_kwargs['ylabel'] = adv['y_axis_label'].value or self.y_axis.replace('_', ' ').title()

        # Set title if provided
        if adv['plot_title'].value:
            plot_kwargs['title'] = adv['plot_title'].value

        # Only set limits if user has explicitly set them
        if adv['x_axis_min'].value is not None and adv['x_axis_max'].value is not None:
            plot_kwargs['xlim'] = (adv['x_axis_min'].value, adv['x_axis_max'].value)

        if adv['y_axis_min'].value is not None and adv['y_axis_max'].value is not None:
            plot_kwargs['ylim'] = (adv['y_axis_min'].value, adv['y_axis_max'].value)

        # if adv['y_axis_secondary_min'].value is not None and adv['y_axis_secondary_max'].value is not None:
        #     plot_kwargs['ylim_secondary'] = (adv['y_axis_secondary_min'].value, adv['y_axis_secondary_max'].value)


        # Add tools
        plot_kwargs['tools'] = adv['tools'].value

        # Use datashader for large datasets if enabled
        if self.use_datashader and len(self.selected_cell_ids) > 100:
            plot_kwargs['datashade'] = True
            plot_kwargs['rasterize'] = True
        # Inside update_plot before creating the plot

        # print(plot_kwargs)
        # Generate the plot
        try:
            main_plot_overlay = self.cycle_data.hvplot(**plot_kwargs)
            main_plot = hv.Overlay(main_plot_overlay.values())
            secondary_plot = None
            # Add secondary y-axis if selected
            if self.y_axis_secondary is not None and self.y_axis_secondary != 'None':
                renderer = hv.renderer('bokeh')
                main_plot_state = renderer.get_plot(main_plot).state

                # Extract colors from the first plot's renderers
                series_colors = [
                    renderer.glyph.line_color if hasattr(renderer.glyph, 'line_color') else
                    renderer.glyph.fill_color for renderer in main_plot_state.renderers
                ]
                print(series_colors)
                # Create secondary axis plot
                secondary_kwargs = plot_kwargs.copy()
                secondary_kwargs['y'] = self.y_axis_secondary

                if adv['y_axis_secondary_label'].value:
                    secondary_kwargs['ylabel'] = adv['y_axis_secondary_label'].value
                else:
                    secondary_kwargs['ylabel'] = self.y_axis_secondary.replace('_', ' ').title()

                # Set secondary axis limits if provided
                if adv['y_axis_secondary_min'].value is not None and adv['y_axis_secondary_max'].value is not None:
                    secondary_kwargs['ylim'] = (
                        adv['y_axis_secondary_min'].value,
                        adv['y_axis_secondary_max'].value
                    )
                secondary_kwargs['yaxis'] = 'right'
                secondary_kwargs['legend'] = False
                secondary_kwargs['color'] = series_colors
                print(self.group_colors)

                print(secondary_kwargs)
                secondary_plot_overlay = self.cycle_data.hvplot(**secondary_kwargs)
                secondary_plot = hv.Overlay(secondary_plot_overlay.values())
            if not secondary_plot is None:
                print(main_plot)
                print(secondary_plot)
                overlay = hv.Overlay([main_plot, secondary_plot]).opts(multi_y=True, show_legend = True)
                print(overlay)
            else:
                overlay = main_plot_overlay
            self.current_plot = overlay

            # Render the plot
            self.plot_container.append(overlay)

        except Exception as e:
            self.plot_container.append(pn.pane.Markdown(
                f"**Error creating plot:** {str(e)}",
                styles={"color": "red"}
            ))
            print(f"Plot error: {str(e)}")
            import traceback
            traceback.print_exc()

    def open_advanced_settings(self, event):
        """Open the advanced settings modal"""
        self.advanced_settings_card.collapsed = False

        # Pre-populate values from current settings
        adv = self.advanced_settings_widgets

        # Update current labels as placeholders
        adv['x_axis_label'].placeholder = self.x_axis.replace('_', ' ').title()
        adv['y_axis_label'].placeholder = self.y_axis.replace('_', ' ').title()

        if self.y_axis_secondary:
            adv['y_axis_secondary_label'].placeholder = self.y_axis_secondary.replace('_', ' ').title()
            adv['y_axis_secondary_label'].disabled = False
            adv['y_axis_secondary_type'].disabled = False
            adv['y_axis_secondary_min'].disabled = False
            adv['y_axis_secondary_max'].disabled = False
        else:
            adv['y_axis_secondary_label'].disabled = True
            adv['y_axis_secondary_type'].disabled = True
            adv['y_axis_secondary_min'].disabled = True
            adv['y_axis_secondary_max'].disabled = True

    def close_advanced_settings(self, event):
        """Close the advanced settings modal without applying changes"""
        self.advanced_settings_card.collapsed = True

    def apply_advanced_settings(self, event):
        """Apply the advanced settings and update the plot"""
        self.update_plot()
        self.advanced_settings_card.collapsed = True

    def open_series_settings(self, event):
        """Open the series settings modal with a tabulator table"""
        self.series_settings_card.collapsed = False
        print("Opening series settings...")
        if self.cycle_data is None or self.cycle_data.is_empty():
            return

        # We can use the existing self.groups directly
        # No need to call update_groups_and_colors() here
        self.update_groups_and_colors()

        # Create a dictionary to hold the settings data
        settings_data = {
            "group": [],
            "visible": [],
            "color": [],
            "line_width": [],
            "line_style": [],
            "marker_size": [],
            "marker_shape": [],
            "opacity": [],
            "y_axis": []  # Primary/Secondary
        }

        # Populate the settings data
        for group in self.groups:
            group_str = str(group)

            # Create settings for this series if it doesn't exist
            if group_str not in self.series_settings:
                self.series_settings[group_str] = {
                    'visible': True,
                    'color': self.group_colors.get(group_str, None),  # Get color from existing group_colors
                    'line_width': 2,
                    'line_style': "solid",
                    'marker_size': 6,
                    'marker_shape': "circle",
                    'opacity': 0.8,
                    'y_axis': 'Primary'
                }

            # Add this group's settings to the data dictionary
            settings = self.series_settings[group_str]
            settings_data["group"].append(group_str)
            settings_data["visible"].append(settings['visible'])
            settings_data["color"].append(settings['color'])
            settings_data["line_width"].append(settings['line_width'])
            settings_data["line_style"].append(settings['line_style'])
            settings_data["marker_size"].append(settings['marker_size'])
            settings_data["marker_shape"].append(settings['marker_shape'])
            settings_data["opacity"].append(settings['opacity'])
            settings_data["y_axis"].append(settings['y_axis'])

        # Create the table as before...
            # Convert to Polars DataFrame
        settings_df = pd.DataFrame(settings_data)
        print(settings_df)

        # Define the tabulator widget with editors for each column
        settings_table = pn.widgets.Tabulator(
            settings_df,  # Convert to pandas for Tabulator
            height=400,
            layout="fit_data_fill",
            editors={
                "visible": {"type": "tickCross"},
                "color": {"type": "color"},
                "line_width": {"type": "number", "min": 1, "max": 10, "step": 1},
                "line_style": {"type": "list", "values": ["solid", "dashed", "dotted", "dotdash"]},
                "marker_size": {"type": "number", "min": 1, "max": 20, "step": 1},
                "marker_shape": {"type": "list",
                                 "values": ["circle", "square", "triangle", "diamond", "cross", "x", "star"]},
                "opacity": {"type": "number", "min": 0.1, "max": 1.0, "step": 0.1},
                "y_axis": {"type": "list", "values": ["Primary", "Secondary"]}
            },
            formatters={
                "visible": {"type": "tickCross"},
                "color": {"type": "color"}
            },
            widths={
                "group": 150,
                "visible": 80,
                "color": 80,
                "line_width": 100,
                "line_style": 120,
                "marker_size": 100,
                "marker_shape": 120,
                "opacity": 100,
                "y_axis": 100
            },
            titles={
                "group": "Series",
                "visible": "Visible",
                "color": "Color",
                "line_width": "Line Width",
                "line_style": "Line Style",
                "marker_size": "Marker Size",
                "marker_shape": "Marker",
                "opacity": "Opacity",
                "y_axis": "Y-Axis"
            },
            configuration={"columnDefaults": {"editable": True}, "columns": [{"field": "group", "editable": False}]},
            show_index=False
        )

        # Add apply and cancel buttons
        self.series_apply_button = pn.widgets.Button(name="Apply Changes", button_type="success", width=150)
        self.series_cancel_button = pn.widgets.Button(name="Cancel", button_type="danger", width=100)

        self.series_apply_button.on_click(self.apply_series_settings)
        self.series_cancel_button.on_click(self.close_series_settings)

        # Add reset button
        self.reset_series_button = pn.widgets.Button(name="Reset to Default", button_type="default", width=150)
        self.reset_series_button.on_click(self.reset_series_settings)

        # Store the table for later access
        self.series_settings_table = settings_table

        # Build the series settings card content
        self.series_settings_card.objects = [
            pn.Column(
                pn.pane.Markdown("## Series Appearance Settings", styles={"text-align": "center"}),
                settings_table,
                pn.Row(
                    self.series_apply_button,
                    self.reset_series_button,
                    self.series_cancel_button,
                    align='end'
                )
            )
        ]

        # Show the series settings card
        self.series_settings_card.collapsed = False

    def reset_series_settings(self, event):
        """Reset series settings to default values"""
        if not hasattr(self, 'series_settings_table'):
            return

        # Clear stored settings
        self.series_settings = {}

        # Reopen the settings dialog to regenerate defaults
        self.open_series_settings(None)

    def close_series_settings(self, event):
        """Close the series settings modal without applying changes"""
        self.series_settings_card.collapsed = True

    def apply_series_settings(self, event):
        """Apply the series settings and update the plot"""
        if not hasattr(self, 'series_settings_table'):
            return

        # Get the current table data
        table_data = self.series_settings_table.value

        # Update the series settings dictionary from the table
        for _, row in table_data.iterrows():
            group_str = str(row['group'])
            self.series_settings[group_str] = {
                'visible': row['visible'],
                'color': row['color'],
                'line_width': row['line_width'],
                'line_style': row['line_style'],
                'marker_size': row['marker_size'],
                'marker_shape': row['marker_shape'],
                'opacity': row['opacity'],
                'y_axis': row['y_axis']
            }

            # Also update the group_colors dictionary for consistency
            if row['visible'] and row['color']:
                self.group_colors[group_str] = row['color']

        # Update the plot with new settings
        self.update_plot()
        self.close_series_settings(None)

    def export_png(self, event):
        """Export the current plot as PNG"""
        if self.current_plot is None:
            return

        try:
            # Create a temporary Bokeh renderer to export the plot
            renderer = hv.renderer('bokeh')

            # Get the Bokeh figure
            bokeh_plot = renderer.get_plot(self.current_plot).state

            # Set up JavaScript callback to trigger download
            export_js = """
            function exportPlot() {
                const canvas = document.createElement('canvas');
                const plot = Bokeh.documents[0].get_model_by_id('${id}');
                const width = plot.inner_width;
                const height = plot.inner_height;

                canvas.width = width;
                canvas.height = height;

                plot.export_png({canvas: canvas}).then(function() {
                    const a = document.createElement('a');
                    a.href = canvas.toDataURL('image/png');
                    a.download = 'battery_cycles_plot.png';
                    a.click();
                });
            }
            exportPlot();
            """

            # Replace the placeholder with the actual model ID
            export_js = export_js.replace('${id}', bokeh_plot.id)

            # Execute the JavaScript to download the PNG
            pn.extension()
            pn.state.execute(export_js)

            # Show a success message
            self.plot_container.append(
                pn.pane.Alert("Plot exported as PNG", alert_type="success", margin=(10, 0, 0, 0))
            )

        except Exception as e:
            # Show an error message
            self.plot_container.append(
                pn.pane.Alert(f"Error exporting PNG: {str(e)}", alert_type="danger", margin=(10, 0, 0, 0))
            )

    def export_svg(self, event):
        """Export the current plot as SVG"""
        if self.current_plot is None:
            return

        try:
            # Create a temporary Bokeh renderer to export the plot
            renderer = hv.renderer('bokeh')

            # Get the Bokeh figure
            bokeh_plot = renderer.get_plot(self.current_plot).state

            # Set up JavaScript callback to trigger download
            export_js = """
            function exportPlot() {
                const plot = Bokeh.documents[0].get_model_by_id('${id}');

                plot.export_svg().then(function(svg) {
                    const a = document.createElement('a');
                    const blob = new Blob([svg], {type: 'image/svg+xml'});
                    a.href = URL.createObjectURL(blob);
                    a.download = 'battery_cycles_plot.svg';
                    a.click();
                });
            }
            exportPlot();
            """

            # Replace the placeholder with the actual model ID
            export_js = export_js.replace('${id}', bokeh_plot.id)

            # Execute the JavaScript to download the SVG
            pn.extension()
            pn.state.execute(export_js)

            # Show a success message
            self.plot_container.append(
                pn.pane.Alert("Plot exported as SVG", alert_type="success", margin=(10, 0, 0, 0))
            )

        except Exception as e:
            # Show an error message
            self.plot_container.append(
                pn.pane.Alert(f"Error exporting SVG: {str(e)}", alert_type="danger", margin=(10, 0, 0, 0))
            )

    def create_layout(self):
        """Create the layout for the cycle plots tab"""
        # Main layout with sidebar and content
        sidebar = pn.Column(
            self.axis_settings_pane,
            pn.layout.Divider(),
            self.action_buttons,
            width=250,
            sizing_mode="fixed",
            styles={'background': '#f8f9fa', 'border-right': '1px solid #ddd', 'padding': '10px'}
        )

        # Create main content area
        main_content = pn.Column(
            pn.pane.Markdown("# Cycle Analysis", styles={"margin-bottom": "10px"}),
            self.plot_container,
            sizing_mode="stretch_width",
            width_policy="max",
            min_width=300
        )

        settings_column = pn.Column(
            self.advanced_settings_card,
            self.series_settings_card,
            width=600,
            sizing_mode="fixed",
            styles = {'padding': '10px', 'border-left': '1px solid #ddd'}
        )

        # Combine sidebar and main content
        layout = pn.Row(
            sidebar,
            main_content,
            settings_column,
            sizing_mode="stretch_both"
        )

        return layout