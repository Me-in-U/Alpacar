# ⚡ 푸쉬 알림 빠른 테스트 명령어

## 🚀 즉시 실행 가능한 테스트

### 1. 브라우저 Console에서 바로 실행

앱에 로그인 후, 개발자 도구 Console(F12)에서 아래 명령어들을 복사해서 실행하세요.

#### 🚗 입차 알림 테스트
```javascript
fetch('/api/notifications/test-entry/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.log('입차 알림:', d));
```

#### 🅿️ 주차 완료 알림 테스트
```javascript
fetch('/api/notifications/test-parking/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.log('주차 완료:', d));
```

#### 🎉 등급 승급 알림 테스트
```javascript
fetch('/api/notifications/test-grade/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.log('등급 승급:', d));
```

#### 🔄 모든 알림 순차 테스트
```javascript
fetch('/api/notifications/test-all/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.log('전체 테스트:', d));
```

### 2. 상태 확인 명령어

#### 알림 권한 확인
```javascript
console.log('알림 권한:', Notification.permission);
console.log('알림 지원:', 'Notification' in window);
```

#### Service Worker 상태 확인
```javascript
navigator.serviceWorker.getRegistrations().then(regs => 
  console.log('Service Worker 등록:', regs)
);
```

#### Push 구독 상태 확인
```javascript
navigator.serviceWorker.ready.then(reg => 
  reg.pushManager.getSubscription()
).then(sub => console.log('Push 구독:', sub));
```

#### 현재 알림 개수 확인
```javascript
fetch('/api/notifications/unread-count/', {
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.log('읽지 않은 알림:', d));
```

## 📱 모바일 테스트용 QR 코드 생성

개발 서버 주소를 QR 코드로 변환해서 모바일에서 쉽게 접속할 수 있습니다.

```javascript
// QR 코드 생성 (현재 URL)
console.log('QR 코드 생성:', `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(window.location.origin)}`);
```

## 🔧 디버깅 명령어

### 알림 목록 조회
```javascript
fetch('/api/notifications/', {
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.table(d.results));
```

### 모든 알림 읽음 처리
```javascript
fetch('/api/notifications/mark-all-read/', {
  method: 'PUT',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.log('읽음 처리:', d));
```

### 모든 알림 삭제
```javascript
fetch('/api/notifications/delete-all/', {
  method: 'DELETE',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
}).then(r => r.json()).then(d => console.log('전체 삭제:', d));
```

## 🏃‍♂️ 원클릭 테스트 함수

Console에 붙여넣기하면 모든 테스트를 자동으로 실행합니다:

```javascript
async function 푸쉬알림_전체테스트() {
  console.log('🔔 푸쉬 알림 전체 테스트 시작');
  
  // 권한 확인
  console.log('1. 알림 권한:', Notification.permission);
  
  // Service Worker 확인
  const regs = await navigator.serviceWorker.getRegistrations();
  console.log('2. Service Worker 등록:', regs.length + '개');
  
  // 현재 알림 수 확인
  const unreadRes = await fetch('/api/notifications/unread-count/', {
    headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
  });
  const unreadData = await unreadRes.json();
  console.log('3. 읽지 않은 알림:', unreadData.unread_count + '개');
  
  // 입차 알림 테스트
  console.log('4. 입차 알림 테스트 중...');
  const entryRes = await fetch('/api/notifications/test-entry/', {
    method: 'POST',
    headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
  });
  const entryData = await entryRes.json();
  console.log('   ✅ 입차 알림:', entryData.message);
  
  // 2초 대기
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // 주차 완료 알림 테스트  
  console.log('5. 주차 완료 알림 테스트 중...');
  const parkingRes = await fetch('/api/notifications/test-parking/', {
    method: 'POST',
    headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
  });
  const parkingData = await parkingRes.json();
  console.log('   ✅ 주차 완료:', parkingData.message);
  
  // 2초 대기
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // 등급 승급 알림 테스트
  console.log('6. 등급 승급 알림 테스트 중...');
  const gradeRes = await fetch('/api/notifications/test-grade/', {
    method: 'POST',
    headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
  });
  const gradeData = await gradeRes.json();
  console.log('   ✅ 등급 승급:', gradeData.message);
  
  // 최종 알림 수 확인
  const finalRes = await fetch('/api/notifications/unread-count/', {
    headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
  });
  const finalData = await finalRes.json();
  console.log('7. 테스트 후 알림 수:', finalData.unread_count + '개');
  
  console.log('🎉 푸쉬 알림 전체 테스트 완료!');
  console.log('📱 브라우저 우상단에 알림이 표시되었는지 확인하세요.');
  console.log('🔔 헤더의 알림함(벨 아이콘)도 확인하세요.');
}

// 실행
푸쉬알림_전체테스트();
```

## 📋 체크리스트

테스트하면서 아래 항목들을 체크하세요:

### 기본 설정
- [ ] Django 서버 실행 중
- [ ] 브라우저에서 앱에 로그인됨  
- [ ] 브라우저 알림 권한 "허용"
- [ ] 앱 내 푸쉬 알림 설정 "ON"

### 브라우저 알림
- [ ] 브라우저 우상단에 알림 팝업 표시
- [ ] 알림 클릭 시 해당 페이지로 이동
- [ ] 알림 내용이 정확히 표시

### 앱 내 알림함
- [ ] 헤더 벨 아이콘에 빨간 뱃지
- [ ] 알림함에 새 알림 추가됨
- [ ] 알림 타입별 아이콘 표시
- [ ] 읽음/안읽음 상태 정상

### API 응답
- [ ] Console에 성공 메시지 출력
- [ ] HTTP 200/201 상태 코드
- [ ] 올바른 JSON 응답 데이터

## 🚨 자주 발생하는 문제

### "Notification.permission denied"
→ 브라우저 설정에서 알림 권한 다시 허용

### "Service Worker not registered" 
→ 페이지 새로고침 후 재시도

### "401 Unauthorized"
→ 다시 로그인해서 새 토큰 획득

### "알림이 안 보임"
→ 브라우저 알림 설정과 앱 푸쉬 설정 모두 확인