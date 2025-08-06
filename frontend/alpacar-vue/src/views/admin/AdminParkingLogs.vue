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
		// 실시간 로그를 저장할 배열
		const logs = ref<
			Array<{
				id: number;
				license_plate: string;
				location: string;
				entrance_time: string | null;
				parking_time: string | null;
				exit_time: string | null;
				status: string;
			}>
		>([]);

		let ws: WebSocket;

		onMounted(() => {
			// 백엔드 WebSocket URL
			ws = new WebSocket("wss://i13e102.p.ssafy.io/ws/parking-logs/");
			// ws = new WebSocket("ws://localhost:8000/ws/parking-logs/");

			ws.onopen = () => {
				console.log("WS 연결 성공: 주차 로그 수신 대기");
			};

			ws.onmessage = (event) => {
				// 서버로부터 { id, license_plate, location, entrance_time, parking_time, exit_time, status } 형태로 수신
				const data = JSON.parse(event.data);
				const idx = logs.value.findIndex((e) => e.id === data.id);
				if (idx !== -1) {
					// 이미 존재하면 업데이트
					logs.value[idx] = data;
				} else {
					// 신규 이벤트면 맨 앞에 추가
					logs.value.unshift(data);
				}
			};

			ws.onerror = (err) => {
				console.error("WS 오류:", err);
			};

			ws.onclose = () => {
				console.log("WS 연결 종료");
			};
		});

		onBeforeUnmount(() => {
			if (ws && ws.readyState === WebSocket.OPEN) {
				ws.close();
			}
		});

		return { logs };
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
