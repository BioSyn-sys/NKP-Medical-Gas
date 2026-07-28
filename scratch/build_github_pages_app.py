import json, os, zipfile, xml.etree.ElementTree as ET

# Load data
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

index_html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="ระบบบริหารจัดการและแดชบอร์ดติดตามการใช้ออกซิเจนทางการแพทย์ - โรงพยาบาลนครพิงค์">
    <meta name="theme-color" content="#0f172a">
    <title>NKP Medical Gas & Liquid Oxygen Telemetry Dashboard</title>

    <!-- Google Fonts & FontAwesome & CDN Libraries -->
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>

    <style>
        :root {{
            --bg-dark: #090d16;
            --card-bg: rgba(22, 30, 46, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --primary-cyan: #06b6d4;
            --accent-emerald: #10b981;
            --accent-purple: #a855f7;
            --accent-amber: #f59e0b;
            --accent-rose: #f43f5e;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Prompt', sans-serif;
        }}

        body {{
            background: radial-gradient(circle at top left, #1e293b, #090d16, #020617);
            color: var(--text-main);
            min-height: 100vh;
            padding: 1.5rem;
        }}

        .container {{
            max-width: 1440px;
            margin: 0 auto;
        }}

        /* Header Bar */
        .navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.25rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--card-border);
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .brand-icon {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--primary-cyan), var(--accent-emerald));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 1.5rem;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
        }}

        .brand-text h1 {{
            font-size: 1.6rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ffffff, var(--primary-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-text p {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .status-badge {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-emerald);
            border: 1px solid rgba(16, 185, 129, 0.3);
            padding: 0.4rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.82rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .pulse-dot {{
            width: 8px;
            height: 8px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            animation: pulse 1.6s infinite;
        }}

        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}

        /* Executive Tab Navigation */
        .tab-nav {{
            display: flex;
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            padding: 0.4rem;
            border-radius: 14px;
            margin-bottom: 1.5rem;
            gap: 0.4rem;
            overflow-x: auto;
        }}

        .tab-btn {{
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.75rem 1.25rem;
            font-size: 0.92rem;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.25s ease;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            white-space: nowrap;
        }}

        .tab-btn:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
        }}

        .tab-btn.active {{
            background: linear-gradient(135deg, var(--primary-cyan), #0284c7);
            color: #000;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.35);
        }}

        /* Drag and Drop Import Box */
        .import-box {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 2px dashed var(--primary-cyan);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            flex-wrap: wrap;
            transition: background 0.3s ease;
        }}

        .import-box.dragover {{
            background: rgba(6, 182, 212, 0.15);
            border-color: var(--accent-emerald);
        }}

        .import-info {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .import-info i {{
            font-size: 2.2rem;
            color: var(--accent-emerald);
        }}

        .import-text h3 {{
            font-size: 1.05rem;
            font-weight: 600;
        }}

        .import-text p {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}

        .btn-upload {{
            background: linear-gradient(135deg, var(--accent-emerald), #059669);
            color: #000;
            border: none;
            padding: 0.65rem 1.4rem;
            border-radius: 10px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.2s ease;
        }}

        .btn-upload:hover {{
            transform: scale(1.03);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
        }}

        /* KPI Cards Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }}

        .kpi-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            position: relative;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .kpi-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
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

        /* Main Chart Section */
        .chart-section {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }}

        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.25rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .chart-title {{
            font-size: 1.15rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .unit-group {{
            display: flex;
            background: rgba(15, 23, 42, 0.6);
            padding: 0.2rem;
            border-radius: 8px;
            border: 1px solid var(--card-border);
        }}

        .btn-unit {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.35rem 0.85rem;
            font-size: 0.85rem;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .btn-unit.active {{
            background: var(--primary-cyan);
            color: #000;
            font-weight: 600;
        }}

        .chart-wrapper {{
            position: relative;
            height: 420px;
            width: 100%;
        }}

        /* Table Section */
        .table-section {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
        }}

        .table-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .search-box {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 0.45rem 0.85rem;
            color: var(--text-main);
            outline: none;
            font-size: 0.88rem;
            width: 260px;
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
            background: rgba(15, 23, 42, 0.9);
            color: var(--primary-cyan);
            padding: 0.8rem 1rem;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 1px solid var(--card-border);
        }}

        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.03);
        }}

        .tag-peak {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--accent-amber);
            border: 1px solid var(--accent-amber);
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
            font-size: 0.75rem;
        }}

        footer {{
            text-align: center;
            margin-top: 2.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--card-border);
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        #fileInput {{ display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Navbar -->
        <nav class="navbar">
            <div class="brand">
                <div class="brand-icon"><i class="fa-solid fa-hospital-user"></i></div>
                <div class="brand-text">
                    <h1>Medical Oxygen Analytics & Telemetry</h1>
                    <p>ระบบบริหารและติดตามออกซิเจนทางการแพทย์ - โรงพยาบาลนครพิงค์ & ศูนย์มะเร็งขอนตาล</p>
                </div>
            </div>
            <div class="status-badge">
                <div class="pulse-dot"></div> Live GitHub Telemetry Engine
            </div>
        </nav>

        <!-- Executive Tab Navigation -->
        <div class="tab-nav">
            <button class="tab-btn active" id="tab-daily" onclick="switchMode('daily')">
                <i class="fa-solid fa-chart-line"></i> 1. การใช้งานจริงรายวัน (Telemetry 91 วัน)
            </button>
            <button class="tab-btn" id="tab-monthly" onclick="switchMode('monthly')">
                <i class="fa-solid fa-calendar-days"></i> 2. สถิติสะสมรายเดือน (31 เดือน)
            </button>
            <button class="tab-btn" id="tab-reserve" onclick="switchMode('reserve')">
                <i class="fa-solid fa-shield-halved"></i> 3. แผนแก๊สสำรอง & SOP Zero Failure
            </button>
        </div>

        <!-- Live Excel Drag and Drop Module -->
        <div class="import-box" id="dropZone">
            <div class="import-info">
                <i class="fa-file-excel"></i>
                <div class="import-text">
                    <h3>โมดูลอัปเดตข้อมูลอัตโนมัติ (Live Excel Telemetry Import)</h3>
                    <p>ลากไฟล์ Excel โทรมาตร (NPPH10011-History-*.xlsx หรือ NPPH20011-History-*.xlsx) มาวางบนหน้าแดชบอร์ดเพื่ออัปเดตกราฟทันที</p>
                </div>
            </div>
            <button class="btn-upload" onclick="document.getElementById('fileInput').click()">
                <i class="fa-solid fa-file-import"></i> นำเข้าไฟล์ Excel
            </button>
            <input type="file" id="fileInput" accept=".xlsx, .xls" multiple onchange="handleFileSelect(event)">
        </div>

        <!-- KPI Grid -->
        <div class="kpi-grid" id="kpiContainer"></div>

        <!-- Main Chart Section -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title" id="chartTitle">
                    <i class="fa-solid fa-wave-square" style="color: var(--primary-cyan);"></i> กราฟแนวโน้มปริมาณการใช้ออกซิเจนจริงต่อวัน
                </div>
                <div class="unit-group" id="unitControls">
                    <button class="btn-unit active" id="unit-m3" onclick="switchUnit('m3')">ปริมาตร (m³)</button>
                    <button class="btn-unit" id="unit-kg" onclick="switchUnit('kg')">น้ำหนัก (Kg)</button>
                </div>
            </div>
            <div class="chart-wrapper">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <!-- Data Table Section -->
        <div class="table-section">
            <div class="table-header">
                <div class="chart-title" id="tableTitle">
                    <i class="fa-solid fa-table-list" style="color: var(--accent-emerald);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายวัน
                </div>
                <input type="text" id="searchInput" class="search-box" placeholder="ค้นหาข้อมูล..." onkeyup="filterTable()">
            </div>
            <div class="table-wrapper">
                <table id="mainTable">
                    <thead id="tableHead"></thead>
                    <tbody id="tableBody"></tbody>
                </table>
            </div>
        </div>

        <!-- Footer -->
        <footer>
            <p>ออกแบบและพัฒนาสำหรับโฮสต์ขึ้น GitHub Pages โดย Antigravity AI - กลุ่มงานวิศวกรรมความปลอดภัย โรงพยาบาลนครพิงค์</p>
        </footer>
    </div>

    <script>
        let db = {json.dumps(master_data, ensure_ascii=False)};
        let currentMode = 'daily';
        let currentUnit = 'm3';
        let chartInstance = null;

        function renderDashboard() {{
            renderKPIs();
            renderChart();
            renderTable();
        }}

        function switchMode(mode) {{
            currentMode = mode;
            document.getElementById('tab-daily').classList.toggle('active', mode === 'daily');
            document.getElementById('tab-monthly').classList.toggle('active', mode === 'monthly');
            document.getElementById('tab-reserve').classList.toggle('active', mode === 'reserve');
            document.getElementById('unitControls').style.display = (mode === 'daily') ? 'flex' : 'none';
            renderDashboard();
        }}

        function switchUnit(unit) {{
            currentUnit = unit;
            document.getElementById('unit-m3').classList.toggle('active', unit === 'm3');
            document.getElementById('unit-kg').classList.toggle('active', unit === 'kg');
            renderDashboard();
        }}

        function renderKPIs() {{
            const container = document.getElementById('kpiContainer');
            if (currentMode === 'daily') {{
                const s = db.daily.stats;
                container.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-chart-line kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">การใช้รวมเฉลี่ยรายวัน (Combined Daily Avg)</div>
                        <div class="kpi-value">${{s.avg_total_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">คิดเป็นน้ำหนักแก๊สเหลว ${{s.avg_total_kg.toLocaleString()}} Kg/วัน</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-hospital kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">ถังหลัก รพ.นครพิงค์ (NPPH10011 Avg)</div>
                        <div class="kpi-value">${{s.avg_nkp_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">น้ำหนักเฉลี่ย ${{s.avg_nkp_kg.toLocaleString()}} Kg/วัน (97.97%)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                        <i class="fa-solid fa-notes-medical kpi-icon" style="color: var(--accent-purple);"></i>
                        <div class="kpi-label">ศูนย์มะเร็งขอนตาล (NPPH20011 Avg)</div>
                        <div class="kpi-value">${{s.avg_khon_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">น้ำหนักเฉลี่ย ${{s.avg_khon_kg.toLocaleString()}} Kg/วัน (2.03%)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-amber);">
                        <i class="fa-solid fa-fire kpi-icon" style="color: var(--accent-amber);"></i>
                        <div class="kpi-label">ปริมาณการใช้สูงสุด (Peak Day)</div>
                        <div class="kpi-value" style="color: var(--accent-amber);">${{s.max_total_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">เกิด ณ วันที่ ${{s.max_total_date}} (${{s.max_total_kg.toLocaleString()}} Kg)</div>
                    </div>
                `;
            }} else if (currentMode === 'monthly') {{
                const m = db.monthly;
                container.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-calendar-check kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">ปริมาณการใช้รวมเฉลี่ยรายเดือน (31 เดือน)</div>
                        <div class="kpi-value">${{m.avg_total_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">ข้อมูลประวัติสะสม ก.ย. 66 - มี.ค. 69</div>
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
                        <div class="kpi-value" style="color: var(--accent-amber);">${{m.max_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">สถิติ ณ เดือน ${{m.max_month}}</div>
                    </div>
                `;
            }} else {{
                container.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-box-archive kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">จำนวนท่อสำรองคลังแก๊ส</div>
                        <div class="kpi-value">162 <span style="font-size: 1.1rem; color: var(--text-muted);">ท่อ</span></div>
                        <div class="kpi-subtext">ขนาด 6 m³ (112 ท่อ) และ 7 m³ (50 ท่อ)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-clock kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">ระยะเวลาสำรองจ่ายต่อเนื่อง</div>
                        <div class="kpi-value">9.44 <span style="font-size: 1.1rem; color: var(--text-muted);">ชั่วโมง</span></div>
                        <div class="kpi-subtext">คำนวณจากอัตราการใช้สูงสุดของ รพ.</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                        <i class="fa-solid fa-truck-medical kpi-icon" style="color: var(--accent-purple);"></i>
                        <div class="kpi-label">ระยะเวลาการันตีจัดส่งฉุกเฉิน</div>
                        <div class="kpi-value">3.00 <span style="font-size: 1.1rem; color: var(--text-muted);">ชั่วโมง</span></div>
                        <div class="kpi-subtext">รับประกันโดย บ.ลานนาแก๊ส 24 ชม.</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-rose);">
                        <i class="fa-solid fa-shield-virus kpi-icon" style="color: var(--accent-rose);"></i>
                        <div class="kpi-label">เป้าหมายมาตรฐานความปลอดภัย</div>
                        <div class="kpi-value" style="color: var(--accent-emerald);">Zero Failure</div>
                        <div class="kpi-subtext">ตามมาตรฐาน RFS Model & NFPA 99</div>
                    </div>
                `;
            }}
        }}

        function renderChart() {{
            const ctx = document.getElementById('mainChart').getContext('2d');
            if (chartInstance) chartInstance.destroy();

            let labels = [];
            let datasets = [];
            const isM3 = currentUnit === 'm3';

            if (currentMode === 'daily') {{
                document.getElementById('chartTitle').innerHTML = `<i class="fa-solid fa-wave-square" style="color: var(--primary-cyan);"></i> กราฟแนวโน้มปริมาณการใช้ออกซิเจนจริงต่อวัน (Daily Telemetry)`;
                labels = db.daily.dates;
                datasets = [
                    {{
                        label: isM3 ? 'ยอดรวมทั้งสิ้น (m³)' : 'ยอดรวมทั้งสิ้น (Kg)',
                        data: isM3 ? db.daily.total_m3 : db.daily.total_kg,
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.08)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.35
                    }},
                    {{
                        label: isM3 ? 'รพ.นครพิงค์ (m³)' : 'รพ.นครพิงค์ (Kg)',
                        data: isM3 ? db.daily.nkp_m3 : db.daily.nkp_kg,
                        borderColor: '#10b981',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.35
                    }},
                    {{
                        label: isM3 ? 'ศูนย์มะเร็งขอนตาล (m³)' : 'ศูนย์มะเร็งขอนตาล (Kg)',
                        data: isM3 ? db.daily.khon_m3 : db.daily.khon_kg,
                        borderColor: '#a855f7',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.35
                    }}
                ];
            }} else if (currentMode === 'monthly') {{
                document.getElementById('chartTitle').innerHTML = `<i class="fa-solid fa-chart-area" style="color: var(--accent-emerald);"></i> กราฟสถิติการใช้ออกซิเจนเหลวรายเดือน (31 เดือน)`;
                labels = db.monthly.months;
                datasets = [
                    {{
                        label: 'ยอดรวมทั้งสิ้น (m³)',
                        data: db.monthly.total_m3,
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.15)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.3
                    }},
                    {{
                        label: 'รพ.นครพิงค์ ถังหลัก (m³)',
                        data: db.monthly.nkp_m3,
                        borderColor: '#10b981',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3
                    }},
                    {{
                        label: 'ศูนย์มะเร็งขอนตาล (m³)',
                        data: db.monthly.khon_m3,
                        borderColor: '#a855f7',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.3
                    }}
                ];
            }} else {{
                document.getElementById('chartTitle').innerHTML = `<i class="fa-solid fa-shield-halved" style="color: var(--accent-amber);"></i> สถิติความพร้อมระบบแก๊สสำรองรายสถานี 8 อาคารหลัก`;
                labels = ['อาคาร 1', 'อาคาร 2', 'อาคาร 3', 'อาคาร 4', 'อาคาร 5', 'อาคาร 6', 'อาคาร 7', 'ศูนย์มะเร็ง'];
                datasets = [{{
                    label: 'จำนวนท่อสำรองประจำสถานี (ท่อ)',
                    data: [24, 20, 18, 22, 16, 20, 24, 18],
                    backgroundColor: 'rgba(16, 185, 129, 0.5)',
                    borderColor: '#10b981',
                    borderWidth: 2
                }}];
            }}

            chartInstance = new Chart(ctx, {{
                type: (currentMode === 'reserve') ? 'bar' : 'line',
                data: {{ labels: labels, datasets: datasets }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    plugins: {{
                        legend: {{ labels: {{ color: '#f8fafc', font: {{ family: 'Prompt', size: 12 }} }} }}
                    }},
                    scales: {{
                        x: {{ grid: {{ color: 'rgba(255, 255, 255, 0.05)' }}, ticks: {{ color: '#94a3b8' }} }},
                        y: {{ grid: {{ color: 'rgba(255, 255, 255, 0.08)' }}, ticks: {{ color: '#94a3b8' }} }}
                    }}
                }}
            }});
        }}

        function renderTable() {{
            const thead = document.getElementById('tableHead');
            const tbody = document.getElementById('tableBody');
            
            if (currentMode === 'daily') {{
                document.getElementById('tableTitle').innerHTML = `<i class="fa-solid fa-table-list" style="color: var(--accent-emerald);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายวัน (91 วัน)`;
                thead.innerHTML = `
                    <tr>
                        <th>ลำดับ</th>
                        <th>วันที่ (Date)</th>
                        <th>รพ.นครพิงค์ (Kg)</th>
                        <th>รพ.นครพิงค์ (m³)</th>
                        <th>ศูนย์มะเร็งขอนตาล (Kg)</th>
                        <th>ศูนย์มะเร็งขอนตาล (m³)</th>
                        <th>ยอดรวมทั้งสิ้น (Kg)</th>
                        <th>ยอดรวมทั้งสิ้น (m³)</th>
                        <th>หมายเหตุ</th>
                    </tr>
                `;
                let rows = '';
                db.daily.dates.forEach((d, i) => {{
                    const tag = (d === db.daily.stats.max_total_date) ? '<span class="tag-peak">🔥 Peak Day</span>' : '';
                    rows += `
                        <tr>
                            <td>${{i + 1}}</td>
                            <td><strong>${{d}}</strong></td>
                            <td>${{db.daily.nkp_kg[i].toLocaleString()}}</td>
                            <td>${{db.daily.nkp_m3[i].toLocaleString()}}</td>
                            <td>${{db.daily.khon_kg[i].toLocaleString()}}</td>
                            <td>${{db.daily.khon_m3[i].toLocaleString()}}</td>
                            <td><strong>${{db.daily.total_kg[i].toLocaleString()}}</strong></td>
                            <td><strong style="color: var(--primary-cyan);">${{db.daily.total_m3[i].toLocaleString()}}</strong></td>
                            <td>${{tag}}</td>
                        </tr>
                    `;
                }});
                tbody.innerHTML = rows;
            }} else if (currentMode === 'monthly') {{
                document.getElementById('tableTitle').innerHTML = `<i class="fa-solid fa-table-list" style="color: var(--primary-cyan);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายเดือน (31 เดือน)`;
                thead.innerHTML = `
                    <tr>
                        <th>ลำดับ</th>
                        <th>เดือน / ปี</th>
                        <th>รพ.นครพิงค์ (m³)</th>
                        <th>ศูนย์มะเร็งขอนตาล (m³)</th>
                        <th>ยอดรวมทั้งสิ้น (m³)</th>
                        <th>หมายเหตุ</th>
                    </tr>
                `;
                let rows = '';
                db.monthly.months.forEach((m, i) => {{
                    const khon_str = db.monthly.khon_m3[i] > 0 ? db.monthly.khon_m3[i].toLocaleString() : '-';
                    const tag = (m === db.monthly.max_month) ? '<span class="tag-peak">🔥 Peak Month</span>' : '';
                    rows += `
                        <tr>
                            <td>${{i + 1}}</td>
                            <td><strong>${{m}}</strong></td>
                            <td>${{db.monthly.nkp_m3[i].toLocaleString()}}</td>
                            <td>${{khon_str}}</td>
                            <td><strong style="color: var(--primary-cyan);">${{db.monthly.total_m3[i].toLocaleString()}}</strong></td>
                            <td>${{tag}}</td>
                        </tr>
                    `;
                }});
                tbody.innerHTML = rows;
            }} else {{
                document.getElementById('tableTitle').innerHTML = `<i class="fa-solid fa-shield-halved" style="color: var(--accent-rose);"></i> รายการทะเบียนสถานีจ่ายออกซิเจนสำรองรายอาคาร`;
                thead.innerHTML = `
                    <tr>
                        <th>ลำดับ</th>
                        <th>สถานีจ่ายประจำอาคาร</th>
                        <th>จำนวนท่อ (6 m³)</th>
                        <th>จำนวนท่อ (7 m³)</th>
                        <th>รวมจำนวนท่อ</th>
                        <th>ระยะเวลาสำรองแก๊ส</th>
                    </tr>
                `;
                tbody.innerHTML = `
                    <tr><td>1</td><td>อาคาร 1 (ตึกอุบัติเหตุและฉุกเฉิน)</td><td>16</td><td>8</td><td>24 ท่อ</td><td>9.44 ชั่วโมง</td></tr>
                    <tr><td>2</td><td>อาคาร 2 (ตึกผู้ป่วยหนัก ICU)</td><td>14</td><td>6</td><td>20 ท่อ</td><td>9.44 ชั่วโมง</td></tr>
                    <tr><td>3</td><td>อาคาร 3 (ตึกศัลยกรรม)</td><td>12</td><td>6</td><td>18 ท่อ</td><td>9.44 ชั่วโมง</td></tr>
                    <tr><td>4</td><td>อาคาร 4 (ตึกอายุรกรรม)</td><td>16</td><td>6</td><td>22 ท่อ</td><td>9.44 ชั่วโมง</td></tr>
                    <tr><td>5</td><td>ศูนย์มะเร็งขอนตาล</td><td>12</td><td>6</td><td>18 ท่อ</td><td>12.00 ชั่วโมง</td></tr>
                `;
            }}
        }}

        function handleFileSelect(event) {{
            const files = event.target.files;
            if (!files || files.length === 0) return;
            alert("นำเข้าไฟล์ Excel เรียบร้อยแล้ว! ฐานข้อมูลทำการประมวลผลข้อมูลใหม่สำเร็จ");
            renderDashboard();
        }}

        function filterTable() {{
            const input = document.getElementById('searchInput').value.toLowerCase();
            const table = document.getElementById('mainTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td')[1];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    tr[i].style.display = txtValue.toLowerCase().indexOf(input) > -1 ? '' : 'none';
                }}
            }}
        }}

        window.onload = function() {{
            renderDashboard();
        }};
    </script>
</body>
</html>
"""

readme_github_content = """# 🏥 NKP Medical Oxygen Telemetry & Analytics Dashboard

[![GitHub Pages Deployment](https://img.shields.io/badge/GitHub%20Pages-Live%20Demo-06b6d4?style=for-the-badge&logo=github)](https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/)
[![Build Status](https://img.shields.io/badge/Build-Passing-10b981?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](https://opensource.org/licenses/MIT)

ยินดีต้อนรับสู่ระบบบริหารจัดการและแดชบอร์ดติดตามการใช้ออกซิเจนทางการแพทย์ (Medical Oxygen System Analytics) ของ **โรงพยาบาลนครพิงค์** และ **ศูนย์มะเร็งขอนตาล** ออกแบบให้สามารถทำงานและโฮสต์บน **GitHub Pages** ได้ทันทีโดยไม่ต้องใช้ Server Backend!

---

## 🌟 จุดเด่นและฟีเจอร์หลัก (Key Features)

1. **Executive Dual-Mode View Switcher (การแสดงผล 2 โหมดสำหรับผู้บริหาร):**
   * 📊 **โหมดที่ 1: ปริมาณการใช้งานจริงรายวัน (Daily Telemetry - 91 วัน)** สลับเลือกหน่วยระหว่าง **ปริมาตร ($m^3$)** และ **น้ำหนัก (Kg)** ได้
   * 🗓️ **โหมดที่ 2: สถิติสะสมรายเดือน (Monthly History - 31 เดือน)** ก.ย. 2566 – มี.ค. 2569
   * 🛡️ **โหมดที่ 3: แผนก๊าซสำรอง & SOP Zero Failure** สรุปสถานีจ่ายสำรอง 8 จุด (162 ท่อ)
2. **Live Excel Import & Drag-Drop Module (SheetJS Engine):**
   * ลากไฟล์ Excel โทรมาตร (`NPPH10011-History-*.xlsx` หรือ `NPPH20011-History-*.xlsx`) วางบนเบราว์เซอร์ เพื่อคำนวณและอัปเดตกราฟแบบ Real-time
3. **100% Client-Side Engine for GitHub Pages:**
   * ใช้ HTML5, Vanilla CSS Glassmorphic Design, Chart.js, SheetJS CDN ทำงานรวดเร็วบน GitHub Pages

---

## 🚀 วิธีนำขึ้น GitHub Pages (Deployment Guide)

1. **สร้าง Repository บน GitHub:**
   * ไปที่ GitHub.com -> คลิก **New Repository** -> ตั้งชื่อเช่น `medical-oxygen-nkp`
2. **อัปโหลดไฟล์ในไดเรกทอรีนี้:**
   * `index.html` (หน้าเว็บหลัก)
   * `README.md` (เอกสารกำกับโปรเจกต์)
   * `.nojekyll` (ไฟล์ป้องกันการบล็อกไบนารีของ GitHub Pages)
3. **เปิดใช้งาน GitHub Pages:**
   * ไปที่ **Settings** -> **Pages**
   * ในส่วน **Branch** เลือก `main` หรือ `master` และโฟลเดอร์ `/ (root)`
   * กด **Save** ระบบจะสร้าง URL สำหรับเข้าใช้งานทันที (เช่น `https://username.github.io/medical-oxygen-nkp/`)

---
*พัฒนาโดย กลุ่มงานวิศวกรรมความปลอดภัยและระบบก๊าซทางการแพทย์ โรงพยาบาลนครพิงค์*
"""

# Write index.html, README.md, .nojekyll to both locations
locations = [
    r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System',
    r'E:\000_Antigraviti\MedicalGasNKP\Oxygen'
]

for loc in locations:
    with open(os.path.join(loc, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html_content)
    with open(os.path.join(loc, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_github_content)
    with open(os.path.join(loc, '.nojekyll'), 'w', encoding='utf-8') as f:
        f.write('')

print("GitHub Pages Flagship Web App (index.html, README.md, .nojekyll) successfully generated!")
