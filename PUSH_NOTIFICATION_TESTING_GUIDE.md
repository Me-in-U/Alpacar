# 🔔 통합 푸시 알림 테스트 시스템 가이드

**업데이트**: 기존의 분산된 테스트 도구들을 하나의 통합된 시스템으로 개선했습니다.

**최근 수정사항 (2025-01-08)**:
- ✅ **404 에러 수정**: 차량 API 호출 시 사용자의 실제 차량번호를 자동으로 조회하여 사용
- ✅ **스마트 폴백 시스템**: 테스트 API 실패 시 차량 API로 자동 전환
- ✅ **향상된 에러 처리**: 각 단계별 에러를 개별적으로 처리하고 사용자에게 명확한 피드백 제공
- ✅ **사용자 차량 정보 활용**: `/vehicles/` API를 통해 등록된 차량번호를 자동으로 가져와서 테스트에 사용
- ✅ **배치 테스트 개선**: 사용자별 차량번호로 일관된 테스트 진행

## 📋 개요

**통합 알림 테스트 시스템**의 주요 특징:

- ✅ **통합된 인터페이스**: 모든 테스트 기능을 하나의 컴포넌트에서 제공
- ✅ **실시간 API 상태 확인**: Production 환경과 Development 환경 자동 호환
- ✅ **스마트 폴백 시스템**: API 엔드포인트가 없을 때 대체 API 사용
- ✅ **관리자/사용자 구분**: 권한에 따른 기능 제한
- ✅ **실시간 상태 모니터링**: 푸시 설정, API 연결, 구독 현황 확인
- ✅ **포괄적 테스트 기능**: 기본, 주차 플로우, 시스템, 배치, 사용자 정의 테스트
- ✅ **도움말 및 문제 해결**: 사용자 친화적 가이드 제공

## 🛠️ 구현된 구성요소

### 1. 백엔드 API 엔드포인트

#### 기존 테스트 API (이미 있던 것들)
```
POST /api/notifications/test-push/          # 기본 푸시 알림 테스트
POST /api/notifications/test-entry/         # 입차 알림 테스트
POST /api/notifications/test-parking/       # 주차 완료 알림 테스트
POST /api/notifications/test-grade/         # 등급 승급 알림 테스트
POST /api/notifications/test-all/           # 모든 알림 순차 테스트
```

#### 새로 추가된 고급 테스트 API
```
POST /api/notifications/test-custom/        # 사용자 정의 알림 생성
POST /api/notifications/test-batch/         # 배치 알림 전송
POST /api/notifications/test-scenario/      # 시나리오 시뮬레이션
GET  /api/notifications/test-status/        # 테스트 상태 조회
DELETE /api/notifications/test-clear/       # 테스트 알림 삭제
```

### 2. 통합 프론트엔드 컴포넌트

#### 🆕 UnifiedNotificationTester.vue
- **파일**: `frontend/alpacar-vue/src/components/UnifiedNotificationTester.vue`
- **기능**: 
  - 모든 사용자(관리자/일반)를 위한 통합 인터페이스
  - 실시간 API 상태 확인 및 연결 테스트
  - 스마트 폴백 시스템으로 Production/Development 환경 모두 지원
  - 권한별 기능 제한 (관리자만 고급 기능 접근)

#### 사용 위치
1. **사용자 설정 페이지**: 모달 형태로 제공 (`UserSetting.vue`)
2. **관리자 테스트 페이지**: `/notification-test` 경로 (`NotificationTestView.vue`)
3. **독립적 접근**: 어디서든 컴포넌트로 임포트 가능

#### 🗂️ 정리된 컴포넌트들
- ~~`NotificationTestCenter.vue`~~ → **제거됨** (기능이 `UnifiedNotificationTester.vue`에 통합)
- ~~`NotificationTester.vue`~~ → **제거됨** (기능이 `UnifiedNotificationTester.vue`에 통합)
- ~~`NotificationTestPage.vue`~~ → **제거됨** (불필요한 래퍼 컴포넌트)

### 3. Python 테스트 도구

#### 종합 테스트 스크립트
- **파일**: `backend/djangoApp/notification_tester.py`
- **기능**: 명령행에서 실행 가능한 종합 테스트 도구

## 🚀 사용 방법

### A. 웹 인터페이스를 통한 테스트

#### 1. 관리자 테스트 센터 사용

1. 관리자로 로그인 후 NotificationTestCenter 페이지에 접속
2. "현재 상태" 섹션에서 푸시 설정 확인
3. "빠른 테스트" 버튼들로 기본 알림 테스트
4. "사용자 정의 알림"으로 원하는 내용의 알림 생성
5. "배치 알림 테스트"로 여러 개 알림 일괄 전송
6. "시나리오 시뮬레이션"으로 실제 사용 패턴 재현

