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
              <div class="profile-header"></div>
              <div class="profile-content">
                <div class="profile-left">
                  <div class="avatar-container">
                    <img :src="avatarImage" alt="User Avatar" class="avatar-image" />
                  </div>
                </div>
                <div class="profile-right">
                  <div class="skill-badge">
                    <div class="skill-icon">
                      <div class="skill-circle" :style="skillCircleVars"></div>
                    </div>
                    <span class="skill-text" :data-text="gradeInfo.text" :style="{ color: gradeInfo.color }">{{ gradeInfo.text }}</span>
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
              <div class="back-header"></div>
              <div class="back-content">
                <div class="back-title">
                  <h2>{{ gradeInfo.text }}({{ userScore }}점)</h2>
                </div>
                <div class="grade-display">
                  <div class="grade-bar">
                    <img class="road-bg" :src="roadSrc" alt="" />
                    <div class="grade-fill" :style="{ width: userScore + '%' }"></div>
                    <div class="grade-marker" :style="{ left: `${Math.max(5, Math.min(95, userScore))}%` }">
                      <div class="marker-icon">
                        <img :src="carWithAlpacaImage" alt="Car With Alpaca" />
                      </div>
                    </div>
                  </div>
                </div>
                <div class="grade-tips">
                  💡Tip! 점수를 올리고 싶다면?<br>
                  (주차 점수를 올리는 팁 두 줄)
                </div>
              </div>
            </div>

          </div> <!-- /card-inner -->
        </div>
      </div>

      <!-- Menu Items -->
      <div class="menu-items">
        <div class="menu-item" @click="goToParkingHistory">
          <div class="menu-content-wrapper">
            <div class="menu-icon">
              <img src="@/assets/alpaca-parkinglog.png" alt="주차기록 아이콘" class="menu-image" />
            </div>
            <p class="menu-title">내 주차기록<br>확인하기</p>
          </div>
          <div class="menu-accent"></div>
        </div>

        <div class="menu-item" @click="goToParkingRecommend">
          <div class="menu-content-wrapper">
            <div class="menu-icon">
              <img src="@/assets/alpaca-parkingrecommend.png" alt="주차 추천 아이콘" class="menu-image" />
            </div>
            <p class="menu-title">주차 자리<br>추천 받기</p>
          </div>
          <div class="menu-accent coral"></div>
        </div>

        <div class="menu-item" @click="goToUserProfile">
          <div class="menu-content-wrapper">
            <div class="menu-icon">
              <img src="@/assets/alpaca-mypage.png" alt="내 정보 아이콘" class="menu-image" />
            </div>
            <p class="menu-title">내 정보<br>확인하기</p>
          </div>
          <div class="menu-accent sage"></div>
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
// HeaderTest import removed - using regular Header component


const router = useRouter()
const userStore = useUserStore()

const carWithAlpacaImage = new URL('@/assets/car-with-alpaca.png', import.meta.url).href

// const userScore = computed(() => userStore.me?.score || 0)
const userScore = ref(90)
const userName = computed(() => userStore.me?.nickname || 'User')
const userVehicleNumber = computed(() => {
  return userStore.vehicles.length > 0 ? userStore.vehicles[0].license_plate : '111 가 1111'
})

const userGrade = computed(() => {
  const score = userScore.value
  if (score <= 50) return 'beginner'
  if (score <= 85) return 'intermediate'
  return 'advanced'
})

const gradeInfo = computed(() => {
  const grade = userGrade.value
  switch (grade) {
    case 'beginner':
      return { text: '초급자', color: '#E1AD8D' }
    case 'intermediate':
      return { text: '중급자', color: '#C0C0C0' }
    case 'advanced':
      return { text: '상급자', color: '#FFD700' }
    default:
      return { text: '초급자', color: '#E1AD8D' }
  }
})

const avatarImage = computed(() => {
  const grade = userGrade.value
  switch (grade) {
    case 'beginner':
      return new URL('@/assets/alpacar-beginner.png', import.meta.url).href
    case 'intermediate':
      return new URL('@/assets/alpacar-intermediate.png', import.meta.url).href
    case 'advanced':
      return new URL('@/assets/alpacar-advanced.png', import.meta.url).href
    default:
      return new URL('@/assets/alpacar-beginner.png', import.meta.url).href
  }
})

