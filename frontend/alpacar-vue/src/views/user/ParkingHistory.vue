<template>
	<div class="parking-history-page">
		<!-- Header Component -->
		<Header />

		<!-- Main Content -->
		<div class="main-content">
			<h1 class="page-title">내 주차기록 확인하기</h1>

			<!-- Loading State -->
			<div v-if="isLoading" class="loading-container">
				<p class="loading-text">데이터를 불러오는 중...</p>
			</div>

			<!-- Error State -->
			<div v-else-if="error" class="error-container">
				<p class="error-text">{{ error }}</p>
				<button @click="loadParkingData" class="retry-btn">다시 시도</button>
			</div>

			<!-- Parking History Section -->
			<section v-else class="history-section">
				<h2 class="section-title">주차 이력</h2>

				<!-- Empty State -->
				<div v-if="allRecords.length === 0" class="empty-state">
					<p class="empty-text">아직 주차 이력이 없습니다.</p>
				</div>

				<!-- Records List -->
				<div v-else v-for="record in displayedRecords" :key="record.id" class="history-item">
					<div class="history-details">
						<p class="history-text">주차 일시 : {{ record.date }} {{ record.time }}</p>
						<p class="history-text">주차 공간 : {{ record.space }}</p>
						<p class="history-text score">주차점수 : {{ record.score }}점</p>
					</div>
				</div>

				<!-- 더보기 버튼 -->
				<div v-if="!showAllRecords && allRecords.length > 3" class="show-more-container">
					<button class="show-more-btn" @click="showAllRecords = true">더보기</button>
				</div>

				<!-- 접기 버튼 -->
				<div v-if="showAllRecords" class="show-more-container">
					<button class="show-more-btn" @click="showAllRecords = false">접기</button>
				</div>
			</section>

			<!-- Parking Score History Chart Section -->
			<section v-if="!isLoading && !error" class="chart-section">
				<h2 class="section-title">주차점수 히스토리</h2>

				<!-- Empty State for Chart -->
				<div v-if="!chartData || (chartData.scores && chartData.scores.length === 0)" class="empty-state">
					<p class="empty-text">아직 주차 점수 이력이 없습니다.</p>
				</div>

				<!-- Chart Component -->
				<ParkingScoreChart v-else :data="chartData" />
			</section>
		</div>

		<!-- Bottom Navigation -->
		<BottomNavigation />
	</div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
import ParkingScoreChart from "@/components/ParkingScoreChart.vue";
import parkingAPI from "@/api/parking";
import { SecureTokenManager } from "@/utils/security";

const router = useRouter();

// 더보기 상태 관리
const showAllRecords = ref(false);

// 데이터 상태 관리
const allRecords = ref([]);
const isLoading = ref(true);
const error = ref(null);

// 표시할 레코드
const displayedRecords = computed(() => {
	return showAllRecords.value ? allRecords.value : allRecords.value.slice(0, 3);
});

// 차트 데이터를 reactive로 관리
const chartData = ref(null);

// 데이터 로드 함수
const loadParkingData = async () => {
	try {
		isLoading.value = true;
		error.value = null;

		// 토큰 확인 (SecureTokenManager 사용)
		const token = SecureTokenManager.getSecureToken("access_token");
		if (!token) {
			console.error("No access token found - redirecting to login");
			router.push("/login");
			return;
		}

		console.log("Loading parking data with token:", token ? "Present" : "Missing");

		// 주차 이력 데이터 가져오기
		try {
			const historyResponse = await parkingAPI.getParkingHistory();
			allRecords.value = historyResponse.data || [];
			console.log("History loaded:", allRecords.value);
		} catch (historyErr) {
			console.error("Failed to load history:", historyErr);
			// 히스토리 로드 실패해도 차트는 시도
			allRecords.value = [];
		}

		// 차트 데이터 가져오기
		try {
			const chartResponse = await parkingAPI.getChartData();
			chartData.value = chartResponse.data || null;
			console.log("Chart data loaded:", chartData.value);
		} catch (chartErr) {
			console.error("Failed to load chart data:", chartErr);
			// 차트 로드 실패해도 계속 진행
			chartData.value = null;
		}

		// 데이터가 없는 것은 정상적인 상태일 수 있으므로 에러로 처리하지 않음
		// 실제 네트워크 에러는 catch 블록에서 처리됨
	} catch (err) {
		console.error("Failed to load parking data:", err);
		console.error("Error details:", {
			message: err.message,
			response: err.response,
			request: err.request,
			config: err.config,
		});

		// 에러 메시지 설정
		if (err.message) {
			error.value = err.message;
		} else {
			error.value = "서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.";
		}

		// 401 에러인 경우 로그인 페이지로 이동
		if (err.response?.status === 401) {
			console.log("401 Unauthorized - clearing tokens and redirecting to login");
			SecureTokenManager.clearAllSecureTokens();
			router.push("/login");
		}
	} finally {
		isLoading.value = false;
	}
};

