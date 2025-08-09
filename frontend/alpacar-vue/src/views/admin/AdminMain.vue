<template>
	<div>
		<div class="page-wrapper">
			<AdminNavbar :showLogout="false" @test-modal="showModal = true" />
			<AdminAuthRequiredModal v-if="showModal" @close="showModal = false" />

			<div class="container">
				<p class="title">실시간 주차장 확인</p>

				<!-- ==== 상단 요약 카드: 실시간(웹소켓/폴링) 값 반영 ==== -->
				<div class="summary-grid">
					<div v-for="c in cards" :key="c.key" class="summary-card" :class="c.color">
						<div class="card-top">
							<span class="icon">{{ c.icon }}</span>
							<span class="live-dot" v-if="c.live"></span>
						</div>
						<div class="card-title">{{ c.title }}</div>
						<div class="card-value">
							{{ c.value }}<span class="unit">{{ c.unit }}</span>
						</div>
					</div>
				</div>

				<!-- ==== 지도: CSS 변수로 모든 크기를 주입 → 즉시 재배치 ==== -->
				<div
					class="parking-lot"
					:style="{
						'--map-w': layout.mapW + 'px',
						'--map-h': layout.mapH + 'px',
						'--slot-w': layout.slotW + 'px',
						'--slot-h': layout.slotH + 'px',
						'--slot-gap': layout.slotGap + 'px',
						'--aisle-w': layout.aisleW + 'px',
						'--divider-m': layout.dividerMargin + 'px',
						'--bg': layout.bgColor,
					}"
				>
					<!-- 차량 오버레이: 탑뷰 트래킹 (서버 fps에 맞춰 갱신) -->
					<svg class="overlay" :width="layout.mapW" :height="layout.mapH">
						<g v-for="obj in vehicles" :key="obj.track_id">
							<polygon :points="toPoints(obj.corners)" fill="none" stroke="#ff0" stroke-width="2" />
							<text :x="obj.center[0]" :y="obj.center[1]" font-size="36" fill="#ff0" text-anchor="middle">
								{{ obj.track_id }}
							</text>
						</g>
					</svg>

					<!-- 레이아웃 행 반복: 왼쪽/차도/오른쪽 -->
					<template v-for="(row, idx) in layout.rows" :key="'row-' + idx">
						<div class="row">
							<!-- 왼쪽 슬롯들 -->
							<template v-for="spot in row.left" :key="'L-' + spot">
								<div class="slot" :id="spot" :class="statusClass(spot)">
									<span class="slot-label">{{ spot }}</span>
									<div class="slot-actions">
										<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
										<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
										<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
									</div>
								</div>
							</template>

							<!-- 중앙 차도 -->
							<div class="aisle"></div>

							<!-- 오른쪽 슬롯들 -->
							<template v-for="spot in row.right" :key="'R-' + spot">
								<div class="slot" :id="spot" :class="statusClass(spot)">
									<span class="slot-label">{{ spot }}</span>
									<div class="slot-actions">
										<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
										<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
										<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
									</div>
								</div>
							</template>
						</div>

						<!-- 첫 번째/중간 행 사이에 분리선 표시(선택) -->
						<div v-if="layout.showDivider && idx === 0" class="divider"></div>
					</template>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
/* Vue/구성요소/유틸 */
import { ref, reactive, computed, onMounted, onBeforeUnmount, defineComponent } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";
import AdminAuthRequiredModal from "@/views/admin/AdminAuthRequiredModal.vue";
import { BACKEND_BASE_URL } from "@/utils/api";

/* 
  백엔드 엔드포인트
  - REST: BACKEND_BASE_URL 사용(예: https://api.example.com)
  - WS: 배포 환경에 맞춰 wss:// 로 교체
*/
const WSS_CAR_URL = `wss://i13e102.p.ssafy.io/ws/car-position/`;
const WSS_SPACE_URL = `wss://i13e102.p.ssafy.io/ws/parking-space/`;

