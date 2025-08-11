<!-- src\views\admin\AdminParkingLogs.vue -->
<template>
	<div class="page-wrapper">
		<AdminNavbar :showLogout="false" />
		<div class="container">
			<div class="title-wrapper">
				<p class="title">주차 이벤트 로그</p>
				<div class="push-control">
					<input v-model="pushPlate" placeholder="차량번호 입력" class="push-input" />
					<button class="btn btn--primary" @click="manualEntrance">수동입차</button>
					<button class="btn btn--outline" @click="sendPush">푸시 발송</button>
				</div>
			</div>

			<div class="card">
				<div class="log-table-wrapper">
					<table class="log-table">
						<thead>
							<tr>
								<th>차량 번호</th>
								<th>배정/주차 정보</th>
								<th>입차 시각</th>
								<th>주차 시각</th>
								<th>출차 시각</th>
								<th>상태</th>
								<th>액션</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="evt in logs" :key="evt.id" class="log-row">
								<td class="mono">{{ evt.license_plate }}</td>
								<td>
									<template v-if="evt.assigned_space">
										{{ evt.assigned_space.label }}
										<small class="slot-status" v-if="evt.assigned_space.status"> · {{ evt.assigned_space.status }} </small>
									</template>
									<template v-else>배정안됨</template>
								</td>
								<td>{{ formatDate(evt.entrance_time) }}</td>
								<td>{{ formatDate(evt.parking_time) }}</td>
								<td>{{ formatDate(evt.exit_time) }}</td>

								<td>
									<span
										class="status-badge"
										:class="{
											'is-entrance': evt.status === 'Entrance',
											'is-parking': evt.status === 'Parking',
											'is-exit': evt.status === 'Exit',
										}"
									>
										{{ evt.status }}
									</span>
								</td>
								<td class="actions">
									<button class="btn btn--ghost" @click="manualParking(evt.vehicle_id)">주차완료</button>
									<button class="btn btn--danger" @click="manualExit(evt.vehicle_id)">출차</button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
				<div class="pagination">
					<button @click="goPrev" :disabled="!prevPage || loading">이전</button>
					<button @click="goNext" :disabled="!nextPage || loading">다음</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeUnmount } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";
import { BACKEND_BASE_URL } from "@/utils/api";

