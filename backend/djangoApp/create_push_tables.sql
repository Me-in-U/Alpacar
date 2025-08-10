-- ===================================================
-- Push 알림 관련 테이블 생성 SQL (MySQL)
-- ===================================================

-- 1. accounts_notification 테이블 생성
DROP TABLE IF EXISTS accounts_notification;
CREATE TABLE accounts_notification (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL COMMENT '알림 제목',
    message TEXT NOT NULL COMMENT '알림 내용',
    notification_type VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT '알림 타입',
    data JSON COMMENT '추가 데이터 (JSON 형태)',
    is_read BOOLEAN NOT NULL DEFAULT FALSE COMMENT '읽음 여부',
    created_at DATETIME(6) NOT NULL COMMENT '생성 시간',
    user_id BIGINT NOT NULL COMMENT '사용자 ID (외래키)',
    
    -- 인덱스 생성 (성능 최적화)
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_is_read (is_read),
    INDEX idx_notification_type (notification_type),
    INDEX idx_user_read (user_id, is_read),
    
    -- 외래키 제약조건
    FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 알림 테이블';

-- 2. accounts_push_subscription 테이블 생성
DROP TABLE IF EXISTS accounts_push_subscription;
CREATE TABLE accounts_push_subscription (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    endpoint VARCHAR(500) NOT NULL COMMENT 'Push 구독 엔드포인트',
    p256dh VARCHAR(255) NOT NULL COMMENT 'P256DH 키',
    auth VARCHAR(255) NOT NULL COMMENT 'Auth 키',
    created_at DATETIME(6) NOT NULL COMMENT '구독 생성 시간',
    user_id BIGINT NOT NULL COMMENT '사용자 ID (외래키)',
    
    -- 인덱스 생성
    INDEX idx_user_id (user_id),
    INDEX idx_endpoint (endpoint(255)),
    INDEX idx_created_at (created_at),
    
    -- 중복 구독 방지를 위한 유니크 제약조건
    UNIQUE KEY uk_user_endpoint (user_id, endpoint(255)),
    
    -- 외래키 제약조건
    FOREIGN KEY (user_id) REFERENCES accounts_user(id) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Push 알림 구독 정보';

-- ===================================================
-- 테이블 생성 후 확인 쿼리
-- ===================================================

-- 생성된 테이블 목록 확인
SHOW TABLES LIKE 'accounts_%';

-- accounts_notification 테이블 구조 확인
DESCRIBE accounts_notification;

-- accounts_push_subscription 테이블 구조 확인
DESCRIBE accounts_push_subscription;

-- 테이블 레코드 수 확인
SELECT 'accounts_notification' as table_name, COUNT(*) as record_count FROM accounts_notification
UNION ALL
SELECT 'accounts_push_subscription' as table_name, COUNT(*) as record_count FROM accounts_push_subscription;

-- ===================================================
-- 테스트 데이터 삽입 (선택사항)
-- ===================================================

-- 테스트용 알림 데이터 삽입 (user_id는 실제 존재하는 사용자 ID로 변경)
/*
INSERT INTO accounts_notification (user_id, title, message, notification_type, data, is_read, created_at) VALUES 
(1, '🚗 입차 알림', '220로1284 차량이 SSAFY 주차장에 입차하였습니다.', 'vehicle_entry', 
 '{"plate_number": "220로1284", "parking_lot": "SSAFY 주차장", "action_url": "/parking-recommend"}', 
 FALSE, NOW(6)),
 
(1, '🅿️ 주차 완료', '220로1284 차량이 A5 구역에 주차를 완료했습니다.', 'parking_complete', 
 '{"plate_number": "220로1284", "parking_space": "A5", "score": 85}', 
 FALSE, NOW(6)),
 
(1, '🎉 등급 승급', '축하드립니다! 주차 등급이 중급자에서 고급자로 승급되었습니다.', 'grade_upgrade', 
 '{"old_grade": "중급자", "new_grade": "고급자", "current_score": 87}', 
 FALSE, NOW(6));
*/

-- ===================================================
-- Django 마이그레이션 테이블 업데이트 (선택사항)
-- ===================================================

-- Django가 이미 마이그레이션이 적용되었다고 인식하도록 설정
-- (실제 마이그레이션 이름은 accounts 앱의 migrations 폴더에서 확인)
/*
INSERT INTO django_migrations (app, name, applied) VALUES 
('accounts', '0003_notification', NOW()),
('accounts', '0004_update_notification_types', NOW())
ON DUPLICATE KEY UPDATE applied = NOW();
*/