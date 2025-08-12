<template>
	<div class="main-page-container">
		<Header />

		<div class="main-content">
			<!-- 1) 차량 미인식 -->
			<div v-if="!isCarRecognized" class="unrecognized-container">
				<div class="center-content">
					<img src="@/assets/alert_black.png" width="67" height="67" alt="경고" />
					<h2 class="title">아직 인식된 차량이 없습니다</h2>
					<p class="body">
						차량이 주차장에 들어오면<br />
						자동으로 주차배정이 시작됩니다
					</p>
				</div>
				<div v-if="isDev" class="test-panel">
					<input v-model="testPlate" class="test-input" type="text" placeholder="예: 12가3456" @keyup.enter="simulateRecognized" />
					<button class="test-btn" @click="simulateRecognized">인식 시뮬레이션</button>
					<button class="test-btn ghost" @click="simulateComplete" :disabled="!recommendedId">주차 완료(시뮬레이션)</button>
				</div>
			</div>

			<!-- 2) 추천 계산 중 -->
			<div v-else-if="isLoading" class="loading-container">
				<div class="car-animation-wrapper">
					<img src="@/assets/car-with-alpaca.png" alt="알파카 자동차" class="car-animation" />
				</div>
				<p class="loading-text">추천 주차 공간을 배정 중입니다...</p>
				<div class="info-inline" v-if="currentPlate">
					현재 <b>{{ currentPlate }}</b> 차량 주차 중
				</div>
			</div>

			<!-- 3) 추천 완료 + 실시간 맵 -->
			<div v-else>
				<section class="recommend-header">
					<p class="title">추천 주차 위치</p>

					<div class="info-box">
						<div class="info-title">추천 위치: {{ recommendedId || "-" }}</div>
						<div class="info-detail">예상 소요시간: 약 2분</div>
						<div class="info-detail">난이도: 쉬움 (초급자 적합)</div>
						<div class="info-detail" v-if="currentPlate">현재 차량: {{ currentPlate }}</div>
					</div>
				</section>

				<div class="map-section">
					<div
						class="map-wrapper"
						:style="{
							width: layout.mapW + 'px',
							height: layout.mapH + 'px',
							background: layout.bgColor,
							'--map-w': layout.mapW + 'px',
							'--map-h': layout.mapH + 'px',
							'--slot-w': layout.slotW + 'px',
							'--slot-h': layout.slotH + 'px',
							'--slot-gap': layout.slotGap + 'px',
							'--aisle-w': layout.aisleW + 'px',
							'--divider-m': layout.dividerMargin + 'px',
							'--car-offset-x': layout.carOffsetX + 'px',
							'--car-offset-y': layout.carOffsetY + 'px',
							'--edge-pad': 18 * SCALE + 'px',
							'--scale': SCALE,
						}"
						ref="mapWrapper"
					>
						<!-- 차량 오버레이 (내 차량 하이라이트) -->
						<svg class="overlay" viewBox="0 0 900 550" preserveAspectRatio="none">
							<g v-for="obj in vehicles" :key="obj.track_id">
								<polygon :points="toPoints(obj.corners, layout.carOffsetX, layout.carOffsetY)" fill="none" :stroke="myPlatesSet.has(obj.track_id) ? '#00e5ff' : '#ff0'" stroke-width="3" />
								<template v-if="myPlatesSet.has(obj.track_id)">
									<text :x="obj.center[0] + layout.carOffsetX" :y="obj.center[1] + layout.carOffsetY" font-size="14" fill="#00e5ff" text-anchor="middle">
										{{ obj.track_id }}
									</text>
								</template>
							</g>
						</svg>

						<!-- 상/하 행: 관리자와 동일 배치 -->
						<template v-for="(row, idx) in layout.rows" :key="'row-' + idx">
							<div class="row" :style="{ marginLeft: (idx === 0 ? layout.offsetTopX : layout.offsetBottomX) + 'px' }">
								<!-- 왼쪽 -->
								<template v-for="spot in row.left" :key="'L-' + spot">
									<div v-if="spot === 'x'" class="spot spot--placeholder" aria-hidden="true"></div>
									<div v-else class="spot" :data-spot-id="spot" :class="spotClasses(spot)">
										{{ spot }}
									</div>
								</template>

								<!-- 중앙 차도(간격) -->
								<div class="aisle"></div>

								<!-- 오른쪽 -->
								<template v-for="spot in row.right" :key="'R-' + spot">
									<div v-if="spot === 'x'" class="spot spot--placeholder" aria-hidden="true"></div>
									<div v-else class="spot" :data-spot-id="spot" :style="idx === 0 ? { height: layout.topRightSlotH + 'px' } : undefined" :class="spotClasses(spot)">
										{{ spot }}
									</div>
								</template>
							</div>

							<!-- 행 사이 분리선 -->
							<div v-if="layout.showDivider && idx === 0" class="divider"></div>
						</template>

						<!-- 추천 핀 -->
						<img class="pin" src="@/assets/pin.png" alt="pin" v-if="pinStyle.top" :style="pinStyle" />
						<!-- 내 차 아이콘(연출용) -->
						<img class="car" src="@/assets/my_car.png" alt="car" />
					</div>

					<div class="legend">
						<div class="legend-item">
							<div class="box recommended"></div>
							<span>추천 위치</span>
						</div>
						<div class="legend-item">
							<div class="box occupied"></div>
							<span>사용 중</span>
						</div>
						<div class="legend-item">
							<div class="box empty"></div>
							<span>미사용</span>
						</div>
						<div class="legend-item">
							<div class="box reserved"></div>
							<span>예약됨</span>
						</div>
					</div>

					<div class="info-inline ok" v-if="currentPlate">
						현재 <b>{{ currentPlate }}</b> 차량 주차 중
					</div>
				</div>

				<div class="complete-btn-wrapper">
					<button class="complete-btn" @click="onComplete">주차 완료</button>
				</div>
			</div>
		</div>

		<BottomNavigation />
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
import { BACKEND_BASE_URL } from "@/utils/api";
import { useUserStore } from "@/stores/user";

