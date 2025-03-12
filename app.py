import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import os
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
REDASH_API_KEY = os.getenv("REDASH_API_KEY", "g49aajpPujqcYb4F45yGLiPbyR5Z5XY3lDKrra8u")
CELL_QUERY_ID = os.getenv("CELL_QUERY_ID", "24")  # ID of the cell data query in Redash


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
        # Construct the API URL for getting query results
        api_url = f"{REDASH_URL}/api/queries/{query_id}/results"

        # Prepare headers and parameters
        headers = {
            "Authorization": f"Key {REDASH_API_KEY}",
            "Content-Type": "application/json"
        }

        params_payload = {"parameters": params or {}}

        # Make the API request
        response = requests.post(api_url, headers=headers, json=params_payload)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        # Parse the response
        query_result = response.json()

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


def main():
    # Title and description
    st.title("🔋 Battery Cell Analytics Dashboard")
    st.markdown("### Cell Selection and Analysis")

    # Add sidebar for filters
    st.sidebar.header("Filters")

    # Add a refresh button
    if st.button("Refresh Data"):
        st.cache_data.clear()

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
        return

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

    # Display data summary
    st.markdown(f"### Showing {len(data)} cells")

    # Main content area - cell table
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display table with selection capability
        if not data.empty:
            # Allow users to select which columns to display
            default_columns = [
                'cell_name', 'design_name', 'design_capacity_mah',
                'actual_nominal_capacity_ah', 'regular_cycles', 'formation_cycles'
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
                # Add cell selection column and display the table
                selection_column = st.checkbox("Add selection column", value=True)

                if selection_column:
                    # This creates a dataframe with select boxes
                    selected_rows = st.data_editor(
                        data[selected_columns],
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
                else:
                    # Just display the table without selection capability
                    st.dataframe(data[selected_columns], hide_index=True, use_container_width=True)
        else:
            st.info("No data available with the current filter settings.")

    with col2:
        # Summary statistics
        st.markdown("### Summary Statistics for all cells with cycles > 20")

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


# Run the app
if __name__ == "__main__":
    main()