export default defineComponent({
	name: "AdminParkingLogs",
	components: { AdminNavbar },
	setup() {
		const logs = ref<any[]>([]);
		const nextPage = ref<string | null>(null);
		const prevPage = ref<string | null>(null);
		const loading = ref(false);
		let ws: WebSocket;

		// 페이지 불러오기
		const fetchPage = async (url = `${BACKEND_BASE_URL}/vehicle-events/?page=1`) => {
			loading.value = true;
			const token = localStorage.getItem("access_token");
			const res = await fetch(url, {
				method: "GET",
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
			});
			if (!res.ok) {
				console.log("이벤트 불러오기 실패", res.status, res.statusText);
				throw new Error("이벤트 불러오기 실패");
			}
			console.log("이벤트 불러오기 성공", res.status, res.statusText);
			const data = await res.json();
			logs.value = data.results;
			nextPage.value = data.next;
			prevPage.value = data.previous;
			loading.value = false;
		};
		const formatDate = (iso: string | null) => {
			if (!iso) return "-";
			// 로컬 타임존, 24h 포맷
			return new Date(iso).toLocaleString("ko-KR", {
				year: "numeric",
				month: "2-digit",
				day: "2-digit",
				hour: "2-digit",
				minute: "2-digit",
				second: "2-digit",
				hour12: false,
			});
		};
		const manualEntrance = async () => {
			const plate = pushPlate.value.trim();
			if (!plate) {
				alert("차량번호를 입력하세요");
				return;
			}
			const token = localStorage.getItem("access_token");
			try {
				const res = await fetch(`${BACKEND_BASE_URL}/vehicles/manual-entrance/`, {
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({ license_plate: plate }),
				});
				if (!res.ok) {
					const err = await res.json().catch(() => ({}));
					alert("수동입차 실패: " + (err.detail || err.message || res.status));
					return;
				}
				const data = await res.json();

				// 목록 갱신: 같은 id 있으면 교체, 없으면 맨 앞 삽입
				const idx = logs.value.findIndex((e) => e.id === data.id);
				if (idx >= 0) logs.value.splice(idx, 1, data);
				else logs.value.unshift(data);

				alert(res.status === 201 ? "입차 이벤트가 생성되었습니다." : "이미 진행 중인 이벤트를 반환했습니다.");
			} catch (e) {
				console.error(e);
				alert("수동입차 처리 중 오류가 발생했습니다.");
			}
		};

		const manualParking = async (vehicleId: number) => {
			const token = localStorage.getItem("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/${vehicleId}/manual-parking/`, {
				method: "POST",
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
			});
			if (!res.ok) throw new Error("주차완료 실패");
			const data = await res.json();

			// 기존에 같은 id가 있으면 교체, 없으면 맨 앞에 추가
			const idx = logs.value.findIndex((e) => e.id === data.id);
			if (idx >= 0) {
				logs.value.splice(idx, 1, data);
			} else {
				logs.value.unshift(data);
			}
		};

		const manualExit = async (vehicleId: number) => {
			const token = localStorage.getItem("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/${vehicleId}/manual-exit/`, {
				method: "POST",
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
			});
			if (!res.ok) throw new Error("출차 실패");
			const data = await res.json();

			const idx = logs.value.findIndex((e) => e.id === data.id);
			if (idx >= 0) {
				logs.value.splice(idx, 1, data);
			} else {
				logs.value.unshift(data);
			}
		};

		onMounted(async () => {
			await fetchPage();

			// ws = new WebSocket("ws://localhost:8000/ws/parking-logs/");
			ws = new WebSocket("wss://i13e102.p.ssafy.io/ws/parking-logs/");
			ws.onopen = () => {
				console.log("[WebSocket] ✅ Connected");
			};
			ws.onmessage = (ev) => {
				const d = JSON.parse(ev.data);
				const idx = logs.value.findIndex((e) => e.id === d.id);
				if (idx >= 0) logs.value.splice(idx, 1, d);
				// 새 로그가 끝 페이지에 있으면 무시
			};
			ws.onerror = (e) => console.error("[WebSocket] ❌ Error", e);
			ws.onclose = () => {
				console.warn("[WebSocket] 🔒 Closed");
			};
		});
		onBeforeUnmount(() => ws?.close());

		const goNext = () => nextPage.value && fetchPage(nextPage.value);
		const goPrev = () => prevPage.value && fetchPage(prevPage.value);

		const pushPlate = ref("");

		const sendPush = async () => {
			if (!pushPlate.value.trim()) {
				alert("차량번호를 입력하세요");
				return;
			}
			const token = localStorage.getItem("access_token");
			const res = await fetch(`${BACKEND_BASE_URL}/vehicles/send-push/`, {
				method: "POST",
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ license_plate: pushPlate.value.trim() }),
			});
			if (!res.ok) {
				alert("푸시 발송 실패");
				return;
			}
			alert("푸시 발송 성공");
			pushPlate.value = "";
		};

		return {
			logs,
			nextPage,
			prevPage,
			loading,
			manualParking,
			manualExit,
			formatDate,
			goNext,
			goPrev,
			pushPlate,
			sendPush,
			manualEntrance,
		};
	},
});
</script>

<style scoped>
/* ───────── Layout ───────── */
.page-wrapper {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
	background-color: #f3eeea;
}

.container {
	background-color: #f3eeea;
	min-height: calc(100vh - 64px);
	padding: 48px 64px;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
}

.title-wrapper {
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 100%;
}

.title {
	font-size: 36px;
	font-weight: 700;
	color: #333333;
}

/* ───────── Push Control ───────── */
.push-control {
	display: flex;
	align-items: center;
	gap: 10px;
}