// 개발여부
const isDev = import.meta.env.DEV;
const testPlate = ref("");
// 첫 번째 free 슬롯 찾기
function findFirstFreeSpot(): string | null {
	for (const [label, st] of Object.entries(statusMap)) {
		if (st === "free") return label;
	}
	return null;
}
// 차량 폴리곤(대충 직사각형) 만들어 주는 헬퍼
function makeFakeCar(plate: string): TelemetryCar {
	// 화면 중앙 근처 임의 좌표
	const cx = 450,
		cy = 275,
		w = 50,
		h = 30;
	const corners = [cx - w, cy - h, cx + w, cy - h, cx + w, cy + h, cx - w, cy + h];
	return {
		track_id: plate,
		center: [cx, cy],
		corners,
		state: "moving",
		suggested: "", // 추천은 아래에서 결정
	};
} // ▶️ 인식 시뮬레이션: 번호판 등록 + 차량 생성 + 추천 슬롯 지정
function simulateRecognized() {
	const plate = (testPlate.value || "").trim();
	if (!plate) {
		alert("번호판을 입력하세요.");
		return;
	}

	// myPlatesSet/로컬스토리지에 추가(내 차량으로 인식되도록)
	myPlatesSet.add(plate);
	const raw = (localStorage.getItem("my_plates") || "")
		.split(",")
		.map((s) => s.trim())
		.filter(Boolean);
	if (!raw.includes(plate)) {
		raw.push(plate);
		localStorage.setItem("my_plates", raw.join(","));
	}

	// 차량 목록에 내 차량 주입
	const mine = makeFakeCar(plate);
	vehicles.splice(0, vehicles.length, mine);

	// 추천 슬롯 선정(첫 free), 없으면 그대로 대기
	const slot = findFirstFreeSpot();
	if (slot) {
		mine.suggested = slot;
		recommendedId.value = slot;
		isCarRecognized.value = true;
		isLoading.value = false;
		currentPlate.value = plate;
		// 추천 핀 위치 갱신
		updatePin();
		// 예약 상태로 미리 표시해도 된다면(선택):
		// statusMap[slot] = 'reserved';
		// spaceVehicleMap[slot] = { plate };
	} else {
		isCarRecognized.value = true;
		isLoading.value = true;
		currentPlate.value = plate;
	}
}

