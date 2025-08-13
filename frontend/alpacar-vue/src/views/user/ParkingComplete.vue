<template>
	<div class="main-page-container">
		<Header />

		<div class="main-content">
			<!-- 1) 미인식 -->
			<div v-if="!isCarRecognized" class="unrecognized-container">
				<div class="center-content">
					<img src="@/assets/alert_black.png" width="67" height="67" alt="경고" />
					<h2 class="title">아직 인식된 차량이 없습니다</h2>
					<p class="body">
						차량을 앞뒤로 움직여<br />
						번호판을 재인식 시켜주세요
					</p>
				</div>
			</div>

			<!-- 2) 인식됨 + 추천 대기 -->
			<div v-else-if="isLoading" class="loading-container">
				<div class="car-animation-wrapper">
					<img src="@/assets/car-with-alpaca.png" alt="알파카 자동차" class="car-animation" />
				</div>
				<p class="loading-text">추천 주차 공간을 배정 중입니다...</p>
			</div>

			<!-- 3) 추천 완료 -->
			<div v-else>
				<section class="recommend-header">
					<p class="title">추천 주차 위치</p>

					<!-- 배너: 내 차량 안내 -->
					<div class="info-box">
						<div class="info-title">내 차량: {{ myPlate }}</div>
						<div class="info-detail">추천 위치: {{ recommendedId || "-" }}</div>
						<div class="info-detail">상태: {{ myVehicleState || "-" }}</div>
					</div>
				</section>

				<!-- 지도 (관리자 화면과 동일 슬롯/상태 컬러) -->
				<div class="map-section">
					<div
						class="map-wrapper"
						ref="mapWrapper"
						:style="{
							'--map-w': layout.mapW + 'px',
							'--map-h': layout.mapH + 'px',
							'--slot-w': layout.slotW + 'px',
							'--slot-h': layout.slotH + 'px',
							'--slot-gap': layout.slotGap + 'px',
						}"
					>
						<!-- 차량 폴리곤 오버레이 -->
						<svg class="overlay" :width="layout.mapW" :height="layout.mapH">
							<g v-for="car in vehicles" :key="car.track_id">
								<polygon
									:points="toPoints(car.corners, layout.carOffsetX, layout.carOffsetY)"
									fill="none"
									:stroke="car.track_id === myPlate ? '#00e5ff' : '#ff0'"
									:stroke-width="car.track_id === myPlate ? 4 : 2"
									:stroke-dasharray="car.track_id === myPlate ? '6 4' : '0'"
								/>
								<text :x="car.center[0] + layout.carOffsetX" :y="car.center[1] + layout.carOffsetY - 8" font-size="18" :fill="car.track_id === myPlate ? '#00e5ff' : '#ff0'" text-anchor="middle">
									{{ car.track_id === myPlate ? "내 차량" : "" }}
								</text>
							</g>
						</svg>

						<!-- 슬롯 격자 -->
						<template v-for="(row, idx) in layout.rows" :key="'row-' + idx">
							<div class="row" :class="idx === 0 ? 'row-1' : 'row-2'">
								<!-- 왼쪽 -->
								<template v-for="spot in row.left" :key="'L-' + spot">
									<div class="spot" :class="slotClass(spot)">
										{{ spot }}
									</div>
								</template>
								<div class="aisle"></div>
								<!-- 오른쪽 -->
								<template v-for="spot in row.right" :key="'R-' + spot">
									<div v-if="spot === 'x'" class="spot spot--placeholder"></div>
									<div v-else class="spot" :class="slotClass(spot)">
										{{ spot }}
									</div>
								</template>
							</div>

							<div v-if="layout.showDivider && idx === 0" class="divider"></div>
						</template>

						<!-- 추천 핀 -->
						<img class="pin" src="@/assets/pin.png" alt="pin" v-if="pinStyle.top" :style="pinStyle" />
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
import { ref, reactive, onMounted, watch, nextTick, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";

/** ===== 설정 ===== */
const WSS_JETSON_URL = `wss://i13e102.p.ssafy.io/ws/jetson/`;

/** ===== 사용자 차량 번호판 (route ?plate=…, 없으면 localStorage.my_plate) ===== */
const route = useRoute();
const myPlate = ref<string>((route.query.plate as string) || localStorage.getItem("my_plate") || "");

/** ===== 지도 레이아웃 (관리자와 동일) ===== */
const layout = reactive({
	mapW: 400,
	mapH: 354,
	slotW: 52,
	slotH: 98,
	slotGap: 6,
	showDivider: true,
	carOffsetX: 0,
	carOffsetY: 0,
	rows: [
		{ left: ["A5", "A4", "A3"], right: ["A2", "A1", "x"] },
		{ left: ["B3", "B2", "B1"], right: ["C3", "C2", "C1"] },
	],
});

/** ===== 슬롯 상태 맵 ===== */
type SlotStatus = "free" | "occupied" | "reserved";
const statusMap = reactive<Record<string, SlotStatus>>({});
function initStatus() {
	layout.rows.forEach((r) => {
		[...r.left, ...r.right].forEach((s) => {
			if (s === "x") return;
			if (!(s in statusMap)) statusMap[s] = "free";
		});
	});
}
initStatus();

/** ===== 차량 오버레이 ===== */
type CarObj = {
	track_id: string;
	center: [number, number];
	corners: number[]; // x1,y1,x2,y2,x3,y3,x4,y4
	state?: string;
	suggested?: string;
};
const vehicles = reactive<CarObj[]>([]);

/** ===== UI 상태 ===== */
const isCarRecognized = ref(false);
const isLoading = ref(true);
const recommendedId = ref<string>("");

/** 내 차량 상태 */
const myVehicle = computed(() => vehicles.find((v) => v.track_id === myPlate.value));
const myVehicleState = computed(() => myVehicle.value?.state || "");
watch(myVehicle, (v) => {
	isCarRecognized.value = !!v;
	// 추천칸 (젯슨 텔레메트리 suggested) 반영
	if (v?.suggested && recommendedId.value !== v.suggested) {
		recommendedId.value = v.suggested;
		updatePin();
	}
	// 추천 끝났다고 판단(추천칸이 정해지면 로딩 해제)
	if (v?.suggested) isLoading.value = false;
	// 주차완료 감지 → 완료 화면
	if (v?.state === "parked" || v?.state === "parked_done") {
		goComplete();
	}
});

/** ===== 소켓 연결 ===== */
let ws: WebSocket | null = null;
function connectWS() {
	ws = new WebSocket(WSS_JETSON_URL);
	ws.onopen = () => console.log("[Jetson WS] connected");
	ws.onerror = (e) => console.error("[Jetson WS] error", e);
	ws.onclose = () => console.warn("[Jetson WS] closed");

	ws.onmessage = (e) => {
		try {
			const data = JSON.parse(e.data);

			// A) 차량 오버레이: 배열
			if (Array.isArray(data)) {
				vehicles.splice(0, vehicles.length, ...data);
				return;
			}

			// B) 젯슨 원본 텔레메트리 {slot:{}, vehicles:[...]}
			if (data && (data.slot || data.vehicles)) {
				if (data.slot) {
					Object.entries(data.slot as Record<string, SlotStatus>).forEach(([k, v]) => {
						if (k in statusMap) statusMap[k] = v;
					});
				}
				if (Array.isArray(data.vehicles)) {
					const conv = data.vehicles.map((v: any) => ({
						track_id: String(v?.plate ?? ""),
						center: [Number(v?.center?.x ?? 0), Number(v?.center?.y ?? 0)] as [number, number],
						corners: (v?.corners ?? []).flat().map(Number),
						state: v?.state,
						suggested: v?.suggested ?? "",
					}));
					vehicles.splice(0, vehicles.length, ...conv);
				}
				return;
			}

			// C) parking_space.update → SpacePayload 맵
			if (data && typeof data === "object") {
				const first = data && data[Object.keys(data)[0] as any];
				const looksLikeSpace = first && typeof first === "object" && "status" in first;
				if (looksLikeSpace) {
					Object.entries(data).forEach(([slot, info]: any) => {
						if (slot in statusMap) statusMap[slot] = info.status;
					});
					return;
				}
			}
		} catch (err) {
			console.error("[Jetson WS] parse error", err, e.data);
		}
	};
}

/** ===== 추천 핀 ===== */
const mapWrapper = ref<HTMLElement | null>(null);
const pinStyle = reactive<{ top: string; left: string }>({ top: "", left: "" });
function updatePin() {
	nextTick(() => {
		if (!mapWrapper.value || !recommendedId.value) return;
		const wrapRect = mapWrapper.value.getBoundingClientRect();
		const el = mapWrapper.value.querySelector<HTMLElement>(`.spot[data-id="${recommendedId.value}"]`) || mapWrapper.value.querySelector<HTMLElement>(`.spot[data-spot-id="${recommendedId.value}"]`); // 호환
		if (!el) return;
		const r = el.getBoundingClientRect();
		const pinW = 24,
			pinH = 24;
		const x = r.left - wrapRect.left + r.width / 2 - pinW / 2;
		const y = r.top - wrapRect.top + r.height / 2 - pinH / 2 - 35;
		pinStyle.left = `${x}px`;
		pinStyle.top = `${y}px`;
	});
}
watch(recommendedId, updatePin);

/** ===== 도우미 ===== */
function toPoints(c: number[] | number[][], dx = 0, dy = 0) {
	const flat: number[] = Array.isArray((c as any)[0]) ? (c as number[][]).flat() : (c as number[]);
	const pts: string[] = [];
	for (let i = 0; i < flat.length; i += 2) pts.push(`${flat[i] + dx},${flat[i + 1] + dy}`);
	return pts.join(" ");
}
function slotClass(spot: string) {
	const s = statusMap[spot];
	return [s === "occupied" ? "occupied" : s === "reserved" ? "reserved" : "empty", spot === recommendedId.value ? "recommended" : ""];
}

/** ===== 완료 이동 ===== */
const router = useRouter();
function goComplete() {
	router.push("/parking-complete");
}
function onComplete() {
	goComplete();
}

/** ===== 진입 시 처리 ===== */
onMounted(() => {
	// 입차 → 이 페이지 자동 이동 로직은 상위 라우터/푸시 알림에서
	// `router.push({ name:'parking-recommend', query:{ plate: '12가3456' } })` 로 트리거
	// 여기서는 소켓 연결과 초기 핀 위치만 처리
	connectWS();
	updatePin();
});
</script>

<style scoped>
/* 모바일 컨테이너 */
.main-page-container {
	width: 100vw;
	max-width: 440px;
	min-height: 100vh;
	background: #f3eeea;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
}
.main-content {
	flex: 1;
	padding-top: 80px;
	padding-bottom: 80px;
	min-height: calc(100vh - 160px);
	overflow-y: auto;
}

/* 상태 화면 */
.unrecognized-container,
.loading-container {
	width: 100%;
	min-height: calc(100vh - 160px);
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	text-align: center;
	padding: 0 16px;
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

/* 추천 결과 */
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
	font-size: 18px;
	font-weight: 700;
	margin-bottom: 6px;
}
.info-detail {
	font-size: 14px;
	color: #666;
	margin: 2px 0;
}

/* 지도 */
.map-section {
	text-align: center;
}
.map-wrapper {
	--map-w: 400px;
	--map-h: 354px;
	--slot-w: 52px;
	--slot-h: 98px;
	--slot-gap: 6px;
	position: relative;
	width: 100%;
	max-width: var(--map-w);
	height: var(--map-h);
	background: #444;
	border-radius: 8px;
	margin: 0 auto;
}
.overlay {
	position: absolute;
	top: 0;
	left: 0;
	pointer-events: none;
	z-index: 2;
}
.row {
	display: flex;
	justify-content: center;
	gap: var(--slot-gap);
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
}
.row-1 {
	top: 10px;
}
.row-2 {
	bottom: 10px;
}
.aisle {
	width: 24px;
}
.divider {
	position: absolute;
	top: 50%;
	width: 100%;
	border-top: 3px dashed #fff;
	transform: translateY(-50%);
}

.spot {
	width: var(--slot-w);
	height: var(--slot-h);
	border: 2px solid #fff;
	color: #fff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 14px;
}
.spot--placeholder {
	visibility: hidden;
	border: 0;
	background: transparent;
}
.spot.empty {
	background: #999;
}
.spot.occupied {
	background: #fe5454;
}
.spot.reserved {
	background: #f5dd29;
	color: #333;
	font-weight: 700;
}
.spot.recommended {
	outline: 3px solid #8fcd2b;
	box-shadow: inset 0 0 0 2px #fff;
}

.pin {
	position: absolute;
	width: 24px;
	height: 24px;
	z-index: 3;
}
.car {
	position: absolute;
	top: calc(50% + 16px);
	left: 10px;
	width: 56px;
	height: 32px;
}

.legend {
	display: flex;
	justify-content: center;
	gap: 16px;
	margin: 16px 0 32px;
}
.legend-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 12px;
	color: #444;
}
.box {
	width: 14px;
	height: 14px;
	border-radius: 4px;
}
.recommended.box {
	background: #8fcd2b;
}
.occupied.box {
	background: #fe5454;
}
.empty.box {
	background: #999;
}
.reserved.box {
	background: #f5dd29;
}

/* 데스크톱에서 440px 고정 */
@media (min-width: 441px) {
	.main-page-container {
		width: 440px;
	}
	.main-content {
		min-height: calc(100vh - 160px);
		padding-bottom: 20px;
	}
}
</style>
