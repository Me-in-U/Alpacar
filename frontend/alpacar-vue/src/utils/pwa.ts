// src/utils/pwa.ts - PWA 및 푸시 알림 관리

import { BACKEND_BASE_URL } from './api';

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

// 사용자 스토어에서 VAPID 키 가져오기 함수
function getVapidKeyFromUser(): string | null {
  try {
    // 1. localStorage에서 user 객체 확인
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');
    if (userStr) {
      const user = JSON.parse(userStr);
      console.log('localStorage user 객체:', user);
      if (user && user.vapid_public_key && typeof user.vapid_public_key === 'string') {
        return user.vapid_public_key;
      }
    }

    // 2. Pinia store에서 직접 접근 시도
    const storeStr = localStorage.getItem('user-store');
    if (storeStr) {
      const store = JSON.parse(storeStr);
      console.log('Pinia store 확인:', store);
      if (store && store.me && store.me.vapid_public_key) {
        return store.me.vapid_public_key;
      }
    }

    console.warn('사용자 정보에서 VAPID 키를 찾을 수 없음');
  } catch (error) {
    console.warn('사용자 정보에서 VAPID 키 추출 실패:', error);
  }
  return null;
}

// 동적 VAPID 키 가져오기
function getVapidKey(): string {
  console.log('VAPID 키 검색 시작...');
  
  // 1. 환경 변수 우선 사용 (로컬 개발)
  if (VAPID_PUBLIC_KEY && typeof VAPID_PUBLIC_KEY === 'string' && VAPID_PUBLIC_KEY.length > 0) {
    console.log('환경 변수에서 VAPID 키 사용');
    return VAPID_PUBLIC_KEY;
  }
  
  // 2. 사용자 정보에서 가져오기 (배포 환경)
  const userVapidKey = getVapidKeyFromUser();
  if (userVapidKey && typeof userVapidKey === 'string' && userVapidKey.length > 0) {
    console.log('사용자 정보에서 VAPID 키 사용');
    return userVapidKey;
  }
  
  console.error('VAPID 키를 찾을 수 없음:', {
    envKey: VAPID_PUBLIC_KEY,
    userKey: userVapidKey
  });
  throw new Error('VAPID 키를 찾을 수 없습니다. 로그인 후 다시 시도해주세요.');
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
    console.warn('알림 권한이 거부되었습니다.');
    throw new Error('알림 권한이 거부되었습니다. 브라우저 설정에서 알림을 허용해주세요.');
  }

  const permission = await Notification.requestPermission();
  if (permission !== 'granted') {
    throw new Error('알림 권한을 허용해주세요.');
  }
  
  return true;
}

// Service Worker 등록
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.warn('이 브라우저는 Service Worker를 지원하지 않습니다.');
    return null;
  }

  // 네트워크 IP 접속 시 HTTPS가 아닌 경우 경고
  if (!window.isSecureContext && location.hostname !== 'localhost') {
    console.warn('PWA는 HTTPS 또는 localhost에서만 완전히 지원됩니다. 일부 기능이 제한될 수 있습니다.');
  }

  try {
    const registration = await navigator.serviceWorker.register('/service-worker.js', {
      scope: '/'
    });
    
    console.log('Service Worker 등록 성공:', registration);
    
    // Service Worker 업데이트 감지
    registration.addEventListener('updatefound', () => {
      console.log('새로운 Service Worker 발견');
      const newWorker = registration.installing;
      if (newWorker) {
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            console.log('새로운 Service Worker 설치됨');
            // 사용자에게 업데이트 알림 표시 가능
          }
        });
      }
    });

    return registration;
  } catch (error) {
    console.error('Service Worker 등록 실패:', error);
    return null;
  }
}

// 푸시 알림 구독
export async function subscribeToPushNotifications(): Promise<PushSubscription | null> {
  // 동적 VAPID 키 가져오기
  let vapidKey: string;
  try {
    vapidKey = getVapidKey();
  } catch (error) {
    console.error('VAPID 키 가져오기 실패:', error);
    throw error;
  }

  const registration = await registerServiceWorker();
  if (!registration) {
    throw new Error('Service Worker 등록 실패');
  }

  const hasPermission = await requestNotificationPermission();
  if (!hasPermission) {
    throw new Error('알림 권한 거부됨');
  }

  try {
    // 기존 구독 확인
    const existingSubscription = await registration.pushManager.getSubscription();
    if (existingSubscription) {
      console.log('기존 구독 사용:', existingSubscription);
      await sendSubscriptionToServer(existingSubscription);
      return existingSubscription;
    }

    // 새 구독 생성
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(vapidKey)
    });

    console.log('푸시 알림 구독 성공:', subscription);
    
    // 서버에 구독 정보 전송
    const serverSuccess = await sendSubscriptionToServer(subscription);
    if (!serverSuccess) {
      console.warn('서버 구독 등록 실패, 로컬 구독은 유지');
    }
    
    return subscription;
  } catch (error) {
    console.error('푸시 알림 구독 실패:', error);
    throw error;
  }
}

// 서버에 구독 정보 전송
export async function sendSubscriptionToServer(subscription: PushSubscription): Promise<boolean> {
  try {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    
    const response = await fetch(`${BACKEND_BASE_URL}/push/subscribe/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(subscription.toJSON())
    });

    if (response.ok) {
      console.log('구독 정보 서버 전송 성공');
      return true;
    } else {
      console.error('구독 정보 서버 전송 실패:', response.status);
      return false;
    }
  } catch (error) {
    console.error('구독 정보 전송 오류:', error);
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