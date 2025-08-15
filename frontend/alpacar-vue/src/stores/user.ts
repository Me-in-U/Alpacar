import { defineStore } from "pinia";
import { BACKEND_BASE_URL } from "@/utils/api";
import { subscribeToPushNotifications, unsubscribeFromPushNotifications } from "@/utils/pwa";
import { 
  SecureTokenManager, 
  encryptUserData, 
  decryptUserData, 
  validateAutoLoginExpiry 
} from "@/utils/security";
import { apiClient } from "@/api/parking";


export interface VehicleModel {
	id: number;
	brand: string;
	model_name: string;
	image_url: string;
}

export interface Vehicle {
	id: number;
	license_plate: string;
	model: VehicleModel;
}

export interface User {
	nickname: string;
	push_on: boolean;
	score: number;
	is_staff: boolean;
	vapid_public_key: string;
	is_social_user?: boolean;
}

export const useUserStore = defineStore("user", {
	state: () => ({
		me: null as User | null,
		vehicles: [] as Vehicle[],
		vehicleModels: [] as VehicleModel[],
		isToggling: false,
		// API 호출 중복 방지
		isLoading: false,
		lastFetchTime: 0,
	}),
	actions: {
		setUser(user: User) {
			this.me = user;
			// 🔒 보안 강화: 최소 데이터만 localStorage 저장
			this.saveMinimalUserData(user);
		},
		// 최소 데이터만 추출 (민감정보 완전 차단)
		saveMinimalUserData(user: any) {
			try {
				const minimalData = this.extractMinimalData(user);
				localStorage.setItem("user", JSON.stringify(minimalData));
				console.log("🔒 [SECURITY] 최소 사용자 데이터 저장:", Object.keys(minimalData));
			} catch (error) {
				console.error("최소 사용자 데이터 저장 실패:", error);
			}
		},
		// 허용된 키만 추출하는 화이트리스트 방식
		extractMinimalData(userData: any): any {
			const allowedKeys = ['nickname', 'is_staff', 'push_on', 'score', 'is_social_user'];
			const minimalData: any = {};
			allowedKeys.forEach(key => {
				if (userData && userData.hasOwnProperty(key)) {
					minimalData[key] = userData[key];
				}
			});
			return minimalData;
		},
		clearUser() {
			this.me = null;
			this.vehicles = [];
			// 보안 강화: 모든 보안 토큰과 데이터 정리
			SecureTokenManager.clearAllSecureTokens();
			// 기존 평문 토큰도 제거
			localStorage.removeItem("access_token");
			localStorage.removeItem("refresh_token");
			sessionStorage.removeItem("access_token");
			sessionStorage.removeItem("refresh_token");
		},

		// 보안 사용자 정보 복원 함수
		restoreUserFromStorage(): User | null {
			try {
				// 먼저 암호화된 데이터에서 복원 시도
				const encryptedUserData = localStorage.getItem("secure_user_data");
				if (encryptedUserData) {
					const userData = decryptUserData(encryptedUserData);
					if (userData) {
						this.me = userData;
						return userData;
					}
				}
				
				// 암호화된 데이터가 없거나 복호화 실패 시 마스킹된 데이터 사용
				const userDataString = localStorage.getItem("user");
				if (userDataString) {
					const userData = JSON.parse(userDataString);
					this.me = userData;
					return userData;
				}
				
				return null;
			} catch (error) {
				console.warn("사용자 정보 복원 실패:", error);
				return null;
			}
		},

		// 자동 로그인 만료 체크 함수 (보안 강화)
		async checkAutoLoginExpiry(): Promise<boolean> {
			try {
				const isValid = await validateAutoLoginExpiry(BACKEND_BASE_URL);
				if (!isValid) {
					console.log("자동 로그인이 만료되었습니다.");
					return true;
				}
				return false;
			} catch (error) {
				console.warn("자동 로그인 만료 검증 실패:", error);
				// 검증 실패 시 만료된 것으로 간주
				SecureTokenManager.clearAllSecureTokens();
				return true;
			}
		},
		async fetchMe(accessToken?: string, baseUrl?: string) {
			// 중복 호출 방지 - 최근 3초 이내에 호출했으면 스킵
			const now = Date.now();
			if (this.isLoading || (this.me && now - this.lastFetchTime < 3000)) {
				console.log("fetchMe 중복 호출 방지 - 기존 정보 사용");
				return this.me;
			}

			this.isLoading = true;
			this.lastFetchTime = now;

			try {
				// 인자 없으면 보안 토큰 관리자에서 가져옴
				const token = accessToken || SecureTokenManager.getSecureToken("access_token");
				if (!token) throw new Error("No token found");

				// baseUrl이 있으면 절대경로, 없으면 apiClient의 baseURL 기준 상대경로
				const url = baseUrl ? `${baseUrl}/users/me/` : "/users/me/";

				const { data } = await apiClient.get<User>(url, {

				});

				this.setUser(data);
				return data;
			} catch (error) {
				console.error("fetchMe 오류:", error);
				throw error;
			} finally {
				this.isLoading = false;
			}
		},
		// 🔒 민감한 사용자 정보 동적 로딩 (UserProfile, UserSetting 전용)
		async fetchDetailedUserInfo() {
			const token = SecureTokenManager.getSecureToken("access_token");
			if (!token) {
				throw new Error("로그인이 필요합니다.");
			}

			try {
				const res = await fetch(`${BACKEND_BASE_URL}/users/me/`, {
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
				});

				if (!res.ok) {
					throw new Error(`사용자 정보 조회 실패 (${res.status})`);
				}

				const userData = await res.json();
				console.log("🔒 [SECURITY] 민감한 사용자 정보 동적 로딩 완료");
				return userData;
			} catch (error) {
				console.error("fetchDetailedUserInfo 오류:", error);
				throw error;
			}
		},
		async updateProfile(data: Partial<Pick<User, "nickname">>) {
			const token = SecureTokenManager.getSecureToken("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");
			const res = await fetch(`${BACKEND_BASE_URL}/users/me/`, {
				method: "PUT",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
				body: JSON.stringify(data),
			});
			if (!res.ok) {
				const err = await res.json();
				throw new Error(err.detail || "프로필 업데이트 실패");
			}
			const updated: User = await res.json();
			this.me = { ...this.me!, ...updated };
			return this.me;
		},
		async changePassword(currentPassword: string, newPassword: string) {
			const token = SecureTokenManager.getSecureToken("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");

			const res = await fetch(`${BACKEND_BASE_URL}/auth/password-change/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
				body: JSON.stringify({
					current_password: currentPassword,
					new_password: newPassword,
					new_password2: newPassword, // 필요 시 confirm 필드
				}),
			});

			if (!res.ok) {
				// 에러 바디 전체 읽어서, detail 또는 field errors를 합친 메시지로
				const errBody = await res.json();
				// detail 필드 우선, 없으면 각 필드 메시지를 모아서
				const message = errBody.detail || Object.values(errBody).flat().join(", ");
				throw new Error(message || "비밀번호 변경 실패");
			}
			return await res.json();
		},
		async login(email: string, password: string, autoLogin: boolean = false) {
			const res = await fetch(`${BACKEND_BASE_URL}/auth/login/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Accept: "application/json",
				},
				body: JSON.stringify({ email, password }),
				// 성능 최적화 옵션
				cache: "no-cache",
				keepalive: true,
			});

			if (!res.ok) {
				let errorMessage = `로그인 실패 (${res.status})`;
				try {
					const errorData = await res.json();
					errorMessage = errorData.detail || errorData.message || errorMessage;
				} catch {
					// JSON 파싱 실패 시 기본 에러 메시지 사용
				}
				throw new Error(errorMessage);
			}

			const data = await res.json();

			// 토큰 확인
			if (!data.access || !data.refresh) {
				throw new Error("서버에서 올바른 인증 토큰을 받지 못했습니다.");
			}

			// 보안 강화: 암호화된 토큰 저장
			if (autoLogin) {
				// 기존 세션 토큰 제거 후 localStorage에 암호화하여 저장
				SecureTokenManager.removeSecureToken("access_token");
				SecureTokenManager.removeSecureToken("refresh_token");
				SecureTokenManager.setSecureToken("access_token", data.access, false);
				SecureTokenManager.setSecureToken("refresh_token", data.refresh, false);
				// 자동 로그인 만료 시간 설정 (1년 후)
				const expiryDate = new Date();
				expiryDate.setFullYear(expiryDate.getFullYear() + 1);
				localStorage.setItem("auto_login_expiry", expiryDate.toISOString());
				console.log("보안 자동 로그인 설정됨 - 1년간 유지 (암호화)");
			} else {
				// 기존 localStorage 토큰 제거 (자동 로그인 정보 삭제)
				localStorage.removeItem(SecureTokenManager.TOKEN_PREFIX + "access_token");
				localStorage.removeItem(SecureTokenManager.TOKEN_PREFIX + "refresh_token");
				localStorage.removeItem("auto_login_expiry");
				// 일반 로그인: sessionStorage에 암호화하여 저장
				SecureTokenManager.setSecureToken("access_token", data.access, true);
				SecureTokenManager.setSecureToken("refresh_token", data.refresh, true);
				console.log("보안 일반 로그인 설정됨 - 브라우저 종료 시 만료 (암호화)");
			}

			await this.fetchMe(data.access);
			
			// 로그인 성공 시 차량 정보도 미리 로드 (라우터 가드 성능 개선)
			try {
				await this.fetchMyVehicles();
				console.log("로그인 시 차량 정보 미리 로드 완료");
			} catch (vehicleError) {
				console.warn("차량 정보 로드 실패 (무시):", vehicleError);
			}
			
			return this.me;
		},

		async adminLogin(email: string, password: string, autoLogin: boolean = false) {
			// 일반 로그인 시도 (자동 로그인 옵션 포함)
			await this.login(email, password, autoLogin);
			// 관리자인지 체크
			if (!this.me?.is_staff) {
				// 권한 없으면 초기화 후 에러
				this.clearUser();
				throw new Error("관리자 권한이 없습니다.");
			}
			return this.me;
		},

		// 동적 URL을 사용하는 로그인 함수 (모바일 호환성 개선)
		async loginWithUrl(email: string, password: string, backendUrl: string) {
			const loginUrl = `${backendUrl}/auth/login/`;

			try {
				const res = await fetch(loginUrl, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						Accept: "application/json",
					},
					body: JSON.stringify({ email, password }),
					mode: "cors",
					credentials: "omit",
					cache: "no-cache",
				});

				if (!res.ok) {
					let errorMessage = `로그인 실패 (${res.status})`;
					try {
						const errorData = await res.json();
						errorMessage = errorData.detail || errorData.message || errorMessage;
					} catch {
						// JSON 파싱 실패 시 기본 에러 메시지 사용
					}
					throw new Error(errorMessage);
				}

				const data = await res.json();

				// 토큰 확인
				if (!data.access || !data.refresh) {
					throw new Error("서버에서 올바른 인증 토큰을 받지 못했습니다.");
				}

				localStorage.setItem("access_token", data.access);
				localStorage.setItem("refresh_token", data.refresh);

				await this.fetchMe(data.access, backendUrl);
				
				// 로그인 성공 시 차량 정보도 미리 로드 (라우터 가드 성능 개선)
				try {
					await this.fetchMyVehicles();
					console.log("동적 URL 로그인 시 차량 정보 미리 로드 완료");
				} catch (vehicleError) {
					console.warn("차량 정보 로드 실패 (무시):", vehicleError);
				}
				
				return this.me;
			} catch (error: any) {
				// Mixed Content나 네트워크 오류에 대한 사용자 친화적 메시지
				if (error.message.includes("Mixed Content") || error.message.includes("Failed to fetch")) {
					throw new Error("네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.");
				}
				throw error;
			}
		},

		async togglePush(on: boolean) {
			if (!this.me) {
				console.warn("togglePush: 유저 정보 없음");
				throw new Error("로그인이 필요합니다.");
			}
			if (this.isToggling) {
				console.warn("togglePush: 이미 처리 중");
				return;
			}
			
			console.log("[togglePush] 시작, 변경 요청:", on);
			console.log("[togglePush] 사용자 VAPID 키 상태:", {
				hasVapidKey: !!this.me.vapid_public_key,
				vapidKeyLength: this.me.vapid_public_key?.length || 0,
				vapidKeyPreview: this.me.vapid_public_key?.substring(0, 10) + '...' || 'MISSING'
			});
			
			this.isToggling = true;
			const prev = this.me.push_on;
			this.me.push_on = on;

			try {
				// VAPID 키 사전 체크
				if (!this.me.vapid_public_key) {
					console.error("[togglePush] VAPID 키 없음 - 사용자 정보 새로고침 시도");
					
					// 사용자 정보 새로고침 시도
					const token = SecureTokenManager.getSecureToken("access_token");
					if (token) {
						try {
							await this.fetchMe(token);
							if (!this.me?.vapid_public_key) {
								throw new Error("서버에서 VAPID 키를 받지 못했습니다. 관리자에게 문의하세요.");
							}
							console.log("[togglePush] 사용자 정보 새로고침 성공, VAPID 키 확인됨");
						} catch (refreshError) {
							console.error("사용자 정보 새로고침 실패:", refreshError);
							throw new Error("로그인 세션이 만료되었습니다. 다시 로그인해 주세요.");
						}
					} else {
						throw new Error("로그인이 필요합니다.");
					}
				}

				if (on) {
					// PWA utils의 통합된 구독 함수 사용
					console.log("[togglePush] PWA 구독 시도");
					await subscribeToPushNotifications();
					console.log("[togglePush] PWA 구독 성공");
				} else {
					// PWA utils의 통합된 구독 해제 함수 사용
					console.log("[togglePush] PWA 구독 해제 시도");
					await unsubscribeFromPushNotifications();
					console.log("[togglePush] PWA 구독 해제 성공");
				}

				// 서버에 설정 저장
				const token = SecureTokenManager.getSecureToken("access_token");
				if (!token) {
					throw new Error("인증 토큰이 없습니다.");
				}

				console.log("[togglePush] 서버에 설정 저장 시도:", on);
				const saveRes = await fetch(`${BACKEND_BASE_URL}/push/setting/`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
					body: JSON.stringify({ push_on: on }),
				});
				if (!saveRes.ok) {
					const errorText = await saveRes.text();
					console.error("서버 저장 오류:", saveRes.status, errorText);
					throw new Error(`서버 설정 저장 실패 (${saveRes.status})`);
				}
				console.log("[togglePush] 서버 설정 저장 성공");
			} catch (e) {
				console.error("[togglePush] 오류 발생, 롤백", e);
				this.me.push_on = prev; // 롤백

				// 사용자에게 구체적인 오류 메시지 제공
				let errorMessage = "푸시 알림 설정에 실패했습니다.";
				if (e instanceof Error) {
					if (e.message.includes("VAPID") || e.message.includes("서버에서")) {
						errorMessage = "서버 설정 오류입니다. 관리자에게 문의하세요.";
					} else if (e.message.includes("Service Worker") || e.message.includes("HTTPS")) {
						errorMessage = "HTTPS 환경에서 사용해주세요.";
					} else if (e.message.includes("Permission") || e.message.includes("권한")) {
						errorMessage = "알림 권한을 허용해주세요.";
					} else if (e.message.includes("로그인") || e.message.includes("세션")) {
						errorMessage = "로그인이 만료되었습니다. 다시 로그인해 주세요.";
					} else if (e.message.includes("인증")) {
						errorMessage = "로그인 상태를 확인해주세요.";
					}
				}
				throw new Error(errorMessage);
			} finally {
				this.isToggling = false;
				console.log("[togglePush] 완료, 최종 상태:", this.me.push_on);
			}
		},

		// 차량 조회
		async fetchMyVehicles() {
			const token = SecureTokenManager.getSecureToken("access_token");
			if (!token) throw new Error("토큰이 없습니다.");

			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/`, {
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
			});
			if (!res.ok) throw new Error("차량 목록 조회 실패");
			const list: Vehicle[] = await res.json();
			this.vehicles = list;
			return list;
		},
		// 모델 리스트 불러오기
		async fetchVehicleModels() {
			const token = SecureTokenManager.getSecureToken("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicle-models/`, {
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
			});
			if (!res.ok) throw new Error("모델 리스트 조회 실패");
			this.vehicleModels = await res.json();
		},

		// 번호판 중복 체크
		async checkLicense(license: string): Promise<boolean> {
			const token = SecureTokenManager.getSecureToken("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/check-license/?license=${encodeURIComponent(license)}`, {
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
			});
			if (!res.ok) throw new Error("중복 체크 API 실패");
			const { exists } = await res.json();
			return !exists;
		},
		// 차량 등록
		async addVehicle(modelId: number, license_plate: string) {
			const token = SecureTokenManager.getSecureToken("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/`, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
				body: JSON.stringify({ model: modelId, license_plate }),
			});
			if (!res.ok) {
				const err = await res.json();
				throw new Error(JSON.stringify(err));
			}
			const newVehicle: Vehicle = await res.json();
			this.vehicles.push(newVehicle);
		},
		// 차량 제거 기능
		async removeVehicle(id: number) {
			const token = SecureTokenManager.getSecureToken("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/${id}/`, {
				method: "DELETE",
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${token}`,
				},
			});
			if (!res.ok) throw new Error("차량 삭제 실패");
			// 스토어 상태에서도 제거
			this.vehicles = this.vehicles.filter((v) => v.id !== id);
		},
	},
});
