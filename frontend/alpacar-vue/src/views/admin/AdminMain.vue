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
				<div class="assign-layout">
					<!-- 좌: 입차 차량 리스트 -->
					<aside class="assign-sidebar">
						<div class="sidebar-title">입차 차량</div>
						<div class="vehicle-list">
							<button
								v-for="v in activeVehicles"
								:key="v.id ?? v.vehicle_id"
								class="vehicle-item"
								:class="{ 'is-selected': selectedVehicle?.vehicle_id === v.vehicle_id }"
								@click="selectedVehicle = v"
								title="선택"
							>
								<div class="plate">{{ v.license_plate }}</div>
								<div class="time">입차: {{ formatDate(v.entrance_time) }}</div>
								<div class="state">상태: {{ v.status }}</div>
								<div class="state">배정: {{ v.assigned_space?.label ?? "-" }}</div>
							</button>
						</div>
					</aside>

					<!-- 중: 주차 지도 -->
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
						<!-- 🔻 차단바: 위/아래 각 1개 -->
						<div class="gate gate--top" title="입구 차단바">
							<div class="gate-pole"></div>
							<div class="gate-arm"></div>
							<div class="gate-box"></div>
						</div>
						<div class="gate gate--bottom" title="출구 차단바">
							<div class="gate-pole"></div>
							<div class="gate-arm"></div>
							<div class="gate-box"></div>
						</div>
						<div class="cars-layer" :style="{ width: layout.mapW + 'px', height: layout.mapH + 'px' }">
							<div v-for="obj in vehicles" :key="obj.track_id" class="car-entity" :style="carStyle(obj)">
								<img :src="carTopImg" class="car-img" alt="car" />
								<div class="car-label">{{ obj.track_id }}</div>
							</div>
						</div>

						<template v-for="(row, idx) in layout.rows" :key="'row-' + idx">
							<div class="row" :style="{ marginLeft: (idx === 0 ? layout.offsetTopX : layout.offsetBottomX) + 'px' }">
								<!-- 왼쪽 슬롯 -->
								<template v-for="spot in row.left" :key="'L-' + spot">
									<div class="slot" :id="spot" :class="[statusClass(spot), { 'is-spot-selected': selectedSpot === spot }]" @click="onSpotClick(spot)">
										<span class="slot-label">{{ spot }}</span>
										<!-- 현재 그 슬롯에 연결된 차량 번호판 표시 -->
										<small v-if="spaceVehicleMap[spot]?.plate" class="slot-plate">
											{{ spaceVehicleMap[spot].plate }}
										</small>
									</div>
								</template>

								<div class="aisle"></div>

								<!-- 오른쪽 슬롯 -->
								<template v-for="spot in row.right" :key="'R-' + spot">
									<div v-if="spot === 'x'" class="slot slot--placeholder" aria-hidden="true"></div>
									<div
										v-else
										class="slot"
										:id="spot"
										:style="idx === 0 ? { height: layout.topRightSlotH + 'px' } : undefined"
										:class="[statusClass(spot), { 'is-spot-selected': selectedSpot === spot }]"
										@click="onSpotClick(spot)"
									>
										<span class="slot-label">{{ spot }}</span>
										<!-- 현재 그 슬롯에 연결된 차량 번호판 표시 -->
										<small v-if="spaceVehicleMap[spot]?.plate" class="slot-plate">
											{{ spaceVehicleMap[spot].plate }}
										</small>
									</div>
								</template>
							</div>

							<div v-if="layout.showDivider && idx === 0" class="divider"></div>
						</template>
					</div>

					<!-- 우: 선택 요약/배정 -->
					<aside class="assign-panel">
						<!--  공통: 선택 슬롯 요약 (한 줄) -->
						<div class="panel-card selection-card">
							<div class="selection-row flash-in" :key="(selectedSpot || 'none') + '-' + (selectedSpot ? statusMap[selectedSpot] : 'none')">
								<span class="selection-label">주차칸</span>
								<span class="selection-slot">
									{{ selectedSpot ? `${selectedSpot} 선택됨` : "미선택" }}
								</span>
								<span class="dot">·</span>
								<span class="status-pill" :data-status="selectedSpot ? statusMap[selectedSpot] : 'none'">
									{{ selectedSpot ? statusMap[selectedSpot] : "상태 없음" }}
								</span>
							</div>
						</div>

						<!-- 수동 배정 -->
						<div class="panel-card">
							<div class="panel-title">수동 배정</div>
							<div class="panel-line">
								<span class="plabel">차량</span>
								<span class="pvalue">{{ selectedVehicle?.license_plate || "- 선택 안됨 -" }}</span>
							</div>
							<button class="btn-assign" :disabled="!canAssign" @click="assignSelected">배정하기</button>
							<p class="hint" :class="{ warn: jetsonLive }">
								{{ jetsonLive ? "• AI가 자리를 배정하고 있습니다. 수동 자리배정이 불가능합니다." : "• 차량을 고르고, 지도에서 비어있는 주차칸을 클릭하세요." }}
							</p>
						</div>

						<!-- 수동 상태 변경 -->
						<div class="panel-card">
							<div class="panel-title">수동 상태 변경</div>
							<div class="manual-status-controls">
								<button class="btn-status" :disabled="!canChangeStatus" @click="changeSelectedStatus('free')">Free</button>
								<button class="btn-status" :disabled="!canChangeStatus" @click="changeSelectedStatus('occupied')">Occupied</button>
								<button class="btn-status" :disabled="!canChangeStatus" @click="changeSelectedStatus('reserved')">Reserved</button>
							</div>
							<p class="hint" :class="{ warn: jetsonLive }">
								{{ jetsonLive ? "• 자동으로 주차칸 상태를 확인하고있습니다. 수동 변경이 불가능합니다." : "• 주차칸을 선택한 뒤 상태를 변경하세요." }}
							</p>
						</div>
					</aside>
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
import { SecureTokenManager } from "@/utils/security";
import { alert, alertSuccess, alertWarning, alertError } from "@/composables/useAlert";
import carTopImg from "@/assets/navi_topview_car_1.png"; // ⬅️ 탑뷰 자동차 이미지