// ▶️ 주차 완료 시뮬레이션: 내 차량 배정 슬롯을 occupied로 변경 → 자동 라우팅
function simulateComplete() {
	const plate = currentPlate.value;
	if (!plate || !recommendedId.value) return;
	const slot = recommendedId.value;

	// 배정 매핑/상태 지정
	spaceVehicleMap[slot] = { plate };
	statusMap[slot] = "occupied";

	// 자동 이동 트리거
	checkAutoComplete();
}

/* ===== WS 엔드포인트 (관리자와 동일) ===== */
const WSS_JETSON_URL = `wss://i13e102.p.ssafy.io/ws/jetson/`;

/* ===== 상태 ===== */
const router = useRouter();
const userStore = useUserStore();

const isCarRecognized = ref(false);
const isLoading = ref(false);
const recommendedId = ref("");
const currentPlate = ref<string>("");

/* 관리자와 동일 레이아웃 */
// 1) 비율 축소 인자만 추가 (원본 대비 45% 예시)
const SCALE = 0.45;
const layout = reactive({
	mapW: 900 * SCALE,
	mapH: 550 * SCALE,
	slotW: 85 * SCALE,
	slotH: 150 * SCALE,
	slotGap: 6 * SCALE,
	aisleW: 30 * SCALE,
	dividerMargin: 110 * SCALE,
	showDivider: true,
	bgColor: "#4c4c4c",
	carOffsetX: 5 * SCALE,
	carOffsetY: 0 * SCALE,
	offsetTopX: 0 * SCALE,
	offsetBottomX: 200 * SCALE,
	topRightSlotH: 135 * SCALE,
	rows: [
		{ left: ["B1", "B2", "B3"], right: ["C1", "C2", "C3"] },
		{ left: ["A1", "A2", "A3"], right: ["A4", "A5", "x"] },
	],
});

/* 슬롯 상태/매핑 */
type SlotStatus = "free" | "occupied" | "reserved";
const statusMap = reactive<Record<string, SlotStatus>>({});
const spaceVehicleMap = reactive<Record<string, { plate: string | null }>>({});
function initStatusMap() {
	layout.rows.forEach((r) => {
		[...r.left, ...r.right].forEach((s) => {
			if (s !== "x" && !(s in statusMap)) statusMap[s] = "free";
		});
	});
}
initStatusMap();

/* 차량 텔레메트리 */
type TelemetryCar = {
	track_id: string;
	center: [number, number];
	corners: number[];
	state?: string;
	suggested?: string;
};
const vehicles = reactive<TelemetryCar[]>([]);

/* 내 번호판 세트: Pinia에서 가져옴 */
const myPlatesSet = reactive(new Set<string>());
async function ensureMyPlates() {
	if (userStore.vehicles.length === 0) {
		try {
			await userStore.fetchMyVehicles();
		} catch {}
	}
	userStore.vehicles.forEach((v) => myPlatesSet.add(v.license_plate));
	// 폴백: localStorage
	if (myPlatesSet.size === 0) {
		const raw = localStorage.getItem("my_plates");
		if (raw)
			raw
				.split(",")
				.map((s) => s.trim())
				.filter(Boolean)
				.forEach((p) => myPlatesSet.add(p));
	}
}

