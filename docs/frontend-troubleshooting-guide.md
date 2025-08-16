# 프론트엔드 트러블슈팅 가이드

## 📋 목차
1. [PWA 서비스 워커 문제 해결](#1-pwa-서비스-워커-문제-해결)
2. [localStorage 보안 문제 해결](#2-localstorage-보안-문제-해결)
3. [Input 태그 무제한 입력 문제 해결](#3-input-태그-무제한-입력-문제-해결)

---

## 1. PWA 서비스 워커 문제 해결

### 1.1 문제 상황
- 서비스 워커 등록 실패
- 푸시 알림 구독 오류
- 브라우저별 호환성 문제
- VAPID 키 설정 오류

### 1.2 해결 방법

**서비스 워커 등록 로직 강화:**
```javascript
// utils/pwa.ts
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  console.log('🔧 === Service Worker 등록 프로세스 시작 ===');
  
  if (!('serviceWorker' in navigator)) {
    console.warn('⚠️ Service Worker가 지원되지 않는 브라우저입니다.');
    return null;
  }
  
  try {
    // 기존 등록 확인 및 해제
    const registrations = await navigator.serviceWorker.getRegistrations();
    for (const registration of registrations) {
      console.log('🗑️ 기존 Service Worker 해제:', registration.scope);
      await registration.unregister();
    }
    
    // 새로운 서비스 워커 등록
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
      updateViaCache: 'none'
    });
    
    console.log('✅ Service Worker 등록 성공:', registration.scope);
    
    // 업데이트 확인
    registration.addEventListener('updatefound', () => {
      console.log('🔄 Service Worker 업데이트 발견');
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed') {
            console.log('🎉 새로운 Service Worker 설치 완료');
          }
        });
      }
    });
    
    return registration;
  } catch (error) {
    console.error('❌ Service Worker 등록 실패:', error);
    return null;
  }
}
```

**푸시 알림 구독 강화:**
```javascript
export async function subscribeToPushNotifications(registration: ServiceWorkerRegistration): Promise<PushSubscription | null> {
  console.log('🔔 === 푸시 알림 구독 프로세스 시작 ===');
  
  try {
    // 권한 확인
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.warn('⚠️ 푸시 알림 권한이 거부되었습니다.');
      return null;
    }
    
    // VAPID 키 가져오기 (다중 소스)
    const vapidKey = await getVapidKey();
    if (!vapidKey) {
      console.error('❌ VAPID 키를 가져올 수 없습니다.');
      return null;
    }
    
    // 푸시 구독
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey)
    });
    
    console.log('✅ 푸시 알림 구독 성공');
    return subscription;
  } catch (error) {
    console.error('❌ 푸시 알림 구독 실패:', error);
    return null;
  }
}
```

**VAPID 키 다중 소스 관리:**
```javascript
async function getVapidKey(): Promise<string | null> {
  // 1. 환경 변수에서 가져오기
  const envKey = import.meta.env.VITE_VAPID_PUBLIC_KEY;
  if (envKey) {
    console.log('🔑 환경 변수에서 VAPID 키 로드');
    return envKey;
  }
  
  // 2. API에서 가져오기
  try {
    const response = await fetch('/api/vapid-key/');
    if (response.ok) {
      const data = await response.json();
      console.log('🔑 API에서 VAPID 키 로드');
      return data.vapid_key;
    }
  } catch (error) {
    console.warn('⚠️ API에서 VAPID 키 로드 실패:', error);
  }
  
  // 3. 하드코딩된 폴백 키 (개발용)
  const fallbackKey = 'BH7hZ9...'; // 실제 키로 교체
  console.log('🔑 폴백 VAPID 키 사용');
  return fallbackKey;
}
```

**브라우저별 호환성 처리:**
```javascript
function getBrowserType(): string {
  const userAgent = navigator.userAgent;
  if (userAgent.includes('Chrome')) return 'chrome';
  if (userAgent.includes('Firefox')) return 'firefox';
  if (userAgent.includes('Safari')) return 'safari';
  if (userAgent.includes('Edge')) return 'edge';
  return 'unknown';
}

export async function initializePWA(): Promise<void> {
  const browser = getBrowserType();
  console.log(`🌐 브라우저 감지: ${browser}`);
  
  // 브라우저별 특별 처리
  if (browser === 'safari') {
    // Safari는 iOS 16.4 이후부터 푸시 알림 지원
    const isSupported = 'PushManager' in window;
    if (!isSupported) {
      console.warn('⚠️ Safari에서 푸시 알림이 지원되지 않습니다.');
      return;
    }
  }
  
  const registration = await registerServiceWorker();
  if (registration) {
    await subscribeToPushNotifications(registration);
  }
}
```

### 1.3 디버깅 팁

**Service Worker 상태 확인:**
```javascript
// 개발자 도구에서 실행
navigator.serviceWorker.getRegistrations().then(registrations => {
  console.log('등록된 Service Worker:', registrations);
  registrations.forEach(reg => {
    console.log('Scope:', reg.scope);
    console.log('State:', reg.active?.state);
  });
});
```

---

## 2. localStorage 보안 문제 해결

### 2.1 문제 상황
- 민감한 정보(이메일, 전화번호, 토큰)가 평문으로 localStorage에 저장
- XSS 공격에 취약한 데이터 노출
- 토큰 탈취 위험

### 2.2 해결 방법

**SecureTokenManager 구현:**
```javascript
// utils/security.ts
export class SecureTokenManager {
  public static readonly TOKEN_PREFIX = 'secure_';
  
  // 보안 토큰 저장
  static setSecureToken(key: string, token: string, useSession: boolean = false): void {
    try {
      const encryptedToken = encryptToken(token);
      const storage = useSession ? sessionStorage : localStorage;
      storage.setItem(this.TOKEN_PREFIX + key, encryptedToken);
    } catch (error) {
      console.error('Secure token storage failed:', error);
      throw error;
    }
  }
  
  // 보안 토큰 조회
  static getSecureToken(key: string): string | null {
    try {
      // sessionStorage 우선 확인
      let encryptedToken = sessionStorage.getItem(this.TOKEN_PREFIX + key);
      if (!encryptedToken) {
        // localStorage 확인
        encryptedToken = localStorage.getItem(this.TOKEN_PREFIX + key);
      }
      
      if (!encryptedToken) {
        return null;
      }
      
      return decryptToken(encryptedToken);
    } catch (error) {
      console.warn('Secure token retrieval failed:', error);
      return null;
    }
  }
  
  // 모든 보안 토큰 제거
  static clearAllSecureTokens(): void {
    this.removeSecureToken('access_token');
    this.removeSecureToken('refresh_token');
    localStorage.removeItem('auto_login_expiry');
    localStorage.removeItem('secure_user_data');
    localStorage.removeItem('user'); // 기존 평문 사용자 정보 제거
  }
}
```

**디바이스 지문 기반 암호화:**
```javascript
// 브라우저 지문 기반 키 생성
function generateDeviceKey(): string {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx!.textBaseline = 'top';
  ctx!.font = '14px Arial';
  ctx!.fillText('Device fingerprint', 2, 2);
  
  const fingerprint = [
    navigator.userAgent,
    navigator.language,
    screen.width + 'x' + screen.height,
    new Date().getTimezoneOffset(),
    canvas.toDataURL()
  ].join('|');
  
  return CryptoJS.SHA256(fingerprint).toString();
}

// 토큰 암호화
function encryptToken(token: string): string {
  try {
    const deviceKey = generateDeviceKey();
    const sessionKey = CryptoJS.lib.WordArray.random(256/8).toString();
    const combinedKey = CryptoJS.SHA256(deviceKey + sessionKey).toString().substr(0, 32);
    
    const encrypted = CryptoJS.AES.encrypt(token, combinedKey).toString();
    
    // sessionKey와 encrypted를 결합하여 저장
    return `${sessionKey}:${encrypted}`;
  } catch (error) {
    console.error('Token encryption failed:', error);
    throw new Error('암호화 실패');
  }
}
```

**민감정보 검증 및 최소화:**
```javascript
// 민감정보 패턴 검증
export function encryptUserData(user: any): string {
  try {
    // 🔒 암호화 전 민감정보 검증
    const userString = JSON.stringify(user);
    const sensitivePatterns = [
      /@[\w.-]+\.[a-zA-Z]{2,}/, // 이메일 패턴
      /\b\d{3}[-.]?\d{3,4}[-.]?\d{4}\b/, // 전화번호 패턴
      /"(?:email|name|full_name|phone|password)"\s*:/ // 민감정보 키 패턴
    ];
    
    for (const pattern of sensitivePatterns) {
      if (pattern.test(userString)) {
        console.warn('🚨 [SECURITY] 민감정보가 암호화 대상에 포함됨:', userString.substring(0, 100));
        break;
      }
    }
    
    const deviceKey = generateDeviceKey();
    const sessionKey = CryptoJS.lib.WordArray.random(256/8).toString();
    const combinedKey = CryptoJS.SHA256(deviceKey + sessionKey).toString().substr(0, 32);
    
    const encrypted = CryptoJS.AES.encrypt(userString, combinedKey).toString();
    return `${sessionKey}:${encrypted}`;
  } catch (error) {
    console.error('User data encryption failed:', error);
    throw new Error('사용자 정보 암호화 실패');
  }
}

// 최소 데이터만 저장
extractMinimalData(userData: any): any {
  const allowedKeys = ['nickname', 'is_staff', 'push_on', 'score', 'is_social_user'];
  const minimalData: any = {};
  
  allowedKeys.forEach(key => {
    if (userData && userData.hasOwnProperty(key)) {
      minimalData[key] = userData[key];
    }
  });
  
  return minimalData;
}
```

### 2.3 마이그레이션 가이드

**기존 평문 데이터를 암호화로 전환:**
```javascript
// stores/user.ts
migrateToSecureStorage() {
  try {
    // 기존 평문 토큰 확인
    const oldToken = localStorage.getItem('access_token');
    if (oldToken) {
      console.log('🔄 기존 토큰을 암호화 저장소로 마이그레이션');
      SecureTokenManager.setSecureToken('access_token', oldToken);
      localStorage.removeItem('access_token');
    }
    
    // 기존 사용자 정보 확인
    const oldUser = localStorage.getItem('user');
    if (oldUser) {
      console.log('🔄 기존 사용자 정보를 최소화하여 저장');
      const userData = JSON.parse(oldUser);
      const minimalData = this.extractMinimalData(userData);
      localStorage.setItem('user', JSON.stringify(minimalData));
    }
  } catch (error) {
    console.error('마이그레이션 실패:', error);
  }
}
```

---

## 3. Input 태그 무제한 입력 문제 해결

### 3.1 문제 상황
- 차량번호 입력 시 길이 제한 없음
- 특수문자, 숫자만 입력 등 검증 누락
- 이름 입력 시 길이 및 문자 종류 제한 없음
- 실시간 유효성 검사 부재

### 3.2 해결 방법

**차량번호 입력 제한:**
```javascript
// 한국 차량번호 패턴 정의
const KOREAN_PLATE_CHARS = "가나다라마거너더러머버서어저고노도로모보소오조구누두루무부수우주아바사자허하호배";
const plateRegex = new RegExp(
  `^(?:0[1-9]|[1-9]\\d|[1-9]\\d{2})` +  // 숫자 부분 (01-999)
  `[${KOREAN_PLATE_CHARS}]` +              // 한글 1자 (지정된 문자만)
  `[1-9]\\d{3}$`                          // 숫자 4자리 (1000-9999)
);

// 실시간 입력 필터링
const handleVehicleNumberInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const value = target.value;
  
  // 1. 허용되지 않는 문자 제거
  const cleanValue = value.replace(/[^0-9ㄱ-ㅎㅏ-ㅣ가-힣]/g, "");
  
  // 2. 최대 길이 제한 (8자리)
  const limitedValue = cleanValue.slice(0, 8);
  
  // 3. 값 업데이트
  vehicleNumber.value = limitedValue;
  target.value = limitedValue;
};

// 키보드 입력 제한
const preventInvalidVehicleChars = (e: KeyboardEvent) => {
  const char = e.key;
  const allowedKeys = ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'];
  
  // 허용된 문자가 아니고 제어 키도 아닌 경우 입력 차단
  if (!/[0-9ㄱ-ㅎㅏ-ㅣ가-힣]/.test(char) && !allowedKeys.includes(char)) {
    e.preventDefault();
  }
};
```

**Vue 템플릿 적용:**
```vue
<template>
  <input
    v-model="vehicleNumber"
    type="text"
    placeholder="차량번호 입력 (예: 12가3456)"
    maxlength="8"
    @input="handleVehicleNumberInput"
    @keydown="preventInvalidVehicleChars"
    :class="{ 
      'valid': vehicleNumberValid, 
      'invalid': vehicleNumber && !vehicleNumberValid 
    }"
  />
</template>
```

**이름 입력 제한:**
```javascript
// 이름 입력 검증
const nameValid = computed(() => {
  const koreanEnglishOnly = /^[a-zA-Z가-힣]+$/.test(formData.full_name);
  return formData.full_name.length > 0 && 
         formData.full_name.length <= 18 && 
         koreanEnglishOnly;
});

// 이름 입력 필터링
const handleNameInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const value = target.value;
  
  // 한글, 영문만 허용하고 길이 제한
  const cleanValue = value.replace(/[^a-zA-Z가-힣]/g, "").slice(0, 18);
  formData.full_name = cleanValue;
  target.value = cleanValue;
};

// 키보드 입력 차단
const preventInvalidNameChars = (e: KeyboardEvent) => {
  const char = e.key;
  if (!/[a-zA-Z가-힣]/.test(char) && 
      !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab'].includes(char)) {
    e.preventDefault();
  }
};
```

**범용 입력 제한 컴포저블:**
```javascript
// composables/useInputValidation.ts
export function useInputValidation() {
  // 한국 전화번호 패턴
  const phoneRegex = /^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$/;
  
  // 이메일 패턴
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  
  // 입력 제한 함수 생성기
  const createInputRestrictor = (
    pattern: RegExp, 
    maxLength: number, 
    allowedKeys: string[] = ['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab']
  ) => {
    return {
      handleInput: (event: Event) => {
        const target = event.target as HTMLInputElement;
        const value = target.value.slice(0, maxLength);
        target.value = value;
      },
      
      handleKeydown: (event: KeyboardEvent) => {
        const char = event.key;
        if (!pattern.test(char) && !allowedKeys.includes(char)) {
          event.preventDefault();
        }
      },
      
      validate: (value: string) => pattern.test(value) && value.length <= maxLength
    };
  };
  
  return {
    // 차량번호 검증
    vehicleNumber: createInputRestrictor(/[0-9ㄱ-ㅎㅏ-ㅣ가-힣]/, 8),
    
    // 이름 검증
    name: createInputRestrictor(/[a-zA-Z가-힣]/, 18),
    
    // 전화번호 검증
    phone: createInputRestrictor(/[0-9-]/, 13),
    
    // 범용 검증
    createInputRestrictor
  };
}
```

### 3.3 실시간 검증 UI

**검증 상태 표시:**
```vue
<template>
  <div class="input-group">
    <input
      v-model="vehicleNumber"
      type="text"
      :class="inputClass"
      @input="handleVehicleNumberInput"
      @keydown="preventInvalidVehicleChars"
    />
    <div class="validation-message">
      <span v-if="vehicleNumber && !vehicleNumberValid" class="error">
        올바른 차량번호 형식이 아닙니다 (예: 12가3456)
      </span>
      <span v-else-if="vehicleNumberValid" class="success">
        ✓ 올바른 형식입니다
      </span>
    </div>
  </div>
</template>

<script setup>
const inputClass = computed(() => ({
  'input-valid': vehicleNumber.value && vehicleNumberValid.value,
  'input-invalid': vehicleNumber.value && !vehicleNumberValid.value,
  'input-neutral': !vehicleNumber.value
}));
</script>

<style scoped>
.input-valid {
  border-color: #10b981;
  background-color: #f0fdf4;
}

.input-invalid {
  border-color: #ef4444;
  background-color: #fef2f2;
}

.validation-message .error {
  color: #ef4444;
  font-size: 0.875rem;
}

.validation-message .success {
  color: #10b981;
  font-size: 0.875rem;
}
</style>
```

---

## 🛠️ 종합 체크리스트

### PWA 관련
- [ ] Service Worker 등록 상태 확인
- [ ] 푸시 알림 권한 상태 확인
- [ ] VAPID 키 설정 확인
- [ ] 브라우저 호환성 테스트

### 보안 관련
- [ ] 평문 토큰 → 암호화 토큰 마이그레이션
- [ ] 민감정보 localStorage 저장 제거
- [ ] 최소 사용자 데이터만 저장
- [ ] 디바이스 지문 기반 암호화 적용

### 입력 검증 관련
- [ ] 모든 입력 필드에 길이 제한 적용
- [ ] 문자 종류 제한 적용
- [ ] 실시간 검증 메시지 표시
- [ ] 키보드 입력 차단 적용

---

**마지막 업데이트:** 2025-08-16