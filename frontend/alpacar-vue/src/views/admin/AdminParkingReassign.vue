<template>
  <div>
    <AdminNavbar :showLogout="false" />
    <div class="container">
      <div class="header-row">
        <p class="title">주차 공간 배정 상태 변경</p>
        <p class="legend">🟩 : 사용 가능 | 🟥 : 사용 중 | 🟦 : 선택한 자리</p>
      </div>

      <div class="view">
        <!-- 주차 공간 구성 -->
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";

export default defineComponent({
  name: "AdminParkingReassign",
  components: {
    AdminNavbar,
  },
});
</script>

<style scoped>
.container {
  background-color: #f3eeea;
  padding: 16px 64px;
  box-sizing: border-box;
  min-height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  max-width: 1440px;
  margin-bottom: 16px;
}

.title {
  font-size: 36px;
  font-weight: 700;
  font-family: "Inter-Bold", Helvetica;
  color: #333333;
}

.legend {
  font-size: 18px;
  font-weight: 500;
  font-family: "Inter-Regular", Helvetica;
  color: #666666;
}
  
.view {
  background-color: #5c5c5c;
  height: 708px;
  width: 800px;
  margin: 0 auto;
  position: relative;
}
</style>