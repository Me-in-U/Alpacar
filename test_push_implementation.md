# Push Notification Implementation Test Guide

## 구현된 기능

### 1. Header 컴포넌트 업데이트
- ✅ 알림함 모달에 푸시 알림 슬라이더 추가
- ✅ 푸시 알림 상태 실시간 표시 (활성화됨/비활성화됨/권한 없음/구독 없음)
- ✅ 테스트 알림 버튼 추가 (푸시 알림이 켜진 경우에만 표시)
- ✅ 푸시 알림 토글 시 자동 상태 확인 및 업데이트

### 2. UserProfile 페이지 업데이트
- ✅ 푸시 알림 토글 제거 (헤더에서만 관리하도록 변경)
- ✅ PWA 설치 기능만 유지

### 3. 백엔드 API 추가
- ✅ `/push/test/` 엔드포인트 추가
- ✅ 사용자 푸시 활성화 상태 확인
- ✅ 구독 정보 확인
- ✅ 테스트 푸시 알림 로깅

### 4. 유틸리티 함수 추가
- ✅ `pushNotification.ts`: 푸시 상태 종합 체크
- ✅ 테스트 푸시 알림 전송 함수
- ✅ 상태별 텍스트 및 CSS 클래스 제공

## 테스트 절차

### Frontend 테스트

1. **헤더 알림 버튼 클릭**
   ```
   - 알림함 모달이 열림
   - 상단 우측에 "푸시 알림" 슬라이더와 상태 표시가 보임
   - 상태: "권한 없음", "구독 없음", "비활성화됨", "활성화됨" 중 하나
   ```

2. **푸시 알림 활성화**
   ```
   - 슬라이더를 켜기로 변경
   - 브라우저에서 알림 권한 요청
   - 권한 허용 시 구독 정보 생성 및 서버 전송
   - 1초 후 "🔔 푸시 알림 활성화" 테스트 알림 표시
   - 상태가 "활성화됨"으로 변경
   ```

3. **테스트 알림 버튼**
   ```
   - 푸시 알림이 켜진 경우에만 "테스트 알림" 버튼 표시
   - 버튼 클릭 시:
     - 로컬 브라우저 알림: "🚗 로컬 테스트 알림"
     - 서버 API 호출: "🎉 서버 테스트 알림"
   ```

4. **UserProfile 페이지**
   ```
   - 푸시 알림 토글이 제거됨
   - "앱 설치" 섹션만 존재
   - PWA 설치 버튼만 표시됨
   ```

### Backend 테스트

1. **Push Setting API**
   ```bash
   # GET 요청 - 푸시 설정 조회
   curl -H "Authorization: Bearer <token>" http://localhost:8000/api/push/setting/
   
   # 응답 예시:
   # {"push_on": true, "vapid_public_key": "..."}
   ```

2. **Test Push API**
   ```bash
   # POST 요청 - 테스트 푸시 알림
   curl -X POST -H "Authorization: Bearer <token>" \
        -H "Content-Type: application/json" \
        -d '{"title": "테스트", "body": "테스트 메시지"}' \
        http://localhost:8000/api/push/test/
   
   # 성공 응답 예시:
   # {
   #   "message": "테스트 푸시 알림이 전송되었습니다.",
   #   "title": "테스트",
   #   "body": "테스트 메시지",
   #   "subscriptions_count": 1
   # }
   ```

3. **Subscribe API**
   ```bash
   # POST 요청 - 구독 정보 등록
   curl -X POST -H "Authorization: Bearer <token>" \
        -H "Content-Type: application/json" \
        -d '{
          "endpoint": "https://...",
          "keys": {
            "p256dh": "...",
            "auth": "..."
          }
        }' \
        http://localhost:8000/api/push/subscribe/
   ```

## 브라우저 개발자 도구에서 확인

### Console 로그 확인
```javascript
// 푸시 상태 확인
console.log('Push status updated:', status);

// 테스트 알림 전송
console.log('서버 테스트 알림 전송 성공');
console.log('로컬 테스트 알림 표시');

// 푸시 토글 변경
console.log('[togglePush] 시작, 변경 요청:', true/false);
console.log('[togglePush] 완료, 최종 상태:', true/false);
```

### Network 탭 확인
```
- /push/setting/ (GET/POST)
- /push/subscribe/ (POST)
- /push/test/ (POST)
```

### Application 탭 확인
```
- Service Workers: service-worker.js 등록 상태
- Push Messaging: 구독 정보 존재 여부
- Local Storage: 사용자 정보 및 토큰
```

## 예상 시나리오

### 성공 시나리오
1. 사용자가 헤더 알림 버튼 클릭
2. 푸시 알림 슬라이더를 "켜기"로 변경
3. 브라우저 권한 허용
4. 구독 정보 생성 및 서버 전송
5. 상태가 "활성화됨"으로 변경
6. "테스트 알림" 버튼 표시
7. 테스트 버튼 클릭 시 로컬 + 서버 알림 전송

### 오류 시나리오
1. **HTTPS 필요**: 로컬 개발 환경에서 HTTP 사용 시 Service Worker 제한
2. **권한 거부**: 사용자가 브라우저 알림 권한 거부
3. **VAPID 키 없음**: 환경 변수 또는 서버 설정 누락
4. **인증 토큰 없음**: 로그인하지 않은 상태

## 디버깅 가이드

### Frontend 디버깅
```javascript
// 푸시 상태 확인
import { checkPushStatus } from '@/utils/pushNotification';
const status = await checkPushStatus();
console.log('Current push status:', status);

// 구독 상태 확인
import { getSubscriptionStatus } from '@/utils/pwa';
const subscription = await getSubscriptionStatus();
console.log('Current subscription:', subscription);
```

### Backend 디버깅
```python
# Django shell에서 확인
from accounts.models import PushSubscription, User

# 사용자별 구독 정보 확인
user = User.objects.get(email='test@example.com')
subscriptions = PushSubscription.objects.filter(user=user)
print(f"User {user.email} has {subscriptions.count()} subscriptions")
print(f"Push enabled: {user.push_enabled}")
```