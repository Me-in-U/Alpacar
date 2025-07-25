// 번호판 인식시 Django 서버로부터 받은 텍스트를 OLED에 표시하는 ESP8266 코드

#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>  // Markus Sattler WebSockets
#include <Wire.h>
#include <U8g2lib.h>
#include <Servo.h>             // 서보 모터
#include <Adafruit_VL53L0X.h>  // VL53L0X 거리센서

// === Wi‑Fi 설정 ===
const char* SSID = "E102";
const char* PASSWORD = "08080808";

// === WebSocket 서버 정보 ===
const char* WS_HOST = "192.168.8.183";
const uint16_t WS_PORT = 8000;
const char* WS_PATH = "/ws_text/";  // 수정: 끝의 슬래시 제거

// === OLED 설정 ===
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(
  U8G2_R0, U8X8_PIN_NONE, SCL, SDA);

// === Servo 설정 ===
Servo gateServo;
const uint8_t SERVO_PIN = D5;  // 예: D5(GPIO14)
const uint8_t SERVO_OPEN_POS = 90;
const uint8_t SERVO_CLOSED_POS = 0;

// === VL53L0X 설정 ===
Adafruit_VL53L0X lox = Adafruit_VL53L0X();
const uint16_t TRIGGER_THRESHOLD_MM = 150;  // 5cm

WebSocketsClient webSocket;
bool wsConnected = false;

// 차량 입차 상태 머신
bool carEntering = false;           // “입차” 명령을 받았는가?
bool carLeftZone = false;           // 차량이 센서 구역을 벗어났는가?
unsigned long leaveDetectedAt = 0;  // 벗어난 시각(ms)

// ——— Wi‑Fi 재연결 함수 ———
void ensureWiFiConnected() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.println("▶ WiFi 끊김, 재연결 시도...");
  u8g2.clearBuffer();
  u8g2.setCursor(0, 14);
  u8g2.print("WiFi 재연결...");
  u8g2.sendBuffer();

  // 자동 재연결 모드에서 reconnect() 호출
  WiFi.reconnect();

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(200);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n▶ WiFi 재연결 성공");
    u8g2.clearBuffer();
    u8g2.setCursor(0, 14);
    u8g2.print("WiFi OK");
    u8g2.sendBuffer();
  } else {
    Serial.println("\n▶ WiFi 재연결 실패");
    u8g2.clearBuffer();
    u8g2.setCursor(0, 14);
    u8g2.print("WiFi FAIL");
    u8g2.sendBuffer();
  }
}

// ——— WebSocket 이벤트 핸들러 ———
void onWsEvent(WStype_t type, uint8_t* payload, size_t length) {
  Serial.printf("▶ onWsEvent: type=%d, len=%u\n", type, length);
  switch (type) {
    case WStype_CONNECTED:
      wsConnected = true;
      displayStatus("WS 연결됨");
      break;
    case WStype_DISCONNECTED:
      wsConnected = false;
      displayStatus("WS 끊김");
      // WS 끊기면 Wi‑Fi도 확인
      ensureWiFiConnected();
      break;
    case WStype_ERROR:
      displayStatus("WS 에러");
      break;
    case WStype_TEXT:
      {
        // 받은 메시지가 JSON이면, {"text":"..."} 형태로 파싱해야 합니다.
        // 여기서는 단순히 payload 전체를 문자열로 보여줍니다.
        String txt = String((char*)payload).substring(0, length);
        // JSON 파싱 생략하고, 따옴표 사이 내용을 꺼내려면:
        int i = txt.indexOf("\"text\":");
        if (i >= 0) {
          int a = txt.indexOf('"', i + 7);
          int b = txt.indexOf('"', a + 1);
          if (a >= 0 && b > a) txt = txt.substring(a + 1, b);
        }
        Serial.printf("▶ TEXT: %s\n", txt);

        u8g2.clearBuffer();
        String t = String(txt);
        if (t.length() <= 16) {
          u8g2.setCursor(0, 14);
          u8g2.print(t);
        } else {
          u8g2.setCursor(0, 14);
          u8g2.print(t.substring(0, 16));
          u8g2.setCursor(0, 30);
          u8g2.print(t.substring(16));
        }
        u8g2.sendBuffer();

        // “입차”로 시작하면 문 열기
        if (txt.startsWith("입차") && !carEntering) {
          carEntering = true;
          carLeftZone = false;
          gateServo.write(SERVO_OPEN_POS);
          displayStatus("Gate Open");
          // leaveDetectedAt 는 아직 기록 안 함
        }
        break;
      }
  }
}

// OLED에 상태 메시지 표시
void displayStatus(const char* msg) {
  Serial.printf("   OLED: %s\n", msg);
  u8g2.clearBuffer();
  u8g2.setCursor(0, 14);
  u8g2.print(msg);
  u8g2.sendBuffer();
  delay(500);
}

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("\n===== 부팅 시작 =====");

  // OLED 초기화
  u8g2.begin();
  u8g2.enableUTF8Print();
  u8g2.setFont(u8g2_font_unifont_t_korean2);

  // Servo
  gateServo.attach(SERVO_PIN);
  gateServo.write(SERVO_CLOSED_POS);

  // VL53L0X
  if (!lox.begin()) {
    displayStatus("VL53 init fail");
    while (1) delay(10);
  }

  // 1) Wi‑Fi 자동 재연결 모드
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);

  // 최초 연결 시도
  Serial.printf("▶ WiFi 연결 시도: %s\n", SSID);
  WiFi.begin(SSID, PASSWORD);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 10000) {
    delay(200);
    Serial.print(".");
  }
  displayStatus(WiFi.status() == WL_CONNECTED ? "WiFi OK" : "WiFi FAIL");

  // 2) WebSocket 설정
  webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
  webSocket.onEvent(onWsEvent);
  webSocket.setReconnectInterval(5000);
  displayStatus("WS 시도...");
  delay(500);
}

void loop() {
  webSocket.loop();
  // 5초마다 Wi‑Fi/WS 상태 확인 및 재연결
  static unsigned long last = 0;
  if (millis() - last > 5000) {
    last = millis();
    if (!wsConnected) {
      Serial.println("▶ WS 재연결 시도");
      webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
      webSocket.onEvent(onWsEvent);
      webSocket.setReconnectInterval(5000);
      displayStatus("WS 시도...");
    }
    ensureWiFiConnected();
  }
  VL53L0X_RangingMeasurementData_t measure;
  lox.rangingTest(&measure, false);
  // 시리얼에 항상 출력해 줍니다.
  if (measure.RangeStatus == 0) {
    Serial.printf("거리: %4d mm\n", measure.RangeMilliMeter);
  } else {
    Serial.printf("거리측정 오류: 상태=%d\n", measure.RangeStatus);
  }
  // 2) 차량이 입차 중이고, 아직 벗어남 감지 전이면 거리 체크
  if (carEntering && !carLeftZone) {
    if (measure.RangeStatus == 0 && measure.RangeMilliMeter > TRIGGER_THRESHOLD_MM) {
      // 구역 벗어남 감지
      carLeftZone = true;
      leaveDetectedAt = millis();
    }
  }
  // 3) 벗어남 감지 후 2초 경과 시 문 닫기
  if (carEntering && carLeftZone && millis() - leaveDetectedAt > 2000) {
    gateServo.write(SERVO_CLOSED_POS);
    displayStatus("Gate Close");
    // 상태 초기화
    carEntering = false;
    carLeftZone = false;
  }

  delay(10);
}
