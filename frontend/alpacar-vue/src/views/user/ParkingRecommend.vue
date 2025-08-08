<template>
  <div class="main-page-container">
    <Header />

    <div class="main-content">
      <!-- 1️⃣ 차량 미인식 상태 -->
      <div v-if="!isCarRecognized" class="unrecognized-container">
        <div class="center-content">
          <img src="@/assets/alert_black.png" width="67" height="67" alt="경고" />
          <h2 class="title">아직 인식된 차량이 없습니다</h2>
          <p class="body">
            차량을 앞뒤로 움직여<br />
            번호판을 재인식 시켜주세요
          </p>
        </div>
      </div>

      <!-- 2️⃣ 차량 인식 완료, 추천 중 -->
      <div v-else-if="isLoading" class="loading-container">
        <div class="car-animation-wrapper">
          <img src="@/assets/car-with-alpaca.png" alt="알파카 자동차" class="car-animation" />
        </div>
        <p class="loading-text">추천 주차 공간을 배정 중입니다...</p>
      </div>

      <!-- 3️⃣ 추천 완료 -->
      <div v-else>
        <section class="recommend-header">
          <p class="title">추천 주차 위치</p>
          <div class="info-box">
            <div class="info-title">추천 위치: {{ recommendedId }}</div>
            <div class="info-detail">예상 소요시간: 2분</div>
            <div class="info-detail">난이도: 쉬움 (초급자 적합)</div>
          </div>
        </section>

        <div class="map-section">
          <div class="map-wrapper" ref="mapWrapper">
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

            <div class="divider"></div>

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

            <img class="pin" src="@/assets/pin.png" alt="pin" v-if="pinStyle.top" :style="pinStyle" />
            <img class="car" src="@/assets/my_car.png" alt="car" />
          </div>

          <div class="legend">
            <div class="legend-item"><div class="box recommended"></div><span>추천 위치</span></div>
            <div class="legend-item"><div class="box occupied"></div><span>사용 중</span></div>
            <div class="legend-item"><div class="box empty"></div><span>미사용</span></div>
          </div>
        </div>

        <div class="complete-btn-wrapper">
          <button class="complete-btn" @click="onComplete">주차 완료</button>
        </div>
      </div>
    </div>

    <BottomNavigation />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Header from '@/components/Header.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'

// 상태
const isCarRecognized = ref(false)
const isLoading = ref(false)
const recommendedId = ref('')

// 테스트 흐름
onMounted(() => {
  setTimeout(() => {
    isCarRecognized.value = true
    isLoading.value = true

    // 추천 결과 수신
    setTimeout(() => {
      recommendedId.value = 'A3'
      isLoading.value = false
      updatePin()
    }, 5500)
  }, 5000)
})

// 추천 핀 위치 계산
const mapWrapper = ref<HTMLElement | null>(null)
const pinStyle = reactive({ top: '', left: '' })

function updatePin() {
  nextTick(() => {
    if (!mapWrapper.value) return
    const wrapRect = mapWrapper.value.getBoundingClientRect()
    const spotEl = mapWrapper.value.querySelector<HTMLElement>(
      `[data-spot-id="${recommendedId.value}"]`
    )
    if (!spotEl) return
    const spotRect = spotEl.getBoundingClientRect()
    const pinW = 24, pinH = 24
    const x = spotRect.left - wrapRect.left + spotRect.width / 2 - pinW / 2
    const y = spotRect.top - wrapRect.top + spotRect.height / 2 - pinH / 2 - 35
    pinStyle.left = `${x}px`
    pinStyle.top = `${y}px`
  })
}

const router = useRouter()
function onComplete() {
  router.push('/parking-complete')
}

// 샘플 데이터
interface Spot { id: string; status: 'occupied' | 'empty' }
const row1 = reactive<Spot[]>([
  { id: 'A5', status: 'empty' },
  { id: 'A4', status: 'empty' },
  { id: 'A3', status: 'empty' },
  { id: 'A2', status: 'occupied' },
  { id: 'A1', status: 'empty' },
])
const row2 = reactive<Spot[]>([
  { id: 'B3', status: 'empty' },
  { id: 'B2', status: 'empty' },
  { id: 'B1', status: 'empty' },
  { id: 'C3', status: 'empty' },
  { id: 'C2', status: 'empty' },
  { id: 'C1', status: 'empty' },
])
watch(recommendedId, updatePin)
</script>

