<template>
	<div>
		<div class="page-wrapper">
			<AdminNavbar :showLogout="false" @test-modal="showModal = true" />

			<AdminAuthRequiredModal v-if="showModal" @close="showModal = false" />
			<div class="container">
				<p class="title">실시간 주차장 확인</p>
				<!-- 백엔드 api 연결 후 수정 예정 -->
				<div class="card">
					<div class="summary-box blue">
						<div class="label">전체 주차 공간</div>
						<div class="value">120개</div>
					</div>

					<div class="summary-box orange">
						<div class="label">사용중</div>
						<div class="value">87개</div>
					</div>

					<div class="summary-box green">
						<div class="label">빈 공간</div>
						<div class="value">33개</div>
					</div>

					<div class="summary-box purple">
						<div class="label">오늘 이용량</div>
						<div class="value">247대</div>
					</div>
				</div>

				<p class="subtitle">실시간 주차 현황</p>
				<div class="parking-lot">
					<!-- 차량 오버레이 -->
					<svg class="overlay" :width="MAP_W" :height="MAP_H">
						<g v-for="obj in vehicles" :key="obj.track_id">
							<!-- 회전 사각형 꼭짓점으로 폴리곤 그리기 -->
							<polygon :points="toPoints(obj.corners)" fill="none" stroke="#ff0" stroke-width="2" />
							<!-- ID 텍스트: 중심좌표 활용 -->
							<text :x="obj.center[0]" :y="obj.center[1]" font-size="36" fill="#ff0" text-anchor="middle">
								{{ obj.track_id }}
							</text>
						</g>
					</svg>
					<!-- 상단 구역 -->
					<div class="row top-row">
						<div class="slot" v-for="spot in ['A5', 'A4', 'A3']" :key="spot" :id="spot" :class="statusClass(spot)">
							{{ spot }}
						</div>
						<div class="aisle"></div>
						<div class="slot" v-for="spot in ['A2', 'A1']" :key="spot" :id="spot" :class="statusClass(spot)">
							{{ spot }}
						</div>
					</div>

					<!-- 분리선 -->
					<div class="divider"></div>

					<!-- 하단 구역 -->
					<div class="row bottom-row">
						<div class="slot" v-for="spot in ['B3', 'B2', 'B1']" :key="spot" :id="spot" :class="statusClass(spot)">
							{{ spot }}
						</div>
						<div class="aisle"></div>
						<div class="slot" v-for="spot in ['C3', 'C2', 'C1']" :key="spot" :id="spot" :class="statusClass(spot)">
							{{ spot }}
						</div>
					</div>
				</div>
				<div class="test-panel">
					<textarea v-model="testInput" rows="4" placeholder='{"A1":"occupied","B2":"free",…}'></textarea>
					<button @click="applyTest">테스트 적용</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { ref } from "vue";
import { defineComponent, reactive, onMounted, onBeforeUnmount } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";
import AdminAuthRequiredModal from "@/views/admin/AdminAuthRequiredModal.vue";
import { BACKEND_BASE_URL } from "@/utils/api";

const showModal = ref(false);
export default defineComponent({
	components: {
		AdminNavbar,
		AdminAuthRequiredModal, // ← 여기에 등록!
	},
	setup() {
		const statusMap = reactive<Record<string, string>>({
			A5: "free",
			A4: "free",
			A3: "free",
			A2: "occupied",
			A1: "reserved",
			B3: "free",
			B2: "free",
			B1: "free",
			C3: "free",
			C2: "free",
			C1: "free",
		});
		const testInput = ref(JSON.stringify(statusMap, null, 2));

		// 맵 크기 (CSS와 동일하게 설정)
		const MAP_W = 800;
		const MAP_H = 566;

		// 실시간 차량 데이터
		const vehicles = reactive<
			Array<{
				track_id: number;
				center: [number, number];
				corners: number[];
			}>
		>([]);
		let ws: WebSocket | null = null;
		const WSS_URL = `wss://i13e102.p.ssafy.io/ws/car-position/`;

		function connect() {
			ws = new WebSocket(WSS_URL);
			ws.onopen = () => {
				console.log("[WebSocket] ✅ Connected");
			};
			ws.onmessage = (e) => {
				console.log("[WebSocket] ◀ Message received");
				const data = JSON.parse(e.data);
				vehicles.splice(0, vehicles.length, ...data);
			};
			ws.onerror = (e) => {
				console.error("[WebSocket] ❌ Error:", e);
			};
			ws.onclose = () => {
				console.warn("[WebSocket] 🔒 Closed");
			};
		}

		onMounted(() => {
			connect();
		});

		onBeforeUnmount(() => ws?.close());

		// [x1,y1,x2,y2,…] → "x1,y1 x2,y2 …" 포맷으로 변환
		function toPoints(c: number[]) {
			const pts: string[] = [];
			for (let i = 0; i < c.length; i += 2) {
				pts.push(`${c[i]},${c[i + 1]}`);
			}
			return pts.join(" ");
		}

		function applyTest() {
			try {
				const obj = JSON.parse(testInput.value);
				Object.assign(statusMap, obj);
			} catch (e) {
				alert("JSON 형식이 올바르지 않습니다.");
			}
		}

		// 나중에 실제 소켓 연결 → statusMap[spot]=newStatus 로 업데이트
		function statusClass(spot: string) {
			return {
				"status-free": statusMap[spot] === "free",
				"status-occupied": statusMap[spot] === "occupied",
				"status-reserved": statusMap[spot] === "reserved",
			};
		}

		return { statusClass, showModal, statusMap, testInput, applyTest, MAP_W, MAP_H, vehicles, toPoints };
	},
});
</script>

<style scoped>
.parking-lot {
	position: relative;
	width: 800px;
	height: 566px;
	margin: 0 auto;
	background-color: #4c4c4c;
	border-radius: 14px;
	padding-top: 10px;
	padding-bottom: 10px;
}
.row {
	display: flex;
	justify-content: center;
	gap: 5px; /* 칸 사이 간격: 16px */
}
.top-row .slot,
.bottom-row .slot {
	width: 80px; /* 칸 너비: 80px */
	height: 160px; /* 칸 높이: 160px */
	border: 2px solid #fff;
	color: #fff;
	font-weight: 600;
	display: flex;
	align-items: center;
	justify-content: center;
	position: relative;
}
.divider {
	border-top: 4px dashed #fff;
	margin: 111px 0; /* 칸 높이 × 0.15 */
}
.aisle {
	width: 32px; /* 차도 폭 */
}
/* 테스트 패널 */
.test-panel {
	margin: 24px auto;
	width: 800px;
	display: flex;
	gap: 8px;
}
.test-panel textarea {
	flex: 1;
	font-family: monospace;
	padding: 8px;
}
.test-panel button {
	padding: 0 16px;
	background: #4c4c4c;
	color: #fff;
	border: none;
	border-radius: 4px;
	cursor: pointer;
}
/* 상태별 색상 */
.status-free {
	background: #9c9c9c;
} /* 초록 */
.status-occupied {
	background: #e75757;
} /* 빨강 */
.status-reserved {
	background: #f5dd29;
} /* 노랑 */
.page-wrapper {
	display: flex;
	flex-direction: column;
	min-height: 100vh; /* 화면 전체 높이 */
	background-color: #f3eeea; /* 페이지 배경색 */
}

/* SVG를 맵 위에 오버레이 */
.overlay {
	position: absolute;
	top: 0;
	left: 0;
	pointer-events: none;
	z-index: 3;
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
