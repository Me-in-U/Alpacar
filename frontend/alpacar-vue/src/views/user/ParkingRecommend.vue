<template>
	<div class="main-page-container">
		<Header />

		<div class="main-content">
			<!-- 1) 차량 미인식 (건너뛰기 버튼만 남김) -->
			<div v-if="!forceShowMap && !isCarRecognized" class="unrecognized-container">
				<div class="center-content">
					<img src="@/assets/alert_black.png" width="67" height="67" alt="경고" />
					<h2 class="title">아직 인식된 차량이 없습니다</h2>
					<p class="body">
						차량이 주차장에 들어오면<br />
						자동으로 주차배정이 시작됩니다
					</p>
				</div>

				<!-- 🔻 새 버튼: 인식 건너뛰기 -->
				<button class="skip-btn" @click="forceShowMap = true">주차장 지도 바로보기</button>
			</div>

			<!-- 2) 추천 계산 중 (강제 표시 중이면 건너뛰고 지도 표시) -->
			<div v-else-if="!forceShowMap && isLoading" class="loading-container">
				<div class="car-animation-wrapper">
					<img src="@/assets/car-with-alpaca.png" alt="알파카 자동차" class="car-animation" />
				</div>
				<p class="loading-text">추천 주차 공간을 배정 중입니다...</p>
				<div class="info-inline" v-if="currentPlate">
					현재 <b>{{ currentPlate }}</b> 차량 주차 중
				</div>
				<!-- 필요하면 여기에도 버튼 노출 가능 -->
				<button class="skip-btn ghost" @click="forceShowMap = true">지도를 먼저 볼래요</button>
			</div>

			<!-- 3) 지도 (forceShowMap=true면 항상 이쪽으로 진입) -->
			<div v-else>
				<section class="recommend-header">
					<p class="title">추천 주차 위치</p>

					<div class="info-box">
						<div class="info-title">추천 위치: {{ recommendedId || "-" }}</div>
						<div class="info-detail">예상 소요시간: 약 2분</div>
						<div class="info-detail">난이도: 쉬움 (초급자 적합)</div>
						<div class="info-detail" v-if="currentPlate">현재 차량: {{ currentPlate }}</div>
						<div v-if="forceShowMap" class="force-hint">차량 인식 대기중입니다.</div>
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

							// 🔻 필요 시 게이트 위치를 JS에서 바로 조정 가능
							'--gate-left': 215 * SCALE + 'px',
							'--gate-top': 170 * SCALE + 'px',
							'--gate-bottom': 170 * SCALE + 'px',
						}"
						ref="mapWrapper"
					>
						<!-- 🔻 차단바: 위/아래 각 1개 -->
						<div class="gate gate--top" title="입구 차단바">
							<div class="gate-pole"></div>
							<div class="gate-box"></div>
						</div>
						<div class="gate gate--bottom" title="출구 차단바">
							<div class="gate-pole"></div>
							<div class="gate-box"></div>
						</div>
						<!-- 차량 오버레이: 이미지로 렌더 -->
						<div class="cars-layer" :style="{ width: layout.mapW + 'px', height: layout.mapH + 'px' }">
							<div v-for="obj in filteredVehicles" :key="obj.track_id" class="car-entity" :class="{ mine: myPlatesSet.has(obj.track_id) }" :style="carStyle(obj)">
								<span v-if="myPlatesSet.has(obj.track_id)" class="ping-ring"></span>
								<img :src="carTopImg" class="car-img" alt="car" />
								<div v-if="myPlatesSet.has(obj.track_id)" class="car-label">내 차</div>
							</div>
						</div>

						<!-- 가이드 라인(화살표)은 유지하려면 아래처럼 SVG엔 경로만 남겨둠 -->
						<svg class="overlay" viewBox="0 0 900 550" preserveAspectRatio="none">
							<defs>
								<marker id="arrowhead" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
									<path d="M 0 0 L 10 5 L 0 10 z" fill="#ff6bf8" />
								</marker>
							</defs>
							<path v-if="arrowD" :d="arrowD" class="guide-path" marker-end="url(#arrowhead)" />
						</svg>

						<!-- 상/하 행: 관리자와 동일 배치 -->
						<template v-for="(row, idx) in layout.rows" :key="'row-' + idx">
							<div class="row" :style="{ marginLeft: (idx === 0 ? layout.offsetTopX : layout.offsetBottomX) + 'px' }">
								<!-- 왼쪽 -->
								<template v-for="spot in row.left" :key="'L-' + spot">
									<div v-if="spot === 'x'" class="slot slot-placeholder" aria-hidden="true"></div>
									<div v-else class="slot" :data-spot-id="spot" :style="idx === 0 ? { height: layout.topRightSlotH + 'px' } : {}" :class="spotClasses(spot)">
										{{ spot }}
									</div>
								</template>

								<!-- 중앙 차도(간격) -->
								<div class="aisle"></div>

								<!-- 오른쪽 -->
								<template v-for="spot in row.right" :key="'R-' + spot">
									<div v-if="spot === 'x'" class="slot slot-placeholder" aria-hidden="true"></div>
									<div v-else class="slot" :data-spot-id="spot" :style="idx === 0 ? { height: layout.topRightSlotH + 'px' } : {}" :class="spotClasses(spot)">
										{{ spot }}
									</div>
								</template>
							</div>

							<!-- 행 사이 분리선 -->
							<div v-if="layout.showDivider && idx === 0" class="divider"></div>
						</template>

						<!-- 추천 핀 -->
						<img class="pin pin--blink" src="@/assets/pin.png" alt="pin" v-if="pinStyle.top" :style="pinStyle" />
					</div>

					<div class="legend">
						<div class="legend-item">
							<div class="box recommended"></div>
							<span>추천 위치</span>
						</div>
						<div class="legend-item">
							<div class="box empty"></div>
							<span>미사용</span>
						</div>
						<div class="legend-item">
							<div class="box reserved"></div>
							<span>예약됨</span>
						</div>
						<div class="legend-item">
							<div class="box occupied"></div>
							<span>사용중</span>
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
import { ref, reactive, watch, nextTick, onMounted, onBeforeUnmount, computed } from "vue";
import { useRouter } from "vue-router";
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
import { useUserStore } from "@/stores/user";
import carTopImg from "@/assets/navi_topview_car_1.png";

