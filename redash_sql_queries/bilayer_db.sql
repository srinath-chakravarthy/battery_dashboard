--
-- PostgreSQL database dump
--

-- Dumped from database version 16.8 (Ubuntu 16.8-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.8 (Ubuntu 16.8-0ubuntu0.24.04.1)

-- Started on 2025-03-12 09:31:50 EDT

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 3774 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- TOC entry 947 (class 1247 OID 17302)
-- Name: analysis_error_category; Type: TYPE; Schema: public; Owner: cell_admin
--

CREATE TYPE public.analysis_error_category AS ENUM (
    'DataLoadingError',
    'DataValidationError',
    'PhaseValidationError',
    'CycleAnalysisError',
    'PerformanceCalculationError',
    'DatabaseError',
    'ConfigurationError',
    'TimeoutError',
    'UnknownError'
);


ALTER TYPE public.analysis_error_category OWNER TO cell_admin;

--
-- TOC entry 274 (class 1255 OID 22270)
-- Name: refresh_cell_layers_view(); Type: FUNCTION; Schema: public; Owner: cell_admin
--

CREATE FUNCTION public.refresh_cell_layers_view() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW vw_cell_layer_structure;
END;
$$;


ALTER FUNCTION public.refresh_cell_layers_view() OWNER TO cell_admin;

--
-- TOC entry 273 (class 1255 OID 22279)
-- Name: refresh_cell_properties_view(); Type: FUNCTION; Schema: public; Owner: cell_admin
--

CREATE FUNCTION public.refresh_cell_properties_view() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    REFRESH MATERIALIZED VIEW vw_cell_properties;
END;
$$;


ALTER FUNCTION public.refresh_cell_properties_view() OWNER TO cell_admin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 231 (class 1259 OID 17321)
-- Name: analysiserror; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.analysiserror (
    error_id bigint NOT NULL,
    run_id bigint NOT NULL,
    error_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    error_category public.analysis_error_category NOT NULL,
    error_code character varying(100),
    error_message text NOT NULL,
    error_details jsonb,
    stack_trace text,
    affected_data jsonb
);


ALTER TABLE public.analysiserror OWNER TO cell_admin;

--
-- TOC entry 232 (class 1259 OID 17327)
-- Name: analysiserror_error_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.analysiserror_error_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analysiserror_error_id_seq OWNER TO cell_admin;

--
-- TOC entry 3775 (class 0 OID 0)
-- Dependencies: 232
-- Name: analysiserror_error_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.analysiserror_error_id_seq OWNED BY public.analysiserror.error_id;


--
-- TOC entry 233 (class 1259 OID 17328)
-- Name: analysisrun; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.analysisrun (
    run_id bigint NOT NULL,
    merged_test_id bigint NOT NULL,
    version_id integer NOT NULL,
    status character varying(50) NOT NULL,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    error_category public.analysis_error_category,
    error_message text,
    progress_percentage double precision DEFAULT 0,
    processing_stages jsonb,
    retry_count integer DEFAULT 0,
    last_successful_stage character varying(100),
    runtime_seconds integer,
    CONSTRAINT analysisrun_status_check CHECK (((status)::text = ANY (ARRAY[('QUEUED'::character varying)::text, ('INITIALIZING'::character varying)::text, ('PROCESSING'::character varying)::text, ('COMPLETED'::character varying)::text, ('FAILED'::character varying)::text, ('TIMEOUT'::character varying)::text, ('ABORTED'::character varying)::text, ('PARTIAL_SUCCESS'::character varying)::text])))
);


ALTER TABLE public.analysisrun OWNER TO cell_admin;

--
-- TOC entry 234 (class 1259 OID 17337)
-- Name: analysisrun_run_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.analysisrun_run_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analysisrun_run_id_seq OWNER TO cell_admin;

--
-- TOC entry 3776 (class 0 OID 0)
-- Dependencies: 234
-- Name: analysisrun_run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.analysisrun_run_id_seq OWNED BY public.analysisrun.run_id;


--
-- TOC entry 235 (class 1259 OID 17338)
-- Name: analyticsversion; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.analyticsversion (
    version_id integer NOT NULL,
    version_number character varying(50) NOT NULL,
    config_snapshot jsonb,
    deployed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    description text
);


ALTER TABLE public.analyticsversion OWNER TO cell_admin;

--
-- TOC entry 236 (class 1259 OID 17344)
-- Name: analyticsversion_version_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.analyticsversion_version_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.analyticsversion_version_id_seq OWNER TO cell_admin;

--
-- TOC entry 3777 (class 0 OID 0)
-- Dependencies: 236
-- Name: analyticsversion_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.analyticsversion_version_id_seq OWNED BY public.analyticsversion.version_id;


--
-- TOC entry 215 (class 1259 OID 16435)
-- Name: anode; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.anode (
    anode_id integer NOT NULL,
    lot_name character varying(100),
    build_date date,
    length_mm double precision NOT NULL,
    width_mm double precision NOT NULL,
    area_mm2 double precision GENERATED ALWAYS AS ((length_mm * width_mm)) STORED,
    layer_build_id integer NOT NULL
);


ALTER TABLE public.anode OWNER TO cell_admin;

--
-- TOC entry 237 (class 1259 OID 17345)
-- Name: anode_anode_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.anode_anode_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.anode_anode_id_seq OWNER TO cell_admin;

--
-- TOC entry 3778 (class 0 OID 0)
-- Dependencies: 237
-- Name: anode_anode_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.anode_anode_id_seq OWNED BY public.anode.anode_id;


--
-- TOC entry 217 (class 1259 OID 16446)
-- Name: cell; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.cell (
    cell_id bigint NOT NULL,
    cell_type character varying(100),
    description text,
    notes text,
    cell_design_id integer,
    cell_number integer NOT NULL,
    doe character varying(100),
    cell_name character varying(120) GENERATED ALWAYS AS ((((cell_type)::text || '-'::text) || (cell_number)::text)) STORED
);


ALTER TABLE public.cell OWNER TO cell_admin;

--
-- TOC entry 252 (class 1259 OID 17372)
-- Name: mergedtest; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.mergedtest (
    merged_test_id bigint NOT NULL,
    cell_id bigint NOT NULL,
    total_records_merged integer NOT NULL,
    last_processed_merged_record integer NOT NULL,
    last_merge_timestamp timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    merge_status character varying(50) DEFAULT 'IN_PROGRESS'::character varying NOT NULL,
    merge_completion_timestamp timestamp without time zone,
    merge_error_message text,
    test_start_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    temperature double precision DEFAULT 25.0 NOT NULL,
    CONSTRAINT mergedtest_merge_status_check CHECK (((merge_status)::text = ANY (ARRAY[('IN_PROGRESS'::character varying)::text, ('COMPLETED'::character varying)::text, ('FAILED'::character varying)::text, ('NEEDS_UPDATE'::character varying)::text])))
);


ALTER TABLE public.mergedtest OWNER TO cell_admin;

--
-- TOC entry 254 (class 1259 OID 17383)
-- Name: mergedtestanalytics; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.mergedtestanalytics (
    merged_test_id bigint NOT NULL,
    formation_cycles integer,
    dcir_cycles integer,
    rpt_cycles integer,
    regular_cycles integer,
    total_cycles integer,
    last_charge_capacity double precision,
    last_discharge_capacity double precision,
    discharge_capacity_throughput double precision,
    discharge_energy_throughput double precision,
    average_coulombic_efficiency double precision,
    average_energy_efficiency double precision,
    discharge_capacity_retention double precision,
    charge_capacity_retention double precision,
    last_processed_timestamp timestamp without time zone,
    phase_metrics_stored boolean DEFAULT true
);


ALTER TABLE public.mergedtestanalytics OWNER TO cell_admin;

--
-- TOC entry 259 (class 1259 OID 17393)
-- Name: testfiles; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.testfiles (
    test_file_id bigint NOT NULL,
    file_id character varying(100) NOT NULL,
    hierarchy_id bigint NOT NULL,
    start_time timestamp without time zone NOT NULL,
    num_records integer NOT NULL,
    max_records integer NOT NULL,
    test_id character varying(100) NOT NULL,
    machine_key character varying(100) NOT NULL,
    last_processed_record integer DEFAULT 0,
    merged_test_id bigint NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    download_id bigint,
    merge_status character varying(50) DEFAULT 'PENDING'::character varying,
    merge_attempts integer DEFAULT 0,
    last_merge_attempt timestamp without time zone,
    merge_completion_timestamp timestamp without time zone,
    merge_error_message text,
    CONSTRAINT testfiles_merge_status_check CHECK (((merge_status)::text = ANY (ARRAY[('PENDING'::character varying)::text, ('IN_PROGRESS'::character varying)::text, ('COMPLETED'::character varying)::text, ('FAILED'::character varying)::text])))
);


ALTER TABLE public.testfiles OWNER TO cell_admin;

--
-- TOC entry 261 (class 1259 OID 17404)
-- Name: testhierarchy; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.testhierarchy (
    hierarchy_id bigint NOT NULL,
    base_barcode character varying(100) NOT NULL,
    test_variant character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.testhierarchy OWNER TO cell_admin;

--
-- TOC entry 267 (class 1259 OID 22155)
-- Name: battery_analytics_overview; Type: VIEW; Schema: public; Owner: cell_admin
--

CREATE VIEW public.battery_analytics_overview AS
 SELECT c.cell_id,
    c.cell_name,
    mt.merged_test_id,
    mt.total_records_merged,
    th.hierarchy_id,
    th.test_variant,
    th.base_barcode,
    count(tf.test_file_id) AS file_count,
    sum(
        CASE
            WHEN ((tf.merge_status)::text = 'COMPLETED'::text) THEN 1
            ELSE 0
        END) AS completed_files,
        CASE
            WHEN (mta.merged_test_id IS NOT NULL) THEN 'Yes'::text
            ELSE 'No'::text
        END AS analytics_present,
        CASE
            WHEN ((ar.status)::text = 'COMPLETED'::text) THEN 'Success'::character varying
            WHEN ((ar.status)::text = 'FAILED'::text) THEN 'Failed'::character varying
            WHEN (ar.status IS NULL) THEN 'Not Run'::character varying
            ELSE ar.status
        END AS analysis_status,
    ar.completed_at AS last_analyzed,
    ar.error_message AS analysis_error,
    mta.last_processed_timestamp AS last_metrics_update,
    mt.temperature AS test_temperature,
    mt.test_start_date
   FROM (((((public.cell c
     JOIN public.mergedtest mt ON ((c.cell_id = mt.cell_id)))
     LEFT JOIN public.testfiles tf ON ((mt.merged_test_id = tf.merged_test_id)))
     LEFT JOIN public.testhierarchy th ON ((tf.hierarchy_id = th.hierarchy_id)))
     LEFT JOIN public.mergedtestanalytics mta ON ((mt.merged_test_id = mta.merged_test_id)))
     LEFT JOIN ( SELECT DISTINCT ON (analysisrun.merged_test_id) analysisrun.merged_test_id,
            analysisrun.status,
            analysisrun.completed_at,
            analysisrun.error_message
           FROM public.analysisrun
          ORDER BY analysisrun.merged_test_id, analysisrun.started_at DESC) ar ON ((mt.merged_test_id = ar.merged_test_id)))
  GROUP BY c.cell_id, c.cell_name, mt.merged_test_id, mt.total_records_merged, th.hierarchy_id, th.test_variant, th.base_barcode, mta.merged_test_id, ar.status, ar.completed_at, ar.error_message, mta.last_processed_timestamp, mt.temperature, mt.test_start_date
  ORDER BY c.cell_id, mt.merged_test_id, th.hierarchy_id;


ALTER VIEW public.battery_analytics_overview OWNER TO cell_admin;

--
-- TOC entry 216 (class 1259 OID 16440)
-- Name: cathode; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.cathode (
    cathode_id integer NOT NULL,
    lot_name character varying(100),
    build_date date,
    length_mm double precision NOT NULL,
    width_mm double precision NOT NULL,
    area_mm2 double precision GENERATED ALWAYS AS ((length_mm * width_mm)) STORED,
    mass_g double precision NOT NULL,
    cam_percentage double precision DEFAULT 0.85 NOT NULL,
    layer_build_id integer NOT NULL
);


ALTER TABLE public.cathode OWNER TO cell_admin;

--
-- TOC entry 218 (class 1259 OID 16453)
-- Name: cellbuild; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.cellbuild (
    cell_build_id integer NOT NULL,
    cell_id bigint NOT NULL,
    build_date date NOT NULL,
    notes text,
    cell_builder_name character varying(100),
    cell_build_status_id integer
);


ALTER TABLE public.cellbuild OWNER TO cell_admin;

--
-- TOC entry 220 (class 1259 OID 16463)
-- Name: celldesign; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.celldesign (
    cell_design_id integer NOT NULL,
    design_name character varying(100) NOT NULL,
    capacity_mah double precision NOT NULL,
    num_layers integer NOT NULL,
    notes text
);


ALTER TABLE public.celldesign OWNER TO cell_admin;

--
-- TOC entry 224 (class 1259 OID 16499)
-- Name: layerassembly; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.layerassembly (
    assembly_id integer NOT NULL,
    multi_layer_id integer,
    layer_build_id integer NOT NULL,
    position_in_cell integer,
    position_in_component integer,
    cell_build_id integer
);


ALTER TABLE public.layerassembly OWNER TO cell_admin;

--
-- TOC entry 269 (class 1259 OID 22177)
-- Name: battery_analytics_view; Type: VIEW; Schema: public; Owner: cell_admin
--

CREATE VIEW public.battery_analytics_view AS
 SELECT c.cell_id,
    c.cell_name,
    c.cell_type,
    c.doe AS experiment_group,
    cd.capacity_mah AS design_capacity_mah,
    mt.merged_test_id,
    mt.test_start_date,
    mt.temperature AS test_temperature,
    mt.total_records_merged,
    mt.last_processed_merged_record,
    mta.last_processed_timestamp,
    mta.formation_cycles,
    mta.dcir_cycles,
    mta.rpt_cycles,
    mta.regular_cycles,
    mta.total_cycles,
    mta.last_charge_capacity,
    mta.last_discharge_capacity,
    mta.discharge_capacity_throughput,
    mta.discharge_energy_throughput,
    mta.average_coulombic_efficiency,
    mta.average_energy_efficiency,
    mta.discharge_capacity_retention,
    mta.charge_capacity_retention,
    ar.status AS latest_analysis_status,
    ar.started_at AS latest_analysis_time,
    ar.completed_at AS latest_analysis_completion,
    cath.mass_g AS cathode_mass_g,
    cath.cam_percentage AS active_material_percentage,
    ((cath.mass_g * cath.cam_percentage) / (100)::double precision) AS active_mass_g,
    (((cath.mass_g * cath.cam_percentage) / (100)::double precision) * (200)::double precision) AS theoretical_capacity_mah
   FROM (((((public.cell c
     JOIN public.celldesign cd ON ((c.cell_design_id = cd.cell_design_id)))
     JOIN public.mergedtest mt ON ((c.cell_id = mt.cell_id)))
     JOIN public.mergedtestanalytics mta ON ((mt.merged_test_id = mta.merged_test_id)))
     JOIN ( SELECT DISTINCT ON (analysisrun.merged_test_id) analysisrun.merged_test_id,
            analysisrun.status,
            analysisrun.started_at,
            analysisrun.completed_at
           FROM public.analysisrun
          WHERE ((analysisrun.status)::text = 'COMPLETED'::text)
          ORDER BY analysisrun.merged_test_id, analysisrun.started_at DESC) ar ON ((mt.merged_test_id = ar.merged_test_id)))
     LEFT JOIN ( SELECT cb.cell_id,
            ca.mass_g,
            ca.cam_percentage
           FROM ((public.cathode ca
             JOIN public.layerassembly la ON ((ca.layer_build_id = la.layer_build_id)))
             JOIN public.cellbuild cb ON ((la.cell_build_id = cb.cell_build_id)))) cath ON ((c.cell_id = cath.cell_id)))
  WHERE (((mt.merge_status)::text = 'COMPLETED'::text) AND (mta.total_cycles > 0));


ALTER VIEW public.battery_analytics_view OWNER TO cell_admin;

--
-- TOC entry 238 (class 1259 OID 17346)
-- Name: cathode_cathode_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.cathode_cathode_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cathode_cathode_id_seq OWNER TO cell_admin;

--
-- TOC entry 3779 (class 0 OID 0)
-- Dependencies: 238
-- Name: cathode_cathode_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.cathode_cathode_id_seq OWNED BY public.cathode.cathode_id;


--
-- TOC entry 239 (class 1259 OID 17347)
-- Name: cell_cell_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.cell_cell_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cell_cell_id_seq OWNER TO cell_admin;

--
-- TOC entry 3780 (class 0 OID 0)
-- Dependencies: 239
-- Name: cell_cell_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.cell_cell_id_seq OWNED BY public.cell.cell_id;


--
-- TOC entry 240 (class 1259 OID 17348)
-- Name: cellbuild_cell_build_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.cellbuild_cell_build_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cellbuild_cell_build_id_seq OWNER TO cell_admin;

--
-- TOC entry 3781 (class 0 OID 0)
-- Dependencies: 240
-- Name: cellbuild_cell_build_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.cellbuild_cell_build_id_seq OWNED BY public.cellbuild.cell_build_id;


--
-- TOC entry 219 (class 1259 OID 16459)
-- Name: cellbuildstatus; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.cellbuildstatus (
    id integer NOT NULL,
    status character varying(100)
);


ALTER TABLE public.cellbuildstatus OWNER TO cell_admin;

--
-- TOC entry 241 (class 1259 OID 17349)
-- Name: cellbuildstatus_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.cellbuildstatus_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cellbuildstatus_id_seq OWNER TO cell_admin;

--
-- TOC entry 3782 (class 0 OID 0)
-- Dependencies: 241
-- Name: cellbuildstatus_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.cellbuildstatus_id_seq OWNED BY public.cellbuildstatus.id;


--
-- TOC entry 242 (class 1259 OID 17350)
-- Name: celldesign_cell_design_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.celldesign_cell_design_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.celldesign_cell_design_id_seq OWNER TO cell_admin;

--
-- TOC entry 3783 (class 0 OID 0)
-- Dependencies: 242
-- Name: celldesign_cell_design_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.celldesign_cell_design_id_seq OWNED BY public.celldesign.cell_design_id;


--
-- TOC entry 221 (class 1259 OID 16469)
-- Name: clamping; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.clamping (
    clamping_id integer NOT NULL,
    pad_type character varying(100) NOT NULL,
    pad_thickness_mm double precision NOT NULL,
    is_double_sided boolean NOT NULL,
    desired_pressure_mpa double precision NOT NULL
);


ALTER TABLE public.clamping OWNER TO cell_admin;

--
-- TOC entry 243 (class 1259 OID 17351)
-- Name: clamping_clamping_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.clamping_clamping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clamping_clamping_id_seq OWNER TO cell_admin;

--
-- TOC entry 3784 (class 0 OID 0)
-- Dependencies: 243
-- Name: clamping_clamping_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.clamping_clamping_id_seq OWNED BY public.clamping.clamping_id;


--
-- TOC entry 222 (class 1259 OID 16473)
-- Name: clampingoutcome; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.clampingoutcome (
    outcome_id integer NOT NULL,
    cell_build_id integer NOT NULL,
    actual_pressure_mpa double precision NOT NULL,
    actual_load_n double precision NOT NULL,
    clamping_person character varying(100) DEFAULT NULL::character varying,
    outcome_notes text,
    clamping_id integer,
    clamping_status_id integer,
    clamping_date date
);


ALTER TABLE public.clampingoutcome OWNER TO cell_admin;

--
-- TOC entry 244 (class 1259 OID 17352)
-- Name: clampingoutcome_outcome_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.clampingoutcome_outcome_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clampingoutcome_outcome_id_seq OWNER TO cell_admin;

--
-- TOC entry 3785 (class 0 OID 0)
-- Dependencies: 244
-- Name: clampingoutcome_outcome_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.clampingoutcome_outcome_id_seq OWNED BY public.clampingoutcome.outcome_id;


--
-- TOC entry 223 (class 1259 OID 16479)
-- Name: clampingstatus; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.clampingstatus (
    clamping_status_id integer NOT NULL,
    status character varying(100) NOT NULL
);


ALTER TABLE public.clampingstatus OWNER TO cell_admin;

--
-- TOC entry 245 (class 1259 OID 17353)
-- Name: clampingstatus_clamping_status_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.clampingstatus_clamping_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clampingstatus_clamping_status_id_seq OWNER TO cell_admin;

--
-- TOC entry 3786 (class 0 OID 0)
-- Dependencies: 245
-- Name: clampingstatus_clamping_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.clampingstatus_clamping_status_id_seq OWNED BY public.clampingstatus.clamping_status_id;


--
-- TOC entry 246 (class 1259 OID 17354)
-- Name: cycleanalytics; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.cycleanalytics (
    cycle_id bigint NOT NULL,
    merged_test_id bigint NOT NULL,
    cycle_number integer NOT NULL,
    cycle_type character varying(50),
    charge_capacity double precision,
    discharge_capacity double precision,
    coulombic_efficiency double precision,
    energy_efficiency double precision,
    charge_duration double precision,
    discharge_duration double precision,
    charge_rdv double precision,
    discharge_rdv double precision,
    rest_voltage_after_charge double precision,
    rest_voltage_after_discharge double precision,
    cv_duration double precision,
    cv_voltage double precision,
    cv_capacity double precision,
    cycle_start_index integer,
    cycle_end_index integer,
    original_start_row integer,
    original_end_row integer,
    charge_energy double precision,
    discharge_energy double precision,
    regular_cycle_number integer
);


ALTER TABLE public.cycleanalytics OWNER TO cell_admin;

--
-- TOC entry 247 (class 1259 OID 17357)
-- Name: cycleanalytics_cycle_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.cycleanalytics_cycle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cycleanalytics_cycle_id_seq OWNER TO cell_admin;

--
-- TOC entry 3787 (class 0 OID 0)
-- Dependencies: 247
-- Name: cycleanalytics_cycle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.cycleanalytics_cycle_id_seq OWNED BY public.cycleanalytics.cycle_id;


--
-- TOC entry 248 (class 1259 OID 17358)
-- Name: filedownloadstatus; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.filedownloadstatus (
    download_id bigint NOT NULL,
    file_id character varying(100) NOT NULL,
    status character varying(50) NOT NULL,
    attempt_count integer DEFAULT 1,
    first_attempt_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_attempt_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completion_timestamp timestamp without time zone,
    error_message text,
    bytes_downloaded bigint,
    total_bytes bigint,
    download_duration integer,
    priority integer DEFAULT 5,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT filedownloadstatus_status_check CHECK (((status)::text = ANY (ARRAY[('PENDING'::character varying)::text, ('DOWNLOADING'::character varying)::text, ('COMPLETED'::character varying)::text, ('FAILED'::character varying)::text, ('QUEUED'::character varying)::text])))
);


ALTER TABLE public.filedownloadstatus OWNER TO cell_admin;

--
-- TOC entry 268 (class 1259 OID 22172)
-- Name: failed_cells_without_analytics; Type: VIEW; Schema: public; Owner: cell_admin
--

CREATE VIEW public.failed_cells_without_analytics AS
 SELECT c.cell_id,
    c.cell_name,
    c.cell_type,
    c.description,
    mt.merged_test_id,
    mt.merge_status,
    mt.merge_error_message,
    COALESCE((mt.total_records_merged)::bigint, file_stats.total_expected_records) AS total_records,
    file_stats.total_files,
    file_stats.total_expected_records,
    file_stats.downloaded_files,
    ar.status AS analysis_status,
    ar.error_message AS analysis_error_message,
    ar.started_at AS analysis_started,
    ar.completed_at AS analysis_completed
   FROM ((((public.cell c
     JOIN public.mergedtest mt ON ((c.cell_id = mt.cell_id)))
     LEFT JOIN public.mergedtestanalytics mta ON ((mt.merged_test_id = mta.merged_test_id)))
     LEFT JOIN ( SELECT tf.merged_test_id,
            count(tf.test_file_id) AS total_files,
            sum(tf.num_records) AS total_expected_records,
            sum(
                CASE
                    WHEN ((fds.status)::text = 'COMPLETED'::text) THEN 1
                    ELSE 0
                END) AS downloaded_files
           FROM (public.testfiles tf
             LEFT JOIN public.filedownloadstatus fds ON ((tf.download_id = fds.download_id)))
          GROUP BY tf.merged_test_id) file_stats ON ((mt.merged_test_id = file_stats.merged_test_id)))
     LEFT JOIN ( SELECT DISTINCT ON (analysisrun.merged_test_id) analysisrun.merged_test_id,
            analysisrun.status,
            analysisrun.error_message,
            analysisrun.started_at,
            analysisrun.completed_at
           FROM public.analysisrun
          ORDER BY analysisrun.merged_test_id, analysisrun.started_at DESC) ar ON ((mt.merged_test_id = ar.merged_test_id)))
  WHERE ((mta.merged_test_id IS NULL) AND (((mt.merge_status)::text = 'FAILED'::text) OR ((ar.status IS NOT NULL) AND ((ar.status)::text = 'FAILED'::text))))
  ORDER BY c.cell_name, ar.started_at DESC;


ALTER VIEW public.failed_cells_without_analytics OWNER TO cell_admin;

--
-- TOC entry 249 (class 1259 OID 17369)
-- Name: filedownloadstatus_download_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.filedownloadstatus_download_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.filedownloadstatus_download_id_seq OWNER TO cell_admin;

--
-- TOC entry 3788 (class 0 OID 0)
-- Dependencies: 249
-- Name: filedownloadstatus_download_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.filedownloadstatus_download_id_seq OWNED BY public.filedownloadstatus.download_id;


--
-- TOC entry 225 (class 1259 OID 16503)
-- Name: layerbuild; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.layerbuild (
    layer_build_id integer NOT NULL,
    build_date date NOT NULL,
    builder_name character varying(100),
    status character varying(50) DEFAULT 'Manufactured'::character varying,
    notes text
);


ALTER TABLE public.layerbuild OWNER TO cell_admin;

--
-- TOC entry 226 (class 1259 OID 16524)
-- Name: multilayer; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.multilayer (
    multi_layer_id integer NOT NULL,
    layer_type character varying(50) NOT NULL,
    notes text,
    CONSTRAINT valid_layer_type CHECK (((layer_type)::text = ANY (ARRAY[('Single'::character varying)::text, ('Bilayer'::character varying)::text, ('Trilayer'::character varying)::text, ('Quad'::character varying)::text, ('Stack'::character varying)::text])))
);


ALTER TABLE public.multilayer OWNER TO cell_admin;

--
-- TOC entry 227 (class 1259 OID 16536)
-- Name: separator; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.separator (
    separator_id integer NOT NULL,
    lot_name character varying(100),
    build_date date,
    length_mm double precision NOT NULL,
    width_mm double precision NOT NULL,
    area_mm2 double precision GENERATED ALWAYS AS ((length_mm * width_mm)) STORED,
    layer_build_id integer NOT NULL
);


ALTER TABLE public.separator OWNER TO cell_admin;

--
-- TOC entry 228 (class 1259 OID 16563)
-- Name: wipprocessoutcome; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.wipprocessoutcome (
    outcome_id integer NOT NULL,
    post_wimp_ocv_v double precision,
    post_wip_impedance_ohms double precision,
    post_wip_anode_length_mm double precision,
    post_wip_anode_width_mm double precision,
    layer_build_id integer,
    pressurization_id integer DEFAULT 1,
    wip_status_id integer,
    wip_process_date date,
    post_wip_cathode_length_mm double precision,
    post_wip_cathode_width_mm double precision,
    post_wip_se_length_mm double precision,
    post_wip_se_width_mm double precision,
    assembly_id integer,
    CONSTRAINT check_wip_reference CHECK (((layer_build_id IS NOT NULL) OR (assembly_id IS NOT NULL)))
);


ALTER TABLE public.wipprocessoutcome OWNER TO cell_admin;

--
-- TOC entry 229 (class 1259 OID 16568)
-- Name: wipstatus; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.wipstatus (
    id integer NOT NULL,
    status character varying(100) NOT NULL
);


ALTER TABLE public.wipstatus OWNER TO cell_admin;

--
-- TOC entry 230 (class 1259 OID 16801)
-- Name: flat_cell_view; Type: VIEW; Schema: public; Owner: cell_admin
--

CREATE VIEW public.flat_cell_view AS
 SELECT c.cell_id,
    c.cell_type AS "Cell_Type",
    c.cell_number AS "Cell_number",
    c.cell_name,
    c.description AS "Cell_Description",
    c.doe AS "Cell_DOE",
    c.notes AS "Cell_Notes",
    cd.design_name AS "Cell_Design",
    cb.cell_build_id,
    cb.build_date AS "CellBuild_date",
    cb.cell_builder_name AS "Builder",
    cbs.status AS "CellBuild_status",
    cb.notes AS "Build_Notes",
    lb.layer_build_id,
    lb.build_date AS "Layer_Build_date",
    lb.builder_name AS "Layer_Builder",
    lb.status AS "Layer_Status",
    lb.notes AS "Layer_Notes",
    ml.multi_layer_id,
    ml.layer_type AS "Layer_Type",
    la.assembly_id,
    la.position_in_cell AS "Position_In_Cell",
    la.position_in_component AS "Position_In_Component",
    a.anode_id,
    a.lot_name AS "Anode_Lot",
    a.length_mm AS "Anode_Length_mm",
    a.width_mm AS "Anode_Width_mm",
    a.area_mm2 AS "Anode_Area_mm2",
    cath.cathode_id,
    cath.lot_name AS "Cathode_Lot",
    cath.length_mm AS "Cathode_Length_mm",
    cath.width_mm AS "Cathode_Width_mm",
    cath.area_mm2 AS "Cathode_Area_mm2",
    cath.mass_g AS "Cathode_Weight_g",
    cath.cam_percentage AS "cathode_material_%",
    se.separator_id,
    se.lot_name AS "SE_Lot",
    se.length_mm AS "SE_Length_mm",
    se.width_mm AS "SE_Width_mm",
    se.area_mm2 AS "SE_Area_mm2",
    wpo.outcome_id AS wip_outcome_id,
    wpo.post_wimp_ocv_v AS "Post_WIP_OCV_V",
    wpo.post_wip_impedance_ohms AS "Post_WIP_Impedance_Ω",
    wpo.wip_process_date AS "WIP_Run_Date",
    ws.status AS "WIP_Status",
    wpo.post_wip_anode_length_mm AS "Post_WIP_Anode_Length_mm",
    wpo.post_wip_anode_width_mm AS "Post_WIP_Anode_Width_mm",
    wpo.post_wip_cathode_length_mm AS "Post_WIP_Cathode_Length_mm",
    wpo.post_wip_cathode_width_mm AS "Post_WIP_Cathode_Width_mm",
    wpo.post_wip_se_length_mm AS "Post_WIP_SE_Length_mm",
    wpo.post_wip_se_width_mm AS "Post_WIP_SE_Width_mm",
    co.outcome_id AS clamping_outcome_id,
    co.actual_pressure_mpa AS "clamping_Actual_P_applied_MPa",
    co.actual_load_n AS "Actual_Load_N",
    co.clamping_person AS "Clamp_person",
    co.clamping_date AS "Clamp_Date",
    cs.status AS "Clamping_Status",
    clamp.pad_type AS "Pad_Type",
    clamp.desired_pressure_mpa AS "Desired_Pressure_MPa"
   FROM ((((((((((((((public.cell c
     LEFT JOIN public.celldesign cd ON ((c.cell_design_id = cd.cell_design_id)))
     LEFT JOIN public.cellbuild cb ON ((c.cell_id = cb.cell_id)))
     LEFT JOIN public.cellbuildstatus cbs ON ((cb.cell_build_status_id = cbs.id)))
     LEFT JOIN public.layerassembly la ON ((cb.cell_build_id = la.cell_build_id)))
     LEFT JOIN public.multilayer ml ON ((la.multi_layer_id = ml.multi_layer_id)))
     LEFT JOIN public.layerbuild lb ON ((la.layer_build_id = lb.layer_build_id)))
     LEFT JOIN public.anode a ON ((lb.layer_build_id = a.layer_build_id)))
     LEFT JOIN public.cathode cath ON ((lb.layer_build_id = cath.layer_build_id)))
     LEFT JOIN public.separator se ON ((lb.layer_build_id = se.layer_build_id)))
     LEFT JOIN public.wipprocessoutcome wpo ON ((lb.layer_build_id = wpo.layer_build_id)))
     LEFT JOIN public.wipstatus ws ON ((wpo.wip_status_id = ws.id)))
     LEFT JOIN public.clampingoutcome co ON ((cb.cell_build_id = co.cell_build_id)))
     LEFT JOIN public.clampingstatus cs ON ((co.clamping_status_id = cs.clamping_status_id)))
     LEFT JOIN public.clamping clamp ON ((co.clamping_id = clamp.clamping_id)));


ALTER VIEW public.flat_cell_view OWNER TO cell_admin;

--
-- TOC entry 250 (class 1259 OID 17370)
-- Name: layerassembly_assembly_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.layerassembly_assembly_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.layerassembly_assembly_id_seq OWNER TO cell_admin;

--
-- TOC entry 3789 (class 0 OID 0)
-- Dependencies: 250
-- Name: layerassembly_assembly_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.layerassembly_assembly_id_seq OWNED BY public.layerassembly.assembly_id;


--
-- TOC entry 251 (class 1259 OID 17371)
-- Name: layerbuild_layer_build_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.layerbuild_layer_build_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.layerbuild_layer_build_id_seq OWNER TO cell_admin;

--
-- TOC entry 3790 (class 0 OID 0)
-- Dependencies: 251
-- Name: layerbuild_layer_build_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.layerbuild_layer_build_id_seq OWNED BY public.layerbuild.layer_build_id;


--
-- TOC entry 253 (class 1259 OID 17382)
-- Name: mergedtest_merged_test_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.mergedtest_merged_test_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.mergedtest_merged_test_id_seq OWNER TO cell_admin;

--
-- TOC entry 3791 (class 0 OID 0)
-- Dependencies: 253
-- Name: mergedtest_merged_test_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.mergedtest_merged_test_id_seq OWNED BY public.mergedtest.merged_test_id;


--
-- TOC entry 255 (class 1259 OID 17386)
-- Name: multilayer_multi_layer_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.multilayer_multi_layer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.multilayer_multi_layer_id_seq OWNER TO cell_admin;

--
-- TOC entry 3792 (class 0 OID 0)
-- Dependencies: 255
-- Name: multilayer_multi_layer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.multilayer_multi_layer_id_seq OWNED BY public.multilayer.multi_layer_id;


--
-- TOC entry 256 (class 1259 OID 17387)
-- Name: phaseanalytics; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.phaseanalytics (
    phase_id bigint NOT NULL,
    cycle_id bigint NOT NULL,
    phase_type character varying(50),
    phase_category character varying(50),
    duration double precision,
    capacity_change double precision,
    energy_change double precision,
    average_voltage double precision,
    average_current double precision,
    initial_voltage double precision,
    final_voltage double precision,
    voltage_efficiency double precision,
    start_time timestamp without time zone,
    end_time timestamp without time zone,
    start_index integer,
    end_index integer,
    original_start_row integer,
    original_end_row integer,
    c_rate integer,
    current_std double precision,
    initial_current double precision,
    final_current double precision,
    voltage_std double precision,
    CONSTRAINT phase_type_check CHECK (((phase_type)::text = ANY (ARRAY[('CC_Charge'::character varying)::text, ('CV_Charge'::character varying)::text, ('CC_Discharge'::character varying)::text, ('Rest'::character varying)::text, ('Drive_Cycle'::character varying)::text, ('DCIR_Pulse'::character varying)::text])))
);


ALTER TABLE public.phaseanalytics OWNER TO cell_admin;

--
-- TOC entry 257 (class 1259 OID 17391)
-- Name: phaseanalytics_phase_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.phaseanalytics_phase_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.phaseanalytics_phase_id_seq OWNER TO cell_admin;

--
-- TOC entry 3793 (class 0 OID 0)
-- Dependencies: 257
-- Name: phaseanalytics_phase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.phaseanalytics_phase_id_seq OWNED BY public.phaseanalytics.phase_id;


--
-- TOC entry 258 (class 1259 OID 17392)
-- Name: separator_separator_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.separator_separator_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.separator_separator_id_seq OWNER TO cell_admin;

--
-- TOC entry 3794 (class 0 OID 0)
-- Dependencies: 258
-- Name: separator_separator_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.separator_separator_id_seq OWNED BY public.separator.separator_id;


--
-- TOC entry 260 (class 1259 OID 17403)
-- Name: testfiles_test_file_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.testfiles_test_file_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.testfiles_test_file_id_seq OWNER TO cell_admin;

--
-- TOC entry 3795 (class 0 OID 0)
-- Dependencies: 260
-- Name: testfiles_test_file_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.testfiles_test_file_id_seq OWNED BY public.testfiles.test_file_id;


--
-- TOC entry 262 (class 1259 OID 17408)
-- Name: testhierarchy_hierarchy_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.testhierarchy_hierarchy_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.testhierarchy_hierarchy_id_seq OWNER TO cell_admin;

--
-- TOC entry 3796 (class 0 OID 0)
-- Dependencies: 262
-- Name: testhierarchy_hierarchy_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.testhierarchy_hierarchy_id_seq OWNED BY public.testhierarchy.hierarchy_id;


--
-- TOC entry 270 (class 1259 OID 22241)
-- Name: vw_analytics_pending_processing; Type: VIEW; Schema: public; Owner: cell_admin
--

CREATE VIEW public.vw_analytics_pending_processing AS
 WITH cell_status AS (
         SELECT mt_1.cell_id,
            mt_1.merged_test_id,
            count(tf_1.test_file_id) AS total_files,
            sum(
                CASE
                    WHEN ((fds_1.status)::text = 'COMPLETED'::text) THEN 1
                    ELSE 0
                END) AS completed_downloads,
            sum(
                CASE
                    WHEN ((fds_1.status)::text = 'PENDING'::text) THEN 1
                    ELSE 0
                END) AS pending_downloads,
            sum(
                CASE
                    WHEN ((fds_1.status)::text = 'FAILED'::text) THEN 1
                    ELSE 0
                END) AS failed_downloads,
                CASE
                    WHEN (mta.merged_test_id IS NULL) THEN true
                    ELSE false
                END AS needs_analytics,
            mt_1.merge_status
           FROM (((public.mergedtest mt_1
             JOIN public.testfiles tf_1 ON ((mt_1.merged_test_id = tf_1.merged_test_id)))
             JOIN public.filedownloadstatus fds_1 ON ((tf_1.download_id = fds_1.download_id)))
             LEFT JOIN public.mergedtestanalytics mta ON ((mt_1.merged_test_id = mta.merged_test_id)))
          GROUP BY mt_1.cell_id, mt_1.merged_test_id, mta.merged_test_id, mt_1.merge_status
        )
 SELECT c.cell_id,
    c.cell_name,
    mt.merged_test_id,
    mt.temperature AS test_temperature,
    mt.test_start_date,
    tf.test_file_id,
    tf.file_id,
    tf.hierarchy_id,
    tf.machine_key,
    tf.start_time,
    tf.num_records,
    tf.max_records,
    fds.download_id,
    fds.status AS download_status,
    cd.capacity_mah AS design_capacity_mah,
    COALESCE(cathode_data.active_mass_g, (0)::double precision) AS active_cathode_mass_g,
    ar.status AS last_analysis_status,
    mt.merge_status,
    cs.needs_analytics,
    cs.total_files,
    cs.completed_downloads,
    cs.pending_downloads,
        CASE
            WHEN ((fds.status)::text = 'PENDING'::text) THEN 'pending_download'::text
            WHEN ((mt.merge_status)::text = 'FAILED'::text) THEN 'failed_merge'::text
            WHEN (cs.needs_analytics AND (cs.completed_downloads > 0)) THEN 'needs_analytics'::text
            ELSE 'other'::text
        END AS processing_status
   FROM (((((((public.testfiles tf
     JOIN public.mergedtest mt ON ((tf.merged_test_id = mt.merged_test_id)))
     JOIN public.cell c ON ((mt.cell_id = c.cell_id)))
     LEFT JOIN public.celldesign cd ON ((c.cell_design_id = cd.cell_design_id)))
     JOIN public.filedownloadstatus fds ON ((tf.download_id = fds.download_id)))
     JOIN cell_status cs ON ((mt.merged_test_id = cs.merged_test_id)))
     LEFT JOIN ( SELECT DISTINCT ON (analysisrun.merged_test_id) analysisrun.merged_test_id,
            analysisrun.status,
            analysisrun.started_at
           FROM public.analysisrun
          ORDER BY analysisrun.merged_test_id, analysisrun.started_at DESC) ar ON ((mt.merged_test_id = ar.merged_test_id)))
     LEFT JOIN ( SELECT cb.cell_id,
            ((ca.mass_g * ca.cam_percentage) / (100)::double precision) AS active_mass_g
           FROM ((public.cathode ca
             JOIN public.layerassembly la ON ((ca.layer_build_id = la.layer_build_id)))
             JOIN public.cellbuild cb ON ((la.cell_build_id = cb.cell_build_id)))) cathode_data ON ((c.cell_id = cathode_data.cell_id)))
  WHERE (((fds.status)::text = 'PENDING'::text) OR ((mt.merge_status)::text = 'FAILED'::text) OR (cs.needs_analytics AND (cs.completed_downloads > 0)))
  ORDER BY
        CASE
            WHEN ((fds.status)::text = 'PENDING'::text) THEN 1
            WHEN ((mt.merge_status)::text = 'FAILED'::text) THEN 2
            WHEN (cs.needs_analytics AND (cs.completed_downloads > 0)) THEN 3
            ELSE 4
        END, mt.merged_test_id;


ALTER VIEW public.vw_analytics_pending_processing OWNER TO cell_admin;

--
-- TOC entry 271 (class 1259 OID 22262)
-- Name: vw_cell_layer_structure; Type: MATERIALIZED VIEW; Schema: public; Owner: cell_admin
--

CREATE MATERIALIZED VIEW public.vw_cell_layer_structure AS
 SELECT c.cell_id,
    c.cell_name,
    count(DISTINCT la.assembly_id) AS total_layers,
    count(DISTINCT ml.multi_layer_id) AS multi_layer_components,
    string_agg(DISTINCT (ml.layer_type)::text, ', '::text) AS layer_types,
    count(DISTINCT
        CASE
            WHEN ((ml.layer_type)::text = 'Single'::text) THEN la.assembly_id
            ELSE NULL::integer
        END) AS single_layers,
    count(DISTINCT
        CASE
            WHEN ((ml.layer_type)::text = 'Bilayer'::text) THEN la.assembly_id
            ELSE NULL::integer
        END) AS bilayers,
    count(DISTINCT
        CASE
            WHEN ((ml.layer_type)::text = 'Trilayer'::text) THEN la.assembly_id
            ELSE NULL::integer
        END) AS trilayers,
    max(la.position_in_cell) AS max_position,
    count(DISTINCT a.anode_id) AS anode_count,
    count(DISTINCT ca.cathode_id) AS cathode_count,
    count(DISTINCT s.separator_id) AS separator_count,
    now() AS last_updated
   FROM ((((((public.cell c
     LEFT JOIN public.cellbuild cb ON ((c.cell_id = cb.cell_id)))
     LEFT JOIN public.layerassembly la ON ((cb.cell_build_id = la.cell_build_id)))
     LEFT JOIN public.multilayer ml ON ((la.multi_layer_id = ml.multi_layer_id)))
     LEFT JOIN public.anode a ON ((la.layer_build_id = a.layer_build_id)))
     LEFT JOIN public.cathode ca ON ((la.layer_build_id = ca.layer_build_id)))
     LEFT JOIN public.separator s ON ((la.layer_build_id = s.layer_build_id)))
  GROUP BY c.cell_id, c.cell_name
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.vw_cell_layer_structure OWNER TO cell_admin;

--
-- TOC entry 272 (class 1259 OID 22271)
-- Name: vw_cell_properties; Type: MATERIALIZED VIEW; Schema: public; Owner: cell_admin
--

CREATE MATERIALIZED VIEW public.vw_cell_properties AS
 SELECT c.cell_id,
    c.cell_name,
    c.cell_type,
    c.doe AS experiment_group,
    c.description,
    c.cell_design_id,
    cd.design_name,
    cd.capacity_mah AS design_capacity_mah,
    cd.num_layers,
    COALESCE(sum(((ca.mass_g * ca.cam_percentage) / (100)::double precision)), (0)::double precision) AS total_active_mass_g,
    COALESCE((sum(((ca.mass_g * ca.cam_percentage) / (100)::double precision)) * (0.2)::double precision), (cd.capacity_mah / (1000.0)::double precision)) AS actual_nominal_capacity_ah,
        CASE
            WHEN (sum(ca.mass_g) IS NULL) THEN false
            ELSE true
        END AS has_active_material_data,
    now() AS last_updated
   FROM ((((public.cell c
     LEFT JOIN public.celldesign cd ON ((c.cell_design_id = cd.cell_design_id)))
     LEFT JOIN public.cellbuild cb ON ((c.cell_id = cb.cell_id)))
     LEFT JOIN public.layerassembly la ON ((cb.cell_build_id = la.cell_build_id)))
     LEFT JOIN public.cathode ca ON ((la.layer_build_id = ca.layer_build_id)))
  GROUP BY c.cell_id, c.cell_name, c.cell_type, c.doe, c.description, c.cell_design_id, cd.design_name, cd.capacity_mah, cd.num_layers
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.vw_cell_properties OWNER TO cell_admin;

--
-- TOC entry 263 (class 1259 OID 17409)
-- Name: wipprocess; Type: TABLE; Schema: public; Owner: cell_admin
--

CREATE TABLE public.wipprocess (
    pressurization_id integer NOT NULL,
    pressure_amount double precision NOT NULL,
    duration_seconds integer NOT NULL,
    temperature double precision NOT NULL,
    description text
);


ALTER TABLE public.wipprocess OWNER TO cell_admin;

--
-- TOC entry 264 (class 1259 OID 17414)
-- Name: wipprocess_pressurization_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.wipprocess_pressurization_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wipprocess_pressurization_id_seq OWNER TO cell_admin;

--
-- TOC entry 3797 (class 0 OID 0)
-- Dependencies: 264
-- Name: wipprocess_pressurization_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.wipprocess_pressurization_id_seq OWNED BY public.wipprocess.pressurization_id;


--
-- TOC entry 265 (class 1259 OID 17415)
-- Name: wipprocessoutcome_outcome_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.wipprocessoutcome_outcome_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wipprocessoutcome_outcome_id_seq OWNER TO cell_admin;

--
-- TOC entry 3798 (class 0 OID 0)
-- Dependencies: 265
-- Name: wipprocessoutcome_outcome_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.wipprocessoutcome_outcome_id_seq OWNED BY public.wipprocessoutcome.outcome_id;


--
-- TOC entry 266 (class 1259 OID 17416)
-- Name: wipstatus_id_seq; Type: SEQUENCE; Schema: public; Owner: cell_admin
--

CREATE SEQUENCE public.wipstatus_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.wipstatus_id_seq OWNER TO cell_admin;

--
-- TOC entry 3799 (class 0 OID 0)
-- Dependencies: 266
-- Name: wipstatus_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cell_admin
--

ALTER SEQUENCE public.wipstatus_id_seq OWNED BY public.wipstatus.id;


--
-- TOC entry 3463 (class 2604 OID 17417)
-- Name: analysiserror error_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analysiserror ALTER COLUMN error_id SET DEFAULT nextval('public.analysiserror_error_id_seq'::regclass);


--
-- TOC entry 3465 (class 2604 OID 17418)
-- Name: analysisrun run_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analysisrun ALTER COLUMN run_id SET DEFAULT nextval('public.analysisrun_run_id_seq'::regclass);


--
-- TOC entry 3469 (class 2604 OID 17419)
-- Name: analyticsversion version_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analyticsversion ALTER COLUMN version_id SET DEFAULT nextval('public.analyticsversion_version_id_seq'::regclass);


--
-- TOC entry 3440 (class 2604 OID 17420)
-- Name: anode anode_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.anode ALTER COLUMN anode_id SET DEFAULT nextval('public.anode_anode_id_seq'::regclass);


--
-- TOC entry 3442 (class 2604 OID 17421)
-- Name: cathode cathode_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cathode ALTER COLUMN cathode_id SET DEFAULT nextval('public.cathode_cathode_id_seq'::regclass);


--
-- TOC entry 3445 (class 2604 OID 17422)
-- Name: cell cell_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cell ALTER COLUMN cell_id SET DEFAULT nextval('public.cell_cell_id_seq'::regclass);


--
-- TOC entry 3447 (class 2604 OID 17423)
-- Name: cellbuild cell_build_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cellbuild ALTER COLUMN cell_build_id SET DEFAULT nextval('public.cellbuild_cell_build_id_seq'::regclass);


--
-- TOC entry 3448 (class 2604 OID 17424)
-- Name: cellbuildstatus id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cellbuildstatus ALTER COLUMN id SET DEFAULT nextval('public.cellbuildstatus_id_seq'::regclass);


--
-- TOC entry 3449 (class 2604 OID 17425)
-- Name: celldesign cell_design_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.celldesign ALTER COLUMN cell_design_id SET DEFAULT nextval('public.celldesign_cell_design_id_seq'::regclass);


--
-- TOC entry 3450 (class 2604 OID 17426)
-- Name: clamping clamping_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clamping ALTER COLUMN clamping_id SET DEFAULT nextval('public.clamping_clamping_id_seq'::regclass);


--
-- TOC entry 3451 (class 2604 OID 17427)
-- Name: clampingoutcome outcome_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clampingoutcome ALTER COLUMN outcome_id SET DEFAULT nextval('public.clampingoutcome_outcome_id_seq'::regclass);


--
-- TOC entry 3453 (class 2604 OID 17428)
-- Name: clampingstatus clamping_status_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clampingstatus ALTER COLUMN clamping_status_id SET DEFAULT nextval('public.clampingstatus_clamping_status_id_seq'::regclass);


--
-- TOC entry 3471 (class 2604 OID 17429)
-- Name: cycleanalytics cycle_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cycleanalytics ALTER COLUMN cycle_id SET DEFAULT nextval('public.cycleanalytics_cycle_id_seq'::regclass);


--
-- TOC entry 3472 (class 2604 OID 17430)
-- Name: filedownloadstatus download_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.filedownloadstatus ALTER COLUMN download_id SET DEFAULT nextval('public.filedownloadstatus_download_id_seq'::regclass);


--
-- TOC entry 3454 (class 2604 OID 17431)
-- Name: layerassembly assembly_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerassembly ALTER COLUMN assembly_id SET DEFAULT nextval('public.layerassembly_assembly_id_seq'::regclass);


--
-- TOC entry 3455 (class 2604 OID 17432)
-- Name: layerbuild layer_build_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerbuild ALTER COLUMN layer_build_id SET DEFAULT nextval('public.layerbuild_layer_build_id_seq'::regclass);


--
-- TOC entry 3478 (class 2604 OID 17433)
-- Name: mergedtest merged_test_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.mergedtest ALTER COLUMN merged_test_id SET DEFAULT nextval('public.mergedtest_merged_test_id_seq'::regclass);


--
-- TOC entry 3457 (class 2604 OID 17434)
-- Name: multilayer multi_layer_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.multilayer ALTER COLUMN multi_layer_id SET DEFAULT nextval('public.multilayer_multi_layer_id_seq'::regclass);


--
-- TOC entry 3484 (class 2604 OID 17435)
-- Name: phaseanalytics phase_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.phaseanalytics ALTER COLUMN phase_id SET DEFAULT nextval('public.phaseanalytics_phase_id_seq'::regclass);


--
-- TOC entry 3458 (class 2604 OID 17436)
-- Name: separator separator_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.separator ALTER COLUMN separator_id SET DEFAULT nextval('public.separator_separator_id_seq'::regclass);


--
-- TOC entry 3485 (class 2604 OID 17437)
-- Name: testfiles test_file_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.testfiles ALTER COLUMN test_file_id SET DEFAULT nextval('public.testfiles_test_file_id_seq'::regclass);


--
-- TOC entry 3490 (class 2604 OID 17438)
-- Name: testhierarchy hierarchy_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.testhierarchy ALTER COLUMN hierarchy_id SET DEFAULT nextval('public.testhierarchy_hierarchy_id_seq'::regclass);


--
-- TOC entry 3492 (class 2604 OID 17439)
-- Name: wipprocess pressurization_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocess ALTER COLUMN pressurization_id SET DEFAULT nextval('public.wipprocess_pressurization_id_seq'::regclass);


--
-- TOC entry 3460 (class 2604 OID 17440)
-- Name: wipprocessoutcome outcome_id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocessoutcome ALTER COLUMN outcome_id SET DEFAULT nextval('public.wipprocessoutcome_outcome_id_seq'::regclass);


--
-- TOC entry 3462 (class 2604 OID 17441)
-- Name: wipstatus id; Type: DEFAULT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipstatus ALTER COLUMN id SET DEFAULT nextval('public.wipstatus_id_seq'::regclass);


--
-- TOC entry 3537 (class 2606 OID 17443)
-- Name: analysiserror analysiserror_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analysiserror
    ADD CONSTRAINT analysiserror_pkey PRIMARY KEY (error_id);


--
-- TOC entry 3540 (class 2606 OID 17445)
-- Name: analysisrun analysisrun_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analysisrun
    ADD CONSTRAINT analysisrun_pkey PRIMARY KEY (run_id);


--
-- TOC entry 3546 (class 2606 OID 17447)
-- Name: analyticsversion analyticsversion_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analyticsversion
    ADD CONSTRAINT analyticsversion_pkey PRIMARY KEY (version_id);


--
-- TOC entry 3501 (class 2606 OID 17449)
-- Name: anode anode_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.anode
    ADD CONSTRAINT anode_pkey PRIMARY KEY (anode_id);


--
-- TOC entry 3503 (class 2606 OID 17451)
-- Name: cathode cathode_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cathode
    ADD CONSTRAINT cathode_pkey PRIMARY KEY (cathode_id);


--
-- TOC entry 3505 (class 2606 OID 17453)
-- Name: cell cell_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cell
    ADD CONSTRAINT cell_pkey PRIMARY KEY (cell_id);


--
-- TOC entry 3509 (class 2606 OID 17455)
-- Name: cellbuild cellbuild_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cellbuild
    ADD CONSTRAINT cellbuild_pkey PRIMARY KEY (cell_build_id);


--
-- TOC entry 3512 (class 2606 OID 17457)
-- Name: cellbuildstatus cellbuildstatus_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cellbuildstatus
    ADD CONSTRAINT cellbuildstatus_pkey PRIMARY KEY (id);


--
-- TOC entry 3514 (class 2606 OID 17459)
-- Name: celldesign celldesign_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.celldesign
    ADD CONSTRAINT celldesign_pkey PRIMARY KEY (cell_design_id);


--
-- TOC entry 3516 (class 2606 OID 17461)
-- Name: clamping clamping_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clamping
    ADD CONSTRAINT clamping_pkey PRIMARY KEY (clamping_id);


--
-- TOC entry 3518 (class 2606 OID 17463)
-- Name: clampingoutcome clampingoutcome_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clampingoutcome
    ADD CONSTRAINT clampingoutcome_pkey PRIMARY KEY (outcome_id);


--
-- TOC entry 3520 (class 2606 OID 17465)
-- Name: clampingstatus clampingstatus_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clampingstatus
    ADD CONSTRAINT clampingstatus_pkey PRIMARY KEY (clamping_status_id);


--
-- TOC entry 3548 (class 2606 OID 17467)
-- Name: cycleanalytics cycleanalytics_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cycleanalytics
    ADD CONSTRAINT cycleanalytics_pkey PRIMARY KEY (cycle_id);


--
-- TOC entry 3558 (class 2606 OID 17469)
-- Name: filedownloadstatus filedownloadstatus_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.filedownloadstatus
    ADD CONSTRAINT filedownloadstatus_pkey PRIMARY KEY (download_id);


--
-- TOC entry 3523 (class 2606 OID 17471)
-- Name: layerassembly layer_build_unique_assignment; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerassembly
    ADD CONSTRAINT layer_build_unique_assignment UNIQUE (layer_build_id);


--
-- TOC entry 3525 (class 2606 OID 17473)
-- Name: layerassembly layerassembly_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerassembly
    ADD CONSTRAINT layerassembly_pkey PRIMARY KEY (assembly_id);


--
-- TOC entry 3527 (class 2606 OID 17475)
-- Name: layerbuild layerbuild_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerbuild
    ADD CONSTRAINT layerbuild_pkey PRIMARY KEY (layer_build_id);


--
-- TOC entry 3565 (class 2606 OID 17477)
-- Name: mergedtest mergedtest_cell_id_key; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.mergedtest
    ADD CONSTRAINT mergedtest_cell_id_key UNIQUE (cell_id);


--
-- TOC entry 3567 (class 2606 OID 17479)
-- Name: mergedtest mergedtest_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.mergedtest
    ADD CONSTRAINT mergedtest_pkey PRIMARY KEY (merged_test_id);


--
-- TOC entry 3571 (class 2606 OID 17481)
-- Name: mergedtestanalytics mergedtestanalytics_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.mergedtestanalytics
    ADD CONSTRAINT mergedtestanalytics_pkey PRIMARY KEY (merged_test_id);


--
-- TOC entry 3529 (class 2606 OID 17483)
-- Name: multilayer multilayer_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.multilayer
    ADD CONSTRAINT multilayer_pkey PRIMARY KEY (multi_layer_id);


--
-- TOC entry 3576 (class 2606 OID 17485)
-- Name: phaseanalytics phaseanalytics_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.phaseanalytics
    ADD CONSTRAINT phaseanalytics_pkey PRIMARY KEY (phase_id);


--
-- TOC entry 3531 (class 2606 OID 17487)
-- Name: separator separator_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.separator
    ADD CONSTRAINT separator_pkey PRIMARY KEY (separator_id);


--
-- TOC entry 3585 (class 2606 OID 17489)
-- Name: testfiles testfiles_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.testfiles
    ADD CONSTRAINT testfiles_pkey PRIMARY KEY (test_file_id);


--
-- TOC entry 3588 (class 2606 OID 17491)
-- Name: testhierarchy testhierarchy_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.testhierarchy
    ADD CONSTRAINT testhierarchy_pkey PRIMARY KEY (hierarchy_id);


--
-- TOC entry 3556 (class 2606 OID 17493)
-- Name: cycleanalytics unique_cycle_per_test; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cycleanalytics
    ADD CONSTRAINT unique_cycle_per_test UNIQUE (merged_test_id, cycle_number);


--
-- TOC entry 3578 (class 2606 OID 17495)
-- Name: phaseanalytics unique_phase_per_cycle; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.phaseanalytics
    ADD CONSTRAINT unique_phase_per_cycle UNIQUE (cycle_id, phase_type, start_index, end_index);


--
-- TOC entry 3590 (class 2606 OID 17497)
-- Name: wipprocess wipprocess_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocess
    ADD CONSTRAINT wipprocess_pkey PRIMARY KEY (pressurization_id);


--
-- TOC entry 3533 (class 2606 OID 17499)
-- Name: wipprocessoutcome wipprocessoutcome_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocessoutcome
    ADD CONSTRAINT wipprocessoutcome_pkey PRIMARY KEY (outcome_id);


--
-- TOC entry 3535 (class 2606 OID 17501)
-- Name: wipstatus wipstatus_pkey; Type: CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipstatus
    ADD CONSTRAINT wipstatus_pkey PRIMARY KEY (id);


--
-- TOC entry 3538 (class 1259 OID 17502)
-- Name: idx_analysis_error_category; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_analysis_error_category ON public.analysiserror USING btree (error_category);


--
-- TOC entry 3541 (class 1259 OID 17503)
-- Name: idx_analysis_run_completion; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_analysis_run_completion ON public.analysisrun USING btree (merged_test_id, completed_at DESC);


--
-- TOC entry 3542 (class 1259 OID 17504)
-- Name: idx_analysis_run_merged_test; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_analysis_run_merged_test ON public.analysisrun USING btree (merged_test_id);


--
-- TOC entry 3543 (class 1259 OID 17505)
-- Name: idx_analysis_run_merged_test_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_analysis_run_merged_test_id ON public.analysisrun USING btree (merged_test_id);


--
-- TOC entry 3544 (class 1259 OID 17506)
-- Name: idx_analysis_run_status; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_analysis_run_status ON public.analysisrun USING btree (status);


--
-- TOC entry 3510 (class 1259 OID 17507)
-- Name: idx_cell_build_cell_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cell_build_cell_id ON public.cellbuild USING btree (cell_id);


--
-- TOC entry 3506 (class 1259 OID 17508)
-- Name: idx_cell_cell_name; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cell_cell_name ON public.cell USING btree (cell_name);


--
-- TOC entry 3507 (class 1259 OID 17509)
-- Name: idx_cell_cell_type; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cell_cell_type ON public.cell USING btree (cell_type);


--
-- TOC entry 3549 (class 1259 OID 17510)
-- Name: idx_cycle_analytics_cycle_type; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cycle_analytics_cycle_type ON public.cycleanalytics USING btree (cycle_type);


--
-- TOC entry 3550 (class 1259 OID 17511)
-- Name: idx_cycle_analytics_date; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cycle_analytics_date ON public.cycleanalytics USING btree (merged_test_id, charge_duration DESC);


--
-- TOC entry 3551 (class 1259 OID 17512)
-- Name: idx_cycle_analytics_merged_test_cycle; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cycle_analytics_merged_test_cycle ON public.cycleanalytics USING btree (merged_test_id, cycle_number);


--
-- TOC entry 3552 (class 1259 OID 17513)
-- Name: idx_cycle_analytics_merged_test_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cycle_analytics_merged_test_id ON public.cycleanalytics USING btree (merged_test_id);


--
-- TOC entry 3553 (class 1259 OID 17514)
-- Name: idx_cycle_analytics_merged_test_type; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cycle_analytics_merged_test_type ON public.cycleanalytics USING btree (merged_test_id, cycle_type);


--
-- TOC entry 3554 (class 1259 OID 17515)
-- Name: idx_cycle_merged_test_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_cycle_merged_test_id ON public.cycleanalytics USING btree (merged_test_id);


--
-- TOC entry 3559 (class 1259 OID 17516)
-- Name: idx_download_file_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_download_file_id ON public.filedownloadstatus USING btree (file_id);


--
-- TOC entry 3560 (class 1259 OID 17517)
-- Name: idx_download_status; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_download_status ON public.filedownloadstatus USING btree (status);


--
-- TOC entry 3521 (class 1259 OID 17518)
-- Name: idx_layer_assembly_cell_build_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_layer_assembly_cell_build_id ON public.layerassembly USING btree (cell_build_id);


--
-- TOC entry 3568 (class 1259 OID 17519)
-- Name: idx_merged_test_analytics_last_processed; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_merged_test_analytics_last_processed ON public.mergedtestanalytics USING btree (last_processed_timestamp);


--
-- TOC entry 3569 (class 1259 OID 17520)
-- Name: idx_merged_test_analytics_merged_test_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_merged_test_analytics_merged_test_id ON public.mergedtestanalytics USING btree (merged_test_id);


--
-- TOC entry 3561 (class 1259 OID 17521)
-- Name: idx_merged_test_cell; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_merged_test_cell ON public.mergedtest USING btree (cell_id);


--
-- TOC entry 3562 (class 1259 OID 17522)
-- Name: idx_merged_test_cell_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_merged_test_cell_id ON public.mergedtest USING btree (cell_id);


--
-- TOC entry 3563 (class 1259 OID 17523)
-- Name: idx_merged_test_status; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_merged_test_status ON public.mergedtest USING btree (merge_status);


--
-- TOC entry 3572 (class 1259 OID 17524)
-- Name: idx_phase_analytics_cycle_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_phase_analytics_cycle_id ON public.phaseanalytics USING btree (cycle_id);


--
-- TOC entry 3573 (class 1259 OID 17525)
-- Name: idx_phase_analytics_type; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_phase_analytics_type ON public.phaseanalytics USING btree (cycle_id, phase_type, phase_category);


--
-- TOC entry 3574 (class 1259 OID 17526)
-- Name: idx_phase_cycle_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_phase_cycle_id ON public.phaseanalytics USING btree (cycle_id);


--
-- TOC entry 3579 (class 1259 OID 17527)
-- Name: idx_test_files_hierarchy; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_test_files_hierarchy ON public.testfiles USING btree (hierarchy_id);


--
-- TOC entry 3580 (class 1259 OID 17528)
-- Name: idx_test_files_machine_key; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_test_files_machine_key ON public.testfiles USING btree (machine_key);


--
-- TOC entry 3581 (class 1259 OID 17529)
-- Name: idx_test_files_merged_test; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_test_files_merged_test ON public.testfiles USING btree (merged_test_id);


--
-- TOC entry 3582 (class 1259 OID 17530)
-- Name: idx_test_files_merged_test_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_test_files_merged_test_id ON public.testfiles USING btree (merged_test_id);


--
-- TOC entry 3583 (class 1259 OID 17531)
-- Name: idx_test_files_status; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_test_files_status ON public.testfiles USING btree (merge_status);


--
-- TOC entry 3586 (class 1259 OID 17532)
-- Name: idx_test_hierarchy_barcode; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_test_hierarchy_barcode ON public.testhierarchy USING btree (base_barcode);


--
-- TOC entry 3591 (class 1259 OID 22269)
-- Name: idx_vw_cell_layer_properties_cell_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_vw_cell_layer_properties_cell_id ON public.vw_cell_layer_structure USING btree (cell_id);


--
-- TOC entry 3592 (class 1259 OID 22278)
-- Name: idx_vw_cell_properties_cell_id; Type: INDEX; Schema: public; Owner: cell_admin
--

CREATE INDEX idx_vw_cell_properties_cell_id ON public.vw_cell_properties USING btree (cell_id);


--
-- TOC entry 3609 (class 2606 OID 17533)
-- Name: analysiserror analysis_error_run_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analysiserror
    ADD CONSTRAINT analysis_error_run_fk FOREIGN KEY (run_id) REFERENCES public.analysisrun(run_id);


--
-- TOC entry 3610 (class 2606 OID 17538)
-- Name: analysisrun analysis_run_merged_test_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analysisrun
    ADD CONSTRAINT analysis_run_merged_test_fk FOREIGN KEY (merged_test_id) REFERENCES public.mergedtest(merged_test_id);


--
-- TOC entry 3611 (class 2606 OID 17543)
-- Name: analysisrun analysis_run_version_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.analysisrun
    ADD CONSTRAINT analysis_run_version_fk FOREIGN KEY (version_id) REFERENCES public.analyticsversion(version_id);


--
-- TOC entry 3593 (class 2606 OID 17548)
-- Name: anode anode_layerbuild_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.anode
    ADD CONSTRAINT anode_layerbuild_fk FOREIGN KEY (layer_build_id) REFERENCES public.layerbuild(layer_build_id);


--
-- TOC entry 3594 (class 2606 OID 17553)
-- Name: cathode cathode_layerbuild_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cathode
    ADD CONSTRAINT cathode_layerbuild_fk FOREIGN KEY (layer_build_id) REFERENCES public.layerbuild(layer_build_id);


--
-- TOC entry 3595 (class 2606 OID 17558)
-- Name: cell cell_celldesign_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cell
    ADD CONSTRAINT cell_celldesign_fk FOREIGN KEY (cell_design_id) REFERENCES public.celldesign(cell_design_id);


--
-- TOC entry 3596 (class 2606 OID 17563)
-- Name: cellbuild cellbuild_cell_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cellbuild
    ADD CONSTRAINT cellbuild_cell_fk FOREIGN KEY (cell_id) REFERENCES public.cell(cell_id);


--
-- TOC entry 3597 (class 2606 OID 17568)
-- Name: cellbuild cellbuild_cellbuildstatus_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cellbuild
    ADD CONSTRAINT cellbuild_cellbuildstatus_fk FOREIGN KEY (cell_build_status_id) REFERENCES public.cellbuildstatus(id);


--
-- TOC entry 3598 (class 2606 OID 17573)
-- Name: clampingoutcome clampingoutcome_cellbuild_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clampingoutcome
    ADD CONSTRAINT clampingoutcome_cellbuild_fk FOREIGN KEY (cell_build_id) REFERENCES public.cellbuild(cell_build_id);


--
-- TOC entry 3599 (class 2606 OID 17578)
-- Name: clampingoutcome clampingoutcome_clamping_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clampingoutcome
    ADD CONSTRAINT clampingoutcome_clamping_fk FOREIGN KEY (clamping_id) REFERENCES public.clamping(clamping_id);


--
-- TOC entry 3600 (class 2606 OID 17583)
-- Name: clampingoutcome clampingoutcome_clampingstatus_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.clampingoutcome
    ADD CONSTRAINT clampingoutcome_clampingstatus_fk FOREIGN KEY (clamping_status_id) REFERENCES public.clampingstatus(clamping_status_id);


--
-- TOC entry 3612 (class 2606 OID 17588)
-- Name: cycleanalytics cycle_merged_test_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.cycleanalytics
    ADD CONSTRAINT cycle_merged_test_fk FOREIGN KEY (merged_test_id) REFERENCES public.mergedtest(merged_test_id);


--
-- TOC entry 3601 (class 2606 OID 17593)
-- Name: layerassembly layerassembly_cellbuild_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerassembly
    ADD CONSTRAINT layerassembly_cellbuild_fk FOREIGN KEY (cell_build_id) REFERENCES public.cellbuild(cell_build_id);


--
-- TOC entry 3602 (class 2606 OID 17598)
-- Name: layerassembly layerassembly_layerbuild_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerassembly
    ADD CONSTRAINT layerassembly_layerbuild_fk FOREIGN KEY (layer_build_id) REFERENCES public.layerbuild(layer_build_id);


--
-- TOC entry 3603 (class 2606 OID 17603)
-- Name: layerassembly layerassembly_multilayer_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.layerassembly
    ADD CONSTRAINT layerassembly_multilayer_fk FOREIGN KEY (multi_layer_id) REFERENCES public.multilayer(multi_layer_id);


--
-- TOC entry 3614 (class 2606 OID 17608)
-- Name: mergedtestanalytics merged_test_analytics_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.mergedtestanalytics
    ADD CONSTRAINT merged_test_analytics_fk FOREIGN KEY (merged_test_id) REFERENCES public.mergedtest(merged_test_id);


--
-- TOC entry 3613 (class 2606 OID 17613)
-- Name: mergedtest merged_test_cell_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.mergedtest
    ADD CONSTRAINT merged_test_cell_fk FOREIGN KEY (cell_id) REFERENCES public.cell(cell_id);


--
-- TOC entry 3615 (class 2606 OID 17618)
-- Name: phaseanalytics phase_cycle_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.phaseanalytics
    ADD CONSTRAINT phase_cycle_fk FOREIGN KEY (cycle_id) REFERENCES public.cycleanalytics(cycle_id);


--
-- TOC entry 3604 (class 2606 OID 17623)
-- Name: separator separator_layerbuild_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.separator
    ADD CONSTRAINT separator_layerbuild_fk FOREIGN KEY (layer_build_id) REFERENCES public.layerbuild(layer_build_id);


--
-- TOC entry 3616 (class 2606 OID 17628)
-- Name: testfiles test_files_download_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.testfiles
    ADD CONSTRAINT test_files_download_fk FOREIGN KEY (download_id) REFERENCES public.filedownloadstatus(download_id);


--
-- TOC entry 3617 (class 2606 OID 17633)
-- Name: testfiles test_files_hierarchy_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.testfiles
    ADD CONSTRAINT test_files_hierarchy_fk FOREIGN KEY (hierarchy_id) REFERENCES public.testhierarchy(hierarchy_id);


--
-- TOC entry 3618 (class 2606 OID 17638)
-- Name: testfiles test_files_merged_test_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.testfiles
    ADD CONSTRAINT test_files_merged_test_fk FOREIGN KEY (merged_test_id) REFERENCES public.mergedtest(merged_test_id);


--
-- TOC entry 3605 (class 2606 OID 24811)
-- Name: wipprocessoutcome wipprocessoutcome_layerassembly_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocessoutcome
    ADD CONSTRAINT wipprocessoutcome_layerassembly_fk FOREIGN KEY (assembly_id) REFERENCES public.layerassembly(assembly_id);


--
-- TOC entry 3606 (class 2606 OID 17643)
-- Name: wipprocessoutcome wipprocessoutcome_layerbuild_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocessoutcome
    ADD CONSTRAINT wipprocessoutcome_layerbuild_fk FOREIGN KEY (layer_build_id) REFERENCES public.layerbuild(layer_build_id);


--
-- TOC entry 3607 (class 2606 OID 17648)
-- Name: wipprocessoutcome wipprocessoutcome_wipprocess_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocessoutcome
    ADD CONSTRAINT wipprocessoutcome_wipprocess_fk FOREIGN KEY (pressurization_id) REFERENCES public.wipprocess(pressurization_id);


--
-- TOC entry 3608 (class 2606 OID 17653)
-- Name: wipprocessoutcome wipprocessoutcome_wipstatus_fk; Type: FK CONSTRAINT; Schema: public; Owner: cell_admin
--

ALTER TABLE ONLY public.wipprocessoutcome
    ADD CONSTRAINT wipprocessoutcome_wipstatus_fk FOREIGN KEY (wip_status_id) REFERENCES public.wipstatus(id);


-- Completed on 2025-03-12 09:31:50 EDT

--
-- PostgreSQL database dump complete
--