export default defineComponent({
	components: { AdminNavbar, AdminAuthRequiredModal },
	setup() {
		const showModal = ref(false);

		/* =========================================================
       1) 레이아웃 변수(여기만 바꾸면 전체가 따라온다)
       ========================================================= */
		const layout = reactive({
			mapW: 900, // 지도 가로(px)
			mapH: 550, // 지도 세로(px)
			slotW: 90, // 슬롯 가로(px)
			slotH: 150, // 슬롯 세로(px)
			slotGap: 6, // 슬롯 간격(px)
			aisleW: 36, // 중앙 차도 폭(px)
			dividerMargin: 110, // 행/행 사이 분리선 여백(px)
			showDivider: true, // 첫 행/둘째 행 사이 분리선 표시 여부
			bgColor: "#4c4c4c", // 지도 배경색
			// 행 구성(왼쪽/오른쪽):
			rows: [
				{ left: ["A5", "A4", "A3"], right: ["A2", "A1"] },
				{ left: ["B3", "B2", "B1"], right: ["C3", "C2", "C1"] },
			],
		});

		/* =========================================================
       2) 슬롯 상태 맵 + 초기화
       - rows에서 등장한 모든 슬롯을 키로 등록(초기값 'free')
       ========================================================= */
		const statusMap = reactive<Record<string, "free" | "occupied" | "reserved">>({});
		function initStatusMap() {
			layout.rows.forEach((row) => {
				[...row.left, ...row.right].forEach((spot) => {
					if (!(spot in statusMap)) statusMap[spot] = "free";
				});
			});
		}
		initStatusMap();

		/* =========================================================
       3) 상단 요약 카드(전체/사용중/빈공간/예약/오늘이용량)
       ========================================================= */
		const totalSlots = computed(() => Object.keys(statusMap).length);
		const occupiedCount = computed(() => Object.values(statusMap).filter((s) => s === "occupied").length);
		const freeCount = computed(() => Object.values(statusMap).filter((s) => s === "free").length);
		const reservedCount = computed(() => Object.values(statusMap).filter((s) => s === "reserved").length);
		const usageToday = ref(0); // 오늘 '입차' 수

		const cards = computed(() => [
			{ key: "total", title: "전체 주차 공간", value: totalSlots.value, unit: "개", color: "c-blue", icon: "🚗", live: true },
			{ key: "occupied", title: "사용중", value: occupiedCount.value, unit: "개", color: "c-orange", icon: "🅿️", live: true },
			{ key: "free", title: "빈 공간", value: freeCount.value, unit: "개", color: "c-green", icon: "✅", live: true },
			{ key: "reserved", title: "예약됨", value: reservedCount.value, unit: "개", color: "c-yellow", icon: "📌", live: true },
			{ key: "usage", title: "오늘 이용량", value: usageToday.value, unit: "대", color: "c-purple", icon: "📈", live: false },
		]);

		/* =========================================================
       4) 차량/슬롯 실시간(웹소켓) + '오늘 이용량' 폴링
       ========================================================= */
		const vehicles = reactive<Array<{ track_id: number; center: [number, number]; corners: number[] }>>([]);

		let wsCar: WebSocket | null = null;
		let wsSpace: WebSocket | null = null;
		let usageTimer: ReturnType<typeof setInterval>;

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
				// { "A1": {status:"occupied", size:"suv"}, ... }
				const payload = JSON.parse(e.data) as Record<string, { status: "free" | "occupied" | "reserved"; size: string }>;
				Object.entries(payload).forEach(([slot, info]) => {
					if (slot in statusMap) statusMap[slot] = info.status;
				});
			};
			wsSpace.onerror = (e) => console.error("[Space WS] ❌ Error:", e);
			wsSpace.onclose = () => console.warn("[Space WS] 🔒 Closed");
		}

		// '오늘 이용량(입차 수)'만 REST로 5초마다 갱신
		async function fetchUsageToday() {
			try {
				const token = localStorage.getItem("access_token");
				const res = await fetch(`${BACKEND_BASE_URL}/parking/stats/today/`, {
					headers: { Authorization: `Bearer ${token}` },
				});
				if (!res.ok) throw new Error(await res.text());
				const d = await res.json();
				usageToday.value = d.usage_today; // 백엔드에서 '입차' 기준으로 계산
			} catch (err) {
				console.error("[usageToday] fetch error:", err);
			}
		}

		onMounted(() => {
			connectCar();
			connectSpace();
			fetchUsageToday();
			usageTimer = setInterval(fetchUsageToday, 5000);
		});

		onBeforeUnmount(() => {
			wsCar?.close();
			wsSpace?.close();
			clearInterval(usageTimer);
		});

		/* =========================================================
       5) 도우미(좌표 변환, 슬롯 변경)
       ========================================================= */
		function toPoints(c: number[]) {
			// [x1,y1,x2,y2,…] → "x1,y1 x2,y2 …"
			const pts: string[] = [];
			for (let i = 0; i < c.length; i += 2) pts.push(`${c[i]},${c[i + 1]}`);
			return pts.join(" ");
		}

		function parseSpot(spot: string) {
			// "A12" → { zone:"A", slot_number:12 }
			return { zone: spot[0], slot_number: Number(spot.slice(1)) };
		}

		async function setSlot(spot: string, status: "free" | "occupied" | "reserved") {
			// 버튼으로 상태 수동 변경(운영툴 용도)
			const token = localStorage.getItem("access_token");
			const { zone, slot_number } = parseSpot(spot);
			const prev = statusMap[spot];

			// 낙관적 UI 업데이트 → 실패 시 롤백
			statusMap[spot] = status;
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
				console.error("[setSlot] error:", e);
				statusMap[spot] = prev;
				alert("상태 변경 실패");
			}
		}

		function statusClass(spot: string) {
			return {
				"status-free": statusMap[spot] === "free",
				"status-occupied": statusMap[spot] === "occupied",
				"status-reserved": statusMap[spot] === "reserved",
			};
		}

		/* expose to template */
		return {
			showModal,
			layout,
			statusMap,
			vehicles,
			cards,
			toPoints,
			setSlot,
			statusClass,
		};
	},
});
</script>

