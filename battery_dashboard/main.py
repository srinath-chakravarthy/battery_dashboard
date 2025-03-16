# battery_dashboard/main.py
import panel as pn
from dotenv import load_dotenv
import param
import re
# load modules
from battery_dashboard.components.cell_selector import CellSelectorTab
from battery_dashboard.components.cycle_plots import CyclePlotsTab
from battery_dashboard.data.loaders import load_initial_data
from battery_dashboard.extensions import create_extensions

# Load environment variables
load_dotenv()

# Panel extensions
pn.extension("plotly", "tabulator", "modal", sizing_mode="stretch_width")
create_extensions()


print("Panel extensions loaded")


# Main Dashboard
class BatteryDashboard(param.Parameterized):
    theme = param.Selector(default="default", objects=["default", "dark"])
    def __init__(self, **params):
        super().__init__(**params)
        self.cell_data = load_initial_data()
        self.cell_selector_tab = CellSelectorTab(self.cell_data)
        self.cycle_plots_tab = CyclePlotsTab()

        # Create the theme toggle
        self.theme_toggle = pn.widgets.Toggle(
            name="Dark Mode",
            value=False,
            width=100,
            align="end"
        )
        self.theme_toggle.param.watch(self.theme_toggle, "value")

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

        # Create header with logo, title, and theme toggle
        header = pn.Row(
            pn.pane.Markdown(
                "# Battery Analytics Dashboard",
                styles={"color": "white", "margin-bottom": "0px"}
            ),
            self.theme_toggle,

            height=70,
            align="center",
            styles={"padding": "0 20px",
                    "background-color":"var(--header-bg)"
            }
        )

        # Create footer with version info
        footer = pn.Row(
            pn.pane.Markdown(
                "Version 1.0 | Updated: March 2025",
                styles={"color": "var(--footer-text)", "font-size": "0.85em"}
            ),
            height=30,
            align="center"
        )

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

# Initialize and run the dashboard
dashboard = BatteryDashboard()
app = dashboard.create_layout()

app.servable()