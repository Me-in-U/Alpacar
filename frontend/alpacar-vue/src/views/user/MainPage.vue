<template>
  <div class="main-page-container">
    <Header />

    <!-- Main Content -->
    <div class="main-content">
      <!-- Welcome Message -->
      <div class="welcome-section">
        <h1 class="welcome-title">알파카와 함께,</h1>
        <p class="welcome-subtitle">내 차에 딱 맞는 주차 공간을 찾아보세요</p>
      </div>

      <!-- User Profile Card with 3D Animation -->
      <div class="profile-card-container">
        <div 
          class="profile-card" 
          :class="{ 'is-flipped': isCardFlipped, 'dragging': isDragging || isMouseDragging }" 
          :style="holoGradeVars"          
          @click="handleClick"
          @mousedown="handleMouseDown"
          @mousemove="handleMouseMove"
          @mouseup="handleMouseUp"
          @mouseleave="handleMouseLeave"
          @touchstart.prevent="handleTouchStart"
          @touchmove.prevent="handleTouchMove"
          @touchend.prevent="handleTouchEnd"
          ref="cardRef"
        >
          <div class="card-inner">
            <!-- Front Side (Original Profile) -->
            <div class="card-front">
              <div class="profile-header">
                <!-- Gray header bar -->
              </div>
              <div class="profile-content">
                <div class="profile-left">
                  <div class="avatar-container">
                    <img :src="avatarImage" alt="User Avatar" class="avatar-image" />
                  </div>
                </div>
                <div class="profile-right">
                  <div class="skill-badge">
                    <div class="skill-icon">
                      <div class="skill-circle" :style="{ backgroundImage: `url(${skillIcon})` }">
                      </div>
                    </div>
                    <span class="skill-text" :style="{ color: gradeInfo.color }">{{ gradeInfo.text }}</span>
                  </div>
                  <div class="user-info">
                    <div class="user-name">
                      <span class="label">Name</span>
                      <span class="separator">|</span>
                      <span class="value">{{ userName }}</span>
                    </div>
                    <div class="user-number">
                      <span class="label">No.</span>
                      <span class="separator">|</span>
                      <span class="value">{{ userVehicleNumber }}</span>
                    </div>
                    <p class='touch-text-description'>카드를 두번 터치하면 화면이 돌아갑니다.</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Back Side (Profile Details) -->
            <div class="card-back">
              <div class="back-header">
                <!-- Gray header bar -->
              </div>
              <div class="back-content">
                <div class="back-title">
                  <h2>{{ gradeInfo.text }}({{ userScore }}점)</h2>
                </div>
                <div class="grade-display">
                  <div class="grade-bar">
                    <div class="grade-fill" :style="{ width: userScore + '%' }"></div>
                    <div class="grade-marker" :style="{ left: `calc(${Math.max(5, Math.min(95, userScore))}% - 20px)` }">
                      <div class="marker-icon">
                        <img :src="alpakaInCarImage" alt="Alpaka in Car" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div> <!-- /card-inner -->
        </div>
      </div>

      <!-- Menu Items -->
      <div class="menu-items">
        <div class="menu-item" @click="goToParkingHistory">
          <div class="menu-icon">
          </div>
          <div class="menu-content">
            <h3 class="menu-title">내 주차기록 확인하기</h3>
            <p class="menu-description">주차기록과 운전 점수를 확인해보세요</p>
          </div>
        </div>

        <div class="menu-item" @click="goToParkingRecommend">
          <div class="menu-icon">
          </div>
          <div class="menu-content">
            <h3 class="menu-title">주차 자리 추천 받기</h3>
            <p class="menu-description">최적화된 주차 자리를 추천받아보세요</p>
          </div>
        </div>

        <div class="menu-item" @click="goToUserProfile">
          <div class="menu-icon">
          </div>
          <div class="menu-content">
            <h3 class="menu-title">내 정보 확인하기</h3>
            <p class="menu-description">등록된 개인정보를 확인해보세요</p>
          </div>
        </div>
      </div>
    </div>

    <BottomNavigation />
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/Header.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 정적 이미지 import
const alpakaInCarImage = new URL('@/assets/alpaka_in_car.png', import.meta.url).href

