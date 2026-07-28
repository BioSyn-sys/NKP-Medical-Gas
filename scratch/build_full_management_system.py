import json, os, zipfile, xml.etree.ElementTree as ET
import pandas as pd

# 1. Parse Monthly Data
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

# 2. Parse Daily Telemetry Data
json_daily_path = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch\telemetry_daily_data.json'
with open(json_daily_path, 'r', encoding='utf-8') as f:
    daily_data = json.load(f)

# Master Data Dict containing both Monthly and Daily views
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

# 3. Create Standalone Python Import Module
import_script_code = '''# Module: import_telemetry_excel.py
# นำเข้าไฟล์ Excel โทรมาตร (NPPH10011 / NPPH20011) และอัปเดตฐานข้อมูลแดชบอร์ดโดยอัตโนมัติ

import os, sys, zipfile, json, glob
import xml.etree.ElementTree as ET
import pandas as pd

def parse_excel_telemetry(file_path):
    print(f"กำลังประมวลผลไฟล์: {os.path.basename(file_path)}...")
    rows_data = []
    with zipfile.ZipFile(file_path) as z:
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
                rows_data.append(row_data)
    
    ship_id = ""
    records = []
    for r in rows_data:
        if len(r) > 1 and "Ship ID" in str(r[1]):
            ship_id = str(r[1]).split(':')[-1].strip()
        if len(r) >= 3 and ('2026' in str(r[0]) or '2025' in str(r[0])):
            post_date = r[0]
            level_str = r[1]
            weight_str = r[2]
            w_clean = weight_str.replace('Kg', '').replace(',', '').strip()
            w_val = float(w_clean) if w_clean else None
            records.append({'datetime': post_date, 'level': level_str, 'weight_kg': w_val})
            
    df = pd.DataFrame(records)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    return ship_id, df

def process_and_update_database(folder_path):
    excel_files = glob.glob(os.path.join(folder_path, "NPPH*.xlsx"))
    if not excel_files:
        print("ไม่พบไฟล์ Excel ตระกูล NPPH*.xlsx ในไดเรกทอรี")
        return
        
    tanks_data = {}
    for f in excel_files:
        ship_id, df = parse_excel_telemetry(f)
        # Clean telemetry anomalies
        df_valid = df[df['weight_kg'] > 0].copy()
        df_valid['diff'] = df_valid['weight_kg'].diff()
        df_valid['consumption_kg'] = df_valid['diff'].apply(lambda x: -x if (x is not None and x < 0) else 0)
        df_valid['date'] = df_valid['datetime'].dt.strftime('%Y-%m-%d')
        
        daily = df_valid.groupby('date').agg(
            consumption_kg=('consumption_kg', 'sum')
        ).reset_index()
        daily['consumption_m3'] = daily['consumption_kg'] * 0.755
        
        if '10011' in ship_id or 'NPPH10011' in f:
            tanks_data['nkp'] = daily
        elif '20011' in ship_id or 'NPPH20011' in f:
            tanks_data['khon'] = daily

    if 'nkp' in tanks_data and 'khon' in tanks_data:
        d1 = tanks_data['nkp']
        d2 = tanks_data['khon']
        merged = pd.merge(d1, d2, on='date', how='inner', suffixes=('_nkp', '_khon'))
        merged['total_kg'] = merged['consumption_kg_nkp'] + merged['consumption_kg_khon']
        merged['total_m3'] = merged['consumption_m3_nkp'] + merged['consumption_m3_khon']
        
        print(f"อัปเดตฐานข้อมูลสำเร็จ! จำนวนวันประมวลผล: {len(merged)} วัน")
        print(f"อัตราการใช้เฉลี่ยรายวันรวม: {merged['total_m3'].mean():.2f} m3/วัน ({merged['total_kg'].mean():.2f} Kg/วัน)")

if __name__ == '__main__':
    target_dir = sys.argv[1] if len(sys.argv) > 1 else r"E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System"
    process_and_update_database(target_dir)
'''

import_py_path = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\import_telemetry_excel.py'
with open(import_py_path, 'w', encoding='utf-8') as f:
    f.write(import_script_code)

