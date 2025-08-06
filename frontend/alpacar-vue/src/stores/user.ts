import { defineStore } from "pinia";
import { BACKEND_BASE_URL } from "@/utils/api";

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
	email: string;
	name: string;
	nickname: string;
	phone: string;
	push_on: boolean;
	score: number;
	is_staff: boolean;
	vapid_public_key: string;
}

export const useUserStore = defineStore("user", {
	state: () => ({
		me: null as User | null,
		vehicles: [] as Vehicle[],
		vehicleModels: [] as VehicleModel[],
		isToggling: false,
	}),
	actions: {
		setUser(user: User) {
			this.me = user;
		},
		clearUser() {
			this.me = null;
			this.vehicles = [];
			localStorage.removeItem("access_token");
			localStorage.removeItem("refresh_token");
		},
		async fetchMe(accessToken: string, baseUrl?: string) {
			const apiUrl = baseUrl || BACKEND_BASE_URL;
			
			const res = await fetch(`${apiUrl}/users/me/`, {
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${accessToken}`,
				},
			});
			
			if (!res.ok) {
				throw new Error(`프로필 조회 실패 (${res.status})`);
			}
			
			// 응답이 JSON인지 확인
			const contentType = res.headers.get('content-type');
			let profile: User;
			
			try {
				if (contentType && contentType.includes('application/json')) {
					const responseText = await res.text();
					if (responseText.trim()) {
						profile = JSON.parse(responseText);
					} else {
						throw new Error('서버에서 빈 응답을 반환했습니다.');
					}
				} else {
					throw new Error('서버에서 JSON이 아닌 응답을 반환했습니다.');
				}
			} catch (parseError) {
				console.error('프로필 JSON 파싱 오류:', parseError);
				throw new Error('프로필 정보를 처리할 수 없습니다.');
			}
			
			this.setUser(profile);
			return profile;
		},
		async updateProfile(data: Partial<Pick<User, "nickname">>) {
			const token = localStorage.getItem("access_token");
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
			const token = localStorage.getItem("access_token");
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
		async login(email: string, password: string) {
			const res = await fetch(`${BACKEND_BASE_URL}/auth/login/`, {
				method: "POST",
				headers: { 
					"Content-Type": "application/json",
					"Accept": "application/json"
				},
				body: JSON.stringify({ email, password }),
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
				throw new Error('서버에서 올바른 인증 토큰을 받지 못했습니다.');
			}

			localStorage.setItem("access_token", data.access);
			localStorage.setItem("refresh_token", data.refresh);

			await this.fetchMe(data.access);
			return this.me;
		},

		async adminLogin(email: string, password: string) {
			// 일반 로그인 시도
			await this.login(email, password);
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
						"Accept": "application/json"
					},
					body: JSON.stringify({ email, password }),
					mode: 'cors',
					credentials: 'omit',
					cache: 'no-cache'
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
					throw new Error('서버에서 올바른 인증 토큰을 받지 못했습니다.');
				}

				localStorage.setItem("access_token", data.access);
				localStorage.setItem("refresh_token", data.refresh);

				await this.fetchMe(data.access, backendUrl);
				return this.me;
			} catch (error: any) {
				// Mixed Content나 네트워크 오류에 대한 사용자 친화적 메시지
				if (error.message.includes('Mixed Content') || 
					error.message.includes('Failed to fetch')) {
					throw new Error('네트워크 연결에 실패했습니다. 인터넷 연결을 확인해주세요.');
				}
				throw error;
			}
		},

		async togglePush(on: boolean) {
			if (!this.me) {
				console.warn("togglePush: 유저 정보 없음");
				return;
			}
			if (this.isToggling) {
				console.warn("togglePush: 이미 처리 중");
				return;
			}
			console.log("[togglePush] 시작, 변경 요청:", on);
			this.isToggling = true;
			const prev = this.me.push_on;
			this.me.push_on = on;

			const token = localStorage.getItem("access_token");
			if (!token) {
				console.error("[togglePush] 토큰 없음, 롤백");
				this.me.push_on = prev;
				this.isToggling = false;
				return;
			}

			try {
				let swReg: ServiceWorkerRegistration | undefined;
				// ready 대신 getRegistration 으로 방어
				if ("serviceWorker" in navigator) {
					swReg = await navigator.serviceWorker.getRegistration();
					if (!swReg) {
						console.warn("[togglePush] SW 미등록, 푸시 구독 로직을 건너뜁니다.");
					}
				}

				if (on && swReg) {
					// 구독
					console.log("[togglePush] 구독 시도");
					const sub = await swReg.pushManager.subscribe({
						userVisibleOnly: true,
						applicationServerKey: urlBase64ToUint8Array(this.me.vapid_public_key),
					});
					const res = await fetch(`${BACKEND_BASE_URL}/push/subscribe/`, {
						method: "POST",
						headers: {
							"Content-Type": "application/json",
							Authorization: `Bearer ${token}`,
						},
						body: JSON.stringify(sub.toJSON()),
					});
					if (!res.ok) throw new Error("구독 API 실패");
					console.log("[togglePush] 구독 성공");
				} else {
					// 구독해제
					console.log("[togglePush] 구독 해제 시도");
					const sub = await swReg?.pushManager.getSubscription();
					if (sub) {
						await sub.unsubscribe();
						const res = await fetch(`${BACKEND_BASE_URL}/push/unsubscribe/`, {
							method: "POST",
							headers: {
								"Content-Type": "application/json",
								Authorization: `Bearer ${token}`,
							},
							body: JSON.stringify({ endpoint: sub.endpoint }),
						});
						if (!res.ok) throw new Error("구독해제 API 실패");
						console.log("[togglePush] 구독 해제 성공");
					}
				}

				console.log("[togglePush] 서버에 설정 저장 시도:", on);
				// 최종 서버 설정 저장
				const saveRes = await fetch(`${BACKEND_BASE_URL}/push/setting/`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
					body: JSON.stringify({ push_on: on }),
				});
				if (!saveRes.ok) throw new Error("설정 저장 실패");
				console.log("[togglePush] 설정 저장 성공");
			} catch (e) {
				console.error("[togglePush] 오류 발생, 롤백", e);
				this.me.push_on = prev; // 롤백
			} finally {
				this.isToggling = false;
				console.log("[togglePush] 완료, 최종 상태:", this.me.push_on);
			}
		},

		// 차량 조회
		async fetchMyVehicles() {
			const token = localStorage.getItem("access_token");
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
			const token = localStorage.getItem("access_token");
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
			const token = localStorage.getItem("access_token");
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
			const token = localStorage.getItem("access_token");
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
			const token = localStorage.getItem("access_token");
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

// VAPID 키 디코드 헬퍼
function urlBase64ToUint8Array(base64String: string) {
	const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
	const base64 = (base64String + padding).replace(/\-/g, "+").replace(/_/g, "/");
	const rawData = atob(base64);
	return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}
