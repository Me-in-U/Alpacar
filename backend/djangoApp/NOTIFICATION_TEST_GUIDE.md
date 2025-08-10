# 🔔 Push 알림 시스템 테스트 가이드

## 📋 구현 완료된 기능

### 1. 알림 타입별 기능

| 알림 타입            | 설명           | 클릭 시 이동 페이지    | 아이콘 |
| -------------------- | -------------- | ---------------------- | ------ |
| `vehicle_entry`    | 입차 알림      | `/parking-recommend` | 🚗     |
| `parking_complete` | 주차 완료 알림 | `/parking-history`   | 🅿️   |
| `grade_upgrade`    | 등급 승급 알림 | `/user/profile`      | 🎉     |
| `system`           | 시스템 알림    | `/main`              | ℹ️   |
| `maintenance`      | 점검 안내      | `/main`              | 🔧     |

### 2. 알림 예시

#### 입차 알림

- **제목**: 🚗 입차 알림
- **내용**: "220로1284 차량이 SSAFY 주차장에 입차하였습니다. 알림을 클릭하면 추천 주차자리를 안내드리겠습니다."
- **클릭 동작**: `/parking-recommend` 페이지로 이동

#### 주차 완료 알림 (점수 없음)

- **제목**: 🅿️ 주차 완료
- **내용**: "220로1284 차량이 A5 구역에 주차를 완료했습니다."
- **클릭 동작**: `/parking-history` 페이지로 이동

#### 주차 완료 알림 (점수 있음)

- **제목**: 🅿️ 주차 완료
- **내용**: "220로1284 차량이 A5 구역에 주차를 완료했습니다. 이번 주차의 점수는 80점입니다."
- **클릭 동작**: `/parking-history` 페이지로 이동

#### 등급 승급 알림

- **제목**: 🎉 등급 승급 축하!
- **내용**: "축하드립니다! 주차 등급이 중급자에서 고급자로 승급되었습니다. (현재 점수: 87점)"
- **클릭 동작**: `/user/profile` 페이지로 이동

## 🧪 테스트 API 엔드포인트

CREATE TABLE accounts_notification (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '사용자 ID (외래키)',

    title VARCHAR(100) NOT NULL COMMENT '알림 제목',
    message TEXT NOT NULL COMMENT '알림 내용',
    notification_type ENUM('system','parking','entry','exit','warning','general')
        NOT NULL DEFAULT 'system' COMMENT '알림 타입',

    data JSON COMMENT '추가 데이터 (JSON 형태)',
    is_read BOOLEAN NOT NULL DEFAULT FALSE COMMENT '읽음 여부',

    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시간',

    CONSTRAINT fk_accounts_notification_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user(id)
        ON DELETE CASCADE,

    -- 실전형 인덱스
    INDEX idx_user_created (user_id, created_at DESC),
    INDEX idx_user_isread_created (user_id, is_read, created_at DESC)

    -- 선택 인덱스/예시는 닫는 괄호 밖으로 빼거나, 위 두 인덱스 뒤에 콤마 없이 주석만 두세요.
) ENGINE=InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci
  COMMENT='사용자 알림 테이블';

### 전제조건

1. 헤더에서 푸시 알림을 **ON**으로 설정
2. 브라우저에서 알림 권한 허용
3. 로그인된 상태 (Bearer 토큰 필요)

### 개별 알림 테스트

#### 1. 입차 알림 테스트

```bash
POST /api/notifications/test-entry/
Headers: {
  "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
```

#### 2. 주차 완료 알림 테스트

```bash
POST /api/notifications/test-parking/
Headers: {
  "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
```

*50% 확률로 점수 포함/미포함 랜덤 테스트*

#### 3. 등급 승급 알림 테스트

```bash
POST /api/notifications/test-grade/
Headers: {
  "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
```

*랜덤 등급 조합으로 테스트*

#### 4. 모든 알림 순차 테스트

```bash
POST /api/notifications/test-all/
Headers: {
  "Authorization": "Bearer YOUR_ACCESS_TOKEN"
}
```

*입차 → 주차완료 → 등급승급 순서로 3초 간격 전송*

### 브라우저 개발자 도구에서 테스트

```javascript
// 입차 알림 테스트
fetch('/api/notifications/test-entry/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
});

// 주차 완료 알림 테스트
fetch('/api/notifications/test-parking/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
});

// 등급 승급 알림 테스트
fetch('/api/notifications/test-grade/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
});

// 모든 알림 순차 테스트
fetch('/api/notifications/test-all/', {
  method: 'POST',
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('access_token')}
});
```

## 🔍 동작 확인 사항

### 1. 브라우저 Push 알림

- [ ] 알림이 브라우저 우상단에 표시됨
- [ ] 알림 클릭 시 해당 페이지로 이동
- [ ] 알림 내용이 정확히 표시됨

### 2. 앱 내 알림함

- [ ] 헤더 벨 아이콘에 빨간 뱃지 표시
- [ ] 알림함 클릭 시 알림 목록에 추가됨
- [ ] 알림 타입별 아이콘 정상 표시
- [ ] 읽음/안읽음 상태 정상 동작

### 3. DB 저장

- [ ] `accounts_notification` 테이블에 레코드 저장
- [ ] 알림 타입(`notification_type`) 정확히 저장
- [ ] 추가 데이터(`data` JSON 필드) 정상 저장

## 🛠️ 마이그레이션 적용 방법

```bash
# Django 가상환경에서 실행
cd backend/djangoApp
python manage.py migrate accounts
```

## ⚠️ 문제 해결

### 알림이 안 오는 경우

1. 푸시 알림 설정이 ON인지 확인
2. 브라우저 알림 권한이 허용되었는지 확인
3. 로그인 상태 및 토큰 유효성 확인
4. 개발자 도구 Console에서 오류 메시지 확인

### 페이지 라우팅이 안 되는 경우

1. 해당 페이지 경로가 존재하는지 확인
2. Service Worker가 정상 등록되었는지 확인
3. 브라우저 개발자 도구 Application 탭에서 Service Workers 확인

### DB 오류가 나는 경우

1. 마이그레이션 적용 여부 확인
2. `accounts_notification` 테이블 존재 여부 확인
3. DB 연결 상태 및 권한 확인

## 🎯 실제 연동 시 참고사항

### 입차 감지 시 호출

```python
from accounts.utils import send_vehicle_entry_notification

# 차량 입차 감지 시
entry_data = {
    'plate_number': detected_plate,  # 인식된 차량번호
    'parking_lot': 'SSAFY 주차장',   # 주차장명
    'entry_time': timezone.now().isoformat(),
    'camera_location': 'Gate A'      # 추가 정보
}
send_vehicle_entry_notification(user, entry_data)
```

### 주차 완료 시 호출

```python
from accounts.utils import send_parking_complete_notification

# 주차 완료 감지 시
parking_data = {
    'plate_number': user_vehicle_plate,
    'parking_space': assigned_space,  # ex: 'A5'
    'parking_time': timezone.now().isoformat(),
    'score': calculated_score,        # 주차 점수 (없으면 None)
    'duration': parking_duration      # 추가 정보
}
send_parking_complete_notification(user, parking_data)
```

### 등급 승급 시 호출

```python
from accounts.utils import send_grade_upgrade_notification

# 점수 업데이트 후 등급 변경 감지 시
grade_data = {
    'old_grade': previous_grade,
    'new_grade': new_grade,
    'current_score': user.score,
    'upgrade_time': timezone.now().isoformat()
}
send_grade_upgrade_notification(user, grade_data)
```
