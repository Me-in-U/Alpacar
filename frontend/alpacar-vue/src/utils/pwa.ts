// src/utils/pwa.ts - PWA 및 푸시 알림 관리

import { BACKEND_BASE_URL } from './api';
import { SecureTokenManager } from './security';

export interface NotificationSubscription {
  endpoint: string;
  keys: {
    p256dh: string;
    auth: string;
  };
}

export interface PushNotificationData {
  type: 'parking' | 'entry' | 'exit' | 'warning' | 'general';
  title: string;
  body: string;
  data?: any;
  requireInteraction?: boolean;
}

// VAPID 공개 키 - 서버에서 동적으로 가져오거나 환경 변수 사용
let VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY;

// 개발 모드 확인
const isDevelopment = import.meta.env.DEV || import.meta.env.NODE_ENV === 'development';
const isProduction = import.meta.env.PROD || import.meta.env.NODE_ENV === 'production';

console.log('PWA 환경 정보:', {
  isDev: isDevelopment,
  isProd: isProduction,
  hasEnvVapidKey: !!VAPID_PUBLIC_KEY,
  envMode: import.meta.env.MODE
});

// 사용자 스토어에서 VAPID 키 가져오기 함수 (강화된 검색)
function getVapidKeyFromUser(): string | null {
  try {
    console.log('VAPID 키 검색 시작 - 모든 저장소 확인...');
    
    // 1. localStorage에서 암호화된 사용자 데이터 우선 확인
    const encryptedUserData = localStorage.getItem('secure_user_data');
    if (encryptedUserData) {
      try {
        // 복호화 시도 (security.ts의 decryptUserData 사용)
        console.log('암호화된 사용자 데이터 발견, 복호화 시도...');
        // 복호화 로직이 있다면 여기에 추가
        // const decryptedUser = decryptUserData(encryptedUserData);
      } catch (decryptError) {
        console.warn('암호화된 데이터 복호화 실패:', decryptError);
      }
    }
    
    // 2. localStorage와 sessionStorage에서 user 객체 확인 (확장된 검색)
    const storageKeys = ['user', 'secure_user_data', 'user-store'];
    const storageTypes = [localStorage, sessionStorage];
    
    for (const storage of storageTypes) {
      for (const key of storageKeys) {
        const userStr = storage.getItem(key);
        if (userStr) {
          try {
            const user = JSON.parse(userStr);
            console.log(`${storage === localStorage ? 'localStorage' : 'sessionStorage'}에서 ${key} 확인:`, {
              hasVapidKey: !!user.vapid_public_key,
              hasMe: !!user.me,
              userStructure: Object.keys(user)
            });
            
            // 직접 vapid_public_key 확인
            if (user && user.vapid_public_key && typeof user.vapid_public_key === 'string') {
              console.log('VAPID 키 발견:', user.vapid_public_key.substring(0, 10) + '...');
              return user.vapid_public_key;
            }
            
            // Pinia store 구조 확인 (user.me.vapid_public_key)
            if (user && user.me && user.me.vapid_public_key && typeof user.me.vapid_public_key === 'string') {
              console.log('Pinia store에서 VAPID 키 발견:', user.me.vapid_public_key.substring(0, 10) + '...');
              return user.me.vapid_public_key;
            }
          } catch (parseError) {
            console.warn(`${key} 파싱 실패:`, parseError);
          }
        }
      }
    }

    // 3. 액세스 토큰 확인 (서버에서 다시 받아올 필요가 있는지 체크)
    const accessToken = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    console.log('액세스 토큰 상태:', accessToken ? '존재함' : '없음');
    
    console.warn('사용자 정보에서 VAPID 키를 찾을 수 없음 - 재로그인 필요');
  } catch (error) {
    console.error('사용자 정보에서 VAPID 키 추출 중 오류:', error);
  }
  return null;
}

