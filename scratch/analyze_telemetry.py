import zipfile, xml.etree.ElementTree as ET, pandas as pd, numpy as np

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

def calc_daily_consumption(df):
    df['diff'] = df['weight_kg'].diff()
    df['consumption_kg'] = df['diff'].apply(lambda x: -x if x < 0 else 0)
    df['refill_kg'] = df['diff'].apply(lambda x: x if x > 0 else 0)
    df['date'] = df['datetime'].dt.strftime('%Y-%m-%d')
    
    daily = df.groupby('date').agg(
        total_consumption_kg=('consumption_kg', 'sum'),
        total_refill_kg=('refill_kg', 'sum'),
        start_weight=('weight_kg', 'first'),
        end_weight=('weight_kg', 'last'),
        reading_count=('weight_kg', 'count')
    ).reset_index()
    
    daily['consumption_m3'] = daily['total_consumption_kg'] * 0.755
    return daily

daily1 = calc_daily_consumption(df1)
daily2 = calc_daily_consumption(df2)

d1_full = daily1[daily1['reading_count'] >= 23].copy()
d2_full = daily2[daily2['reading_count'] >= 23].copy()

print("=== NPPH10011 (Main Hospital Tank) Daily Summary ===")
print("Full days count 1:", len(d1_full))
print(f"Average daily consumption NPPH10011: {d1_full['total_consumption_kg'].mean():.2f} kg ({d1_full['consumption_m3'].mean():.2f} m3)")
max_idx1 = d1_full['total_consumption_kg'].idxmax()
min_idx1 = d1_full['total_consumption_kg'].idxmin()
print(f"Max daily consumption NPPH10011: {d1_full.loc[max_idx1, 'total_consumption_kg']:.2f} kg ({d1_full.loc[max_idx1, 'consumption_m3']:.2f} m3) on {d1_full.loc[max_idx1, 'date']}")
print(f"Min daily consumption NPPH10011: {d1_full.loc[min_idx1, 'total_consumption_kg']:.2f} kg ({d1_full.loc[min_idx1, 'consumption_m3']:.2f} m3) on {d1_full.loc[min_idx1, 'date']}")

print("\n=== NPPH20011 (Khon San Cancer Center Tank) Daily Summary ===")
print("Full days count 2:", len(d2_full))
print(f"Average daily consumption NPPH20011: {d2_full['total_consumption_kg'].mean():.2f} kg ({d2_full['consumption_m3'].mean():.2f} m3)")
max_idx2 = d2_full['total_consumption_kg'].idxmax()
min_idx2 = d2_full['total_consumption_kg'].idxmin()
print(f"Max daily consumption NPPH20011: {d2_full.loc[max_idx2, 'total_consumption_kg']:.2f} kg ({d2_full.loc[max_idx2, 'consumption_m3']:.2f} m3) on {d2_full.loc[max_idx2, 'date']}")
print(f"Min daily consumption NPPH20011: {d2_full.loc[min_idx2, 'total_consumption_kg']:.2f} kg ({d2_full.loc[min_idx2, 'consumption_m3']:.2f} m3) on {d2_full.loc[min_idx2, 'date']}")

# Combine daily data
merged = pd.merge(d1_full[['date', 'total_consumption_kg', 'consumption_m3']], 
                  d2_full[['date', 'total_consumption_kg', 'consumption_m3']], 
                  on='date', how='inner', suffixes=('_nkp', '_khon'))
merged['total_consumption_kg_combined'] = merged['total_consumption_kg_nkp'] + merged['total_consumption_kg_khon']
merged['total_consumption_m3_combined'] = merged['consumption_m3_nkp'] + merged['consumption_m3_khon']

print("\n=== Combined Daily Summary (90 Days: May 2026 - Jul 2026) ===")
print("Average Combined Daily Consumption:", f"{merged['total_consumption_kg_combined'].mean():.2f} kg ({merged['total_consumption_m3_combined'].mean():.2f} m3)")
print("Max Combined Daily Consumption:", f"{merged['total_consumption_kg_combined'].max():.2f} kg ({merged['total_consumption_m3_combined'].max():.2f} m3)")
print("Min Combined Daily Consumption:", f"{merged['total_consumption_kg_combined'].min():.2f} kg ({merged['total_consumption_m3_combined'].min():.2f} m3)")

merged.to_csv(r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch\daily_o2_consumption.csv', index=False)
print("Saved daily_o2_consumption.csv!")
