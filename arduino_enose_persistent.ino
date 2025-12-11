// ========================================
// E-NOSE RAM — PERSISTENT CONNECTION VERSION
// HOLD 1.5 MENIT | PURGE 3.5 MENIT | LEVEL 1-5 OTOMATIS
// MODIFIKASI: Kipas menyala 5 detik lebih dulu daripada Pompa di fase PURGE.
// PERBAIKAN: Pompa dengan kontrol arah untuk PURGE yang benar
// ========================================

#include <WiFiS3.h>
#include <Wire.h>
#include "Multichannel_Gas_GMXXX.h"

// ==================== WIFI ====================
const char* ssid     = "vivo V60 Lite 5G";
const char* pass     = "12345678";
const char* RUST_IP  = "10.175.177.11";   // GANTI KALAU IP BERUBAH
const int   RUST_PORT = 8081;
WiFiClient client;

// ==================== SENSOR ====================
GAS_GMXXX<TwoWire> gas;
#define MICS_PIN    A1
#define RLOAD       820.0
#define VCC         5.0
float R0_mics = 100000.0;  // Default, nanti di-update di udara bersih

// ==================== MOTOR (PIN DISESUAIKAN) ====================
// Kipas (Motor A): PWM 6, DIR 9, 10
const int PWM_KIPAS   = 6;
const int DIR_KIPAS_1 = 9;
const int DIR_KIPAS_2 = 10;
// Pompa (Motor B): PWM 5, DIR 7, 8
const int PWM_POMPA   = 5;
const int DIR_POMPA_1 = 7;
const int DIR_POMPA_2 = 8;

// ==================== FSM & LEVEL ====================
enum State { IDLE, PRE_COND, RAMP_UP, HOLD, PURGE, RECOVERY, DONE };
State currentState = IDLE;
unsigned long stateTime = 0;
int currentLevel = 0;  // 0–4 → Rust +1 → 1–5
const int speeds[5] = {51, 102, 153, 204, 255}; // Kecepatan untuk Level 1-5
bool samplingActive = false;

// Variabel flag untuk mencetak pesan di Serial Monitor hanya sekali per fase PURGE
bool printFanLead = false;
bool printBoth = false;

// ==================== TIMING (SYNCHRONIZED!) ====================
const unsigned long T_FAN_LEAD = 5000;  // Kipas menyala duluan selama 5 detik
const unsigned long T_PRECOND  = 5000;   // 5 seconds
const unsigned long T_RAMP     = 3000;   // 3 seconds
const unsigned long T_HOLD     = 30000;  // 30 seconds (testing - ganti ke 60000 untuk 1 menit)
const unsigned long T_PURGE    = 30000;  // 30 seconds (testing - ganti ke 120000 untuk 2 menit)
const unsigned long T_RECOVERY = 5000;   // 5 seconds
unsigned long lastSend = 0;
unsigned long lastReconnect = 0;

// ==================== MOTOR CONTROL ====================
void kipas(int speed, bool buang = false) {
  digitalWrite(DIR_KIPAS_1, buang ? LOW : HIGH);
  digitalWrite(DIR_KIPAS_2, buang ? HIGH : LOW);
  analogWrite(PWM_KIPAS, speed);
}

void pompa(int speed, bool buang = false) {
  // buang = true → pompa mengeluarkan udara (untuk PURGE)
  // buang = false → pompa normal (untuk fase lain jika diperlukan)
  // CATATAN: Kalau arah masih terbalik, tukar LOW/HIGH di bawah ini
  digitalWrite(DIR_POMPA_1, buang ? LOW : HIGH);
  digitalWrite(DIR_POMPA_2, buang ? HIGH : LOW);
  analogWrite(PWM_POMPA, speed);
}

void stopAll() { 
  analogWrite(PWM_KIPAS, 0); 
  analogWrite(PWM_POMPA, 0); 
}

void rampKipas(int target) {
  static int cur = 0;
  if (cur < target) cur += 15;
  else if (cur > target) cur -= 15;
  cur = constrain(cur, 0, 255);
  kipas(cur);
}