/* ==== 지도 강제 표시 토글 ==== */
const forceShowMap = ref(false);

// 인식 확정/해제 지연(ms)
const SEEN_CONFIRM_MS = 800;
const LOST_GRACE_MS = 5000;

// 내부 상태
let seenTimer: number | null = null;
let lostTimer: number | null = null;

// 현재 프레임에서 "내 차"가 있는지 마지막 판단 캐시
let lastFrameHasMine = false;

// 안전하게 상태 전환하는 헬퍼
function setRecognizedStable(next: boolean) {
	if (next === isCarRecognized.value) return;
	isCarRecognized.value = next;

	if (!next) {
		// 미인식 전환 시에만 초기화(필요 시 원하는 값만 리셋)
		isLoading.value = false;
		// recommendedId.value = ""; // 추천 유지하고 싶으면 주석 처리 유지
		// resetPin();                // 핀 초기화도 원치 않으면 주석
	}
}

/* ===== WS 엔드포인트 (관리자와 동일) ===== */
const WSS_PARKING_STATUS_URL = `wss://i13e102.p.ssafy.io/ws/parking_status`;
// const WSS_PARKING_STATUS_URL = `ws://localhost:8000/ws/parking_status`;

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
	slotW: 71 * SCALE,
	slotH: 150 * SCALE,
	slotGap: 0 * SCALE,
	aisleW: 20 * SCALE,
	dividerMargin: 110 * SCALE,
	showDivider: true,
	bgColor: "#4c4c4c",
	carOffsetX: 0 * SCALE,
	carOffsetY: 0 * SCALE,
	offsetTopX: 210 * SCALE,
	offsetBottomX: 230 * SCALE,
	topRightSlotH: 135 * SCALE,
	rows: [
		{ left: ["B1", "B2", "B3"], right: ["C1", "C2", "C3"] },
		{ left: ["A1", "A2", "A3"], right: ["A4", "A5", "x"] },
	],
});

