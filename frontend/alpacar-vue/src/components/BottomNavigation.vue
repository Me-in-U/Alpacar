<template>
  <div class="bottom-nav">
    <div 
      class="nav-item" 
      :class="{ active: isActivePage('/main') }"
      @click="goToMain"
    >
      <img 
        :src="getNavIcon('home')" 
        alt="Home" 
        class="nav-icon" 
      />
    </div>
    <div 
      class="nav-item" 
      :class="{ active: isActivePage('/parking-history') }"
      @click="goToParkingHistory"
    >
      <img 
        :src="getNavIcon('history')" 
        alt="History" 
        class="nav-icon" 
      />
    </div>
    <div
      class="nav-item"
      :class="{ active: isActivePage('/parking-recommend') }"
      @click="goToMap"
    >
    <img 
      :src="getNavIcon('map')" 
      alt="Map" 
      class="nav-icon" 
      />
    </div>
    <div>
    <div class="nav-item">
      <img 
        :src="getNavIcon('user')" 
        alt="User" 
        class="nav-icon" 
      />
    </div>
  </div>
</div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import navBarHome from '@/assets/nav_bar_home.png'
import navBarHomeSelected from '@/assets/nav_bar_home_selected.png'
import navBarHistory from '@/assets/nav_bar_history.png'
import navBarHistorySelected from '@/assets/nav_bar_history_selected.png'
import navBarMap from '@/assets/nav_bar_map.png'
import navBarMapSelected from '@/assets/nav_bar_map_selected.png'
import navBarUser from '@/assets/nav_bar_user.png'
import navBarUserSelected from '@/assets/nav_bar_user_selected.png'

const router = useRouter()
const route = useRoute()

// 현재 페이지 확인
const isActivePage = (path: string) => {
  return route.path === path
}

// 네비게이션 아이콘 결정 (현재 페이지에 따라 selected 이미지 표시)
const getNavIcon = (iconType: string) => {
  const currentPath = route.path
  
  switch (iconType) {
    case 'home':
      return currentPath === '/main' ? navBarHomeSelected : navBarHome
    case 'history':
      return currentPath === '/parking-history' ? navBarHistorySelected : navBarHistory
    case 'map':
      return currentPath === '/parking-recommend' ? navBarMapSelected : navBarMap // 맵 페이지가 구현되면 조건부 적용
    case 'user':
      return navBarUser // 사용자 페이지가 구현되면 조건부 적용
    default:
      return navBarHome
  }
}

const goToMain = () => {
  router.push('/main')
}

const goToParkingHistory = () => {
  router.push('/parking-history')
}

const goToMap = () => {
  router.push('/parking-recommend')
}
</script>

<style scoped>
/* Bottom Navigation */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 440px;
  height: 80px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: space-around;
  border-top: 1px solid #E5E5E5;
  z-index: 1000;
}

/* PC 환경에서는 자연스러운 위치에 배치 */
@media (min-width: 441px) {
  .bottom-nav {
    position: relative;
    bottom: auto;
    left: auto;
    transform: none;
    width: 440px;
    margin: 0 auto;
  }
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