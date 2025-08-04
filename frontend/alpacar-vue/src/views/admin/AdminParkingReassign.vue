<template>
  <div class="page-wrapper">
    <AdminNavbar :showLogout="false" />

    <div class="container">
      <div class="header-row">
        <p class="title">주차 공간 배정 상태 변경</p>
      </div>

      <div class="view-and-legend">
        <!-- 주차장 도면 -->
        <div class="view">
          <div class="parking-map">
            <!-- 첫 번째 줄 -->
            <div class="row row-1">
              <div
                v-for="spot in row1"
                :key="spot.id"
                class="spot"
                :class="{
                  available: spot.status==='available' && !isSelected(spot.id),
                  occupied:  spot.status==='occupied',
                  selected:  isSelected(spot.id)
                }"
                @click="toggleSelect(spot)"
              >
                {{ spot.id }}
              </div>
            </div>
            <!-- 두 번째 줄 -->
            <div class="row row-2">
              <div
                v-for="spot in row2"
                :key="spot.id"
                class="spot"
                :class="{
                  available: spot.status==='available' && !isSelected(spot.id),
                  occupied:  spot.status==='occupied',
                  selected:  isSelected(spot.id)
                }"
                @click="toggleSelect(spot)"
              >
                {{ spot.id }}
              </div>
            </div>
          </div>
        </div>

        <!-- 도면 오른쪽: 범례 + 변경하기 버튼 -->
        <div class="side-panel">
          <div class="legend-outside">
            🟩 : 사용 가능<br/>
            🟥 : 사용 중<br/>
            🟦 : 선택한 자리
          </div>
          <button class="reassign-btn" @click="onContainerClick">
            변경하기
          </button>
        </div>
      </div>
    </div>

    <!-- 재배치 확인 모달 -->
 <AdminReassignModal
    v-if="showModal"
   :seat-id="selected!"
    @close="showModal = false"
  />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import AdminNavbar from '@/views/admin/AdminNavbar.vue'
import AdminReassignModal from '@/views/admin/AdminReassignModal.vue'

type Spot = { id: string; status: 'available' | 'occupied' }

// 샘플 데이터
const row1 = reactive<Spot[]>([
  { id: 'A5', status: 'available' },
  { id: 'A4', status: 'occupied' },
  { id: 'A3', status: 'available' },
  { id: 'A2', status: 'available' },
  { id: 'A1', status: 'available' },
])
const row2 = reactive<Spot[]>([
  { id: 'B3', status: 'available' },
  { id: 'B2', status: 'occupied' },
  { id: 'B1', status: 'available' },
  { id: 'C3', status: 'available' },
  { id: 'C2', status: 'available' },
  { id: 'C1', status: 'available' },
])

// 단일 선택
const selected = ref<string|null>(null)
function isSelected(id: string) {
  return selected.value === id
}
function toggleSelect(spot: Spot) {
  if (spot.status !== 'available') return
  selected.value = selected.value === spot.id ? null : spot.id
}

// 모달 제어
const showModal = ref(false)
function onContainerClick() {
  if (!selected.value) {
    alert('먼저 사용 가능한 공간을 선택하세요.')
    return
  }
  showModal.value = true
}
</script>

<style scoped>
.page-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f3eeea;
}

.container {
  padding: 48px 64px;
  box-sizing: border-box;
  flex: 1;
}

.header-row {
  margin-bottom: 16px;
}

.title {
  font-size: 36px;
  font-weight: 700;
  color: #333333;
}

/* view + side-panel */
.view-and-legend {
  display: flex;
  align-items: flex-start;
  gap: 32px;
}

/* 도면 */
.view {
  position: relative;
  width: 800px;
  height: 708px;
  background-color: #5c5c5c;
  overflow: hidden;
  box-sizing: border-box;
}
.view::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  border-top: 4px dashed #fff;
  transform: translateY(-2px);
}

/* 주차칸 배치 */
.parking-map {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  box-sizing: border-box;
}

.row {
  display: flex;
}
.row-1 .spot:nth-child(3),
.row-2 .spot:nth-child(3) {
  margin-right: 24px;
}
.row-2 .spot:nth-child(n+4) {
  height: 175px;
  margin-top: calc(205px - 175px);
}

/* 주차칸 */
.spot {
  width: 110px;
  height: 205px;
  border: 3.5px solid #fff;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-family: sans-serif;
  cursor: pointer;
  user-select: none;
}
.spot.available { background-color: #8fcd2b; }
.spot.occupied  { background-color: #fe5454; cursor: not-allowed; }
.spot.selected  { background-color: #42a5f5; }

/* 오른쪽 패널 (범례 + 버튼) */
.side-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between; /* 위아래 배치 */
  height: 708px;                  /* view와 동일 높이 */
  gap: 24px;
}

.legend-outside {
  font-size: 18px;
  font-weight: 500;
  color: #666666;
  line-height: 1.5;
  white-space: nowrap;
}

/* 변경하기 버튼 */
.reassign-btn {
  width: 120px;
  height: 50px;
  background-color: #776b5d;
  color: #fff;
  font-size: 24px;
  font-weight: 600;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.reassign-btn:hover {
  background-color: #5f554b;
}
</style>