.push-input {
	height: 36px;
	padding: 0 12px;
	border: 1px solid #d8d0c7;
	border-radius: 8px;
	outline: none;
	transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.push-input:focus {
	border-color: #a29280;
	box-shadow: 0 0 0 3px rgba(162, 146, 128, 0.18);
}

/* ───────── Buttons ───────── */
.btn {
	appearance: none;
	border: 1px solid transparent;
	border-radius: 8px;
	padding: 8px 14px;
	font-weight: 700;
	cursor: pointer;
	transition: transform 0.08s ease, background-color 0.2s ease, border-color 0.2s ease;
	user-select: none;
}
.btn:active {
	transform: translateY(1px);
}

.btn--primary {
	background-color: #a29280;
	color: #fff;
}
.btn--primary:hover {
	background-color: #8e7f6f;
}

.btn--outline {
	background-color: transparent;
	color: #6e6257;
	border: 1px solid #cfc6ba;
}
.btn--outline:hover {
	background-color: #efe9e2;
	border-color: #b8aa9a;
}

.btn--ghost {
	background: #ffffff;
	color: #6e6257;
	border: 1px solid #e6dfd6;
}
.btn--ghost:hover {
	background: #f4efe9;
	border-color: #d5c9bb;
}

.btn--danger {
	background: #c36a6a;
	color: #fff;
}
.btn--danger:hover {
	background: #b25858;
}

/* ───────── Card ───────── */
.card {
	background-color: #faf8f5;
	width: 100%;
	flex: 1;
	padding: 48px;
	border-radius: 16px;
	box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
	box-sizing: border-box;
}

/* ───────── Log Table ───────── */
.log-table-wrapper {
	width: 100%;
	overflow: auto;
	border: 1px solid #e6dfd6;
	border-radius: 12px;
	background: #ffffff;
}

.log-table {
	width: 100%;
	border-collapse: collapse;
}

.log-table thead th {
	position: sticky;
	top: 0;
	background: linear-gradient(180deg, #fbfaf8 0%, #f6f3ef 100%);
	z-index: 1;
	font-size: 16px;
	letter-spacing: 0.2px;
	color: #5a5249;
	border-bottom: 1px solid #e6dfd6;
}

.log-table th,
.log-table td {
	padding: 12px 14px;
	font-size: 15px;
	vertical-align: middle;
	text-align: center; /* 가운데 정렬 */
}

.log-table tbody tr:nth-child(odd) {
	background: #faf7f3;
}
.log-table tbody tr:hover {
	background: #f2ede7;
}

.mono {
	font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
	font-variant-numeric: tabular-nums;
}

td.actions {
	display: flex;
	justify-content: center; /* 버튼도 가운데 */
	gap: 8px;
}

/* ───────── Status Badges ───────── */
.status-badge {
	display: inline-flex;
	align-items: center;
	padding: 4px 10px;
	border-radius: 999px;
	font-size: 12px;
	font-weight: 800;
	letter-spacing: 0.2px;
	border: 1px solid transparent;
}
.status-badge.is-entrance {
	color: #24577a;
	background: #e6f4ff;
	border-color: #cde7fb;
}
.status-badge.is-parking {
	color: #2f6b4f;
	background: #e9f7ef;
	border-color: #cfeadb;
}
.status-badge.is-exit {
	color: #7a2a2a;
	background: #ffefef;
	border-color: #f3d4d4;
}

/* ───────── Pagination ───────── */
.pagination {
	margin-top: auto;
	display: flex;
	justify-content: center;
	padding-top: 16px;
	border-top: 1px solid #e0e0e0;
	gap: 12px; /* 버튼 사이 간격 */
}
.pagination button {
	all: unset;
	padding: 8px 14px;
	border-radius: 8px;
	background-color: #a29280;
	color: #ffffff;
	font-weight: 700;
	cursor: pointer;
	transition: background-color 0.2s ease, transform 0.08s ease;
}
.pagination button:hover {
	background-color: #8e7f6f;
}
.pagination button:active {
	transform: translateY(1px);
}
.pagination button:disabled {
	background-color: #d7cec4;
	color: #fff;
	cursor: not-allowed;
	transform: none;
}

/* ───────── Responsive ───────── */
@media (max-width: 768px) {
	.container {
		padding: 32px 24px;
	}
	.title {
		font-size: 28px;
	}
	.card {
		padding: 24px;
	}
}
.slot-status {
	margin-left: 4px;
	font-size: 12px;
	color: #6b7280; /* slate-500 느낌 */
}
</style>
