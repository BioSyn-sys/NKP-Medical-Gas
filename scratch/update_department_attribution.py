import os, re

target_text = "ออกแบบและจัดทำโดยกลุ่มงานโครงสร้างและวิศวกรรมการแพทย์ หมวดงานเครื่องมือแพทย์ โรงพยาบาลนครพิงค์"

# Update python generator script build_flagship_v2_dashboard.py
builder_script = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch\build_flagship_v2_dashboard.py'
if os.path.exists(builder_script):
    with open(builder_script, 'r', encoding='utf-8') as f:
        code = f.read()
    
    code_updated = re.sub(
        r'ออกแบบและจัดทำโดย.*?โรงพยาบาลนครพิงค์',
        target_text,
        code
    )
    code_updated = re.sub(
        r'กลุ่มงานวิศวกรรมความปลอดภัย.*?โรงพยาบาลนครพิงค์',
        target_text,
        code_updated
    )
    with open(builder_script, 'w', encoding='utf-8') as f:
        f.write(code_updated)
    print("Updated build_flagship_v2_dashboard.py!")

# Re-run build_flagship_v2_dashboard.py
os.system(f'python "{builder_script}"')

# Also update docx report builder script and re-run
report_script = r'E:\000_Antigraviti\MedicalGasNKP\Oxygen\scratch\build_complete_report.py'
if os.path.exists(report_script):
    with open(report_script, 'r', encoding='utf-8') as f:
        rcode = f.read()
    
    rcode_updated = re.sub(
        r'กลุ่มงานวิศวกรรมความปลอดภัย.*?โรงพยาบาลนครพิงค์',
        target_text,
        rcode
    )
    with open(report_script, 'w', encoding='utf-8') as f:
        f.write(rcode_updated)
    print("Updated build_complete_report.py!")

os.system(f'python "{report_script}"')

print("All system files updated with official department attribution!")