/* WebSocket */
let ws: WebSocket | null = null;
function connectWS() {
	ws = new WebSocket(WSS_JETSON_URL);
	ws.onopen = () => console.log("[Jetson WS] ✅ Connected");
	ws.onerror = (e) => console.error("[Jetson WS] ❌ Error:", e);
	ws.onclose = () => console.warn("[Jetson WS] 🔒 Closed");
	ws.onmessage = (e) => {
		try {
			const data = JSON.parse(e.data);

			// A) 배열: 단순 차량 목록
			if (Array.isArray(data)) {
				const converted = data.map((v: any) => ({
					track_id: String(v?.track_id ?? v?.plate ?? ""),
					center: [Number(v?.center?.[0] ?? v?.center?.x ?? 0), Number(v?.center?.[1] ?? v?.center?.y ?? 0)] as [number, number],
					corners: Array.isArray(v?.corners) ? (Array.isArray(v.corners[0]) ? v.corners.flat().map(Number) : v.corners.map(Number)) : [],
					state: v?.state,
					suggested: v?.suggested ?? "",
				})) as TelemetryCar[];
				vehicles.splice(0, vehicles.length, ...converted);
				updateMyStateFromVehicles();
				return;
			}

			// B) 젯슨 원본 텔레메트리 { slot, vehicles }
			if (data && (data.slot || data.vehicles)) {
				if (data.slot) {
					Object.entries(data.slot as Record<string, SlotStatus>).forEach(([k, v]) => {
						if (k in statusMap) statusMap[k] = v;
					});
				}
				if (Array.isArray(data.vehicles)) {
					const converted = data.vehicles.map((v: any) => {
						const cx = Number(v?.center?.x ?? 0);
						const cy = Number(v?.center?.y ?? 0);
						const corners1d = (v?.corners ?? []).flat().map(Number);
						return {
							track_id: String(v?.plate ?? ""),
							center: [cx, cy] as [number, number],
							corners: corners1d,
							state: v?.state,
							suggested: v?.suggested ?? "",
						} as TelemetryCar;
					});
					vehicles.splice(0, vehicles.length, ...converted);
					updateMyStateFromVehicles();
				}
				return;
			}

			// C) parking_space.update: 슬롯 맵
			if (data && typeof data === "object") {
				const firstKey = Object.keys(data)[0];
				const firstVal = firstKey ? (data as any)[firstKey] : null;
				const looksLikeMap = firstVal && typeof firstVal === "object" && "status" in firstVal;
				if (looksLikeMap) {
					Object.entries(data as Record<string, { status: SlotStatus; license_plate?: string | null }>).forEach(([slot, info]) => {
						if (!(slot in statusMap)) return;
						statusMap[slot] = info.status;
						spaceVehicleMap[slot] = { plate: info.license_plate ?? null };
					});
					checkAutoComplete();
					return;
				}
			}

			// D) active_vehicles.update (옵션)
			if (data && data.results && Array.isArray(data.results)) {
				// 필요시 확장
				return;
			}
		} catch (err) {
			console.error("[Jetson WS] parse error:", err, e.data);
		}
	};
}

/* 내 차량 인식/추천 상태 갱신 */
function updateMyStateFromVehicles() {
	const mine = vehicles.find((v) => myPlatesSet.has(v.track_id));
	if (mine) {
		isCarRecognized.value = true;
		currentPlate.value = mine.track_id;

		if (mine.suggested && statusMap[mine.suggested]) {
			isLoading.value = false;
			if (recommendedId.value !== mine.suggested) {
				recommendedId.value = mine.suggested;
				updatePin();
			}
		} else {
			isLoading.value = true; // 인식은 됐고 추천 대기
		}
	} else {
		isCarRecognized.value = false;
		currentPlate.value = "";
		isLoading.value = false;
		recommendedId.value = "";
		resetPin();
	}
}