// ==================== MiCS-5524 ====================
float calculateRs() {
  int raw = analogRead(MICS_PIN);
  if (raw < 10) return -1;
  float Vout = raw * (VCC / 1023.0);
  if (Vout >= VCC || Vout <= 0) return -1;
  return RLOAD * ((VCC - Vout) / Vout);
}

float ppmFromRatio(float ratio, String gas) {
  if (ratio <= 0 || R0_mics == 0) return -1;
  float ppm = 0.0;
  if (gas == "CO")      ppm = pow(10, (log10(ratio) - 0.35) / -0.85);
  else if (gas == "C2H5OH") ppm = pow(10, (log10(ratio) - 0.15) / -0.65);
  else if (gas == "VOC")    ppm = pow(10, (log10(ratio) + 0.1) / -0.75);
  return (ppm >= 0 && ppm <= 5000) ? ppm : -1;
}

// ==================== CONNECTION MANAGEMENT ====================
void ensureConnected() {
  if (client.connected()) {
    return;
  }
  
  if (millis() - lastReconnect < 5000) {
    return;
  }
  
  lastReconnect = millis();
  Serial.print("🔌 Connecting to backend "); Serial.print(RUST_IP); Serial.print(":"); Serial.println(RUST_PORT);
  
  if (client.connect(RUST_IP, RUST_PORT)) {
    Serial.println("✅ Connected to backend!");
    client.println("HELLO:Arduino E-NOSE ZIZU");
  } else {
    Serial.println("❌ Connection failed, will retry...");
  }
}

// ==================== SETUP ====================
void setup() {
  Serial.begin(9600);
  Serial.println("\n\n========================================");
  Serial.println("🚀 E-NOSE ZIZU INITIALIZING (Kipas Lead + Pompa Buang)");
  Serial.println("========================================");
  
  // Setup motor pins
  pinMode(DIR_KIPAS_1, OUTPUT); 
  pinMode(DIR_KIPAS_2, OUTPUT); 
  pinMode(PWM_KIPAS, OUTPUT);
  pinMode(DIR_POMPA_1, OUTPUT); 
  pinMode(DIR_POMPA_2, OUTPUT); 
  pinMode(PWM_POMPA, OUTPUT);
  stopAll();
  Serial.println("✅ Motor pins configured");

  // Setup I2C and gas sensor
  Wire.begin();
  gas.begin(Wire, 0x08);
  Serial.println("✅ GM-XXX gas sensor initialized");

  // KALIBRASI R0 SEKALI DI UDARA BERSIH
  Serial.println("\n🔬 Calibrating MiCS-5524 in clean air...");
  delay(2000);
  float Rs_air = calculateRs();
  if (Rs_air > 0) {
    R0_mics = Rs_air;
    Serial.print("✅ R0 MiCS-5524 measured: ");  Serial.print(R0_mics/1000.0, 2);  Serial.println(" kΩ");
  } else {
    Serial.println("⚠  R0 MiCS-5524 using default: 100 kΩ");
  }

  // Connect to WiFi
  Serial.println("\n📡 Connecting to WiFi...");
  Serial.print("   SSID: "); Serial.println(ssid);
  
  while (WiFi.begin(ssid, pass) != WL_CONNECTED) {  Serial.print(".");  delay(500);  }
  
  Serial.println("\n✅ WiFi Connected!");
  Serial.print("   IP Address: "); Serial.println(WiFi.localIP());
  Serial.print("   Backend: "); Serial.print(RUST_IP); Serial.print(":"); Serial.println(RUST_PORT);
  
  ensureConnected();
  
  Serial.println("\n========================================");
  Serial.println("✅ E-NOSE ZIZU READY!");
  Serial.println("📝 Timing (TESTING MODE - 30s each):");
  Serial.println("   - HOLD: 30s (testing)");
  Serial.println("   - PURGE: 30s (testing)");
  Serial.println("   - Kipas lead: 5s");
  Serial.println("========================================\n");
}

