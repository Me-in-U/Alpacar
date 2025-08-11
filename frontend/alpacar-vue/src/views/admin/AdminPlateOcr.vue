<template>
	<div>
		<div class="page-wrapper">
			<AdminNavbar :showLogout="false" @test-modal="showModal = true" />

			<AdminAuthRequiredModal v-if="showModal" @close="showModal = false" />

			<div class="container">
				<p class="title">차단바 CCTV</p>

				<div class="stream-card">
					<div class="stream-header">
						<span class="live-dot"></span>
						<span class="live-text">LIVE</span>
					</div>

					<div class="video-wrap" :class="{ 'is-loading': !videoSrc }">
						<img v-if="videoSrc" :src="videoSrc" alt="라이브 영상" class="video" />
						<!-- 로딩 스켈레톤 -->
						<div v-else class="video-skeleton" aria-hidden="true"></div>

						<!-- OCR 칩 (오버레이) -->
						<div class="ocr-chip" :class="{ 'is-waiting': plateText === '대기 중...' }" title="OCR 결과">
							{{ plateText }}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { ref, onMounted, onUnmounted, defineComponent } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";
import AdminAuthRequiredModal from "@/views/admin/AdminAuthRequiredModal.vue";

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
			ws = new WebSocket(`https://i13e102.p.ssafy.io/ws/stream/`);
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
} /* 카드 컨테이너 */
.stream-card {
	width: 100%;
	max-width: 830px;
	background: #faf8f5;
	border: 1px solid #e6dfd6;
	border-radius: 16px;
	box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
	padding: 16px 16px 20px;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

/* 상단 LIVE 헤더 */
.stream-header {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	align-self: flex-start;
	background: #fff;
	border: 1px solid #eadfd2;
	border-radius: 999px;
	padding: 8px 12px;
	font-weight: 800;
	color: #6b6257;
	letter-spacing: 0.2px;
}

.live-dot {
	width: 10px;
	height: 10px;
	border-radius: 50%;
	background: #e74c3c;
	box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.6);
	animation: livePulse 1.6s ease-out infinite;
}
@keyframes livePulse {
	0% {
		box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.6);
	}
	70% {
		box-shadow: 0 0 0 12px rgba(231, 76, 60, 0);
	}
	100% {
		box-shadow: 0 0 0 0 rgba(231, 76, 60, 0);
	}
}

.live-text {
	font-size: 12px;
}

/* 비디오 박스 */
.video-wrap {
	position: relative;
	width: 100%;
	max-width: 830px; /* 최대 폭 제한 */
	aspect-ratio: 4 / 3; /* 4:3 비율 유지 */
	border-radius: 12px;
	overflow: hidden;
	background: #000;
	border: 1px solid #e6dfd6;
}

/* 실제 영상 */
.video {
	display: block;
	width: 100%;
	height: 100%;
	object-fit: cover; /* 비율 맞추면서 꽉 채우기 */
}

/* 로딩 스켈레톤 */
.video-skeleton {
	width: 100%;
	height: 100%;
	background: linear-gradient(90deg, #eee8e0 25%, #f6f2ec 37%, #eee8e0 63%);
	background-size: 400% 100%;
	animation: shimmer 1.4s ease infinite;
	border-radius: 12px;
}
@keyframes shimmer {
	0% {
		background-position: 100% 0;
	}
	100% {
		background-position: 0 0;
	}
}

/* OCR 결과 칩 (오버레이) */
.ocr-chip {
	position: absolute;
	left: 12px;
	bottom: 12px;
	display: inline-flex;
	align-items: center;
	gap: 8px;
	max-width: calc(100% - 24px);
	padding: 8px 12px;
	border-radius: 999px;
	backdrop-filter: blur(4px);
	background: rgba(255, 255, 255, 0.86);
	border: 1px solid rgba(214, 204, 192, 0.8);
	color: #2c2c2c;
	font-weight: 800;
	font-size: 14px;
	letter-spacing: 0.2px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

/* 대기 상태 색감 */
.ocr-chip.is-waiting {
	background: rgba(250, 248, 245, 0.92);
	color: #6b6257;
	border-color: #eadfd2;
}

/* 컨테이너 기본 여백 조정(이미 있으면 유지) */
.container {
	align-items: center; /* 가운데 정렬 */
}

/* 반응형 */
@media (max-width: 720px) {
	.stream-card {
		padding: 12px;
		border-radius: 14px;
	}
	.ocr-chip {
		left: 10px;
		bottom: 10px;
		font-size: 13px;
	}
}
</style>
