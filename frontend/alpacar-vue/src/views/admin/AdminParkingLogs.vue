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
								<th>주차 위치</th>
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
								<td>{{ evt.entrance_time || "-" }}</td>
								<td>{{ evt.parking_time || "-" }}</td>
								<td>{{ evt.exit_time || "-" }}</td>
								<td>{{ evt.status }}</td>
								<td>
									<button @click="manualParking(evt.vehicle_id)">주차완료</button>
									<button @click="manualExit(evt.vehicle_id)">출차</button>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</div>
	</div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onBeforeUnmount } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";

export default defineComponent({
	name: "AdminParkingLogs",
	components: { AdminNavbar },
	setup() {
		const logs = ref<Array<any>>([]);
		let ws: WebSocket;

		const manualParking = async (vehicleId: number) => {
			const res = await fetch(`/api/vehicles/${vehicleId}/manual-parking/`, { method: "POST", credentials: "include" });
			if (!res.ok) throw new Error("주차완료 실패");
			const data = await res.json();
			logs.value.unshift(data);
		};

		const manualExit = async (vehicleId: number) => {
			const res = await fetch(`/api/vehicles/${vehicleId}/manual-exit/`, { method: "POST", credentials: "include" });
			if (!res.ok) throw new Error("출차 실패");
			const data = await res.json();
			logs.value.unshift(data);
		};

		onMounted(() => {
			ws = new WebSocket("wss://i13e102.p.ssafy.io/ws/parking-logs/");
			ws.onmessage = (ev) => {
				const d = JSON.parse(ev.data);
				const idx = logs.value.findIndex((e) => e.id === d.id);
				idx >= 0 ? logs.value.splice(idx, 1, d) : logs.value.unshift(d);
			};
		});
		onBeforeUnmount(() => ws?.close());

		return { logs, manualParking, manualExit };
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
