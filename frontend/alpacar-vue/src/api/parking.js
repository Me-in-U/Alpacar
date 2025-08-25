// src/api/parking.js

import axios from "axios";
import { BACKEND_BASE_URL, tryRefreshToken } from "@/utils/api";
import { SecureTokenManager } from "@/utils/security";

// API 기본 URL 설정 - utils/api.ts의 설정 사용
const API_BASE_URL = BACKEND_BASE_URL;

// axios 인스턴스 생성
export const apiClient = axios.create({
	baseURL: API_BASE_URL,
	timeout: 30000, // 30초 타임아웃으로 증가 (배포 환경 고려)
	headers: {
		"Content-Type": "application/json",
	},
	withCredentials: false, // CORS 문제 방지
});

// 동시 401 대응용
let isRefreshing = false;
let refreshQueue = [];

// 새 토큰이 준비되면 대기중 요청 재개
function resolveQueue(newAccess) {
	refreshQueue.forEach((cb) => cb(newAccess));
	refreshQueue = [];
}

// 요청 인터셉터 - 토큰 자동 추가 (SecureTokenManager 사용)
apiClient.interceptors.request.use(
	(config) => {
		const token = SecureTokenManager.getSecureToken("access_token");
		if (token) {
			config.headers.Authorization = `Bearer ${token}`;
			console.log("API Request with token:", config.method.toUpperCase(), config.url, "Token present:");
		} else {
			console.warn("API Request without token:", config.method.toUpperCase(), config.url);
		}
		return config;
	},
	(error) => {
		console.error("Request Error:", error);
		return Promise.reject(error);
	}
);

// 응답 인터셉터 - 에러 처리
apiClient.interceptors.response.use(
	(response) => {
		console.log("API Response:", response.config.url, response.status);
		return response;
	},
	async (error) => {
		console.error("Response Error:", error);
		console.error("API Base URL:", API_BASE_URL);

		// 401 처리 (refresh 로직 추가)
		if (error?.response?.status === 401 && !error.config._retry) {
			const originalRequest = error.config;
			originalRequest._retry = true;

			if (isRefreshing) {
				return new Promise((resolve, reject) => {
					refreshQueue.push((newAccess) => {
						if (newAccess) {
							originalRequest.headers.Authorization = `Bearer ${newAccess}`;
							resolve(apiClient(originalRequest));
						} else {
							reject(error);
						}
					});
				});
			}

			isRefreshing = true;
			const newAccess = await tryRefreshToken().catch(() => null);
			isRefreshing = false;
			resolveQueue(newAccess);

			if (newAccess) {
				apiClient.defaults.headers.common.Authorization = `Bearer ${newAccess}`;
				originalRequest.headers.Authorization = `Bearer ${newAccess}`;
				return apiClient(originalRequest);
			} else {
				error.message = "인증이 필요합니다. 다시 로그인해주세요.";
				return Promise.reject(error);
			}
		}

		if (error.code === "ECONNABORTED") {
			console.error("Request timeout");
			error.message = "요청 시간이 초과되었습니다. 다시 시도해주세요.";
		} else if (error.code === "ERR_NETWORK") {
			console.error("Network error detected");
			error.message = "서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.";
		} else if (error.response) {
			// 서버가 응답했지만 에러 상태 코드
			console.error("Error Status:", error.response.status);
			console.error("Error Data:", error.response.data);

			if (error.response.status === 504 || error.response.status === 502) {
				error.message = "서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.";
			} else if (error.response.status === 401) {
				error.message = "인증이 필요합니다. 다시 로그인해주세요.";
			} else if (error.response.status === 403) {
				error.message = "권한이 없습니다.";
			} else if (error.response.status === 404) {
				error.message = "요청한 리소스를 찾을 수 없습니다.";
			} else if (error.response.status >= 500) {
				error.message = "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
			}
		} else if (error.request) {
			// 요청은 보냈지만 응답을 받지 못함
			console.error("No response received:", error.request);
			console.error("Request URL:", error.config?.url);
			error.message = "서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.";
		}

		return Promise.reject(error);
	}
);

// 주차 관련 API
export const parkingAPI = {
	// 주차 이력 조회
	getParkingHistory() {
		return apiClient.get("/parking/history/");
	},

	// 주차 점수 히스토리 조회
	getParkingScoreHistory() {
		return apiClient.get("/parking/score-history/");
	},

	// 차트 데이터 조회
	getChartData() {
		return apiClient.get("/parking/chart-data/");
	},

	// 주차 배정 생성
	createParkingAssignment(data) {
		return apiClient.post("/parking/assign/", data);
	},

	// 주차 완료 처리
	completeParkingAssignment(assignmentId) {
		return apiClient.post(`/parking/complete/${assignmentId}/`);
	},
};
export default parkingAPI;
