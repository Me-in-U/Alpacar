# Gitlab 소스 클론 이후 빌드 및 배포 가이드

## 목차

- [서버 구조](#서버-구조)
- [환경 변수](#환경-변수)
- [배포 시 특이사항](#배포-시-특이사항)
- [빌드 및 배포 가이드라인](#빌드-및-배포-가이드라인)
- [DB 접속 방법](#db-접속-방법)

## 서버 구조

![alt text](imgs/인프라구조도.png)

## 환경 변수

```Plain Text
SECRET_KEY='django-insecure-kxf+#3en!ta!hk#!pu2@ke!96)4kw5ez-r)9rhl(u2*n4ctic!'

DB_NAME=alpaca_car
DB_USER=E102
DB_PASSWORD=E102
DB_HOST=i13e102.p.ssafy.io
DB_PORT=3306
VAPID_PUBLIC_KEY=BKAyFkRk32KxeaF010jLccB0I16OmwD8_Ug0q3kA2lJRbtrccndnHyt7SKgN7aFEG6U5vhxOkXgSOoLV0w2RWzo
VAPID_PRIVATE_KEY=lRWK3qbuVWYx7FP6_WuBMGlyRAYrpNQgatnsyMqNPHc
VAPID_CLAIM_SUB=mailto:admin@example.com
GOOGLE_CLIENT_ID=397483208541-9s0evi1barg541jekfe3jp36e6b17549.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
SMTP_USER=jun3021303
SMTP_PASS=3N1S2EZYJTPB
SMTP_DEFAULT_FROM_EMAIL=jun3021303@naver.com

DJANGO_ALLOWED_HOSTS=i13e102.p.ssafy.io
VITE_BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api
VITE_FRONTEND_BASE_URL=https://i13e102.p.ssafy.io

FRONTEND_BASE_URL=https://i13e102.p.ssafy.io
BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api
```

## 배포 시 특이사항

현재 프로젝트는 develop 브랜치에서만 배포가 적용됩니다.
변경이 필요하시다면 소스의 .gitlab-ci.yml 코드에서 파이프라인을 수정해서 사용하시면 됩니다.

```yml
stages:
  - deploy

deploy-to-ec2:
  stage: deploy
  tags:
    - test
  script:
    - docker-compose down || true
    - docker-compose build | tee docker_build.log
    - docker-compose up -d --force-recreate
    - docker system prune -af --volumes
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"' # develop 브랜치만 적용된 설정
```

## 빌드 및 배포 가이드라인

아래의 가이드라인은 su 를 통한 계정 전환 이전까지는 모두 root 계정으로 실행된 것이 전제입니다.

### 1. 인증서 발급

```bash
sudo -s
apt update
apt install certbot
certbot certonly --standalone -d i13e102.p.ssafy.io

apt isntall net-tools
apt isntall docker
apt isntall docker.io
apt install docker-compose
apt isntall npm

ufw allow 80
```

### 2. gitlab runner 용 계정 생성

```bash

useradd --commend 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
su gitlab-runner
gitlab-runner
gitlab-runner register  --url https://lab.ssafy.com  --token glrt-e1JLOrTSI3Aqkw74C0Mtf286MQpwOm4zZHYKdDozCnU6azYzFA.01.1e15yvtmp
```

### 3. nginx conf 파일 생성 /home/gitlab-runner/i13e102.p.ssafy.io.conf

```Plain Text
server {
        listen 443 ssl;
        server_name i13e102.p.ssafy.io;

        ssl_certificate /etc/letsencrypt/live/i13e102.p.ssafy.io/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/i13e102.p.ssafy.io/privkey.pem;

        location / {
                proxy_pass http://localhost:5173;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $schema;
        }
}
server {
        listen 80;
        server_name i13e102.p.ssafy.io;
        return 301 https://$host$request_uri;
}
```

### 4. gitlab-runner 의 홈디렉터리에 .env 파일 생성

```Plain Text
SECRET_KEY='django-insecure-kxf+#3en!ta!hk#!pu2@ke!96)4kw5ez-r)9rhl(u2*n4ctic!'

DB_NAME=alpaca_car
DB_USER=E102
DB_PASSWORD=E102
DB_HOST=i13e102.p.ssafy.io
DB_PORT=3306
VAPID_PUBLIC_KEY=BKAyFkRk32KxeaF010jLccB0I16OmwD8_Ug0q3kA2lJRbtrccndnHyt7SKgN7aFEG6U5vhxOkXgSOoLV0w2RWzo
VAPID_PRIVATE_KEY=lRWK3qbuVWYx7FP6_WuBMGlyRAYrpNQgatnsyMqNPHc
VAPID_CLAIM_SUB=mailto:admin@example.com
GOOGLE_CLIENT_ID=397483208541-9s0evi1barg541jekfe3jp36e6b17549.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
SMTP_USER=jun3021303
SMTP_PASS=3N1S2EZYJTPB
SMTP_DEFAULT_FROM_EMAIL=jun3021303@naver.com

DJANGO_ALLOWED_HOSTS=i13e102.p.ssafy.io
VITE_BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api
VITE_FRONTEND_BASE_URL=https://i13e102.p.ssafy.io

FRONTEND_BASE_URL=https://i13e102.p.ssafy.io
BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api
```

### 5. 서버 실행

```bash
# 소스 디렉터리에서 실행
docker-compose build | tee docker_build.log
docker-compose up -d --force-recreate
docker system prune -af --volumes
```

## DB 접속 방법

현재 DB는 외부에서 바로 접속할 수 없게 설정되어있습니다.
SSH 터널링과 docker 를 통해서 CLI 기반으로만 접근가능합니다.

```bash
ssh -i I13E102T.pem ubuntu@i13e102.p.ssafy.io # EC2 접속
sudo -s # 계정 전환
docker ps -a # DB 컨테이너 확인
docker exec -it [DB 컨테이너 ID] bash # DB 컨테이너 접속
mysql -u E102 -pE102 # DB 접속
```
