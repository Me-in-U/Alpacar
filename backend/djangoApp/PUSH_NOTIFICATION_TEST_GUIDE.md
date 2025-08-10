# 🔔 푸쉬 알림 테스트 가이드

## 📋 준비 사항

### 1. 서버 준비
```bash
# Django 서버 시작
cd C:\Users\baekj\Desktop\백종석\S13P11E102\backend\djangoApp
"C:\Users\baekj\Desktop\백종석\S13P11E102\backend\djangoApp\venv\Scripts\python.exe" manage.py runserver
```

### 2. DB 테이블 확인
- ✅ `accounts_notification` 테이블 존재
- ✅ `accounts_push_subscription` 테이블 존재
- ✅ Django 모델 연동 완료

## 🌐 브라우저에서 테스트

### Step 1: 앱에 로그인
1. 브라우저에서 `http://localhost:8000` 접속
2. 계정으로 로그인 (`jun3021303@naver.com`)

### Step 2: 푸쉬 알림 권한 설정
1. **브라우저 알림 권한 허용**
   - Chrome: 주소창 왼쪽 🔒 클릭 → "알림" → "허용"
   - Firefox: 주소창 왼쪽 🛡️ 클릭 → "알림 권한" → "허용"

2. **앱 내 푸쉬 알림 설정**
   - 헤더에서 푸쉬 알림을 **ON**으로 설정
   - Service Worker 등록 확인

### Step 3: 개발자 도구에서 테스트

#### 3-1. 브라우저 개발자 도구 열기
- **Chrome/Edge**: F12 또는 Ctrl+Shift+I
- **Firefox**: F12 또는 Ctrl+Shift+I

#### 3-2. Console 탭에서 API 호출

##### 입차 알림 테스트
```javascript
fetch('/api/notifications/test-entry/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
    'Content-Type': 'application/json'
  }
}).then(response => response.json()).then(data => console.log(data));
```

##### 주차 완료 알림 테스트
```javascript
fetch('/api/notifications/test-parking/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
    'Content-Type': 'application/json'
  }
}).then(response => response.json()).then(data => console.log(data));
```

##### 등급 승급 알림 테스트
```javascript
fetch('/api/notifications/test-grade/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
    'Content-Type': 'application/json'
  }
}).then(response => response.json()).then(data => console.log(data));
```

##### 모든 알림 순차 테스트
```javascript
fetch('/api/notifications/test-all/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
    'Content-Type': 'application/json'
  }
}).then(response => response.json()).then(data => console.log(data));
```

## 🧪 Postman/Insomnia 테스트

### 1. 로그인하여 토큰 획득
```http
POST http://localhost:8000/api/auth/login/
Content-Type: application/json

{
  "email": "jun3021303@naver.com",
  "password": "your_password"
}
```

### 2. 응답에서 access_token 복사

### 3. 알림 테스트 API 호출

#### 입차 알림
```http
POST http://localhost:8000/api/notifications/test-entry/
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

#### 주차 완료 알림
```http
POST http://localhost:8000/api/notifications/test-parking/
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

#### 등급 승급 알림
```http
POST http://localhost:8000/api/notifications/test-grade/
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

#### 모든 알림 순차 테스트
```http
POST http://localhost:8000/api/notifications/test-all/
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```

## 🔍 테스트 확인 사항

### 1. 브라우저 Push 알림
- [ ] 알림이 브라우저 우상단에 표시됨
- [ ] 알림 제목과 내용이 올바르게 표시됨
- [ ] 알림 클릭 시 해당 페이지로 이동됨

### 2. 앱 내 알림함
- [ ] 헤더 벨 아이콘에 빨간 뱃지 표시
- [ ] 알림함 클릭 시 새 알림이 추가되어 있음
- [ ] 알림 타입별 아이콘이 정확히 표시됨
- [ ] 읽음/안읽음 상태가 올바름

### 3. Service Worker 작동
- [ ] 브라우저 개발자 도구 → Application → Service Workers에서 등록 확인
- [ ] Console에 Service Worker 메시지 표시

### 4. 데이터베이스 저장
- [ ] `accounts_notification` 테이블에 새 레코드 저장
- [ ] 알림 타입(`notification_type`)이 정확함
- [ ] JSON 데이터(`data` 필드)가 올바르게 저장됨

## 📱 모바일 테스트

### Chrome 모바일 시뮬레이션
1. 개발자 도구 → 모바일 아이콘 클릭
2. iPhone/Android 기기 선택
3. 위의 테스트 과정 반복

### 실제 모바일 기기
1. 모바일 브라우저에서 접속
2. PWA 설치 (Add to Home Screen)
3. 알림 권한 허용
4. 테스트 진행

## 🛠️ 문제 해결

### 알림이 안 나타나는 경우

#### 1. 브라우저 설정 확인
```javascript
// 브라우저가 알림을 지원하는지 확인
console.log('Notification' in window); // true여야 함

