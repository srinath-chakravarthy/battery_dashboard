import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Battery Cell Analytics Dashboard",
    page_icon="🔋",
    layout="wide"
)

# Redash API configuration
REDASH_URL = os.getenv("REDASH_URL", "http://192.168.80.30:8080")
REDASH_API_KEY = os.getenv("REDASH_API_KEY", "FJBeHB2jfkXiNIClff27R2rdoO6W4UuGflX8EfJ4")
CELL_QUERY_ID = os.getenv("CELL_QUERY_ID", "24")  # ID of the cell data query in Redash
CYCLE_QUERY_ID = os.getenv("CYCLE_QUERY_ID", "28")  # ID for cycle data query - update this!

# Function to fetch data from Redash with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_redash_query_results(query_id, params=None):
    """
    Fetch results from a Redash query using the API

    Args:
        query_id: ID of the Redash query
        params: Optional dictionary of parameters for the query

    Returns:
        DataFrame containing the query results
    """
    try:

        # Print out connection details for debugging
        # st.write(f"Redash URL: {REDASH_URL}")
        # st.write(f"Query ID: {query_id}")
        # st.write(f"API Key: {REDASH_API_KEY[:5]}...{REDASH_API_KEY[-5:]}")  # Partial key for security
        # Construct the API URL for getting query results
        api_url = f"{REDASH_URL}/api/queries/{query_id}/results"

        # Prepare headers and parameters
        headers = {
            "Authorization": f"Key {REDASH_API_KEY}",
            "Content-Type": "application/json"
        }

        params_payload = {"parameters": params or {}}

        # # Detailed logging of the request
        # st.write("Sending request with:")
        # st.write(f"URL: {api_url}")
        # st.write(f"Headers: {headers}")
        # st.write(f"Payload: {params_payload}")

        # Make the API request
        response = requests.post(api_url, headers=headers, json=params_payload)
        # # Log the full response details
        # st.write(f"Response Status Code: {response.status_code}")
        # st.write(f"Response Headers: {response.headers}")

        # response.raise_for_status()  # Raise exception for 4XX/5XX responses

        # Parse the response
        query_result = {}
        try:
            query_result = response.json()
            # st.write(f"Response content preview: {str(query_result)[:500]}...")
        except Exception as e:
            st.write(f"Response content preview: {str(query_result)[:500]}...")
            st.write(f"Error parsing response content: {str(e)}")

        if "query_result" in query_result and "data" in query_result["query_result"]:
            data = query_result["query_result"]["data"]
            df = pd.DataFrame(data["rows"])
            return df
        else:
            st.error("Unexpected response format from Redash API")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from Redash: {e}")
        return pd.DataFrame()


# Function to get cell data with optional filtering
def get_cell_data(filters=None):
    """
    Get cell data from Redash with optional filtering

    Args:
        filters: Dictionary of filter parameters to pass to the Redash query

    Returns:
        DataFrame with cell data
    """
    return get_redash_query_results(CELL_QUERY_ID, filters)


import datetime


def get_redash_last_update_time(query_id):
    """Fetch the last execution timestamp of a Redash query."""
    try:
        query_url = f"{REDASH_URL}/api/queries/{query_id}"
        headers = {"Authorization": f"Key {REDASH_API_KEY}"}

        response = requests.get(query_url, headers=headers)
        response.raise_for_status()

        query_data = response.json()
        if "retrieved_at" in query_data:
            last_update_time = datetime.datetime.fromisoformat(query_data["retrieved_at"].replace("Z", "+00:00"))
            return last_update_time
        else:
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch Redash update time: {e}")
        return None