const WSS_PARKING_STATUS_URL = `wss://i13e102.p.ssafy.io/ws/parking_status`;
// const WSS_PARKING_STATUS_URL = `ws://localhost:8000/ws/parking_status`;

export default defineComponent({
	components: { AdminNavbar, AdminAuthRequiredModal },
	setup() {
		// ---- 차량 스무딩 상태/유틸 ----
		const rawTargets = new Map<string, { center: [number, number]; corners: number[]; state?: string; suggested?: string; track_id: string }>();

		type SmoothState = {
			center: [number, number];
			corners: number[];
			meta: { track_id: string; state?: string; suggested?: string };
			opacity: number; // 0~1
			fadingOut: boolean; // true면 사라지는 중
		};

		const smoothMap = new Map<string, SmoothState>();

		const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
		const lerpArr = (out: number[], from: number[], to: number[], t: number) => {
			const n = Math.min(from.length, to.length);
			out.length = n;
			for (let i = 0; i < n; i++) out[i] = lerp(from[i], to[i], t);
			return out;
		};

		// 이동 스무딩(작을수록 더 빨리 붙음)
		const TAU_SEC = 0.18;
		// 페이드 인/아웃 시간
		const IN_FADE_SEC = 0.2;
		const OUT_FADE_SEC = 0.35;

		let rafId = 0;
		let lastTs = performance.now();

		function smoothTick(ts: number) {
			const dt = Math.min(0.05, (ts - lastTs) / 1000); // 최대 50ms
			lastTs = ts;
			const alpha = 1 - Math.exp(-dt / TAU_SEC);

			// 목표 향해 스무딩
			for (const [id, target] of rawTargets) {
				const s = smoothMap.get(id)!;
				// 이동
				s.center[0] = lerp(s.center[0], target.center[0], alpha);
				s.center[1] = lerp(s.center[1], target.center[1], alpha);
				s.corners = lerpArr(new Array(target.corners.length), s.corners, target.corners, alpha);
				// 메타 갱신
				s.meta.state = target.state;
				s.meta.suggested = target.suggested;
				// 페이드 인
				s.fadingOut = false;
				if (s.opacity < 1) {
					s.opacity = Math.min(1, s.opacity + dt / IN_FADE_SEC);
				}
			}

			// 사라진 차량 페이드 아웃 및 제거
			for (const [id, s] of Array.from(smoothMap.entries())) {
				if (!rawTargets.has(id)) {
					s.fadingOut = true;
					s.opacity = Math.max(0, s.opacity - dt / OUT_FADE_SEC);
					if (s.opacity <= 0) {
						smoothMap.delete(id);
					}
				}
			}

			// 화면에 그릴 배열 재구성 (opacity 포함)
			vehicles.splice(
				0,
				vehicles.length,
				...Array.from(smoothMap.values()).map((s) => ({
					track_id: s.meta.track_id,
					center: [s.center[0], s.center[1]] as [number, number],
					corners: [...s.corners],
					state: s.meta.state,
					suggested: s.meta.suggested,
					opacity: s.opacity, // 👈 추가
				}))
			);

			rafId = requestAnimationFrame(smoothTick);
		}
		/** 코너 배열에서 점 읽기 */
		function getPt(corners: number[], idx: number) {
			const i = (idx % (corners.length / 2)) * 2;
			return { x: corners[i] ?? 0, y: corners[i + 1] ?? 0 };
		}
		/** 두 점 사이 거리 */
		const dist = (ax: number, ay: number, bx: number, by: number) => Math.hypot(bx - ax, by - ay);

		/**
		 * bbox(사각형 4코너 가정)에서
		 * - 길이/너비(픽셀)
		 * - 각도(rad, x+축 기준 시계반대)
		 * 를 추정. 코너 순서가 [p0,p1,p2,p3]로 인접하게 들어온다는 전제.
		 */
		function metricsFromCorners(corners: number[]) {
			if (!Array.isArray(corners) || corners.length < 8) {
				// corners가 없으면 적당한 기본 크기
				return { length: 70, width: 32, angle: 0 };
			}
			const p0 = getPt(corners, 0);
			const p1 = getPt(corners, 1);
			const p2 = getPt(corners, 2);
			// 두 변 길이
			const a = dist(p0.x, p0.y, p1.x, p1.y);
			const b = dist(p1.x, p1.y, p2.x, p2.y);

			// 더 긴 쪽을 차량의 "길이"로 간주
			let length = Math.max(a, b);
			let width = Math.min(a, b);

			// 각도: 더 긴 변의 방향 벡터 사용
			let vx: number, vy: number;
			if (a >= b) {
				vx = p1.x - p0.x;
				vy = p1.y - p0.y;
			} else {
				vx = p2.x - p1.x;
				vy = p2.y - p1.y;
			}
			const angle = Math.atan2(vy, vx);

			// 너무 작게 들어오는 경우 최소값 보정(보기 좋게)
			length = Math.max(50, length);
			width = Math.max(26, width);

			return { length, width, angle };
		}

		/**
		 * 각 차량의 이미지 스타일(위치/회전/크기/투명도) 계산
		 */
		function carStyle(obj: { center: [number, number]; corners: number[]; opacity?: number }) {
			const { length, width, angle } = metricsFromCorners(obj.corners);

			// 중심좌표 + (필요시 오프셋)
			const cx = (obj.center?.[0] ?? 0) + (layout.carOffsetX || 0);
			const cy = (obj.center?.[1] ?? 0) + (layout.carOffsetY || 0);

			return {
				left: cx + "px",
				top: cy + "px",
				width: length + "px",
				height: width + "px",
				transform: `translate(-50%, -50%) rotate(${angle}rad)`,
				opacity: obj.opacity ?? 1,
			} as const;
		}

		const authHeaders = () => ({
			Authorization: `Bearer ${SecureTokenManager.getSecureToken("access_token")}`,
			"Content-Type": "application/json",
		});

		const jetsonLive = ref(false);

		let liveDebounce: ReturnType<typeof setTimeout> | null = null;
		const showModal = ref(false);

		type AssignedSpace = {
			id: number;
			zone: string;
			slot_number: number;
			label: string;
			status?: "free" | "occupied" | "reserved";
		};
		type ActiveVehicleItem = {
			id?: number;
			vehicle_id: number;
			license_plate: string;
			entrance_time: string | null;
			status: string;
			assigned_space?: AssignedSpace | null;
		};

		const spaceVehicleMap = reactive<Record<string, { vehicle_id: number | null; plate: string | null }>>({});
		const selectedVehicle = ref<null | ActiveVehicleItem>(null);
		const selectedSpot = ref<string | null>(null);
		const activeVehicles = ref<Array<ActiveVehicleItem>>([]);

		async function fetchActiveVehicles() {
			const res = await fetch(`${BACKEND_BASE_URL}/vehicle-events/active/`, {
				headers: authHeaders(),
			});
			if (!res.ok) return;
			const data = await res.json();
			const rows: any[] = Array.isArray(data) ? data : data.results ?? [];
			activeVehicles.value = rows.map((ev: any) => {
				let assigned: AssignedSpace | null = null;
				if (ev.assigned_space) {
					const z = ev.assigned_space.zone ?? ev.assigned_space.Zone ?? "";
					const n = ev.assigned_space.slot_number ?? ev.assigned_space.slot ?? ev.assigned_space.number ?? "";
					assigned = {
						id: ev.assigned_space.id ?? 0,
						zone: String(z),
						slot_number: Number(n),
						label: `${String(z)}${Number(n)}`,
						status: ev.assigned_space.status,
					};
				}
				return {
					id: ev.id,
					vehicle_id: ev.vehicle_id,
					license_plate: ev.license_plate,
					entrance_time: ev.entrance_time ?? null,
					status: ev.status ?? "Entrance",
					assigned_space: assigned,
				} as ActiveVehicleItem;
			});
		}

		function onSpotClick(spot: string) {
			if (jetsonLive.value) return; // AI가 배정 중이면 선택 자체만 막음(요구조건 유지)
			// ✅ 상태와 관계없이 선택 허용 (상태 변경을 위해)
			selectedSpot.value = selectedSpot.value === spot ? null : spot;
		}
		const canAssign = computed(
			() =>
				!!selectedVehicle.value &&
				!!selectedSpot.value &&
				statusMap[selectedSpot.value!] === "free" && // ✅ free 슬롯만 수동 배정 허용
				!jetsonLive.value
		);
		async function assignSelected() {
			if (!canAssign.value) return;
			if (jetsonLive.value) {
				// 추가 방어
				await alertWarning("실시간 수신 중에는 수동 배정이 비활성화됩니다.");
				return;
			}
			const token = SecureTokenManager.getSecureToken("access_token");
			const plate = selectedVehicle.value!.license_plate;
			const { zone, slot_number } = parseSpot(selectedSpot.value!);
			const slotLabel = selectedSpot.value!;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/parking/assign/`, {
					method: "POST",
					headers: authHeaders(),
					body: JSON.stringify({ license_plate: plate, zone, slot_number }),
				});
				if (!res.ok) throw new Error(await res.text());
				statusMap[slotLabel] = "reserved";
				spaceVehicleMap[slotLabel] = { vehicle_id: selectedVehicle.value!.vehicle_id, plate };
				const v = activeVehicles.value.find((x) => x.vehicle_id === selectedVehicle.value!.vehicle_id);
				if (v) {
					v.assigned_space = { id: 0, zone, slot_number, label: slotLabel, status: "reserved" };
				}
				await alertSuccess(`배정 완료: ${plate} → ${slotLabel}`);
				selectedSpot.value = null;
				selectedVehicle.value = null;
			} catch (e) {
				console.error(e);
				await alertError("배정 중 오류가 발생했습니다.");
			}
		}

		/* ===== 레이아웃 ===== */
		const layout = reactive({
			mapW: 900,
			mapH: 550,
			slotW: 71,
			slotH: 150,
			slotGap: 0,
			aisleW: 20,
			dividerMargin: 110,
			showDivider: true,
			bgColor: "#4c4c4c",
			carOffsetX: 0,
			carOffsetY: 0,
			offsetTopX: 210,
			offsetBottomX: 230,
			topRightSlotH: 135,
			rows: [
				{ left: ["B1", "B2", "B3"], right: ["C1", "C2", "C3"] },
				{ left: ["A1", "A2", "A3"], right: ["A4", "A5", "x"] },
			],
		});

		/* ===== 슬롯 상태 맵 초기화 ===== */
		const statusMap = reactive<Record<string, "free" | "occupied" | "reserved">>({});
		function initStatusMap() {
			layout.rows.forEach((row) => {
				[...row.left, ...row.right].forEach((spot) => {
					if (spot === "x") return;
					if (!(spot in statusMap)) statusMap[spot] = "free";
				});
			});
		}
		initStatusMap();

		/* ===== 상단 카드 ===== */
		const totalSlots = computed(() => Object.keys(statusMap).length);
		const occupiedCount = computed(() => Object.values(statusMap).filter((s) => s === "occupied").length);
		const freeCount = computed(() => Object.values(statusMap).filter((s) => s === "free").length);
		const reservedCount = computed(() => Object.values(statusMap).filter((s) => s === "reserved").length);
		const usageToday = ref(0);
		const cards = computed(() => [
			{ key: "total", title: "전체 주차 공간", value: totalSlots.value, unit: "개", color: "c-blue", icon: "🚗", live: true },
			{ key: "free", title: "빈 공간", value: freeCount.value, unit: "개", color: "c-green", icon: "✅", live: true },
			{ key: "occupied", title: "사용중", value: occupiedCount.value, unit: "개", color: "c-orange", icon: "🅿️", live: true },
			{ key: "reserved", title: "예약됨", value: reservedCount.value, unit: "개", color: "c-yellow", icon: "📌", live: true },
			{ key: "usage", title: "오늘 이용량", value: usageToday.value, unit: "대", color: "c-purple", icon: "📈", live: false },
		]);

		/* ===== 실시간: 단일 WS ===== */
		const vehicles = reactive<
			Array<{
				track_id: string;
				center: [number, number];
				corners: number[];
				state?: string;
				suggested?: string;
				opacity?: number;
			}>
		>([]);

		let ws: WebSocket | null = null;
		let usageTimer: ReturnType<typeof setInterval>;

		const canChangeStatus = computed(() => !!selectedSpot.value && !jetsonLive.value);

		async function changeSelectedStatus(status: "free" | "occupied" | "reserved") {
			if (!canChangeStatus.value || !selectedSpot.value) return;
			await setSlot(selectedSpot.value, status);
		}

		function connectWS() {
			ws = new WebSocket(WSS_PARKING_STATUS_URL);
			ws.onopen = () => console.log("[ParkingStatus WS] ✅ Connected");
			ws.onerror = (e) => console.error("[ParkingStatus WS] ❌ Error:", e);
			ws.onclose = () => {
				console.warn("[ParkingStatus WS] 🔒 Closed");
				jetsonLive.value = false; // 연결 종료 시 수동 변경 가능
				if (liveDebounce) clearTimeout(liveDebounce);
			};

			ws.onmessage = (e) => {
				try {
					const data = JSON.parse(e.data);

					// ✅ 진짜 AI 신호일 때만 라이브 플래그 토글
					const isAiSignal = data?.origin === "ai";

					if (isAiSignal) {
						if (liveDebounce) clearTimeout(liveDebounce);
						jetsonLive.value = true;
						liveDebounce = setTimeout(() => (jetsonLive.value = false), 1500);
					}

					switch (data?.message_type) {
						case "car_position": {
							const arr = Array.isArray(data.vehicles) ? data.vehicles : [];
							const converted = arr.map((v: any) => ({
								track_id: String(v?.track_id ?? v?.plate ?? ""),
								center: [Number(v?.center?.x ?? v?.center?.[0] ?? 0), Number(v?.center?.y ?? v?.center?.[1] ?? 0)] as [number, number],
								corners: Array.isArray(v?.corners) ? (Array.isArray(v.corners[0]) ? v.corners.flat().map(Number) : v.corners.map(Number)) : [],
								state: v?.state,
								suggested: v?.suggested ?? "",
							}));

							// 1) 이번 프레임에서 본 차량 id 수집
							const seen = new Set<string>();

							// 2) 목표(rawTargets) 업데이트 + 새 차량 seed
							for (const car of converted) {
								seen.add(car.track_id);
								rawTargets.set(car.track_id, car);

								if (!smoothMap.has(car.track_id)) {
									// 새로 보인 차량: 위치 seed + opacity=0으로 시작(페이드 인)
									smoothMap.set(car.track_id, {
										center: [car.center[0], car.center[1]] as [number, number], // 🔧 tuple로 명시
										corners: [...car.corners],
										meta: { track_id: car.track_id, state: car.state, suggested: car.suggested },
										opacity: 0, // 👈 페이드 인 시작
										fadingOut: false,
									});
								} else {
									// 기존: 메타만 즉시 동기화 (좌표는 smoothTick에서 보간)
									const s = smoothMap.get(car.track_id)!;
									s.meta.state = car.state;
									s.meta.suggested = car.suggested;
								}
							}

							// 3) 이번 프레임에 안 보인 차량은 rawTargets에서 제거 → 페이드 아웃 트리거
							for (const id of Array.from(rawTargets.keys())) {
								if (!seen.has(id)) rawTargets.delete(id);
							}

							break;
						}

						case "parking_space": {
							const payload = data.spaces || {};
							Object.entries(payload).forEach(([slot, info]: any) => {
								if (!(slot in statusMap)) return;
								statusMap[slot] = info.status;
								spaceVehicleMap[slot] = { vehicle_id: info.vehicle_id ?? null, plate: info.license_plate ?? null };
								if (info.status === "reserved" || info.status === "occupied") {
									const v = activeVehicles.value.find((x) => x.vehicle_id === info.vehicle_id);
									if (v) {
										v.assigned_space = {
											id: 0,
											zone: slot[0],
											slot_number: Number(slot.slice(1)),
											label: slot,
											status: info.status,
										};
									}
								} else if (info.status === "free") {
									const target = activeVehicles.value.find((x) => x.assigned_space?.label === slot);
									if (target) target.assigned_space = null;
								}
							});
							break;
						}
						case "active_vehicles": {
							const rows: any[] = Array.isArray(data.results) ? data.results : [];
							activeVehicles.value = rows.map((ev: any) => {
								const assigned = ev.assigned_space
									? {
											id: 0,
											zone: String(ev.assigned_space.zone),
											slot_number: Number(ev.assigned_space.slot_number),
											label: ev.assigned_space.label,
											status: ev.assigned_space.status,
									  }
									: null;
								return {
									id: ev.id,
									vehicle_id: ev.vehicle_id,
									license_plate: ev.license_plate,
									entrance_time: ev.entrance_time,
									status: ev.status ?? "Entrance",
									assigned_space: assigned,
								};
							});

							// 슬롯-번호판 동기화(옵션)
							const bySlot: Record<string, { vehicle_id: number | null; plate: string | null }> = {};
							for (const v of activeVehicles.value) {
								if (v.assigned_space?.label) {
									bySlot[v.assigned_space.label] = { vehicle_id: v.vehicle_id, plate: v.license_plate };
								}
							}
							Object.keys(spaceVehicleMap).forEach((k) => delete spaceVehicleMap[k]);
							Object.assign(spaceVehicleMap, bySlot);
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

		async function fetchUsageToday() {
			try {
				const token = SecureTokenManager.getSecureToken("access_token");
				const res = await fetch(`${BACKEND_BASE_URL}/parking/stats/today/`, {
					headers: authHeaders(),
				});
				if (!res.ok) throw new Error(await res.text());
				const d = await res.json();
				usageToday.value = d.usage_today;
			} catch (err) {
				console.error("[usageToday] fetch error:", err);
			}
		}

		onMounted(() => {
			connectWS();
			fetchUsageToday();
			fetchActiveVehicles(); // 초기 보정용
			usageTimer = setInterval(fetchUsageToday, 5000);
			lastTs = performance.now();
			rafId = requestAnimationFrame(smoothTick);
		});
		onBeforeUnmount(() => {
			ws?.close();
			clearInterval(usageTimer);
			cancelAnimationFrame(rafId);
		});

		/* ===== 도우미 ===== */
		function toPoints(c: number[] | number[][], offsetX = 0, offsetY = 0) {
			const first = (c as any)[0];
			const flat: number[] = Array.isArray(first) ? (c as number[][]).flat() : (c as number[]);
			const pts: string[] = [];
			for (let i = 0; i < flat.length; i += 2) {
				pts.push(`${flat[i] + offsetX},${flat[i + 1] + offsetY}`);
			}
			return pts.join(" ");
		}

		function parseSpot(spot: string) {
			return { zone: spot[0], slot_number: Number(spot.slice(1)) };
		}
		async function setSlot(spot: string, status: "free" | "occupied" | "reserved") {
			const token = SecureTokenManager.getSecureToken("access_token");
			const { zone, slot_number } = parseSpot(spot);
			const prev = statusMap[spot];
			statusMap[spot] = status;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/parking/space/set-status/`, {
					method: "POST",
					headers: authHeaders(),
					body: JSON.stringify({ zone, slot_number, status }),
				});
				if (!res.ok) throw new Error(await res.text());
			} catch (e) {
				console.error("[setSlot] error:", e);
				statusMap[spot] = prev;
				await alertError("상태 변경 실패");
			}
		}
		const formatDate = (iso: string | null) =>
			iso ? new Date(iso).toLocaleString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }) : "-";
		function statusClass(spot: string) {
			return { "status-free": statusMap[spot] === "free", "status-occupied": statusMap[spot] === "occupied", "status-reserved": statusMap[spot] === "reserved" };
		}

		return {
			showModal,
			layout,
			statusMap,
			vehicles,
			cards,
			toPoints,
			setSlot,
			statusClass,
			selectedVehicle,
			selectedSpot,
			activeVehicles,
			onSpotClick,
			canAssign,
			assignSelected,
			formatDate,
			spaceVehicleMap,
			jetsonLive,
			canChangeStatus,
			changeSelectedStatus,
			carStyle,
			carTopImg,
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
	background: #f9f5ec;
}
.container {
	background: #f9f5ec;
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
	--slot-border: 6px;
	--slot-border-color: #ece9e4;
	/* 상태 팔레트(저채도, 대비 확보) */
	--c-free: #63b99b; /* soft green */
	--c-free-2: #6aa992;

	--c-reserved: #f0c245; /* warm pastel yellow */
	--c-reserved-2: #e6c75e;

	--c-occupied: #e88f8f; /* muted rose */
	--c-occupied-2: #d37c7c;
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
	z-index: 1;
	position: relative;
	width: var(--slot-w);
	height: var(--slot-h);
	border: var(--slot-border, 7px) solid var(--slot-border-color, #fff);
	color: #fff;
	font-weight: 600;
	display: flex;
	align-items: center;
	justify-content: center;
	box-sizing: border-box;
	overflow: hidden;
	transition: transform 120ms ease, box-shadow 120ms ease, outline-color 120ms ease;
	will-change: transform, box-shadow;
}
/* 이웃 슬롯 사이 중앙선: 왼쪽 보더 제거*/
.row .slot + .slot {
	border-left: 0;
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
	background: linear-gradient(180deg, var(--c-free) 0%, var(--c-free-2) 100%);
	box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.15);
}
.status-reserved {
	background: linear-gradient(180deg, var(--c-reserved) 0%, var(--c-reserved-2) 100%);
	box-shadow: inset 0 0 0 2px rgba(0, 0, 0, 0.05);
}
.status-occupied {
	background: linear-gradient(180deg, var(--c-occupied) 0%, var(--c-occupied-2) 100%);
	box-shadow: inset 0 0 0 2px rgba(0, 0, 0, 0.08);
}

