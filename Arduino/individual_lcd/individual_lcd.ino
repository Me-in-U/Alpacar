// ==============================
// ESP8266 Plate Display (OLED)
// 슬롯 전용 표시기: ws/platedisplay/ 브로드캐스트 수신
// ==============================
#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>  // Markus Sattler WebSockets (ESP8266)
#include <U8g2lib.h>
#include <Wire.h>

// ====== 슬롯 라벨(이 장치가 담당하는 자리) ======
const char* SLOT_LABEL = "A1";  // <-- 각 기기마다 A1, A2, ... 로 바꿔 빌드

// ====== Wi-Fi ======
const char* SSID = "E102";
const char* PASSWORD = "08080808";

// ====== WebSocket(Server) ======
// const char* WS_HOST = "i13e102.p.ssafy.io";
const char* WS_HOST = "192.168.30.180";
// const uint16_t WS_PORT = 443;
const uint16_t WS_PORT = 8000;
const char* WS_PATH = "/ws/platedisplay/";

// ====== OLED(SSD1306 128x32 I2C) ======
U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(
  U8G2_R0, U8X8_PIN_NONE, SCL, SDA);

// ====== WebSocket ======
WebSocketsClient webSocket;
bool wsConnected = false;

// ====== 화면 중복 업데이트 방지 ======
String lastShown = "";

// ---------- 유틸: 문자열 대문자화 ----------
String upper(const String& s) {
  String t = s;
  t.toUpperCase();
  return t;
}

// ---------- JSON 문자열 추출(간단 파서) ----------
String extractJsonString(const String& json, const char* key) {
  // "key":"value" 형태만 처리(이스케이프 미고려). 번호판/라벨은 안전.
  String pat = String("\"") + key + "\":";
  int k = json.indexOf(pat);
  if (k < 0) return "";
  int q1 = json.indexOf('\"', k + pat.length());
  if (q1 < 0) return "";
  int q2 = json.indexOf('\"', q1 + 1);
  if (q2 < 0) return "";
  return json.substring(q1 + 1, q2);
}

// ─────────────────────────────────────────────────────────────
// UTF-8 한/영 자동 줄바꿈 (명시적 \n 먼저 처리) + 상단 패딩
// ─────────────────────────────────────────────────────────────
void drawMultilineUTF8(const String& raw) {
  const int SCREEN_W = 128;
  const int SCREEN_H = 64;
  const int LEFT_PAD = 0;
  const int TOP_PAD = 2;  // 상단 잘림 방지용
  const int RIGHT_PAD = 0;

  // 1) \r\n, \r → \n 정규화
  String msg = raw;
  msg.replace("\r\n", "\n");
  msg.replace("\r", "\n");

  u8g2.firstPage();
  do {
    u8g2.setFont(u8g2_font_unifont_t_korean2);
    u8g2.setFontDirection(0);
    u8g2.setFontPosTop();  // y 기준을 top으로
    const int lineH = u8g2.getMaxCharHeight();
    const int maxW = SCREEN_W - LEFT_PAD;


    // 2) '\n' 기준 1차 분할
    //    각 물리 줄을 다시 폭 기준으로 감싸기
    int y = TOP_PAD;
    int start = 0;
    while (start <= msg.length()) {
      int nl = msg.indexOf('\n', start);
      String phys = (nl >= 0) ? msg.substring(start, nl) : msg.substring(start);
      start = (nl >= 0) ? nl + 1 : msg.length() + 1;

      // 공백 줄도 한 줄 높이 확보
      if (phys.length() == 0) {
        if (y + lineH > SCREEN_H) break;
        // 빈 줄은 그냥 y만 내린다
        y += lineH;
        continue;
      }

      // 3) 폭 기준 wrap
      String line = "";
      for (uint16_t i = 0; i < phys.length();) {
        uint8_t c = phys[i];
        uint8_t step = (c < 0x80) ? 1 : ((c & 0xE0) == 0xC0 ? 2 : ((c & 0xF0) == 0xE0 ? 3 : 4));
        String next = phys.substring(i, i + step);
        String test = line + next;

        if (u8g2.getUTF8Width(test.c_str()) <= maxW) {
          line = test;
          i += step;
        } else {
          // 현재 줄 그리기
          if (y + lineH > SCREEN_H) break;
          // 가운데 정렬
          int x = (SCREEN_W - u8g2.getUTF8Width(line.c_str())) / 2;
          if (x < 0) x = 0;
          u8g2.setCursor(x, y);
          u8g2.print(line);
          y += lineH;
          line = next;  // 다음 줄 시작
          i += step;
        }
      }
      // 남은 조각 출력
      if (line.length() > 0 && y + lineH <= SCREEN_H) {
        int x = (SCREEN_W - u8g2.getUTF8Width(line.c_str())) / 2;
        if (x < 0) x = 0;
        u8g2.setCursor(x, y);
        u8g2.print(line);
        y += lineH;
      }
      if (y + lineH > SCREEN_H) break;  // 화면 꽉 찼으면 종료
    }
  } while (u8g2.nextPage());
}

