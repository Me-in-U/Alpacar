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
		async fetchMe(accessToken: string) {
			const res = await fetch(`${BACKEND_BASE_URL}/users/me/`, {
				headers: {
					"Content-Type": "application/json",
					Authorization: `Bearer ${accessToken}`,
				},
			});
			if (!res.ok) throw new Error("프로필 조회 실패");
			const profile: User = await res.json();
			this.setUser(profile);
			return profile;
		},
		async login(email: string, password: string) {
			const res = await fetch(`${BACKEND_BASE_URL}/auth/login/`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ email, password }),
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail || "로그인 실패");

			localStorage.setItem("access_token", data.access);
			localStorage.setItem("refresh_token", data.refresh);

			await this.fetchMe(data.access);
			return this.me;
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
	},
});