// 백엔드 API에서 VAPID 키 가져오기
async function fetchVapidKeyFromAPI(): Promise<string | null> {
  try {
    console.log('백엔드 API에서 VAPID 키 가져오기 시도...');
    
    const token = SecureTokenManager.getSecureToken('access_token');
    if (!token) {
      console.warn('인증 토큰이 없음 - API 호출 스킨');
      return null;
    }
    
    const response = await fetch(`${BACKEND_BASE_URL}/push/setting/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      console.error(`API 응답 오류: ${response.status}`);
      return null;
    }
    
    const data = await response.json();
    if (data.vapid_public_key && typeof data.vapid_public_key === 'string') {
      console.log('백엔드 API에서 VAPID 키 가져오기 성공:', data.vapid_public_key.substring(0, 10) + '...');
      return data.vapid_public_key;
    }
    
    console.warn('백엔드 API 응답에 VAPID 키가 없음');
    return null;
  } catch (error) {
    console.error('백엔드 API VAPID 키 가져오기 실패:', error);
    return null;
  }
}

// 동적 VAPID 키 가져오기 (개선된 오류 처리)
async function getVapidKey(): Promise<string> {
  console.log('VAPID 키 검색 시작...');
  
  // 1. 환경 변수 우선 사용 (로컬 개발)
  if (VAPID_PUBLIC_KEY && typeof VAPID_PUBLIC_KEY === 'string' && VAPID_PUBLIC_KEY.length > 0) {
    console.log('환경 변수에서 VAPID 키 사용:', VAPID_PUBLIC_KEY.substring(0, 10) + '...');
    return VAPID_PUBLIC_KEY;
  }
  
  // 2. 백엔드 API에서 가져오기 (새로운 방식)
  const apiVapidKey = await fetchVapidKeyFromAPI();
  if (apiVapidKey && typeof apiVapidKey === 'string' && apiVapidKey.length > 0) {
    console.log('백엔드 API에서 VAPID 키 사용:', apiVapidKey.substring(0, 10) + '...');
    return apiVapidKey;
  }
  
  // 3. 사용자 정보에서 가져오기 (기존 방식 - 백업)
  const userVapidKey = getVapidKeyFromUser();
  if (userVapidKey && typeof userVapidKey === 'string' && userVapidKey.length > 0) {
    console.log('사용자 정보에서 VAPID 키 사용:', userVapidKey.substring(0, 10) + '...');
    return userVapidKey;
  }
  
  console.error('VAPID 키를 찾을 수 없음:', {
    envKey: VAPID_PUBLIC_KEY ? `${VAPID_PUBLIC_KEY.substring(0, 10)}...` : 'MISSING',
    apiKey: apiVapidKey ? `${apiVapidKey.substring(0, 10)}...` : 'MISSING',
    userKey: userVapidKey ? `${userVapidKey.substring(0, 10)}...` : 'MISSING',
    isDev: isDevelopment,
    storageCheck: {
      localStorage: !!localStorage.getItem('user'),
      sessionStorage: !!sessionStorage.getItem('user'),
      secureUserData: !!localStorage.getItem('secure_user_data'),
      userStore: !!localStorage.getItem('user-store')
    }
  });
  
  if (isDevelopment) {
    throw new Error('개발 환경에서는 .env 파일에 VITE_VAPID_PUBLIC_KEY를 설정하거나, 백엔드 서버가 정상 동작하고 있는지 확인해 주세요.');
  } else {
    throw new Error('VAPID 키가 설정되지 않았습니다. 다시 로그인해 주세요.');
  }
}

// URL-safe base64를 Uint8Array로 변환
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  // 입력값 검증
  if (!base64String || typeof base64String !== 'string') {
    console.error('urlBase64ToUint8Array: 잘못된 입력값:', base64String);
    throw new Error('VAPID 키 형식이 올바르지 않습니다.');
  }

  if (base64String.length === 0) {
    throw new Error('VAPID 키가 비어있습니다.');
  }

  try {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  } catch (error) {
    console.error('VAPID 키 디코딩 실패:', error);
    throw new Error('VAPID 키 디코딩에 실패했습니다. 관리자에게 문의하세요.');
  }
}

// 푸시 알림 권한 요청
export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) {
    console.warn('이 브라우저는 알림을 지원하지 않습니다.');
    return false;
  }

  // HTTPS 환경 확인 (배포 환경 호환성)
  if (!window.isSecureContext && location.hostname !== 'localhost') {
    console.warn('푸시 알림은 HTTPS 환경에서만 지원됩니다.');
    throw new Error('HTTPS 환경에서 사용해주세요.');
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission === 'denied') {
    console.warn('알림 권한이 거부된 상태입니다.');
    // 크롬에서는 사용자가 직접 설정을 변경해야 하므로 더 상세한 안내 제공
    const userAgent = navigator.userAgent.toLowerCase();
    const isChrome = userAgent.includes('chrome') && !userAgent.includes('edg');
    
    if (isChrome) {
      throw new Error('크롬 브라우저에서 알림이 차단되어 있습니다.\n\n해결 방법:\n1. 주소창 왼쪽의 🔒 또는 🛡️ 아이콘을 클릭\n2. "알림" 설정을 "허용"으로 변경\n3. 페이지를 새로고침 후 다시 시도해주세요.');
    } else {
      throw new Error('알림 권한이 거부되었습니다. 브라우저 설정에서 알림을 허용해주세요.');
    }
  }

  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      throw new Error('알림 권한을 허용해주세요.');
    }
    return true;
  } catch (error) {
    // 권한 요청 자체가 실패한 경우 (이미 거부된 상태에서 재요청 시)
    console.error('알림 권한 요청 실패:', error);
    throw new Error('알림 권한 요청에 실패했습니다. 브라우저 설정에서 직접 허용해주세요.');
  }
}

// Service Worker 등록
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  console.log('🔧 === Service Worker 등록 프로세스 시작 ===');
  
  if (!('serviceWorker' in navigator)) {
    console.error('❌ Service Worker가 지원되지 않는 브라우저');
    return null;
  }

  // 환경 확인
  console.log('🌐 환경 확인:', {
    isSecureContext: window.isSecureContext,
    protocol: location.protocol,
    hostname: location.hostname,
    pathname: location.pathname
  });

  // 네트워크 IP 접속 시 HTTPS가 아닌 경우 경고
  if (!window.isSecureContext && location.hostname !== 'localhost') {
    console.warn('⚠️ PWA는 HTTPS 또는 localhost에서만 완전히 지원됩니다. 일부 기능이 제한될 수 있습니다.');
  }

  try {
    // 기존 등록 확인
    console.log('🔍 기존 Service Worker 등록 확인...');
    let existingRegistration;
    try {
      existingRegistration = await navigator.serviceWorker.getRegistration();
      console.log('기존 등록 조회 결과:', existingRegistration ? '발견됨' : '없음');
    } catch (getRegError) {
      console.error('❌ 기존 등록 조회 실패:', getRegError);
      existingRegistration = null;
    }

    if (existingRegistration) {
      console.log('📄 기존 Service Worker 등록 정보:', {
        scope: existingRegistration.scope,
        installing: !!existingRegistration.installing,
        waiting: !!existingRegistration.waiting,
        active: !!existingRegistration.active,
        updateViaCache: existingRegistration.updateViaCache
      });
      
      // 등록이 유효한지 확인
      if (existingRegistration.active) {
        console.log('✅ 활성 Service Worker 확인됨, 재사용');
        return existingRegistration;
      } else {
        console.log('⚠️ Service Worker가 활성 상태가 아님, 새로 등록 시도');
      }
    } else {
      console.log('ℹ️ 기존 Service Worker 등록이 없음');
    }

    console.log('🆕 새 Service Worker 등록 시도...');
    console.log('등록 설정:', {
      scriptURL: '/service-worker.js',
      scope: '/',
      type: 'classic'
    });

    let registration: ServiceWorkerRegistration;
    try {
      registration = await navigator.serviceWorker.register('/service-worker.js', {
        scope: '/'
      });
      console.log('🎉 Service Worker 등록 성공!');
    } catch (registerError) {
      console.error('❌ Service Worker 등록 중 오류:', {
        error: registerError,
        name: registerError instanceof Error ? registerError.name : 'Unknown',
        message: registerError instanceof Error ? registerError.message : String(registerError)
      });
      throw registerError;
    }
    
    console.log('📊 등록된 Service Worker 정보:', {
      scope: registration.scope,
      installing: !!registration.installing,
      waiting: !!registration.waiting,
      active: !!registration.active,
      updateViaCache: registration.updateViaCache
    });
    
    // Service Worker 상태 확인
    if (registration.installing) {
      console.log('⏳ Service Worker 설치 중...');
    } else if (registration.waiting) {
      console.log('⏳ Service Worker 대기 중...');
    } else if (registration.active) {
      console.log('✅ Service Worker 즉시 활성화됨');
    }
    
    // Service Worker 업데이트 감지
    registration.addEventListener('updatefound', () => {
      console.log('🔄 새로운 Service Worker 발견');
      const newWorker = registration.installing;
      if (newWorker) {
        console.log('새 워커 상태:', newWorker.state);
        newWorker.addEventListener('statechange', () => {
          console.log('🔄 Service Worker 상태 변경:', newWorker.state);
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            console.log('✅ 새로운 Service Worker 설치됨');
          }
        });
      }
    });

    return registration;
  } catch (error) {
    console.error('❌ Service Worker 등록 실패:', {
      error: error,
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    });
    
    if (error instanceof Error) {
      if (error.message.includes('unsupported')) {
        console.error('💡 Service Worker가 지원되지 않는 환경');
      } else if (error.message.includes('network')) {
        console.error('💡 네트워크 오류로 Service Worker 등록 실패');
      } else if (error.message.includes('script')) {
        console.error('💡 Service Worker 스크립트 파일을 찾을 수 없음');
      }
    }
    return null;
  }
}

// 푸시 알림 구독
export async function subscribeToPushNotifications(): Promise<PushSubscription | null> {
  console.log('=== 푸시 알림 구독 시작 ===');
  
  // 브라우저 환경 상세 확인
  console.log('브라우저 환경 확인:', {
    userAgent: navigator.userAgent,
    serviceWorkerSupport: 'serviceWorker' in navigator,
    pushManagerSupport: 'PushManager' in window,
    notificationSupport: 'Notification' in window,
    isSecureContext: window.isSecureContext,
    protocol: location.protocol,
    hostname: location.hostname
  });

  // 브라우저 지원 확인
  if (!('serviceWorker' in navigator)) {
    console.error('❌ Service Worker가 지원되지 않음');
    throw new Error('이 브라우저는 Service Worker를 지원하지 않습니다.');
  }
  
  if (!('PushManager' in window)) {
    console.error('❌ Push Manager가 지원되지 않음');
    throw new Error('이 브라우저는 Push Manager를 지원하지 않습니다.');
  }

  console.log('✅ 브라우저 기본 지원 확인 완료');

  // 동적 VAPID 키 가져오기 (개선된 오류 처리)
  let vapidKey: string;
  try {
    console.log('🔑 VAPID 키 가져오기 시도...');
    vapidKey = await getVapidKey();
    console.log('✅ VAPID 키 확인 성공:', {
      length: vapidKey.length,
      prefix: vapidKey.substring(0, 10) + '...',
      type: typeof vapidKey
    });
  } catch (error) {
    console.error('❌ VAPID 키 가져오기 실패:', error);
    
    // 사용자 친화적 오류 메시지 제공
    const errorMessage = error instanceof Error ? error.message : String(error);
    if (errorMessage.includes('로그인')) {
      throw new Error('로그인 세션이 만료되었습니다. 다시 로그인해 주세요.');
    } else if (errorMessage.includes('설정')) {
      throw new Error('서버 설정에 문제가 있습니다. 잠시 후 다시 시도하거나 관리자에게 문의하세요.');
    } else {
      throw new Error('푸시 알림 설정에 실패했습니다. 페이지를 새로고침 후 다시 시도해주세요.');
    }
  }

  // Service Worker 등록 확인
  console.log('🔧 Service Worker 등록 확인 중...');
  const registration = await registerServiceWorker();
  if (!registration) {
    console.error('❌ Service Worker 등록 실패');
    throw new Error('Service Worker 등록에 실패했습니다. HTTPS 환경인지 확인해주세요.');
  }
  
  console.log('✅ Service Worker 등록 성공:', {
    scope: registration.scope,
    installing: !!registration.installing,
    waiting: !!registration.waiting,
    active: !!registration.active
  });

  // Service Worker가 active 상태가 될 때까지 대기
  if (registration.installing) {
    console.log('⏳ Service Worker 설치 중... 대기');
    await new Promise((resolve) => {
      registration.installing!.addEventListener('statechange', function() {
        console.log('🔄 Service Worker 상태 변경:', this.state);
        if (this.state === 'activated') {
          console.log('✅ Service Worker 활성화 완료');
          resolve(true);
        }
      });
    });
  } else if (registration.active) {
    console.log('✅ Service Worker 이미 활성 상태');
  } else if (registration.waiting) {
    console.log('⏳ Service Worker 대기 중...');
  }

  // 알림 권한 확인
  console.log('🔔 알림 권한 확인 중...');
  console.log('현재 알림 권한 상태:', Notification.permission);
  
  const hasPermission = await requestNotificationPermission();
  if (!hasPermission) {
    console.error('❌ 알림 권한 거부됨');
    throw new Error('알림 권한이 거부되었습니다.');
  }
  
  console.log('✅ 알림 권한 확인 완료');

  try {
    console.log('📋 푸시 구독 과정 시작...');
    
    // PushManager 지원 확인
    console.log('🔍 PushManager 지원 확인...');
    if (!registration.pushManager) {
      console.error('❌ PushManager가 등록에서 지원되지 않음');
      throw new Error('이 브라우저는 Push Manager를 지원하지 않습니다.');
    }
    console.log('✅ PushManager 지원 확인됨');

    // 기존 구독 확인
    console.log('🔍 기존 구독 확인 중...');
    let existingSubscription;
    try {
      existingSubscription = await registration.pushManager.getSubscription();
      console.log('기존 구독 조회 결과:', existingSubscription ? '발견됨' : '없음');
    } catch (getSubError) {
      console.error('❌ 기존 구독 조회 실패:', getSubError);
      existingSubscription = null;
    }

    if (existingSubscription) {
      console.log('📄 기존 구독 정보:', {
        endpoint: existingSubscription.endpoint,
        expirationTime: existingSubscription.expirationTime,
        p256dh: existingSubscription.getKey('p256dh') ? 'OK' : 'MISSING',
        auth: existingSubscription.getKey('auth') ? 'OK' : 'MISSING'
      });
      
      // 기존 구독이 유효한지 확인
      console.log('🔍 기존 구독 서버 검증 시도...');
      try {
        const serverSuccess = await sendSubscriptionToServer(existingSubscription);
        if (serverSuccess) {
          console.log('✅ 기존 구독 재사용 성공');
          return existingSubscription;
        } else {
          console.log('⚠️ 기존 구독이 서버에서 거부됨, 새 구독 생성 필요');
          try {
            await existingSubscription.unsubscribe();
            console.log('✅ 기존 구독 해제 완료');
          } catch (unsubError) {
            console.error('⚠️ 기존 구독 해제 실패:', unsubError);
          }
        }
      } catch (serverError) {
        console.error('❌ 기존 구독 서버 확인 실패:', serverError);
        try {
          await existingSubscription.unsubscribe();
          console.log('✅ 기존 구독 해제 완료 (서버 오류로 인한)');
        } catch (unsubError) {
          console.error('⚠️ 기존 구독 해제 실패:', unsubError);
        }
      }
    } else {
      console.log('ℹ️ 기존 구독이 없음, 새 구독 생성 진행');
    }

    // VAPID 키 변환
    console.log('🔑 VAPID 키 변환 시도...');
    let applicationServerKey: Uint8Array;
    try {
      applicationServerKey = urlBase64ToUint8Array(vapidKey);
      console.log('✅ VAPID 키 변환 성공:', {
        originalLength: vapidKey.length,
        convertedLength: applicationServerKey.length,
        expectedLength: 65, // VAPID 키는 65바이트여야 함
        isValidLength: applicationServerKey.length === 65
      });
      
      if (applicationServerKey.length !== 65) {
        console.error('❌ VAPID 키 길이가 올바르지 않음');
        throw new Error(`VAPID 키 길이 오류: ${applicationServerKey.length} (예상: 65)`);
      }
    } catch (keyError) {
      console.error('❌ VAPID 키 변환 실패:', keyError);
      throw new Error('VAPID 키 형식이 올바르지 않습니다. 관리자에게 문의하세요.');
    }

    // 브라우저별 특별 처리
    const userAgent = navigator.userAgent.toLowerCase();
    const isChrome = userAgent.includes('chrome') && !userAgent.includes('edg');
    const isFirefox = userAgent.includes('firefox');
    
    if (isChrome) {
      console.log('🌐 Chrome 브라우저 감지: Chrome Push Service 사용');
    } else if (isFirefox) {
      console.log('🌐 Firefox 브라우저 감지: Mozilla Push Service 사용');
    }

    // 새 구독 생성
    console.log('🆕 새 푸시 구독 생성 시도...');
    console.log('구독 옵션:', {
      userVisibleOnly: true,
      applicationServerKey: `Uint8Array(${applicationServerKey.length})`,
      browser: isChrome ? 'Chrome' : isFirefox ? 'Firefox' : 'Other'
    });
    
    let subscription: PushSubscription;
    try {
      // 구독 생성 시도
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });
      console.log('🎉 푸시 알림 구독 성공!');
    } catch (subscribeError) {
      console.error('❌ 푸시 구독 생성 중 오류:', {
        error: subscribeError,
        name: subscribeError instanceof Error ? subscribeError.name : 'Unknown',
        message: subscribeError instanceof Error ? subscribeError.message : String(subscribeError),
        stack: subscribeError instanceof Error ? subscribeError.stack : undefined,
        userAgent: navigator.userAgent
      });
      
      // AbortError에 대한 특별 처리
      if (subscribeError instanceof Error && subscribeError.name === 'AbortError') {
        console.log('🔄 AbortError 감지, Push service 재연결 시도...');
        
        // 잠시 대기 후 재시도
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        try {
          console.log('🔄 푸시 구독 재시도...');
          subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
          });
          console.log('🎉 푸시 알림 구독 재시도 성공!');
        } catch (retryError) {
          console.error('❌ 푸시 구독 재시도도 실패:', retryError);
          throw retryError;
        }
      } else {
        throw subscribeError;
      }
    }

    console.log('📊 구독 정보 상세:', {
      endpoint: subscription.endpoint,
      expirationTime: subscription.expirationTime,
      p256dh: subscription.getKey('p256dh') ? {
        length: subscription.getKey('p256dh')!.byteLength,
        status: 'OK'
      } : 'MISSING',
      auth: subscription.getKey('auth') ? {
        length: subscription.getKey('auth')!.byteLength,
        status: 'OK'
      } : 'MISSING'
    });
    
    // 서버에 구독 정보 전송
    try {
      const serverSuccess = await sendSubscriptionToServer(subscription);
      if (!serverSuccess) {
        console.warn('서버 구독 등록 실패했지만 로컬 구독은 유지');
      } else {
        console.log('서버 구독 등록 성공');
      }
    } catch (serverError) {
      console.error('서버 구독 등록 중 오류:', serverError);
      // 서버 등록 실패해도 로컬 구독은 유지
    }
    
    return subscription;
  } catch (error) {
    console.error('푸시 알림 구독 과정에서 오류:', error);
    
    // 구체적인 에러 메시지 생성
    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        if (error.message.includes('Registration failed')) {
          throw new Error('푸시 서비스 등록에 실패했습니다. 잠시 후 다시 시도해주세요.');
        } else {
          throw new Error('푸시 알림 설정이 중단되었습니다. 다시 시도해주세요.');
        }
      } else if (error.name === 'NotSupportedError') {
        throw new Error('이 브라우저나 환경에서는 푸시 알림이 지원되지 않습니다.');
      } else if (error.name === 'NotAllowedError') {
        throw new Error('푸시 알림이 차단되었습니다. 브라우저 설정을 확인해주세요.');
      } else if (error.message.includes('VAPID')) {
        throw new Error('서버 설정에 문제가 있습니다. 관리자에게 문의하세요.');
      }
    }
    
    throw new Error('푸시 알림 설정에 실패했습니다. 브라우저나 네트워크 상태를 확인해주세요.');
  }
}

// 서버에 구독 정보 전송
export async function sendSubscriptionToServer(subscription: PushSubscription): Promise<boolean> {
  console.log('📡 서버에 구독 정보 전송 시도...');
  
  // 개발 모드에서는 서버 통신 우회 (선택적)
  const skipServerSend = import.meta.env.VITE_DEV_MODE === 'true' || import.meta.env.VITE_SKIP_PUSH_SERVER === 'true';
  if (skipServerSend) {
    console.log('🚧 개발 모드: 서버 통신 우회, 구독 성공으로 가정');
    return true;
  }
  
  try {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    console.log('인증 토큰 확인:', token ? `${token.substring(0, 10)}...` : 'MISSING');
    
    if (!token) {
      console.error('❌ 인증 토큰이 없음');
      return false;
    }

    const subscriptionJson = subscription.toJSON();
    console.log('📋 전송할 구독 정보:', {
      endpoint: subscriptionJson.endpoint,
      keys: {
        p256dh: subscriptionJson.keys?.p256dh ? 'OK' : 'MISSING',
        auth: subscriptionJson.keys?.auth ? 'OK' : 'MISSING'
      }
    });

    const url = `${BACKEND_BASE_URL}/push/subscribe/`;
    console.log('📡 서버 URL:', url);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(subscriptionJson)
    });

    console.log('📡 서버 응답:', {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
      headers: {
        contentType: response.headers.get('content-type'),
        contentLength: response.headers.get('content-length')
      }
    });

    if (response.ok) {
      try {
        const responseData = await response.json();
        console.log('✅ 구독 정보 서버 전송 성공:', responseData);
      } catch (jsonError) {
        console.log('✅ 구독 정보 서버 전송 성공 (응답 JSON 파싱 불가)');
      }
      return true;
    } else {
      try {
        const errorData = await response.text();
        console.error('❌ 구독 정보 서버 전송 실패:', {
          status: response.status,
          statusText: response.statusText,
          errorData: errorData
        });
      } catch (textError) {
        console.error('❌ 구독 정보 서버 전송 실패:', response.status, response.statusText);
      }
      return false;
    }
  } catch (error) {
    console.error('❌ 구독 정보 전송 네트워크 오류:', {
      error: error,
      name: error instanceof Error ? error.name : 'Unknown',
      message: error instanceof Error ? error.message : String(error)
    });
    return false;
  }
}

// 푸시 알림 구독 해제
export async function unsubscribeFromPushNotifications(): Promise<boolean> {
  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) {
      return false;
    }

    const subscription = await registration.pushManager.getSubscription();
    if (!subscription) {
      return false;
    }

    const success = await subscription.unsubscribe();
    
    if (success) {
      // 서버에서도 구독 정보 제거
      await removeSubscriptionFromServer(subscription);
      console.log('푸시 알림 구독 해제 성공');
    }
    
    return success;
  } catch (error) {
    console.error('푸시 알림 구독 해제 실패:', error);
    return false;
  }
}

// 서버에서 구독 정보 제거
async function removeSubscriptionFromServer(subscription: PushSubscription): Promise<void> {
  try {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    
    await fetch(`${BACKEND_BASE_URL}/push/unsubscribe/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        endpoint: subscription.endpoint
      })
    });
  } catch (error) {
    console.error('서버 구독 해제 오류:', error);
  }
}

