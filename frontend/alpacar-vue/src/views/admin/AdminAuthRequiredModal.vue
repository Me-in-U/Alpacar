<template>
  <div class="modal-overlay">
    <div class="modal-container">
      <p class="modal-title">관리자만 접근 가능합니다</p>
      <button class="back-button" @click="onClose">돌아가기</button>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits(['close'])

function onClose() {
  emit('close')
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.4);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-container {
  	background-color: #F9F5EC;
  border: 1px solid #000;
  border-radius: 12px;
  padding: 48px 32px;
  width: 480px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
  text-align: center;
}

.modal-title {
  font-size: 24px;
  font-weight: 700;
  font-family: Inter;
  margin-bottom: 40px; /* ✅ 여기 간격 조절 */
}

.back-button {
  	background-color: #4B3D34;
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  padding: 14px 32px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
</style>