/* 슬롯 상태/매핑 */
/* 슬롯 상태/매핑 */
type SlotStatus = "free" | "occupied" | "reserved";
const statusMap = reactive<Record<string, SlotStatus>>({});
const spaceVehicleMap = reactive<Record<string, { plate: string | null }>>({});

/** 점유 상태인 슬롯 중 해당 번호판이 점유한 슬롯을 반환 */
function plateOccupiedSlot(plate: string): string | null {
	for (const [slot, info] of Object.entries(spaceVehicleMap)) {
		if (info?.plate === plate && statusMap[slot] === "occupied") {
			return slot;
		}
	}
	return null;
}

/** 차량이 이미 주차 완료 상태인지 */
function isVehicleParked(plate: string): boolean {
	return !!plate && !!plateOccupiedSlot(plate);
}

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
	opacity?: number;
};
const vehicles = ref<TelemetryCar[]>([]);

// WS로 막 들어온 최신 원시값(목표)
const rawTargets = new Map<string, TelemetryCar>();

type SmoothState = {
	center: [number, number];
	corners: number[];
	meta: { track_id: string; state?: string; suggested?: string };
	opacity: number;
	fadingOut: boolean;
};
const smoothMap = new Map<string, SmoothState>();
/* ==== 필터링된 차량 목록 getter ==== */
const filteredVehicles = computed(() => {
	const list = vehicles.value;

	return list;
});

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
	ws = new WebSocket(WSS_PARKING_STATUS_URL);
	ws.onopen = () => console.log("[ParkingStatus WS] ✅ Connected");
	ws.onerror = (e) => console.error("[ParkingStatus WS] ❌ Error:", e);
	ws.onclose = () => console.warn("[ParkingStatus WS] 🔒 Closed");
	ws.onmessage = (e) => {
		try {
			const data = JSON.parse(e.data);

			switch (data?.message_type) {
				case "car_position": {
					// 1) 들어온 프레임을 표준 형태로 변환
					const arr = Array.isArray(data.vehicles) ? data.vehicles : [];
					const converted = arr.map((v: any) => ({
						track_id: String(v?.track_id ?? v?.plate ?? ""),
						center: [Number(v?.center?.x ?? v?.center?.[0] ?? 0), Number(v?.center?.y ?? v?.center?.[1] ?? 0)] as [number, number],
						corners: Array.isArray(v?.corners) ? (Array.isArray(v.corners[0]) ? v.corners.flat().map(Number) : v.corners.map(Number)) : [],
						state: v?.state,
						suggested: v?.suggested ?? "",
					})) as TelemetryCar[];

					// 2) 목표값(rawTargets) 갱신 + smoothMap 초기화/메타 갱신
					for (const car of converted) {
						rawTargets.set(car.track_id, car);
						if (!smoothMap.has(car.track_id)) {
							smoothMap.set(car.track_id, {
								center: [...car.center],
								corners: [...car.corners],
								meta: { track_id: car.track_id, state: car.state, suggested: car.suggested },
								opacity: 0, // 👈 페이드 인 시작
								fadingOut: false,
							});
						} else {
							const s = smoothMap.get(car.track_id)!;
							s.meta.state = car.state;
							s.meta.suggested = car.suggested;
						}
					}

					// 3) 인식 상태는 "이번 프레임 원본(converted)"로 판정
					const mineRaw = converted.find((v) => myPlatesSet.has(v.track_id));
					lastFrameHasMine = !!mineRaw;

					currentPlate.value = mineRaw ? mineRaw.track_id : "";

					if (lastFrameHasMine) {
						if (lostTimer) {
							clearTimeout(lostTimer);
							lostTimer = null;
						}
						if (!isCarRecognized.value && !seenTimer) {
							seenTimer = window.setTimeout(() => {
								setRecognizedStable(true);
								seenTimer = null;
							}, SEEN_CONFIRM_MS);
						}
					} else {
						if (seenTimer) {
							clearTimeout(seenTimer);
							seenTimer = null;
						}
						if (isCarRecognized.value && !lostTimer) {
							lostTimer = window.setTimeout(() => {
								setRecognizedStable(false);
								lostTimer = null;
							}, LOST_GRACE_MS);
						}
					}

					// 4) 추천 슬롯 반영(원본 프레임에도 있을 때)
					if (mineRaw?.suggested && statusMap[mineRaw.suggested]) {
						if (recommendedId.value !== mineRaw.suggested) {
							recommendedId.value = mineRaw.suggested;
							updatePin();
						}
						isLoading.value = false;
					} else if (lastFrameHasMine) {
						isLoading.value = true; // 인식은 됐고 추천 대기
					}

					// 5) 가이드 재계산(표시는 스무딩된 vehicles가 매 프레임 업데이트)
					nextTick(recomputeGuide);
					break;
				}

				case "parking_space": {
					const payload = data.spaces || {};
					Object.entries(payload).forEach(([slot, info]: any) => {
						if (!(slot in statusMap)) return;
						statusMap[slot] = info.status;
						spaceVehicleMap[slot] = { plate: info.license_plate ?? null };
					});
					checkAutoComplete();
					break;
				}
				// ParkingStatus WS onmessage switch에 추가
				case "re-assignment": {
					const { license_plate, assignment } = data;
					// 내 차량이면 추천/핀 갱신 트리거
					if (myPlatesSet.has(String(license_plate))) {
						recommendedId.value = assignment || "";
						updatePin();
						isLoading.value = false;
					}
					break;
				}

				case "active_vehicles": {
					// 필요시 확장
					break;
				}
				default:
					break;
			}
		} catch (err) {
			console.error("[ParkingStatus WS] parse error:", err, e.data);
		}
	};
}
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const lerpArr = (out: number[], from: number[], to: number[], t: number) => {
	const n = Math.min(from.length, to.length);
	out.length = n;
	for (let i = 0; i < n; i++) out[i] = lerp(from[i], to[i], t);
	return out;
};

