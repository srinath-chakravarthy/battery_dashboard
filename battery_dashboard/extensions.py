import panel as pn

# def create_extensions():
#     pn.extension(raw_css=["""
#         /* Make checkboxes significantly larger and more visible */
#         .tabulator .tabulator-cell input[type="checkbox"],
#         .tabulator .tabulator-header-contents input[type="checkbox"] {
#             width: 24px !important;
#             height: 24px !important;
#             transform: scale(1.5) !important;
#             cursor: pointer !important;
#             display: block !important;
#             margin: 0 auto !important;
#             opacity: 1 !important;
#             visibility: visible !important;
#         }
#
#         /* Add a clear border to separate the checkbox column from other columns */
#         .tabulator .tabulator-cell.tabulator-row-handle,
#         .tabulator .tabulator-header .tabulator-col.tabulator-row-handle {
#             border-right: 2px solid #999 !important;
#             background-color: #f8f8f8 !important; /* Subtle background difference */
#             padding: 10px 15px !important;
#             min-width: 40px !important;
#         }
#
#         /* Style for the checkbox cell when selected */
#         .tabulator .tabulator-row.tabulator-selected .tabulator-cell.tabulator-row-handle {
#             background-color: #e0e8ff !important; /* Different background when selected */
#         }
#
#         /* Add a visible border to make checkboxes stand out */
#         .tabulator input[type="checkbox"] {
#             border: 2px solid #666 !important;
#             border-radius: 3px !important;
#             background-color: white !important;
#         }
#     """])

def create_extensions():
    pn.extension(raw_css=["""
        /* Light theme variables */
        :root {
            --primary-color: #3B82F6;
            --primary-dark: #2563EB;
            --secondary-color: #F8FAFC;
            --text-color: #334155;
            --border-color: #E2E8F0;
            --sidebar-bg: #F8FAFC;
            --card-bg: white;
            --success-color: #10B981;
            --warning-color: #F59E0B;
            --danger-color: #EF4444;
            --table-header-bg: #F8FAFC;
            --table-row-hover: rgba(0, 0, 0, 0.02);
            --table-selected-bg: rgba(59, 130, 246, 0.1);
            --table-selected-hover: rgba(59, 130, 246, 0.15);
            --body-bg: #FFFFFF;
            --card-header-bg: #F8FAFC;
            --header-bg: #3B82F6;
            --footer-bg: #F1F5F9;
            --footer-text: #64748B;
        }

        /* Dark theme variables - applied when [data-theme="dark"] */
        [data-theme="dark"] {
            --primary-color: #3B82F6;
            --primary-dark: #2563EB;
            --secondary-color: #1E293B;
            --text-color: #E2E8F0;
            --border-color: #334155;
            --sidebar-bg: #1E293B;
            --card-bg: #0F172A;
            --success-color: #10B981;
            --warning-color: #F59E0B;
            --danger-color: #EF4444;
            --table-header-bg: #1E293B;
            --table-row-hover: rgba(255, 255, 255, 0.05);
            --table-selected-bg: rgba(59, 130, 246, 0.2);
            --table-selected-hover: rgba(59, 130, 246, 0.25);
            --body-bg: #0F172A;
            --card-header-bg: #1E293B;
            --header-bg: #1E293B;
            --footer-bg: #1E293B;
            --footer-text: #94A3B8;
        }

        /* Apply the variables */
        body {
            color: var(--text-color);
            background-color: var(--body-bg);
        }

        /* Card styling */
        .bk-card {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            background-color: var(--card-bg);
        }

        .bk-card-header {
            padding: 0.75rem 1.25rem;
            font-weight: 600;
            background-color: var(--card-header-bg);
            color: var(--text-color);
        }

        /* Table styling */
        .tabulator {
            border: 1px solid var(--border-color) !important;
            border-radius: 6px;
            overflow: hidden;
            background-color: var(--card-bg) !important;
        }

        .tabulator .tabulator-header {
            background-color: var(--table-header-bg) !important;
            border-bottom: 2px solid var(--border-color) !important;
        }

        .tabulator .tabulator-header .tabulator-col {
            background-color: var(--table-header-bg) !important;
            border-right: 1px solid var(--border-color) !important;
            color: var(--text-color) !important;
        }

        .tabulator .tabulator-row {
            border-bottom: 1px solid var(--border-color) !important;
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
        }

        .tabulator .tabulator-row:hover {
            background-color: var(--table-row-hover) !important;
        }

        .tabulator .tabulator-row.tabulator-selected {
            background-color: var(--table-selected-bg) !important;
        }

        .tabulator .tabulator-row.tabulator-selected:hover {
            background-color: var(--table-selected-hover) !important;
        }

        /* Make checkboxes significantly larger and more visible */
        .tabulator .tabulator-cell input[type="checkbox"],
        .tabulator .tabulator-header-contents input[type="checkbox"] {
            width: 18px !important;
            height: 18px !important;
            transform: scale(1.2) !important;
            cursor: pointer !important;
            display: block !important;
            margin: 0 auto !important;
            opacity: 1 !important;
            visibility: visible !important;
        }

        /* Checkbox column styling */
        .tabulator .tabulator-cell.tabulator-row-handle,
        .tabulator .tabulator-header .tabulator-col.tabulator-row-handle {
            border-right: 1px solid var(--border-color) !important;
            background-color: var(--table-header-bg) !important;
            padding: 10px 15px !important;
            min-width: 40px !important;
        }

        /* Style for the checkbox cell when selected */
        .tabulator .tabulator-row.tabulator-selected .tabulator-cell.tabulator-row-handle {
            background-color: var(--table-selected-bg) !important;
        }

        /* Button styling */
        button.bk-btn {
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        button.bk-btn-primary {
            background-color: var(--primary-color) !important;
            border-color: var(--primary-color) !important;
        }

        button.bk-btn-primary:hover {
            background-color: var(--primary-dark) !important;
            border-color: var(--primary-dark) !important;
        }

        /* Widget styling */
        .bk-input {
            border-radius: 6px !important;
            border: 1px solid var(--border-color) !important;
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
        }

        .bk-input:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25) !important;
        }

        /* Sidebar styling */
        .sidebar {
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            padding: 1rem;
        }

        /* Status indicators */
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 6px;
        }

        .status-success {
            background-color: var(--success-color);
        }

        .status-warning {
            background-color: var(--warning-color);
        }

        .status-danger {
            background-color: var(--danger-color);
        }

        /* Theme toggle styling */
        .theme-toggle {
            margin-left: auto;
        }

        /* Make sure text is properly colored in markdown components */
        .markdown {
            color: var(--text-color);
        }

        /* Ensure select, dropdown menus are themed */
        select, .bk-menu {
            background-color: var(--card-bg) !important;
            color: var(--text-color) !important;
            border-color: var(--border-color) !important;
        }

        /* Style tabs to match theme */
        .bk-header.bk-tab {
            background-color: var(--sidebar-bg) !important;
            color: var(--text-color) !important;
            border-color: var(--border-color) !important;
        }

        .bk-header.bk-tab.bk-active {
            background-color: var(--primary-color) !important;
            color: white !important;
        }
    """])