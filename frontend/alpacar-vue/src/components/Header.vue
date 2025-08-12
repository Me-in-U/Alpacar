<template>
	<div class="header">
		<div class="logo" @click="goToMain">
			<img src="@/assets/home_logo.png" alt="Home Logo" class="logo-icon" />
		</div>
		<div class="notification" @click="openNotificationModal">
			<img src="@/assets/notification-bell.png" alt="Notification" class="notification-bell" />
			<span v-if="notificationStore.unreadCount > 0" class="notification-badge">
				{{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
			</span>
		</div>
	</div>

	<!-- Notification Modal -->
	<div v-if="showNotificationModal" class="modal-overlay" @click="showNotificationModal = false">
		<div class="modal-content" @click.stop>
			<div class="modal-header">
				<h2 class="modal-title">알림함</h2>
				<!-- 푸시 알림 설정 버튼 -->
				<label class="switch"> <input type="checkbox" v-model="pushOn" :disabled="userStore.isToggling" /><span class="slider"></span> </label>
			</div>

			<div class="notification-list">
				<div class="list-header">
					<div class="delete-all" @click="deleteAllNotifications">전체 삭제</div>
				</div>

				<!-- 로딩 상태 -->
				<div v-if="notificationStore.isLoading && notificationStore.notifications.length === 0" class="loading">
					알림을 불러오는 중...
				</div>

				<!-- 알림이 없는 경우 -->
				<div v-else-if="notificationStore.notifications.length === 0" class="no-notifications">
					알림이 없습니다.
				</div>

				<!-- 실제 알림 목록 -->
				<div v-else>
					<div 
						v-for="notification in notificationStore.notifications" 
						:key="notification.id"
						class="notification-item"
						:class="{ 'unread': !notification.is_read }"
						@click="handleNotificationClick(notification)"
					>
						<div class="notification-content">
							<div class="notification-header">
								<span class="notification-icon">{{ notificationStore.getNotificationIcon(notification.notification_type) }}</span>
								<h3 class="notification-title">{{ notification.title }}</h3>
								<span class="notification-time">{{ notificationStore.formatDate(notification.created_at) }}</span>
							</div>
							<div class="notification-message">
								<!-- 주차 완료 알림인 경우 특별한 형태로 표시 -->
								<div v-if="notification.notification_type === 'parking_complete'">
									<p class="notification-text">주차 일시: {{ formatParkingTime(notification.data.parking_time) }}</p>
									<p class="notification-text">주차 공간: {{ notification.data.parking_space || 'A4' }}</p>
								</div>
								<!-- 기타 알림 -->
								<div v-else>
									<p class="notification-text">{{ notification.message }}</p>
								</div>
							</div>
						</div>
						<div class="delete-button" @click.stop="deleteNotification(notification.id)">삭제</div>
					</div>

					<!-- 더보기 버튼 -->
					<div v-if="notificationStore.hasMore" class="load-more">
						<button @click="loadMoreNotifications" :disabled="notificationStore.isLoading" class="load-more-button">
							{{ notificationStore.isLoading ? '로딩 중...' : '더보기' }}
						</button>
					</div>
				</div>
			</div>

			<div class="modal-footer">
				<button class="close-button" @click="showNotificationModal = false">닫기</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { useNotificationStore, type Notification } from "@/stores/notification";

const router = useRouter();
const showNotificationModal = ref(false);
const userStore = useUserStore();
const notificationStore = useNotificationStore();

const pushOn = computed<boolean>({
	get: () => userStore.me?.push_on ?? false,
	set: (value: boolean) => {
		userStore.togglePush(value);
	},
});

const goToMain = () => {
	router.push("/main");
};

const openNotificationModal = async () => {
	showNotificationModal.value = true;
	try {
		// 알림 목록 새로고침
		await notificationStore.fetchNotifications(true);
	} catch (error) {
		console.error("알림 목록 로드 실패:", error);
	}
};

const markAsRead = async (notificationId: number) => {
	try {
		await notificationStore.markAsRead(notificationId);
	} catch (error) {
		console.error("알림 읽음 처리 실패:", error);
	}
};

const handleNotificationClick = async (notification: Notification) => {
	try {
		// 알림을 읽음으로 표시
		await notificationStore.markAsRead(notification.id);
		
		// 주차 관련 알림인 경우 parking-recommend 페이지로 리다이렉트
		if (notification.notification_type === 'parking' ||
			notification.title?.includes('주차 배정') ||
			notification.message?.includes('주차 배정')) {
			
			// 모달 닫기
			showNotificationModal.value = false;
			
			// parking-recommend 페이지로 이동
			router.push('/parking-recommend');
		}
	} catch (error) {
		console.error("알림 처리 실패:", error);
	}
};

const deleteNotification = async (id: number) => {
	try {
		await notificationStore.deleteNotification(id);
	} catch (error) {
		console.error("알림 삭제 실패:", error);
		alert("알림 삭제에 실패했습니다.");
	}
};

const deleteAllNotifications = async () => {
	if (!confirm("모든 알림을 삭제하시겠습니까?")) {
		return;
	}

	try {
		const deletedCount = await notificationStore.deleteAllNotifications();
		alert(`${deletedCount}개의 알림이 삭제되었습니다.`);
	} catch (error) {
		console.error("전체 알림 삭제 실패:", error);
		alert("알림 삭제에 실패했습니다.");
	}
};

const loadMoreNotifications = async () => {
	try {
		await notificationStore.fetchNotifications();
	} catch (error) {
		console.error("추가 알림 로드 실패:", error);
	}
};

const formatParkingTime = (timeString: string | undefined): string => {
	if (!timeString) return '';
	
	try {
		const date = new Date(timeString);
		return date.toLocaleString('ko-KR', {
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
			hour: '2-digit',
			minute: '2-digit',
		});
	} catch (error) {
		return timeString;
	}
};

// 컴포넌트 마운트 시 읽지 않은 알림 개수 조회
onMounted(async () => {
	if (userStore.me) {
		try {
			await notificationStore.fetchUnreadCount();
		} catch (error) {
			console.error("읽지 않은 알림 개수 조회 실패:", error);
		}
	}
});

</script>

<style scoped>
/* Header */
.header {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 60px;
	background: #776b5d;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 20px;
	z-index: 10;
}

.logo {
	cursor: pointer;
}

.logo-icon {
	width: 35px;
	height: 35px;
	object-fit: contain;
}

.notification {
	position: relative;
	cursor: pointer;
}

.notification-bell {
	width: 20px;
	height: 20px;
	object-fit: contain;
}

.notification-badge {
	position: absolute;
	top: -5px;
	right: -5px;
	background: #ff4757;
	color: white;
	border-radius: 10px;
	padding: 2px 6px;
	font-size: 10px;
	font-weight: bold;
	min-width: 16px;
	text-align: center;
}

/* Modal Styles */
.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: flex-start;
	justify-content: center;
	z-index: 1000;
	padding-top: 80px; /* 헤더 높이만큼 상단 패딩 */
}

.modal-content {
	width: 440px;
	height: 500px;
	background-color: #f3eeea;
	border-radius: 12px;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.modal-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20px 30px;
	border-bottom: 1px solid #e5e5e5;
}

.modal-title {
	color: #000000;
	font-size: 24px;
	font-weight: 600;
	font-family: "Inter", sans-serif;
	margin: 0;
}

.list-header {
	display: flex;
	justify-content: flex-end;
	margin-bottom: 10px;
}

.delete-all {
	color: #000000;
	font-size: 12px;
	font-weight: 400;
	font-family: "Inter", sans-serif;
	cursor: pointer;
	padding: 5px 10px;
	border-radius: 4px;
	transition: background-color 0.3s ease;
}

.delete-all:hover {
	background-color: rgba(0, 0, 0, 0.1);
}

.loading, .no-notifications {
	text-align: center;
	color: #666;
	font-size: 14px;
	padding: 40px 20px;
	font-family: "Inter", sans-serif;
}

.notification-header {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 5px;
}

.notification-icon {
	font-size: 16px;
}

.notification-time {
	margin-left: auto;
	color: #666;
	font-size: 11px;
	font-family: "Inter", sans-serif;
}

.notification-message {
	margin-top: 5px;
}

.notification-item.unread {
	border-left: 4px solid #776b5d;
	background: #f0ede8;
}

.load-more {
	text-align: center;
	margin-top: 15px;
}

.load-more-button {
	background: #776b5d;
	color: white;
	border: none;
	border-radius: 6px;
	padding: 8px 16px;
	cursor: pointer;
	font-size: 12px;
	font-family: "Inter", sans-serif;
	transition: background-color 0.3s ease;
}

.load-more-button:hover:not(:disabled) {
	background: #665a4d;
}

.load-more-button:disabled {
	opacity: 0.6;
	cursor: not-allowed;
}

.notification-list {
	flex: 1;
	padding: 20px 30px;
	overflow-y: auto;
	display: flex;
	flex-direction: column;
	gap: 20px;
}

.notification-item {
	background: #ebe3d5;
	border: 1px solid #b3b3b3;
	border-radius: 10px;
	padding: 15px;
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	gap: 15px;
}

.notification-content {
	flex: 1;
}

.notification-title {
	color: #000000;
	font-size: 18px;
	font-weight: 400;
	font-family: "Inter", sans-serif;
	margin: 0 0 5px 0;
	line-height: 1.2;
}

.notification-text {
	color: #000000;
	font-size: 18px;
	font-weight: 400;
	font-family: "Inter", sans-serif;
	margin: 0;
	line-height: 1.2;
}

.delete-button {
	color: #000000;
	font-size: 12px;
	font-weight: 400;
	font-family: "Inter", sans-serif;
	cursor: pointer;
	padding: 5px 10px;
	border-radius: 4px;
	transition: background-color 0.3s ease;
	white-space: nowrap;
}

.delete-button:hover {
	background-color: rgba(0, 0, 0, 0.1);
}

.modal-footer {
	padding: 20px 30px;
	border-top: 1px solid #e5e5e5;
	display: flex;
	justify-content: center;
}

.close-button {
	width: 280px;
	height: 50px;
	background-color: #776b5d;
	color: #ffffff;
	border: none;
	border-radius: 8px;
	font-size: 16px;
	font-weight: 600;
	font-family: "Inter", sans-serif;
	cursor: pointer;
	transition: all 0.3s ease;
}

.close-button:hover {
	background-color: #665a4d;
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}

/* Switch */
.switch {
	position: relative;
	display: inline-block;
	width: 50px;
	height: 24px;
	margin-left: 16px;
}
.switch input {
	opacity: 0;
	width: 0;
	height: 0;
}
.slider {
	position: absolute;
	inset: 0;
	background: #ccc;
	border-radius: 24px;
	transition: 0.4s;
}
.slider:before {
	content: "";
	position: absolute;
	width: 18px;
	height: 18px;
	left: 3px;
	bottom: 3px;
	background: #fff;
	border-radius: 50%;
	transition: 0.4s;
}
.switch input:checked + .slider {
	background: #66bb6a;
}
.switch input:checked + .slider:before {
	transform: translateX(26px);
}

/* Responsive Design */
@media (max-width: 440px) {
	.modal-overlay {
		align-items: flex-start;
		padding-top: 0; /* 모바일에서는 패딩 제거 */
	}

	.modal-content {
		width: 100vw;
		height: calc(100vh - 160px); /* 헤더(80px) + 하단 네비게이션바(80px) 제외 */
		border-radius: 0;
		margin-top: 80px; /* 헤더 높이만큼 상단 마진 */
		max-height: calc(100vh - 160px);
	}

	.modal-header {
		padding: 20px;
		flex-shrink: 0;
	}

	.notification-list {
		padding: 20px;
		flex: 1;
		overflow-y: auto;
	}

	.modal-footer {
		padding: 20px;
		padding-bottom: 30px; /* 닫기 버튼 하단 여유 공간 추가 */
		flex-shrink: 0;
	}
}

@media (min-width: 441px) {
	.modal-content {
		width: 440px;
		margin: 0 auto;
	}
}
</style>
