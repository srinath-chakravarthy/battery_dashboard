import panel as pn


def create_extensions():
    pn.extension(raw_css=["""
        /* Modern Design System Variables */
        :root {
            --primary-blue: #4F78FF;
            --primary-blue-dark: #3B5EDB;
            --success-green: #10B981;
            --warning-orange: #F59E0B;
            --danger-red: #EF4444;
            --text-primary: #1F2937;
            --text-secondary: #6B7280;
            --text-muted: #9CA3AF;
            --bg-primary: #FFFFFF;
            --bg-secondary: #F9FAFB;
            --bg-tertiary: #F3F4F6;
            --border-light: #E5E7EB;
            --border-medium: #D1D5DB;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --radius-sm: 6px;
            --radius-md: 8px;
            --radius-lg: 12px;
        }

        /* Dark theme variables */
        [data-theme="dark"] {
            --text-primary: #F9FAFB;
            --text-secondary: #D1D5DB;
            --text-muted: #9CA3AF;
            --bg-primary: #111827;
            --bg-secondary: #1F2937;
            --bg-tertiary: #374151;
            --border-light: #374151;
            --border-medium: #4B5563;
        }

        /* Global Styles */
        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            color: var(--text-primary);
            background-color: var(--bg-primary);
            line-height: 1.5;
        }

        /* Header Styling */
        .dashboard-header {
            background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-dark) 100%);
            padding: 16px 24px;
            box-shadow: var(--shadow-md);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .dashboard-title {
            color: white !important;
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .status-badge {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 4px 12px;
            border-radius: var(--radius-sm);
            font-size: 0.875rem;
            font-weight: 500;
            backdrop-filter: blur(10px);
        }

        /* Tab Navigation */
        .bk-header.bk-tab {
            background: var(--bg-primary) !important;
            border: 1px solid var(--border-light) !important;
            border-bottom: none !important;
            color: var(--text-secondary) !important;
            font-weight: 500;
            padding: 12px 24px !important;
            border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
            transition: all 0.2s ease;
        }

        .bk-header.bk-tab:hover {
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
        }

        .bk-header.bk-tab.bk-active {
            background: var(--primary-blue) !important;
            color: white !important;
            border-color: var(--primary-blue) !important;
            box-shadow: var(--shadow-sm);
        }

        /* Modern Cards */
        .modern-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            padding: 0;
            overflow: hidden;
            transition: box-shadow 0.2s ease;
        }

        .modern-card:hover {
            box-shadow: var(--shadow-md);
        }

        .card-header {
            background: var(--bg-secondary);
            padding: 16px 20px;
            border-bottom: 1px solid var(--border-light);
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-content {
            padding: 20px;
        }

        /* Sidebar Styling */
        .sidebar {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-light);
            padding: 20px;
            min-height: 100vh;
        }

        .sidebar-section {
            margin-bottom: 24px;
        }

        .sidebar-title {
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.025em;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Modern Form Controls */
        .bk-input, select, .bk-input-group .bk-input {
            border: 1px solid var(--border-medium) !important;
            border-radius: var(--radius-md) !important;
            padding: 8px 12px !important;
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            font-size: 0.875rem;
            transition: all 0.2s ease;
        }

        .bk-input:focus, select:focus {
            border-color: var(--primary-blue) !important;
            box-shadow: 0 0 0 3px rgba(79, 120, 255, 0.1) !important;
            outline: none !important;
        }

        /* Modern Buttons */
        .bk-btn {
            border-radius: var(--radius-md) !important;
            font-weight: 500;
            padding: 8px 16px !important;
            border: none !important;
            transition: all 0.2s ease;
            font-size: 0.875rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .bk-btn-primary {
            background: var(--primary-blue) !important;
            color: white !important;
        }

        .bk-btn-primary:hover {
            background: var(--primary-blue-dark) !important;
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }

        .bk-btn-success {
            background: var(--success-green) !important;
            color: white !important;
        }

        .bk-btn-default {
            background: var(--bg-primary) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-medium) !important;
        }

        .bk-btn-default:hover {
            background: var(--bg-secondary) !important;
        }

        /* Search Bar */
        .search-container {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
            align-items: center;
        }

        .search-input {
            flex: 1;
            position: relative;
        }

        .search-input .bk-input {
            padding-left: 40px !important;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236B7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'/%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: 12px center;
            background-size: 16px 16px;
        }

        /* Table Styling */
        .tabulator {
            border: 1px solid var(--border-light) !important;
            border-radius: var(--radius-lg) !important;
            overflow: hidden;
            background: var(--bg-primary) !important;
            box-shadow: var(--shadow-sm);
        }

        .tabulator .tabulator-header {
            background: var(--bg-secondary) !important;
            border-bottom: 1px solid var(--border-light) !important;
        }

        .tabulator .tabulator-header .tabulator-col {
            background: transparent !important;
            border-right: 1px solid var(--border-light) !important;
            color: var(--text-primary) !important;
            font-weight: 600;
            font-size: 0.875rem;
            padding: 12px 16px !important;
        }

        .tabulator .tabulator-row {
            border-bottom: 1px solid var(--border-light) !important;
            background: var(--bg-primary) !important;
            transition: background-color 0.15s ease;
        }

        .tabulator .tabulator-row:hover {
            background: var(--bg-secondary) !important;
        }

        .tabulator .tabulator-row.tabulator-selected {
            background: rgba(79, 120, 255, 0.05) !important;
        }

        .tabulator .tabulator-cell {
            padding: 12px 16px !important;
            color: var(--text-primary) !important;
            font-size: 0.875rem;
            border-right: 1px solid var(--border-light) !important;
        }

        /* Status Indicators */
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .status-active { background-color: var(--success-green); }
        .status-testing { background-color: var(--warning-orange); }
        .status-degraded { background-color: var(--danger-red); }

        /* Statistics Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-md);
            padding: 16px;
            text-align: center;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--primary-blue);
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
        }

        /* Selection Controls */
        .selection-controls {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 16px;
        }

        .selection-count {
            background: var(--bg-secondary);
            padding: 8px 12px;
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-primary);
        }

        /* Load Button Special Styling */
        .load-button {
            background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-dark) 100%) !important;
            border: none !important;
            color: white !important;
            padding: 12px 24px !important;
            font-weight: 600;
            border-radius: var(--radius-md) !important;
            box-shadow: var(--shadow-md);
            transition: all 0.2s ease;
        }

        .load-button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .load-button:disabled {
            background: var(--text-muted) !important;
            cursor: not-allowed;
            transform: none !important;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .dashboard-header {
                padding: 12px 16px;
            }

            .sidebar {
                padding: 16px;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Animation for loading states */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border-medium);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-muted);
        }
    """])