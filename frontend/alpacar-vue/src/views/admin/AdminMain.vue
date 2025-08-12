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
						<svg class="overlay" :width="layout.mapW" :height="layout.mapH">
							<g v-for="obj in vehicles" :key="obj.track_id">
								<polygon :points="toPoints(obj.corners, layout.carOffsetX, layout.carOffsetY)" fill="none" stroke="#ff0" stroke-width="2" />
								<text :x="obj.center[0] + layout.carOffsetX" :y="obj.center[1] + layout.carOffsetY" font-size="36" fill="#ff0" text-anchor="middle">
									{{ obj.track_id }}
								</text>
							</g>
						</svg>

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
										<div class="slot-actions">
											<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
											<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
											<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
										</div>
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
										<div class="slot-actions">
											<button class="btn-mini" @click.stop="setSlot(spot, 'free')">F</button>
											<button class="btn-mini" @click.stop="setSlot(spot, 'occupied')">O</button>
											<button class="btn-mini" @click.stop="setSlot(spot, 'reserved')">R</button>
										</div>
									</div>
								</template>
							</div>

							<div v-if="layout.showDivider && idx === 0" class="divider"></div>
						</template>
					</div>

					<!-- 우: 선택 요약/배정 -->
					<aside class="assign-panel">
						<div class="panel-card">
							<div class="panel-title">수동 배정</div>
							<div class="panel-line">
								<span class="plabel">차량</span>
								<span class="pvalue">{{ selectedVehicle?.license_plate || "-" }}</span>
							</div>
							<div class="panel-line">
								<span class="plabel">슬롯</span>
								<span class="pvalue">{{ selectedSpot || "-" }}</span>
							</div>
							<button class="btn-assign" :disabled="!canAssign" @click="assignSelected">배정하기</button>
							<p class="hint">• 차량을 고르고, 지도에서 <b>비어있는</b> 슬롯을 클릭하세요.</p>
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

/* 
  백엔드 엔드포인트
  - REST: BACKEND_BASE_URL 사용(예: https://api.example.com)
  - WS: 배포 환경에 맞춰 wss:// 로 교체
*/

const WSS_JETSON_URL = `wss://i13e102.p.ssafy.io/ws/jetson/`;