onMounted(() => {
	loadParkingData();
});
</script>

<style scoped>
.parking-history-page {
	width: 440px;
	height: 956px;
	position: relative;
	background: #f3eeea;
	overflow: hidden;
	margin: 0 auto;
}

.main-content {
	position: relative;
	padding-top: 80px;
	height: calc(100% - 160px);
	overflow-y: auto;
	padding-left: 50px;
	padding-right: 50px;
}

.page-title {
	color: #000000;
	font-size: 24px;
	font-weight: 700;
	font-family: "Inter", "Noto Sans KR", sans-serif;
	margin: 40px 0 40px 0;
	line-height: 1.2;
}

.history-section {
	margin-bottom: 50px;
}

.section-title {
	color: #333333;
	font-size: 20px;
	font-weight: 600;
	font-family: "Inter", "Noto Sans KR", sans-serif;
	margin: 0 0 20px 0;
	line-height: 1.2;
}

.history-item {
	background: #ebe3d5;
	border: 1px solid #b3b3b3;
	border-radius: 10px;
	box-shadow: 4px 4px 4px 0px rgba(0, 0, 0, 0.25);
	margin-bottom: 15px;
	padding: 15px;
	width: 100%;
	box-sizing: border-box;
}

.history-details {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.history-text {
	color: #000000;
	font-size: 18px;
	font-weight: 400;
	font-family: "Inter", "Noto Sans KR", sans-serif;
	margin: 0;
	line-height: 1.2;
}

.history-text.score {
	color: #776b5d;
	font-weight: 600;
}

.show-more-container {
	display: flex;
	justify-content: center;
	margin-top: 15px;
}

.show-more-btn {
	background: #776b5d;
	color: #ffffff;
	border: none;
	border-radius: 20px;
	padding: 10px 20px;
	font-size: 14px;
	font-weight: 500;
	font-family: "Inter", "Noto Sans KR", sans-serif;
	cursor: pointer;
	transition: all 0.3s ease;
}

.show-more-btn:hover {
	background: #665a4d;
	transform: translateY(-1px);
	box-shadow: 0 2px 8px rgba(119, 107, 93, 0.3);
}

.chart-section {
	margin-bottom: 30px;
}

/* Loading, Error, Empty States */
.loading-container,
.error-container,
.empty-state {
	text-align: center;
	padding: 40px 20px;
}

.loading-text,
.error-text,
.empty-text {
	color: #666666;
	font-size: 16px;
	font-family: "Inter", "Noto Sans KR", sans-serif;
	margin: 0;
	line-height: 1.4;
}

.error-text {
	color: #d32f2f;
	margin-bottom: 20px;
}

.retry-btn {
	background: #776b5d;
	color: #ffffff;
	border: none;
	border-radius: 6px;
	padding: 10px 20px;
	font-size: 14px;
	font-weight: 500;
	font-family: "Inter", "Noto Sans KR", sans-serif;
	cursor: pointer;
	transition: all 0.3s ease;
}

.retry-btn:hover {
	background: #665a4d;
	transform: translateY(-1px);
	box-shadow: 0 2px 8px rgba(119, 107, 93, 0.3);
}

/* Responsive Design */
@media (max-width: 440px) {
	.parking-history-page {
		width: 100vw;
		height: 100vh;
	}

	.main-content {
		padding-left: 45px;
		padding-right: 45px;
	}

	.page-title {
		font-size: 22px;
		margin: 30px 0 30px 0;
	}

	.section-title {
		font-size: 18px;
	}

	.history-text {
		font-size: 16px;
	}
}

@media (min-width: 441px) {
	.parking-history-page {
		width: 440px;
		height: auto;
		min-height: 100vh;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
	}

	.main-content {
		flex: 1;
		height: auto;
		min-height: calc(100vh - 160px);
		padding-bottom: 20px;
	}
}
</style>