/* 슬롯 라벨/버튼 */
.slot-label {
	position: absolute;
	top: 8px;
	left: 0;
	right: 0;
	text-align: center;
	pointer-events: none;
	z-index: 1;
}
.slot--placeholder {
	visibility: hidden;
	border: 0;
	background: transparent;
}

/* 좌측 리스트 + 지도 + 우측 패널 3열 레이아웃 */
.assign-layout {
	display: grid;
	grid-template-columns: 280px auto auto;
	justify-content: center;
	gap: 16px;
	width: 100%;
	max-width: 1200px;
	margin-top: 12px;
}

/* 왼쪽: 입차 차량 목록 */
.assign-sidebar {
	background: #fff;
	border: 1px solid #e6dfd6;
	border-radius: 12px;
	padding: 12px;
	height: var(--map-h); /* 지도와 동일 높이 느낌 */
	box-sizing: border-box;
	overflow: auto;
}
.sidebar-title {
	font-weight: 800;
	color: #5a5249;
	margin-bottom: 8px;
}
.vehicle-list {
	display: flex;
	flex-direction: column;
	gap: 8px;
}
.vehicle-item {
	text-align: left;
	border: 1px solid #e6dfd6;
	border-radius: 8px;
	background: #faf8f5;
	padding: 10px;
	cursor: pointer;
	transition: background 0.2s ease, border-color 0.2s ease, transform 0.08s ease;
}
.vehicle-item:hover {
	background: #f2ede7;
}
.vehicle-item.is-selected {
	border-color: #a29280;
	background: #efe9e2;
}
.vehicle-item .plate {
	font-weight: 800;
	color: #333;
}
.vehicle-item .time {
	font-size: 12px;
	color: #6f6a63;
	margin-top: 4px;
}
.vehicle-item .state {
	font-size: 12px;
	color: #24577a;
	margin-top: 2px;
}

