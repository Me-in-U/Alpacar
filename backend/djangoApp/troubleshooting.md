# 🔧 푸쉬 알림 문제 해결 가이드

## 🚨 문제별 해결 방법

### 1. 브라우저에 알림이 안 나타남

#### 문제: 알림 권한이 차단됨
```javascript
// 권한 상태 확인
console.log(Notification.permission);
// "denied" 또는 "default"인 경우
```

**해결방법:**
- **Chrome**: 주소창 🔒 클릭 → 알림 → 허용
- **Firefox**: 주소창 🛡️ 클릭 → 알림 권한 → 허용
- **Edge**: 주소창 🔒 클릭 → 사이트 권한 → 알림 → 허용

#### 문제: Service Worker가 등록되지 않음
```javascript
// Service Worker 등록 확인
navigator.serviceWorker.getRegistrations().then(console.log);
// 빈 배열이 반환되는 경우
```

**해결방법:**
1. 페이지 새로고침 (Ctrl+F5)
2. 브라우저 캐시 삭제
3. Service Worker 재등록:
```javascript
navigator.serviceWorker.register('/service-worker.js')
.then(reg => console.log('등록 성공:', reg))
.catch(err => console.error('등록 실패:', err));
```

#### 문제: HTTPS 미지원
Push 알림은 HTTPS에서만 작동합니다.

**해결방법:**
- 개발 환경: `localhost`는 예외적으로 HTTP도 지원
- 프로덕션: HTTPS 인증서 설치 필요

### 2. API 호출 에러

#### 401 Unauthorized
```json
{"detail": "Invalid token."}
```

**해결방법:**
```javascript
// 토큰 확인
console.log(localStorage.getItem('access_token'));

// 토큰이 없거나 만료된 경우 다시 로그인
// 또는 새 토큰 발급
fetch('/api/auth/token/refresh/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    refresh: localStorage.getItem('refresh_token')
  })
}).then(r => r.json()).then(data => {
  localStorage.setItem('access_token', data.access);
});
```

#### 403 Forbidden
```json
{"detail": "Push notifications are disabled for this user."}
```

**해결방법:**
1. 사용자 푸쉬 알림 설정 확인
2. 헤더에서 푸쉬 알림 ON으로 변경
3. Push 구독 활성화:
```javascript
fetch('/api/push/setting/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({enabled: true})
});
```

#### 500 Internal Server Error
**해결방법:**
1. Django 서버 콘솔에서 에러 로그 확인
2. 데이터베이스 연결 상태 확인
3. VAPID 키 설정 확인

### 3. 앱 내 알림함에 알림이 안 쌓임

#### 문제: Service Worker 메시지 전달 실패
**해결방법:**
```javascript
// Service Worker에서 앱으로 메시지 전달 확인
navigator.serviceWorker.addEventListener('message', event => {
  console.log('Service Worker 메시지:', event.data);
});
```

#### 문제: Store 연동 실패 (Vue/Pinia)
**해결방법:**
1. main.ts에서 Service Worker 리스너 확인
2. Store의 addNotification 함수 확인
3. 알림 데이터 형식 검증

### 4. 모바일에서 알림이 안 옴

#### 문제: 배터리 최적화 설정
**Android 해결방법:**
1. 설정 → 배터리 → 배터리 최적화
2. 브라우저 앱 → 최적화하지 않음 선택

#### 문제: PWA 설치 필요
**해결방법:**
1. 브라우저 메뉴 → "홈 화면에 추가"
2. PWA로 설치 후 알림 권한 재설정

### 5. 알림 클릭 시 페이지 이동 안 됨

#### 문제: Service Worker의 notificationclick 핸들러 오류
**해결방법:**
Service Worker 파일 확인:
```javascript
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  
  // URL 라우팅 로직 확인
  let urlToOpen = '/';
  switch (data.type) {
    case 'vehicle_entry':
      urlToOpen = '/parking-recommend';
      break;
    // ... 기타 케이스
  }
  
  console.log('알림 클릭, 이동할 URL:', urlToOpen);
});
```

## 🔍 진단 도구

