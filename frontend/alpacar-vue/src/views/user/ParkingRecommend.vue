<template>
  <div class="main-page-container">
    <Header />

    <div class="main-content">
      <!-- 제목 + 정보박스 -->
      <section class="recommend-header">
        <p class="title">추천 주차 위치</p>
        <div class="info-box">
          <div class="info-title">추천 위치: {{ recommendedId }}</div>
          <div class="info-detail">예상 소요시간: 2분</div>
          <div class="info-detail">난이도: 쉬움 (초급자 적합)</div>
        </div>
      </section>

      <!-- 맵 섹션 -->
      <div class="map-section">
        <div class="map-wrapper" ref="mapWrapper">
          <!-- 1행: 3칸 + 2칸 -->
          <div class="row row-1">
            <div
              v-for="spot in row1"
              :key="spot.id"
              class="spot"
              :class="spot.id === recommendedId ? 'recommended' : spot.status"
              :data-spot-id="spot.id"
            >
              {{ spot.id }}
            </div>
          </div>

          <!-- 흰 점선 -->
          <div class="divider"></div>

          <!-- 2행: 3칸 + 3칸 -->
          <div class="row row-2">
            <div
              v-for="(spot, idx) in row2"
              :key="spot.id"
              class="spot"
              :class="spot.id === recommendedId ? 'recommended' : (idx >= 3 ? 'lower ' + spot.status : spot.status)"
              :data-spot-id="spot.id"
            >
              {{ spot.id }}
            </div>
          </div>

          <!-- 추천 핀 -->
          <img
            class="pin"
            src="@/assets/pin.png"
            alt="pin"
            v-if="pinStyle.top"
            :style="pinStyle"
          />

          <!-- 차 아이콘 -->
          <img class="car" src="@/assets/my_car.png" alt="car" />
        </div>

        <!-- 범례 -->
        <div class="legend">
          <div class="legend-item">
            <div class="box recommended"></div>
            <span>추천 위치</span>
          </div>
          <div class="legend-item">
            <div class="box occupied"></div>
            <span>사용 중</span>
          </div>
          <div class="legend-item">
            <div class="box empty"></div>
            <span>미사용</span>
          </div>
        </div>
      </div>

      <!-- 완료 버튼 -->
      <div class="complete-btn-wrapper">
        <button class="complete-btn" @click="onComplete">주차 완료</button>
      </div>
    </div>

    <BottomNavigation />
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import Header from '@/components/Header.vue';
import BottomNavigation from '@/components/BottomNavigation.vue';

const router = useRouter();
// 추천 위치 (추후 props/API 연동)
const recommendedId = ref('A1');

// map-wrapper 참조
const mapWrapper = ref<HTMLElement | null>(null);
// 핀 위치 스타일
const pinStyle = reactive({ top: '', left: '' });

function updatePin() {
  nextTick(() => {
    if (!mapWrapper.value) return;
    const wrapRect = mapWrapper.value.getBoundingClientRect();
    const spotEl = mapWrapper.value.querySelector<HTMLElement>(`[data-spot-id="${recommendedId.value}"]`);
    if (!spotEl) return;
    const spotRect = spotEl.getBoundingClientRect();
    const pinW = 24;
    const pinH = 24;
    // 번호 중앙, 위로 추가 오프셋 20px
    const x = spotRect.left - wrapRect.left + spotRect.width / 2 - pinW / 2;
    const y = spotRect.top - wrapRect.top + spotRect.height / 2 - pinH / 2 - 35;
    pinStyle.left = `${x}px`;
    pinStyle.top = `${y}px`;
  });
}

onMounted(updatePin);
watch(recommendedId, updatePin);

function onComplete() {
  router.push('/parking-complete');
}

interface Spot { id: string; status: 'occupied' | 'empty' }
const row1 = reactive<Spot[]>([
  { id: 'A5', status: 'empty' },
  { id: 'A4', status: 'empty' },
  { id: 'A3', status: 'empty' },
  { id: 'A2', status: 'occupied' },
  { id: 'A1', status: 'empty' },
]);
const row2 = reactive<Spot[]>([
  { id: 'B3', status: 'empty' },
  { id: 'B2', status: 'empty' },
  { id: 'B1', status: 'empty' },
  { id: 'C3', status: 'empty' },
  { id: 'C2', status: 'empty' },
  { id: 'C1', status: 'empty' },
]);
</script>

<style scoped>
/* Layout */
.main-page-container {
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
}

/* Header */
.recommend-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  margin-bottom: 24px;
  text-align: center;
}
.title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  margin: 0 0 8px;
  padding-top: 24px;
}
.info-box {
  width: 60%;
  max-width: 260px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}
.info-box .info-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}
.info-box .info-detail {
  font-size: 18px;
  color: #666;
  margin: 2px 0;
}

/* Map Section */
.map-section {
  width: 100%;
  text-align: center;
}
.map-wrapper {
  position: relative;
  width: 400px;
  height: 354px;
  background: #444;
  border-radius: 8px;
  overflow: hidden;
  margin: 0 auto;
}
.row {
  display: flex;
  justify-content: center;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.row-1 {
  top: 0px;
}
.row-2 {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  /* 추가 */
  align-items: flex-end;
}
.row-1 .spot:nth-child(3),
.row-2 .spot:nth-child(3) {
  margin-right: 24px;
}
.row-2 .spot {
  width: 52px;
  height: 98px;
}

/* 2행 4~6번째 칸만 높이 조정 */
.row-2 .spot:nth-child(n+4) {
  height: 89px;
  align-self: flex-end;
}
.spot {
  width: 52px;
  height: 98px;
  border: 2px solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 14px;
  box-sizing: border-box;
}
.row-2 .spot:nth-child(n+4) {
  height: 89px;
}
.spot.recommended {
  background: #8fcd2b;
}
.spot.occupied {
  background: #fe5454;
}
.spot.empty {
  background: #999;
}
.divider {
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  border-top: 3px dashed #fff;
  transform: translateY(-50%);
}
/* Legend */
.legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
  margin-bottom: 32px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}
.box {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}
.recommended.box { background: #8fcd2b; }
.occupied.box    { background: #fe5454; }
.empty.box       { background: #999; }
.pin {
  position: absolute;
  width: 24px;
  height: 24px;
}
.car {
  position: absolute;
  top: calc(50% + 16px);
  left: 10px;
  width: 56px;
  height: 32px;
}

/* Complete Button */
.complete-btn-wrapper {
  display: flex;
  justify-content: center;
  padding-bottom: 24px;
}
.complete-btn {
  width: 80%;
  height: 50px;
  background: #6ba368;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease;
}
.complete-btn:hover {
  background: #5a9857;
}

/* Responsive */
@media (max-width: 440px) {
  .main-page-container {
    width: 100vw;
    height: 100vh;
  }
}
</style>
