# battery_dashboard/main.py
import panel as pn
from dotenv import load_dotenv
import param
import re
# load modules
from battery_dashboard.components.cell_selector import CellSelectorTab
from battery_dashboard.components.cycle_plots import CyclePlotsTab
from battery_dashboard.data.loaders import load_initial_data

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


# Main Dashboard
class BatteryDashboard(param.Parameterized):
    theme = param.Selector(default="light", objects=["light", "dark"])
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
        self.theme_toggle.param.watch(self.toggle_theme, "value")

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