const skillIcon = computed(() => {
  switch (userGrade.value) {
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

const skillCircleVars = computed(() => {
  // 등급별 금/은/동 베이스 컬러 유지 (UI 기본 팔레트는 CSS에서 변경)
  const base = {
    beginner: ['#D4A373', '#8B5E3C'],
    intermediate: ['#C0C0C0', '#7D7D7D'],
    advanced: ['#FFD700', '#B8860B']
  }[userGrade.value]

  return {
    '--icon-mask': `url(${skillIcon.value})`,
    '--icon-g1': base[0],
    '--icon-g2': base[1]
  }
})

/* 등급별 변수 (테두리 그라데이션 팔레트 + 광택 강도 + 헤더 색) */
const holoGradeVars = computed(() => {
  switch (userGrade.value) {
    case 'beginner': // 동 (Bronze)
      return {
        '--c1': '#D4A373', // 밝은 브론즈 (고급스러운 황갈색)
        '--c2': '#8B5E3C', // 어두운 브론즈 (차분한 브라운)
        '--grade-gloss': 0.45,
        '--header-color': '#D4A373',
        '--card-back-bg': '#F2E0C9' // 뒷면 밝은 브론즈
      }
    case 'intermediate': // 은 (Silver)
      return {
        '--c1': '#C0C0C0', // 은색
        '--c2': '#7D7D7D', // 진회색
        '--grade-gloss': 0.85,
        '--header-color': '#C0C0C0',
        '--card-back-bg': '#F0F0F0' // 뒷면 밝은 은색 톤
      }
    case 'advanced': // 금 (Gold)
      return {
        '--c1': '#FFD700', // 금색
        '--c2': '#B8860B', // 황토·금빛 섀도
        '--grade-gloss': 1.2,
        '--header-color': '#FFD700',
        '--card-back-bg': '#FFF3CC' // 뒷면 밝은 금색 톤
      }
    default:
      return {
        '--c1': '#B87333',
        '--c2': '#7B3F00',
        '--grade-gloss': 0.45,
        '--header-color': '#B87333',
        '--card-back-bg': '#F3D9C0'
      }
  }
})

const roadSrc = new URL('@/assets/road.png', import.meta.url).href

const goToParkingHistory = async () => { try { await router.push('/parking-history') } catch (e) { console.error(e) } }
const goToParkingRecommend = async () => { try { await router.push('/parking-recommend') } catch (e) { console.error(e) } }
const goToUserProfile = async () => { try { await router.push('/user-profile') } catch (e) { console.error(e) } }

const detectMobile = () => {
  const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0)
  return isMobileUA || isTouchDevice
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

const flipCard = () => { isCardFlipped.value = !isCardFlipped.value }
const handleClick = () => { if (!isDragging.value) flipCard() }

/* 커서/터치 위치에 따른 빛 하이라이트 변수 업데이트 (얼굴 전체에서 공유) */
function updateShineVars(x: number, y: number, rect: DOMRect) {
  if (!cardRef.value) return
  const cx = rect.width / 2
  const cy = rect.height / 2
  const dx = (x - cx) / cx
  const dy = (y - cy) / cy
  const mag = Math.min(1, Math.hypot(dx, dy))
  const shineO = (0.22 + 0.38 * mag).toFixed(3)
  const sx = (x / rect.width) * 100
  const sy = (y / rect.height) * 100
  cardRef.value.style.setProperty('--shineX', `${sx}%`)
  cardRef.value.style.setProperty('--shineY', `${sy}%`)
  cardRef.value.style.setProperty('--shineO', `${shineO}`)
}

const handleMouseMove = (event: MouseEvent) => {
  if (!cardRef.value) return
  if (isMouseDown.value) { handleMouseMoveWhileDragging(event); return }
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
    cardRef.value.style.transform = isCardFlipped.value ? 'rotateX(0deg) rotateY(180deg)' : 'rotateX(0deg) rotateY(0deg)'
    cardRef.value.style.setProperty('--rotate-x', '0deg')
    cardRef.value.style.setProperty('--rotate-y', '0deg')
    cardRef.value.style.setProperty('--shineX', '50%')
    cardRef.value.style.setProperty('--shineY', '50%')
    cardRef.value.style.setProperty('--shineO', '0.28')
  }
}

const handleMouseDown = (event: MouseEvent) => {
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
  isMouseDown.value = false
  if (isMouseDragging.value) isDragging.value = false
  isMouseDragging.value = false
  if (!cardRef.value) return
  cardRef.value.style.transform = isCardFlipped.value ? 'rotateX(0deg) rotateY(180deg)' : 'rotateX(0deg) rotateY(0deg)'
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
  cardRef.value.style.setProperty('--shineX', '50%')
  cardRef.value.style.setProperty('--shineY', '50%')
  cardRef.value.style.setProperty('--shineO', '0.28')
}

const handleTouchStart = (event: TouchEvent) => {
  const touch = event.touches[0]
  initialTouch.value = { x: touch.clientX, y: touch.clientY }
  isTouching.value = true
  isDragging.value = false
  touchStartTime.value = Date.now()
}

const handleTouchMove = (event: TouchEvent) => {
  if (!isTouching.value || !cardRef.value) return
  const touch = event.touches[0]
  const deltaX = Math.abs(touch.clientX - initialTouch.value.x)
  const deltaY = Math.abs(touch.clientY - initialTouch.value.y)
  if (deltaX > 3 || deltaY > 3) {
    isDragging.value = true
    tapCount.value = 0
    lastTapTime.value = 0
  }
  if (isDragging.value) {
    const rect = cardRef.value.getBoundingClientRect()
    const x = touch.clientX - rect.left
    const y = touch.clientY - rect.top
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
}

const handleTouchEnd = () => {
  const touchDuration = Date.now() - touchStartTime.value
  const currentTime = Date.now()
  if (!isDragging.value && touchDuration < 250) {
    const timeSinceLastTap = currentTime - lastTapTime.value
    if (timeSinceLastTap < doubleTapDelay.value) {
      tapCount.value++
      if (tapCount.value >= 2) {
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
    }
    lastTapTime.value = currentTime
    setTimeout(() => {
      if (tapCount.value === 1) {
        tapCount.value = 0
        lastTapTime.value = 0
      }
    }, doubleTapDelay.value)
  } else if (isDragging.value) {
    tapCount.value = 0
    lastTapTime.value = 0
  }

  isTouching.value = false
  isDragging.value = false

  if (!cardRef.value) return
  cardRef.value.style.transform = isCardFlipped.value ? 'rotateX(0deg) rotateY(180deg)' : 'rotateX(0deg) rotateY(0deg)'
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
  cardRef.value.style.setProperty('--shineX', '50%')
  cardRef.value.style.setProperty('--shineY', '50%')
  cardRef.value.style.setProperty('--shineO', '0.28')
}

onMounted(async () => {
  isMobile.value = detectMobile()
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      if (!userStore.me) { await userStore.fetchMe(token) }
      if (userStore.vehicles.length === 0) { await userStore.fetchMyVehicles() }
    }
  } catch (error) {
    console.error('사용자 정보 로드 실패:', error)
  }

  const handleGlobalMouseUp = () => { if (isMouseDown.value) handleMouseUp() }
  const handleGlobalMouseMove = (event: MouseEvent) => {
    if (isMouseDown.value && cardRef.value) handleMouseMoveWhileDragging(event)
  }
  document.addEventListener('mouseup', handleGlobalMouseUp)
  document.addEventListener('mousemove', handleGlobalMouseMove)

  onUnmounted(() => {
    document.removeEventListener('mouseup', handleGlobalMouseUp)
    document.removeEventListener('mousemove', handleGlobalMouseMove)
  })
})
</script>

<style scoped>
.main-page-container {
  width: 440px;
  height: 956px;
  position: relative;
  background: #F9F5EC; /* 유지 */
  overflow: hidden;
  margin: 0 auto;
}

.main-content {
  position: relative;
  padding-top: 80px; /* 헤더 높이 */
  padding-bottom: calc(80px + env(safe-area-inset-bottom, 0px)); /* 하단 네비 + 안전영역 */
  height: auto;
  min-height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.welcome-section {
  padding: 0px 26px 30px;
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
  color: #565656; /* #666666 → 팔레트 mid-gray */
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
  border: var(--card-border) solid transparent; /* 테두리는 링에서 표현 */
  background: transparent;
  width: var(--card-width);
  aspect-ratio: 5 / 7;
  position: relative;
  cursor: pointer;
  transform-style: preserve-3d;
  transition: transform 0.18s ease-out;
  touch-action: none;
  user-select: none;

  min-height: 200px;
  min-width: 150px;

  /* 등급 주입 변수: --c1, --c2, --grade-gloss, --header-color */
  --lp: 50%;
  --tp: 50%;
  --px_s: 50%;
  --py_s: 50%;
  --opc: 0.75;

  background: #ffffff;
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

/* 그라데이션 테두리 링 */
.profile-card::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: var(--card-radius);
  padding: var(--card-border);

  /* 기존 그라데이션 + 스파클/홀로 시트 오버레이 */
  background:
    url("https://assets.codepen.io/13471/sparkles.gif"),
    url("https://assets.codepen.io/13471/holo.png"),
    linear-gradient(115deg, var(--c1), var(--c2));
  background-size: 160%, 160%, auto;
  background-position: 50% 50%, 50% 50%, center;
  background-repeat: no-repeat;
  background-blend-mode: screen, screen, normal;

  pointer-events: none;

  /* 테두리만 보이도록 마스크 (카드 내부는 구멍) */
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;

  /* 홀로그램 광택 강도 (이미 코드에 있는 --opc, --grade-gloss 사용) */
  opacity: calc(var(--opc) * var(--grade-gloss));
  /* filter:
    brightness(calc(1 + 0.25 * var(--grade-gloss)))
    contrast(calc(1 + 0.15 * var(--grade-gloss))); */
}

.profile-card.is-flipped {
  transform: rotateY(180deg);
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  text-align: center;
  transition: transform 0.18s ease-out;
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
  isolation: isolate;
}

/* ========= 공통: 얼굴 전체에서 커서/터치에 반응하는 SHINE ========= */
.card-front::before,
.card-back::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  --shineX: 50%;
  --shineY: 50%;
  --shineO: 0.28;
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
      rgba(255,255,255, calc(var(--shineO) * 0.30)) 0%,
      rgba(255,255,255, 0) 60%
    );
  mix-blend-mode: screen;
  transition: background-position 60ms linear, opacity 120ms ease;
  opacity: 1;
}

/* ========= Hologram: 앞면 특정 영역 + 뒷면 헤더만 ========= */

/* 공통 홀로그램 배경 */
@keyframes _holoSparkleDummy {}
.holo-bg {
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
}

/* 앞면 - 헤더 */
.profile-header {
  height: 50px;
  background: var(--header-color);
  border-top-left-radius: calc(var(--card-radius) - var(--card-border));
  border-top-right-radius: calc(var(--card-radius) - var(--card-border));
  position: relative;
  overflow: hidden;
}
.profile-header::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  mix-blend-mode: color-dodge;
  opacity: calc(var(--opc) * var(--grade-gloss));
  filter: brightness(calc(1 + 0.25 * var(--grade-gloss)))
          contrast(calc(1 + 0.15 * var(--grade-gloss)));
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
}

