import panel as pn
import pandas as pd
import numpy as np
import holoviews as hv
from holoviews.operation.datashader import datashade, dynspread
import param
from pathlib import Path
import tempfile
import os
import logging
import traceback
from typing import List, Dict, Any, Optional

# Initialize Panel and HoloViews
pn.extension(comms='vscode')
hv.extension('bokeh')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BatteryAnalyzerUI")

# Import the battery analytics library components
try:
    from src.battery_cycle_analytics.battery_cycle_analyzer import BatteryCycleAnalyzer
    from src.battery_cycle_analytics.cycle_analysis.cycling_metrics import CyclingMetricsProcessor
    from src.battery_cycle_analytics.phase_detection.phase_detection_factory import PhaseDetectorFactory
    from src.battery_cycle_analytics.cycle_analysis.cycle_detection import CycleDetector

    BATTERY_ANALYTICS_AVAILABLE = True
except ImportError:
    logger.warning("Battery cycle analytics library not available. Using mock implementation.")
    BATTERY_ANALYTICS_AVAILABLE = False

# Define formation patterns for cycle detection
FORMATION_PATTERNS = [
    {
        'name': 'Formation Solstice 1',
        'cycle_range': (1, 5),
        'steps': [
            {'charge_c_rate': 0.1, 'discharge_c_rate': 0.1},
            {'charge_c_rate': 0.1, 'discharge_c_rate': 0.33},
            {'charge_c_rate': 0.1, 'discharge_c_rate': 1.0},
            {'charge_c_rate': 0.1, 'discharge_c_rate': 0.1}
        ]
    },
    {
        'name': 'Formation Solstice 2',
        'cycle_range': (1, 8),
        'steps': [
            {'charge_c_rate': 0.1, 'discharge_c_rate': 0.1},
            {'charge_c_rate': 0.1, 'discharge_c_rate': 0.1},
            {'charge_c_rate': 0.1, 'discharge_c_rate': 0.33},
            {'charge_c_rate': 0.1, 'discharge_c_rate': 1.0},
            {'charge_c_rate': 0.1, 'discharge_c_rate': 0.1}
        ]
    }
]