<style scoped>
/* ✅ 모바일 기본: 100vw + 440px 상한으로 확대/축소 방지 */
.main-page-container {
  width: 100vw;
  max-width: 440px;
  min-height: 100vh;
  position: relative;
  background: #f3eeea;
  margin: 0 auto;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ✅ main-content: 폭은 100%, 가운데 정렬은 상태 컨테이너에서 처리 */
.main-content {
  flex: 1;
  display: block;
  padding-top: 80px;      /* 헤더 */
  padding-bottom: 80px;   /* 하단 내비 */
  min-height: calc(100vh - 160px);
  overflow-y: auto;
  width: 100%;
}

/* 1️⃣ 차량 미인식 상태 */
.unrecognized-container {
  width: 100%;
  min-height: calc(100vh - 160px); /* 헤더+하단바 제외 */
  display: flex;
  flex-direction: column;
  justify-content: center;  /* 세로 중앙 */
  align-items: center;      /* 가로 중앙 */
  text-align: center;
  padding: 0 16px;
  box-sizing: border-box;
}
.center-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.center-content .title {
  font-size: 20px;
  font-weight: 600;
  color: #464038;
  margin: 16px 0 12px;
}
.center-content .body {
  font-size: 16px;
  color: #666;
  line-height: 1.4;
}

/* 2️⃣ 로딩 중 */
.loading-container{
  width: 100%;
  min-height: calc(100vh - 160px);
  display: flex;
  flex-direction: column;   /* 이미지 위, 텍스트 아래 */
  justify-content: center;
  align-items: center;
  text-align: center;
  padding: 0 16px;
  box-sizing: border-box;
}
.car-animation-wrapper {
  position: relative;
  width: 100%;
  max-width: 400px;        /* 맵 폭과 일치 */
  height: 100px;
  overflow: hidden;
}
.car-animation {
  position: absolute;
  bottom: 0;
  left: -100px;
  width: 100px;
  height: auto;
  animation: moveCar 4s linear infinite;
}
@keyframes moveCar {
  0% { transform: translateX(0); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateX(600px); opacity: 0; }
}
.loading-text {
  margin-top: 16px;
  font-size: 16px;
  color: #666;
}

/* 3️⃣ 추천 결과 */
.recommend-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
  text-align: center;
}
.title {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  padding-top: 24px;
}
.info-box {
  width: 60%;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}
.info-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}
.info-detail {
  font-size: 18px;
  color: #666;
  margin: 2px 0;
}

/* 맵 */
.map-section { text-align: center; }
.map-wrapper {
  position: relative;
  width: 100%;             /* 모바일은 100%, 상한 400px */
  max-width: 400px;
  height: 354px;
  background: #444;
  border-radius: 8px;
  margin: 0 auto;
}
.row {
  display: flex;
  justify-content: center;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}
.row-1 { top: 0; }
.row-2 {
  bottom: 0;
  align-items: flex-end;
}
.row-1 .spot:nth-child(3),
.row-2 .spot:nth-child(3) { margin-right: 24px; }
.row-2 .spot { width: 52px; height: 98px; }
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
}
.spot.recommended { background: #8fcd2b; }
.spot.occupied { background: #fe5454; }
.spot.empty { background: #999; }
.divider {
  position: absolute;
  top: 50%;
  width: 100%;
  border-top: 3px dashed #fff;
  transform: translateY(-50%);
}
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
.legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin: 16px 0 32px;
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
.occupied.box { background: #fe5454; }
.empty.box { background: #999; }

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

/* 데스크톱(441px 이상)에서만 440px 고정 */
@media (min-width: 441px) {
  .main-page-container {
    width: 440px;
    min-height: 100vh;
  }
  .main-content {
    min-height: calc(100vh - 160px);
    padding-bottom: 20px;
  }
}
</style>