/* 앞면 - 아바타 */
.avatar-container {
  width: 90px;
  height: 120px;
  background: #ffffff;
  border: 3px solid transparent; 
  display: block;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative; /* ::after 기준 */
  box-sizing: border-box;
}

/* 그라데이션 링 */
.avatar-container::before {
  content: "";
  position: absolute;
  inset: 0;
  padding: 3px;            /* 링 두께 = avatar-container의 border 두께와 동일 */
  background:
    url("https://assets.codepen.io/13471/sparkles.gif"),
    url("https://assets.codepen.io/13471/holo.png"),
    linear-gradient(115deg, var(--c1), var(--c2));
  background-size: 160%, 160%, auto;                 /* profile-card::after와 동일 */
  background-position: 50% 50%, 50% 50%, center;
  background-repeat: no-repeat;
  background-blend-mode: screen, screen, normal;

  pointer-events: none;

  /* 링만 보이도록 내부를 투명하게 마스킹 (profile-card::after와 동일 기법) */
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  mask-composite: exclude;

  /* 홀로그램 광택 강도: 카드와 동일 변수 사용 */
  opacity: calc(var(--opc) * var(--grade-gloss));
  z-index: 2;
}

.avatar-container::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  /* border-radius: inherit; */
  mix-blend-mode: color-dodge;
  opacity: calc(var(--opc) * var(--grade-gloss));
  filter: brightness(calc(1 + 0.25 * var(--grade-gloss)))
          contrast(calc(1 + 0.15 * var(--grade-gloss)));
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
}

