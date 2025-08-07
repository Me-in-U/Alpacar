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

// VAPID 공개 키 (환경 변수에서 안전하게 가져옴)
const VAPID_PUBLIC_KEY = import.meta.env.VITE_VAPID_PUBLIC_KEY;

// URL-safe base64를 Uint8Array로 변환
function urlBase64ToUint8Array(base64String: string): Uint8Array {
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
}

// 푸시 알림 권한 요청
export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) {
    console.warn('이 브라우저는 알림을 지원하지 않습니다.');
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission === 'denied') {
    console.warn('알림 권한이 거부되었습니다.');
    return false;
  }

  const permission = await Notification.requestPermission();
  return permission === 'granted';
}

// Service Worker 등록
export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    console.warn('이 브라우저는 Service Worker를 지원하지 않습니다.');
    return null;
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
  const registration = await registerServiceWorker();
  if (!registration) {
    return null;
  }

  const hasPermission = await requestNotificationPermission();
  if (!hasPermission) {
    return null;
  }

  try {
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
    });

    console.log('푸시 알림 구독 성공:', subscription);
    
    // 서버에 구독 정보 전송
    await sendSubscriptionToServer(subscription);
    
    return subscription;
  } catch (error) {
    console.error('푸시 알림 구독 실패:', error);
    return null;
  }
}

// 서버에 구독 정보 전송
export async function sendSubscriptionToServer(subscription: PushSubscription): Promise<boolean> {
  try {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    
    const response = await fetch(`${BACKEND_BASE_URL}/notifications/subscribe/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        subscription: {
          endpoint: subscription.endpoint,
          keys: {
            p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')!))),
            auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth')!)))
          }
        }
      })
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
    
    await fetch(`${BACKEND_BASE_URL}/notifications/unsubscribe/`, {
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
    icon: '/alpaca-logo-small.png',
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