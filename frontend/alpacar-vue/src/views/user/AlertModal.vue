<template>
  <div class="backdrop" @click.self="close">
    <div class="modal">
      <!-- 아이콘: slot 으로 교체 가능 -->
      <div class="icon">
        <slot name="icon" />
      </div>

      <!-- 제목: slot 또는 prop -->
      <h2 class="title">
        <slot name="title">{{ title }}</slot>
      </h2>

      <!-- 본문: slot 또는 prop -->
      <div class="body">
        <slot name="body">{{ body }}</slot>
      </div>

      <!-- 닫기 버튼 -->
      <div class="actions">
        <button class="btn" @click="close">{{ closeText }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

const props = defineProps({
  title:     { type: String, default: '' },
  body:      { type: String, default: '' },
  closeText: { type: String, default: '닫기' }
})

const emit = defineEmits(['close'])
function close() {
  emit('close')
}
</script>

<style scoped>
.backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 16px;
  width: 90%;
  max-width: 360px;
  padding: 24px;
  box-sizing: border-box;
  text-align: center;
}

.icon {
  margin-bottom: 16px;
}

.title {
  margin: 0 0 12px;
  font-size: 20px;
  font-weight: 600;
  color: #464038;
}

.body {
  margin-bottom: 24px;
  font-size: 16px;
  color: #666;
  line-height: 1.4;
}

.actions {
  display: flex; justify-content: center;
}

.btn {
  padding: 10px 24px;
  background: #776b5d;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
}

.btn:hover {
  background: #5f554b;
}
</style>
