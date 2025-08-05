# 모바일 로그인 트러블슈팅 가이드

## 🚨 문제 상황

**증상**: 
- 웹 브라우저에서는 로그인이 정상 작동
- 모바일 환경에서 로그인 시도 시 실패
- 배포 환경에서 웹/모바일 모두 로그인 실패

**에러 메시지**:
```
POST https://i13e102.p.ssafy.io/undefined/auth/login/ 405 (Not Allowed)
로그인 실패: Error: 로그인 실패 (405)
```

## 🔍 원인 분석

### 1차 문제: Mixed Content 보안 정책
- **원인**: HTTPS 배포 환경에서 HTTP 로컬 서버로 연결 시도
- **증상**: `보안 정책으로 인한 연결 실패: HTTPS 서버에 HTTP에서 연결할 수 없습니다`
- **영향**: 특히 모바일 브라우저에서 Mixed Content 정책이 엄격하게 적용됨

### 2차 문제: 환경변수 로딩 실패  
- **원인**: `BACKEND_BASE_URL`이 `undefined`로 설정됨
- **증상**: URL이 `https://i13e102.p.ssafy.io/undefined/auth/login/`로 생성
- **영향**: 모든 환경에서 로그인 실패

## 🛠️ 해결 과정

### 1단계: Mixed Content 문제 진단
#### 문제 발견
- 모바일에서만 로그인 실패
- HTTP 로컬 서버 설정 시 문제 발생
- Mixed Content 보안 정책으로 인한 차단

#### 해결 방법
```typescript
// .env.development 설정
VITE_BACKEND_BASE_URL=http://192.168.137.1:8000/api  // 로컬 테스트용
VITE_FRONTEND_BASE_URL=http://192.168.137.1:5173

// .env.production 설정  
VITE_BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api  // 배포용
VITE_FRONTEND_BASE_URL=https://i13e102.p.ssafy.io
```

#### 검증 과정
- 모바일 디버그 인터페이스 구현
- 실시간 프로토콜 상태 확인
- URL 동적 변경 기능 추가

### 2단계: 환경변수 문제 해결
#### 문제 발견
```javascript
// 문제가 된 코드
export const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL;
// → undefined가 될 수 있음
```

#### 해결 방법
```javascript
// api.ts 수정
export const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL || "https://i13e102.p.ssafy.io/api";
export const FRONTEND_BASE_URL = import.meta.env.VITE_FRONTEND_BASE_URL || "https://i13e102.p.ssafy.io";
```

```typescript
// Login.vue 수정
const handleLogin = async () => {
  try {
    const userStore = useUserStore();
    // 복잡한 loginWithUrl 대신 기본 login 함수 사용
    await userStore.login(email.value, password.value);
    router.push("/main");
  } catch (err: any) {
    console.error("로그인 실패:", err);
    alert("로그인 실패: " + err.message);
  }
};
```

### 3단계: 코드 최적화
#### 불필요한 코드 제거
- 복잡한 모바일 디버그 UI 제거
- 중복된 `loginWithUrl` 함수 정리
- 과도한 디버그 로그 제거

#### 환경별 설정 정리
```bash
# 기본 환경 (.env)
VITE_BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api
VITE_FRONTEND_BASE_URL=https://i13e102.p.ssafy.io

# 개발 환경 (.env.development) 
VITE_BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api
VITE_FRONTEND_BASE_URL=https://i13e102.p.ssafy.io

# 배포 환경 (.env.production)
VITE_BACKEND_BASE_URL=https://i13e102.p.ssafy.io/api
VITE_FRONTEND_BASE_URL=https://i13e102.p.ssafy.io
```

## ✅ 최종 해결책

### 핵심 변경사항
1. **환경변수 Fallback 추가**: `undefined` 방지
2. **로그인 함수 통합**: 복잡한 로직 제거  
3. **환경 설정 표준화**: 모든 환경에서 HTTPS 사용

### 테스트 결과
- ✅ 웹 브라우저 로그인 정상
- ✅ 모바일 브라우저 로그인 정상
- ✅ 배포 환경 정상 작동
- ✅ 개발 환경 정상 작동

## 🚀 예방 방법

### 1. 환경변수 안전성 확보
```typescript
// 항상 fallback 값 제공
export const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL || "기본값";
```

### 2. 프로토콜 일관성 유지
- 개발환경과 배포환경 모두 HTTPS 사용
- Mixed Content 문제 원천 차단

### 3. 모바일 테스트 필수
- 개발 중 정기적인 모바일 테스트
- 다양한 모바일 브라우저 호환성 확인

### 4. 환경별 설정 검증
```javascript
// 환경변수 로딩 확인
console.log('Environment:', import.meta.env.MODE);
console.log('Backend URL:', import.meta.env.VITE_BACKEND_BASE_URL);
```

## 📋 체크리스트

### 개발 시 확인사항
- [ ] 환경변수에 fallback 값 설정
- [ ] 모바일 환경에서 테스트
- [ ] HTTPS/HTTP 프로토콜 일관성 확인
- [ ] 빌드 후 환경변수 적용 여부 확인

### 배포 시 확인사항  
- [ ] `.env.production` 파일 설정
- [ ] 빌드된 파일에서 환경변수 확인
- [ ] 웹/모바일 양쪽 환경에서 테스트
- [ ] 네트워크 탭에서 실제 요청 URL 확인

## 🔧 디버깅 도구

### 브라우저 개발자 도구
```javascript
// 콘솔에서 환경변수 확인
console.log('BACKEND_BASE_URL:', BACKEND_BASE_URL);
console.log('Environment:', import.meta.env);
```

### 네트워크 탭
- 실제 요청 URL 확인
- 요청 헤더 및 응답 확인
- CORS 에러 여부 확인

### 모바일 디버깅
- Chrome DevTools → Device Mode
- 실제 모바일 기기에서 테스트
- Safari/Chrome 모바일 브라우저 각각 테스트

---

**작성일**: 2025-08-05  
**해결된 이슈**: 모바일 로그인 실패 문제  
**관련 파일**: 
- `src/utils/api.ts`
- `src/views/user/Login.vue`  
- `src/stores/user.ts`
- `.env`, `.env.development`, `.env.production`