// 현재 알림 권한 상태 확인
console.log(Notification.permission); // "granted"여야 함
```

#### 2. Service Worker 등록 확인
```javascript
// Service Worker 등록 상태 확인
navigator.serviceWorker.ready.then(registration => {
  console.log('Service Worker registered:', registration);
});

// 활성화된 Service Worker 확인
navigator.serviceWorker.getRegistrations().then(registrations => {
  console.log('Registrations:', registrations);
});
```

#### 3. Push 구독 상태 확인
```javascript
// Push 구독 정보 확인
navigator.serviceWorker.ready.then(registration => {
  return registration.pushManager.getSubscription();
}).then(subscription => {
  console.log('Push subscription:', subscription);
});
```

### API 오류 해결

#### 401 Unauthorized
- 토큰이 만료되었거나 잘못됨
- 다시 로그인하여 새 토큰 획득

#### 403 Forbidden
- 사용자 권한 문제
- 푸쉬 알림이 비활성화된 상태

#### 500 Internal Server Error
- 서버 에러 로그 확인
- Django 서버 콘솔에서 에러 메시지 확인

## 🔧 고급 테스트

### 1. 수동으로 Push 구독 생성
```javascript
// VAPID 공개키 (Django settings에서 확인)
const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY';

// Push 구독 생성
navigator.serviceWorker.ready.then(registration => {
  return registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: vapidPublicKey
  });
}).then(subscription => {
  console.log('New subscription:', subscription);
  
  // 서버에 구독 정보 전송
  fetch('/api/push/subscribe/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      endpoint: subscription.endpoint,
      keys: {
        p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')))),
        auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth'))))
      }
    })
  });
});
```

### 2. Python 스크립트로 테스트
```bash
# 터미널에서 실행
cd C:\Users\baekj\Desktop\백종석\S13P11E102\backend\djangoApp
"C:\Users\baekj\Desktop\백종석\S13P11E102\backend\djangoApp\venv\Scripts\python.exe" test_notifications.py
```

## 📊 테스트 결과 예시

### 성공적인 API 응답
```json
{
  "message": "입차 알림이 전송되었습니다.",
  "type": "vehicle_entry",
  "data": {
    "plate_number": "220로1284",
    "parking_lot": "SSAFY 주차장",
    "entry_time": "2025-08-11T02:02:08.493370",
    "test": true
  }
}
```

### 알림함에 표시되는 내용
- **입차**: 🚗 "220로1284 차량이 SSAFY 주차장에 입차하였습니다. 알림을 클릭하면 추천 주차자리를 안내드리겠습니다."
- **주차완료**: 🅿️ "220로1284 차량이 A5 구역에 주차를 완료했습니다. 이번 주차의 점수는 79점입니다."
- **등급승급**: 🎉 "축하드립니다! 주차 등급이 전문가에서 마스터로 승급되었습니다. (현재 점수: 87점)"

## 🚨 주의사항

1. **HTTPS 필수**: Push 알림은 HTTPS에서만 작동 (localhost는 예외)
2. **브라우저 지원**: Chrome, Firefox, Edge 지원 (Safari는 제한적)
3. **사용자 상호작용**: 첫 알림은 사용자가 페이지와 상호작용한 후에만 작동
4. **서비스 워커**: 페이지가 닫혀있어도 백그라운드에서 작동
5. **배터리 최적화**: 모바일에서 배터리 최적화 설정이 알림을 차단할 수 있음

## 📞 지원

문제가 발생하면:
1. 브라우저 콘솔에서 에러 메시지 확인
2. Django 서버 로그 확인
3. Service Worker 등록 상태 확인
4. Push 구독 상태 확인