// 시간상수(감속 강도). 값이 작을수록 더 빠르게 따라감.
const TAU_SEC = 0.18;
const IN_FADE_SEC = 0.2;
const OUT_FADE_SEC = 0.35;
let rafId = 0;
let lastTs = performance.now();

function getPt(corners: number[], idx: number) {
	const i = (idx % (corners.length / 2)) * 2;
	return { x: corners[i] ?? 0, y: corners[i + 1] ?? 0 };
}
const dist = (ax: number, ay: number, bx: number, by: number) => Math.hypot(bx - ax, by - ay);

function metricsFromCorners(corners: number[]) {
	if (!Array.isArray(corners) || corners.length < 8) {
		return { length: 70 * SCALE, width: 32 * SCALE, angle: 0 };
	}
	const p0 = getPt(corners, 0);
	const p1 = getPt(corners, 1);
	const p2 = getPt(corners, 2);
	const a = dist(p0.x, p0.y, p1.x, p1.y);
	const b = dist(p1.x, p1.y, p2.x, p2.y);

	let length = Math.max(a, b) * SCALE;
	let width = Math.min(a, b) * SCALE;

	let vx: number, vy: number;
	if (a >= b) {
		vx = p1.x - p0.x;
		vy = p1.y - p0.y;
	} else {
		vx = p2.x - p1.x;
		vy = p2.y - p1.y;
	}
	const angle = Math.atan2(vy, vx);

	length = Math.max(50 * SCALE, length);
	width = Math.max(26 * SCALE, width);

	return { length, width, angle };
}

function carStyle(obj: { center: [number, number]; corners: number[]; opacity?: number }) {
	const { length, width, angle } = metricsFromCorners(obj.corners);

	// 🔧 좌표도 축소 비율 적용
	const sx = SCALE;
	const cx = (obj.center?.[0] ?? 0) * sx + (layout.carOffsetX || 0);
	const cy = (obj.center?.[1] ?? 0) * sx + (layout.carOffsetY || 0);

	return {
		left: cx + "px",
		top: cy + "px",
		width: length + "px", // length/width는 metricsFromCorners에서 이미 SCALE 반영
		height: width + "px",
		transform: `translate(-50%, -50%) rotate(${angle}rad)`,
		opacity: obj.opacity ?? 1,
	} as const;
}

