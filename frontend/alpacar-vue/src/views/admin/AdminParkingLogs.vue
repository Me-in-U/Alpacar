<template>
	<div class="page-wrapper">
		<AdminNavbar :showLogout="false" />
		<div class="container">
			<p class="title">주차 이벤트 로그</p>

			<div class="card">
				<div class="log-table-wrapper">
					<table class="log-table">
						<thead>
							<tr>
								<th>차량 번호</th>
								<th>주차 위치(임시 모델)</th>
								<th>입차 시각</th>
								<th>주차 시각</th>
								<th>출차 시각</th>
								<th>상태</th>
								<th>액션</th>
								<!-- 추가 -->
							</tr>
						</thead>
						<tbody>
							<tr v-for="evt in logs" :key="evt.id">
								<td>{{ evt.license_plate }}</td>
								<td>{{ evt.location }}</td>
								<td>{{ formatDate(evt.entrance_time) }}</td>
								<td>{{ formatDate(evt.parking_time) }}</td>
								<td>{{ formatDate(evt.exit_time) }}</td>

								<td>{{ evt.status }}</td>
								<td>
									<button @click="manualParking(evt.vehicle_id)">주차완료</button>
									<button @click="manualExit(evt.vehicle_id)">출차</button>
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

			ws = new WebSocket("wss://i13e102.p.ssafy.io/ws/parking-logs/");
			// ws = new WebSocket("ws://localhost:8000/ws/parking-logs/");
			ws.onopen = () => console.log("[WS] 연결 열림");
			ws.onerror = (e) => console.error("[WS] 에러", e);
			ws.onclose = () => console.warn("[WS] 연결 종료");
			ws.onmessage = (ev) => {
				const d = JSON.parse(ev.data);
				const idx = logs.value.findIndex((e) => e.id === d.id);
				if (idx >= 0) logs.value.splice(idx, 1, d);
				// 새 로그가 끝 페이지에 있으면 무시
			};
		});
		onBeforeUnmount(() => ws?.close());
		const goNext = () => nextPage.value && fetchPage(nextPage.value);
		const goPrev = () => prevPage.value && fetchPage(prevPage.value);

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
		};
	},
});
</script>

<style scoped>
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

.title {
	font-size: 36px;
	font-weight: 700;
	font-family: "Inter-Bold", Helvetica;
	color: #333333;
	margin-bottom: 32px;
}

.card {
	background-color: #faf8f5;
	width: 100%;
	flex: 1;
	padding: 48px;
	border-radius: 16px;
	box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
	box-sizing: border-box;
}

.log-table-wrapper {
	width: 100%;
	overflow-x: auto;
}

.log-table {
	width: 100%;
	border-collapse: collapse;
}

.log-table th {
	text-align: left;
	padding: 12px;
	font-weight: 600;
	color: #333333;
	border-bottom: 1px solid #ccc;
}

.log-table td {
	padding: 12px;
	color: #666666;
	border: none;
}

.pagination {
	margin-top: auto; /* 위쪽 여백을 자동으로 채워서 맨 아래로 */
	display: flex;
	justify-content: center; /* 중앙 정렬 */
	padding-top: 16px;
	border-top: 1px solid #e0e0e0; /* 분리선 */
}

.pagination button {
	margin: 0 8px;
	padding: 8px 16px;
	border: none;
	border-radius: 4px;
	background-color: #a29280;
	color: #ffffff;
	font-weight: 600;
	cursor: pointer;
	transition: background-color 0.3s;
}

.pagination button:disabled {
	background-color: #cccccc;
	cursor: not-allowed;
}

.pagination button:not(:disabled):hover {
	background-color: #6e6257;
}
/* Mobile 대응 */
@media (max-width: 768px) {
	.container {
		padding: 32px 24px;
	}
	.title {
		font-size: 28px;
		margin-bottom: 24px;
	}
	.card {
		padding: 24px;
	}
}
</style>
