<template>
  <div class="main-page-container">
    <Header />

    <div class="main-content">
      <!-- 페이지 제목 + 정보 박스 -->
      <section class="recommend-header">
        <p class="title">추천 주차 위치</p>
        <div class="info-box">
          <div class="info-title">추천 위치: A3</div>
          <div class="info-detail">예상 소요시간: 2분</div>
          <div class="info-detail">난이도: 쉬움 (초급자 적합)</div>
        </div>
      </section>

      <!-- 맵 + 범례 섹션 -->
      <div class="map-section">
        <div class="map-placeholder">
          <!-- 실제 주차장 맵 컴포넌트를 여기에 넣으세요 -->
        </div>
        <div class="legend">
          <div class="legend-item">
            <div class="rectangle green"></div>
            <span class="label">추천</span>
          </div>
          <span class="divider">|</span>
          <div class="legend-item">
            <div class="rectangle red"></div>
            <span class="label">사용 중</span>
          </div>
        </div>
      </div>

      <!-- 완료 버튼 -->
      <div class="complete-btn-wrapper">
        <div class="complete-btn" @click="onComplete">
          <span>주차 완료</span>
        </div>
      </div>
    </div>

    <BottomNavigation />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import Header from '@/components/Header.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'

const router = useRouter()
function onComplete() {
  router.push('/parking-complete')
}
</script>

<style scoped>
/* 컨테이너: 모바일 100vw/100vh, 데스크탑 440x100% */
.main-page-container {
  width: 440px;
  height: 956px;
  position: relative;
  background: #f3eeea;
  overflow: hidden;
  margin: 0 auto;
}

/* 콘텐츠 영역: 헤더/네비 제외하고 스크롤 가능 */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 64px 20px 0; /* Header 높이 64px */
  box-sizing: border-box;
}

/* 제목 + 정보박스 */
.recommend-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0 16px;
}
.title {
  font-size: 28px;
  font-weight: 700;
  color: #333333;
  margin: 0 0 8px;
  text-align: center;
}
.info-box {
  background: #ffffff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  width: 60%;
  max-width: 260px;
  margin: 0 auto 16px;
  text-align: center;
}
.info-title {
  font-size: 20px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 8px;
}
.info-detail {
  font-size: 18px;
  color: #666666;
  margin: 2px 0;
}

/* ─── 맵 + 범례 컨테이너 ─── */
.map-section {
  width: 80%;
  margin: 16px auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.map-placeholder {
  width: 100%;
  height: 300px;
  background: #dddddd;
  border-radius: 8px;
  box-sizing: border-box;
}
/* 범례: 맵 바로 아래, 오른쪽 정렬 */
.map-section .legend {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.rectangle {
  width: 11px;
  height: 11px;
  border-radius: 1px;
}
.green { background-color: #8fcd2b; }
.red   { background-color: #fe5454; }
.label,
.divider {
  font-size: 14px;
  color: #333333;
  font-family: Inter, sans-serif;
}

/* 완료 버튼 */
.complete-btn-wrapper {
  width: 100%;
  display: flex;
  justify-content: center;
  margin: 24px 0;
}
.complete-btn {
  width: 80%;
  height: 50px;
  background-color: #6ba368;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background-color 0.2s;
}
.complete-btn:hover {
  background-color: #5a9857;
}
.complete-btn span {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
}

/* 반응형: 폭 ≤ 440px */
@media (max-width: 440px) {
  .main-page-container {
    width: 100vw;
    height: 100vh;
  }
  .map-section {
    width: 90%;
  }
  .map-placeholder {
    height: 200px;
  }
}
@media (min-width: 441px) {
  .main-page-container {
    width: 440px;
    margin: 0 auto;
  }
}
</style>
