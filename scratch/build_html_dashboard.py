import json, os

json_path = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch\telemetry_daily_data.json'
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

html_content = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>แดชบอร์ดสรุปปริมาณการใช้ออกซิเจนรายวัน - โรงพยาบาลนครพิงค์</title>
    <!-- Google Fonts & Chart.js / FontAwesome -->
    <link href="https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-dark: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-border: rgba(255, 255, 255, 0.1);
            --primary-cyan: #06b6d4;
            --accent-emerald: #10b981;
            --accent-purple: #a855f7;
            --accent-amber: #f59e0b;
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
            padding: 2rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1fr solid var(--card-border);
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
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }}

        .badge-live {{
            background: rgba(16, 185, 129, 0.2);
            color: var(--accent-emerald);
            border: 1px solid var(--accent-emerald);
            padding: 0.35rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            display: inline-flex;
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

        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2rem;
        }}

        .kpi-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            position: relative;
            overflow: hidden;
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
            opacity: 0.25;
        }}

        .kpi-label {{
            color: var(--text-muted);
            font-size: 0.88rem;
            font-weight: 500;
        }}

        .kpi-value {{
            font-size: 1.9rem;
            font-weight: 700;
            margin: 0.4rem 0;
            color: var(--text-main);
        }}

        .kpi-subtext {{
            font-size: 0.8rem;
            color: var(--text-muted);
        }}

        /* Chart Controls & Container */
        .chart-section {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.75rem;
            margin-bottom: 2rem;
        }}

        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
            gap: 1rem;
        }}

        .chart-title {{
            font-size: 1.2rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .btn-group {{
            display: flex;
            background: rgba(15, 23, 42, 0.6);
            padding: 0.25rem;
            border-radius: 10px;
            border: 1px solid var(--card-border);
        }}

        .btn-toggle {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.45rem 1rem;
            font-size: 0.88rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 500;
        }}

        .btn-toggle.active {{
            background: var(--primary-cyan);
            color: #000;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(6, 182, 212, 0.4);
        }}

        .chart-wrapper {{
            position: relative;
            height: 420px;
            width: 100%;
        }}

        /* Data Table */
        .table-section {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.5rem;
            overflow: hidden;
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
            padding: 0.5rem 0.9rem;
            color: var(--text-main);
            outline: none;
            font-size: 0.88rem;
            width: 240px;
        }}

        .table-wrapper {{
            overflow-x: auto;
            max-height: 400px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }}

        th {{
            background: rgba(15, 23, 42, 0.8);
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
            color: var(--text-main);
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.03);
        }}

        .tag-peak {{
            background: rgba(245, 158, 11, 0.2);
            color: var(--accent-amber);
            border: 1px solid var(--accent-amber);
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
        }}

        footer {{
            text-align: center;
            margin-top: 2rem;
            color: var(--text-muted);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="header-title">
                <h1><i class="fa-solid to-fa-hospital"></i> รายงานสถิติปริมาณการใช้ออกซิเจนรายวัน (Daily LOX Consumption)</h1>
                <p>ข้อมูลวิเคราะห์จากระบบโทรมาตรทางไกล (IoT Telemetry Logs) โรงพยาบาลนครพิงค์ & ศูนย์มะเร็งขอนตาล (91 วัน)</p>
            </div>
            <div class="badge-live">
                <div class="pulse-dot"></div> Telemetry Verified (NPPH10011 / NPPH20011)
            </div>
        </header>

        <!-- KPI Metric Cards -->
        <div class="kpi-grid">
            <div class="kpi-card" style="border-left: 4px solid var(--primary-cyan);">
                <i class="fa-solid fa-chart-line kpi-icon" style="color: var(--primary-cyan);"></i>
                <div class="kpi-label">การใช้รวมเฉลี่ยรายวัน (Combined Daily Avg)</div>
                <div class="kpi-value">{data['stats']['avg_total_m3']:,.2f} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                <div class="kpi-subtext">คิดเป็นน้ำหนักแก๊สเหลว {data['stats']['avg_total_kg']:,.2f} Kg/วัน</div>
            </div>

            <div class="kpi-card" style="border-left: 4px solid var(--accent-emerald);">
                <i class="fa-solid fa-hospital-user kpi-icon" style="color: var(--accent-emerald);"></i>
                <div class="kpi-label">ถังหลัก รพ.นครพิงค์ (NPPH10011 Avg)</div>
                <div class="kpi-value">{data['stats']['avg_nkp_m3']:,.2f} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                <div class="kpi-subtext">น้ำหนักเฉลี่ย {data['stats']['avg_nkp_kg']:,.2f} Kg/วัน (97.97%)</div>
            </div>

            <div class="kpi-card" style="border-left: 4px solid var(--accent-purple);">
                <i class="fa-solid fa-notes-medical kpi-icon" style="color: var(--accent-purple);"></i>
                <div class="kpi-label">ศูนย์มะเร็งขอนตาล (NPPH20011 Avg)</div>
                <div class="kpi-value">{data['stats']['avg_khon_m3']:,.2f} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                <div class="kpi-subtext">น้ำหนักเฉลี่ย {data['stats']['avg_khon_kg']:,.2f} Kg/วัน (2.03%)</div>
            </div>

            <div class="kpi-card" style="border-left: 4px solid var(--accent-amber);">
                <i class="fa-solid fa-fire kpi-icon" style="color: var(--accent-amber);"></i>
                <div class="kpi-label">ปริมาณการใช้สูงสุด (Peak Day)</div>
                <div class="kpi-value" style="color: var(--accent-amber);">{data['stats']['max_total_m3']:,.2f} <span style="font-size: 1.1rem; color: var(--text-muted);">m³</span></div>
                <div class="kpi-subtext">เกิดขึ้นเมื่อวันที่ {data['stats']['max_total_date']} ({data['stats']['max_total_kg']:,.2f} Kg)</div>
            </div>
        </div>

        <!-- Line Chart Section -->
        <div class="chart-section">
            <div class="chart-header">
                <div class="chart-title">
                    <i class="fa-solid fa-wave-square" style="color: var(--primary-cyan);"></i> กราฟแสดงแนวโน้มปริมาณการใช้งานออกซิเจนจริงต่อวัน (Daily Consumption Trend)
                </div>
                <div class="btn-group">
                    <button class="btn-toggle active" id="btn-m3" onclick="switchUnit('m3')">ปริมาตร (m³)</button>
                    <button class="btn-toggle" id="btn-kg" onclick="switchUnit('kg')">น้ำหนัก (Kg)</button>
                </div>
            </div>
            <div class="chart-wrapper">
                <canvas id="dailyO2Chart"></canvas>
            </div>
        </div>

        <!-- Data Table Section -->
        <div class="table-section">
            <div class="table-header">
                <div class="chart-title">
                    <i class="fa-solid fa-table-list" style="color: var(--accent-emerald);"></i> ตารางสถิติปริมาณการใช้ออกซิเจนรายวัน (91 วัน)
                </div>
                <input type="text" id="searchInput" class="search-box" placeholder="ค้นหาตามวันที่ (YYYY-MM-DD)..." onkeyup="filterTable()">
            </div>
            <div class="table-wrapper">
                <table id="dataTable">
                    <thead>
                        <tr>
                            <th>ลำดับ</th>
                            <th>วันที่ (Date)</th>
                            <th>รพ.นครพิงค์ (Kg)</th>
                            <th>รพ.นครพิงค์ (m³)</th>
                            <th>ศูนย์มะเร็งขอนตาล (Kg)</th>
                            <th>ศูนย์มะเร็งขอนตาล (m³)</th>
                            <th>ยอดรวมทั้งสิ้น (Kg)</th>
                            <th>ยอดรวมทั้งสิ้น (m³)</th>
                            <th>สถานะ</th>
                        </tr>
                    </thead>
                    <tbody>
"""

for idx, (d, nkp_kg, nkp_m3, khon_kg, khon_m3, tot_kg, tot_m3) in enumerate(
    zip(data['dates'], data['nkp_kg'], data['nkp_m3'], data['khon_kg'], data['khon_m3'], data['total_kg'], data['total_m3']), 
    start=1
):
    tag = ""
    if d == data['stats']['max_total_date']:
        tag = '<span class="tag-peak">🔥 Peak Day</span>'
    elif d == data['stats']['min_total_date']:
        tag = '<span style="color: #94a3b8;">❄️ Min Day</span>'

    html_content += f"""                        <tr>
                            <td>{idx}</td>
                            <td><strong>{d}</strong></td>
                            <td>{nkp_kg:,.2f}</td>
                            <td>{nkp_m3:,.2f}</td>
                            <td>{khon_kg:,.2f}</td>
                            <td>{khon_m3:,.2f}</td>
                            <td><strong>{tot_kg:,.2f}</strong></td>
                            <td><strong style="color: var(--primary-cyan);">{tot_m3:,.2f}</strong></td>
                            <td>{tag}</td>
                        </tr>
"""

html_content += f"""                    </tbody>
                </table>
            </div>
        </div>

        <footer>
            <p>รายงานสร้างโดย Antigravity AI - กลุ่มงานวิศวกรรมความปลอดภัยและระบบก๊าซทางการแพทย์ โรงพยาบาลนครพิงค์</p>
        </footer>
    </div>

    <!-- Chart Script -->
    <script>
        const rawData = {json.dumps(data, ensure_ascii=False)};
        let currentUnit = 'm3';
        let chartInstance = null;

        function getChartDatasets(unit) {{
            const isM3 = unit === 'm3';
            return [
                {{
                    label: isM3 ? 'ยอดรวมทั้งสิ้น (m³)' : 'ยอดรวมทั้งสิ้น (Kg)',
                    data: isM3 ? rawData.total_m3 : rawData.total_kg,
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 2,
                    pointHoverRadius: 6
                }},
                {{
                    label: isM3 ? 'รพ.นครพิงค์ ถังหลัก (m³)' : 'รพ.นครพิงค์ ถังหลัก (Kg)',
                    data: isM3 ? rawData.nkp_m3 : rawData.nkp_kg,
                    borderColor: '#10b981',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.35,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }},
                {{
                    label: isM3 ? 'ศูนย์มะเร็งขอนตาล (m³)' : 'ศูนย์มะเร็งขอนตาล (Kg)',
                    data: isM3 ? rawData.khon_m3 : rawData.khon_kg,
                    borderColor: '#a855f7',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.35,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }}
            ];
        }}

        function renderChart(unit) {{
            const ctx = document.getElementById('dailyO2Chart').getContext('2d');
            if (chartInstance) {{
                chartInstance.destroy();
            }}

            chartInstance = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: rawData.dates,
                    datasets: getChartDatasets(unit)
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{
                        mode: 'index',
                        intersect: false
                    }},
                    plugins: {{
                        legend: {{
                            labels: {{
                                color: '#f8fafc',
                                font: {{ family: 'Prompt', size: 12 }}
                            }}
                        }},
                        tooltip: {{
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleFont: {{ family: 'Prompt', size: 13, weight: 'bold' }},
                            bodyFont: {{ family: 'Prompt', size: 12 }},
                            padding: 12,
                            borderColor: 'rgba(255,255,255,0.1)',
                            borderWidth: 1,
                            callbacks: {{
                                label: function(context) {{
                                    let label = context.dataset.label || '';
                                    if (label) label += ': ';
                                    if (context.parsed.y !== null) {{
                                        label += new Intl.NumberFormat('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}).format(context.parsed.y);
                                        label += unit === 'm3' ? ' m³' : ' Kg';
                                    }}
                                    return label;
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                            ticks: {{ color: '#94a3b8', font: {{ family: 'Prompt', size: 11 }} }}
                        }},
                        y: {{
                            grid: {{ color: 'rgba(255, 255, 255, 0.08)' }},
                            ticks: {{
                                color: '#94a3b8',
                                font: {{ family: 'Prompt', size: 11 }},
                                callback: function(value) {{
                                    return new Intl.NumberFormat('en-US').format(value) + (unit === 'm3' ? ' m³' : ' Kg');
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        function switchUnit(unit) {{
            currentUnit = unit;
            document.getElementById('btn-m3').classList.toggle('active', unit === 'm3');
            document.getElementById('btn-kg').classList.toggle('active', unit === 'kg');
            renderChart(unit);
        }}

        function filterTable() {{
            const input = document.getElementById('searchInput').value.toLowerCase();
            const table = document.getElementById('dataTable');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const tdDate = tr[i].getElementsByTagName('td')[1];
                if (tdDate) {{
                    const txtValue = tdDate.textContent || tdDate.innerText;
                    tr[i].style.display = txtValue.toLowerCase().indexOf(input) > -1 ? '' : 'none';
                }}
            }}
        }}

        window.onload = function() {{
            renderChart('m3');
        }};
    </script>
</body>
</html>
"""

out1 = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\daily_o2_chart.html'
out2 = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\daily_o2_chart.html'

with open(out1, 'w', encoding='utf-8') as f:
    f.write(html_content)

with open(out2, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("HTML Dashboard successfully saved to both system locations!")
