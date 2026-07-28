# ระบบที่ 2: ระบบมอนิเตอร์และสลับฝั่งจ่ายอัตโนมัติ (Automatic Manifold Monitor)

ระบบนี้ใช้บอร์ดไมโครคอนโทรลเลอร์ ESP32 (เช่น TTGO T-Display) ในการตรวจสอบสถานะปริมาณออกซิเจนสำรองในท่อจ่ายฝั่งซ้าย (Left Bank) และฝั่งขวา (Right Bank) รวมถึงมีระบบควบคุมสัญญาณเตือนในพื้นที่และบริการข้อมูลผ่านเว็บเบราว์เซอร์ (Web Server REST API)

---

## 🛠️ 1. รายละเอียดการเชื่อมต่อฮาร์ดแวร์ (Hardware Pinout)

ระบบทำงานบน ESP32 โดยมีการกำหนดขาใช้งาน GPIO ดังต่อไปนี้:

### สวิตช์เซนเซอร์ตรวจจับปริมาณก๊าซ (Sensor Inputs)
* ขาเซนเซอร์กำหนดการเชื่อมต่อเป็นแบบ **Input Pull-up (Active LOW)** (เมื่อสวิตช์ลูกลอย/ความดันทำงาน จะดึงสัญญาณลง GND)

| เซนเซอร์ / อุปกรณ์ | ขา GPIO (ESP32) | คำอธิบายสถานะ |
| :--- | :---: | :--- |
| **Left Bank Empty Sensor** | `25` | ลูกลอยตรวจจับก๊าซฝั่งซ้ายหมด (HIGH = หมด, LOW = ปกติ) |
| **Right Bank Empty Sensor** | `26` | ลูกลอยตรวจจับก๊าซฝั่งขวาหมด (HIGH = หมด, LOW = ปกติ) |

### อุปกรณ์แจ้งเตือนสถานะในพื้นที่ (Local Indicators)
* **RGB LED:** แสดงผลสถานะเฉพาะฝั่งซ้าย (Common Cathode ต่อตรงแบบ Active HIGH)
* **Buzzer:** บัสเซอร์แบบมีเสียงในตัว (Active Buzzer Module ต่อตรงแบบ Active HIGH)

| อุปกรณ์แจ้งเตือน | ขา GPIO (ESP32) | สถานะทางลอจิก | คำอธิบาย |
| :--- | :---: | :---: | :--- |
| **RGB LED - สีแดง (Red)** | `21` | Active HIGH | แสดงเมื่อฝั่งซ้ายก๊าซหมด (Empty) |
| **RGB LED - สีเขียว (Green)** | `22` | Active HIGH | แสดงเมื่อฝั่งซ้ายกำลังถูกใช้งาน (In Use) |
| **RGB LED - สีน้ำเงิน (Blue)** | `15` | Active HIGH | ใช้คู่กับสีแดงเพื่อทำสีเหลืองสแตนบาย (Standby) |
| **Buzzer Alarm** | `13` | Active HIGH | ส่งเสียงเตือนแบบมีจังหวะตามความวิกฤต |

---

## ⚙️ 2. ตรรกะการสลับฝั่งอัตโนมัติ (State Machine Logic)

ระบบมีกลไกสลับฝั่งการจ่ายแก๊สอัตโนมัติเพื่อป้องกันก๊าซขาดตอนในระบบ โดยยึดตรรกะในฟังก์ชั่น `loop()` ดังนี้:

1. **สลับไปฝั่งขวา (Active Bank = 2):** เมื่อพบว่าก๊าซฝั่งซ้ายหมด แต่ก๊าซฝั่งขวายังมีอยู่ (`isLeftEmpty` เป็นจริง และ `isRightEmpty` เป็นเท็จ)
2. **สลับไปฝั่งซ้าย (Active Bank = 1):** เมื่อพบว่าก๊าซฝั่งขวาหมด แต่ก๊าซฝั่งซ้ายยังมีอยู่ (`isLeftEmpty` เป็นเท็จ และ `isRightEmpty` เป็นจริง)
3. **การแจ้งเตือนเสียง (Buzzer Alarm Pattern):**
   * **สถานะปกติ (Normal):** ไม่มีเสียงเตือน (`Buzzer = LOW`)
   * **สถานะเตือนทั่วไป (Warning):** เมื่อฝั่งใดฝั่งหนึ่งหมด เสียงบัสเซอร์จะดังเตือนห่างกันทุกๆ **500 ms**
   * **สถานะวิกฤต (Critical):** เมื่อก๊าซหมดพร้อมกันทั้งสองฝั่ง บัสเซอร์จะดังถี่มากทุกๆ **150 ms** เพื่อให้ช่างเข้าทำการช่วยเหลือด่วน

---

## 🌐 3. หน้าเว็บแสดงผลและ REST API (Web Service)

บอร์ด ESP32 ทำงานเป็น Web Server (ที่พอร์ต 80) เพื่อเชื่อมต่อวงแลนโรงพยาบาลและให้บริการข้อมูลดังนี้:

### หน้าเว็บ Dashboard (GET `/`)
* บริการหน้าเว็บ HTML ที่เขียนด้วย CSS/JS สวยงามเพื่อแสดงสถานะถังก๊าซแบบ Real-time โดยมีการดึงข้อมูลผ่านการใช้ Fetch API ทุกๆ 1 วินาที
* ไฟล์อินเตอร์เฟสเดี่ยวสามารถดูได้ที่: [index.html](file:///E:/000_Antigraviti/MedicalGasNKP/Oxygen/02_Automatic_Manifold_Monitor/index.html)

### ข้อมูล JSON (GET `/data`)
คืนค่าสถานะปัจจุบันของระบบในรูปแบบ JSON ตัวอย่างเช่น:
```json
{
  "left_empty": 0,
  "right_empty": 1,
  "active_bank": 1
}
```
* `left_empty`: 1 = หมด, 0 = ปกติ
* `right_empty`: 1 = หมด, 0 = ปกติ
* `active_bank`: 1 = ใช้ฝั่งซ้าย, 2 = ใช้ฝั่งขวา

---

## 📂 ลิงก์ซอร์สโค้ดและไฟล์ระบบ

* **ซอร์สโค้ด Arduino Sketch (.ino):** [NKP_Manifold_Monitor_RGB_Buzzer1.ino](file:///E:/000_Antigraviti/MedicalGasNKP/Oxygen/02_Automatic_Manifold_Monitor/NKP_Manifold_Monitor_RGB_Buzzer1.ino)
* **หน้าเว็บอินเตอร์เฟสแยก (.html):** [index.html](file:///E:/000_Antigraviti/MedicalGasNKP/Oxygen/02_Automatic_Manifold_Monitor/index.html)
* **ไฟล์บีบอัดแพ็คเกจโปรเจกต์สำรอง (.rar):** [Project_O2Monitor_System_BUEM.rar](file:///E:/000_Antigraviti/MedicalGasNKP/Oxygen/02_Automatic_Manifold_Monitor/Project_O2Monitor_System_BUEM.rar)
