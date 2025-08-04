<template>
  <div class="main-page-container">
    <Header />

    <div class="main-content parking-complete">
      <!-- 완료 메시지 -->
      <h1 class="complete-title">주차가 완료되었습니다!</h1>
      <!-- 완료 아이콘 -->
      <div class="status-icon">
        <img src="@/assets/check.png" alt="주차 완료 확인">
      </div>

      <!-- 상세 정보 -->
      <div class="detail-box">
        <div class="info-item">
          <span class="label">차량번호</span>
          <span class="value">111가 1111</span>
        </div>
        <div class="info-item">
          <span class="label">주차 위치</span>
          <span class="value">A3</span>
        </div>
        <div class="info-item">
          <span class="label">주차 시간</span>
          <span class="value">2024.01.15 14:30</span>
        </div>
      </div>

      <!-- 홈으로 돌아가기 버튼 -->
      <button class="home-button" @click="goHome">홈으로 돌아가기</button>
    </div>

    <BottomNavigation />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import Header from '@/components/Header.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'

const router = useRouter()
function goHome() {
  router.push('/main')
}
</script>

<style scoped>
/* MainPage.vue 공통 컨테이너 */
.main-page-container {
  width: 440px;
  height: 956px;
  position: relative;
  background: #f3eeea;
  overflow: hidden;
  margin: 0 auto;
}

/* MainPage.vue 공통 콘텐츠 영역 */
.main-content {
  position: relative;
  padding-top: 80px; /* Header 높이 감안 */
  height: calc(100% - 160px); /* Header + BottomNavigation 높이 감안 */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}


.parking-complete .complete-title {
  font-family: 'Inter-Bold', Helvetica, sans-serif;
  font-size: 28px;
  color: #6BA368;
  margin: 0;
  padding-top: 60px;
}

/* 상세 정보 박스 */
.detail-box {
  width: 60%;
  max-width: 320px;
  background-color: #D6E3C8;
  border-radius: 8px;
  padding: 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: left;
  margin-bottom: 32px;
}

/* 각 항목 스타일 */
.detail-box .info-item {
  display: flex;
  justify-content: space-between;
  font-family: 'Inter', sans-serif;
}

/* 라벨은 항상 bold */
.detail-box .info-item:nth-child(-n+2) .label {
  font-size: 16px;
  font-weight: 600;
  color: #000;
}

.detail-box .info-item:nth-child(3) .label {
  font-size: 16px;
  font-weight: 400;
  color: #666;
}

/* 첫 두 항목의 값은 bold, 마지막 값은 normal */
.detail-box .info-item:nth-child(-n+2) .value {
  font-size: 16px;
  font-weight: 600;
  color: #000;
}
.detail-box .info-item:nth-child(3) .value {
  font-size: 16px;
  font-weight: 400;
  color: #666;
}

.parking-complete .home-button {
  width: 80%;
  background-color: #776b5d;
  color: white;
  border: none;
  padding: 16px 32px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  font-family: 'Inter-SemiBold', Helvetica, sans-serif;
}

.parking-complete .home-button:hover {
  background-color: #5f554b;
}

/* 반응형: MainPage.vue 기준 */
@media (max-width: 440px) {
  .main-page-container {
    width: 100vw;
    height: 100vh;
  }
  .main-content {
    padding-top: 60px;
  }
}
@media (min-width: 441px) {
  .main-page-container {
    width: 440px;
    margin: 0 auto;
  }
}
</style>