<style scoped>
/* ===== 페이지 공통 ===== */
.page-wrapper {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
	background: #f3eeea;
}
.container {
	background: #f3eeea;
	min-height: calc(100vh - 64px);
	padding: 48px 64px;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.title {
	font-size: 36px;
	font-weight: 700;
	color: #333;
	margin-bottom: 32px;
	align-self: flex-start;
}

/* ===== 요약 카드 ===== */
.summary-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
	gap: 16px;
	width: 100%;
	max-width: 1200px;
	margin-bottom: 8px;
}
.summary-card {
	position: relative;
	padding: 16px 18px 18px;
	border-radius: 14px;
	background: rgba(255, 255, 255, 0.35);
	backdrop-filter: blur(6px);
	box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}
.card-top {
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.icon {
	font-size: 22px;
	line-height: 1;
}
.live-dot {
	width: 10px;
	height: 10px;
	border-radius: 50%;
	background: #18c964;
	box-shadow: 0 0 0 0 rgba(24, 201, 100, 0.7);
	animation: livePing 1.8s infinite;
}
@keyframes livePing {
	0% {
		box-shadow: 0 0 0 0 rgba(24, 201, 100, 0.7);
	}
	70% {
		box-shadow: 0 0 0 10px rgba(24, 201, 100, 0);
	}
	100% {
		box-shadow: 0 0 0 0 rgba(24, 201, 100, 0);
	}
}
.card-title {
	margin-top: 8px;
	font-size: 14px;
	font-weight: 600;
	color: #334155;
}
.card-value {
	margin-top: 6px;
	font-size: 28px;
	font-weight: 800;
	color: #0f172a;
}
.card-value .unit {
	margin-left: 4px;
	font-size: 16px;
	font-weight: 600;
	color: #475569;
}
/* 색상 테마 */
.c-blue {
	background: linear-gradient(180deg, #eef6ff 0%, rgba(238, 246, 255, 0.55) 100%);
}
.c-orange {
	background: linear-gradient(180deg, #fff2e5 0%, rgba(255, 242, 229, 0.55) 100%);
}
.c-green {
	background: linear-gradient(180deg, #f2fff2 0%, rgba(242, 255, 242, 0.55) 100%);
}
.c-yellow {
	background: linear-gradient(180deg, #fffbe5 0%, rgba(255, 251, 229, 0.55) 100%);
}
.c-purple {
	background: linear-gradient(180deg, #f7e8ff 0%, rgba(247, 232, 255, 0.55) 100%);
}

/* ===== 지도/칸 배치 (CSS 변수 기반) ===== */
.parking-lot {
	position: relative;
	width: var(--map-w);
	height: var(--map-h);
	margin: 0 auto;
	background-color: var(--bg, #4c4c4c);
	border-radius: 14px;
	padding: 10px 0;
	box-sizing: border-box;
	margin-top: 10px;
}
/* 차량 오버레이는 상단 고정 */
.overlay {
	position: absolute;
	top: 0;
	left: 0;
	pointer-events: none;
	z-index: 3;
}

/* 한 행: 왼쪽 슬롯들 + 중앙 차도 + 오른쪽 슬롯들 */
.row {
	display: flex;
	justify-content: center;
	gap: var(--slot-gap);
}
/* 개별 슬롯 */
.slot {
	position: relative;
	width: var(--slot-w);
	height: var(--slot-h);
	border: 2px solid #fff;
	color: #fff;
	font-weight: 600;
	display: flex;
	align-items: center;
	justify-content: center;
	box-sizing: border-box;
	overflow: hidden;
}
/* 중앙 차도 */
.aisle {
	width: var(--aisle-w);
}
/* 행 사이 분리선 */
.divider {
	border-top: 4px dashed #fff;
	margin: var(--divider-m) 0;
}

/* 상태 색상 */
.status-free {
	background: #9c9c9c;
}
.status-occupied {
	background: #e75757;
}
.status-reserved {
	background: #f5dd29;
}

/* 슬롯 라벨/버튼 */
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
.slot-label {
	position: absolute;
	top: 8px;
	left: 0;
	right: 0;
	text-align: center;
	pointer-events: none;
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
</style>
