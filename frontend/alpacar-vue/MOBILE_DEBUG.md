# 모바일 로컬 환경 접속 가이드

## 문제 상황
모바일에서 로컬 개발 서버에 접속할 때 `localhost`나 `127.0.0.1`로는 접근할 수 없습니다.

## 해결 방법

### 1. 컴퓨터의 실제 IP 주소 확인
Windows 명령프롬프트에서 다음 명령어 실행:
```bash
ipconfig
```

또는 PowerShell에서:
```bash
Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi" | Select-Object IPAddress
```

일반적으로 `192.168.x.x` 형태의 IP 주소를 찾습니다.

### 2. 환경 변수 설정
`.env.development` 파일에서 IP 주소를 실제 값으로 변경:

```env
# 예시: 192.168.0.100이 컴퓨터 IP인 경우
VITE_BACKEND_BASE_URL=http://192.168.0.100:8000/api
VITE_FRONTEND_BASE_URL=http://192.168.0.100:5173/
```

### 3. 개발 서버 설정
Vue 개발 서버를 모든 IP에서 접근 가능하도록 설정:

```bash
npm run dev -- --host 0.0.0.0
```

또는 `vite.config.ts`에서:
```typescript
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5173
  }
})
```

### 4. 백엔드 서버 설정
Django 개발 서버도 모든 IP에서 접근 가능하도록 설정:

```bash
python manage.py runserver 0.0.0.0:8000
```

그리고 `settings.py`에서:
```python
ALLOWED_HOSTS = ['*']  # 개발 환경에서만 사용
```

### 5. 방화벽 설정
Windows 방화벽에서 포트 5173과 8000을 허용해야 할 수 있습니다.

## 디버깅 도구

모바일에서 로그인 페이지에 접속하면 "디버그 정보" 버튼이 표시됩니다.
이를 통해 다음 정보를 확인할 수 있습니다:

- 현재 접속 URL
- Backend API URL
- User Agent (모바일 기기 정보)
- 네트워크 상태
- 서버 연결 테스트

## 일반적인 문제 해결

### 1. "네트워크 연결 실패" 오류
- 컴퓨터와 모바일이 같은 Wi-Fi 네트워크에 연결되어 있는지 확인
- IP 주소가 올바른지 확인
- 방화벽 설정 확인

### 2. CORS 오류
- 백엔드에서 CORS 설정이 올바른지 확인
- Django의 경우 `django-cors-headers` 패키지 설정 확인

### 3. "서버 오류" 응답
- 백엔드 서버가 실행 중인지 확인
- 백엔드 로그 확인

## 브라우저 개발자 도구 사용 (모바일)

### Android Chrome
1. Chrome에서 `chrome://inspect` 접속
2. USB 디버깅 활성화 후 기기 연결
3. 원격 디버깅 사용

### iOS Safari
1. 설정 > Safari > 고급 > 웹 검사기 활성화
2. Mac의 Safari에서 개발 메뉴 > 기기명 > 웹페이지 선택

이를 통해 모바일에서도 콘솔 로그와 네트워크 탭을 확인할 수 있습니다.