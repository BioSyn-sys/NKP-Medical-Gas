#include <SPI.h>
#include <TFT_eSPI.h>
#include <WiFi.h>
#include <WebServer.h>

TFT_eSPI tft = TFT_eSPI();
WebServer server(80);

// ==========================================
// การตั้งค่า Wi-Fi (ตั้งค่าให้ตรงกับวงแลนของโรงพยาบาล)
// ==========================================
const char* ssid = "ASUS_70";       // ใส่ชื่อ Wi-Fi ที่ต้องการเชื่อมต่อ
const char* password = "password@1234"; // ใส่รหัสผ่าน Wi-Fi

// ==========================================
// ขา GPIO สำหรับอ่านสัญญาณ (เซนเซอร์ Float Switch)
// ==========================================
const int PIN_LEFT_EMPTY = 25;  
const int PIN_RIGHT_EMPTY = 26; 

// ==========================================
// ขา GPIO สำหรับ RGB LED (แสดงสถานะฝั่งซ้าย) และ Buzzer
// RGB LED: สมมติเป็น Common Cathode ต่อผ่านตัวต้านทาน, Active HIGH
// Buzzer: สมมติเป็น Active Buzzer Module, Active HIGH
// ==========================================
const int PIN_RGB_R = 21; // เปลี่ยนจาก 27 เพราะ 27 ถูกใช้เป็น INPUT แล้ว
const int PIN_RGB_G = 22; // เปลี่ยนจาก 32 เพราะ 32 ถูกใช้เป็น INPUT แล้ว
const int PIN_RGB_B = 15; // เปลี่ยนจาก 33 เพราะ 33 ถูกใช้เป็น INPUT แล้ว (หมายเหตุ: 15 เป็น strapping pin แต่ใช้เป็น output ปกติได้)
const int PIN_BUZZER = 13; // เปลี่ยนจาก 17 เพราะ 17 ถูกใช้เป็น INPUT แล้ว

// ตัวแปรเก็บสถานะ
int leftState = -1;
int rightState = -1;

// ตัวแปร Memory จำฝั่งที่ใช้งาน (1 = Left Bank, 2 = Right Bank)
int activeBank = 1; 

// ตัวแปรสถานะปัจจุบันของฝั่งซ้าย (ใช้ควบคุม RGB LED และ Buzzer แบบ non-blocking ทุกรอบ loop)
bool g_leftEmpty   = false;
bool g_rightEmpty  = false;
bool g_leftInUse   = true;
bool g_leftStandby = false;

// ตัวแปรสำหรับจังหวะ Buzzer (non-blocking)
unsigned long lastBuzzerToggle = 0;
bool buzzerState = false;

