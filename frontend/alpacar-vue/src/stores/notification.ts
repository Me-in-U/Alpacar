import { defineStore } from "pinia";
import { BACKEND_BASE_URL } from "@/utils/api";

export interface Notification {
	id: number;
	title: string;
	message: string;
	notification_type: 'parking_complete' | 'parking' | 'entry' | 'exit' | 'grade_upgrade' | 'system' | 'maintenance';
	data: Record<string, any>;
	is_read: boolean;
	created_at: string;
}

export interface NotificationResponse {
	count: number;
	next: string | null;
	previous: string | null;
	results: Notification[];
}

export const useNotificationStore = defineStore("notification", {
	state: () => ({
		notifications: [] as Notification[],
		unreadCount: 0,
		isLoading: false,
		hasMore: true,
		nextUrl: null as string | null,
	}),
	actions: {
		async fetchNotifications(refresh = false) {
			const token = localStorage.getItem("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");

			this.isLoading = true;

			try {
				// refresh가 true이면 처음부터 다시 로드
				const url = refresh || !this.nextUrl 
					? `${BACKEND_BASE_URL}/notifications/`
					: this.nextUrl;

				const res = await fetch(url, {
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
				});

				if (!res.ok) {
					throw new Error("알림 목록 조회 실패");
				}

				const data: NotificationResponse = await res.json();
				
				if (refresh) {
					this.notifications = data.results;
				} else {
					this.notifications.push(...data.results);
				}

				this.nextUrl = data.next;
				this.hasMore = data.next !== null;

				return data.results;
			} catch (error) {
				console.error("알림 조회 실패:", error);
				throw error;
			} finally {
				this.isLoading = false;
			}
		},

		async fetchUnreadCount() {
			const token = localStorage.getItem("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");

			try {
				const res = await fetch(`${BACKEND_BASE_URL}/notifications/unread-count/`, {
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
				});

				if (!res.ok) {
					throw new Error("읽지 않은 알림 개수 조회 실패");
				}

				const data = await res.json();
				this.unreadCount = data.unread_count;
				return data.unread_count;
			} catch (error) {
				console.error("읽지 않은 알림 개수 조회 실패:", error);
				throw error;
			}
		},

		async markAsRead(notificationId: number) {
			const token = localStorage.getItem("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");

			try {
				const res = await fetch(`${BACKEND_BASE_URL}/notifications/${notificationId}/`, {
					method: "PUT",
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
					body: JSON.stringify({ is_read: true }),
				});

				if (!res.ok) {
					throw new Error("알림 읽음 처리 실패");
				}

				// 스토어 상태 업데이트
				const notification = this.notifications.find(n => n.id === notificationId);
				if (notification && !notification.is_read) {
					notification.is_read = true;
					this.unreadCount = Math.max(0, this.unreadCount - 1);
				}

			} catch (error) {
				console.error("알림 읽음 처리 실패:", error);
				throw error;
			}
		},

		async deleteNotification(notificationId: number) {
			const token = localStorage.getItem("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");

			try {
				const res = await fetch(`${BACKEND_BASE_URL}/notifications/${notificationId}/delete/`, {
					method: "DELETE",
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
				});

				if (!res.ok) {
					throw new Error("알림 삭제 실패");
				}

				// 스토어 상태 업데이트
				const index = this.notifications.findIndex(n => n.id === notificationId);
				if (index !== -1) {
					const notification = this.notifications[index];
					if (!notification.is_read) {
						this.unreadCount = Math.max(0, this.unreadCount - 1);
					}
					this.notifications.splice(index, 1);
				}

			} catch (error) {
				console.error("알림 삭제 실패:", error);
				throw error;
			}
		},

		async deleteAllNotifications() {
			const token = localStorage.getItem("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");

			try {
				const res = await fetch(`${BACKEND_BASE_URL}/notifications/delete-all/`, {
					method: "DELETE",
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
				});

				if (!res.ok) {
					throw new Error("전체 알림 삭제 실패");
				}

				const data = await res.json();
				
				// 스토어 상태 초기화
				this.notifications = [];
				this.unreadCount = 0;
				this.hasMore = true;
				this.nextUrl = null;

				return data.deleted_count;
			} catch (error) {
				console.error("전체 알림 삭제 실패:", error);
				throw error;
			}
		},

		async markAllAsRead() {
			const token = localStorage.getItem("access_token");
			if (!token) throw new Error("로그인이 필요합니다.");

			try {
				const res = await fetch(`${BACKEND_BASE_URL}/notifications/mark-all-read/`, {
					method: "PUT",
					headers: {
						"Content-Type": "application/json",
						Authorization: `Bearer ${token}`,
					},
				});

				if (!res.ok) {
					throw new Error("전체 알림 읽음 처리 실패");
				}

				// 스토어 상태 업데이트
				this.notifications.forEach(notification => {
					notification.is_read = true;
				});
				this.unreadCount = 0;

			} catch (error) {
				console.error("전체 알림 읽음 처리 실패:", error);
				throw error;
			}
		},

		// 새 알림이 들어왔을 때 실시간으로 추가
		addNotification(notification: Notification) {
			this.notifications.unshift(notification);
			if (!notification.is_read) {
				this.unreadCount++;
			}
		},

		// 날짜 포맷팅 헬퍼
		formatDate(dateString: string): string {
			const date = new Date(dateString);
			const now = new Date();
			const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

			if (diffInHours < 1) {
				return "방금 전";
			} else if (diffInHours < 24) {
				return `${Math.floor(diffInHours)}시간 전`;
			} else if (diffInHours < 24 * 7) {
				return `${Math.floor(diffInHours / 24)}일 전`;
			} else {
				return date.toLocaleDateString('ko-KR', {
					year: 'numeric',
					month: 'long',
					day: 'numeric'
				});
			}
		},

		// 알림 타입별 아이콘 가져오기
		getNotificationIcon(type: string): string {
			switch (type) {
				case 'parking_complete':
					return '🚗';
				case 'parking':
					return '🅿️';
				case 'entry':
					return '🚪';
				case 'exit':
					return '🚗';
				case 'grade_upgrade':
					return '⭐';
				case 'system':
					return 'ℹ️';
				case 'maintenance':
					return '🔧';
				default:
					return '📢';
			}
		}
	},
});