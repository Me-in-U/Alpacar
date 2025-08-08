<template>
	<div class="header">
		<div class="logo" @click="goToMain">
			<img src="@/assets/home_logo.png" alt="Home Logo" class="logo-icon" />
		</div>
		<div class="notification" @click="showNotificationModal = true">
			<img src="@/assets/notification-bell.png" alt="Notification" class="notification-bell" />
		</div>
	</div>

	<!-- Notification Modal -->
	<div v-if="showNotificationModal" class="modal-overlay" @click="showNotificationModal = false">
		<div class="modal-content" @click.stop>
			<div class="modal-header">
				<div class="header-left">
					<h2 class="modal-title">알림함</h2>
				</div>
				<div class="header-right">
					<!-- 푸시 알림 상태 표시 -->
					<div class="push-status">
						<div class="push-info">
							<span class="push-label">푸시 알림</span>
							<span class="push-status-text" :class="getPushStatusClass(pushStatus)">
								{{ getPushStatusText(pushStatus) }}
							</span>
						</div>
						<label class="switch"> 
							<input type="checkbox" v-model="pushOn" :disabled="userStore.isToggling" />
							<span class="slider"></span> 
						</label>
					</div>
				</div>
			</div>

			<div class="notification-list">
				<div class="list-actions">
					<button v-if="pushOn" class="test-button" @click="sendTestNotification">테스트 알림</button>
					<div class="delete-all" @click="deleteAllNotifications">전체 삭제</div>
				</div>
				<!-- 주차 완료 알림 -->
				<div class="notification-item">
					<div class="notification-content">
						<h3 class="notification-title">주차 완료 알림</h3>
						<p class="notification-text">주차 일시 : 2025-07-20 16:00</p>
						<p class="notification-text">주차 공간 : A4</p>
					</div>
					<div class="delete-button" @click="deleteNotification(1)">삭제</div>
				</div>

				<!-- 등급 승급 알림 -->
				<div class="notification-item">
					<div class="notification-content">
						<h3 class="notification-title">등급 승급 알림</h3>
						<p class="notification-text">주차 등급이 초급자 에서 중급자 로 승급되었습니다</p>
					</div>
					<div class="delete-button" @click="deleteNotification(2)">삭제</div>
				</div>
			</div>

			<div class="modal-footer">
				<button class="close-button" @click="showNotificationModal = false">닫기</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { showLocalNotification } from "@/utils/pwa";
import { BACKEND_BASE_URL } from "@/utils/api";
import { checkPushStatus, sendTestPushNotification, getPushStatusText, getPushStatusClass, type PushStatus } from "@/utils/pushNotification";

const router = useRouter();
const showNotificationModal = ref(false);
const userStore = useUserStore();
const pushStatus = ref<PushStatus>({
	isEnabled: false,
	hasPermission: false,
	hasSubscription: false
});

const pushOn = computed<boolean>({
	get: () => userStore.me?.push_on ?? false,
	set: async (value: boolean) => {
		try {
			await userStore.togglePush(value);
			
			// 푸시 상태 업데이트
			await updatePushStatus();
			
			// 푸시 알림이 활성화되었을 때 테스트 알림 표시
			if (value) {
				setTimeout(() => {
					showLocalNotification({
						type: 'general',
						title: '🔔 푸시 알림 활성화',
						body: '알림 설정이 완료되었습니다!'
					});
				}, 1000);
			}
		} catch (error: any) {
			console.error('Push toggle error:', error);
			alert(error.message || '푸시 알림 설정 중 오류가 발생했습니다.');
		}
	},
});

const goToMain = () => {
	router.push("/main");
};

const deleteNotification = (id: number) => {
	console.log("알림 삭제:", id);
	// 실제로는 API 호출로 알림을 삭제
};

const deleteAllNotifications = () => {
	console.log("전체 알림 삭제");
	// 실제로는 API 호출로 모든 알림을 삭제
};

const sendTestNotification = async () => {
	try {
		// 로컬 테스트 알림 발송
		await showLocalNotification({
			type: 'general',
			title: '🚗 로컬 테스트 알림',
			body: '브라우저에서 직접 표시되는 알림입니다!',
			requireInteraction: true
		});

		// 서버를 통한 실제 푸시 알림 테스트
		try {
			await sendTestPushNotification('🎉 서버 테스트 알림', '서버에서 보낸 푸시 알림입니다!');
			console.log('서버 테스트 알림 전송 성공');
		} catch (error: any) {
			console.warn('서버 테스트 알림 오류:', error.message);
		}

		// 푸시 상태 업데이트
		await updatePushStatus();
	} catch (error: any) {
		console.error('테스트 알림 발송 실패:', error);
		alert(`테스트 알림 발송에 실패했습니다: ${error.message}`);
	}
};

const updatePushStatus = async () => {
	try {
		const status = await checkPushStatus();
		pushStatus.value = status;
		console.log('Push status updated:', status);
	} catch (error) {
		console.error('Push status update failed:', error);
	}
};

// 컴포넌트 마운트 시 푸시 상태 확인
onMounted(async () => {
	await updatePushStatus();
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
	cursor: pointer;
}

.notification-bell {
	width: 20px;
	height: 20px;
	object-fit: contain;
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

.header-left {
	flex: 1;
}

.header-right {
	display: flex;
	align-items: center;
}

.push-status {
	display: flex;
	align-items: center;
	gap: 12px;
}

.push-info {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2px;
}

.push-label {
	font-size: 14px;
	font-weight: 500;
	color: #333;
	white-space: nowrap;
}

.push-status-text {
	font-size: 11px;
	font-weight: 400;
	padding: 2px 6px;
	border-radius: 10px;
	white-space: nowrap;
}

.push-status-text.status-active {
	color: #2e7d32;
	background-color: rgba(76, 175, 80, 0.1);
}

.push-status-text.status-warning {
	color: #f57c00;
	background-color: rgba(255, 152, 0, 0.1);
}

.push-status-text.status-inactive {
	color: #757575;
	background-color: rgba(117, 117, 117, 0.1);
}

.modal-title {
	color: #000000;
	font-size: 24px;
	font-weight: 600;
	font-family: "Inter", sans-serif;
	margin: 0;
}

.list-actions {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
	gap: 10px;
}

.test-button {
	background: #4CAF50;
	color: white;
	border: none;
	padding: 8px 16px;
	border-radius: 6px;
	font-size: 12px;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.3s ease;
	white-space: nowrap;
}

.test-button:hover {
	background: #45a049;
	transform: translateY(-1px);
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
	margin-left: auto;
}

.delete-all:hover {
	background-color: rgba(0, 0, 0, 0.1);
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