.avatar-image {
  position: absolute;
  left: 50%;
  bottom: 3px;                   /* 하단에 딱 붙음 */
  transform: translateX(-50%); /* 가로 중앙 정렬 */
  width: 100px;
  height: 100px;
  object-fit: contain;
  z-index: 1;
}

/* 앞면 - 스킬 아이콘/텍스트 */
.skill-badge {
  display:flex;
  align-items:center;
  justify-content:center;
  gap:12px;
}

.skill-icon {
  flex:0 0 auto;
  display:inline-flex;
  align-items:center;
}
.skill-icon::after {
  content: none !important;
}

.skill-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  -webkit-mask: var(--icon-mask) center/contain no-repeat;
  mask: var(--icon-mask) center/contain no-repeat;
  background: linear-gradient(135deg, var(--icon-g1), var(--icon-g2));
  position: relative; 
}

.skill-circle::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 50%;
  mix-blend-mode: color-dodge;
  opacity: calc(var(--opc) * var(--grade-gloss));
  filter:
    brightness(calc(1 + 0.25 * var(--grade-gloss)))
    contrast(calc(1 + 0.15 * var(--grade-gloss)));
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
}

.skill-text {
  font-size: 18px;
  font-weight: 700;
  font-family: 'Inter', sans-serif;
  position: relative;
  display: inline-block;
  background: none;
  flex:0 0 auto;
}
.skill-text::after {
  content: attr(data-text);
  position: absolute;
  inset: 0;
  font: inherit;
  pointer-events: none;
  mix-blend-mode: color-dodge;
  opacity: calc(var(--opc) * var(--grade-gloss));
  filter: brightness(calc(1 + 0.25 * var(--grade-gloss)))
          contrast(calc(1 + 0.15 * var(--grade-gloss)));
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
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 뒷면 - 헤더에만 홀로그램 */
.card-back {
  background: var(--card-back-bg);
  border: 1px solid transparent;
  transform: rotateY(180deg);
}

.back-header {
  height: 50px;
  background: var(--header-color);
  border-top-left-radius: calc(var(--card-radius) - var(--card-border));
  border-top-right-radius: calc(var(--card-radius) - var(--card-border));
  position: relative;
  overflow: hidden;
}
.back-header::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  mix-blend-mode: color-dodge;
  opacity: calc(var(--opc) * var(--grade-gloss));
  filter: brightness(calc(1 + 0.25 * var(--grade-gloss)))
          contrast(calc(1 + 0.15 * var(--grade-gloss)));
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
}

