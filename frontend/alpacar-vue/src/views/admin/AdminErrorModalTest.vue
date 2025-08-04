<template>
  <div class="test-page">
    <h2>🚨 관리자 모달 스타일 테스트</h2>

    <!-- 에러 모달 열기 -->
    <button class="open-btn" @click="showError = true">
      에러 모달 열기
    </button>
    <AdminErrorModal
      v-if="showError"
      @confirm="showError = false"
    />

    <!-- 재배치 확인 모달 열기 -->
    <button class="open-btn" @click="showReassign = true">
      재배치 확인 모달 열기
    </button>
    <AdminReassignModal
      v-if="showReassign"
      @close="showReassign = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AdminErrorModal from './AdminErrorModal.vue'
import AdminReassignModal from './AdminReassignModal.vue'

const showError     = ref(false)
const showReassign  = ref(false)
</script>

<style scoped>
.test-page {
  padding: 40px;
  text-align: center;
}
.open-btn {
  margin: 12px 0;
  padding: 10px 20px;
  background: #776b5d;
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.open-btn:hover {
  background: #5f554b;
}
</style>