# Mock BatteryCycleAnalyzer for UI development if the actual module isn't available
class MockBatteryCycleAnalyzer:
    def __init__(self, filepaths, cycler_type="neware_notebook", nominal_capacity=1.0, formation_patterns=None):
        self.filepaths = filepaths
        self.cycler_type = cycler_type
        self.nominal_capacity = nominal_capacity
        self.formation_patterns = formation_patterns or FORMATION_PATTERNS

    def analyze(self):
        # Mock data generation
        logger.info(f"Analyzing files: {self.filepaths}")
        # Generate some mock data
        times = np.linspace(0, 10000, 10000)
        current = np.concatenate([
            np.ones(2000) * 1.0,  # Charge phase
            np.zeros(1000),  # Rest phase
            np.ones(2000) * -1.0,  # Discharge phase
            np.zeros(1000),  # Rest phase
            np.ones(2000) * 1.0,  # Charge phase
            np.zeros(1000),  # Rest phase
            np.ones(2000) * -1.0  # Discharge phase
        ])
        voltage = 3.5 + 0.5 * np.sin(times / 2000)
        capacity = np.cumsum(current) / 3600

        # Create a dataframe
        data = pd.DataFrame({
            'elapsed_time': times,
            'current': current,
            'voltage': voltage,
            'capacity': capacity,
            'cycle_number': np.floor(times / 3000) + 1,  # Assign cycle numbers
            'phase_type': np.nan,
            'phase_category': np.nan,
            'index': np.arange(len(times))
        })

        # Assign phase types and categories
        phases = [
            {'start_index': 0, 'end_index': 1999, 'phase_type': 'CC_Charge', 'phase_category': 'Charge'},
            {'start_index': 2000, 'end_index': 2999, 'phase_type': 'Rest', 'phase_category': 'Rest'},
            {'start_index': 3000, 'end_index': 4999, 'phase_type': 'CC_Discharge', 'phase_category': 'Discharge'},
            {'start_index': 5000, 'end_index': 5999, 'phase_type': 'Rest', 'phase_category': 'Rest'},
            {'start_index': 6000, 'end_index': 7999, 'phase_type': 'CC_Charge', 'phase_category': 'Charge'},
            {'start_index': 8000, 'end_index': 8999, 'phase_type': 'Rest', 'phase_category': 'Rest'},
            {'start_index': 9000, 'end_index': 9999, 'phase_type': 'CC_Discharge', 'phase_category': 'Discharge'}
        ]

        # Apply phases to data
        for phase in phases:
            start, end = phase['start_index'], phase['end_index']
            data.loc[start:end, 'phase_type'] = phase['phase_type']
            data.loc[start:end, 'phase_category'] = phase['phase_category']

        # Generate cycle metrics
        cycle_metrics = pd.DataFrame({
            'cycle_number': [1, 2, 3],
            'cycle_type': ['regular', 'regular', 'regular'],
            'charge_capacity_change': [1.0, 0.98, 0.95],
            'discharge_capacity_change': [0.95, 0.93, 0.91],
            'coulombic_efficiency': [95.0, 94.8, 95.2],
            'charge_duration': [2000, 2000, 2000],
            'discharge_duration': [2000, 2000, 2000],
            'energy_efficiency': [90.0, 89.8, 89.5],
            'cycle_start_index': [0, 3000, 6000],
            'cycle_end_index': [2999, 5999, 9999]
        })

        # Generate phase metrics
        phase_metrics = pd.DataFrame([
            {
                'phase_type': phase['phase_type'],
                'phase_category': phase['phase_category'],
                'start_index': phase['start_index'],
                'end_index': phase['end_index'],
                'cycle_number': int(np.floor(phase['start_index'] / 3000) + 1),
                'duration': phase['end_index'] - phase['start_index'] + 1,
                'capacity_change': np.abs(capacity[phase['end_index']] - capacity[phase['start_index']]),
                'energy_change': np.abs(np.sum(current[phase['start_index']:phase['end_index'] + 1] *
                                               voltage[phase['start_index']:phase['end_index'] + 1]) / 3600)
            }
            for phase in phases
        ])

        test_metrics = pd.DataFrame({
            'total_cycles': [3],
            'total_regular_drive_cycles': [3],
            'average_coulombic_efficiency': [95.0],
            'average_energy_efficiency': [90.0],
            'discharge_capacity_sum_regular_drive': [sum(cycle_metrics['discharge_capacity_change'])],
            'discharge_energy_sum_regular_drive': [sum(cycle_metrics['discharge_capacity_change']) * 3.6],
            'last_charge_capacity': [cycle_metrics['charge_capacity_change'].iloc[-1]],
            'last_discharge_capacity': [cycle_metrics['discharge_capacity_change'].iloc[-1]],
            'capacity_retention_discharge': [cycle_metrics['discharge_capacity_change'].iloc[-1] /
                                             cycle_metrics['discharge_capacity_change'].iloc[0]]
        })

        return {
            'raw_data': data,
            'detected_phases': phases,
            'categorized_data': data,
            'metrics': {
                'cycle_metrics': cycle_metrics,
                'phase_metrics': phase_metrics,
                'test_metrics': test_metrics
            }
        }