function smoothTick(ts: number) {
	const dt = Math.min(0.05, (ts - lastTs) / 1000);
	lastTs = ts;
	const alpha = 1 - Math.exp(-dt / TAU_SEC);

	// 목표 반영 + 페이드 인
	for (const [id, target] of rawTargets) {
		const s = smoothMap.get(id)!;
		s.center[0] = lerp(s.center[0], target.center[0], alpha);
		s.center[1] = lerp(s.center[1], target.center[1], alpha);
		s.corners = lerpArr(new Array(target.corners.length), s.corners, target.corners, alpha);
		s.meta.state = target.state;
		s.meta.suggested = target.suggested;
		s.fadingOut = false;
		if (s.opacity < 1) s.opacity = Math.min(1, s.opacity + dt / IN_FADE_SEC);
	}

	// 사라진 차량 페이드 아웃 및 제거
	for (const [id, s] of Array.from(smoothMap.entries())) {
		if (!rawTargets.has(id)) {
			s.fadingOut = true;
			s.opacity = Math.max(0, s.opacity - dt / OUT_FADE_SEC);
			if (s.opacity <= 0) smoothMap.delete(id);
		}
	}

	// 화면 배열 재구성
	vehicles.value = Array.from(smoothMap.values()).map((s) => ({
		track_id: s.meta.track_id,
		center: [s.center[0], s.center[1]] as [number, number],
		corners: [...s.corners],
		state: s.meta.state,
		suggested: s.meta.suggested,
		opacity: s.opacity,
	}));

	rafId = requestAnimationFrame(smoothTick);
}
/* 내 차량 인식/추천 상태 갱신 */
function updateMyStateFromVehicles() {
	const mine = vehicles.value.find((v) => myPlatesSet.has(v.track_id));
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
			pinH = 30;
		const x = spotRect.left - wrapRect.left + spotRect.width / 2 - pinW / 2;
		const y = spotRect.top - wrapRect.top + spotRect.height / 2 - pinH / 2 - 25;
		pinStyle.left = `${x}px`;
		pinStyle.top = `${y}px`;
		// 🔻 핀 위치 갱신 후 경로도 갱신
		recomputeGuide();
	});
}
// 🔻 안내 경로 SVG d 문자열
const arrowD = ref("");

// 슬롯 중심 좌표(px) → overlay viewBox 좌표(0..900, 0..550) 변환
function getSlotCenterInViewBox(slotId: string) {
	if (!mapWrapper.value) return null;
	const wrap = mapWrapper.value;
	const wrapRect = wrap.getBoundingClientRect();
	const el = wrap.querySelector<HTMLElement>(`[data-spot-id="${slotId}"]`);
	if (!el) return null;
	const r = el.getBoundingClientRect();

	const pxX = r.left - wrapRect.left + r.width / 2;
	const pxY = r.top - wrapRect.top + r.height / 2;

	const x = (pxX / wrapRect.width) * 900; // viewBox width
	const y = (pxY / wrapRect.height) * 550; // viewBox height
	return { x, y };
}
function clamp(n: number, lo: number, hi: number) {
	return Math.max(lo, Math.min(hi, n));
}
function isTopRow(slotId: string) {
	const top = layout.rows[0];
	return top.left.includes(slotId) || top.right.includes(slotId);
}