### 전체 시스템 진단
```javascript
async function 푸쉬알림_진단() {
  console.log('🔍 푸쉬 알림 시스템 진단 시작');
  
  // 1. 브라우저 지원 확인
  console.log('1. 브라우저 지원');
  console.log('   - Notification 지원:', 'Notification' in window);
  console.log('   - Service Worker 지원:', 'serviceWorker' in navigator);
  console.log('   - Push Manager 지원:', 'PushManager' in window);
  
  // 2. 권한 상태
  console.log('2. 권한 상태');
  console.log('   - 알림 권한:', Notification.permission);
  
  // 3. Service Worker 상태
  console.log('3. Service Worker 상태');
  const registrations = await navigator.serviceWorker.getRegistrations();
  console.log('   - 등록된 수:', registrations.length);
  
  if (registrations.length > 0) {
    const reg = registrations[0];
    console.log('   - 상태:', reg.active ? '활성' : '비활성');
    console.log('   - Scope:', reg.scope);
  }
  
  // 4. Push 구독 상태
  console.log('4. Push 구독 상태');
  if (registrations.length > 0) {
    const subscription = await registrations[0].pushManager.getSubscription();
    console.log('   - 구독 여부:', subscription ? '구독됨' : '구독안됨');
    if (subscription) {
      console.log('   - Endpoint:', subscription.endpoint.substr(0, 50) + '...');
    }
  }
  
  // 5. 로그인 상태
  console.log('5. 로그인 상태');
  const token = localStorage.getItem('access_token');
  console.log('   - 토큰 존재:', !!token);
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      console.log('   - 토큰 만료:', new Date(payload.exp * 1000) < new Date() ? '만료됨' : '유효함');
    } catch (e) {
      console.log('   - 토큰 파싱 실패');
    }
  }
  
  // 6. 서버 연결 테스트
  console.log('6. 서버 연결 테스트');
  try {
    const response = await fetch('/api/notifications/unread-count/', {
      headers: {'Authorization': 'Bearer ' + token}
    });
    console.log('   - API 응답:', response.status, response.ok ? '성공' : '실패');
  } catch (e) {
    console.log('   - API 에러:', e.message);
  }
  
  console.log('🔍 진단 완료');
}

// 실행
푸쉬알림_진단();
```

### 실시간 로그 모니터링
```javascript
// Service Worker 메시지 모니터링
navigator.serviceWorker.addEventListener('message', event => {
  console.log('📨 Service Worker 메시지:', event.data);
});

// Push 이벤트 리스너 (디버깅용)
navigator.serviceWorker.ready.then(registration => {
  registration.addEventListener('message', event => {
    console.log('📱 Push 이벤트:', event.data);
  });
});
```

## 🔄 캐시 및 재설정

### 브라우저 캐시 완전 삭제
1. **Chrome**: Ctrl+Shift+Del → "고급" → 모든 항목 선택 → 데이터 삭제
2. **Firefox**: Ctrl+Shift+Del → 모든 항목 선택 → 지금 지우기
3. **개발자 도구**: F12 → Application → Storage → Clear storage

### Service Worker 완전 재등록
```javascript
// 기존 Service Worker 해제
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(registration => {
    registration.unregister().then(success => {
      console.log('Service Worker 해제:', success);
    });
  });
});

// 페이지 새로고침 후 재등록 확인
location.reload();
```

### 푸쉬 구독 재설정
```javascript
async function 푸쉬구독_재설정() {
  // 기존 구독 해제
  const registration = await navigator.serviceWorker.ready;
  const subscription = await registration.pushManager.getSubscription();
  if (subscription) {
    await subscription.unsubscribe();
    console.log('기존 구독 해제됨');
  }
  
  // 새 구독 생성
  const vapidPublicKey = 'YOUR_VAPID_PUBLIC_KEY'; // settings.py에서 확인
  const newSubscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: vapidPublicKey
  });
  
  // 서버에 새 구독 전송
  await fetch('/api/push/subscribe/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      endpoint: newSubscription.endpoint,
      keys: {
        p256dh: btoa(String.fromCharCode(...new Uint8Array(newSubscription.getKey('p256dh')))),
        auth: btoa(String.fromCharCode(...new Uint8Array(newSubscription.getKey('auth'))))
      }
    })
  });
  
  console.log('푸쉬 구독 재설정 완료');
}
```

## 📞 개발자 지원

### Django 서버 로그 확인
```bash
# Django 서버를 디버그 모드로 실행
python manage.py runserver --settings=djangoApp.settings
```

### 데이터베이스 직접 확인
```sql
-- 알림 테이블 확인
SELECT * FROM accounts_notification ORDER BY created_at DESC LIMIT 10;

-- Push 구독 확인
SELECT * FROM accounts_push_subscription;

-- 사용자 푸쉬 설정 확인
SELECT email, push_enabled FROM accounts_user WHERE email = 'jun3021303@naver.com';
```

### Python 스크립트 실행
```bash
# 백엔드 테스트 실행
cd C:\Users\baekj\Desktop\백종석\S13P11E102\backend\djangoApp
"C:\Users\baekj\Desktop\백종석\S13P11E102\backend\djangoApp\venv\Scripts\python.exe" test_notifications.py
```

## 🆘 긴급 복구

모든 설정을 초기화하고 처음부터 다시 설정:

```javascript
async function 긴급복구() {
  console.log('🆘 푸쉬 알림 시스템 긴급 복구 시작');
  
  // 1. 모든 Service Worker 해제
  const registrations = await navigator.serviceWorker.getRegistrations();
  for (const registration of registrations) {
    await registration.unregister();
  }
  
  // 2. 로컬 스토리지 정리
  localStorage.removeItem('notification_settings');
  
  // 3. 알림 권한 재요청 (사용자 액션 필요)
  if (Notification.permission !== 'granted') {
    await Notification.requestPermission();
  }
  
  // 4. 페이지 새로고침
  console.log('📱 페이지를 새로고침하고 다시 설정하세요.');
  setTimeout(() => location.reload(), 2000);
}
```