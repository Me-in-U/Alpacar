// 번호판 인식시 Django 서버로부터 받은 텍스트를 OLED에 표시하는 ESP8266 코드

#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>  // Markus Sattler WebSockets
#include <Wire.h>
#include <U8g2lib.h>

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

WebSocketsClient webSocket;
bool wsConnected = false;

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
        delay(500);
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
}
