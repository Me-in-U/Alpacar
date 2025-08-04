<template>
  <div>
    <AdminNavbar :showLogout="false" />
    <div class="container">
      <p class="title">주차 이벤트 로그</p>

      <div class="card">
        <!-- 추후 로그 테이블 들어갈 자리 -->
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";

export default defineComponent({
  name: "AdminParkingLogs",
  components: {
    AdminNavbar,
  },
});
</script>

<style scoped>
.container {
  background-color: #f3eeea;
  min-height: calc(100vh - 64px); /* 네비게이션바 높이를 제외한 높이 */
  padding: 16px 64px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.title {
  font-size: 36px;
  font-weight: 700;
  font-family: "Inter-Bold", Helvetica;
  color: #333333;
  margin-bottom: 32px;
}

.card {
  background-color: #faf8f5;
  width: 100%;
  flex: 1;
  padding: 48px;
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  box-sizing: border-box;
}
</style>
