# PWA 배포 환경 설정 가이드

## 배포 서버 푸시 알림 문제 해결

### 주요 수정사항

1. **VAPID 키 동적 로딩**:
   - 로컬: 환경 변수 `VITE_VAPID_PUBLIC_KEY` 사용
   - 배포: 서버 응답의 `vapid_public_key` 필드 사용

2. **HTTPS 요구사항 검증**:
   - 배포 환경에서 HTTPS 필수 확인
   - 보안 컨텍스트 검증 추가

3. **사용자 정보 영속화**:
   - localStorage에 사용자 정보 저장
   - PWA utils에서 동적 VAPID 키 접근

### 배포 체크리스트

- [ ] 배포 서버가 HTTPS로 서비스되는지 확인
- [ ] 백엔드 API에서 `vapid_public_key` 필드 반환 확인
- [ ] 푸시 알림 권한 요청 가능한 브라우저 환경 확인
- [ ] Service Worker 등록 성공 여부 확인

### 테스트 방법

```javascript
// 브라우저 콘솔에서 VAPID 키 확인
console.log('환경변수 VAPID:', import.meta.env.VITE_VAPID_PUBLIC_KEY);
const user = JSON.parse(localStorage.getItem('user') || '{}');
console.log('사용자 VAPID:', user.vapid_public_key);
```