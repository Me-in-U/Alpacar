<template>
  <div>
    <AdminNavbar :showLogout="false" @test-modal="showModal = true" />

    <AdminAuthRequiredModal v-if="showModal" @close="showModal = false" />
    <div class="container">
      <p class="title">실시간 주차장 확인</p>
      <!-- 백엔드 api 연결 후 수정 예정 -->
      <div class="card">
        <div class="summary-box blue">
          <div class="label">전체 주차 공간</div>
          <div class="value">120개</div>
        </div>

        <div class="summary-box orange">
          <div class="label">사용중</div>
          <div class="value">87개</div>
        </div>

        <div class="summary-box green">
          <div class="label">빈 공간</div>
          <div class="value">33개</div>
        </div>

        <div class="summary-box purple">
          <div class="label">오늘 이용량</div>
          <div class="value">247대</div>
        </div>
      </div>

      <p class="subtitle">실시간 주차 현황</p>
    </div>
  </div>
</template>

<script lang="ts">
import { ref } from 'vue'
import { defineComponent } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";
import AdminAuthRequiredModal from '@/views/admin/AdminAuthRequiredModal.vue'
const showModal = ref(false)

export default defineComponent({
  name: 'AdminMain',
  components: {
    AdminNavbar,
    AdminAuthRequiredModal,
  },
  setup() {
    const showModal = ref(false);
    return {
      showModal
    };
  }
});
</script>

<style scoped>
.container {
  background-color: #f3eeea;
  min-height: calc(100vh - 64px); /* 네비게이션바 높이 감안 */
  padding: 16px 64px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.title {
  font-size: 36px;
  font-weight: 700;
  font-family: "Inter-Bold", Helvetica;
  color: #333333;
  margin-bottom: 32px;
  align-self: flex-start;
}

.subtitle {
  font-size: 24px;
  font-weight: 600;
  color: #4c4c4c;
  margin-top: 48px;
  align-self: flex-start;
}

/* 카드 섹션 */
.card {
  background-color: #faf8f5;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  gap: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
  width: 100%;
  max-width: 1200px;
  box-sizing: border-box;
  flex-wrap: wrap;
  justify-content: center;
}

/* 각 박스 */
.summary-box {
  flex: 1 1 220px;
  height: 140px;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-sizing: border-box;
  border: 1px solid #ccc;
  text-align: center;
}

.label {
  font-size: 16px;
  font-weight: 600;
  color: #4c4c4c;
}

.value {
  font-size: 28px;
  font-weight: 700;
  color: #333;
}

/* 색상 스타일 */
.blue {
  background-color: #e5f2ff;
  border-color: #b2cce5;
}
.orange {
  background-color: #fff2e5;
  border-color: #e5ccb2;
}
.green {
  background-color: #f2fff2;
  border-color: #b2e5b2;
}
.purple {
  background-color: #fff2ff;
  border-color: #e5b2e5;
}
</style>