/* Front content layout */
.profile-content {
  display: flex;
  padding: 14px;
  gap: 10px;
  height: calc(100% - 50px);
  flex-direction: column;
  justify-content: center;
}

.profile-left {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.profile-right {
  display: flex;
  flex-direction: column;
  gap: 15px;
  align-items: center;
}

.touch-text-description {
  color: #565656; /* #666666 → 팔레트 mid-gray */
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
  color: #212730; /* #333333 → 팔레트 primary-dark */
  font-size: 16px;
  font-weight: 600;
  font-family: 'Inter', sans-serif;
}

.separator {
  color: #272d37; /* #666666 → 팔레트 secondary-dark */
  font-size: 16px;
}

.value {
  color: #565656; /* #666666 → 팔레트 mid-gray */
  font-size: 16px;
  font-family: 'Inter', sans-serif;
}

/* Back content */
.back-content {
  padding: 10px;
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

.grade-tips {
  margin-top: 10px;          
  padding: 8px 12px;         
  background-color: #f9f9f9; 
  border-radius: 6px;        
  border: 1px solid #c1b49e; /* #e0e0e0 → 팔레트 light beige-gray */
  font-size: 12px;           
  line-height: 1.4;          
  color: #565656;            /* #555 → 팔레트 mid-gray */
  text-align: left;         
}

.grade-bar {
  position: relative;
  width: 100%;
  height: 85px;         /* 원하는 전체 크기 */
  overflow: visible;
}

.road-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 90%;
  object-fit: contain;  /* 비율 유지 + 컨테이너에 맞춤 */
  z-index: 0;
  pointer-events: none;
}

.grade-fill {
  position: relative;
  z-index: 1;
  height: 100%;
  background: transparent;
  transition: width 0.3s ease;
}

.grade-marker {
  position: absolute;
  top: 50%;
  transform: translateX(-50%) translateY(-50%);
  width: 60px;
  height: 45px;
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
  width: 40px;
  height: 28px;
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
  padding: 0 16px;
  display: flex;
  flex-direction: row; /* 🔹 가로 배치 */
  gap: 12px;           /* 카드 간격 */
  justify-content: center; /* 가운데 정렬 */
}

.menu-item {
  flex: 0 0 calc((100% - 24px) / 3);  /* 12px 갭 * 2 제외 후 1/3 */
  box-sizing: border-box;             /* 패딩 포함 계산 */
  min-width: 0;                       /* 자식 최소폭으로 밀리지 않게 */
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;

  padding: 0px;                      /* 기존 20px → 16px */
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.1);
  cursor: pointer;
  transition: all .3s ease;
  position: relative;
  overflow: hidden;
}

