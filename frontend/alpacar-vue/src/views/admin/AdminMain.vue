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
						<div class="value">{{ totalSlots }}개</div>
					</div>
					<div class="summary-box orange">
						<div class="label">사용중</div>
						<div class="value">{{ occupiedCount }}개</div>
					</div>
					<div class="summary-box green">
						<div class="label">빈 공간</div>
						<div class="value">{{ freeCount }}개</div>
					</div>
					<div class="summary-box yellow">
						<div class="label">예약됨</div>
						<div class="value">{{ reservedCount }}개</div>
					</div>
					<div class="summary-box purple">
						<div class="label">오늘 이용량</div>
						<div class="value">{{ usageToday }}대</div>
					</div>
				</div>

				<p class="subtitle">실시간 주차 현황</p>
				<div class="parking-lot">
					<!-- 차량 오버레이 -->
					<svg class="overlay" :width="MAP_W" :height="MAP_H">
						<g v-for="obj in vehicles" :key="obj.track_id">
							<polygon :points="toPoints(obj.corners)" fill="none" stroke="#ff0" stroke-width="2" />
							<text :x="obj.center[0]" :y="obj.center[1]" font-size="36" fill="#ff0" text-anchor="middle">
								{{ obj.track_id }}
							</text>
						</g>
					</svg>

					<!-- 상단 구역 -->
					<div class="row top-row">
						<div class="slot" v-for="spot in ['A5', 'A4', 'A3']" :key="spot" :id="spot" :class="statusClass(spot)">
							<span class="slot-label">{{ spot }}</span>
							<div class="slot-actions">
								<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
							</div>
						</div>

						<div class="aisle"></div>

						<div class="slot" v-for="spot in ['A2', 'A1']" :key="spot" :id="spot" :class="statusClass(spot)">
							<span class="slot-label">{{ spot }}</span>
							<div class="slot-actions">
								<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
							</div>
						</div>
					</div>

					<!-- 분리선 -->
					<div class="divider"></div>

					<!-- 하단 구역 -->
					<div class="row bottom-row">
						<div class="slot" v-for="spot in ['B3', 'B2', 'B1']" :key="spot" :id="spot" :class="statusClass(spot)">
							<span class="slot-label">{{ spot }}</span>
							<div class="slot-actions">
								<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
							</div>
						</div>

						<div class="aisle"></div>

						<div class="slot" v-for="spot in ['C3', 'C2', 'C1']" :key="spot" :id="spot" :class="statusClass(spot)">
							<span class="slot-label">{{ spot }}</span>
							<div class="slot-actions">
								<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
								<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
							</div>
						</div>
					</div>
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
			A2: "free",
			A1: "free",
			B3: "free",
			B2: "free",
			B1: "free",
			C3: "free",
			C2: "free",
			C1: "free",
		});

		// 합계 상태
		const totalSlots = ref(0);
		const occupiedCount = ref(0);
		const freeCount = ref(0);
		const reservedCount = ref(0);
		const usageToday = ref(0); // 백엔드에서 가져옴

		function recomputeTotals() {
			const statuses = Object.values(statusMap);
			totalSlots.value = Object.keys(statusMap).length;
			occupiedCount.value = statuses.filter((s) => s === "occupied").length;
			freeCount.value = statuses.filter((s) => s === "free").length;
			reservedCount.value = statuses.filter((s) => s === "reserved").length;
		}

		async function fetchUsageToday() {
			const token = localStorage.getItem("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/parking/stats/today/`, {
				headers: { Authorization: `Bearer ${token}` },
			});
			if (res.ok) {
				const d = await res.json();
				usageToday.value = d.usage_today; // 백엔드 정의에 맞춤
				console.log("오늘 이용량:", usageToday.value);
			}
		}

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
		let wsCar: WebSocket | null = null;
		let wsSpace: WebSocket | null = null;

		let usageTimer: number;

		const WSS_CAR_URL = `wss://i13e102.p.ssafy.io/ws/car-position/`;
		const WSS_SPACE_URL = `wss://i13e102.p.ssafy.io/ws/parking-space/`;

		function connectCar() {
			wsCar = new WebSocket(WSS_CAR_URL);
			wsCar.onopen = () => console.log("[Car WS] ✅ Connected");
			wsCar.onmessage = (e) => {
				const data = JSON.parse(e.data);
				vehicles.splice(0, vehicles.length, ...data);
			};
			wsCar.onerror = (e) => console.error("[Car WS] ❌ Error:", e);
			wsCar.onclose = () => console.warn("[Car WS] 🔒 Closed");
		}

		function connectSpace() {
			wsSpace = new WebSocket(WSS_SPACE_URL);
			wsSpace.onopen = () => console.log("[Space WS] ✅ Connected");
			wsSpace.onmessage = (e) => {
				const payload = JSON.parse(e.data) as Record<string, { status: string; size: string }>;
				console.log("[Space WS] 📦 Data:", payload);
				Object.entries(payload).forEach(([slot, info]) => {
					// info.status: "free" | "occupied" | "reserved"
					statusMap[slot] = info.status;
				});
				recomputeTotals(); // ← 합계 갱신
			};

			wsSpace.onerror = (e) => console.error("[Space WS] ❌ Error:", e);
			wsSpace.onclose = () => console.warn("[Space WS] 🔒 Closed");
		}

		onMounted(() => {
			connectCar();
			connectSpace();
			recomputeTotals();
			fetchUsageToday();
			usageTimer = window.setInterval(fetchUsageToday, 5000);
		});

		onBeforeUnmount(() => {
			wsCar?.close();
			wsSpace?.close();
			clearInterval(usageTimer);
		});

		// [x1,y1,x2,y2,…] → "x1,y1 x2,y2 …" 포맷으로 변환
		function toPoints(c: number[]) {
			const pts: string[] = [];
			for (let i = 0; i < c.length; i += 2) {
				pts.push(`${c[i]},${c[i + 1]}`);
			}
			return pts.join(" ");
		}

		function parseSpot(spot: string) {
			// "A12" → { zone:"A", slot_number:12 }
			return { zone: spot[0], slot_number: Number(spot.slice(1)) };
		}
		async function setSlot(spot: string, status: "free" | "occupied" | "reserved") {
			const token = localStorage.getItem("access_token");
			const { zone, slot_number } = parseSpot(spot);
			const prev = statusMap[spot];
			statusMap[spot] = status;
			recomputeTotals(); // 낙관적 갱신
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/parking/space/set-status/`, {
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({ zone, slot_number, status }),
				});
				if (!res.ok) throw new Error(await res.text());
			} catch (e) {
				console.error(e);
				statusMap[spot] = prev; // 롤백
				recomputeTotals(); // 롤백 반영
				alert("상태 변경 실패");
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

		return { statusClass, showModal, statusMap, MAP_W, MAP_H, vehicles, toPoints, reservedCount, setSlot, totalSlots, occupiedCount, freeCount, usageToday };
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
	box-sizing: border-box;
}
.row {
	display: flex;
	justify-content: center;
	gap: 5px;
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
	box-sizing: border-box;
	overflow: hidden;
}

/* 도로 분리선/차도 */
.divider {
	border-top: 4px dashed #fff;
	margin: 111px 0; /* 슬롯 높이(160px) 기준 적당한 간격 */
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
} /* 빈자리 */
.status-occupied {
	background: #e75757;
} /* 사용중 */
.status-reserved {
	background: #f5dd29;
} /* 예약 */

.page-wrapper {
	display: flex;
	flex-direction: column;
	min-height: 100vh; /* 화면 전체 높이 */
	background-color: #f3eeea; /* 페이지 배경색 */
}

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
.yellow {
	background-color: #fffbe5;
	border-color: #e5deb2;
}

.slot {
	position: relative;
}

/* 슬롯 버튼: 바닥 중앙 고정 */
.slot-actions {
	position: absolute;
	left: 4px;
	right: 4px;
	bottom: 4px;
	display: flex;
	gap: 4px;
	justify-content: center;
	z-index: 2;
}

/* 슬롯 라벨: 위쪽 중앙 고정 */
.slot-label {
	position: absolute;
	top: 8px;
	left: 0;
	right: 0;
	text-align: center;
	pointer-events: none; /* 클릭 방해 제거 */
	z-index: 1;
}

.btn-mini {
	padding: 2px 6px;
	border: none;
	border-radius: 3px;
	font-size: 12px;
	cursor: pointer;
	background: #222;
	color: #fff;
	opacity: 0.9;
}
.btn-mini:hover {
	opacity: 1;
}
.btn-mini:hover {
	opacity: 1;
}
</style>