/* 오른쪽: 선택 요약 패널 */
.assign-panel {
	display: flex;
	flex-direction: column;
	gap: 16px;
	height: var(--map-h); /* 지도와 동일 높이 */
}
.panel-card {
	background: #fff;
	border: 1px solid #e6dfd6;
	border-radius: 12px;
	padding: 14px;
}
.panel-title {
	font-weight: 800;
	color: #5a5249;
	margin-bottom: 8px;
}
.panel-line {
	display: flex;
	justify-content: space-between;
	padding: 6px 0;
	border-bottom: 1px dashed #e6dfd6;
}
.panel-line:last-child {
	border-bottom: 0;
}
.plabel {
	color: #6b6257;
	font-weight: 700;
}
.pvalue {
	color: #0f172a;
	font-weight: 800;
}

/* 배정 버튼 */
.btn-assign {
	width: 100%;
	margin-top: 12px;
	background: #a29280;
	color: #fff;
	border: 0;
	border-radius: 8px;
	padding: 10px 12px;
	font-weight: 800;
	cursor: pointer;
	transition: background 0.2s ease, transform 0.08s ease;
}
.btn-assign:hover {
	background: #8e7f6f;
}
.btn-assign:active {
	transform: translateY(1px);
}
.btn-assign:disabled {
	background: #d7cec4;
	cursor: not-allowed;
}
.is-spot-selected::before {
	content: "";
	position: absolute;
	top: 0;
	left: 0; /* overflow:hidden 때문에 음수로 빼지 말고 내부에 그린다 */
	width: var(--slot-border); /* 보더 두께만큼 */
	height: 100%;
	background: var(--slot-border-color);
	pointer-events: none;
	z-index: 1; /* 라벨(1)과 겹치면 0~1 사이로 조절 */
}
.row > .slot.is-spot-selected:first-child::before,
.row > .aisle + .slot.is-spot-selected::before {
	display: none;
}
/* 슬롯 클릭 선택 하이라이트 */
.is-spot-selected {
	z-index: 4; /* 게이트/이웃 슬롯보다 위 */
	transform: translateY(-2px) scale(1.04);
	/* ⛔ outline 제거해서 이중 테두리 방지 */
	outline: none;

	/* 펄스는 drop-shadow로 → overflow에 안 잘리고 훨씬 잘 보임 */
	filter: drop-shadow(0 0 4px rgba(255, 255, 255, 0.35)) drop-shadow(0 0 10px rgba(162, 146, 128, 0.35));

	animation: glowPulse 1.2s ease-in-out infinite;
}
/* 더 잘 보이는 글로우 펄스 */
@keyframes glowPulse {
	0% {
		filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.25)) drop-shadow(0 0 8px rgba(162, 146, 128, 0.25));
	}
	50% {
		filter: drop-shadow(0 0 12px rgba(255, 255, 255, 0.85)) drop-shadow(0 0 24px rgba(162, 146, 128, 0.65));
	}
	100% {
		filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.25)) drop-shadow(0 0 8px rgba(162, 146, 128, 0.25));
	}
}
/* 모션 줄이기 선호시 최소화 */
@media (prefers-reduced-motion: reduce) {
	.slot {
		transition: none;
	}
	.is-spot-selected {
		transform: none;
		animation: none;
		filter: none;
		box-shadow: inset 0 0 0 2px #fff; /* 정적 하이라이트만 */
	}
}

