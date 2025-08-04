<template>
  <div class="page-wrapper">
    <AdminNavbar :showLogout="false" />
    <div class="container">
      <p class="title">주차 이벤트 로그</p>

      <div class="card">
        <div class="log-table-wrapper">
          <table class="log-table">
            <thead>
              <tr>
                <th>차량 번호</th>
                <th>주차 위치</th>
                <th>입차 시각</th>
                <th>주차 시각</th>
                <th>출차 시각</th>
                <th>상태</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>111가1111</td>
                <td>A1</td>
                <td>2025-07-23 16:00</td>
                <td>2025-07-23 16:05</td>
                <td>2025-07-23 18:00</td>
                <td>출차 완료</td>
              </tr>
              <tr>
                <td>222가2222</td>
                <td>B1</td>
                <td>2025-07-23 17:00</td>
                <td>2025-07-23 17:05</td>
                <td>-</td>
                <td>주차 완료</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import AdminNavbar from "@/views/admin/AdminNavbar.vue";

export default defineComponent({
  name: "AdminParkingLogs",
  components: { AdminNavbar },
});
</script>

<style scoped>
.page-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;           /* 화면 전체 높이 */
  background-color: #f3eeea;   /* 페이지 배경색 */
}

.container {
  background-color: #f3eeea;
  min-height: calc(100vh - 64px); /* 네비게이션 바 높이를 제외한 높이 */
  padding: 48px 64px;
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

/* 가로 스크롤 처리 */
.log-table-wrapper {
  width: 100%;
  overflow-x: auto;
}

/* 표 스타일링 */
.log-table {
  width: 100%;
  border-collapse: collapse;
}
/* 헤더 밑줄만 표시 */
.log-table th {
  text-align: left;
  padding: 12px;
  font-weight: 600;
  color: #333333;
  border-bottom: 1px solid #ccc;
}

/* 본문 셀은 테두리 제거 */
.log-table td {
  padding: 12px;
  color: #666666;
  border: none;
}

/* Mobile 대응 */
@media (max-width: 768px) {
  .container {
    padding: 32px 24px;
  }
  .title {
    font-size: 28px;
    margin-bottom: 24px;
  }
  .card {
    padding: 24px;
  }
}
</style>