// 사용자 정보 기반 computed 속성들
const userScore = computed(() => userStore.me?.score || 90)
const userName = computed(() => userStore.me?.nickname || 'User')
const userVehicleNumber = computed(() => {
  // 가장 첫 번째 등록된 차량의 번호를 반환
  return userStore.vehicles.length > 0 ? userStore.vehicles[0].license_plate : '111 가 1111'
})

// 점수별 등급 계산
const userGrade = computed(() => {
  const score = userScore.value
  if (score <= 50) return 'beginner'
  if (score <= 85) return 'intermediate'
  return 'advanced'
})

// 등급별 텍스트 및 색상
const gradeInfo = computed(() => {
  const grade = userGrade.value
  switch (grade) {
    case 'beginner':
      return { text: '초급자', color: '#80360E' }
    case 'intermediate':
      return { text: '중급자', color: '#9A9FA2' }
    case 'advanced':
      return { text: '상급자', color: '#ECB908' }
    default:
      return { text: '초급자', color: '#80360E' }
  }
})

// 등급별 이미지 경로
const avatarImage = computed(() => {
  const grade = userGrade.value
  switch (grade) {
    case 'beginner':
      return new URL('@/assets/alpaca-beginner.PNG', import.meta.url).href
    case 'intermediate':
      return new URL('@/assets/alpaca-intermediate.png', import.meta.url).href
    case 'advanced':
      return new URL('@/assets/alpaca-advanced.PNG', import.meta.url).href
    default:
      return new URL('@/assets/alpaca-beginner.PNG', import.meta.url).href
  }
})

const skillIcon = computed(() => {
  const grade = userGrade.value
  switch (grade) {
    case 'beginner':
      return new URL('@/assets/handle-bronze.png', import.meta.url).href
    case 'intermediate':
      return new URL('@/assets/handle-silver.png', import.meta.url).href
    case 'advanced':
      return new URL('@/assets/handle-gold.png', import.meta.url).href
    default:
      return new URL('@/assets/handle-bronze.png', import.meta.url).href
  }
})

/* ✅ 등급별 테두리/광택 변수 매핑 (로직 변경 아님: 스타일 주입만) */
const holoGradeVars = computed(() => {
  switch (userGrade.value) {
    case 'beginner':
      return {
        '--border-color': '#80411E',
        '--grade-gloss': 0.55,
        '--header-color': '#80360E'
      }
    case 'intermediate':
      return {
        '--border-color': '#CECFD1',
        '--grade-gloss': 0.80,
        '--header-color': '#9A9FA2'
      }
    case 'advanced':
      return {
        '--border-color': '#E6BB21',
        '--grade-gloss': 1.15,
        '--header-color': '#ECB908'
      }
    default:
      return {
        '--border-color': '#80411E',
        '--grade-gloss': 0.55,
        '--header-color': '#80360E'
      }
  }
})


// 주차 히스토리 페이지로 이동
const goToParkingHistory = async () => {
  console.log('Navigating to parking history from main...')
  try {
    await router.push('/parking-history')
    console.log('Navigation to parking history completed')
  } catch (error) {
    console.error('Navigation error:', error)
  }
}

const goToParkingRecommend = async () => {
  console.log('Navigating to parking recommend from main...')
  try {
    await router.push('/parking-recommend')
    console.log('Navigation to parking recommend completed')
  } catch (error) {
    console.error('Navigation error:', error)
  }
}

// 사용자 프로필 페이지로 이동
const goToUserProfile = async () => {
  console.log('Navigating to user profile from main...')
  try {
    await router.push('/user-profile')
    console.log('Navigation to user profile completed')
  } catch (error) {
    console.error('Navigation error:', error)
  }
}

// 모바일 기기 감지 함수
const detectMobile = () => {
  const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0)
  const result = isMobileUA || isTouchDevice
  return result || isTouchDevice
}

