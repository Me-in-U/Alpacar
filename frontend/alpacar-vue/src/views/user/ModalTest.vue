<template>
  <div class="main-page-container">
    <Header />
  <div class="main-content">
  <div class="test-page">
    <h2>🚧 Modal 스타일 테스트 페이지</h2>

    <div class="controls">
      <button @click="showNoCar = true">차량 미인식 모달 보기</button>
      <button @click="showReassign = true">재배치 알림 모달 보기</button>
    </div>

    <!-- 차량 미인식 모달 (기본 흰 배경) -->
    <AlertModal
      v-if="showNoCar"
      @close="showNoCar = false"
      closeText="확인"
    >
      <template #icon>
        <img src="@/assets/alert_black.png" width="67" height="67" alt="경고" />
      </template>
      <template #title>아직 인식된 차량이 없습니다</template>
      <template #body>
        차량을 앞뒤로 움직여<br />
        번호판을 재인식 시켜주세요
      </template>
    </AlertModal>

    <!-- 재배치 알림 모달 (dark-modal 클래스 적용) -->
    <AlertModal
      v-if="showReassign"
      @close="showReassign = false"
      closeText="확인"
      class="dark-modal"
    >
      <template #icon>
        <img src="@/assets/alert_red.png" width="75" height="75" alt="알림" />
      </template>
      <template #title>
        <div>다른 차량이</div>
        <div>주차 중입니다.</div>
      </template>
      <template #body>새 주차공간을 배정합니다.</template>
    </AlertModal>
  </div>
  </div>
  <BottomNavigation />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AlertModal from '@/views/user/AlertModal.vue'
import Header from '@/components/Header.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'

const showNoCar    = ref(false)
const showReassign = ref(false)
</script>

<style scoped>
.main-page-container {
  width: 440px;
  height: 956px;
  position: relative;
  background: #F9F5EC;
  overflow: hidden;
  margin: 0 auto;
}
.main-content {
  position: relative;
  padding-top: 80px;
  height: calc(100% - 160px);
  overflow-y: auto;
}
.test-page {
  padding: 40px 20px;
  text-align: center;
}
.controls {
  margin-bottom: 24px;
}
button {
  margin: 0 8px;
  padding: 8px 16px;
  background: #4B3D34;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
button:hover {
  background: #594D44;
}

/* dark-modal 클래스가 붙은 AlertModal 내부 스타일 덮어쓰기 */
.dark-modal :deep(.modal) {
  background-color: #2B2B2B !important;
}
.dark-modal :deep(.title) {
  color: #FFF !important;
  font-size: 28px !important;
}
.dark-modal :deep(.body) {
  color: #FFF !important;
  font-size: 20px !important;
}
</style>
