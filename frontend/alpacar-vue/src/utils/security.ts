/**
 * 보안 유틸리티 모듈
 * XSS 공격으로부터 민감한 데이터를 보호하기 위한 암호화/복호화 기능 제공
 */

import CryptoJS from 'crypto-js';

// 브라우저 지문 기반 키 생성 (device fingerprinting)
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

// 보안 토큰 암호화 (내부 사용)
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

// 보안 토큰 복호화 (내부 사용)
function decryptToken(encryptedData: string): string | null {
  try {
    if (!encryptedData || typeof encryptedData !== 'string') {
      return null;
    }
    
    const [sessionKey, encrypted] = encryptedData.split(':');
    if (!sessionKey || !encrypted) {
      console.warn('암호화된 토큰 형식이 올바르지 않음');
      return null;
    }
    
    const deviceKey = generateDeviceKey();
    const combinedKey = CryptoJS.SHA256(deviceKey + sessionKey).toString().substr(0, 32);
    
    const decrypted = CryptoJS.AES.decrypt(encrypted, combinedKey);
    return decrypted.toString(CryptoJS.enc.Utf8);
  } catch (error) {
    console.warn('Token decryption failed:', error);
    return null;
  }
}


// 실제 사용자 정보는 암호화하여 저장 (민감정보 검증 포함)
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

// 암호화된 사용자 정보 복호화
export function decryptUserData(encryptedData: string): any | null {
  try {
    const [sessionKey, encrypted] = encryptedData.split(':');
    if (!sessionKey || !encrypted) {
      return null;
    }
    
    const deviceKey = generateDeviceKey();
    const combinedKey = CryptoJS.SHA256(deviceKey + sessionKey).toString().substr(0, 32);
    
    const decrypted = CryptoJS.AES.decrypt(encrypted, combinedKey);
    const userDataString = decrypted.toString(CryptoJS.enc.Utf8);
    
    return JSON.parse(userDataString);
  } catch (error) {
    console.warn('User data decryption failed:', error);
    return null;
  }
}

// 보안 토큰 유틸리티
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
  
  // 보안 토큰 제거
  static removeSecureToken(key: string): void {
    sessionStorage.removeItem(this.TOKEN_PREFIX + key);
    localStorage.removeItem(this.TOKEN_PREFIX + key);
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

// 자동 로그인 만료 검증 (클라이언트 사이드만)
export async function validateAutoLoginExpiry(backendUrl: string): Promise<boolean> {
  const expiryDate = localStorage.getItem('auto_login_expiry');
  if (!expiryDate) {
    return false; // 만료 정보 없음
  }
  
  const expiry = new Date(expiryDate);
  const now = new Date();
  
  if (now > expiry) {
    // 클라이언트 사이드 만료
    console.log('Auto login expired - clearing tokens');
    SecureTokenManager.clearAllSecureTokens();
    return false;
  }
  
  // 토큰 존재 확인
  const token = SecureTokenManager.getSecureToken('access_token');
  if (!token) {
    console.log('No access token found - clearing auto login');
    SecureTokenManager.clearAllSecureTokens();
    return false;
  }
  
  console.log('Auto login still valid');
  return true;
}