function recomputeGuide() {
	const mine = vehicles.value.find((v) => myPlatesSet.has(v.track_id));
	if (!mine || !recommendedId.value) {
		arrowD.value = "";
		return;
	}

	const start = { x: mine.center[0] + layout.carOffsetX, y: mine.center[1] + layout.carOffsetY };
	const target = getSlotCenterInViewBox(recommendedId.value);
	if (!target) {
		arrowD.value = "";
		return;
	}

	const dirY = isTopRow(recommendedId.value) ? -1 : +1;

	// 너무 가까우면 숨김
	const dist = Math.hypot(target.x - start.x, target.y - start.y);
	if (dist < 34) {
		arrowD.value = "";
		return;
	}

	// 슬롯 앞 살짝 들어온 엔트리/정지점
	const ENTRY_IN = 18;
	const PARK_INSET = 12;
	const entry = { x: target.x, y: target.y - dirY * ENTRY_IN };
	const park = { x: target.x, y: target.y - dirY * PARK_INSET };

	// ===== 핵심: start→entry 벡터의 법선으로, "목표가 있는 쪽"으로 컨트롤을 민다
	const vx = entry.x - start.x;
	const vy = entry.y - start.y;

	// 법선(n) = (-vy, vx) 또는 (vy, -vx) 중 하나
	let nx = -vy,
		ny = vx;
	// 컨트롤이 반드시 목표가 있는 쪽(수평 방향으로 target.x 쪽)으로 밀리도록 부호 결정
	const needXSign = Math.sign(target.x - start.x) || 1;
	if (Math.sign(nx) !== needXSign) {
		nx = -nx;
		ny = -ny;
	}

	// 정규화
	const nLen = Math.hypot(nx, ny) || 1;
	nx /= nLen;
	ny /= nLen;

	// 오프셋 크기(멀수록 크게 휨)
	const offset = clamp(dist * 0.35, 18, 90);

	// 컨트롤 포인트: start와 entry의 중간쯤에서 법선 방향으로 offset 만큼 이동
	let cx = start.x + vx * 0.52 + nx * offset;
	let cy = start.y + vy * 0.52 + ny * offset;

	// 단조(y 되돌림 방지): 컨트롤 y가 start↔entry 범위를 벗어나지 않게
	const yMin = Math.min(start.y, entry.y),
		yMax = Math.max(start.y, entry.y);
	cy = clamp(cy, yMin, yMax);

	// x도 시작→목표 방향으로만 진행하도록 (지나친 되돌림 방지)
	const xMin = Math.min(start.x, entry.x),
		xMax = Math.max(start.x, entry.x);
	cx = clamp(cx, xMin, xMax);

	// ===== 경로: 단 하나의 Quadratic Bézier → 수직으로 살짝 밀어넣기
	arrowD.value = `M ${start.x.toFixed(1)} ${start.y.toFixed(1)} ` + `Q ${cx.toFixed(1)} ${cy.toFixed(1)}, ${entry.x.toFixed(1)} ${entry.y.toFixed(1)} ` + `L ${park.x.toFixed(1)} ${park.y.toFixed(1)}`;
}

watch(recommendedId, updatePin);
watch(
	vehicles,
	() => {
		updateMyStateFromVehicles(); // 🔻 추가(핵심)
		nextTick(recomputeGuide);
	},
	{ deep: true }
);
/* 슬롯 클래스 (상태 3종 + 추천) */
function spotClasses(spot: string) {
	const st = statusMap[spot];
	const isRec = recommendedId.value === spot;

	return {
		recommended: isRec,
		// 추천일 땐 다른 상태 클래스 붙이지 않음 → 추천색이 항상 우선
		occupied: !isRec && st === "occupied",
		reserved: !isRec && st === "reserved",
		empty: !isRec && st === "free",
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
	if (statusMap[slot] === "occupied") router.push("/parking-history");
}

/* 수동 완료 */
function onComplete() {
	router.push("/parking-history");
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
	window.addEventListener("resize", recomputeGuide);
	recomputeGuide();
	lastTs = performance.now();
	rafId = requestAnimationFrame(smoothTick);
});
onBeforeUnmount(() => {
	ws?.close();
	if (seenTimer) {
		clearTimeout(seenTimer);
		seenTimer = null;
	}
	if (isCarRecognized.value && !lostTimer) {
		lostTimer = window.setTimeout(() => {
			setRecognizedStable(false);
			currentPlate.value = ""; // 🔻 추가(선택)
			lostTimer = null;
		}, LOST_GRACE_MS);
	}
	window.removeEventListener("resize", recomputeGuide);
	cancelAnimationFrame(rafId);
});
</script>