def cell_metadata_tab():
    """Content for the Cell Metadata tab"""
    st.markdown("### Cell Selection and Analysis")

    if st.session_state.get('active_tab') == "Cell Metadata":
        # Add sidebar for filters
        st.sidebar.header("Filters")
        # Add a refresh button
        if st.button("Refresh Data"):
            st.cache_data.clear()
        st.rerun()
    # Initialize page number in session state if not already done
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1

    # Initially load data without filters to get unique values for filter options
    with st.spinner("Loading initial data..."):
        initial_data = get_cell_data()

    # Fetch and display the last update time
    last_update = get_redash_last_update_time(CELL_QUERY_ID)

    if last_update:
        st.sidebar.markdown(f"**🔄 Last Updated:** {last_update.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        st.sidebar.warning("Unable to fetch last update time.")

    if initial_data.empty:
        st.error("No data available. Please check your Redash connection and query configuration.")
        return initial_data, []

    # ✅ **Apply hardcoded filter: Only keep regular cycles > 20**
    if "regular_cycles" in initial_data.columns:
        initial_data = initial_data[initial_data["regular_cycles"] > 20]

    # Create filter widgets in the sidebar
    filters = {}

    # Cell type filter
    if 'design_name' in initial_data.columns:
        cell_design_types = [''] + sorted(initial_data['design_name'].dropna().unique().tolist())
        filters['design_name'] = st.sidebar.selectbox("Cell Design Name", cell_design_types)

    # Experiment group filter
    if 'experiment_group' in initial_data.columns:
        experiment_groups = [''] + sorted(initial_data['experiment_group'].dropna().unique().tolist())
        filters['experiment_group'] = st.sidebar.selectbox("Experiment Group", experiment_groups)

    # Layer type filter
    if 'layer_types' in initial_data.columns:
        layer_types = [''] + sorted(initial_data['layer_types'].dropna().unique().tolist())
        filters['layer_types'] = st.sidebar.selectbox("Layer Type", layer_types)

    # Test status filter
    if 'test_status' in initial_data.columns:
        test_statuses = [''] + sorted(initial_data['test_status'].dropna().unique().tolist())
        filters['test_status'] = st.sidebar.selectbox("Test Status", test_statuses)

    # Year filter
    if 'test_year' in initial_data.columns:
        years = [''] + sorted(initial_data['test_year'].dropna().unique().astype(int).astype(str).tolist())
        filters['test_year'] = st.sidebar.selectbox("Test Year", years)

    # Remove empty filters
    filters = {k: v for k, v in filters.items() if v != ''}

    # Apply filters and reload data if needed
    if filters:
        with st.spinner("Applying filters..."):
            data = initial_data[initial_data[list(filters.keys())].isin(filters.values()).all(axis=1)]
    else:
        data = initial_data

    # Pagination settings
    items_per_page = 100
    page_number = st.session_state.page_number
    total_pages = (len(data) + items_per_page - 1) // items_per_page

    # Ensure page number is valid
    if page_number > total_pages and total_pages > 0:
        page_number = total_pages
        st.session_state.page_number = page_number

    start_idx = (page_number - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(data))

    # Display data summary
    st.markdown(f"### Showing {len(data)} cells")

    # Main content area - cell table
    col1, col2 = st.columns([2, 1])

    # Initialize selected_cell_ids as an empty list
    selected_cell_ids = []

    with col1:
        # Display table with selection capability
        if not data.empty:
            # Allow users to select which columns to display
            default_columns = [
                'cell_name', 'design_name', 'design_capacity_mah',
                'actual_nominal_capacity_ah', 'regular_cycles', 'formation_cycles',
                'discharge_capacity_retention', 'average_coulombic_efficiency', 'last_discharge_capacity'
            ]

            # Only include columns that exist in the data
            display_columns = [col for col in default_columns if col in data.columns]

            # Allow manual selection of columns
            with st.expander("Customize displayed columns"):
                all_columns = data.columns.tolist()
                selected_columns = st.multiselect(
                    "Select columns to display",
                    all_columns,
                    default=display_columns
                )

            if selected_columns:
                # Get the current page of data
                paginated_data = data.iloc[start_idx:end_idx].copy()

                # Initialize with selection column
                if '_selected' not in paginated_data.columns:
                    paginated_data['_selected'] = False

                # Add "Select All" button for filtered data
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Select All on Current Page"):
                        paginated_data['_selected'] = True
                with col2:
                    if st.button("Clear All Selections"):
                        paginated_data['_selected'] = False
                        st.session_state['selected_cell_ids'] = []
                        st.rerun()

                # This creates a dataframe with select boxes
                edited_df = st.data_editor(
                    paginated_data[['_selected'] + selected_columns],
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "_selected": st.column_config.CheckboxColumn(
                            "Select",
                            help="Select cells for analysis",
                            default=False
                        )
                    },
                    disabled=False
                )

                # Get selected cell IDs
                selected_rows = edited_df[edited_df['_selected']]
                if not selected_rows.empty:
                    # Map indices to original data indices
                    selected_indices = selected_rows.index.tolist()
                    # Adjust indices to account for pagination
                    selected_original_indices = [idx + start_idx for idx in selected_indices]
                    # Get the cell_ids from the original data
                    selected_cell_ids = data.iloc[selected_original_indices]['cell_id'].tolist()

                # Display pagination controls and info
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    if page_number > 1:
                        if st.button("◀ Previous"):
                            st.session_state.page_number = page_number - 1
                            st.rerun()
                with col3:
                    if page_number < total_pages:
                        if st.button("Next ▶"):
                            st.session_state.page_number = page_number + 1
                            st.rerun()
                with col2:
                    st.markdown(
                        f"Page {page_number} of {total_pages} • Showing rows {start_idx + 1}-{end_idx} of {len(data)}")
            else:
                st.warning("Please select at least one column to display")
        else:
            st.info("No data available with the current filter settings.")

    with col2:
        # Summary statistics
        st.markdown("### Summary Statistics")

        if not initial_data.empty:
            # Count by cell type
            if 'design_name' in initial_data.columns:
                cell_type_counts = initial_data['design_name'].value_counts().reset_index()
                cell_type_counts.columns = ['Cell Design', 'Count']

                # Create a bar chart
                st.subheader("Cell Designs")
                fig = px.bar(
                    cell_type_counts,
                    x='Cell Design',
                    y='Count',
                    color='Cell Design'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Show capacity retention distribution if available
            if 'discharge_capacity_retention' in data.columns:
                # Filter out null values
                retention_data = data['discharge_capacity_retention'].dropna()

                if not retention_data.empty:
                    st.subheader("Capacity Retention Distribution")
                    fig = px.histogram(
                        retention_data,
                        nbins=20,
                        labels={'value': 'Capacity Retention'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # Display info about selected cells
        st.markdown("### Selected Cells")
        st.markdown(f"**{len(selected_cell_ids)}** cells selected for analysis")

        # If cells are selected, show a summary
        if selected_cell_ids:
            selected_info = data[data['cell_id'].isin(selected_cell_ids)]
            if 'design_name' in selected_info.columns:
                design_counts = selected_info['design_name'].value_counts()
                st.markdown("**Selected cell designs:**")
                for design, count in design_counts.items():
                    st.markdown(f"- {design}: {count} cells")

    # Store selected cell IDs in session state to share with other tabs
    st.session_state['selected_cell_ids'] = selected_cell_ids
    # Store the filtered data in session state for reference in other tabs
    st.session_state['filtered_cell_data'] = data

    # Return the filtered data and selected cell IDs
    return data, selected_cell_ids


# Function to get cycle data for specific cell IDs
def get_cycle_data(cell_ids=None):
    """
    Get cycle data for specific cell IDs from the materialized view

    Args:
        cell_ids: List of cell IDs to filter by

    Returns:
        DataFrame with cycle data
    """
    # Create parameters for the query
    try:
        # Prepare parameters
        params = {}
        if not cell_ids:
            return pd.DataFrame()

        all_results = []
        for cell_id in cell_ids:
            # Get data for a single cell (which we know works)
            params = {"cell_ids": str(cell_id)}
            df = get_redash_query_results(CYCLE_QUERY_ID, params)
            all_results.append(df)

        # Combine all results
        if all_results:
            return pd.concat(all_results, ignore_index=True)
        return pd.DataFrame()
        # Fetch data from Redash

    except Exception as e:
        st.error(f"Error fetching cell data: {e}")
        return pd.DataFrame()


def cycle_plotting_tab():
    """Content for the Cycle Plotting tab"""
    st.markdown("### Cycle Performance Analysis")

    # Only show sidebar content when this tab is active
    if st.session_state.get('active_tab') != 'Cycle Plotting':
        return

    # Get selected cell IDs from session state
    selected_cell_ids = st.session_state.get('selected_cell_ids', [])
    cell_data = st.session_state.get('filtered_cell_data', pd.DataFrame())

    # Show warning if no cells selected
    if not selected_cell_ids:
        st.warning("Please select cells in the Cell Metadata tab for analysis")
        return

    # User-configurable cell limit
    st.sidebar.markdown("### Analysis Settings")
    cell_limit = st.sidebar.number_input(
        "Maximum cells to analyze",
        min_value=1,
        max_value=100,
        value=10,
        help="Limit the number of cells to plot for better performance"
    )

    # Check if selected cells exceed the limit
    if len(selected_cell_ids) > cell_limit:
        st.warning(f"⚠️ You've selected {len(selected_cell_ids)} cells, but the limit is set to {cell_limit}. " +
                   f"Only the first {cell_limit} cells will be analyzed. Adjust the limit in the sidebar if needed.")
        # Limit the cells to analyze
        selected_cell_ids = selected_cell_ids[:cell_limit]

    # Show selected cells
    st.markdown(f"#### Selected Cells ({len(selected_cell_ids)})")

    # If we have cell data, show a table of selected cells
    if not cell_data.empty:
        selected_cell_data = cell_data[cell_data['cell_id'].isin(selected_cell_ids)]
        if not selected_cell_data.empty:
            st.dataframe(
                selected_cell_data[['cell_name', 'design_name', 'experiment_group']],
                hide_index=True,
                use_container_width=True
            )

    # Fetch cycle data for selected cells
    with st.spinner(f"Fetching cycle data for {len(selected_cell_ids)} cells..."):
        cycle_data = get_cycle_data(selected_cell_ids)

    if cycle_data.empty:
        st.error("No cycle data available for the selected cells")
        return
    # st.write("Available columns:", list(cycle_data.columns))
    # Display data size metrics
    row_count = len(cycle_data)
    memory_usage = cycle_data.memory_usage(deep=True).sum() / (1024 * 1024)  # MB
    st.info(f"📊 Data loaded: {row_count:,} cycles ({memory_usage:.2f} MB)")

    # Plot configuration
    st.markdown("#### Plot Configuration")

    col1, col2 = st.columns(2)

    with col1:
        # X-axis selector
        x_options = ['regular_cycle_number', 'cycle_number']
        x_axis = st.selectbox("X-Axis", x_options, index=0)

        # Plot type selector
        plot_type = st.selectbox(
            "Plot Type",
            ["Line Plot", "Scatter Plot", "Line + Scatter"],
            index=0
        )

        # Normalize capacity option
        normalize_capacity = st.checkbox("Normalize Capacity", value=False)

    with col2:
        # Y-axis selector(s) - multiselect for multiple lines
        y_options = [
            'discharge_capacity', 'charge_capacity', 'discharge_energy',
            'coulombic_efficiency', 'energy_efficiency', 'cv_capacity',
            'cv_duration', 'charge_rdv', 'discharge_rdv'
        ]
        y_axis = st.multiselect("Y-Axis", y_options, default=['discharge_capacity'])

        # Grouping selector
        if 'experiment_group' in cell_data.columns and 'design_name' in cell_data.columns:
            group_options = ['None', 'cell_name', 'design_name', 'experiment_group']
            group_by = st.selectbox("Group By", group_options, index=0)
        else:
            group_options = ['None', 'cell_name']
            group_by = st.selectbox("Group By", group_options, index=0)

        # Color scale for groups
        color_scale = st.selectbox(
            "Color Scale",
            ["viridis", "plasma", "inferno", "magma", "cividis", "turbo"],
            index=0
        )

    # Join cycle data with cell metadata
    if not cell_data.empty:
        cycle_data = cycle_data.merge(
            cell_data[['cell_id', 'cell_name', 'design_name', 'experiment_group', 'actual_nominal_capacity_ah']],
            on='cell_id',
            how='left'
        )

    # Generate plots
    st.markdown("#### Performance Plots")

    if not y_axis:
        st.warning("Please select at least one Y-axis variable to plot")
        return

    # Create a subplot for each Y-axis variable
    for y_var in y_axis:
        with st.container():
            st.markdown(f"##### {y_var}")

            # Apply normalization if selected
            if normalize_capacity and 'capacity' in y_var and 'actual_nominal_capacity_ah' in cycle_data.columns:
                # Create a copy to avoid modification warnings
                plot_data = cycle_data.copy()
                # Scale capacity by nominal capacity
                plot_data[y_var] = plot_data[y_var] / (plot_data['actual_nominal_capacity_ah'] * 1000)
                y_label = f"Normalized {y_var}"
            else:
                plot_data = cycle_data
                # Infer units
                if 'capacity' in y_var:
                    y_label = f"{y_var} (mAh)"
                elif 'energy' in y_var:
                    y_label = f"{y_var} (mWh)"
                elif 'efficiency' in y_var:
                    y_label = f"{y_var} (%)"
                elif 'duration' in y_var:
                    y_label = f"{y_var} (s)"
                else:
                    y_label = y_var

            # Set up the figure
            fig = go.Figure()

            # Group the data
            if group_by != 'None':
                groups = plot_data[group_by].unique()

                for i, group in enumerate(groups):
                    group_data = plot_data[plot_data[group_by] == group]

                    # Skip empty groups
                    if group_data.empty:
                        continue

                    # For cell-level data, we need to plot each cell separately
                    if group_by == 'cell_name':
                        # Add a line trace
                        if plot_type in ["Line Plot", "Line + Scatter"]:
                            fig.add_trace(go.Scatter(
                                x=group_data[x_axis],
                                y=group_data[y_var],
                                mode='lines',
                                name=str(group),
                                line=dict(width=2)
                            ))

                        # Add scatter points
                        if plot_type in ["Scatter Plot", "Line + Scatter"]:
                            fig.add_trace(go.Scatter(
                                x=group_data[x_axis],
                                y=group_data[y_var],
                                mode='markers',
                                name=str(group) if plot_type == "Scatter Plot" else None,
                                marker=dict(size=6),
                                showlegend=plot_type == "Scatter Plot"
                            ))
                    else:
                        # For other groupings, we treat each group as a series
                        for cell_id in group_data['cell_id'].unique():
                            cell_group_data = group_data[group_data['cell_id'] == cell_id]

                            # Skip empty cell groups
                            if cell_group_data.empty:
                                continue

                            cell_name = cell_group_data['cell_name'].iloc[
                                0] if 'cell_name' in cell_group_data.columns else f"Cell {cell_id}"

                            # Add a line trace
                            if plot_type in ["Line Plot", "Line + Scatter"]:
                                fig.add_trace(go.Scatter(
                                    x=cell_group_data[x_axis],
                                    y=cell_group_data[y_var],
                                    mode='lines',
                                    name=f"{group} - {cell_name}",
                                    line=dict(width=2),
                                    legendgroup=str(group)
                                ))

                            # Add scatter points
                            if plot_type in ["Scatter Plot", "Line + Scatter"]:
                                fig.add_trace(go.Scatter(
                                    x=cell_group_data[x_axis],
                                    y=cell_group_data[y_var],
                                    mode='markers',
                                    name=f"{group} - {cell_name}" if plot_type == "Scatter Plot" else None,
                                    marker=dict(size=6),
                                    showlegend=plot_type == "Scatter Plot",
                                    legendgroup=str(group)
                                ))
            else:
                # No grouping, plot each cell individually
                for cell_id in plot_data['cell_id'].unique():
                    cell_data_subset = plot_data[plot_data['cell_id'] == cell_id]

                    # Skip empty cell data
                    if cell_data_subset.empty:
                        continue

                    cell_name = cell_data_subset['cell_name'].iloc[
                        0] if 'cell_name' in cell_data_subset.columns else f"Cell {cell_id}"

                    # Add a line trace
                    if plot_type in ["Line Plot", "Line + Scatter"]:
                        fig.add_trace(go.Scatter(
                            x=cell_data_subset[x_axis],
                            y=cell_data_subset[y_var],
                            mode='lines',
                            name=cell_name,
                            line=dict(width=2)
                        ))

                    # Add scatter points
                    if plot_type in ["Scatter Plot", "Line + Scatter"]:
                        fig.add_trace(go.Scatter(
                            x=cell_data_subset[x_axis],
                            y=cell_data_subset[y_var],
                            mode='markers',
                            name=cell_name if plot_type == "Scatter Plot" else None,
                            marker=dict(size=6),
                            showlegend=plot_type == "Scatter Plot"
                        ))

            # Update layout
            fig.update_layout(
                title=f"{y_var} vs {x_axis}",
                xaxis_title=x_axis,
                yaxis_title=y_label,
                legend_title=group_by if group_by != 'None' else "Cell",
                height=600
            )

            # Render plot
            st.plotly_chart(fig, use_container_width=True)

            # Add a horizontal line to separate plots
            st.markdown("---")


def main():
    # Title and description
    st.title("🔋 Battery Cell Analytics Dashboard")
    st.markdown("### Cell Selection and Analysis")



    # Create tabs
    tab1, tab2 = st.tabs(["Cell Metadata", "Cycle Plotting"])

    # Track active tab
    if tab1:
        st.session_state['active_tab'] = "Cell Metadata"
    if tab2:
        st.session_state['active_tab'] = "Cycle Plotting"

    # Tab content
    with tab1:
        data, selected_cell_ids = cell_metadata_tab()

    with tab2:
        cycle_plotting_tab()


# Run the app
if __name__ == "__main__":
    main()