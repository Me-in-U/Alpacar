<template>
	<div>
		<div class="page-wrapper">
			<AdminNavbar :showLogout="false" @test-modal="showModal = true" />

			<AdminAuthRequiredModal v-if="showModal" @close="showModal = false" />

			<div class="container">
				<p class="title">차단바 CCTV</p>
				<!-- WebSocket 스트리밍 결과 표시 -->
				<img :src="videoSrc" width="640" height="480" alt="라이브 영상" />
				<p>
					OCR: <span class="value">{{ plateText }}</span>
				</p>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { ref, onMounted, onUnmounted, defineComponent } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";
import AdminAuthRequiredModal from "@/views/admin/AdminAuthRequiredModal.vue";
import { BACKEND_BASE_URL } from "@/utils/api";

export default defineComponent({
	name: "AdminMain",
	components: {
		AdminNavbar,
		AdminAuthRequiredModal,
	},
	setup() {
		const showModal = ref(false);

		// WebSocket 관련 state
		const videoSrc = ref(""); // data:image/jpeg;base64,... 형태
		const plateText = ref("대기 중...");

		let ws: WebSocket | null = null;

		onMounted(() => {
			ws = new WebSocket(`${BACKEND_BASE_URL}/ws/stream/`);
			ws.onopen = () => {
				console.log("[WebSocket] ✅ Connected");
			};
			ws.onmessage = (evt) => {
				try {
					const { image, text } = JSON.parse(evt.data);
					videoSrc.value = "data:image/jpeg;base64," + image;
					plateText.value = text;
				} catch (e) {
					console.error("[WebSocket] 데이터 파싱 실패:", e);
				}
			};
			ws.onerror = (evt) => {
				console.error("[WebSocket] ❌ Error:", evt);
			};
			ws.onclose = (evt) => {
				console.warn("[WebSocket] 🔒 Closed:", evt);
			};
		});

		onUnmounted(() => {
			if (ws) ws?.close();
		});

		return {
			showModal,
			videoSrc,
			plateText,
		};
	},
});
</script>

<style scoped>
.page-wrapper {
	display: flex;
	flex-direction: column;
	min-height: 100vh; /* 화면 전체 높이 */
	background-color: #f3eeea; /* 페이지 배경색 */
}

.container {
	background-color: #f3eeea;
	min-height: calc(100vh - 64px); /* 네비게이션바 높이 감안 */
	padding: 48px 64px;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.title {
	font-size: 36px;
	font-weight: 700;
	font-family: "Inter-Bold", Helvetica;
	color: #333333;
	margin-bottom: 32px;
	align-self: flex-start;
}

.subtitle {
	font-size: 24px;
	font-weight: 600;
	color: #4c4c4c;
	margin-top: 48px;
	align-self: flex-start;
}

/* 카드 섹션 */
.card {
	background-color: #faf8f5;
	border-radius: 12px;
	padding: 24px;
	display: flex;
	gap: 24px;
	box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
	width: 100%;
	max-width: 1200px;
	box-sizing: border-box;
	flex-wrap: wrap;
	justify-content: center;
}

/* 각 박스 */
.summary-box {
	flex: 1 1 220px;
	height: 140px;
	border-radius: 8px;
	padding: 16px;
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	box-sizing: border-box;
	border: 1px solid #ccc;
	text-align: center;
}

.label {
	font-size: 16px;
	font-weight: 600;
	color: #4c4c4c;
}

.value {
	font-size: 28px;
	font-weight: 700;
	color: #333;
}

/* 색상 스타일 */
.blue {
	background-color: #e5f2ff;
	border-color: #b2cce5;
}
.orange {
	background-color: #fff2e5;
	border-color: #e5ccb2;
}
.green {
	background-color: #f2fff2;
	border-color: #b2e5b2;
}
.purple {
	background-color: #fff2ff;
	border-color: #e5b2e5;
}
</style>