// ---------- 슬롯 라벨 + 본문 2줄 출력 ----------
void drawSlotAndText(const String& slot, const String& text) {
  String composed = slot + "\n" + text;
  drawMultilineUTF8(composed);
}

// ---------- 화면 표시/지우기 ----------
void displayPlate(const String& slot, const String& plate) {
  String msg = slot + String("\n") + plate;
  if (msg == lastShown) return;
  lastShown = msg;
  drawSlotAndText(slot, plate);
}

void clearDisplayToIdle(const String& slot) {
  String msg = slot + String("\n") + "빈 자리";
  if (msg == lastShown) return;
  lastShown = msg;
  drawSlotAndText(slot, "빈 자리");
}

// OLED에 상태 메시지 표시(중복 출력 방지)
void displayStatus(const String& msg) {
  static String lastShown = "";
  if (msg == lastShown) return;
  lastShown = msg;
  Serial.printf("   OLED: %s\n", msg.c_str());
  drawMultilineUTF8(msg);
}


// ——— Wi‑Fi 재연결 함수 ———
void ensureWiFiConnected() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.println("▶ WiFi 끊김, 재연결 시도...");
  displayStatus("WiFi 재연결...");

  // 자동 재연결 모드에서 reconnect() 호출
  WiFi.reconnect();

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
    delay(200);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n▶ WiFi 재연결 성공");
    displayStatus("WiFi OK");
  } else {
    Serial.println("\n▶ WiFi 재연결 실패");
    displayStatus("WiFi FAIL");
  }
}

// ——— WebSocket 이벤트 핸들러 ———
void onWsEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      wsConnected = true;
      // 연결되면 슬롯/대기 표시
      clearDisplayToIdle(SLOT_LABEL);
      break;

    case WStype_DISCONNECTED:
      wsConnected = false;
      // 끊기면 대기 화면
      clearDisplayToIdle(SLOT_LABEL);
      ensureWiFiConnected();
      break; 

    case WStype_ERROR:
      displayStatus("WS 에러");
      break;

    case WStype_TEXT:
      {
        String txt = String((char*)payload).substring(0, length);

        // 기대 JSON 예:
        // {"assignment":"A1","license_plate":"12가3456"}
        // {"assignment":"A1","license_plate":""}  // exit → 지움
        String assignment = extractJsonString(txt, "assignment");
        String plate = extractJsonString(txt, "license_plate");

        if (upper(assignment) != upper(SLOT_LABEL)) {
          // 내 슬롯 아님 → 무시
          return;
        }

        if (plate.length() == 0) {
          // EXIT → 지움
          clearDisplayToIdle(SLOT_LABEL);
        } else {
          displayPlate(SLOT_LABEL, plate);
        }
        break;
      }
    case WStype_BIN:
    case WStype_FRAGMENT_TEXT_START:
    case WStype_FRAGMENT_FIN:
    default:
      break;
  }
}

void setup() {
  // 시리얼
  Serial.begin(19200);
  delay(100);
  Serial.println("\n===== 부팅 시작 =====");

  // OLED
  u8g2.begin();
  u8g2.enableUTF8Print();
  u8g2.setFont(u8g2_font_unifont_t_korean2);
  drawSlotAndText(SLOT_LABEL, "부팅중...");

  // Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
  WiFi.setSleepMode(WIFI_NONE_SLEEP);
  Serial.printf("▶ WiFi 연결 시도: %s\n", SSID);
  WiFi.begin(SSID, PASSWORD);
  unsigned long t0 = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - t0 < 10000) {
    delay(200);
  }
  clearDisplayToIdle(SLOT_LABEL);

  // WebSocket 설정
  // WebSocket (ws)
  webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
  // WebSocket (wss)
  // webSocket.beginSSL(WS_HOST, WS_PORT, WS_PATH)
  webSocket.onEvent(onWsEvent);
  webSocket.setReconnectInterval(5000);
  webSocket.enableHeartbeat(15000, 3000, 2);
}

void loop() {
  webSocket.loop();

  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 5000) {
    lastCheck = millis();
    if (!wsConnected) {
      ensureWiFiConnected();
    }
  }
  delay(10);
}
