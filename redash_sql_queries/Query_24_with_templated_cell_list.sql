-- Enhanced cell selection view that combines key information from multiple sources
WITH cell_test_status AS (
    -- Subquery to determine test status for each cell
    SELECT
        c.cell_id,
        CASE
            WHEN mt.merged_test_id IS NULL THEN 'untested'
            WHEN mta.merged_test_id IS NULL THEN 'no_analytics'
            WHEN ar.status = 'COMPLETED' THEN 'analysis_complete'
            WHEN ar.status = 'FAILED' THEN 'analysis_failed'
            ELSE 'processing'
        END AS test_status,
        mt.merged_test_id,
        mt.test_start_date,
        mt.temperature AS test_temperature
    FROM
        cell c
        LEFT JOIN mergedtest mt ON c.cell_id = mt.cell_id
        LEFT JOIN mergedtestanalytics mta ON mt.merged_test_id = mta.merged_test_id
        LEFT JOIN (
            -- Get most recent analysis run status
            SELECT DISTINCT ON (merged_test_id)
                merged_test_id, status
            FROM analysisrun
            ORDER BY merged_test_id, started_at DESC
        ) ar ON mt.merged_test_id = ar.merged_test_id
)
SELECT
    -- Cell identification and basic properties
    cp.cell_id,
    cp.cell_name,
    cp.cell_type,
    cp.experiment_group,
    cp.description,
    cp.design_name,
    cp.design_capacity_mah,
    cp.actual_nominal_capacity_ah,
    cp.total_active_mass_g,

    -- Structure information
    cls.total_layers,
    cls.multi_layer_components,
    cls.layer_types,
    cls.single_layers,
    cls.bilayers,
    cls.trilayers,

    -- Test status information
    cts.test_status,
    cts.merged_test_id,
    cts.test_start_date,
    cts.test_temperature,

    -- Date-based grouping fields
    EXTRACT(YEAR FROM cts.test_start_date) AS test_year,
    EXTRACT(QUARTER FROM cts.test_start_date) AS test_quarter,
    EXTRACT(MONTH FROM cts.test_start_date) AS test_month,

    -- Performance indicators (only for cells with analytics)
    mta.total_cycles,
    mta.regular_cycles,
    mta.formation_cycles,
    mta.last_discharge_capacity,
    mta.discharge_capacity_throughput,
    mta.average_coulombic_efficiency,
    mta.average_energy_efficiency,
    mta.discharge_capacity_retention,

    -- Additional calculated fields for filtering and grouping
    CASE
        WHEN mta.discharge_capacity_retention > 0.8 THEN 'high_retention'
        WHEN mta.discharge_capacity_retention > 0.6 THEN 'medium_retention'
        WHEN mta.discharge_capacity_retention IS NOT NULL THEN 'low_retention'
        ELSE 'unknown'
    END AS retention_category,

    CASE
        WHEN mta.total_cycles > 100 THEN 'long_cycle'
        WHEN mta.total_cycles > 20 THEN 'medium_cycle'
        WHEN mta.total_cycles IS NOT NULL THEN 'short_cycle'
        ELSE 'unknown'
    END AS cycle_life_category

FROM
    vw_cell_properties cp
    LEFT JOIN vw_cell_layer_structure cls ON cp.cell_id = cls.cell_id
    LEFT JOIN cell_test_status cts ON cp.cell_id = cts.cell_id
    LEFT JOIN mergedtestanalytics mta ON cts.merged_test_id = mta.merged_test_id