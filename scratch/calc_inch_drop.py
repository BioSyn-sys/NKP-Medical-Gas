import zipfile, xml.etree.ElementTree as ET, pandas as pd

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

df1 = parse_history(r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\NPPH10011-History-28072026.xlsx')
df1_valid = df1[df1['weight_kg'] > 0].copy()
df1_valid['level_inch'] = df1_valid['level'].str.replace('Inch', '').str.strip().astype(float)
df1_valid['inch_diff'] = df1_valid['level_inch'].diff()
df1_valid['inch_drop'] = df1_valid['inch_diff'].apply(lambda x: -x if (x is not None and x < 0) else 0)
df1_valid['date'] = df1_valid['datetime'].dt.strftime('%Y-%m-%d')

daily_inch1 = df1_valid.groupby('date').agg(total_inch_drop=('inch_drop', 'sum')).reset_index()

df2 = parse_history(r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\07_Liquid_Oxygen_Main_System\NPPH20011-History-28072026.xlsx')
df2_valid = df2[df2['weight_kg'] > 0].copy()
df2_valid['level_inch'] = df2_valid['level'].str.replace('Inch', '').str.strip().astype(float)
df2_valid['inch_diff'] = df2_valid['level_inch'].diff()
df2_valid['inch_drop'] = df2_valid['inch_diff'].apply(lambda x: -x if (x is not None and x < 0) else 0)
df2_valid['date'] = df2_valid['datetime'].dt.strftime('%Y-%m-%d')

daily_inch2 = df2_valid.groupby('date').agg(total_inch_drop=('inch_drop', 'sum')).reset_index()

avg1 = daily_inch1['total_inch_drop'].mean()
max1 = daily_inch1['total_inch_drop'].max()
min1 = daily_inch1['total_inch_drop'].min()

avg2 = daily_inch2['total_inch_drop'].mean()
max2 = daily_inch2['total_inch_drop'].max()
min2 = daily_inch2['total_inch_drop'].min()

print("=== INCH DROP PER DAY RESULTS ===")
print(f"NPPH10011 (Main Tank): Average = {avg1:.2f} Inches/day, Max = {max1:.2f} Inches/day, Min = {min1:.2f} Inches/day")
print(f"NPPH20011 (Khon San): Average = {avg2:.2f} Inches/day, Max = {max2:.2f} Inches/day, Min = {min2:.2f} Inches/day")
