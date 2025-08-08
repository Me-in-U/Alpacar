// src/utils/pushNotification.ts - Push notification utility functions
import { BACKEND_BASE_URL } from './api';
import { getSubscriptionStatus } from './pwa';

export interface PushStatus {
  isEnabled: boolean;
  hasPermission: boolean;
  hasSubscription: boolean;
  subscriptionCount?: number;
}

/**
 * 현재 푸시 알림 상태를 종합적으로 확인
 */
export async function checkPushStatus(): Promise<PushStatus> {
  try {
    // 1. 브라우저 알림 권한 확인
    const hasPermission = 'Notification' in window && Notification.permission === 'granted';
    
    // 2. Service Worker 구독 상태 확인
    const subscription = await getSubscriptionStatus();
    const hasSubscription = !!subscription;
    
    // 3. 서버 설정 확인
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    let isEnabled = false;
    
    if (token) {
      try {
        const response = await fetch(`${BACKEND_BASE_URL}/push/setting/`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          isEnabled = data.push_on === true;
        }
      } catch (error) {
        console.warn('서버 푸시 설정 확인 실패:', error);
      }
    }
    
    return {
      isEnabled,
      hasPermission,
      hasSubscription,
      subscriptionCount: hasSubscription ? 1 : 0
    };
  } catch (error) {
    console.error('푸시 알림 상태 확인 오류:', error);
    return {
      isEnabled: false,
      hasPermission: false,
      hasSubscription: false,
      subscriptionCount: 0
    };
  }
}

/**
 * 테스트 푸시 알림 전송
 */
export async function sendTestPushNotification(title?: string, body?: string): Promise<boolean> {
  try {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('로그인이 필요합니다.');
    }
    
    const response = await fetch(`${BACKEND_BASE_URL}/push/test/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: title || '🚗 테스트 알림',
        body: body || '이것은 테스트 푸시 알림입니다!'
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('테스트 푸시 알림 전송 성공:', data);
      return true;
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || '테스트 푸시 알림 전송 실패');
    }
  } catch (error: any) {
    console.error('테스트 푸시 알림 전송 오류:', error);
    throw error;
  }
}

/**
 * 푸시 알림 상태 표시를 위한 문자열 생성
 */
export function getPushStatusText(status: PushStatus): string {
  if (!status.hasPermission) {
    return '권한 없음';
  }
  
  if (!status.hasSubscription) {
    return '구독 없음';
  }
  
  if (!status.isEnabled) {
    return '비활성화됨';
  }
  
  return '활성화됨';
}

/**
 * 푸시 알림 상태에 따른 색상 클래스 반환
 */
export function getPushStatusClass(status: PushStatus): string {
  if (status.isEnabled && status.hasPermission && status.hasSubscription) {
    return 'status-active';
  }
  
  if (status.hasPermission && status.hasSubscription) {
    return 'status-warning';
  }
  
  return 'status-inactive';
}