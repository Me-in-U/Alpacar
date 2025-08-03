<template>
  <div class="parking-history-page">
    <!-- Header Component -->
    <Header />

    <!-- Main Content -->
    <div class="main-content">
      <h1 class="page-title">내 주차기록 확인하기</h1>
      
      <!-- Parking History Section -->
      <section class="history-section">
        <h2 class="section-title">주차 이력</h2>
        
        <div 
          v-for="record in displayedRecords" 
          :key="record.id" 
          class="history-item"
        >
          <div class="history-details">
            <p class="history-text">주차 일시 : {{ record.date }} {{ record.time }}</p>
            <p class="history-text">주차 공간 : {{ record.space }}</p>
            <p class="history-text score">주차점수 : {{ record.score }}점</p>
          </div>
        </div>
        
        <!-- 더보기 버튼 -->
        <div 
          v-if="!showAllRecords && allRecords.length > 3" 
          class="show-more-container"
        >
          <button class="show-more-btn" @click="showAllRecords = true">
            더보기
          </button>
        </div>
        
        <!-- 접기 버튼 -->
        <div 
          v-if="showAllRecords" 
          class="show-more-container"
        >
          <button class="show-more-btn" @click="showAllRecords = false">
            접기
          </button>
        </div>
      </section>

      <!-- Parking Score History Chart Section -->
      <section class="chart-section">
        <h2 class="section-title">주차점수 히스토리</h2>
        
        <!-- Chart Component -->
        <ParkingScoreChart :data="chartData" />
      </section>
    </div>

    <!-- Bottom Navigation -->
    <BottomNavigation />
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import Header from '@/components/Header.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'
import ParkingScoreChart from '@/components/ParkingScoreChart.vue'
import { mockParkingRecords, getChartData } from '@/data/mockData.js'

// 더보기 상태 관리
const showAllRecords = ref(false)

// 테스트 데이터 가져오기
const allRecords = mockParkingRecords
const displayedRecords = computed(() => {
  return showAllRecords.value ? allRecords : allRecords.slice(0, 3)
})

// 차트 데이터를 reactive로 관리
const chartData = ref(null)

onMounted(() => {
  // 컴포넌트가 마운트된 후 차트 데이터 설정
  const data = getChartData()
  chartData.value = data
  console.log('ParkingHistory - Chart data loaded:', data)
})
</script>

<style scoped>
.parking-history-page {
  width: 440px;
  height: 956px;
  position: relative;
  background: #F3EEEA;
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
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
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
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
  margin: 0 0 20px 0;
  line-height: 1.2;
}

.history-item {
  background: #EBE3D5;
  border: 1px solid #B3B3B3;
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
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
  margin: 0;
  line-height: 1.2;
}

.history-text.score {
  color: #776B5D;
  font-weight: 600;
}

.show-more-container {
  display: flex;
  justify-content: center;
  margin-top: 15px;
}

.show-more-btn {
  background: #776B5D;
  color: #FFFFFF;
  border: none;
  border-radius: 20px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
}

.show-more-btn:hover {
  background: #665A4D;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(119, 107, 93, 0.3);
}

.chart-section {
  margin-bottom: 30px;
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