const isCardFlipped = ref(false)
const cardRef = ref<HTMLElement>()
const isTouching = ref(false)
const isDragging = ref(false)
const touchStartTime = ref(0)
const isMobile = ref(false)
const initialTouch = ref({ x: 0, y: 0 })
const touchThreshold = ref(1)
const isMouseDown = ref(false)
const initialMouse = ref({ x: 0, y: 0 })
const isMouseDragging = ref(false)
const lastTapTime = ref(0)
const tapCount = ref(0)
const doubleTapDelay = ref(400)

const flipCard = () => {
  isCardFlipped.value = !isCardFlipped.value
}

const handleClick = () => {
  if (!isDragging.value) {
    console.log('Click event - flipping card')
    flipCard()
  } else {
    console.log('Click event - blocked due to dragging')
  }
}

function updateShineVars(x: number, y: number, rect: DOMRect) {
  if (!cardRef.value) return
  const cx = rect.width / 2
  const cy = rect.height / 2
  const dx = (x - cx) / cx
  const dy = (y - cy) / cy
  const mag = Math.min(1, Math.hypot(dx, dy))             // 중심에서 얼마나 벗어났는지
  const shineO = (0.22 + 0.38 * mag).toFixed(3)           // 0.22 ~ 0.60 정도로
  const sx = (x / rect.width) * 100
  const sy = (y / rect.height) * 100

  cardRef.value.style.setProperty('--shineX', `${sx}%`)
  cardRef.value.style.setProperty('--shineY', `${sy}%`)
  cardRef.value.style.setProperty('--shineO', `${shineO}`)
}


const handleMouseMove = (event: MouseEvent) => {
  if (!cardRef.value) return
  if (isMouseDown.value) {
    handleMouseMoveWhileDragging(event)
    return
  }
  const rect = cardRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const rotateX = (y - centerY) / centerY * -10
  const rotateY = (x - centerX) / centerX * 10
  if (isCardFlipped.value) {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY + 180}deg)`
  } else {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
  }
  cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
  cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
  updateShineVars(x, y, rect)
}

const handleMouseLeave = () => {
  if (!cardRef.value) return
  if (!isMouseDown.value) {
    if (isCardFlipped.value) {
      cardRef.value.style.transform = 'rotateX(0deg) rotateY(180deg)'
    } else {
      cardRef.value.style.transform = 'rotateX(0deg) rotateY(0deg)'
    }
    cardRef.value.style.setProperty('--rotate-x', '0deg')
    cardRef.value.style.setProperty('--rotate-y', '0deg')
    cardRef.value.style.setProperty('--shineX', '50%')
    cardRef.value.style.setProperty('--shineY', '50%')
    cardRef.value.style.setProperty('--shineO', '0.28')
  }
}

const handleMouseDown = (event: MouseEvent) => {
  console.log('Mouse down event:', { isMobile: isMobile.value, button: event.button })
  if (event.button !== 0) return
  isMouseDown.value = true
  isMouseDragging.value = false
  initialMouse.value = { x: event.clientX, y: event.clientY }
  event.preventDefault()
}

const handleMouseMoveWhileDragging = (event: MouseEvent) => {
  if (!isMouseDown.value || !cardRef.value) return
  const deltaX = Math.abs(event.clientX - initialMouse.value.x)
  const deltaY = Math.abs(event.clientY - initialMouse.value.y)
  if (deltaX > 1 || deltaY > 1) {
    isMouseDragging.value = true
    isDragging.value = true
  }
  const rect = cardRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const rotateX = (y - centerY) / centerY * -20
  const rotateY = (x - centerX) / centerX * 20
  if (isCardFlipped.value) {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY + 180}deg)`
  } else {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
  }
  cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
  cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
  updateShineVars(x, y, rect)
}

