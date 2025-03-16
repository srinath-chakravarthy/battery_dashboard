import polars as pl
import requests
from datetime import datetime
from ..config import REDASH_URL, REDASH_API_KEY, CELL_QUERY_ID, CYCLE_QUERY_ID
# Cache for query results
query_cache = {}


# Fetch Redash query results
def get_redash_query_results(query_id, params=None, cache_ttl=300):
    """Fetch results from a Redash query with caching."""
    cache_key = f"{query_id}_{str(params)}"

    # Check cache
    if cache_key in query_cache:
        cached_result, timestamp = query_cache[cache_key]
        if (datetime.now() - timestamp).total_seconds() < cache_ttl:
            return cached_result

    try:
        api_url = f"{REDASH_URL}/api/queries/{query_id}/results"
        headers = {"Authorization": f"Key {REDASH_API_KEY}", "Content-Type": "application/json"}
        response = requests.post(api_url, headers=headers, json={"parameters": params or {}})
        response.raise_for_status()

        query_result = response.json()
        if "query_result" in query_result and "data" in query_result["query_result"]:
            df = pl.DataFrame(query_result["query_result"]["data"]["rows"])
            query_cache[cache_key] = (df, datetime.now())
            return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Redash: {e}")

    return pl.DataFrame()


# Load initial data
def load_initial_data():
    df = get_redash_query_results(CELL_QUERY_ID)
    if not df.is_empty() and "regular_cycles" in df.columns:
        df = df.filter(pl.col("regular_cycles") > 20)
    return df


def get_cycle_data(cell_ids=None, cell_metadata=None):
    """Get cycle data and join with cell metadata."""
    if not cell_ids:
        return pl.DataFrame()

    # Create a progress widget
    # progress = pn.widgets.Progress(value=0, max=len(cell_ids), name="Loading Cells")
    # if status_indicator:
    #     status_indicator.object = pn.Column(
    #         "**Fetching cycle data from database...**",
    #         progress
    #     )

    all_results = []
    for cell_id in cell_ids:
        params = {"cell_ids": str(cell_id)}
        cell_data = get_redash_query_results(CYCLE_QUERY_ID, params)
        if not cell_data.is_empty():
            # List of columns that should be normalized (containing capacity or energy)
            normalize_columns = [col for col in cell_data.columns if
                                 any(term in col.lower() for term in ['_capacity', '_energy'])]

            # Create expressions for normalization
            norm_expressions = []
            for col in normalize_columns:
                # 1. Regular cycle normalization (using cycle 1 as reference)
                first_cycle_val = cell_data.filter(pl.col('regular_cycle_number') == 1)[col].item()
                norm_expressions.append(
                    (pl.col(col) / first_cycle_val).alias(f'{col}_norm_reg')
                )

                # 2. 95th percentile normalization
                p95_val = cell_data[col].quantile(0.95)
                norm_expressions.append(
                    (pl.col(col) / p95_val).alias(f'{col}_norm_p95')
                )

            # Apply normalizations for this cell
            if norm_expressions:
                cell_data = cell_data.with_columns(norm_expressions)

            all_results.append(cell_data)

    cycle_data = pl.concat(all_results) if all_results else pl.DataFrame()
    return cycle_data