<style scoped>
/* ===== 페이지 컨테이너(모바일 폭 고정) ===== */
.main-page-container {
	width: 100vw;
	max-width: 440px;
	height: 100vh; /* ✅ 내부 스크롤 컨테이너 방식: 고정 높이 */
	position: relative;
	background: #f9f5ec;
	margin: 0 auto;
	overflow: hidden;
	display: flex;
	flex-direction: column;
}

.main-content {
	flex: 1; /* ✅ 남은 공간을 차지 */
	display: block;
	width: 100%;
	overflow-y: auto; /* ✅ 이 영역만 스크롤 */
	height: auto; /* ✅ 내부 스크롤용 */
	padding-top: 30px;
	padding-bottom: 80px;
	/* min-height 제거 */
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
.slot {
	position: relative;
	width: var(--slot-w);
	height: var(--slot-h);
	border: 3px solid #fff;
	color: #fff;
	font-weight: 600;
	display: flex;
	align-items: center;
	justify-content: center;
	box-sizing: border-box;
	overflow: hidden;
}
/* 슬롯이 슬롯을 바로 이어받을 때만 왼쪽 보더 제거 → 가운데 경계선이 한 번만 보임 */
.row .slot + .slot {
	border-left: 0;
}
.slot.recommended {
	background: #e62d2d;
} /* 추천 */
.slot.reserved {
	background: #b49b55;
} /* 예약 */
.slot.occupied {
	background: #9e9d9d;
} /* 점유 */
.slot.empty {
	background: #6acaa8;
} /* 미사용 */
.slot-placeholder {
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
/* 깜빡 + 살짝 점프 느낌 */
.pin.pin--blink {
	animation: pinBlink 1.1s ease-in-out infinite;
	filter: drop-shadow(0 0 4px rgba(255, 107, 248, 0.55));
}

@keyframes pinBlink {
	0%,
	100% {
		opacity: 1;
		transform: translateY(0);
	}
	50% {
		opacity: 0.35; /* 깜빡임 강도 */
		transform: translateY(-3px);
	}
}
/* 차량 이미지 레이어(지도 위) */
.cars-layer {
	position: absolute;
	top: 0;
	left: 0;
	pointer-events: none; /* 클릭 막기 */
	z-index: 3; /* 슬롯보다 위 */
}

/* 차량 개체 */
.car-entity {
	position: absolute; /* left/top은 center 기준 */
	transform-origin: 50% 50%; /* 회전 기준 중심 */
	will-change: transform, width, height, opacity;
	filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.35));
}

/* 실제 탑뷰 이미지 */
.car-img {
	width: 100%;
	height: 100%;
	display: block;
	object-fit: contain;
	pointer-events: none;
}

