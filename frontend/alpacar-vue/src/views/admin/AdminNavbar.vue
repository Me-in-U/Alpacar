<template>
  <div class="div-wrapper">
    <div class="frame">
      <div class="menu-item" @click="goTo('/admin-main')">실시간 주차 현황</div>
      <div class="menu-item" @click="goTo('/admin-parkinglogs')">로그 및 기록</div>
      <div class="menu-item" @click="goTo('/admin-parkingreassign')">주차 배정 정보 변경</div>
    </div>

    <img
      class="logo-img"
      alt="Logo"
      src="@/assets/alpaca-logo-small.png"
      @click="goTo('/admin-main')"
    />

    <img
      v-if="showLogout"
      class="signout"
      alt="로그아웃"
      src="@/assets/signout.png"
      @click="$emit('logout')"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { useRouter } from "vue-router";

export default defineComponent({
  name: "AdminNavbar",
  props: {
    showLogout: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["logout"],
  setup(_, { emit }) {
    const router = useRouter();
    const goTo = (path: string) => {
      router.push(path);
    };
    return { goTo };
  },
});
</script>

<style scoped>
.div-wrapper {
  background-color: #776b5d;
  height: 64px;
  position: relative;
  width: 100%;
  margin-bottom: 0;
  padding-bottom: 0;
}

.frame {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  position: absolute;
  top: 12px;
  left: 850px;
}

.menu-item {
  color: white;
  font-family: "Inder-Regular", Helvetica, sans-serif;
  font-size: 16px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background-color: #5f554b;
}

.logo-img {
  height: 36px; /* 기존 70px → 축소 */
  width: auto;
  position: absolute;
  top: 14px;
  left: 16px;
  cursor: pointer;
}

.signout {
  height: 32px;
  width: 32px;
  position: absolute;
  top: 16px;
  right : 16px;
  cursor: pointer;
}
</style>
