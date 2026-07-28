import zipfile, xml.etree.ElementTree as ET, pandas as pd, numpy as np, json

def parse_history(path):
    rows_data = []
    with zipfile.ZipFile(path) as z:
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
    
    records = []
    for r in rows_data:
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
    return df

path1 = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\NPPH10011-History-28072026.xlsx'
path2 = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\NPPH20011-History-28072026.xlsx'

df1 = parse_history(path1)
df2 = parse_history(path2)

def clean_telemetry(df):
    df_valid = df[df['weight_kg'] > 0].copy()
    df_valid['diff'] = df_valid['weight_kg'].diff()
    
    df_valid['consumption_kg'] = df_valid['diff'].apply(lambda x: -x if (x is not None and x < 0) else 0)
    df_valid['refill_kg'] = df_valid['diff'].apply(lambda x: x if (x is not None and x > 100) else 0)
    df_valid['date'] = df_valid['datetime'].dt.strftime('%Y-%m-%d')
    
    daily = df_valid.groupby('date').agg(
        consumption_kg=('consumption_kg', 'sum'),
        refill_kg=('refill_kg', 'sum'),
        min_weight=('weight_kg', 'min'),
        max_weight=('weight_kg', 'max'),
        valid_hours=('weight_kg', 'count')
    ).reset_index()
    
    daily['consumption_m3'] = daily['consumption_kg'] * 0.755
    return daily

daily1 = clean_telemetry(df1)
daily2 = clean_telemetry(df2)

print("=== CLEANED NPPH10011 (Main Hospital Tank) Daily Summary ===")
print("Days count:", len(daily1))
print(f"Average Daily Consumption: {daily1['consumption_kg'].mean():.2f} kg ({daily1['consumption_m3'].mean():.2f} m3)")
max1 = daily1.loc[daily1['consumption_kg'].idxmax()]
min1 = daily1.loc[daily1['consumption_kg'].idxmin()]
print(f"Max Daily Consumption: {max1['consumption_kg']:.2f} kg ({max1['consumption_m3']:.2f} m3) on {max1['date']}")
print(f"Min Daily Consumption: {min1['consumption_kg']:.2f} kg ({min1['consumption_m3']:.2f} m3) on {min1['date']}")

print("\n=== CLEANED NPPH20011 (Khon San Cancer Center Tank) Daily Summary ===")
print("Days count:", len(daily2))
print(f"Average Daily Consumption: {daily2['consumption_kg'].mean():.2f} kg ({daily2['consumption_m3'].mean():.2f} m3)")
max2 = daily2.loc[daily2['consumption_kg'].idxmax()]
min2 = daily2.loc[daily2['consumption_kg'].idxmin()]
print(f"Max Daily Consumption: {max2['consumption_kg']:.2f} kg ({max2['consumption_m3']:.2f} m3) on {max2['date']}")
print(f"Min Daily Consumption: {min2['consumption_kg']:.2f} kg ({min2['consumption_m3']:.2f} m3) on {min2['date']}")

merged = pd.merge(daily1[['date', 'consumption_kg', 'consumption_m3']], 
                  daily2[['date', 'consumption_kg', 'consumption_m3']], 
                  on='date', how='inner', suffixes=('_nkp', '_khon'))
merged['total_kg'] = merged['consumption_kg_nkp'] + merged['consumption_kg_khon']
merged['total_m3'] = merged['consumption_m3_nkp'] + merged['consumption_m3_khon']

print("\n=== COMBINED DAILY SUMMARY ===")
print(f"Average Combined Daily: {merged['total_kg'].mean():.2f} kg ({merged['total_m3'].mean():.2f} m3)")
max_c = merged.loc[merged['total_kg'].idxmax()]
min_c = merged.loc[merged['total_kg'].idxmin()]
print(f"Max Combined Daily: {max_c['total_kg']:.2f} kg ({max_c['total_m3']:.2f} m3) on {max_c['date']}")
print(f"Min Combined Daily: {min_c['total_kg']:.2f} kg ({min_c['total_m3']:.2f} m3) on {min_c['date']}")

data_dict = {
    'dates': merged['date'].tolist(),
    'nkp_kg': [round(x, 2) for x in merged['consumption_kg_nkp']],
    'nkp_m3': [round(x, 2) for x in merged['consumption_m3_nkp']],
    'khon_kg': [round(x, 2) for x in merged['consumption_kg_khon']],
    'khon_m3': [round(x, 2) for x in merged['consumption_m3_khon']],
    'total_kg': [round(x, 2) for x in merged['total_kg']],
    'total_m3': [round(x, 2) for x in merged['total_m3']],
    'stats': {
        'avg_nkp_kg': round(daily1['consumption_kg'].mean(), 2),
        'avg_nkp_m3': round(daily1['consumption_m3'].mean(), 2),
        'avg_khon_kg': round(daily2['consumption_kg'].mean(), 2),
        'avg_khon_m3': round(daily2['consumption_m3'].mean(), 2),
        'avg_total_kg': round(merged['total_kg'].mean(), 2),
        'avg_total_m3': round(merged['total_m3'].mean(), 2),
        'max_total_kg': round(max_c['total_kg'], 2),
        'max_total_m3': round(max_c['total_m3'], 2),
        'max_total_date': max_c['date'],
        'min_total_kg': round(min_c['total_kg'], 2),
        'min_total_m3': round(min_c['total_m3'], 2),
        'min_total_date': min_c['date'],
    }
}

with open(r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch\telemetry_daily_data.json', 'w', encoding='utf-8') as f:
    json.dump(data_dict, f, ensure_ascii=False, indent=2)

print("Saved telemetry_daily_data.json successfully!")