export default defineComponent({
	components: { AdminNavbar, AdminAuthRequiredModal },
	setup() {
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
		type SpacePayload = Record<
			string,
			{
				status: "free" | "occupied" | "reserved";
				size: string | null;
				vehicle_id?: number | null;
				license_plate?: string | null;
			}
		>;

		const spaceVehicleMap = reactive<Record<string, { vehicle_id: number | null; plate: string | null }>>({});
		const selectedVehicle = ref<null | ActiveVehicleItem>(null);
		const selectedSpot = ref<string | null>(null);
		const activeVehicles = ref<Array<ActiveVehicleItem>>([]);

		async function fetchActiveVehicles() {
			const token = localStorage.getItem("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicle-events/active/`, {
				headers: { Authorization: `Bearer ${token}` },
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
			if (statusMap[spot] !== "free") return;
			selectedSpot.value = selectedSpot.value === spot ? null : spot;
		}
		const canAssign = computed(() => !!selectedVehicle.value && !!selectedSpot.value);

		async function assignSelected() {
			if (!canAssign.value) return;
			const token = localStorage.getItem("access_token");
			const plate = selectedVehicle.value!.license_plate;
			const { zone, slot_number } = parseSpot(selectedSpot.value!);
			const slotLabel = selectedSpot.value!;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/parking/assign/`, {
					method: "POST",
					headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
					body: JSON.stringify({ license_plate: plate, zone, slot_number }),
				});
				if (!res.ok) throw new Error(await res.text());
				statusMap[slotLabel] = "reserved";
				spaceVehicleMap[slotLabel] = { vehicle_id: selectedVehicle.value!.vehicle_id, plate };
				const v = activeVehicles.value.find((x) => x.vehicle_id === selectedVehicle.value!.vehicle_id);
				if (v) {
					v.assigned_space = { id: 0, zone, slot_number, label: slotLabel, status: "reserved" };
				}
				alert(`배정 완료: ${plate} → ${slotLabel}`);
				selectedSpot.value = null;
				selectedVehicle.value = null;
			} catch (e) {
				console.error(e);
				alert("배정 중 오류가 발생했습니다.");
			}
		}

		/* ===== 레이아웃 ===== */
		const layout = reactive({
			mapW: 900,
			mapH: 550,
			slotW: 85,
			slotH: 150,
			slotGap: 6,
			aisleW: 28,
			dividerMargin: 110,
			showDivider: true,
			bgColor: "#4c4c4c",
			carOffsetX: 5,
			carOffsetY: 0,
			offsetTopX: 0,
			offsetBottomX: 0,
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
			{ key: "occupied", title: "사용중", value: occupiedCount.value, unit: "개", color: "c-orange", icon: "🅿️", live: true },
			{ key: "free", title: "빈 공간", value: freeCount.value, unit: "개", color: "c-green", icon: "✅", live: true },
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
			}>
		>([]);

		let ws: WebSocket | null = null;
		let usageTimer: ReturnType<typeof setInterval>;

		function connectWS() {
			ws = new WebSocket(WSS_JETSON_URL);
			ws.onopen = () => console.log("[Jetson WS] ✅ Connected");
			ws.onerror = (e) => console.error("[Jetson WS] ❌ Error:", e);
			ws.onclose = () => console.warn("[Jetson WS] 🔒 Closed");

			ws.onmessage = (e) => {
				try {
					const data = JSON.parse(e.data);

					// A) car_position.update → 배열 그대로
					if (Array.isArray(data)) {
						vehicles.splice(0, vehicles.length, ...data);
						return;
					}

					// B) active_vehicles.update → {results:[...]}
					if (data && data.results && Array.isArray(data.results)) {
						const rows: any[] = data.results;
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
								status: ev.status,
								assigned_space: assigned,
							};
						});
						// 슬롯 위 번호판 동기화(옵션)
						const bySlot: Record<string, { vehicle_id: number | null; plate: string | null }> = {};
						for (const v of activeVehicles.value) {
							if (v.assigned_space?.label) {
								bySlot[v.assigned_space.label] = { vehicle_id: v.vehicle_id, plate: v.license_plate };
							}
						}
						Object.keys(spaceVehicleMap).forEach((k) => delete spaceVehicleMap[k]);
						Object.assign(spaceVehicleMap, bySlot);
						return;
					}

					// C) 젯슨 원본 텔레메트리 {slot:{...}, vehicles:[...]}
					if (data && (data.slot || data.vehicles)) {
						// 슬롯 반영
						if (data.slot) {
							Object.entries(data.slot as Record<string, "free" | "occupied" | "reserved">).forEach(([label, status]) => {
								if (label in statusMap) statusMap[label] = status;
							});
						}
						// 차량 변환 후 반영
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
								};
							});
							vehicles.splice(0, vehicles.length, ...converted);
						}
						return;
					}

					// D) parking_space.update → SpacePayload 맵
					if (data && typeof data === "object") {
						const payload = data as SpacePayload;
						const first = payload && payload[Object.keys(payload)[0] as any];
						const looksLikeSpaceMap = first && typeof first === "object" && "status" in first;
						if (looksLikeSpaceMap) {
							Object.entries(payload).forEach(([slot, info]) => {
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
							return;
						}
					}
				} catch (err) {
					console.error("[Jetson WS] parse error:", err, e.data);
				}
			};
		}

		async function fetchUsageToday() {
			try {
				const token = localStorage.getItem("access_token");
				const res = await fetch(`${BACKEND_BASE_URL}/parking/stats/today/`, {
					headers: { Authorization: `Bearer ${token}` },
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
		});
		onBeforeUnmount(() => {
			ws?.close();
			clearInterval(usageTimer);
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
			const token = localStorage.getItem("access_token");
			const { zone, slot_number } = parseSpot(spot);
			const prev = statusMap[spot];
			statusMap[spot] = status;
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/parking/space/set-status/`, {
					method: "POST",
					headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
					body: JSON.stringify({ zone, slot_number, status }),
				});
				if (!res.ok) throw new Error(await res.text());
			} catch (e) {
				console.error("[setSlot] error:", e);
				statusMap[spot] = prev;
				alert("상태 변경 실패");
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
.slot--placeholder {
	visibility: hidden;
	border: 0;
	background: transparent;
}

/* 좌측 리스트 + 지도 + 우측 패널 3열 레이아웃 */
.assign-layout {
	display: grid;
	grid-template-columns: 280px auto 260px;
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

/* 슬롯 클릭 선택 하이라이트 */
.is-spot-selected {
	outline: 3px solid rgba(162, 146, 128, 0.55);
	box-shadow: inset 0 0 0 2px #fff;
}
.slot-plate {
	position: absolute;
	top: 55px;
	left: 0;
	right: 0;
	text-align: center;
	font-size: 14px;
	font-weight: 800;
	color: #000000;
	color: #000000;
	text-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
	pointer-events: none;
	z-index: 2;
}
</style>
