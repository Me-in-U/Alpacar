# 단순 푸시 알림 시스템 가이드

## 📋 개요

관리자 페이지에서 수동 입차/주차 배정/주차 완료/출차 등의 이벤트 발생 시 사용자에게 푸시 알림을 보내는 단순 동기 처리 시스템입니다.

**아키텍처**: 이벤트 발생 → 즉시 Notification 레코드 생성 → WebPush 전송 (동기 처리)

## 🔧 특징

- **No Redis/Celery**: 외부 의존성 없음
- **동기 처리**: 관리자 액션 시 즉시 알림 생성 및 전송
- **간단한 설정**: Django 기본 설정만 필요
- **WebPush 사용**: FCM 대신 표준 WebPush API 사용

## 📱 알림 종류 및 트리거

### 1. 입차 알림 (`vehicle_entry`)
- **트리거**: `events/views.py:manual_entrance()`
- **메시지**: "관리자가 {번호판} 차량의 입차를 처리했습니다."
- **액션**: 주차 추천 페이지로 이동

### 2. 주차 배정 알림 (`parking_assigned`)
- **트리거**: 주차 배정 시 (수동으로 추가 가능)
- **메시지**: "관리자가 {번호판} 차량을 {구역}에 배정했습니다."
- **액션**: 관리자 주차 상태 페이지로 이동

### 3. 주차 완료 알림 (`parking_complete`)
- **트리거**: `events/views.py:manual_parking_complete()`
- **메시지**: "관리자가 {번호판} 차량의 주차를 완료 처리했습니다. ({구역}, {점수}점)"
- **액션**: 주차 이력 페이지로 이동

### 4. 출차 완료 알림 (`vehicle_exit`)
- **트리거**: `events/views.py:manual_exit()`
- **메시지**: "관리자가 {번호판} 차량의 출차를 처리했습니다. ({구역}에서 {시간} 주차)"
- **액션**: 주차 이력 페이지로 이동

## 🔄 시스템 플로우

```
관리자 액션 → 즉시 알림 생성 → WebPush 전송 → 사용자 수신
```

### 동기 처리의 장단점
- **장점**: 
  - 설정 간단함
  - 외부 의존성 없음
  - 디버깅 용이
  - 즉시 결과 확인 가능

- **단점**:
  - 관리자 페이지 응답이 푸시 전송 시간만큼 지연될 수 있음
  - 푸시 전송 실패 시 재시도 메커니즘 없음
  - 대량 사용자에게 동시 전송 시 성능 이슈 가능

## 📁 파일 구조

```
backend/djangoApp/
├── accounts/
│   ├── notification_helpers.py     # 알림 전송 헬퍼 함수
│   ├── utils.py                    # 기본 알림 생성 및 푸시 전송
│   └── models.py                   # Notification, PushSubscription 모델
├── events/views.py                 # 관리자 액션 뷰 (알림 트리거)
├── djangoApp/
│   └── settings.py                 # Django 설정 (VAPID 키 설정)
└── accounts/management/commands/
    └── test_simple_push.py         # Django management command 테스트
```

## 🧪 테스트 방법

### 1. 시스템 테스트 실행
```bash
# Django management command로 테스트 실행
python manage.py test_simple_push
```

### 2. 수동 테스트
1. Django 서버 실행: `python manage.py runserver`
2. 관리자 페이지에서 수동 입차/주차완료/출차 실행
3. 사용자 디바이스에서 알림 확인

### 3. 로그 확인
- **Django 로그**:
  ```
  [NOTIFICATION] 알림 생성: {notification_id}
  [PUSH] 푸시 알림 전송 요청: {user_email} - {title}
  [ADMIN] 입차 알림 전송됨: {license_plate}
  ```

## 🔧 설정

### VAPID 키 설정 (.env 파일)
```bash
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_CLAIM_SUB=mailto:admin@i13e102.p.ssafy.io
```

### 프론트엔드 Service Worker 구독 필요
- 사용자가 실제 푸시를 받기 위해서는 프론트엔드에서 Service Worker 등록 필요
- PushSubscription 모델에 구독 정보가 저장되어야 함

## 🔧 트러블슈팅

### 푸시 알림이 전송되지 않는 경우
1. **VAPID 키 확인**: `.env` 파일의 VAPID 키가 올바른지 확인
2. **구독 확인**: 사용자의 PushSubscription 데이터가 있는지 확인
3. **push_enabled 확인**: 사용자의 `push_enabled` 필드가 `True`인지 확인

### 알림이 생성되지 않는 경우
1. **사용자 확인**: 차량의 소유자 정보가 올바른지 확인
2. **Django 로그 확인**: 콘솔에서 `[NOTIFICATION]`, `[ADMIN]` 태그 확인
3. **데이터베이스 확인**: Notification 테이블에 레코드가 생성되는지 확인

## 📊 모니터링

### 로그 패턴
```python
# 성공적인 알림 생성
[NOTIFICATION] 알림 생성: 123

# 성공적인 푸시 전송
[PUSH] 푸시 알림 전송 요청: user@example.com - 관리자 입차 처리

# 관리자 액션 성공
[ADMIN] 입차 알림 전송됨: 12가3456 -> user@example.com

# 푸시 설정 문제
[PUSH] 푸시 알림 비활성화됨: user@example.com (push_enabled=False)
[PUSH] 구독 정보 없음: user@example.com - 프론트엔드에서 service worker 구독 등록 필요

# 오류
[PUSH ERROR] 푸시 전송 실패: {error_message}
[ADMIN ERROR] 입차 알림 전송 실패: {error_message}
```

## 🚀 확장 가능성

향후 필요에 따라 다음과 같이 확장 가능:

1. **비동기 처리 추가**: Celery 재도입으로 성능 향상
2. **재시도 메커니즘**: 푸시 전송 실패 시 재시도 로직
3. **배치 전송**: 여러 사용자에게 효율적 전송
4. **알림 템플릿**: 다양한 알림 유형에 대한 템플릿화
5. **통계 및 분석**: 알림 전송 성공률, 사용자 반응 등 분석

## 📞 지원

문제 발생 시:
1. Django 콘솔 로그 확인 (`[NOTIFICATION]`, `[PUSH]`, `[ADMIN]` 태그)
2. 테스트 스크립트 실행으로 기본 기능 점검
3. 프론트엔드 Service Worker 구독 상태 확인
4. VAPID 키 설정 재확인