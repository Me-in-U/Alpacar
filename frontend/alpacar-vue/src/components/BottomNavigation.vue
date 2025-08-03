<template>
  <div class="bottom-nav">
    <div class="nav-item active" @click="goToMain">
      <img src="@/assets/nav_bar_home.png" alt="Home" class="nav-icon" />
    </div>
    <div class="nav-item">
      <img src="@/assets/nav_bar_history.png" alt="History" class="nav-icon" />
    </div>
    <div class="nav-item"  @click="goToMap">
      <img src="@/assets/nav_bar_map.png" alt="Map" class="nav-icon" />
    </div>
    <div class="nav-item">
      <img src="@/assets/nav_bar_user.png" alt="User" class="nav-icon" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goToMain = () => {
  router.push('/main')
}

const goToMap = () => {
  router.push('/parking-recommend')
}
</script>

<style scoped>
/* Bottom Navigation */
.bottom-nav {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: space-around;
  border-top: 1px solid #E5E5E5;
  z-index: 10;
}

.nav-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.nav-item:hover {
  background-color: #F5F5F5;
}

.nav-item.active {
  background-color: #F0F0F0;
}

.nav-icon {
  width: 28px;
  height: 28px;
  object-fit: contain;
}
</style>