/* 1번째 메뉴 */
.menu-item:nth-child(1) {
  border-bottom: 2px solid #4E7F58;
}

/* 2번째 메뉴 */
.menu-item:nth-child(2) {
  border-bottom: 2px solid #C7A653;
}

/* 3번째 메뉴 */
.menu-item:nth-child(3) {
  border-bottom: 2px solid #A14436;
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
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 8px; 
}

.menu-image {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.menu-content-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  padding: 16px 8px; /* 🔹 상하 여백 동일하게 */
  height: 100%; /* 카드 높이 내에서 균등 배치 */
}

.menu-title {
  font-size: 14px;
  font-weight: 600;
  color: #212730; /* #333 → 팔레트 primary-dark */
  margin: 0;
  white-space: normal; /* 줄바꿈 허용 */
  text-align: center;
}

.menu-description {
  color: #565656; /* #666666 → 팔레트 mid-gray */
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
  
  .main-content {
    padding-top: 40px;
    padding-bottom: calc(
      var(--bottom-nav-height) + 16px
      + env(safe-area-inset-bottom, 0px)
    ) !important;
    /* 일부 브라우저 구버전 호환 (iOS 오래된 사파리) */
    padding-bottom: calc(
      var(--bottom-nav-height) + 16px
      + constant(safe-area-inset-bottom, 0px)
    ) !important;
  }
}

/* 터치 환경 최적화 */
.profile-card { }
.profile-card.dragging { transition: none !important; }
.profile-card.double-tap-feedback { animation: doubleTapPulse 0.3s ease-out; }
@keyframes doubleTapPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}

.card-front *,
.card-back * {
  pointer-events: none !important;
}

/* 기존 터치 영역 확장 */
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

.profile-card,
.card-inner,
.card-front,
.card-back {
  touch-action: none !important;
}

@media (hover: none) and (pointer: coarse) {
  .profile-card { cursor: default; }
  .profile-card:hover { transition: none; }
  .profile-card:active { }
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