@keyframes slotPulse {
	0% {
		box-shadow: 0 0 0 0 rgba(162, 146, 128, 0.45);
		opacity: 1;
	}
	70% {
		box-shadow: 0 0 0 14px rgba(162, 146, 128, 0);
		opacity: 0.85;
	}
	100% {
		box-shadow: 0 0 0 0 rgba(162, 146, 128, 0);
		opacity: 1;
	}
}
.slot-plate {
	position: absolute;
	top: 55px;
	left: 0;
	right: 0;
	text-align: center;
	font-size: 17px;
	font-weight: 800;
	color: #000000;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
	pointer-events: none;
	z-index: 2;
}
/* ===== 차단바(Gate) - 사진 스타일 ===== */
.gate {
	/* 크기/색 변수 */
	--pole-w: 10px; /* 기둥 너비 */
	--pole-h: 80px; /* 기둥 높이 */
	--box: 30px; /* 작은 네모 한 변 */
	--gap-x: 0px; /* 기둥과 상자 사이 간격 */
	--pole-background: #ff5b5b; /* 기둥 테두리(밝은 빨강) */
	--box-background: #ffe521; /* 상자 테두리(짙은 자주/빨강) */

	position: absolute;
	left: 215px; /* 지도 왼쪽에서의 위치(필요시 조정) */
	width: calc(var(--pole-w) + var(--gap-x) + var(--box));
	height: var(--pole-h);
	z-index: 2; /* 슬롯 위, SVG 오버레이 아래 */
	pointer-events: none;
}