// ==================== LOOP ====================
void loop() {
  ensureConnected();
  
  // Check for commands from backend
  if (client.available()) {
    String cmd = client.readStringUntil('\n');
    cmd.trim();
    Serial.println("📥 Command from backend: " + cmd);
    if (cmd == "START_SAMPLING") startSampling();
    else if (cmd == "STOP_SAMPLING") stopSampling();
  }
  
  // Also check Serial for local commands
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n'); 
    cmd.trim();
    Serial.println("📥 Command received: " + cmd);
    
    if (cmd == "START_SAMPLING") { startSampling(); }
    else if (cmd == "STOP_SAMPLING") { stopSampling(); }
    else { Serial.println("❌ Unknown command: " + cmd); }
  }

  // Send sensor data periodically
  if (millis() - lastSend >= 250) { 
    lastSend = millis(); 
    sendSensorData(); 
  }
  
  // Run FSM
  if (samplingActive) {
    runFSM();
  }
}

// ==================== FSM LOGIC ====================
void startSampling() {
  if (!samplingActive) {
    samplingActive = true;
    currentLevel = 0;
    changeState(PRE_COND);
    Serial.println("\n🎯 ========================================");
    Serial.println("🎯 SAMPLING STARTED!");
    Serial.println("🎯 5 Levels | Hold: 30s | Purge: 30s (TESTING)");
    Serial.println("🎯 ========================================\n");
  } else {
    Serial.println("⚠  Sampling already active!");
  }
}

void stopSampling() {
  if (samplingActive) {
    samplingActive = false;
    currentLevel = 0;
    changeState(IDLE);
    stopAll();
    Serial.println("\n🛑 ========================================");
    Serial.println("🛑 SAMPLING STOPPED!");
    Serial.println("🛑 ========================================\n");
  } else {
    Serial.println("⚠  No active sampling to stop!");
  }
}

void changeState(State s) {
  currentState = s;
  stateTime = millis();
  
  // Reset flags untuk mencetak pesan hanya sekali di state PURGE
  printFanLead = false;
  printBoth = false;
  
  String names[] = {"IDLE","PRE-COND","RAMP_UP","HOLD","PURGE","RECOVERY","DONE"};
  
  Serial.println("\n🔄 ----------------------------------------");
  Serial.print("🔄 STATE: "); Serial.print(names[s]); Serial.print(" | Level: "); Serial.println(currentLevel + 1);
  
  switch(s) {
    case PRE_COND: Serial.println("   ⏱  Duration: 5 seconds"); Serial.println("   🌀 Fan: 120 (medium) | Pump: OFF"); break;
    case RAMP_UP: Serial.println("   ⏱  Duration: 3 seconds"); Serial.print("   🌀 Fan: ramping to "); Serial.println(speeds[currentLevel]); break;
    case HOLD: Serial.println("   ⏱  Duration: 30 seconds (testing)"); Serial.print("   🌀 Fan: "); Serial.print(speeds[currentLevel]); Serial.println(" | Pump: OFF"); Serial.println("   📊 Collecting data..."); break;
    case PURGE:
      Serial.println("   ⏱  Duration: 30 seconds (testing)");
      Serial.println("   🌀 Fan: 255 (MAX, reverse) | Pump: 255 (MAX, BUANG)");
      Serial.println("   🔔 Pompa akan menyusul 5 detik setelah Kipas.");
      Serial.println("   🧹 Purging chamber...");
      break;
    case RECOVERY: Serial.println("   ⏱  Duration: 5 seconds"); Serial.println("   🛑 All motors: OFF"); Serial.println("   💤 Recovery period..."); break;
    case DONE: Serial.println("   ✅ All 5 levels completed!"); Serial.println("   📊 Data ready for training!"); break;
    case IDLE: Serial.println("   💤 Waiting for command..."); break;
  }
  Serial.println("🔄 ----------------------------------------");
}

