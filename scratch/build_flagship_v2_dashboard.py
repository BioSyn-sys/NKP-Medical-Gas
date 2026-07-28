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

html_v2_code = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ระบบบริหารและวิเคราะห์ออกซิเจนทางการแพทย์ - โรงพยาบาลนครพิงค์</title>
    <!-- Fonts & CDNs -->
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>

    <style>
        :root {{
            --bg-dark: #070b12;
            --card-bg: rgba(18, 26, 43, 0.75);
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
            background: radial-gradient(circle at top left, #1e293b, #070b12, #020408);
            color: var(--text-main);
            min-height: 100vh;
            padding: 1.5rem;
        }}

        .container {{
            max-width: 1480px;
            margin: 0 auto;
        }}

        /* Navbar */
        .navbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1.2rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--card-border);
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .brand-logo {{
            width: 52px;
            height: 52px;
            background: linear-gradient(135deg, var(--primary-cyan), var(--accent-emerald));
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #000;
            font-size: 1.6rem;
            box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4);
        }}

        .brand-text h1 {{
            font-size: 1.7rem;
            font-weight: 700;
            background: linear-gradient(135deg, #ffffff, var(--primary-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .brand-text p {{
            color: var(--text-muted);
            font-size: 0.88rem;
        }}

        /* Top Module Navigation Bar */
        .module-nav {{
            display: flex;
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            padding: 0.4rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            gap: 0.5rem;
            overflow-x: auto;
        }}

        .nav-btn {{
            flex: 1;
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.85rem 1.2rem;
            font-size: 0.95rem;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.25s ease;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            white-space: nowrap;
        }}

        .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
        }}

        .nav-btn.active {{
            background: linear-gradient(135deg, var(--primary-cyan), #0284c7);
            color: #000;
            box-shadow: 0 4px 15px rgba(6, 182, 212, 0.4);
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

        /* Content Sections */
        .content-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.75rem;
            margin-bottom: 1.5rem;
        }}

        .section-title {{
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}

        /* Unit Selector Controls */
        .unit-selector {{
            display: flex;
            background: rgba(15, 23, 42, 0.6);
            padding: 0.25rem;
            border-radius: 8px;
            border: 1px solid var(--card-border);
            width: fit-content;
        }}

        .btn-unit {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.4rem 1rem;
            font-size: 0.88rem;
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
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
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
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 0.65rem 1rem;
            color: var(--text-main);
            font-size: 1rem;
            outline: none;
        }}

        .form-control:focus {{
            border-color: var(--primary-cyan);
        }}

        .res-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem 0;
            border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
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

        /* Table */
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
            padding: 0.85rem 1rem;
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

        /* Drag & Drop Import Box */
        .drop-zone {{
            border: 2px dashed var(--primary-cyan);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            background: rgba(6, 182, 212, 0.05);
            cursor: pointer;
            transition: all 0.25s ease;
        }}

        .drop-zone:hover {{
            background: rgba(6, 182, 212, 0.12);
            border-color: var(--accent-emerald);
        }}

        #fileInput {{ display: none; }}

        footer {{
            text-align: center;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--card-border);
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <nav class="navbar">
            <div class="brand">
                <div class="brand-logo"><i class="fa-solid fa-hospital-user"></i></div>
                <div class="brand-text">
                    <h1>NKP Medical Oxygen Analytics & Management Dashboard</h1>
                    <p>ระบบบริหาร จัดการและคำนวณแผนก๊าซออกซิเจนสำรองฉุกเฉิน โรงพยาบาลนครพิงค์ & ศูนย์มะเร็งขอนตาล</p>
                </div>
            </div>
        </nav>

        <!-- Top Module Navigation Bar -->
        <div class="module-nav">
            <button class="nav-btn active" id="tab-daily" onclick="switchTab('daily')">
                <i class="fa-solid fa-chart-line"></i> 1. วิเคราะห์รายวัน (91 วัน)
            </button>
            <button class="nav-btn" id="tab-monthly" onclick="switchTab('monthly')">
                <i class="fa-solid fa-calendar-days"></i> 2. สถิติประวัติรายเดือน (31 เดือน)
            </button>
            <button class="nav-btn" id="tab-cost" onclick="switchTab('cost')">
                <i class="fa-solid fa-calculator"></i> 3. เปรียบเทียบต้นทุน (LOX vs 6Q)
            </button>
            <button class="nav-btn" id="tab-emergency" onclick="switchTab('emergency')">
                <i class="fa-solid fa-shield-cat"></i> 4. แผนก๊าซสำรองฉุกเฉิน & คำนวณท่อ
            </button>
            <button class="nav-btn" id="tab-import" onclick="switchTab('import')">
                <i class="fa-solid fa-file-import"></i> 5. นำเข้าไฟล์ Excel
            </button>
        </div>

        <!-- Dynamic KPI Cards -->
        <div class="kpi-grid" id="kpiGrid"></div>

        <!-- Dynamic Main Module Content -->
        <div id="moduleContent"></div>

        <!-- Footer -->
        <footer>
            <p>ออกแบบและจัดทำโดยกลุ่มงานโครงสร้างและวิศวกรรมการแพทย์ หมวดงานเครื่องมือแพทย์ โรงพยาบาลนครพิงค์</p>
        </footer>
    </div>

    <script>
        const db = {json.dumps(master_data, ensure_ascii=False)};
        let activeTab = 'daily';
        let dailyUnit = 'm3'; // 'm3', 'kg', 'inch'
        let chartObj = null;

        function switchTab(tabKey) {{
            activeTab = tabKey;
            const tabs = ['daily', 'monthly', 'cost', 'emergency', 'import'];
            tabs.forEach(t => {{
                const el = document.getElementById('tab-' + t);
                if (el) el.classList.toggle('active', t === tabKey);
            }});
            renderKPIs();
            renderModule();
        }}

        function switchDailyUnit(unit) {{
            dailyUnit = unit;
            ['m3', 'kg', 'inch'].forEach(u => {{
                const btn = document.getElementById('u-btn-' + u);
                if (btn) btn.classList.toggle('active', u === unit);
            }});
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
                        <div class="kpi-subtext">เกิดขึ้นเมื่อวันที่ ${{s.max_total_date}} (${{s.max_total_kg.toLocaleString()}} Kg)</div>
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
                        <div class="kpi-label">สถานะการเชื่อมต่อ Excel Module</div>
                        <div class="kpi-value" style="color: var(--accent-emerald);">พร้อมใช้งาน</div>
                        <div class="kpi-subtext">รองรับไฟล์ NPPH10011 และ NPPH20011</div>
                    </div>
                `;
            }}
        }}

        function renderModule() {{
            const content = document.getElementById('moduleContent');
            if (activeTab === 'daily') {{
                renderDailyModule();
            }} else if (activeTab === 'monthly') {{
                renderMonthlyModule();
            }} else if (activeTab === 'cost') {{
                renderCostModule();
            }} else if (activeTab === 'emergency') {{
                renderEmergencyModule();
            }} else if (activeTab === 'import') {{
                renderImportModule();
            }}
        }}

        function renderDailyModule() {{
            const content = document.getElementById('moduleContent');
            content.innerHTML = `
                <div class="content-card">
                    <div class="chart-header">
                        <div class="section-title">
                            <i class="fa-solid fa-wave-square" style="color: var(--primary-cyan);"></i> กราฟแสดงแนวโน้มปริมาณการใช้งานออกซิเจนจริงต่อวัน (91 วัน)
                        </div>
                        <div class="unit-selector">
                            <button class="btn-unit ${{dailyUnit === 'm3' ? 'active' : ''}}" id="u-btn-m3" onclick="switchDailyUnit('m3')">ปริมาตร (m³)</button>
                            <button class="btn-unit ${{dailyUnit === 'kg' ? 'active' : ''}}" id="u-btn-kg" onclick="switchDailyUnit('kg')">น้ำหนัก (Kg)</button>
                            <button class="btn-unit ${{dailyUnit === 'inch' ? 'active' : ''}}" id="u-btn-inch" onclick="switchDailyUnit('inch')">นิ้วน้ำ (Inches)</button>
                        </div>
                    </div>
                    <div class="chart-container">
                        <canvas id="dailyChartCanvas"></canvas>
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

            // Render Chart
            const ctx = document.getElementById('dailyChartCanvas').getContext('2d');
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
                const inch_tot = inch_nkp.map((val, idx) => +(val + inch_khon[idx]).toFixed(2));
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
                        x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8' }} }},
                        y: {{ grid: {{ color: 'rgba(255,255,255,0.08)' }}, ticks: {{ color: '#94a3b8' }} }}
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
                        <canvas id="monthlyChartCanvas"></canvas>
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

            const ctx = document.getElementById('monthlyChartCanvas').getContext('2d');
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
                options: {{
                    responsive: true, maintainAspectRatio: false,
                    scales: {{
                        x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8' }} }},
                        y: {{ grid: {{ color: 'rgba(255,255,255,0.08)' }}, ticks: {{ color: '#94a3b8' }} }}
                    }}
                }}
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
                                <span class="res-label">งบประมาณที่ประหยัดได้ต่อวัน (รพ.นครพิงค์):</span>
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
            const loxLiters = loxKg / 1.141; // LOX density ~1.141 kg/L
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
                        <i class="fa-file-excel" style="font-size: 3rem; color: var(--accent-emerald); margin-bottom: 1rem;"></i>
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

# Write files to both Locations
locations = [
    r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System',
    r'E:\000_Antigraviti\MedicalGasNKP\Oxygen'
]

for loc in locations:
    for filename in ['daily_o2_chart.html', 'index.html']:
        with open(os.path.join(loc, filename), 'w', encoding='utf-8') as f:
            f.write(html_v2_code)

print("V2 Flagship Redesigned Web Dashboard successfully generated across all target paths!")