/* 위/아래 게이트의 수직 위치만 다름 */
.gate--top {
	top: 170px;
} /* 필요시 숫자만 조정 */
.gate--bottom {
	bottom: 170px;
}

/* 기둥: 속 빈 사각형 */
.gate-pole {
	position: absolute;
	top: 0;
	left: 0;
	width: var(--pole-w);
	height: var(--pole-h);
	background: var(--pole-background);
	box-sizing: border-box;
}

/* 작은 네모: 오른쪽으로 떨어져서 위치 */
.gate-box {
	position: absolute;
	left: calc(var(--pole-w) + var(--gap-x));
	width: var(--box);
	height: var(--box);
	background: var(--box-background);
	box-sizing: border-box;
}

/* ⬆️ 위 게이트: 상단에 붙여 배치 */
.gate--top .gate-box {
	top: -10px; /* 살짝 위로(음수면 테두리 맞춤) */
}

/* ⬇️ 아래 게이트: 하단에 붙여 배치 */
.gate--bottom .gate-box {
	bottom: -10px;
}
.manual-status-controls {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 8px;
	margin-top: 19px;
}
.btn-status {
	padding: 8px 10px;
	border: 0;
	border-radius: 8px;
	font-weight: 800;
	background: #6b7280;
	color: #fff;
	cursor: pointer;
	transition: background 0.2s;
}
.btn-status:hover {
	background: #4b5563;
}
.btn-status:disabled {
	background: #cbd5e1;
	cursor: not-allowed;
}
.hint.warn {
	color: #b45309;
}
/* ===== 공통 선택 카드 ===== */
.selection-card {
	background: #fff;
	border: 1px solid #e6dfd6;
	border-radius: 12px;
	padding: 12px 14px;
	box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
}
.selection-row {
	display: flex;
	align-items: center;
	gap: 8px;
	min-height: 28px;
	font-weight: 800;
	color: #403a34;
}