// ==========================================
// HTML/CSS/JS (หน้า Web UI)
// ==========================================
const char* htmlPage PROGMEM = R"=====(
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NKP Automatic Manifold Monitor</title>
    <style>
        body { background-color: #f0f0f0; font-family: 'Arial', sans-serif; display: flex; flex-direction: column; align-items: center; margin-top: 50px; }
        .panel { background-color: #38b6b3; border-radius: 20px; padding: 30px; width: 600px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); }
        .header-text { color: #006b6b; font-style: italic; font-weight: bold; font-size: 24px; text-align: center; margin-top: 20px; }
        .bank-labels { display: flex; justify-content: space-between; padding: 0 60px; margin-bottom: 10px; font-weight: bold; color: #111; }
        .controls-container { display: flex; justify-content: space-between; align-items: center; }
        .led-col { display: flex; flex-direction: column; gap: 15px; }
        .led-row { display: flex; align-items: center; font-weight: bold; color: #fff; text-shadow: 1px 1px 2px #000; }
        .led-row.left { justify-content: flex-end; }
        .led-row.right { justify-content: flex-start; }
        .led { width: 20px; height: 20px; border-radius: 50%; border: 2px solid #222; background-color: #333; margin: 0 10px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.8); }
        .led.green.on { background-color: #0f0; box-shadow: 0 0 15px #0f0; }
        .led.yellow.on { background-color: #ffcc00; box-shadow: 0 0 15px #ffcc00; }
        .led.red.on { background-color: #ff0000; box-shadow: 0 0 15px #ff0000; }
        .lcd-display { background-color: #111; width: 250px; height: 80px; border-radius: 5px; border: 4px solid #222; display: flex; justify-content: center; align-items: center; color: #00ff00; font-family: 'Courier New', monospace; font-size: 22px; font-weight: bold; box-shadow: inset 0 0 10px #000; }
    </style>
</head>
<body>
    <h2>Oxygen Reserve Monitor (NKP)</h2>
    <div class="panel">
        <div class="bank-labels"><span>Left Bank</span><span>Right Bank</span></div>
        <div class="controls-container">
            <div class="led-col">
                <div class="led-row left">In Use <div class="led green" id="l-inuse"></div></div>
                <div class="led-row left">Standby <div class="led yellow" id="l-standby"></div></div>
                <div class="led-row left">Empty <div class="led red" id="l-empty"></div></div>
            </div>
            <div class="lcd-display" id="lcd-text">LOADING...</div>
            <div class="led-col">
                <div class="led-row right"><div class="led green" id="r-inuse"></div> In Use</div>
                <div class="led-row right"><div class="led yellow" id="r-standby"></div> Standby</div>
                <div class="led-row right"><div class="led red" id="r-empty"></div> Empty</div>
            </div>
        </div>
        <div class="header-text">Fully Automatic Manifold</div>
    </div>
    <script>
        function updateUI() {
            fetch('/data')
                .then(res => res.json())
                .then(data => {
                    const lEmpty = data.left_empty === 1;
                    const rEmpty = data.right_empty === 1;
                    const activeBank = data.active_bank;
                    const lcd = document.getElementById('lcd-text');
                    
                    document.querySelectorAll('.led').forEach(el => el.classList.remove('on'));
                    
                    if (!lEmpty && !rEmpty) {
                        if (activeBank === 1) {
                            document.getElementById('l-inuse').classList.add('on');
                            document.getElementById('r-standby').classList.add('on');
                        } else {
                            document.getElementById('r-inuse').classList.add('on');
                            document.getElementById('l-standby').classList.add('on');
                        }
                        lcd.style.color = "#00ff00"; 
                        lcd.innerText = "SYSTEM NORMAL";
                    } else if (lEmpty && !rEmpty) {
                        document.getElementById('l-empty').classList.add('on');
                        document.getElementById('r-inuse').classList.add('on');
                        lcd.style.color = "#ffaa00"; 
                        lcd.innerText = "LEFT EMPTY!";
                    } else if (!lEmpty && rEmpty) {
                        document.getElementById('l-inuse').classList.add('on');
                        document.getElementById('r-empty').classList.add('on');
                        lcd.style.color = "#ffaa00"; 
                        lcd.innerText = "RIGHT EMPTY!";
                    } else {
                        document.getElementById('l-empty').classList.add('on');
                        document.getElementById('r-empty').classList.add('on');
                        lcd.style.color = "#ff0000"; 
                        lcd.innerText = "CRITICAL: EMPTY!";
                    }
                })
                .catch(err => console.error(err));
        }
        setInterval(updateUI, 1000);
    </script>
</body>
</html>
)=====";

// ==========================================
// Web Server Handlers
// ==========================================
void handleRoot() { server.send(200, "text/html", htmlPage); }

void handleData() {
  String json = "{";
  json += "\"left_empty\":" + String(leftState == HIGH ? 1 : 0) + ",";
  json += "\"right_empty\":" + String(rightState == HIGH ? 1 : 0) + ",";
  json += "\"active_bank\":" + String(activeBank);
  json += "}";
  server.send(200, "application/json", json);
}

// ==========================================
// ฟังก์ชันวาด UI บนจอ TTGO (TFT)
// ==========================================
void drawStaticTFT(String ipAddress) {
  tft.fillScreen(TFT_BLACK);
  
  tft.setTextColor(tft.color565(56, 182, 179), TFT_BLACK); 
  tft.setTextDatum(TC_DATUM);
  tft.setTextSize(1);
  tft.drawString("Fully Automatic Manifold", 120, 5);
  
  // แสดง IP Address ที่ได้รับจากเร้าเตอร์ ไว้ที่ขอบบนของจอ
  tft.setTextColor(TFT_YELLOW, TFT_BLACK);
  tft.drawString("IP: " + ipAddress, 120, 15);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.drawString("LEFT", 30, 30);
  tft.drawString("RIGHT", 210, 30);

  tft.setTextDatum(MR_DATUM);
  tft.drawString("In Use", 55, 55);
  tft.drawString("Stby", 55, 85);
  tft.drawString("Empty", 55, 115);
  
  tft.setTextDatum(ML_DATUM);
  tft.drawString("In Use", 185, 55);
  tft.drawString("Stby", 185, 85);
  tft.drawString("Empty", 185, 115);
  
  tft.drawRect(65, 50, 110, 75, TFT_DARKGREY);
}

void updateTFT_UI(bool l_emp, bool r_emp, int act_bank) {
  uint16_t C_OFF = tft.color565(40, 40, 40); 
  
  bool l_inUse = false, l_standby = false;
  bool r_inUse = false, r_standby = false;
  String lcdText = "";
  uint16_t lcdColor = TFT_WHITE;

  // ตรรกะแยกสถานะไฟ
  if (!l_emp && !r_emp) {
    if (act_bank == 1) { l_inUse = true; r_standby = true; } 
    else { r_inUse = true; l_standby = true; }
    lcdText = "NORMAL";
    lcdColor = TFT_GREEN;
  } else if (l_emp && !r_emp) {
    r_inUse = true;
    lcdText = "L-EMPTY";
    lcdColor = TFT_ORANGE;
  } else if (!l_emp && r_emp) {
    l_inUse = true;
    lcdText = "R-EMPTY";
    lcdColor = TFT_ORANGE;
  } else {
    lcdText = "CRITICAL";
    lcdColor = TFT_RED;
  }

  // วาดไฟ LED
  tft.fillCircle(70, 55, 6, l_inUse ? TFT_GREEN : C_OFF);
  tft.fillCircle(70, 85, 6, l_standby ? TFT_YELLOW : C_OFF);
  tft.fillCircle(70, 115, 6, l_emp ? TFT_RED : C_OFF);

  tft.fillCircle(170, 55, 6, r_inUse ? TFT_GREEN : C_OFF);
  tft.fillCircle(170, 85, 6, r_standby ? TFT_YELLOW : C_OFF);
  tft.fillCircle(170, 115, 6, r_emp ? TFT_RED : C_OFF);

  // อัปเดตกล่องข้อความ
  tft.fillRect(78, 75, 84, 25, TFT_BLACK); 
  tft.setTextColor(lcdColor, TFT_BLACK);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(lcdText, 120, 87);

  // เก็บสถานะฝั่งซ้ายไว้ในตัวแปร Global เพื่อให้ loop() ใช้ควบคุม RGB LED / Buzzer
  g_leftEmpty   = l_emp;
  g_rightEmpty  = r_emp;
  g_leftInUse   = l_inUse;
  g_leftStandby = l_standby;
}

// ==========================================
// ควบคุม RGB LED ให้แสดงสถานะฝั่งซ้าย
// เขียว = In Use, เหลือง = Standby, แดง = Empty
// ==========================================
void setLeftRGB(bool inUse, bool standby, bool empty) {
  if (empty) {
    digitalWrite(PIN_RGB_R, HIGH);
    digitalWrite(PIN_RGB_G, LOW);
    digitalWrite(PIN_RGB_B, LOW);
  } else if (inUse) {
    digitalWrite(PIN_RGB_R, LOW);
    digitalWrite(PIN_RGB_G, HIGH);
    digitalWrite(PIN_RGB_B, LOW);
  } else if (standby) {
    // เหลือง = แดง + เขียว พร้อมกัน
    digitalWrite(PIN_RGB_R, HIGH);
    digitalWrite(PIN_RGB_G, HIGH);
    digitalWrite(PIN_RGB_B, LOW);
  } else {
    digitalWrite(PIN_RGB_R, LOW);
    digitalWrite(PIN_RGB_G, LOW);
    digitalWrite(PIN_RGB_B, LOW);
  }
}

// ==========================================
// ควบคุม Buzzer แบบ non-blocking (ไม่หยุดการทำงานของ WebServer)
// alarmActive = true เมื่อฝั่งใดฝั่งหนึ่ง Empty
// beepInterval = จังหวะกระพริบ (ms) ยิ่งน้อยยิ่งดังถี่ (Critical จะถี่กว่า)
// ==========================================
void handleBuzzer(bool alarmActive, unsigned long beepInterval) {
  if (!alarmActive) {
    digitalWrite(PIN_BUZZER, LOW);
    buzzerState = false;
    return;
  }
  unsigned long now = millis();
  if (now - lastBuzzerToggle >= beepInterval) {
    lastBuzzerToggle = now;
    buzzerState = !buzzerState;
    digitalWrite(PIN_BUZZER, buzzerState ? HIGH : LOW);
  }
}

// ==========================================
// Setup & Loop
// ==========================================
void setup() {
  Serial.begin(115200);

  tft.init();
  tft.setRotation(1); 
  
  pinMode(PIN_LEFT_EMPTY, INPUT_PULLUP);
  pinMode(PIN_RIGHT_EMPTY, INPUT_PULLUP);

  // ตั้งค่าขา RGB LED และ Buzzer เป็น Output พร้อมปิดไว้ก่อน
  pinMode(PIN_RGB_R, OUTPUT);
  pinMode(PIN_RGB_G, OUTPUT);
  pinMode(PIN_RGB_B, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_RGB_R, LOW);
  digitalWrite(PIN_RGB_G, LOW);
  digitalWrite(PIN_RGB_B, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  // หน้าจอตอนกำลังเชื่อมต่อ Wi-Fi
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setTextDatum(MC_DATUM);
  tft.drawString("Connecting to Wi-Fi...", 120, 60);
  tft.drawString(ssid, 120, 80);

  // เชื่อมต่อวงแลน (Station Mode)
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  // รอจนกว่าจะเชื่อมต่อสำเร็จ
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  // วาดโครงสร้าง UI พื้นฐานบน TFT (พร้อมส่ง IP ไปโชว์บนจอ)
  drawStaticTFT(WiFi.localIP().toString());

  server.on("/", handleRoot);
  server.on("/data", handleData);
  server.begin();
}

void loop() {
  server.handleClient(); 

  int readLeft = digitalRead(PIN_LEFT_EMPTY);
  int readRight = digitalRead(PIN_RIGHT_EMPTY);

  if (readLeft != leftState || readRight != rightState) {
    delay(50); // Debounce
    readLeft = digitalRead(PIN_LEFT_EMPTY);
    readRight = digitalRead(PIN_RIGHT_EMPTY);
    
    if (readLeft != leftState || readRight != rightState) {
      leftState = readLeft;
      rightState = readRight;
      
      bool isLeftEmpty = (leftState == HIGH);
      bool isRightEmpty = (rightState == HIGH);

      // State Machine: สลับ In Use อัตโนมัติเมื่ออีกฝั่งหมด
      if (isLeftEmpty && !isRightEmpty) {
        activeBank = 2; // ขวาเป็น In Use
      } 
      else if (!isLeftEmpty && isRightEmpty) {
        activeBank = 1; // ซ้ายเป็น In Use
      }
      
      updateTFT_UI(isLeftEmpty, isRightEmpty, activeBank);
      
      Serial.print("Left: "); Serial.print(isLeftEmpty ? "EMPTY" : "OK");
      Serial.print(" | Right: "); Serial.print(isRightEmpty ? "EMPTY" : "OK");
      Serial.print(" | Active Bank: "); Serial.println(activeBank == 1 ? "LEFT" : "RIGHT");
    }
  }

  // อัปเดต RGB LED (ฝั่งซ้าย) ทุกรอบ loop ตามสถานะล่าสุด
  setLeftRGB(g_leftInUse, g_leftStandby, g_leftEmpty);

  // จัดการ Buzzer แบบ non-blocking: ดังเมื่อฝั่งใดฝั่งหนึ่ง Empty
  // ถ้า Empty ทั้งสองฝั่ง (Critical) ให้ดังถี่ขึ้น
  bool alarmActive = g_leftEmpty || g_rightEmpty;
  unsigned long beepInterval = (g_leftEmpty && g_rightEmpty) ? 150 : 500;
  handleBuzzer(alarmActive, beepInterval);
}
