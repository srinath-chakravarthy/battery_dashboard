# battery_dashboard/main.py

import panel as pn
import param
import holoviews as hv

# Load modules
from battery_dashboard.components.cell_selector import CellSelectorTab
from battery_dashboard.components.cycle_plots import CyclePlotsTab
from battery_dashboard.data.loaders import load_initial_data
from battery_dashboard.extensions import create_extensions
from battery_dashboard.config import DEBUG, ENVIRONMENT

# Panel extensions
pn.extension("plotly", "tabulator", "modal", sizing_mode="stretch_width")
create_extensions()

print(f"Panel extensions loaded for {ENVIRONMENT} environment")


class BatteryDashboard(param.Parameterized):
    theme = param.Selector(default="default", objects=["default", "dark"])

    def __init__(self, **params):
        super().__init__(**params)

        print("Loading initial cell data...")
        self.cell_data = load_initial_data()
        print(f"Loaded {len(self.cell_data)} cells")

        # Initialize tabs
        self.cell_selector_tab = CellSelectorTab(self.cell_data)
        self.cycle_plots_tab = CyclePlotsTab()

        # Create the theme toggle
        self.theme_toggle = pn.widgets.Toggle(
            name="Dark Mode",
            value=False,
            width=100,
            align="end"
        )
        self.theme_toggle.param.watch(self.toggle_theme, "value")

        # Link tab interactions
        self.cell_selector_tab.param.watch(self.on_selection_change, ["selected_cell_ids", "selected_data"])

    def toggle_theme(self, event):
        """Toggle between light and dark themes"""
        if event.new:
            self.theme = "dark"
            # Add dark theme class to document
            pn.state.add_periodic_callback(
                lambda: pn.pane.HTML('<script>document.documentElement.setAttribute("data-theme", "dark");</script>'),
                100, count=1
            )
        else:
            self.theme = "default"
            # Remove dark theme class
            pn.state.add_periodic_callback(
                lambda: pn.pane.HTML('<script>document.documentElement.removeAttribute("data-theme");</script>'),
                100, count=1
            )

    def on_selection_change(self, event):
        """Handle selection changes from cell selector tab"""
        # Only update if both selected_cell_ids and selected_data are available
        if (hasattr(self.cell_selector_tab, "selected_cell_ids") and
                hasattr(self.cell_selector_tab, "selected_data")):
            if self.cell_selector_tab.selected_data is not None:
                print(f"Selection changed: {len(self.cell_selector_tab.selected_cell_ids)} cells selected")
                self.cycle_plots_tab.update_selection(
                    self.cell_selector_tab.selected_cell_ids,
                    self.cell_selector_tab.selected_data
                )

    def create_layout(self):
        """Create the main dashboard layout"""
        # Create tab pages
        cell_selector_page = self.cell_selector_tab.create_layout()
        cycle_plots_page = self.cycle_plots_tab.create_layout()

        # Create tabs container
        tabs = pn.Tabs(
            ("🔋 Cell Selection", cell_selector_page),
            ("📊 Cycle Analysis", cycle_plots_page),
            ("📈 Statistics", pn.pane.Markdown("## Statistics Dashboard\n*Coming Soon*")),
            ("🤖 ML Analysis", pn.pane.Markdown("## Machine Learning Analysis\n*Coming Soon*")),
            tabs_location="left" if DEBUG else "above"
        )

        # Create header with title and theme toggle
        header = pn.Row(
            pn.pane.HTML(
                """
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.5em; margin-right: 10px;">🔋</span>
                    <h1 style="margin: 0; color: white;">Battery Analytics Dashboard</h1>
                </div>
                """,
                margin=(0, 10)
            ),
            pn.Spacer(),
            self.theme_toggle,
            height=70,
            align="center",
            styles={
                "padding": "0 20px",
                "background-color": "var(--header-bg)",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
            }
        )

        # Create footer
        footer = pn.Row(
            pn.pane.Markdown(
                f"**Battery Analytics Dashboard** | Version 1.0 | Environment: {ENVIRONMENT.title()}",
                styles={"color": "var(--footer-text)", "font-size": "0.85em"}
            ),
            height=30,
            align="center",
            styles={
                "padding": "0 20px",
                "background-color": "var(--footer-bg)",
                "border-top": "1px solid var(--border-color)"
            }
        )

        # Use FastListTemplate for better layout control
        template = pn.template.FastListTemplate(
            title="Battery Analytics",
            header=header,
            main=pn.Column(tabs, footer),
            sidebar=None,
            accent_base_color="#3B82F6",
            header_background="#3B82F6",
            header_color="white",
            sidebar_width=0,
            main_max_width="100%",
            theme=self.theme
        )

        return template


def create_app():
    """Create and return the dashboard application"""
    try:
        dashboard = BatteryDashboard()
        app = dashboard.create_layout()
        print("✓ Dashboard created successfully")
        return app
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        import traceback
        traceback.print_exc()
        # Return a simple error page
        return pn.pane.Markdown(f"## Error\nFailed to load dashboard: {str(e)}")


# For Panel serve command
if __name__ == '__main__':
    app = create_app()
    app.servable()
else:
    # For imports
    try:
        dashboard = BatteryDashboard()
        app = dashboard.create_layout()
    except Exception as e:
        print(f"Warning: Dashboard initialization failed: {e}")
        app = pn.pane.Markdown("Dashboard failed to initialize")