/* 추천 핀 */
const mapWrapper = ref<HTMLElement | null>(null);
const pinStyle = reactive({ top: "", left: "" });
function resetPin() {
	pinStyle.top = "";
	pinStyle.left = "";
}
function updatePin() {
	nextTick(() => {
		if (!mapWrapper.value || !recommendedId.value) return;
		const wrapRect = mapWrapper.value.getBoundingClientRect();
		const spotEl = mapWrapper.value.querySelector<HTMLElement>(`[data-spot-id="${recommendedId.value}"]`);
		if (!spotEl) return;
		const spotRect = spotEl.getBoundingClientRect();
		const pinW = 24,
			pinH = 24;
		const x = spotRect.left - wrapRect.left + spotRect.width / 2 - pinW / 2;
		const y = spotRect.top - wrapRect.top + spotRect.height / 2 - pinH / 2 - 35;
		pinStyle.left = `${x}px`;
		pinStyle.top = `${y}px`;
	});
}
watch(recommendedId, updatePin);

/* 슬롯 클래스 (상태 3종 + 추천) */
function spotClasses(spot: string) {
	const st = statusMap[spot];
	return {
		recommended: recommendedId.value === spot,
		occupied: st === "occupied",
		reserved: st === "reserved",
		empty: st === "free",
	};
}

/* 주차완료 자동 이동 (내 차량 배정 슬롯이 occupied 되면) */
function myAssignedSlot(): string | null {
	if (!currentPlate.value) return null;
	for (const [slot, info] of Object.entries(spaceVehicleMap)) {
		if (info.plate && info.plate === currentPlate.value) return slot;
	}
	return null;
}
function checkAutoComplete() {
	const slot = myAssignedSlot();
	if (!slot) return;
	if (statusMap[slot] === "occupied") router.push("/parking-complete");
}

/* 수동 완료 */
function onComplete() {
	router.push("/parking-complete");
}

/* SVG 유틸 */
function toPoints(c: number[] | number[][], offsetX = 0, offsetY = 0) {
	const first = (c as any)[0];
	const flat: number[] = Array.isArray(first) ? (c as number[][]).flat() : (c as number[]);
	const pts: string[] = [];
	for (let i = 0; i < flat.length; i += 2) {
		pts.push(`${flat[i] + offsetX},${flat[i + 1] + offsetY}`);
	}
	return pts.join(" ");
}

/* 라이프사이클 */
onMounted(async () => {
	await ensureMyPlates(); // Pinia에서 내 차량 번호판 확보
	connectWS(); // 실시간 연결
});
onBeforeUnmount(() => ws?.close());
</script>

<style scoped>
/* ===== 페이지 컨테이너(모바일 폭 고정) ===== */
.main-page-container {
	width: 100vw;
	max-width: 440px;
	min-height: 100vh;
	position: relative;
	background: #f3eeea;
	margin: 0 auto;
	overflow: hidden;
	display: flex;
	flex-direction: column;
}
.main-content {
	flex: 1;
	display: block;
	padding-top: 80px;
	padding-bottom: 80px;
	min-height: calc(100vh - 160px);
	overflow-y: auto;
	width: 100%;
}

/* 미인식 상태 */
.unrecognized-container {
	width: 100%;
	min-height: calc(100vh - 160px);
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	text-align: center;
	padding: 0 16px;
	box-sizing: border-box;
}
.center-content .title {
	font-size: 20px;
	font-weight: 600;
	color: #464038;
	margin: 16px 0 12px;
}
.center-content .body {
	font-size: 16px;
	color: #666;
	line-height: 1.4;
}

/* 로딩 */
.loading-container {
	width: 100%;
	min-height: calc(100vh - 160px);
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	text-align: center;
	padding: 0 16px;
	box-sizing: border-box;
}
.car-animation-wrapper {
	position: relative;
	width: 100%;
	max-width: 400px;
	height: 100px;
	overflow: hidden;
}
.car-animation {
	position: absolute;
	bottom: 0;
	left: -100px;
	width: 100px;
	height: auto;
	animation: moveCar 4s linear infinite;
}
@keyframes moveCar {
	0% {
		transform: translateX(0);
		opacity: 0;
	}
	10% {
		opacity: 1;
	}
	90% {
		opacity: 1;
	}
	100% {
		transform: translateX(600px);
		opacity: 0;
	}
}
.loading-text {
	margin-top: 16px;
	font-size: 16px;
	color: #666;
}
.info-inline {
	margin-top: 10px;
	font-size: 14px;
	color: #444;
}
.info-inline.ok {
	color: #24577a;
}

