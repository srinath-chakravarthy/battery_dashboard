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

    def create_modern_header(self):
        """Create modern dashboard header matching the screenshot"""
        # Get cell count dynamically
        cell_count = len(self.cell_data) if hasattr(self, 'cell_data') else 0

        # Status indicator with dynamic cell count
        status_badge = pn.pane.HTML(f"""
            <div style="background: rgba(255, 255, 255, 0.2); color: white; padding: 6px 12px; 
                        border-radius: 6px; font-size: 0.875rem; font-weight: 500;
                        backdrop-filter: blur(10px); display: flex; align-items: center; gap: 6px;">
                ✅ Status: {cell_count} cells loaded
            </div>
        """)

        # Dark mode toggle with modern styling
        dark_mode_toggle = pn.Row(
            pn.pane.HTML("""
                <span style="color: white; font-size: 0.875rem; margin-right: 8px;">🌙</span>
            """),
            self.theme_toggle,
            align="center"
        )

        # Main header row
        header = pn.Row(
            pn.pane.HTML("""
                <div style="display: flex; align-items: center; gap: 12px; color: white;">
                    🔋 <span style="font-size: 1.5rem; font-weight: 600;">Battery Analytics Dashboard</span>
                </div>
            """),
            pn.Spacer(),
            status_badge,
            dark_mode_toggle,
            height=70,
            align="center",
            styles={
                "padding": "0 24px",
                "background": "linear-gradient(135deg, #4F78FF 0%, #3B5EDB 100%)",
                "box-shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
                "border-bottom": "1px solid rgba(255, 255, 255, 0.1)"
            }
        )

        return header

    def create_modern_tabs(self):
        """Create modern tab navigation with icons"""
        # Create tab pages
        cell_selector_page = self.cell_selector_tab.create_layout()
        cycle_plots_page = self.cycle_plots_tab.create_layout()

        # Statistics placeholder with better styling
        stats_page = pn.Column(
            pn.pane.HTML("""
                <div style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 20px;">📊</div>
                    <h2 style="color: var(--text-primary); margin-bottom: 10px;">Statistics Dashboard</h2>
                    <p style="font-size: 1.1rem;">Advanced statistical analysis and comparisons coming soon!</p>
                    <div style="margin-top: 30px; padding: 20px; background: var(--bg-secondary); 
                                border-radius: 12px; display: inline-block;">
                        <p><strong>Planned Features:</strong></p>
                        <ul style="text-align: left; margin: 10px 0;">
                            <li>ANOVA analysis between experiment groups</li>
                            <li>Correlation matrices and scatter plots</li>
                            <li>Distribution analysis with Q-Q plots</li>
                            <li>Statistical significance testing</li>
                        </ul>
                    </div>
                </div>
            """),
            sizing_mode="stretch_both"
        )

        # ML Analysis placeholder with better styling
        ml_page = pn.Column(
            pn.pane.HTML("""
                <div style="text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                    <div style="font-size: 3rem; margin-bottom: 20px;">🤖</div>
                    <h2 style="color: var(--text-primary); margin-bottom: 10px;">Machine Learning Analysis</h2>
                    <p style="font-size: 1.1rem;">Predictive modeling and advanced analytics coming soon!</p>
                    <div style="margin-top: 30px; padding: 20px; background: var(--bg-secondary); 
                                border-radius: 12px; display: inline-block;">
                        <p><strong>Planned Features:</strong></p>
                        <ul style="text-align: left; margin: 10px 0;">
                            <li>Capacity degradation prediction models</li>
                            <li>Anomaly detection for battery performance</li>
                            <li>Feature importance analysis</li>
                            <li>End-of-life forecasting</li>
                        </ul>
                    </div>
                </div>
            """),
            sizing_mode="stretch_both"
        )

        # Create tabs with icons and modern styling
        tabs = pn.Tabs(
            ("📊 Cell Selection", cell_selector_page),
            ("📈 Cycle Analysis", cycle_plots_page),
            ("📋 Statistics", stats_page),
            ("🤖 ML Analysis", ml_page),
            tabs_location="above",
            dynamic=True
        )

        return tabs

    def create_modern_footer(self):
        """Create modern footer with environment info"""
        footer = pn.Row(
            pn.pane.HTML(f"""
                <div style="display: flex; align-items: center; gap: 20px; color: var(--footer-text); 
                            font-size: 0.85em;">
                    <span><strong>Battery Analytics Dashboard</strong> v1.0</span>
                    <span>•</span>
                    <span>Environment: {ENVIRONMENT.title()}</span>
                    <span>•</span>
                    <span>Updated: March 2025</span>
                </div>
            """),
            height=40,
            align="center",
            styles={
                "padding": "0 24px",
                "background-color": "var(--footer-bg)",
                "border-top": "1px solid var(--border-light)"
            }
        )
        return footer

    def create_layout(self):
        """Create the complete modern dashboard layout"""
        # Create modern components
        header = self.create_modern_header()
        tabs = self.create_modern_tabs()
        footer = self.create_modern_footer()

        # Use FastListTemplate for better layout control
        template = pn.template.FastListTemplate(
            title="Battery Analytics",
            header=header,
            main=pn.Column(tabs, footer, sizing_mode="stretch_both"),
            sidebar=None,
            accent_base_color="#4F78FF",
            header_background="#4F78FF",
            header_color="white",
            sidebar_width=0,
            main_max_width="100%",
            theme=self.theme,
            theme_toggle=False  # We handle our own theme toggle
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
        # Return a simple error page with modern styling
        error_page = pn.Column(
            pn.pane.HTML(f"""
                <div style="text-align: center; padding: 60px 20px;">
                    <div style="font-size: 3rem; color: #EF4444; margin-bottom: 20px;">❌</div>
                    <h2 style="color: #1F2937; margin-bottom: 10px;">Dashboard Error</h2>
                    <p style="color: #6B7280; font-size: 1.1rem;">Failed to load dashboard</p>
                    <div style="margin-top: 20px; padding: 16px; background: #FEF2F2; 
                                border: 1px solid #FECACA; border-radius: 8px; display: inline-block;">
                        <code style="color: #DC2626;">{str(e)}</code>
                    </div>
                </div>
            """),
            sizing_mode="stretch_both"
        )
        return error_page


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
        # Create a simple fallback app
        app = pn.pane.HTML("""
            <div style="text-align: center; padding: 40px;">
                <h2>Dashboard Loading...</h2>
                <p>Please refresh the page if this message persists.</p>
            </div>
        """)