#### 2. 일반 사용자 테스트 위젯 사용

1. 사용자 페이지에 NotificationTester 컴포넌트 추가
2. 푸시 알림 설정 상태 확인
3. "기본 알림 테스트" 또는 "주차 알림 체험" 버튼 클릭
4. 테스트 결과를 실시간으로 확인

### B. API를 직접 호출한 테스트

#### 1. 기본 푸시 알림 테스트

```bash
curl -X POST http://localhost:8000/api/notifications/test-push/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

#### 2. 사용자 정의 알림 생성

```bash
curl -X POST http://localhost:8000/api/notifications/test-custom/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "테스트 알림",
    "message": "이것은 사용자 정의 테스트 알림입니다.",
    "notification_type": "system"
  }'
```

#### 3. 배치 알림 전송

```bash
curl -X POST http://localhost:8000/api/notifications/test-batch/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notifications": [
      {
        "title": "첫 번째 알림",
        "message": "첫 번째 배치 알림입니다.",
        "notification_type": "system"
      },
      {
        "title": "두 번째 알림",
        "message": "두 번째 배치 알림입니다.",
        "notification_type": "system"
      }
    ],
    "delay": 3
  }'
```

#### 4. 시나리오 시뮬레이션

```bash
# 주차 플로우 시나리오
curl -X POST http://localhost:8000/api/notifications/test-scenario/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "parking_flow",
    "delay": 3
  }'

# 일일 사용 패턴 시나리오
curl -X POST http://localhost:8000/api/notifications/test-scenario/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "daily_usage",
    "delay": 2
  }'

# 긴급 상황 시나리오
curl -X POST http://localhost:8000/api/notifications/test-scenario/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "emergency_alerts",
    "delay": 1
  }'

# 등급 진행 시나리오
curl -X POST http://localhost:8000/api/notifications/test-scenario/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario": "grade_progression",
    "delay": 4
  }'
```

#### 5. 테스트 상태 조회

```bash
curl -X GET http://localhost:8000/api/notifications/test-status/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### C. Python 스크립트를 통한 테스트

#### 1. 기본 실행 (종합 테스트)

```bash
cd backend/djangoApp
python notification_tester.py
```

#### 2. 특정 기능만 테스트

```bash
# 상태 확인
python notification_tester.py --status

# 기본 알림 테스트
python notification_tester.py --basic

# 사용자 정의 알림
python notification_tester.py --custom "테스트 제목" "테스트 메시지"

# 배치 알림 (5개)
python notification_tester.py --batch 5

# 주차 시나리오
python notification_tester.py --scenario parking_flow

# 테스트 알림 삭제
python notification_tester.py --clear
```

#### 3. 옵션을 조합한 실행

```bash
# 3초 간격으로 배치 알림 7개 전송
python notification_tester.py --batch 7 --delay 3

# 5초 간격으로 주차 시나리오 실행
python notification_tester.py --scenario parking_flow --delay 5
```

## 📊 시나리오 설명

### 1. 주차 플로우 (parking_flow)
실제 주차장 사용 흐름을 재현합니다:
1. 🚗 **입차 감지**: "차량이 입차했습니다"
2. 📍 **진행 상황**: "추천 구역으로 이동 중"
3. ✅ **주차 완료**: "주차가 완료되었습니다"

### 2. 일일 사용 패턴 (daily_usage)
하루 동안의 알림 패턴을 시뮬레이션:
1. 🌅 **굿모닝**: "오늘도 안전한 주차되세요"
2. 🍽️ **점심시간**: "점심시간 혼잡 예상"
3. 🌆 **퇴근시간**: "퇴근 러시아워 주의"
4. 🌙 **일일 리포트**: "오늘의 주차 통계"

### 3. 긴급 상황 (emergency_alerts)
비상 상황 대응 알림:
1. 🚨 **긴급 경보**: "화재 경보 발생, 즉시 대피"
2. ⚠️ **차량 이동**: "긴급차량 진입, 차량 이동 요청"
3. ✅ **상황 종료**: "긴급상황 해결, 정상 이용 가능"

### 4. 등급 진행 (grade_progression)
사용자 등급 승급 과정:
1. 📊 **초급자 → 중급자**
2. 📈 **중급자 → 고급자**
3. 🏆 **고급자 → 전문가**
4. 👑 **전문가 → 마스터**

## 🔍 테스트 확인 방법

### 1. 브라우저에서 확인
- 브라우저 오른쪽 상단에 푸시 알림 팝업 표시
- 알림 클릭 시 해당 페이지로 이동
- 브라우저 알림 히스토리에서 확인 가능

### 2. 앱 내 알림함 확인
- 헤더의 벨 아이콘에 빨간 뱃지 표시
- 알림함 클릭하여 알림 목록 확인
- 읽음/안읽음 상태 확인