const handleMouseUp = () => {
  console.log('Mouse up event:', { 
    isMouseDown: isMouseDown.value, 
    isMouseDragging: isMouseDragging.value 
  })
  isMouseDown.value = false
  if (isMouseDragging.value) {
    isDragging.value = false
    console.log('Mouse drag completed')
  }
  isMouseDragging.value = false
  if (!cardRef.value) return
  if (isCardFlipped.value) {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(180deg)'
  } else {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(0deg)'
  }
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
  cardRef.value.style.setProperty('--shineX', '50%')
  cardRef.value.style.setProperty('--shineY', '50%')
  cardRef.value.style.setProperty('--shineO', '0.28')
}

const handleTouchStart = (event: TouchEvent) => {
  console.log('Touch start event triggered!', { isMobile: isMobile.value, touches: event.touches.length })
  const touch = event.touches[0]
  initialTouch.value = { x: touch.clientX, y: touch.clientY }
  isTouching.value = true
  isDragging.value = false
  touchStartTime.value = Date.now()
}

const handleTouchMove = (event: TouchEvent) => {
  console.log('Touch move event triggered!', { isMobile: isMobile.value, isTouching: isTouching.value })
  if (!isTouching.value || !cardRef.value) {
    console.log('Touch move blocked:', { isTouching: isTouching.value, cardRef: !!cardRef.value })
    return
  }
  const touch = event.touches[0]
  const deltaX = Math.abs(touch.clientX - initialTouch.value.x)
  const deltaY = Math.abs(touch.clientY - initialTouch.value.y)
  if (deltaX > 3 || deltaY > 3) {
    isDragging.value = true
    tapCount.value = 0
    lastTapTime.value = 0
    console.log('드래그 감지 - 탭 카운트 리셋')
  }
  if (isDragging.value) {
    const rect = cardRef.value.getBoundingClientRect()
    const x = touch.clientX - rect.left
    const y = touch.clientY - rect.top
    const centerX = rect.width / 2
    const centerY = rect.height / 2
    const rotateX = (y - centerY) / centerY * -20
    const rotateY = (x - centerX) / centerX * 20
    console.log('Touch drag - 3D Animation ACTIVE:', { rotation: { rotateX, rotateY }})
    if (isCardFlipped.value) {
      cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY + 180}deg)`
    } else {
      cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
    }
    cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
    cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
    updateShineVars(x, y, rect)
  }
}

const handleTouchEnd = () => {
  console.log('Touch end event triggered!')
  const touchDuration = Date.now() - touchStartTime.value
  const currentTime = Date.now()
  console.log('Touch end:', { duration: touchDuration, isDragging: isDragging.value })

  if (!isDragging.value && touchDuration < 250) {
    const timeSinceLastTap = currentTime - lastTapTime.value
    if (timeSinceLastTap < doubleTapDelay.value) {
      tapCount.value++
      if (tapCount.value >= 2) {
        console.log('더블 탭 감지! 카드 뒤집기')
        if (cardRef.value) {
          cardRef.value.classList.add('double-tap-feedback')
          setTimeout(() => { cardRef.value && cardRef.value.classList.remove('double-tap-feedback') }, 300)
        }
        flipCard()
        tapCount.value = 0
        lastTapTime.value = 0
      }
    } else {
      tapCount.value = 1
      console.log('첫 번째 탭 감지, 더블 탭 대기 중...')
    }
    lastTapTime.value = currentTime
    setTimeout(() => {
      if (tapCount.value === 1) {
        console.log('더블 탭 시간 초과, 단일 탭으로 처리')
        tapCount.value = 0
        lastTapTime.value = 0
      }
    }, doubleTapDelay.value)
  } else if (isDragging.value) {
    console.log('Touch end - drag completed')
    tapCount.value = 0
    lastTapTime.value = 0
  }

  isTouching.value = false
  isDragging.value = false

  if (!cardRef.value) return
  if (isCardFlipped.value) {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(180deg)'
  } else {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(0deg)'
  }
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
  cardRef.value.style.setProperty('--shineX', '50%')
  cardRef.value.style.setProperty('--shineY', '50%')
  cardRef.value.style.setProperty('--shineO', '0.28')
}

onMounted(async () => {
  isMobile.value = detectMobile()
  console.log('모바일 감지 결과:', isMobile.value)
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      if (!userStore.me) { await userStore.fetchMe(token) }
      if (userStore.vehicles.length === 0) { await userStore.fetchMyVehicles() }
    }
  } catch (error) {
    console.error('사용자 정보 로드 실패:', error)
  }

  const handleGlobalMouseUp = () => {
    if (isMouseDown.value) {
      console.log('Global mouse up - ending drag')
      handleMouseUp()
    }
  }
  const handleGlobalMouseMove = (event: MouseEvent) => {
    if (isMouseDown.value && cardRef.value) {
      handleMouseMoveWhileDragging(event)
    }
  }
  document.addEventListener('mouseup', handleGlobalMouseUp)
  document.addEventListener('mousemove', handleGlobalMouseMove)

  onUnmounted(() => {
    document.removeEventListener('mouseup', handleGlobalMouseUp)
    document.removeEventListener('mousemove', handleGlobalMouseMove)
  })

  if (cardRef.value) {
    console.log('카드 요소 이벤트 바인딩 상태 확인:', {
      touchstart: cardRef.value.ontouchstart,
      touchmove: cardRef.value.ontouchmove,
      touchend: cardRef.value.ontouchend,
      mousedown: cardRef.value.onmousedown,
      mousemove: cardRef.value.onmousemove,
      mouseup: cardRef.value.onmouseup
    })
  }
})


</script>

<style scoped>
.main-page-container {
  width: 440px;
  height: 956px;
  position: relative;
  background: #F3EEEA;
  overflow: hidden;
  margin: 0 auto;
}

/* Main Content */
.main-content {
  position: relative;
  padding-top: 80px;
  height: calc(100% - 160px);
  overflow-y: auto;
}

/* Welcome Section */
.welcome-section {
  padding: 40px 26px 30px;
}

.welcome-title {
  color: #000000;
  font-size: 28px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  line-height: 1.2;
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  color: #666666;
  font-size: 16px;
  font-family: 'Inter', sans-serif;
  font-weight: 400;
  line-height: 1.4;
  margin: 0;
}

/* Profile Card with 3D Animation */
.profile-card-container {
  margin: 0 26px 40px;
  perspective: 1000px;
  display: flex;
  justify-content: center;
}

.profile-card {
  --rotate-x: 0deg;
  --rotate-y: 0deg;
  --card-width: 280px;
  --card-radius: 12px;
  --card-border: 2px; 
  border-radius: var(--card-radius);
  border: var(--card-border) solid var(--border-color);
  background: transparent;
  width: var(--card-width);
  aspect-ratio: 5 / 7;
  position: relative;
  cursor: pointer;
  transform-style: preserve-3d;
  transition: transform 0.9s ease-in-out;
  touch-action: none;
  user-select: none;

  min-height: 200px;
  min-width: 150px;

  /* 홀로그램 팔레트 */
  --c1: rgb(134, 243, 255);
  --c2: rgb(255, 145, 244);

  /* 🔸 script에서 주입됨 */
  --border-color: #80411E;
  --grade-gloss: 0.7;
  --lp: 50%;
  --tp: 50%;
  --px_s: 50%;
  --py_s: 50%;
  --opc: 0.75;

  background: transparent;
  box-sizing: border-box;
  background-clip: padding-box; 
}

.profile-card::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  z-index: -1;
  background: transparent;
}

/* 기존 호버효과 유지 */
.profile-card:hover {
  transition: transform 0.1s ease-out;
}

/* 플립 클래스는 기존대로 유지 */
.profile-card.is-flipped {
  transform: rotateY(180deg);
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  text-align: center;
  transition: transform 0.9s ease-in-out; /* 50% 느리게 조정 */
  transform-style: preserve-3d;
}

.card-front,
.card-back {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  border-radius: calc(var(--card-radius) - var(--card-border));
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.3s ease;
  box-sizing: border-box;
  /* ✅ 각 면에 홀로그램을 붙이기 위해 기준 지정 */
  isolation: isolate;
}

/* 🟡 움직이는 샤인(빛 하이라이트) 레이어: 마우스/터치 위치를 따라감 */
.card-front::before,
.card-back::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  /* 하이라이트 중심 좌표 & 세기(스크립트에서 갱신) */
  --shineX: 50%;
  --shineY: 50%;
  --shineO: 0.28;
  /* 레퍼런스 느낌의 radial + 약한 스윕 조합 */
  background:
    radial-gradient(
      circle at var(--shineX) var(--shineY),
      rgba(255,255,255, calc(var(--shineO) * 0.95)) 0%,
      rgba(255,255,255, calc(var(--shineO) * 0.60)) 16%,
      rgba(255,255,255, calc(var(--shineO) * 0.25)) 32%,
      rgba(255,255,255, 0) 60%
    ),
    linear-gradient(
      135deg,
      rgba(255,255,255, calc(var(--shineO) * 0.3)) 0%,
      rgba(255,255,255, 0) 60%
    );
  mix-blend-mode: screen;           /* 밝은 면에서 더 잘 보이게 */
  transition: background-position 60ms linear, opacity 120ms ease;
  opacity: 1;                       /* 필요 시 0~1로 애니메이션 가능 */
}

/* ✅ 홀로그램 레이어를 '각 면'의 ::after 로 이동 */
.card-front::after,
.card-back::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  mix-blend-mode: color-dodge;
  border-radius: inherit;

  background:
    url("https://assets.codepen.io/13471/sparkles.gif"),
    url("https://assets.codepen.io/13471/holo.png"),
    linear-gradient(
      125deg,
      #ff008450 15%,
      #fca40040 30%,
      #ffff0030 40%,
      #00ff8a20 60%,
      #00cfff40 70%,
      #cc4cfa50 85%
    );
      background-size: 160%;
  background-position: var(--px_s) var(--py_s);
  background-blend-mode: overlay;

  /* 등급에 따른 광택 강도 */
  opacity: calc(var(--opc) * var(--grade-gloss));
  filter:
    brightness(calc(1 + 0.25 * var(--grade-gloss)))
    contrast(calc(1 + 0.15 * var(--grade-gloss)));
}

/* hover 시 상자 그림자 */
.profile-card:hover .card-front,
.profile-card:hover .card-back {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
}

.card-front {
  background: #FFFFFF;
}

/* ✅ 뒷면 안쪽 테두리도 등급색으로 동기화(원하면 이 줄만 삭제 가능) */
.card-back {
  background: #EBE3D5;
  border: 1px solid var(--border-color);
  transform: rotateY(180deg);
}

/* Front Side Styles */
.profile-header {
  height: 50px;
  background: var(--header-color);
  border-top-left-radius: calc(var(--card-radius) - var(--card-border));
  border-top-right-radius: calc(var(--card-radius) - var(--card-border));
}

.profile-content {
  display: flex;
  padding: 20px;
  gap: 15px;
  height: calc(100% - 50px);
  flex-direction: column;
  justify-content: center;
}

.profile-left {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.avatar-container {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 3px solid #E5E5E5;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar-image {
  width: 70px;
  height: 70px;
  object-fit: contain;
}

.profile-right {
  display: flex;
  flex-direction: column;
  gap: 15px;
  align-items: center;
}

.skill-badge {
  display: flex;
  align-items: center;
  gap: 10px;
}

.skill-icon {
  display: flex;
  align-items: center;
}

.skill-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  display: flex;
  align-items: center;
  justify-content: center;
}

.skill-text {
  color: #4CAF50;
  font-size: 18px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
}

.touch-text-description {
  color: #666666;
  font-size: 12px;
  font-weight: 400;
  font-family: 'Inter', sans-serif;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: center;
}

.user-name,
.user-number {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.label {
  color: #333333;
  font-size: 16px;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
}

.separator {
  color: #666666;
  font-size: 16px;
}

.value {
  color: #666666;
  font-size: 16px;
  font-family: 'Inter', sans-serif;
}

/* Back Side Styles */
.back-header {
  height: 50px;
  background: var(--header-color);
  border-top-left-radius: calc(var(--card-radius) - var(--card-border));
  border-top-right-radius: calc(var(--card-radius) - var(--card-border));
}

.back-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 25px;
  height: calc(100% - 50px);
  justify-content: center;
}

.back-title h2 {
  color: #000000;
  font-size: 18px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  text-align: center;
  margin: 0;
}

.grade-display {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.grade-bar {
  position: relative;
  width: 100%;
  height: 60px;
  background-image: url('@/assets/road.png');
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  border-radius: 8px;
  overflow: visible;
}

.grade-fill {
  height: 100%;
  background: transparent;
  transition: width 0.3s ease;
}

.grade-marker {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 30px;
  transition: left 0.3s ease;
  z-index: 2;
  max-width: calc(100% - 10px);
}

.marker-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.3));
}

.marker-icon img {
  width: 35px;
  height: 25px;
  object-fit: contain;
}

.grade-labels {
  display: flex;
  justify-content: space-between;
  padding: 5px 5px 0 5px;
  margin-top: 5px;
}

.grade-label {
  color: #000000;
  font-size: 12px;
  font-weight: 400;
  font-family: 'Inter', sans-serif;
}

/* Menu Items */
.menu-items {
  padding: 0 26px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.menu-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.menu-item:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.menu-icon {
  flex-shrink: 0;
}

.menu-content {
  flex: 1;
}

.menu-title {
  color: #333333;
  font-size: 18px;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
  margin: 0 0 5px 0;
  line-height: 1.3;
}

.menu-description {
  color: #666666;
  font-size: 14px;
  font-weight: 400;
  font-family: 'Inter', sans-serif;
  margin: 0;
  line-height: 1.4;
}

/* Responsive Design */
@media (max-width: 440px) {
  .main-page-container {
    width: 100vw;
    height: 100vh;
  }
  
  .welcome-section {
    padding: 30px 20px 25px;
  }
  
  .profile-card-container {
    margin: 0 20px 30px;
  }
  
  .profile-card {
    --card-width: 260px;
  }
  
  .menu-items {
    padding: 0 20px;
  }
}

/* 터치 환경 최적화 - 모든 터치 기기에 적용 */
.profile-card {
  /* 카드 내부 요소들의 터치 이벤트 차단하여 부모에서 통합 처리 */
}

/* 드래그 중일 때 빠른 반응을 위한 클래스 */
.profile-card.dragging {
  transition: none !important;
}

/* 더블 탭 시각적 피드백 */
.profile-card.double-tap-feedback {
  animation: doubleTapPulse 0.3s ease-out;
}

@keyframes doubleTapPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.card-front *,
.card-back * {
  pointer-events: none !important;
}

/* 🔸 기존 터치 영역 확장: 그대로 둠(홀로그램은 ::after 사용하므로 충돌 없음) */
.profile-card::before {
  content: '';
  position: absolute;
  top: -10px;
  left: -10px;
  right: -10px;
  bottom: -10px;
  z-index: -1;
  background: transparent;
}

/* 카드 전체가 터치 가능하도록 */
.profile-card,
.card-inner,
.card-front,
.card-back {
  touch-action: none !important;
}

/* 모바일 전용 최적화 */
@media (hover: none) and (pointer: coarse) {
  .profile-card {
    cursor: default;
  }
  
  .profile-card:hover {
    transition: none;
  }
  
  .profile-card:active {
    /* transform 제거하여 JavaScript 제어와 충돌 방지 */
  }
}

@media (min-width: 441px) {
  .main-page-container {
    width: 440px;
    height: auto;
    min-height: 100vh;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
  }
  
  .main-content {
    flex: 1;
    height: auto;
    min-height: calc(100vh - 160px);
    padding-bottom: 20px;
  }
}
</style>
