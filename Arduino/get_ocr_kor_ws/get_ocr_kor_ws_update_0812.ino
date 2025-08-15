// ==============================
// ESP8266 Plate Display (OLED)
// 출입관리 차단바: ws/text/ 브로드캐스트 수신
// ==============================
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
const char* WS_HOST = "i13e102.p.ssafy.io";
const uint16_t WS_PORT = 443;
const char* WS_PATH = "/ws/text/";
// const char* WS_HOST = "192.168.30.180";
// const uint16_t WS_PORT = 8000;
// const char* WS_PATH = "/ws/text/";

// === OLED 설정 ===
// U8G2_SSD1306_128X32_UNIVISION_F_HW_I2C u8g2(U8G2_R0, U8X8_PIN_NONE, SCL, SDA);
U8G2_SSD1306_128X64_NONAME_1_HW_I2C u8g2(U8G2_R0, /* reset=*/U8X8_PIN_NONE);

// === Servo 설정 ===
Servo gateServo;
const uint8_t SERVO_PIN = D5;  // 예: D5(GPIO14)
const uint8_t SERVO_OPEN_POS = 90;
const uint8_t SERVO_CLOSED_POS = 0;

// === VL53L0X 설정 ===
// Adafruit_VL53L0X lox = Adafruit_VL53L0X();
const uint16_t TRIGGER_THRESHOLD_MM = 150;  // 5cm

WebSocketsClient webSocket;
bool wsConnected = false;

// 차량 입차 상태 머신
bool carEntering = false;           // “입차” 명령을 받았는가?
bool carLeftZone = false;           // 차량이 센서 구역을 벗어났는가?
unsigned long leaveDetectedAt = 0;  // 벗어난 시각(ms)

String lastShown = "";

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
    const int maxW = SCREEN_W - LEFT_PAD - RIGHT_PAD;

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
          u8g2.setCursor(LEFT_PAD, y);
          u8g2.print(line);
          y += lineH;
          line = next;  // 다음 줄 시작
          i += step;
        }
      }
      // 남은 조각 출력
      if (line.length() > 0 && y + lineH <= SCREEN_H) {
        u8g2.setCursor(LEFT_PAD, y);
        u8g2.print(line);
        y += lineH;
      }
      if (y + lineH > SCREEN_H) break;  // 화면 꽉 찼으면 종료
    }
  } while (u8g2.nextPage());
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
        // 받은 메시지가 JSON이면, {"text":"..."} 형태로 파싱
        String txt = String((char*)payload).substring(0, length);
        int i = txt.indexOf("\"text\":");
        if (i >= 0) {
          int a = txt.indexOf('"', i + 7);
          int b = txt.indexOf('"', a + 1);
          if (a >= 0 && b > a) txt = txt.substring(a + 1, b);
        }

        // ▼ JSON 이스케이프된 줄바꿈을 실제 줄바꿈으로
        txt.replace("\\r\\n", "\n");
        txt.replace("\\n", "\n");
        Serial.printf("▶ TEXT: %s\n", txt.c_str());

        // 화면 표시 (자동 줄바꿈)
        displayStatus(txt);

        // “입차”로 시작하면 문 열기
        if (txt.startsWith("입차") && !carEntering) {
          carEntering = true;
          carLeftZone = false;
          gateServo.write(SERVO_OPEN_POS);
          displayStatus("Gate Open");
          // leaveDetectedAt 는 아직 기록 안 함 (VL53L0X 로직과 연동 지점)
        }
        break;
      }
    default:
      break;
  }
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
  // if (!lox.begin()) {
  //   displayStatus("VL53 init fail");
  //   while (1) delay(100);
  // }

  // 1) Wi‑Fi 자동 재연결 모드
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);
  WiFi.setSleepMode(WIFI_NONE_SLEEP);

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
  // webSocket.begin(WS_HOST, WS_PORT, WS_PATH);
  webSocket.beginSSL(WS_HOST, WS_PORT, WS_PATH);
  webSocket.onEvent(onWsEvent);
  webSocket.setReconnectInterval(5000);
  webSocket.enableHeartbeat(15000, 3000, 2);
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
      displayStatus("WS 시도...");
    }
    ensureWiFiConnected();
  }

  // VL53L0X_RangingMeasurementData_t measure;
  // lox.rangingTest(&measure, false);
  // 시리얼에 항상 출력해 줍니다.
  // if (measure.RangeStatus == 0) {
  //   Serial.printf("거리: %4d mm\n", measure.RangeMilliMeter);
  // } else {
  //   Serial.printf("거리측정 오류: 상태=%d\n", measure.RangeStatus);
  // }
  // // 2) 차량이 입차 중이고, 아직 벗어남 감지 전이면 거리 체크
  // if (carEntering && !carLeftZone) {
  //   if (measure.RangeStatus == 0 && measure.RangeMilliMeter > TRIGGER_THRESHOLD_MM) {
  //     // 구역 벗어남 감지
  //     carLeftZone = true;
  //     leaveDetectedAt = millis();
  //   }
  // }

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
