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
      <span class="nav-label">홈</span>
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
      <span class="nav-label">히스토리</span>
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
      <span class="nav-label">추천받기</span>
    </div>
    <div 
      class="nav-item" 
      :class="{ active: isActivePage('/user-profile') }"
      @click="goToUserProfile"
    >
      <img 
        :src="getNavIcon('user')" 
        alt="User" 
        class="nav-icon" 
      />
      <span class="nav-label">My</span>
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
      return currentPath === '/user-profile' ? navBarUserSelected : navBarUser
    default:
      return navBarHome
  }
}

const goToMain = async () => {
  console.log('Navigating to main...')
  try {
    await router.push('/main')
    console.log('Navigation to main completed')
  } catch (error) {
    console.error('Navigation error:', error)
  }
}

const goToParkingHistory = async () => {
  console.log('Navigating to parking history...')
  try {
    await router.push('/parking-history')
    console.log('Navigation to parking history completed')
  } catch (error) {
    console.error('Navigation error:', error)
  }
}

const goToMap = async () => {
  console.log('Navigating to parking recommend...')
  try {
    await router.push('/parking-recommend')
    console.log('Navigation to parking recommend completed')
  } catch (error) {
    console.error('Navigation error:', error)
  }
}

const goToUserProfile = async () => {
  console.log('Navigating to user profile...')
  try {
    await router.push('/user-profile')
    console.log('Navigation to user profile completed')
  } catch (error) {
    console.error('Navigation error:', error)
  }
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
  height: 60px;
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
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.nav-item:hover {
  background-color: #F5F5F5;
}

.nav-item:active {
  background-color: #E0E0E0;
  transform: scale(0.95);
}

.nav-item.active {
  background-color: #F0F0F0;
}

.nav-label {
  font-size: 10px;
  color: #4B3D34;
  margin-top: 4px;
  text-align: center;
  font-family: "Inter", sans-serif;
}

.nav-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}
</style>