class BatteryCycleAnalyzerApp(param.Parameterized):
    def __init__(self, **params):
        super().__init__(**params)
        # State variables
        self.uploaded_files = []
        self.temp_dir = None
        self.nominal_capacity = 1.0  # Default value in Ah
        self.cycler_type = "neware_notebook"  # Default cycler type
        self.analyzer = None
        self.analysis_results = None

        # Set up UI components
        self.setup_ui()

    def setup_ui(self):
        # File upload component
        self.file_upload = pn.widgets.FileInput(accept='.csv, .xlsx', multiple=True)
        self.file_upload.param.watch(self.handle_file_upload, 'value')

        # Nominal capacity input
        self.nominal_capacity_widget = pn.widgets.FloatInput(
            name='Nominal Capacity (Ah)',
            value=self.nominal_capacity,
            step=0.1,
            start=0.1
        )
        self.nominal_capacity_widget.param.watch(self.update_nominal_capacity, 'value')

        # Cycler type selection
        self.cycler_type_widget = pn.widgets.Select(
            name='Cycler Type',
            options=['neware_notebook', 'maccor', 'mb_cycling'],
            value=self.cycler_type
        )
        self.cycler_type_widget.param.watch(self.update_cycler_type, 'value')

        # Analysis button
        self.analyze_button = pn.widgets.Button(name='Run Analysis', button_type='primary', disabled=True)
        self.analyze_button.on_click(self.run_analysis)

        # Export button
        self.export_button = pn.widgets.Button(name='Export Results', button_type='success', disabled=True)
        self.export_button.on_click(self.export_results)

        # Status message
        self.status = pn.pane.Markdown("Upload files to begin analysis.")

        # Visualization containers
        self.plot_container = pn.Column(pn.pane.Markdown("## Visualization will appear here after analysis"))

        # Metrics tabs
        self.cycle_metrics_table = pn.pane.DataFrame(pd.DataFrame(), width=800)
        self.phase_metrics_table = pn.pane.DataFrame(pd.DataFrame(), width=800)
        self.test_metrics_table = pn.pane.DataFrame(pd.DataFrame(), width=800)

        self.metrics_tabs = pn.Tabs(
            ('Cycle Metrics', self.cycle_metrics_table),
            ('Phase Metrics', self.phase_metrics_table),
            ('Test Metrics', self.test_metrics_table)
        )

        # Cycle modification tools
        self.cycle_mod_container = pn.Column(
            pn.pane.Markdown("## Cycle Modification Tools"),
            pn.Row(
                pn.widgets.Button(name='Split Cycle', disabled=True),
                pn.widgets.Button(name='Merge Cycles', disabled=True),
                pn.widgets.Button(name='Reset Selection', disabled=True)
            ),
            visible=False
        )

        # Build sidebar
        self.sidebar = pn.Column(
            pn.pane.Markdown("## Battery Cycle Analyzer"),
            pn.pane.Markdown("### Data Input"),
            pn.Row(self.file_upload),
            pn.Row(self.nominal_capacity_widget),
            pn.Row(self.cycler_type_widget),
            pn.Row(self.analyze_button),
            pn.Row(self.export_button),
            self.status,
            width=300
        )

        # Main layout
        self.main = pn.Column(
            pn.pane.Markdown("# Battery Cycling Data Analysis"),
            pn.Row(
                self.plot_container,
                width=800,
                height=500
            ),
            self.cycle_mod_container,
            pn.Row(
                pn.pane.Markdown("## Analysis Results"),
                width=800
            ),
            pn.Row(
                self.metrics_tabs,
                width=800
            )
        )

        # Create the full app layout
        self.layout = pn.Row(self.sidebar, self.main)

    def handle_file_upload(self, event):
        """Process uploaded files"""
        logger.info(f"File upload event: {event}")
        if event.new:
            # Clean up previous temp directory if it exists
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    for file in os.listdir(self.temp_dir):
                        os.remove(os.path.join(self.temp_dir, file))
                    os.rmdir(self.temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")

            # Create new temporary directory
            self.temp_dir = tempfile.mkdtemp()
            filepaths = []

            # Process uploaded files - handle multiple files properly
            for i, file_content in enumerate(event.new):
                # Get filename from the widget if available, otherwise use index
                if hasattr(event.obj, 'filename') and len(event.obj.filename) > i:
                    filename = event.obj.filename[i]
                else:
                    filename = f"uploaded_file_{i}.csv"

                temp_path = os.path.join(self.temp_dir, filename)
                with open(temp_path, 'wb') as f:
                    f.write(file_content)  # Now writing a single bytes object, not a list
                filepaths.append(temp_path)

            self.uploaded_files = [Path(path) for path in filepaths]
            self.status.object = f"Uploaded file. Ready for analysis."
            self.analyze_button.disabled = False

    def update_nominal_capacity(self, event):
        """Update nominal capacity value"""
        self.nominal_capacity = event.new
        logger.info(f"Nominal capacity set to {self.nominal_capacity} Ah")

    def update_cycler_type(self, event):
        """Update cycler type"""
        self.cycler_type = event.new
        logger.info(f"Cycler type set to {self.cycler_type}")

    def run_analysis(self, event):
        """Run the analysis using BatteryCycleAnalyzer"""
        if not self.uploaded_files:
            self.status.object = "Please upload files first."
            return

        self.status.object = "Running analysis..."

        try:
            # Use actual or mock BatteryCycleAnalyzer depending on availability
            if BATTERY_ANALYTICS_AVAILABLE:
                logger.info("Using actual BatteryCycleAnalyzer")
                self.analyzer = BatteryCycleAnalyzer(
                    filepaths=self.uploaded_files,
                    cycler_type=self.cycler_type,
                    nominal_capacity=self.nominal_capacity,
                    formation_patterns=FORMATION_PATTERNS
                )
            else:
                logger.info("Using mock BatteryCycleAnalyzer")
                self.analyzer = MockBatteryCycleAnalyzer(
                    filepaths=self.uploaded_files,
                    cycler_type=self.cycler_type,
                    nominal_capacity=self.nominal_capacity,
                    formation_patterns=FORMATION_PATTERNS
                )

            self.analysis_results = self.analyzer.analyze()
            self.update_visualization()
            self.update_metrics_tables()

            self.status.object = "Analysis completed successfully."
            self.export_button.disabled = False
            self.cycle_mod_container.visible = True
        except Exception as e:
            logger.exception("Error during analysis")
            self.status.object = f"Error during analysis: {str(e)}\n{traceback.format_exc()}"

    def update_visualization(self):
        """Update the visualization with analysis results"""
        if self.analysis_results is None:
            return

        data = self.analysis_results['raw_data']
        phases = self.analysis_results.get('detected_phases', [])

        # Create HoloViews dataset
        dataset = hv.Dataset(data)

        # Create phase color map
        phase_colors = {
            'CC_Charge': 'blue',
            'CV_Charge': 'lightblue',
            'CC_Discharge': 'red',
            'Dynamic_Discharge': 'orange',
            'Rest': 'green',
            'DCIR_Pulse': 'purple'
        }

        # Create current, voltage, and capacity curves
        current_curve = hv.Curve(dataset, 'elapsed_time', 'current', label='Current (A)')
        voltage_curve = hv.Curve(dataset, 'elapsed_time', 'voltage', label='Voltage (V)')
        capacity_curve = hv.Curve(dataset, 'elapsed_time', 'capacity', label='Capacity (Ah)')

        # Apply datashader for large datasets
        current_ds = dynspread(datashade(current_curve, cmap='blue', alpha=0.7))
        voltage_ds = dynspread(datashade(voltage_curve, cmap='red', alpha=0.7))
        capacity_ds = dynspread(datashade(capacity_curve, cmap='green', alpha=0.7))

        # Create phase highlight areas
        phase_areas = []
        for phase in phases:
            start_idx = phase['start_index']
            end_idx = phase['end_index']

            if start_idx >= len(data) or end_idx >= len(data):
                continue

            start_time = data.iloc[start_idx]['elapsed_time']
            end_time = data.iloc[end_idx]['elapsed_time']

            # Get color for this phase type
            phase_type = phase['phase_type']
            color = phase_colors.get(phase_type, 'gray')

            # Create a semi-transparent area highlighting this phase
            phase_area = hv.Area((start_time, end_time), 0, 1, label=phase_type).opts(
                fill_alpha=0.2, fill_color=color, line_color=None
            )

            phase_areas.append(phase_area)

        # Combine phase areas if any
        if phase_areas:
            phases_overlay = hv.Overlay(phase_areas)
        else:
            phases_overlay = hv.Empty()

        # Combine with primary curves
        time_voltage_plot = voltage_ds * phases_overlay
        time_current_plot = current_ds * phases_overlay
        time_capacity_plot = capacity_ds * phases_overlay

        # Create a combined view with all data
        combined_plot = current_ds * voltage_ds * capacity_ds * phases_overlay

        # Create a layout with tabs
        plot_tabs = pn.Tabs(
            ('Combined', combined_plot),
            ('Current', time_current_plot),
            ('Voltage', time_voltage_plot),
            ('Capacity', time_capacity_plot)
        )

        self.plot_container.clear()
        self.plot_container.append(pn.pane.Markdown("## Battery Cycling Data Visualization"))
        self.plot_container.append(plot_tabs)

    def update_metrics_tables(self):
        """Update all metrics tables with analysis results"""
        if self.analysis_results is None:
            return

        metrics = self.analysis_results['metrics']

        # Update cycle metrics table
        if 'cycle_metrics' in metrics:
            self.cycle_metrics_table.object = metrics['cycle_metrics']

        # Update phase metrics table
        if 'phase_metrics' in metrics:
            self.phase_metrics_table.object = metrics['phase_metrics']

        # Update test metrics table
        if 'test_metrics' in metrics:
            self.test_metrics_table.object = metrics['test_metrics']

    def export_results(self, event):
        """Export analysis results to CSV files"""
        if self.analysis_results is None:
            self.status.object = "No analysis results to export."
            return

        try:
            # Create an export directory
            export_dir = os.path.join(self.temp_dir, "exports") if self.temp_dir else "./exports"
            os.makedirs(export_dir, exist_ok=True)

            # Export cycle metrics
            if 'cycle_metrics' in self.analysis_results['metrics']:
                cycle_path = os.path.join(export_dir, "cycle_metrics.csv")
                self.analysis_results['metrics']['cycle_metrics'].to_csv(cycle_path, index=False)

            # Export phase metrics
            if 'phase_metrics' in self.analysis_results['metrics']:
                phase_path = os.path.join(export_dir, "phase_metrics.csv")
                self.analysis_results['metrics']['phase_metrics'].to_csv(phase_path, index=False)

            # Export test metrics
            if 'test_metrics' in self.analysis_results['metrics']:
                test_path = os.path.join(export_dir, "test_metrics.csv")
                self.analysis_results['metrics']['test_metrics'].to_csv(test_path, index=False)

            self.status.object = f"Results exported to {export_dir}"
        except Exception as e:
            logger.exception("Export error")
            self.status.object = f"Error exporting results: {str(e)}"

    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                for file in os.listdir(self.temp_dir):
                    os.remove(os.path.join(self.temp_dir, file))
                os.rmdir(self.temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")


class MiniTest(param.Parameterized):
    def __init__(self, **params):
        super().__init__(**params)
        self.file_upload = pn.widgets.FileInput(accept='.csv,.xlsx', multiple=False)
        self.file_upload.param.watch(self._on_upload, 'value')

    def _on_upload(self, event):
        print(f"Triggered upload event! New value size: {len(event.new) if event.new else 0} bytes")



# Create and serve the app
app = BatteryCycleAnalyzerApp()
# app.layout.servable()
# app = MiniTest()
if __name__ == '__main__':
    app.layout.show(port=8562)
    # app.cleanup()