void runFSM() {
  unsigned long elapsed = millis() - stateTime;
  
  switch (currentState) {
    case PRE_COND:   
      kipas(120); 
      pompa(0); 
      if (elapsed >= T_PRECOND) { changeState(RAMP_UP); }
      break;
      
    case RAMP_UP:    
      rampKipas(speeds[currentLevel]); 
      pompa(0); 
      if (elapsed >= T_RAMP) { changeState(HOLD); }
      break;
      
    case HOLD:       
      kipas(speeds[currentLevel]); 
      pompa(0); 
      if (elapsed >= T_HOLD) { changeState(PURGE); }
      break;
      
    case PURGE:      
      kipas(255, true); // FASE WAJIB: Kipas ON (MAX, arah buang)
      
      if (elapsed < T_FAN_LEAD) { // Jika waktu < 5 detik
        pompa(0); // Pompa masih OFF
        if (!printFanLead) {
          Serial.println("   🌪  Kipas menyala duluan (5s lead)...");
          printFanLead = true;
        }
      } else {
        // Jika waktu >= 5 detik, Pompa menyusul dengan arah BUANG
        pompa(255, true); // Pompa ON MAX dengan arah BUANG (mengeluarkan udara)
        if (!printBoth) {
          Serial.println("   💨 Kipas & Pompa ON bersamaan (PURGE MODE - BUANG UDARA).");
          printBoth = true;
        }
      }
      
      if (elapsed >= T_PURGE) { changeState(RECOVERY); }
      break;
      
    case RECOVERY:   
      stopAll(); 
      if (elapsed >= T_RECOVERY) {
        currentLevel++;
        if (currentLevel >= 5) { 
          changeState(DONE); 
          samplingActive = false;
          Serial.println("\n🎉 ========================================");
          Serial.println("🎉 ALL 5 LEVELS COMPLETED!");
          Serial.println("========================================\n");
        }
        else { changeState(RAMP_UP); }
      }
      break;
      
    case IDLE: 
    case DONE: 
      stopAll(); 
      break;
  }
}

// ==================== KIRIM DATA KE RUST ====================
void sendSensorData() {
  if (!client.connected()) { return; }
  
  // GM-XXX
  float no2 = (gas.measure_NO2()  < 30000) ? gas.measure_NO2()  / 1000.0 : -1.0;
  float eth = (gas.measure_C2H5OH()< 30000) ? gas.measure_C2H5OH()/ 1000.0 : -1.0;
  float voc = (gas.measure_VOC()  < 30000) ? gas.measure_VOC()  / 1000.0 : -1.0;
  float co  = (gas.measure_CO()   < 30000) ? gas.measure_CO()   / 1000.0 : -1.0;

  // MiCS-5524
  float Rs = calculateRs();
  float co_mics = (Rs > 0) ? ppmFromRatio(Rs / R0_mics, "CO") : -1.0;
  float eth_mics = (Rs > 0) ? ppmFromRatio(Rs / R0_mics, "C2H5OH") : -1.0;
  float voc_mics = (Rs > 0) ? ppmFromRatio(Rs / R0_mics, "VOC") : -1.0;

  // Format data yang dikirim ke backend (Rust)
  String data = "SENSOR:";
  data += String(no2,3) + "," + String(eth,3) + "," + String(voc,3) + "," + String(co,3) + ",";
  data += String(co_mics,3) + "," + String(eth_mics,3) + "," + String(voc_mics,3) + ",";
  data += String(currentState) + "," + String(currentLevel);

  client.println(data);
  
  // Print to Serial Monitor (hanya pada HOLD state setiap 2 detik)
  if (samplingActive && currentState == HOLD) {
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint > 2000) {
      Serial.println("📊 Sensor Data:");
      Serial.print("   GM-XXX → NO2: "); Serial.print(no2, 2);
      Serial.print(" | ETH: "); Serial.print(eth, 2);
      Serial.print(" | VOC: "); Serial.print(voc, 2);
      Serial.print(" | CO: "); Serial.println(co, 2);
      Serial.print("   MiCS   → CO: "); Serial.print(co_mics, 2);
      Serial.print(" | ETH: "); Serial.print(eth_mics, 2);
      Serial.print(" | VOC: "); Serial.println(voc_mics, 2);
      lastPrint = millis();
    }
  }
}