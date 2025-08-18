-- 1) DB 생성 (이름: alpaca_car)
CREATE DATABASE `alpaca_car` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2) 계정 생성
CREATE USER 'E102' @'%' IDENTIFIED BY 'E102';

-- 3) 모든 권한 부여 (외부접속 포함)
GRANT ALL PRIVILEGES ON `alpaca_car`.* TO 'E102' @'%';

FLUSH PRIVILEGES;