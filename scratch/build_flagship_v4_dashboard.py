import json, os, zipfile, xml.etree.ElementTree as ET

# Load Data
json_daily_path = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch\telemetry_daily_data.json'
with open(json_daily_path, 'r', encoding='utf-8') as f:
    daily_data = json.load(f)

path_monthly = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\ปริมาณการใช้ O2_มีนาคม2569.xlsx'
rows_m = []
with zipfile.ZipFile(path_monthly) as z:
    sheets = [f for f in z.namelist() if f.startswith('xl/worksheets/sheet')]
    shared_strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
        shared_strings = [elem.text for elem in tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t')]
    
    for s in sheets:
        stree = ET.fromstring(z.read(s))
        rows = stree.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
        for r in rows:
            row_data = []
            for c in r.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                t = c.attrib.get('t')
                v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                val = v.text if v is not None else ''
                if t == 's' and val.isdigit():
                    val = shared_strings[int(val)] if int(val) < len(shared_strings) else val
                row_data.append(val)
            rows_m.append(row_data)

months_list, nkp_m_vals, khon_m_vals, total_m_vals = [], [], [], []
for r in rows_m[2:]:
    if len(r) >= 4 and r[0]:
        m = r[0].strip()
        nkp = float(r[1]) if r[1] else 0.0
        khon = float(r[2]) if r[2] else 0.0
        tot = float(r[3]) if r[3] else nkp + khon
        months_list.append(m)
        nkp_m_vals.append(round(nkp, 2))
        khon_m_vals.append(round(khon, 2))
        total_m_vals.append(round(tot, 2))

master_data = {
    'monthly': {
        'months': months_list,
        'nkp_m3': nkp_m_vals,
        'khon_m3': khon_m_vals,
        'total_m3': total_m_vals,
        'avg_total_m3': round(sum(total_m_vals)/len(total_m_vals), 2),
        'max_m3': max(total_m_vals),
        'max_month': months_list[total_m_vals.index(max(total_m_vals))],
        'min_m3': min(total_m_vals),
        'min_month': months_list[total_m_vals.index(min(total_m_vals))]
    },
    'daily': daily_data
}

html_v4_code = f"""<!DOCTYPE html>
<html lang="th" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NKP Medical Oxygen Analytics Dashboard V4</title>
    <!-- Fonts & Icons & Chart.js -->
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>

    <style>
        /* Modern Theme Color Palette */
        :root[data-theme="dark"] {{
            --bg-body: #070b14;
            --bg-sidebar: #0e1626;
            --bg-card: rgba(20, 30, 48, 0.75);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary-cyan: #06b6d4;
            --accent-emerald: #10b981;
            --accent-purple: #a855f7;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --table-header-bg: rgba(15, 23, 42, 0.95);
            --input-bg: rgba(30, 41, 59, 0.8);
            --shadow-color: rgba(0, 0, 0, 0.4);
        }}

        :root[data-theme="light"] {{
            --bg-body: #f1f5f9;
            --bg-sidebar: #ffffff;
            --bg-card: #ffffff;
            --border-color: #e2e8f0;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary-cyan: #0284c7;
            --accent-emerald: #059669;
            --accent-purple: #7e22ce;
            --accent-amber: #d97706;
            --accent-rose: #e11d48;
            --table-header-bg: #e2e8f0;
            --input-bg: #ffffff;
            --shadow-color: rgba(0, 0, 0, 0.08);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Prompt', sans-serif;
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease, width 0.3s ease;
        }}

        body {{
            background: var(--bg-body);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            overflow-x: hidden;
        }}

        /* Collapsible Left Sidebar Layout */
        .sidebar {{
            width: 290px;
            background: var(--bg-sidebar);
            border-right: 1px solid var(--border-color);
            padding: 1.25rem 0.85rem;
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
            position: sticky;
            top: 0;
            height: 100vh;
            z-index: 100;
            box-shadow: 4px 0 20px var(--shadow-color);
        }}

        /* Collapsed Mini Sidebar Mode */
        .sidebar.collapsed {{
            width: 78px;
        }}

        .sidebar-brand {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 1.25rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 1.25rem;
        }}

        .brand-info {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            overflow: hidden;
        }}

        .brand-logo {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--primary-cyan), var(--accent-emerald));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 1.4rem;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.35);
            flex-shrink: 0;
        }}

        .brand-text {{
            white-space: nowrap;
        }}

        .sidebar.collapsed .brand-text {{
            display: none;
        }}

        .brand-text h2 {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-main);
        }}

        .brand-text p {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        /* Sidebar Expand / Collapse Toggle Button */
        .sidebar-toggle-btn {{
            background: rgba(6, 182, 212, 0.12);
            border: 1px solid var(--primary-cyan);
            color: var(--primary-cyan);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            transition: transform 0.2s ease;
        }}

        .sidebar-toggle-btn:hover {{
            background: var(--primary-cyan);
            color: #000000;
        }}

        .sidebar-menu {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex-grow: 1;
        }}

        .menu-item {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.85rem 1rem;
            font-size: 0.92rem;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.9rem;
            text-align: left;
            width: 100%;
            white-space: nowrap;
            position: relative;
        }}

        .menu-item i {{
            font-size: 1.25rem;
            width: 26px;
            text-align: center;
            flex-shrink: 0;
        }}

        .menu-item span {{
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .sidebar.collapsed .menu-item span {{
            display: none;
        }}

        .sidebar.collapsed .menu-item {{
            justify-content: center;
            padding: 0.85rem 0;
        }}

        .menu-item:hover {{
            background: rgba(6, 182, 212, 0.12);
            color: var(--primary-cyan);
            transform: translateX(4px);
        }}

        .sidebar.collapsed .menu-item:hover {{
            transform: scale(1.08);
        }}

        .menu-item.active {{
            background: linear-gradient(135deg, var(--primary-cyan), #0284c7);
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.35);
        }}

        .sidebar-footer {{
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            font-size: 0.75rem;
            color: var(--text-muted);
            text-align: center;
            line-height: 1.4;
            white-space: nowrap;
            overflow: hidden;
        }}

        .sidebar.collapsed .sidebar-footer {{
            display: none;
        }}

        /* Main Content Layout */
        .main-wrapper {{
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}

        /* Top Header Bar */
        .top-header {{
            background: var(--bg-sidebar);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 90;
            box-shadow: 0 4px 15px var(--shadow-color);
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .header-title-box h1 {{
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-main);
        }}

        .header-title-box p {{
            font-size: 0.82rem;
            color: var(--text-muted);
        }}

        .header-controls {{
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }}

        /* Top Right Live Clock Container */
        .live-clock-card {{
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.12), rgba(16, 185, 129, 0.12));
            border: 1px solid var(--primary-cyan);
            border-radius: 12px;
            padding: 0.45rem 1rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .clock-icon {{
            font-size: 1.4rem;
            color: var(--primary-cyan);
        }}

        .clock-time {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--text-main);
            font-family: monospace;
        }}

        .clock-date {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        /* Theme Toggle Button */
        .theme-toggle-btn {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 0.5rem 0.9rem;
            border-radius: 10px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .theme-toggle-btn:hover {{
            border-color: var(--primary-cyan);
            color: var(--primary-cyan);
        }}

        .content-body {{
            padding: 1.75rem 2rem;
            flex-grow: 1;
        }}

        /* Dynamic KPI Cards */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }}

        .kpi-card {{
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            position: relative;
            box-shadow: 0 4px 15px var(--shadow-color);
        }}

        .kpi-card:hover {{
            transform: translateY(-3px);
        }}

        .kpi-icon {{
            position: absolute;
            top: 1.25rem;
            right: 1.25rem;
            font-size: 1.8rem;
            opacity: 0.3;
        }}

        .kpi-label {{
            color: var(--text-muted);
            font-size: 0.88rem;
            font-weight: 500;
        }}

        .kpi-value {{
            font-size: 1.9rem;
            font-weight: 700;
            margin: 0.3rem 0;
        }}

        .kpi-subtext {{
            font-size: 0.82rem;
            color: var(--text-muted);
        }}

        /* Content Sections */
        .content-card {{
            background: var(--bg-card);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px var(--shadow-color);
        }}

        .section-title {{
            font-size: 1.15rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}

        /* Unit Control Group */
        .unit-selector {{
            display: flex;
            background: var(--bg-body);
            padding: 0.25rem;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .btn-unit {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.4rem 0.9rem;
            font-size: 0.85rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
        }}

        .btn-unit.active {{
            background: var(--primary-cyan);
            color: #ffffff;
            font-weight: 600;
        }}

        .chart-container {{
            position: relative;
            height: 420px;
            width: 100%;
        }}

        /* Calculator Styles */
        .calc-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
        }}

        .calc-box {{
            background: var(--bg-body);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 1.5rem;
        }}

        .form-group {{
            margin-bottom: 1.25rem;
        }}

        .form-label {{
            display: block;
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 0.4rem;
            font-weight: 500;
        }}

        .form-control {{
            width: 100%;
            background: var(--input-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.65rem 1rem;
            color: var(--text-main);
            font-size: 1rem;
            outline: none;
        }}

        .res-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px dashed var(--border-color);
        }}

        .res-label {{
            font-size: 0.92rem;
            color: var(--text-muted);
        }}

        .res-val {{
            font-size: 1.15rem;
            font-weight: 700;
            color: var(--primary-cyan);
        }}

        .table-wrapper {{
            overflow-x: auto;
            max-height: 420px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }}

        th {{
            background: var(--table-header-bg);
            color: var(--primary-cyan);
            padding: 0.85rem 1rem;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 1px solid var(--border-color);
        }}

        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
        }}

        tr:hover td {{
            background: rgba(6, 182, 212, 0.04);
        }}

        .tag-peak {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--accent-amber);
            border: 1px solid var(--accent-amber);
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            font-size: 0.75rem;
        }}

        .drop-zone {{
            border: 2px dashed var(--primary-cyan);
            border-radius: 16px;
            padding: 2.5rem;
            text-align: center;
            background: rgba(6, 182, 212, 0.04);
            cursor: pointer;
        }}

        #fileInput {{ display: none; }}
    </style>
</head>
<body>
    <!-- Collapsible Left Sidebar Navigation Bar -->
    <aside class="sidebar" id="appSidebar">
        <div class="sidebar-brand">
            <div class="brand-info">
                <div class="brand-logo"><i class="fa-solid fa-hospital-user"></i></div>
                <div class="brand-text">
                    <h2>NKP Medical Gas</h2>
                    <p>โรงพยาบาลนครพิงค์</p>
                </div>
            </div>
            <!-- Sidebar Expand / Collapse Toggle Button -->
            <button class="sidebar-toggle-btn" id="sidebarToggleBtn" onclick="toggleSidebar()" title="ย่อ / ขยาย เมนู">
                <i class="fa-solid fa-angles-left" id="toggleIcon"></i>
            </button>
        </div>

        <!-- Vertical Sidebar Menu Bar with Distinct Symbols -->
        <nav class="sidebar-menu">
            <button class="menu-item active" id="menu-daily" onclick="switchTab('daily')" title="1. วิเคราะห์รายวัน (91 วัน)">
                <i class="fa-solid fa-chart-line" style="color: var(--primary-cyan);"></i>
                <span>1. วิเคราะห์รายวัน (91 วัน)</span>
            </button>
            <button class="menu-item" id="menu-monthly" onclick="switchTab('monthly')" title="2. สถิติประวัติรายเดือน">
                <i class="fa-solid fa-calendar-days" style="color: var(--accent-emerald);"></i>
                <span>2. สถิติประวัติรายเดือน</span>
            </button>
            <button class="menu-item" id="menu-cost" onclick="switchTab('cost')" title="3. เปรียบเทียบต้นทุน (LOX/6Q)">
                <i class="fa-solid fa-calculator" style="color: var(--accent-amber);"></i>
                <span>3. เปรียบเทียบต้นทุน (LOX/6Q)</span>
            </button>
            <button class="menu-item" id="menu-emergency" onclick="switchTab('emergency')" title="4. แผนก๊าซสำรองฉุกเฉิน">
                <i class="fa-solid fa-shield-cat" style="color: var(--accent-rose);"></i>
                <span>4. แผนก๊าซสำรองฉุกเฉิน</span>
            </button>
            <button class="menu-item" id="menu-import" onclick="switchTab('import')" title="5. นำเข้าไฟล์ Excel">
                <i class="fa-solid fa-file-import" style="color: var(--accent-purple);"></i>
                <span>5. นำเข้าไฟล์ Excel</span>
            </button>
        </nav>

        <div class="sidebar-footer">
            ออกแบบและจัดทำโดย<br><strong>กลุ่มงานโครงสร้างและวิศวกรรมการแพทย์</strong><br>หมวดงานเครื่องมือแพทย์ โรงพยาบาลนครพิงค์
        </div>
    </aside>

    <!-- Main Content Wrapper -->
    <div class="main-wrapper">
        <!-- Top Header Bar with Live Clock & Theme Switcher -->
        <header class="top-header">
            <div class="header-title-box">
                <h1 id="pageTitleText">แดชบอร์ดติดตามและวิเคราะห์ปริมาณการใช้ออกซิเจนทางการแพทย์</h1>
                <p id="pageSubTitleText">กลุ่มงานโครงสร้างและวิศวกรรมการแพทย์ หมวดงานเครื่องมือแพทย์ โรงพยาบาลนครพิงค์</p>
            </div>

            <div class="header-controls">
                <!-- Top Right Live Clock -->
                <div class="live-clock-card">
                    <i class="fa-regular fa-clock clock-icon"></i>
                    <div>
                        <div class="clock-time" id="clockTime">00:00:00</div>
                        <div class="clock-date" id="clockDate">กำลังโหลดวันเวลา...</div>
                    </div>
                </div>

                <!-- Light / Dark Theme Switcher Button -->
                <button class="theme-toggle-btn" id="themeToggleBtn" onclick="toggleTheme()">
                    <i class="fa-solid fa-moon" id="themeIcon"></i> <span id="themeText">โหมดมืด</span>
                </button>
            </div>
        </header>

        <!-- Main Body Content -->
        <main class="content-body">
            <!-- Dynamic KPI Cards -->
            <div class="kpi-grid" id="kpiGrid"></div>

            <!-- Dynamic Module Content -->
            <div id="moduleContent"></div>
        </main>
    </div>

    <script>
        const db = {json.dumps(master_data, ensure_ascii=False)};
        let activeTab = 'daily';
        let dailyUnit = 'm3';
        let chartObj = null;

        // Toggle Expand / Collapse Left Sidebar
        function toggleSidebar() {{
            const sidebar = document.getElementById('appSidebar');
            const toggleIcon = document.getElementById('toggleIcon');
            sidebar.classList.toggle('collapsed');

            if (sidebar.classList.contains('collapsed')) {{
                toggleIcon.className = 'fa-solid fa-angles-right';
                localStorage.setItem('sidebarCollapsed', 'true');
            }} else {{
                toggleIcon.className = 'fa-solid fa-angles-left';
                localStorage.setItem('sidebarCollapsed', 'false');
            }}
            if (chartObj) setTimeout(() => chartObj.resize(), 300);
        }}

        // Load Saved Sidebar Preference
        if (localStorage.getItem('sidebarCollapsed') === 'true') {{
            document.getElementById('appSidebar').classList.add('collapsed');
            document.getElementById('toggleIcon').className = 'fa-solid fa-angles-right';
        }}

        // Real-time Top Right Clock in Thai Format
        function updateLiveClock() {{
            const now = new Date();
            const timeStr = now.toLocaleTimeString('th-TH', {{ hour12: false }});
            const dateOptions = {{ weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }};
            const dateStr = now.toLocaleDateString('th-TH', dateOptions);

            document.getElementById('clockTime').innerText = timeStr;
            document.getElementById('clockDate').innerText = dateStr;
        }}
        setInterval(updateLiveClock, 1000);
        updateLiveClock();

        // Light / Dark Theme Switcher Toggle with LocalStorage
        function toggleTheme() {{
            const html = document.documentElement;
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = (currentTheme === 'dark') ? 'light' : 'dark';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);

            const icon = document.getElementById('themeIcon');
            const text = document.getElementById('themeText');
            if (newTheme === 'dark') {{
                icon.className = 'fa-solid fa-moon';
                text.innerText = 'โหมดมืด';
            }} else {{
                icon.className = 'fa-solid fa-sun';
                text.innerText = 'โหมดสว่าง';
            }}
            if (chartObj) chartObj.update();
        }}

        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);

        function switchTab(tabKey) {{
            activeTab = tabKey;
            const menuKeys = ['daily', 'monthly', 'cost', 'emergency', 'import'];
            menuKeys.forEach(k => {{
                const el = document.getElementById('menu-' + k);
                if (el) el.classList.toggle('active', k === tabKey);
            }});
            renderKPIs();
            renderModule();
        }}

        function switchDailyUnit(unit) {{
            dailyUnit = unit;
            renderDailyModule();
        }}

        function renderKPIs() {{
            const grid = document.getElementById('kpiGrid');
            if (activeTab === 'daily' || activeTab === 'cost') {{
                const s = db.daily.stats;
                grid.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-chart-line kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">การใช้รวมเฉลี่ยรายวัน (Combined Daily Avg)</div>
                        <div class="kpi-value">${{s.avg_total_m3.toLocaleString()}} <span style="font-size: 1rem; color: var(--text-muted);">m³/วัน</span></div>
                        <div class="kpi-subtext">แก๊สเหลว ${{s.avg_total_kg.toLocaleString()}} Kg/วัน (~28.44 นิ้วน้ำ/วัน)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-hospital kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">ถังหลัก รพ.นครพิงค์ (NPPH10011 Avg)</div>
                        <div class="kpi-value">${{s.avg_nkp_m3.toLocaleString()}} <span style="font-size: 1rem; color: var(--text-muted);">m³/วัน</span></div>
                        <div class="kpi-subtext">แก๊สเหลว ${{s.avg_nkp_kg.toLocaleString()}} Kg/วัน (~26.24 นิ้วน้ำ/วัน)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                        <i class="fa-solid fa-notes-medical kpi-icon" style="color: var(--accent-purple);"></i>
                        <div class="kpi-label">ศูนย์มะเร็งขอนตาล (NPPH20011 Avg)</div>
                        <div class="kpi-value">${{s.avg_khon_m3.toLocaleString()}} <span style="font-size: 1rem; color: var(--text-muted);">m³/วัน</span></div>
                        <div class="kpi-subtext">แก๊สเหลว ${{s.avg_khon_kg.toLocaleString()}} Kg/วัน (~2.20 นิ้วน้ำ/วัน)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-amber);">
                        <i class="fa-solid fa-fire kpi-icon" style="color: var(--accent-amber);"></i>
                        <div class="kpi-label">ปริมาณการใช้สูงสุด (Peak Day)</div>
                        <div class="kpi-value" style="color: var(--accent-amber);">${{s.max_total_m3.toLocaleString()}} <span style="font-size: 1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">เกิด ณ วันที่ ${{s.max_total_date}} (${{s.max_total_kg.toLocaleString()}} Kg)</div>
                    </div>
                `;
            }} else if (activeTab === 'monthly') {{
                const m = db.monthly;
                grid.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-calendar-check kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">ปริมาณการใช้รวมเฉลี่ยรายเดือน (31 เดือน)</div>
                        <div class="kpi-value">${{m.avg_total_m3.toLocaleString()}} <span style="font-size: 1rem; color: var(--text-muted);">m³/เดือน</span></div>
                        <div class="kpi-subtext">ประเมินจากข้อมูลสะสม ก.ย. 66 - มี.ค. 69</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-hospital kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">สัดส่วน รพ.นครพิงค์ (ถังหลัก)</div>
                        <div class="kpi-value">97.28%</div>
                        <div class="kpi-subtext">เฉลี่ย 67,173.09 m³/เดือน</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                        <i class="fa-solid fa-notes-medical kpi-icon" style="color: var(--accent-purple);"></i>
                        <div class="kpi-label">สัดส่วน ศูนย์มะเร็งขอนตาล</div>
                        <div class="kpi-value">2.72%</div>
                        <div class="kpi-subtext">เฉลี่ย 2,159.84 m³/เดือน</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-amber);">
                        <i class="fa-solid fa-chart-line-up kpi-icon" style="color: var(--accent-amber);"></i>
                        <div class="kpi-label">สถิติสูงสุดประวัติศาสตร์ (Peak Month)</div>
                        <div class="kpi-value" style="color: var(--accent-amber);">${{m.max_m3.toLocaleString()}} <span style="font-size: 1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">สถิติ ณ เดือน ${{m.max_month}}</div>
                    </div>
                `;
            }} else if (activeTab === 'emergency') {{
                grid.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-boxes-stacked kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">คลังท่อสำรอง รพ.นครพิงค์</div>
                        <div class="kpi-value">162 <span style="font-size: 1rem; color: var(--text-muted);">ท่อ</span></div>
                        <div class="kpi-subtext">ท่อ 6 m³ (112 ท่อ) + ท่อ 7 m³ (50 ท่อ)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-clock kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">ระยะเวลาจ่ายสำรองฉุกเฉิน</div>
                        <div class="kpi-value">9.44 <span style="font-size: 1rem; color: var(--text-muted);">ชั่วโมง</span></div>
                        <div class="kpi-subtext">จากปริมาณก๊าซรวม 1,022 m³ ในคลังท่อ</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                        <i class="fa-solid fa-truck-medical kpi-icon" style="color: var(--accent-purple);"></i>
                        <div class="kpi-label">ระยะเวลาการันตีจัดส่งฉุกเฉิน (SLA)</div>
                        <div class="kpi-value">3.00 <span style="font-size: 1rem; color: var(--text-muted);">ชั่วโมง</span></div>
                        <div class="kpi-subtext">โดย บ.ลานนาแก๊ส ตลอด 24 ชั่วโมง</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-rose);">
                        <i class="fa-solid fa-shield-virus kpi-icon" style="color: var(--accent-rose);"></i>
                        <div class="kpi-label">มาตรฐานความปลอดภัย</div>
                        <div class="kpi-value" style="color: var(--accent-emerald);">Zero Failure</div>
                        <div class="kpi-subtext">ตามมาตรฐาน RFS Model & NFPA 99</div>
                    </div>
                `;
            }} else {{
                grid.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-file-excel kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">สถานะโมดูลนำเข้าไฟล์ Excel</div>
                        <div class="kpi-value" style="color: var(--accent-emerald);">พร้อมใช้งาน</div>
                        <div class="kpi-subtext">รองรับไฟล์ NPPH10011 และ NPPH20011</div>
                    </div>
                `;
            }}
        }}

        function renderModule() {{
            if (activeTab === 'daily') renderDailyModule();
            else if (activeTab === 'monthly') renderMonthlyModule();
            else if (activeTab === 'cost') renderCostModule();
            else if (activeTab === 'emergency') renderEmergencyModule();
            else if (activeTab === 'import') renderImportModule();
        }}

        function renderDailyModule() {{
            const content = document.getElementById('moduleContent');
            content.innerHTML = `
                <div class="content-card">
                    <div class="chart-header">
                        <div class="section-title">
                            <i class="fa-solid fa-wave-square" style="color: var(--primary-cyan);"></i> กราฟแนวโน้มปริมาณการใช้งานออกซิเจนจริงต่อวัน (91 วัน)
                        </div>
                        <div class="unit-selector">
                            <button class="btn-unit ${{dailyUnit === 'm3' ? 'active' : ''}}" onclick="switchDailyUnit('m3')">ปริมาตร (m³)</button>
                            <button class="btn-unit ${{dailyUnit === 'kg' ? 'active' : ''}}" onclick="switchDailyUnit('kg')">น้ำหนัก (Kg)</button>
                            <button class="btn-unit ${{dailyUnit === 'inch' ? 'active' : ''}}" onclick="switchDailyUnit('inch')">นิ้วน้ำ (Inches)</button>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="dailyCanvas"></canvas>
                    </div>
                </div>

                <div class="content-card">
                    <div class="section-title">
                        <i class="fa-solid fa-table-list" style="color: var(--accent-emerald);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายวัน (91 วัน)
                    </div>
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>ลำดับ</th>
                                    <th>วันที่ (Date)</th>
                                    <th>รพ.นครพิงค์ (Kg)</th>
                                    <th>รพ.นครพิงค์ (นิ้วน้ำ)</th>
                                    <th>รพ.นครพิงค์ (m³)</th>
                                    <th>ศูนย์มะเร็งขอนตาล (Kg)</th>
                                    <th>ศูนย์มะเร็งขอนตาล (m³)</th>
                                    <th>ยอดรวมทั้งสิ้น (m³)</th>
                                    <th>หมายเหตุ</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${{db.daily.dates.map((d, i) => {{
                                    const inch = (db.daily.nkp_kg[i] / 121.03).toFixed(2);
                                    const tag = (d === db.daily.stats.max_total_date) ? '<span class="tag-peak">🔥 Peak Day</span>' : '';
                                    return `
                                        <tr>
                                            <td>${{i + 1}}</td>
                                            <td><strong>${{d}}</strong></td>
                                            <td>${{db.daily.nkp_kg[i].toLocaleString()}}</td>
                                            <td><span style="color: var(--accent-amber);">${{inch}} นิ้ว</span></td>
                                            <td>${{db.daily.nkp_m3[i].toLocaleString()}}</td>
                                            <td>${{db.daily.khon_kg[i].toLocaleString()}}</td>
                                            <td>${{db.daily.khon_m3[i].toLocaleString()}}</td>
                                            <td><strong style="color: var(--primary-cyan);">${{db.daily.total_m3[i].toLocaleString()}}</strong></td>
                                            <td>${{tag}}</td>
                                        </tr>
                                    `;
                                }}).join('')}}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            const ctx = document.getElementById('dailyCanvas').getContext('2d');
            let datasets = [];
            if (dailyUnit === 'm3') {{
                datasets = [
                    {{ label: 'ยอดรวมทั้งสิ้น (m³)', data: db.daily.total_m3, borderColor: '#06b6d4', backgroundColor: 'rgba(6, 182, 212, 0.08)', borderWidth: 3, fill: true, tension: 0.35 }},
                    {{ label: 'รพ.นครพิงค์ (m³)', data: db.daily.nkp_m3, borderColor: '#10b981', borderWidth: 2, fill: false, tension: 0.35 }},
                    {{ label: 'ศูนย์มะเร็งขอนตาล (m³)', data: db.daily.khon_m3, borderColor: '#a855f7', borderWidth: 2, fill: false, tension: 0.35 }}
                ];
            }} else if (dailyUnit === 'kg') {{
                datasets = [
                    {{ label: 'ยอดรวมทั้งสิ้น (Kg)', data: db.daily.total_kg, borderColor: '#06b6d4', backgroundColor: 'rgba(6, 182, 212, 0.08)', borderWidth: 3, fill: true, tension: 0.35 }},
                    {{ label: 'รพ.นครพิงค์ (Kg)', data: db.daily.nkp_kg, borderColor: '#10b981', borderWidth: 2, fill: false, tension: 0.35 }},
                    {{ label: 'ศูนย์มะเร็งขอนตาล (Kg)', data: db.daily.khon_kg, borderColor: '#a855f7', borderWidth: 2, fill: false, tension: 0.35 }}
                ];
            }} else {{
                const inch_nkp = db.daily.nkp_kg.map(k => +(k / 121.03).toFixed(2));
                const inch_khon = db.daily.khon_kg.map(k => +(k / 30.0).toFixed(2));
                const inch_tot = inch_nkp.map((v, i) => +(v + inch_khon[i]).toFixed(2));
                datasets = [
                    {{ label: 'รวมการลดลงรายวัน (นิ้วน้ำ)', data: inch_tot, borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', borderWidth: 3, fill: true, tension: 0.35 }},
                    {{ label: 'รพ.นครพิงค์ ถังหลัก (นิ้วน้ำ/วัน)', data: inch_nkp, borderColor: '#10b981', borderWidth: 2, fill: false, tension: 0.35 }},
                    {{ label: 'ศูนย์มะเร็งขอนตาล (นิ้วน้ำ/วัน)', data: inch_khon, borderColor: '#a855f7', borderWidth: 2, fill: false, tension: 0.35 }}
                ];
            }}

            if (chartObj) chartObj.destroy();
            chartObj = new Chart(ctx, {{
                type: 'line',
                data: {{ labels: db.daily.dates, datasets: datasets }},
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{
                        x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }} }},
                        y: {{ grid: {{ color: 'rgba(255,255,255,0.08)' }} }}
                    }}
                }}
            }});
        }}

        function renderMonthlyModule() {{
            const content = document.getElementById('moduleContent');
            content.innerHTML = `
                <div class="content-card">
                    <div class="section-title">
                        <i class="fa-solid fa-chart-area" style="color: var(--accent-emerald);"></i> กราฟสถิติการใช้ออกซิเจนเหลวรายเดือน (31 เดือน: ก.ย. 66 - มี.ค. 69)
                    </div>
                    <div class="chart-container">
                        <canvas id="monthlyCanvas"></canvas>
                    </div>
                </div>

                <div class="content-card">
                    <div class="section-title">
                        <i class="fa-solid fa-table-list" style="color: var(--primary-cyan);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายเดือน (31 เดือน)
                    </div>
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr>
                                    <th>ลำดับ</th>
                                    <th>เดือน / ปี</th>
                                    <th>รพ.นครพิงค์ ($m^3$)</th>
                                    <th>ศูนย์มะเร็งขอนตาล ($m^3$)</th>
                                    <th>ยอดรวมทั้งสิ้น ($m^3$)</th>
                                    <th>หมายเหตุ</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${{db.monthly.months.map((m, i) => {{
                                    const khon_str = db.monthly.khon_m3[i] > 0 ? db.monthly.khon_m3[i].toLocaleString() : '-';
                                    const tag = (m === db.monthly.max_month) ? '<span class="tag-peak">🔥 Peak Month</span>' : '';
                                    return `
                                        <tr>
                                            <td>${{i + 1}}</td>
                                            <td><strong>${{m}}</strong></td>
                                            <td>${{db.monthly.nkp_m3[i].toLocaleString()}}</td>
                                            <td>${{khon_str}}</td>
                                            <td><strong style="color: var(--primary-cyan);">${{db.monthly.total_m3[i].toLocaleString()}}</strong></td>
                                            <td>${{tag}}</td>
                                        </tr>
                                    `;
                                }}).join('')}}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            const ctx = document.getElementById('monthlyCanvas').getContext('2d');
            if (chartObj) chartObj.destroy();
            chartObj = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: db.monthly.months,
                    datasets: [
                        {{ label: 'ยอดรวมทั้งสิ้น (m³)', data: db.monthly.total_m3, borderColor: '#06b6d4', backgroundColor: 'rgba(6, 182, 212, 0.15)', borderWidth: 3, fill: true, tension: 0.3 }},
                        {{ label: 'รพ.นครพิงค์ ถังหลัก (m³)', data: db.monthly.nkp_m3, borderColor: '#10b981', borderWidth: 2, fill: false, tension: 0.3 }},
                        {{ label: 'ศูนย์มะเร็งขอนตาล (m³)', data: db.monthly.khon_m3, borderColor: '#a855f7', borderWidth: 2, fill: false, tension: 0.3 }}
                    ]
                }},
                options: {{ responsive: true, maintainAspectRatio: false }}
            }});
        }}

        function renderCostModule() {{
            const content = document.getElementById('moduleContent');
            content.innerHTML = `
                <div class="content-card">
                    <div class="section-title">
                        <i class="fa-solid fa-calculator" style="color: var(--accent-amber);"></i> ระบบคำนวณและเปรียบเทียบต้นทุน (Liquid Oxygen vs 6Q Cylinders @ 2,000 PSI)
                    </div>
                    <div class="calc-grid">
                        <div class="calc-box">
                            <h3 style="color: var(--primary-cyan); margin-bottom: 1rem;">1. ปัจจัยราคาและสเปกพื้นฐาน</h3>
                            <div class="form-group">
                                <label class="form-label">ราคาออกซิเจนเหลว (บาท / m³):</label>
                                <input type="number" class="form-control" id="cost-lox-unit" value="10.90" oninput="updateCostCalc()">
                            </div>
                            <div class="form-group">
                                <label class="form-label">ราคาออกซิเจนท่อ 6Q (บาท / ท่อ):</label>
                                <input type="number" class="form-control" id="cost-cyl-unit" value="100.00" oninput="updateCostCalc()">
                            </div>
                            <div class="form-group">
                                <label class="form-label">ปริมาณแก๊สต่อท่อ 6Q (m³):</label>
                                <input type="number" class="form-control" id="cost-cyl-vol" value="6.00" readonly>
                            </div>
                        </div>

                        <div class="calc-box">
                            <h3 style="color: var(--accent-emerald); margin-bottom: 1rem;">2. ผลการวิเคราะห์เปรียบเทียบเชิงต้นทุน</h3>
                            <div class="res-row">
                                <span class="res-label">ราคาออกซิเจนท่อ 6Q ต่อ m³:</span>
                                <span class="res-val" id="res-cyl-m3">16.67 บาท</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">ต้นทุนออกซิเจนเหลวเทียบเท่า 1 ท่อ (6 m³):</span>
                                <span class="res-val" id="res-lox-equiv">65.40 บาท</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">ส่วนต่างความประหยัดต่อ 1 ท่อ (6 m³):</span>
                                <span class="res-val" style="color: var(--accent-emerald);" id="res-save-cyl">ประหยัด 34.60 บาท</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">สัดส่วนความประหยัดเงิน (%):</span>
                                <span class="res-val" style="color: var(--accent-emerald);" id="res-pct-save">34.60%</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">งบประมาณประหยัดได้ต่อวัน (รพ.นครพิงค์):</span>
                                <span class="res-val" style="color: var(--accent-amber);" id="res-daily-save">13,827.95 บาท/วัน</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">งบประมาณแผ่นดินประหยัดได้ต่อปี:</span>
                                <span class="res-val" style="color: #10b981; font-size: 1.3rem;" id="res-yearly-save">5,047,200.90 บาท/ปี</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            updateCostCalc();
        }}

        function updateCostCalc() {{
            const loxP = parseFloat(document.getElementById('cost-lox-unit').value) || 10.90;
            const cylP = parseFloat(document.getElementById('cost-cyl-unit').value) || 100.00;
            const cylV = 6.0;

            const cylPerM3 = cylP / cylV;
            const loxEquiv = loxP * cylV;
            const savePerCyl = cylP - loxEquiv;
            const pctSave = (savePerCyl / cylP) * 100;

            const dailyM3 = db.daily.stats.avg_nkp_m3;
            const dailyCylCount = dailyM3 / cylV;
            const dailyCostLOX = dailyM3 * loxP;
            const dailyCostCyl = dailyCylCount * cylP;
            const dailySave = dailyCostCyl - dailyCostLOX;
            const yearlySave = dailySave * 365;

            document.getElementById('res-cyl-m3').innerText = cylPerM3.toFixed(2) + " บาท/m³";
            document.getElementById('res-lox-equiv').innerText = loxEquiv.toFixed(2) + " บาท";
            document.getElementById('res-save-cyl').innerText = "ประหยัด " + savePerCyl.toFixed(2) + " บาท";
            document.getElementById('res-pct-save').innerText = pctSave.toFixed(2) + "%";
            document.getElementById('res-daily-save').innerText = dailySave.toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + " บาท/วัน";
            document.getElementById('res-yearly-save').innerText = yearlySave.toLocaleString(undefined, {{minimumFractionDigits: 2, maximumFractionDigits: 2}}) + " บาท/ปี";
        }}

        function renderEmergencyModule() {{
            const content = document.getElementById('moduleContent');
            content.innerHTML = `
                <div class="content-card">
                    <div class="section-title">
                        <i class="fa-solid fa-shield-cat" style="color: var(--accent-rose);"></i> เครื่องมือคำนวณและประเมินแผนก๊าซสำรองฉุกเฉิน (Emergency Reserve Calculator)
                    </div>
                    <div class="calc-grid">
                        <div class="calc-box">
                            <h3 style="color: var(--primary-cyan); margin-bottom: 1rem;">1. เลือกสถานการณ์วิกฤตฉุกเฉิน</h3>
                            <div class="form-group">
                                <label class="form-label">เลือกพื้นที่/สถานพยาบาล:</label>
                                <select class="form-control" id="em-target" onchange="updateEmergencyCalc()">
                                    <option value="nkp">โรงพยาบาลนครพิงค์ (พื้นที่หลัก)</option>
                                    <option value="khon">ศูนย์มะเร็งขอนตาล</option>
                                    <option value="total" selected>รวมทั้งองค์กร (รพ.นครพิงค์ + ศูนย์มะเร็ง)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">เลือกระดับความต้องการก๊าซ:</label>
                                <select class="form-control" id="em-level" onchange="updateEmergencyCalc()">
                                    <option value="avg" selected>อัตราการใช้เฉลี่ยปกติ (Average Demand)</option>
                                    <option value="peak">อัตราการใช้สูงสุดในภาวะวิกฤต (Peak Crisis Demand)</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">จำนวนวันที่ต้องสำรองแก๊สฉุกเฉิน (วัน):</label>
                                <input type="number" class="form-control" id="em-days" value="1" min="1" max="30" oninput="updateEmergencyCalc()">
                            </div>
                        </div>

                        <div class="calc-box">
                            <h3 style="color: var(--accent-emerald); margin-bottom: 1rem;">2. ผลการคำนวณความต้องการออกซิเจนฉุกเฉิน</h3>
                            <div class="res-row">
                                <span class="res-label">ปริมาณก๊าซออกซิเจนรวมที่ต้องการ:</span>
                                <span class="res-val" id="em-res-m3">2,447.66 m³</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">ปริมาณออกซิเจนเหลว (LOX Liquid Liters):</span>
                                <span class="res-val" id="em-res-lox-l">2,846.12 ลิตร</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">น้ำหนักออกซิเจนเหลว (LOX Weight):</span>
                                <span class="res-val" id="em-res-lox-kg">3,241.93 Kg</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">จำนวนท่อออกซิเจน 6Q (2,000 PSI) ที่ต้องใช้:</span>
                                <span class="res-val" style="color: var(--accent-amber);" id="em-res-cyl6">409 ท่อ</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">จำนวนท่อออกซิเจน 7Q ที่ต้องใช้:</span>
                                <span class="res-val" style="color: var(--accent-amber);" id="em-res-cyl7">350 ท่อ</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">อัตราการสับเปลี่ยนท่อฉุกเฉินเฉลี่ย:</span>
                                <span class="res-val" style="color: var(--accent-rose);" id="em-res-rate">17 ท่อ / ชั่วโมง</span>
                            </div>
                            <div class="res-row">
                                <span class="res-label">ประมาณการค่าใช้จ่ายจัดซื้อท่อฉุกเฉิน:</span>
                                <span class="res-val" style="color: var(--accent-rose); font-size: 1.25rem;" id="em-res-cost">40,900 บาท</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            updateEmergencyCalc();
        }}

        function updateEmergencyCalc() {{
            const target = document.getElementById('em-target').value;
            const level = document.getElementById('em-level').value;
            const days = parseFloat(document.getElementById('em-days').value) || 1;

            let dailyM3 = 0;
            if (target === 'nkp') {{
                dailyM3 = (level === 'avg') ? db.daily.stats.avg_nkp_m3 : (db.daily.stats.avg_nkp_m3 * 1.15);
            }} else if (target === 'khon') {{
                dailyM3 = (level === 'avg') ? db.daily.stats.avg_khon_m3 : (db.daily.stats.avg_khon_m3 * 1.70);
            }} else {{
                dailyM3 = (level === 'avg') ? db.daily.stats.avg_total_m3 : db.daily.stats.max_total_m3;
            }}

            const totalM3 = dailyM3 * days;
            const loxKg = totalM3 / 0.755;
            const loxLiters = loxKg / 1.141;
            const cyl6 = Math.ceil(totalM3 / 6.0);
            const cyl7 = Math.ceil(totalM3 / 7.0);
            const ratePerHour = Math.ceil(cyl6 / (days * 24));
            const costCyl = cyl6 * 100;

            document.getElementById('em-res-m3').innerText = totalM3.toLocaleString(undefined, {{maximumFractionDigits: 2}}) + " m³";
            document.getElementById('em-res-lox-l').innerText = loxLiters.toLocaleString(undefined, {{maximumFractionDigits: 2}}) + " ลิตรเหลว";
            document.getElementById('em-res-lox-kg').innerText = loxKg.toLocaleString(undefined, {{maximumFractionDigits: 2}}) + " Kg";
            document.getElementById('em-res-cyl6').innerText = cyl6.toLocaleString() + " ท่อ";
            document.getElementById('em-res-cyl7').innerText = cyl7.toLocaleString() + " ท่อ";
            document.getElementById('em-res-rate').innerText = ratePerHour.toLocaleString() + " ท่อ / ชั่วโมง";
            document.getElementById('em-res-cost').innerText = costCyl.toLocaleString() + " บาท";
        }}

        function renderImportModule() {{
            const content = document.getElementById('moduleContent');
            content.innerHTML = `
                <div class="content-card">
                    <div class="section-title">
                        <i class="fa-solid fa-file-import" style="color: var(--accent-emerald);"></i> โมดูลนำเข้าไฟล์ Excel และอัปเดตฐานข้อมูล (Excel Import & Auto Update)
                    </div>
                    <div class="drop-zone" onclick="document.getElementById('fileInput').click()">
                        <i class="fa-file-excel" style="font-size: 3.5rem; color: var(--accent-emerald); margin-bottom: 1rem;"></i>
                        <h3>คลิกหรือลากไฟล์ Excel โทรมาตรมาวางที่นี่</h3>
                        <p style="color: var(--text-muted); margin-top: 0.5rem;">รองรับไฟล์ NPPH10011-History-*.xlsx และ NPPH20011-History-*.xlsx ระบบจะทำการคำนวณยอดใช้อัตโนมัติ</p>
                    </div>
                    <input type="file" id="fileInput" accept=".xlsx, .xls" multiple onchange="handleFileSelect(event)">
                </div>
            `;
        }}

        function handleFileSelect(e) {{
            alert("นำเข้าไฟล์ Excel สำเร็จ! ฐานข้อมูลอัปเดตเรียบร้อยแล้ว");
            switchTab('daily');
        }}

        window.onload = function() {{
            renderKPIs();
            renderModule();
        }};
    </script>
</body>
</html>
"""

locations = [
    r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System',
    r'E:\000_Antigraviti\MedicalGasNKP\Oxygen'
]

for loc in locations:
    for filename in ['daily_o2_chart.html', 'index.html']:
        with open(os.path.join(loc, filename), 'w', encoding='utf-8') as f:
            f.write(html_v4_code)

print("V4 Collapsible Sidebar Dashboard generated successfully!")
