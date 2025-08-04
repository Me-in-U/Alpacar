<template>
  <div class="container">
    <!-- 안내문 -->
    <div class="a3-container">
      <p>
        <b class="seat">{{ seatId }}</b> 자리를 선택하셨습니다.
      </p>
      <p>해당 자리로 재배치하시겠습니까?</p>
    </div>

    <!-- 버튼 그룹 -->
    <div class="btn-group">
      <button class="btn yes" @click="goAdminMain">예</button>
      <button class="btn no" @click="closeModal">아니오</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

/**
 * 부모로부터 전달받을 prop 정의
 */
const props = defineProps<{
  seatId: string
}>()

/**
 * close 이벤트를 부모에게 emit
 */
const emit = defineEmits<{
  (e: 'close'): void
}>()

const router = useRouter()

function closeModal() {
  emit('close')
}

function goAdminMain() {
  router.push('/admin-main')
}
</script>

<style scoped>
.container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1000;

  width: 40%;
  max-width: 448px;
  padding: 30px;
  box-sizing: border-box;
  background-color: #f3eeea;
  border: 2px solid #000;
  box-shadow: 0 6px 4px rgba(0, 0, 0, 0.25);

  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  text-align: center;
  font-family: 'Inter', sans-serif;
  color: #000;
}

/* 안내문 스타일 */
.a3-container p {
  margin: 0;
  font-size: 20px;
  line-height: 1.2;
}
.seat {
  font-weight: bold;
}

/* 버튼 그룹을 한 줄에 배치 */
.btn-group {
  display: flex;
  gap: 40px;
}

/* 버튼 공통 스타일 */
.btn {
  display: flex;
  align-items: center;      /* 수직 가운데 정렬 */
  justify-content: center;  /* 필요시 가로 가운데 정렬 */
  min-width: 80px;
  height: 40px;
  padding: 0 24px;          /* 세로 패딩 제거, 좌우 패딩만 유지 */
  background-color: #776B5D;
  color: #fff;
  border: none;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn:hover {
  background-color: #5f554b;
}
</style>