/* 내 차 강조 */
.car-entity.mine .car-img {
	filter: drop-shadow(0 0 6px rgba(0, 229, 255, 0.8)) drop-shadow(0 0 14px rgba(0, 229, 255, 0.45));
}
.car-label {
	position: absolute;
	left: 50%;
	top: -16px;
	transform: translateX(-50%);
	font-size: 14px;
	font-weight: 800;
	color: #00e5ff;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
	white-space: nowrap;
	pointer-events: none;
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
	background: #e770ff;
}
.occupied.box {
	background: #9e9d9d;
}
.empty.box {
	background: #6acaa8;
}
.reserved.box {
	background: #b49b55;
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
/* 인식 건너뛰기 버튼 */
.skip-btn {
	margin-top: 14px;
	padding: 10px 14px;
	border-radius: 8px;
	background: #6b7280; /* slate-500 느낌 */
	color: #fff;
	border: none;
	font-weight: 700;
	cursor: pointer;
}
.skip-btn:hover {
	background: #4b5563;
}
.skip-btn.ghost {
	background: #9ca3af;
}
.skip-btn.ghost:hover {
	background: #6b7280;
}
.skip-btn.sm {
	padding: 6px 10px;
	font-size: 12px;
}

.force-hint {
	margin-top: 8px;
	font-size: 12px;
	color: #334155;
}

.view-toggle {
	display: flex;
	gap: 6px;
	margin-top: 10px;
}

.toggle-btn {
	padding: 6px 10px;
	border: 1px solid #cbd5e1;
	background: #f1f5f9;
	border-radius: 6px;
	font-size: 13px;
	cursor: pointer;
}

.toggle-btn.active {
	background: #3b82f6;
	color: white;
	border-color: #2563eb;
}
/* ===== 차단바(Gate) - 사진 스타일 ===== */
.gate {
	/* 크기/색 변수 */
	--gate-left: calc(215px * var(--scale));
	--gate-top: calc(160px * var(--scale));
	--gate-bottom: calc(180px * var(--scale));

	--pole-w: calc(10px * var(--scale)); /* 기둥 너비 */
	--pole-h: calc(80px * var(--scale)); /* 기둥 높이 */
	--box: calc(30px * var(--scale)); /* 작은 네모 한 변 */
	--gap-x: 0px; /* 기둥과 네모 간격(필요시 scale 곱해도 됨) */

	--pole-background: #ff2d2d;
	--box-background: #ffe100;

	position: absolute;
	left: var(--gate-left);
	width: calc(var(--pole-w) + var(--gap-x) + var(--box));
	height: var(--pole-h);
	z-index: 2; /* 슬롯 위, SVG 오버레이 아래 */
	pointer-events: none;
}

/* 상단/하단 위치는 변수로 제어 */
.gate--top {
	top: var(--gate-top);
}
.gate--bottom {
	bottom: var(--gate-bottom);
}

/* 기둥 */
.gate-pole {
	position: absolute;
	top: 0;
	left: 0;
	width: var(--pole-w);
	height: var(--pole-h);
	background: var(--pole-background);
	box-sizing: border-box;
}

/* 네모 박스 */
.gate-box {
	position: absolute;
	left: calc(var(--pole-w) + var(--gap-x));
	width: var(--box);
	height: var(--box);
	background: var(--box-background);
	box-sizing: border-box;
}
/* 위 게이트: 살짝 위로 */
.gate--top .gate-box {
	top: calc(-10px * var(--scale));
}
/* 아래 게이트: 살짝 아래로 */
.gate--bottom .gate-box {
	bottom: calc(-10px * var(--scale));
}

/* 🔻 내 차량 → 배정 슬롯 안내 라인 */
.guide-path {
	stroke: #ff6bf8; /* 눈에 잘 띄는 분홍 */
	stroke-width: 6;
	fill: none;
	stroke-dasharray: 12 10;
	stroke-linecap: round;
	opacity: 1;
	animation: guideDash 1.2s linear infinite;
	filter: drop-shadow(0 0 2px rgba(255, 255, 255, 0.35));
}
@keyframes guideDash {
	to {
		stroke-dashoffset: -22;
	}
}

/* 핑(ping) 링 이펙트 */
.ping-ring {
	position: absolute;
	left: 50%;
	top: 50%;
	transform: translate(-50%, -50%);
	width: 28px;
	height: 28px;
	border-radius: 999px;
	pointer-events: none;
	box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.75);
	animation: ping 1.1s ease-out infinite;
}
.car-entity.mine .ping-ring {
	display: block;
}

@keyframes ping {
	0% {
		box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.75);
		opacity: 1;
	}
	80% {
		box-shadow: 0 0 0 14px rgba(0, 229, 255, 0);
		opacity: 0.45;
	}
	100% {
		box-shadow: 0 0 0 0 rgba(0, 229, 255, 0);
		opacity: 0;
	}
}

/* 이미 있는 내 차 강조와 조화롭게 (있다면 그대로 두어도 OK) */
.car-entity.mine .car-img {
	filter: drop-shadow(0 0 10px rgba(0, 229, 255, 0.85)) drop-shadow(0 0 20px rgba(0, 229, 255, 0.45));
}
</style>