### 3. 개발자 도구에서 확인
- F12 → Console 탭에서 푸시 관련 로그 확인
- Application 탭 → Service Workers에서 SW 상태 확인
- Network 탭에서 API 호출 결과 확인

### 4. 데이터베이스에서 확인
```sql
-- 최근 생성된 테스트 알림 확인
SELECT * FROM accounts_notification 
WHERE JSON_EXTRACT(data, '$.test') = true 
ORDER BY created_at DESC 
LIMIT 10;

-- 사용자별 푸시 구독 상태 확인
SELECT u.email, COUNT(ps.id) as subscription_count
FROM accounts_user u 
LEFT JOIN accounts_push_subscription ps ON u.id = ps.user_id 
GROUP BY u.id, u.email;
```

## ⚠️ 주의사항 및 문제해결

### 1. 푸시 알림이 표시되지 않는 경우

#### 브라우저 설정 확인
```javascript
// 브라우저 콘솔에서 실행
console.log('알림 권한:', Notification.permission);
console.log('푸시 API 지원:', 'PushManager' in window);
```

#### Service Worker 상태 확인
```javascript
// Service Worker 등록 상태 확인
navigator.serviceWorker.getRegistrations().then(registrations => {
  console.log('SW 등록 수:', registrations.length);
  registrations.forEach(reg => console.log('SW:', reg));
});
```

### 2. API 호출 실패 시

#### 토큰 확인
```javascript
// 액세스 토큰 확인
const token = localStorage.getItem('access_token');
console.log('토큰 존재:', !!token);
console.log('토큰 길이:', token?.length);
```

#### 차량 등록 확인 (404 에러 해결)
```bash
# 사용자에게 차량이 등록되어 있는지 확인
curl -X GET http://localhost:8000/api/vehicles/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**차량 등록이 없는 경우:**
- 차량 등록 페이지(`/social-login-info`)에서 차량을 먼저 등록하세요
- 또는 관리자가 테스트용 차량을 직접 등록할 수 있습니다

#### 500 Internal Server Error 해결
**일반적인 원인:**
1. **VAPID 키 설정 누락**: Django settings에서 VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY 확인
2. **푸시 구독 없음**: 사용자가 푸시 알림을 허용하지 않았거나 구독 정보가 없음
3. **사용자 푸시 설정 비활성화**: User.push_enabled = False

**디버그 방법:**
```bash
# Django 서버 로그 확인
cd backend/djangoApp
python manage.py runserver --verbosity=2
```

**VAPID 키 설정 확인:**
```python
# Django shell에서 확인
python manage.py shell
>>> from django.conf import settings
>>> print('VAPID_PRIVATE_KEY:', hasattr(settings, 'VAPID_PRIVATE_KEY'))
>>> print('VAPID_PUBLIC_KEY:', hasattr(settings, 'VAPID_PUBLIC_KEY'))
```

### 3. 대량 테스트 시 주의사항

- 배치 알림은 한 번에 최대 10개까지만 가능
- 연속 테스트 시 2-3초 간격 권장
- 푸시 서비스 rate limit 고려하여 적절한 간격 유지

### 4. 모바일 브라우저에서 테스트

- PWA로 설치된 경우에만 백그라운드 푸시 가능
- 일부 모바일 브라우저는 절전 모드에서 알림 제한
- iOS Safari는 PWA 설치 필수

## 📝 추가 개발 예정 기능

### 단기 계획
- [ ] 알림 스케줄링 기능
- [ ] A/B 테스트를 위한 다중 버전 알림
- [ ] 푸시 성공률 통계 대시보드
- [ ] 알림 템플릿 관리 시스템

### 장기 계획
- [ ] 머신러닝 기반 최적 알림 시간 예측
- [ ] 사용자 행동 기반 개인화 알림
- [ ] 실시간 알림 효과 분석
- [ ] 다국어 알림 지원

## 🤝 기여하기

버그 리포트나 기능 제안은 다음과 같이 해주세요:

1. **버그 발견 시**: 재현 단계와 함께 이슈 등록
2. **새 기능 제안**: 사용 사례와 함께 제안서 작성
3. **코드 개선**: Pull Request로 개선사항 제출

## 📞 지원

문제가 발생하면 다음 정보와 함께 문의해주세요:

1. 사용 중인 브라우저 및 버전
2. 재현 가능한 단계
3. 에러 메시지 (콘솔 로그 포함)
4. 기대했던 결과와 실제 결과

---

## 📚 관련 문서

- [푸시 알림 시스템 아키텍처](./docs/push-notification-architecture.md)
- [API 문서](./docs/api-reference.md)
- [Service Worker 가이드](./docs/service-worker-guide.md)
- [보안 가이드라인](./docs/security-guidelines.md)