.selection-label {
	color: #6b6257;
	font-weight: 900;
	letter-spacing: 0.2px;
}
.selection-slot {
	color: #0f172a;
	font-weight: 900;
}
.dot {
	color: #9aa0a6;
}
.selection-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 8px;
}

.selection-title {
	font-weight: 900;
	color: #403a34;
}

.status-pill {
	padding: 2px 8px;
	border-radius: 999px;
	font-size: 12px;
	font-weight: 800;
	text-transform: capitalize;
	background: #e5e7eb;
	color: #374151;
}
.status-pill[data-status="free"] {
	background: #e8f7ec;
	color: #166534;
}
.status-pill[data-status="reserved"] {
	background: #fff7cc;
	color: #92400e;
}
.status-pill[data-status="occupied"] {
	background: #fde2e2;
	color: #991b1b;
}
.status-pill[data-status="none"] {
	background: #e5e7eb;
	color: #6b7280;
}
/* 빠르게 나타나는 짧은 애니메이션 (장식 없음) */
@keyframes flashIn {
	0% {
		opacity: 0;
		transform: translateY(2px) scale(0.995);
	}
	100% {
		opacity: 1;
		transform: translateY(0) scale(1);
	}
}
.flash-in {
	animation: flashIn 300ms ease-out;
}

.assign-panel .panel-card + .panel-card {
	margin-top: 8px;
}

/* 패널 간격 살짝 조정 */
.assign-panel .panel-card + .panel-card {
	margin-top: 8px;
}
/* 차량 이미지 레이어(지도 위에 절대배치) */
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

/* 실제 이미지 */
.car-img {
	width: 120%;
	height: 120%;
	display: block;
	object-fit: contain; /* 비율 유지 */
	pointer-events: none;
}

/* 번호판/트랙ID 라벨 */
.car-label {
	position: absolute;
	left: 50%;
	top: -18px; /* 차량 위에 살짝 */
	transform: translateX(-50%);
	font-size: 16px;
	font-weight: 800;
	color: #ff0;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
	white-space: nowrap;
	pointer-events: none;
}
</style>