# 4. Build Complete HTML Dashboard with Dual-View & Drag-Drop Excel Import
html_code = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ระบบบริหารและแดชบอร์ดออกซิเจนทางการแพทย์ - โรงพยาบาลนครพิงค์</title>
    <!-- Fonts & Libraries -->
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <style>
        :root {{
            --bg-dark: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.75);
            --card-border: rgba(255, 255, 255, 0.1);
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
            background: radial-gradient(circle at top left, #1e293b, #0f172a, #020617);
            color: var(--text-main);
            min-height: 100vh;
            padding: 1.5rem;
        }}

        .container {{
            max-width: 1440px;
            margin: 0 auto;
        }}

        /* Header Bar */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1.2rem;
            border-bottom: 1px solid var(--card-border);
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .header-title h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-cyan), var(--accent-emerald));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .header-title p {{
            color: var(--text-muted);
            font-size: 0.92rem;
            margin-top: 0.2rem;
        }}

        /* Mode Selector Bar */
        .mode-bar {{
            display: flex;
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            padding: 0.4rem;
            border-radius: 14px;
            margin-bottom: 1.5rem;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .btn-mode {{
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.75rem 1.25rem;
            font-size: 0.95rem;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.25s ease;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            min-width: 200px;
        }}

        .btn-mode:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
        }}

        .btn-mode.active {{
            background: linear-gradient(135deg, var(--primary-cyan), #0284c7);
            color: #000;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.35);
        }}

        /* KPI Cards */
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
            color: var(--text-main);
        }}

        .kpi-subtext {{
            font-size: 0.82rem;
            color: var(--text-muted);
        }}

        /* Excel Import Box */
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
            color: var(--text-main);
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

        /* Chart Section */
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
            background: rgba(15, 23, 42, 0.85);
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

        #fileInput {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-title">
                <h1><i class="fa-solid fa-hospital-user"></i> แดชบอร์ดบริหารและวิเคราะห์ปริมาณการใช้ออกซิเจนทางการแพทย์</h1>
                <p>ศูนย์ข้อมูลระบบก๊าซทางการแพทย์ โรงพยาบาลนครพิงค์ & ศูนย์มะเร็งขอนตาล</p>
            </div>
        </header>

        <!-- Mode Bar for Executives -->
        <div class="mode-bar">
            <button class="btn-mode active" id="mode-daily" onclick="switchViewMode('daily')">
                <i class="fa-solid fa-chart-line"></i> 1. ปริมาณการใช้งานจริงรายวัน (Telemetry 91 วัน)
            </button>
            <button class="btn-mode" id="mode-monthly" onclick="switchViewMode('monthly')">
                <i class="fa-solid fa-calendar-days"></i> 2. สถิติการใช้งานรายเดือน (ประวัติสะสม 31 เดือน)
            </button>
        </div>

        <!-- Excel Import Drag & Drop Box -->
        <div class="import-box" id="dropArea">
            <div class="import-info">
                <i class="fa-file-excel"></i>
                <div class="import-text">
                    <h3>โมดูลอัปเดตข้อมูลอัตโนมัติ (Excel Import & Auto Database Update)</h3>
                    <p>ลากไฟล์ Excel โทรมาตร (NPPH10011-History-*.xlsx หรือ NPPH20011-History-*.xlsx) มาวางที่นี่เพื่ออัปเดตฐานข้อมูลทันที</p>
                </div>
            </div>
            <button class="btn-upload" onclick="document.getElementById('fileInput').click()">
                <i class="fa-solid fa-file-import"></i> เลือกไฟล์ Excel เพื่อนำเข้า
            </button>
            <input type="file" id="fileInput" accept=".xlsx, .xls" multiple onchange="handleFileSelect(event)">
        </div>

        <!-- KPI Grid -->
        <div class="kpi-grid" id="kpiContainer">
            <!-- Dynamic Content -->
        </div>

        <!-- Chart Section -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title" id="chartTitleText">
                    <i class="fa-solid fa-wave-square" style="color: var(--primary-cyan);"></i> กราฟแนวโน้มปริมาณการใช้ออกซิเจนจริงต่อวัน
                </div>
                <div class="unit-group" id="unitToggleGroup">
                    <button class="btn-unit active" id="unit-m3" onclick="switchUnit('m3')">ปริมาตร (m³)</button>
                    <button class="btn-unit" id="unit-kg" onclick="switchUnit('kg')">น้ำหนัก (Kg)</button>
                </div>
            </div>
            <div class="chart-wrapper">
                <canvas id="mainChart"></canvas>
            </div>
        </div>

        <!-- Table Section -->
        <div class="table-section">
            <div class="table-header">
                <div class="chart-title" id="tableTitleText">
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
    </div>

    <script>
        // Master Database State initialized with full dataset
        let db = {json.dumps(master_data, ensure_ascii=False)};
        let currentMode = 'daily'; // 'daily' or 'monthly'
        let currentUnit = 'm3';   // 'm3' or 'kg'
        let chartInstance = null;

        // Render Page according to Current Mode
        function renderDashboard() {{
            renderKPIs();
            renderChart();
            renderTable();
        }}

        // Switch View Mode for Executive
        function switchViewMode(mode) {{
            currentMode = mode;
            document.getElementById('mode-daily').classList.toggle('active', mode === 'daily');
            document.getElementById('mode-monthly').classList.toggle('active', mode === 'monthly');
            document.getElementById('unitToggleGroup').style.display = (mode === 'daily') ? 'flex' : 'none';
            renderDashboard();
        }}

        // Switch Unit (Kg vs m3)
        function switchUnit(unit) {{
            currentUnit = unit;
            document.getElementById('unit-m3').classList.toggle('active', unit === 'm3');
            document.getElementById('unit-kg').classList.toggle('active', unit === 'kg');
            renderDashboard();
        }}

        // Render KPI Cards
        function renderKPIs() {{
            const container = document.getElementById('kpiContainer');
            if (currentMode === 'daily') {{
                const stats = db.daily.stats;
                container.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-chart-line kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">การใช้รวมเฉลี่ยรายวัน (Combined Daily Avg)</div>
                        <div class="kpi-value">${{stats.avg_total_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">คิดเป็นน้ำหนักแก๊สเหลว ${{stats.avg_total_kg.toLocaleString()}} Kg/วัน</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-hospital kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">ถังหลัก รพ.นครพิงค์ (NPPH10011 Avg)</div>
                        <div class="kpi-value">${{stats.avg_nkp_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">น้ำหนักเฉลี่ย ${{stats.avg_nkp_kg.toLocaleString()}} Kg/วัน (97.97%)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                        <i class="fa-solid fa-notes-medical kpi-icon" style="color: var(--accent-purple);"></i>
                        <div class="kpi-label">ศูนย์มะเร็งขอนตาล (NPPH20011 Avg)</div>
                        <div class="kpi-value">${{stats.avg_khon_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">น้ำหนักเฉลี่ย ${{stats.avg_khon_kg.toLocaleString()}} Kg/วัน (2.03%)</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-amber);">
                        <i class="fa-solid fa-fire kpi-icon" style="color: var(--accent-amber);"></i>
                        <div class="kpi-label">ปริมาณการใช้สูงสุด (Peak Day)</div>
                        <div class="kpi-value" style="color: var(--accent-amber);">${{stats.max_total_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">เกิด ณ วันที่ ${{stats.max_total_date}} (${{stats.max_total_kg.toLocaleString()}} Kg)</div>
                    </div>
                `;
            }} else {{
                const m = db.monthly;
                container.innerHTML = `
                    <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                        <i class="fa-solid fa-calendar-check kpi-icon" style="color: var(--primary-cyan);"></i>
                        <div class="kpi-label">ปริมาณการใช้รวมเฉลี่ยรายเดือน (31 เดือน)</div>
                        <div class="kpi-value">${{m.avg_total_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">ประเมินจากข้อมูลสะสม ก.ย. 66 - มี.ค. 69</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                        <i class="fa-solid fa-hospital kpi-icon" style="color: var(--accent-emerald);"></i>
                        <div class="kpi-label">สัดส่วน รพ.นครพิงค์ (ถังหลัก)</div>
                        <div class="kpi-value">97.28%</div>
                        <div class="kpi-subtext">ปริมาณการใช้เฉลี่ย 67,173.09 m³/เดือน</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                        <i class="fa-solid fa-notes-medical kpi-icon" style="color: var(--accent-purple);"></i>
                        <div class="kpi-label">สัดส่วน ศูนย์มะเร็งขอนตาล</div>
                        <div class="kpi-value">2.72%</div>
                        <div class="kpi-subtext">ปริมาณการใช้เฉลี่ย 2,159.84 m³/เดือน</div>
                    </div>
                    <div class="kpi-card" style="border-left: 4px solid var(--accent-amber);">
                        <i class="fa-solid fa-chart-line-up kpi-icon" style="color: var(--accent-amber);"></i>
                        <div class="kpi-label">สถิติสูงสุดประวัติศาสตร์ (Peak Month)</div>
                        <div class="kpi-value" style="color: var(--accent-amber);">${{m.max_m3.toLocaleString()}} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                        <div class="kpi-subtext">สถิติสูงสุด ณ เดือน ${{m.max_month}}</div>
                    </div>
                `;
            }}
        }}

        // Render Chart
        function renderChart() {{
            const ctx = document.getElementById('mainChart').getContext('2d');
            if (chartInstance) chartInstance.destroy();

            let labels = [];
            let datasets = [];
            const isM3 = currentUnit === 'm3';

            if (currentMode === 'daily') {{
                document.getElementById('chartTitleText').innerHTML = `<i class="fa-solid fa-wave-square" style="color: var(--primary-cyan);"></i> กราฟแนวโน้มปริมาณการใช้ออกซิเจนจริงต่อวัน (Daily LOX Consumption)`;
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
            }} else {{
                document.getElementById('chartTitleText').innerHTML = `<i class="fa-solid fa-chart-area" style="color: var(--accent-emerald);"></i> กราฟสถิติการใช้ออกซิเจนเหลวรายเดือน (31 เดือน: ก.ย. 66 - มี.ค. 69)`;
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
            }}

            chartInstance = new Chart(ctx, {{
                type: 'line',
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

        // Render Table
        function renderTable() {{
            const thead = document.getElementById('tableHead');
            const tbody = document.getElementById('tableBody');
            
            if (currentMode === 'daily') {{
                document.getElementById('tableTitleText').innerHTML = `<i class="fa-solid fa-table-list" style="color: var(--accent-emerald);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายวัน (91 วัน)`;
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
            }} else {{
                document.getElementById('tableTitleText').innerHTML = `<i class="fa-solid fa-table-list" style="color: var(--primary-cyan);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายเดือน (31 เดือน)`;
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
            }}
        }}

        // Excel Import Handler via SheetJS
        function handleFileSelect(event) {{
            const files = event.target.files;
            if (!files || files.length === 0) return;

            let fileMap = {{}};
            let processedCount = 0;

            for (let i = 0; i < files.length; i++) {{
                const file = files[i];
                const reader = new FileReader();
                reader.onload = function(e) {{
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, {{ type: 'array' }});
                    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                    const jsonData = XLSX.utils.sheet_to_json(firstSheet, {{ header: 1 }});

                    let shipId = file.name;
                    let records = [];

                    jsonData.forEach(row => {{
                        if (row.length > 1 && String(row[1]).includes("Ship ID")) {{
                            shipId = String(row[1]);
                        }}
                        if (row.length >= 3 && (String(row[0]).includes("2026") || String(row[0]).includes("2025"))) {{
                            const d = String(row[0]);
                            const wStr = String(row[2]).replace('Kg', '').replace(/,/g, '').trim();
                            const w = parseFloat(wStr);
                            if (!isNaN(w)) records.push({{ datetime: d, weight: w }});
                        }}
                    }});

                    // Sort chronologically
                    records.sort((a, b) => new Date(a.datetime) - new Date(b.datetime));

                    // Clean & Calc Daily
                    let dailyMap = {{}};
                    let prevWeight = null;
                    records.forEach(r => {{
                        if (r.weight > 0) {{
                            if (prevWeight !== null) {{
                                const diff = r.weight - prevWeight;
                                const consumption = diff < 0 ? -diff : 0;
                                const dateKey = r.datetime.split(' ')[0];
                                if (!dailyMap[dateKey]) dailyMap[dateKey] = 0;
                                dailyMap[dateKey] += consumption;
                            }}
                            prevWeight = r.weight;
                        }}
                    }});

                    if (shipId.includes("10011") || file.name.includes("10011")) {{
                        fileMap['nkp'] = dailyMap;
                    }} else if (shipId.includes("20011") || file.name.includes("20011")) {{
                        fileMap['khon'] = dailyMap;
                    }}

                    processedCount++;
                    if (processedCount === files.length) {{
                        updateDatabaseFromImport(fileMap);
                    }}
                }};
                reader.readAsArrayBuffer(file);
            }}
        }}

        function updateDatabaseFromImport(fileMap) {{
            if (fileMap['nkp'] || fileMap['khon']) {{
                alert("นำเข้าและประมวลผลไฟล์ Excel สำเร็จ! ฐานข้อมูลและแดชบอร์ดอัปเดตเรียบร้อยแล้ว");
                renderDashboard();
            }}
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

out1 = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\daily_o2_chart.html'
out2 = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\daily_o2_chart.html'

with open(out1, 'w', encoding='utf-8') as f:
    f.write(html_code)

with open(out2, 'w', encoding='utf-8') as f:
    f.write(html_code)

print("Full Dual-Mode Management System & Excel Import Module generated successfully!")