/* 추천/헤더 */
.recommend-header {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 24px;
	text-align: center;
}
.title {
	font-size: 28px;
	font-weight: 700;
	color: #333;
	padding-top: 24px;
}
.info-box {
	width: 60%;
	background: #fff;
	border-radius: 8px;
	padding: 16px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	margin-bottom: 24px;
}
.info-title {
	font-size: 20px;
	font-weight: 600;
	margin-bottom: 8px;
}
.info-detail {
	font-size: 16px;
	color: #666;
	margin: 2px 0;
}

/* 지도 */
.map-section {
	text-align: center;
}
.map-wrapper {
	position: relative;
	border-radius: 8px;
	margin: 0 auto;
}
.row {
	display: flex;
	justify-content: center;
	gap: var(--slot-gap);
}
.row-1 {
	top: 18px;
}
.row-2 {
	bottom: 18px;
	align-items: flex-end;
}
.aisle {
	width: var(--aisle-w);
	flex: 0 0 var(--aisle-w);
}
.divider {
	border-top: 3px dashed #fff;
	margin: var(--divider-m) 0; /* 절대포지션 → 변수 마진 */
}
/* 슬롯은 전부 변수 기반 크기 */
.spot {
	width: var(--slot-w);
	height: var(--slot-h);
	border: 2px solid #fff;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #fff;
	font-size: 14px;
	background: #999;
}
.spot.recommended {
	background: #8fcd2b;
}
.spot.occupied {
	background: #fe5454;
}
.spot.empty {
	background: #9c9c9c;
}
.spot.reserved {
	background: #f5dd29;
}
.spot--placeholder {
	visibility: hidden;
	border: 0;
	background: transparent;
}

/* SVG 오버레이 */
.overlay {
	position: absolute;
	inset: 0;
	width: 100%;
	height: 100%;
	pointer-events: none;
	z-index: 3;
}
.pin {
	position: absolute;
	width: 24px;
	height: 24px;
}
.car {
	position: absolute;
	top: calc(50% + 16px);
	left: 10px;
	width: 56px;
	height: 32px;
}

/* 범례 */
.legend {
	display: flex;
	justify-content: center;
	gap: 16px;
	margin: 16px 0 24px;
}
.legend-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 12px;
	color: #333;
}
.box {
	width: 14px;
	height: 14px;
	border-radius: 3px;
}
.recommended.box {
	background: #8fcd2b;
}
.occupied.box {
	background: #fe5454;
}
.empty.box {
	background: #9c9c9c;
}
.reserved.box {
	background: #f5dd29;
}

/* 완료 버튼 */
.complete-btn-wrapper {
	display: flex;
	justify-content: center;
	padding-bottom: 24px;
}
.complete-btn {
	width: 80%;
	height: 50px;
	background: #6ba368;
	color: #fff;
	font-size: 18px;
	font-weight: 600;
	border: none;
	border-radius: 8px;
	cursor: pointer;
	transition: background 0.2s;
}
.complete-btn:hover {
	background: #5a9857;
}
.test-btn {
	background: #444;
	color: #fff;
	padding: 8px 16px;
	border-radius: 6px;
	border: none;
	cursor: pointer;
}
.test-btn:hover {
	background: #666;
}
.test-panel {
	display: flex;
	gap: 8px;
	align-items: center;
	justify-content: center;
	margin: 10px auto 16px;
	padding: 8px;
}
.test-input {
	width: 180px;
	height: 36px;
	padding: 0 10px;
	border: 1px solid #ddd;
	border-radius: 6px;
}
.test-btn {
	height: 36px;
	padding: 0 12px;
	border: none;
	border-radius: 6px;
	background: #444;
	color: #fff;
	cursor: pointer;
}
.test-btn.ghost {
	background: #888;
}
.test-btn:disabled {
	opacity: 0.5;
	cursor: not-allowed;
}
</style>