// 현재 구독 상태 확인
export async function getSubscriptionStatus(): Promise<PushSubscription | null> {
  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (!registration) {
      return null;
    }

    return await registration.pushManager.getSubscription();
  } catch (error) {
    console.error('구독 상태 확인 오류:', error);
    return null;
  }
}

// 알림 권한 상태 확인
export function getNotificationPermissionStatus(): NotificationPermission {
  if (!('Notification' in window)) {
    console.warn('이 브라우저는 알림을 지원하지 않습니다.');
    return 'denied';
  }
  return Notification.permission;
}

// 브라우저별 권한 안내 메시지 생성
export function getPermissionGuideMessage(): string {
  const userAgent = navigator.userAgent.toLowerCase();
  const isChrome = userAgent.includes('chrome') && !userAgent.includes('edg');
  const isFirefox = userAgent.includes('firefox');
  const isSafari = userAgent.includes('safari') && !userAgent.includes('chrome');
  
  if (isChrome) {
    return '크롬에서 알림 허용하기:\n1. 주소창 왼쪽의 🔒 또는 🛡️ 아이콘 클릭\n2. "알림" 설정을 "허용"으로 변경\n3. 페이지 새로고침';
  } else if (isFirefox) {
    return '파이어폭스에서 알림 허용하기:\n1. 주소창 왼쪽의 방패 아이콘 클릭\n2. "알림" 설정을 "허용"으로 변경\n3. 페이지 새로고침';
  } else if (isSafari) {
    return '사파리에서 알림 허용하기:\n1. Safari > 환경설정 > 웹 사이트 > 알림\n2. 현재 사이트를 "허용"으로 설정\n3. 페이지 새로고침';
  } else {
    return '브라우저 설정에서 이 사이트의 알림을 허용해주세요.';
  }
}

// PWA 설치 가능 여부 확인
export function isPWAInstallable(): boolean {
  return 'serviceWorker' in navigator && 'PushManager' in window;
}

// PWA 설치 프롬프트 표시
export function promptPWAInstall(deferredPrompt: any): void {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult: any) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('사용자가 PWA 설치를 승인했습니다');
      } else {
        console.log('사용자가 PWA 설치를 거부했습니다');
      }
    });
  }
}

// 로컬 알림 표시 (테스트용)
export async function showLocalNotification(data: PushNotificationData): Promise<void> {
  const hasPermission = await requestNotificationPermission();
  if (!hasPermission) {
    return;
  }

  const notification = new Notification(data.title, {
    body: data.body,
    icon: '/alpaca-192.png',
    tag: `${data.type}-notification`,
    data: data.data,
    requireInteraction: data.requireInteraction || false
  });

  // 알림 클릭 시 페이지로 이동
  notification.onclick = () => {
    window.focus();
    notification.close();
  };
}