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
                    <img src="@/assets/초급자알파카_아바타.png" alt="User Avatar" class="avatar-image" />
                  </div>
                </div>
                <div class="profile-right">
                  <div class="skill-badge">
                    <div class="skill-icon">
                      <div class="skill-circle">
                      </div>
                    </div>
                    <span class="skill-text">초급자</span>
                  </div>
                  <div class="user-info">
                    <div class="user-name">
                      <span class="label">Name</span>
                      <span class="separator">|</span>
                      <span class="value">User</span>
                    </div>
                    <div class="user-number">
                      <span class="label">No.</span>
                      <span class="separator">|</span>
                      <span class="value">111 가 1111</span>
                    </div>
                    <p class='touch-text-description'>카드를 터치하면 화면이 돌아갑니다.</p>
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
                  <h2>초급자(50점)</h2>
                </div>
                <div class="grade-display">
                  <div class="grade-bar">
                    <div class="grade-fill" style="width: 50%"></div>
                    <div class="grade-marker" style="left: 50%">
                      <div class="marker-icon">
                        <img src="@/assets/alpaka_in_car.png" alt="Alpaka in Car" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Menu Items -->
      <div class="menu-items">
        <div class="menu-item">
          <div class="menu-icon">
          </div>
          <div class="menu-content">
            <h3 class="menu-title">내 주차기록 확인하기</h3>
            <p class="menu-description">주차기록과 운전 점수를 확인해보세요</p>
          </div>
        </div>

        <div class="menu-item">
          <div class="menu-icon">
          </div>
          <div class="menu-content">
            <h3 class="menu-title">주차 자리 추천 받기</h3>
            <p class="menu-description">최적화된 주차 자리를 추천받아보세요</p>
          </div>
        </div>

        <div class="menu-item">
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
import { ref, onMounted, onUnmounted } from 'vue'

// 모바일 기기 감지 함수
const detectMobile = () => {
  const isMobileUA = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0)
  const result = isMobileUA || isTouchDevice
  
  console.log('모바일 감지:', {
    userAgent: navigator.userAgent,
    isMobileUA,
    isTouchDevice,
    maxTouchPoints: navigator.maxTouchPoints,
    ontouchstart: 'ontouchstart' in window,
    result
  })
  
  // 터치 이벤트가 있는 모든 기기에서 활성화 (데스크톱 터치스크린 포함)
  return result || isTouchDevice // 터치 지원 기기에서 모두 활성화
}

const isCardFlipped = ref(false)
const cardRef = ref<HTMLElement>()
const isTouching = ref(false)
const isDragging = ref(false)
const touchStartTime = ref(0)
const isMobile = ref(false)
const initialTouch = ref({ x: 0, y: 0 })
const touchThreshold = ref(1) // 터치 이동 임계값 (매우 민감하게)
const isMouseDown = ref(false)
const initialMouse = ref({ x: 0, y: 0 })
const isMouseDragging = ref(false)
const lastTapTime = ref(0)
const tapCount = ref(0)
const doubleTapDelay = ref(400) // 더블 탭 인식 시간 (ms) - 조금 더 여유있게

const flipCard = () => {
  isCardFlipped.value = !isCardFlipped.value
}

const handleClick = () => {
  // 드래그 중이 아닐 때만 카드 뒤집기 (모바일/데스크톱 모두)
  if (!isDragging.value) {
    console.log('Click event - flipping card')
    flipCard()
  } else {
    console.log('Click event - blocked due to dragging')
  }
}

const handleMouseMove = (event: MouseEvent) => {
  // 마우스 이동 처리 - 드래그 중이면 드래그 핸들러로, 아니면 호버 효과
  if (!cardRef.value) return
  
  if (isMouseDown.value) {
    // 드래그 중이면 드래그 핸들러 호출
    handleMouseMoveWhileDragging(event)
    return
  }
  
  // 호버 효과 (드래그 중이 아닐 때만)
  console.log('Mouse hover effect:', { isMobile: isMobile.value, clientX: event.clientX, clientY: event.clientY })
  
  const rect = cardRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  
  const rotateX = (y - centerY) / centerY * -10 // -10 to 10 degrees
  const rotateY = (x - centerX) / centerX * 10 // -10 to 10 degrees
  
  // 마우스 호버 시 3D 효과 (카드 뒤집기 상태 고려)
  if (isCardFlipped.value) {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY + 180}deg)`
  } else {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
  }
  
  cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
  cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
}

const handleMouseLeave = () => {
  // 마우스 떠날 시 처리 (모바일 포함)
  if (!cardRef.value) return
  
  console.log('Mouse leave event:', { isMobile: isMobile.value, isMouseDown: isMouseDown.value })
  
  // 드래그 중이 아닐 때만 호버 효과 초기화
  if (!isMouseDown.value) {
    // 마우스 떠날 시 초기화 (카드 뒤집기 상태 고려)
    if (isCardFlipped.value) {
      cardRef.value.style.transform = 'rotateX(0deg) rotateY(180deg)'
    } else {
      cardRef.value.style.transform = 'rotateX(0deg) rotateY(0deg)'
    }
    
    cardRef.value.style.setProperty('--rotate-x', '0deg')
    cardRef.value.style.setProperty('--rotate-y', '0deg')
  }
}

// 마우스 드래그 이벤트 핸들러들
const handleMouseDown = (event: MouseEvent) => {
  console.log('Mouse down event:', { isMobile: isMobile.value, button: event.button })
  
  // 좌클릭만 처리
  if (event.button !== 0) return
  
  isMouseDown.value = true
  isMouseDragging.value = false
  initialMouse.value = { x: event.clientX, y: event.clientY }
  
  console.log('Mouse down processed:', { 
    position: { x: event.clientX, y: event.clientY },
    isMouseDown: isMouseDown.value
  })
  
  // 마우스 이벤트 차단하여 텍스트 선택 방지
  event.preventDefault()
}

const handleMouseMoveWhileDragging = (event: MouseEvent) => {
  if (!isMouseDown.value || !cardRef.value) return
  
  const deltaX = Math.abs(event.clientX - initialMouse.value.x)
  const deltaY = Math.abs(event.clientY - initialMouse.value.y)
  
  // 마우스 이동이 조금이라도 있으면 즉시 드래그로 인식
  if (deltaX > 1 || deltaY > 1) {
    isMouseDragging.value = true
    isDragging.value = true // 전역 드래그 상태도 설정
  }
  
  const rect = cardRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  
  const rotateX = (y - centerY) / centerY * -20 // -20 to 20 degrees
  const rotateY = (x - centerX) / centerX * 20 // -20 to 20 degrees
  
  console.log('Mouse drag - 3D Animation:', { 
    mouse: { x: event.clientX, y: event.clientY },
    rect: { x: rect.left, y: rect.top, width: rect.width, height: rect.height },
    center: { x: centerX, y: centerY },
    rotation: { rotateX, rotateY }, 
    isMouseDragging: isMouseDragging.value,
    delta: { deltaX, deltaY }
  })
  
  // 즉시 3D 회전 적용 (카드 뒤집기 상태 고려)
  if (isCardFlipped.value) {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY + 180}deg)`
  } else {
    cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
  }
  
  cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
  cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
}

const handleMouseUp = () => {
  console.log('Mouse up event:', { 
    isMouseDown: isMouseDown.value, 
    isMouseDragging: isMouseDragging.value 
  })
  
  isMouseDown.value = false
  
  // 마우스 드래그가 끝나면 전역 드래그 상태도 해제
  if (isMouseDragging.value) {
    isDragging.value = false
    console.log('Mouse drag completed')
  }
  
  isMouseDragging.value = false
  
  // 마우스 드래그 종료 후 상태에 따른 초기화
  if (!cardRef.value) return
  
  if (isCardFlipped.value) {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(180deg)'
  } else {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(0deg)'
  }
  
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
}

const handleTouchStart = (event: TouchEvent) => {
  console.log('Touch start event triggered!', { isMobile: isMobile.value, touches: event.touches.length })
  
  const touch = event.touches[0]
  initialTouch.value = { x: touch.clientX, y: touch.clientY }
  
  isTouching.value = true
  isDragging.value = false
  touchStartTime.value = Date.now()
  
  console.log('Touch start processed:', { 
    position: { x: touch.clientX, y: touch.clientY },
    isMobile: isMobile.value,
    isTouching: isTouching.value
  })
  
  // 터치 시작 시 즉시 3D 애니메이션 준비 상태로 설정
  if (cardRef.value) {
    console.log('카드 3D 애니메이션 준비됨 - 터치 시작, 다음 move에서 즉시 활성화됨')
  }
  
  // Vue의 prevent 모디파이어로 처리됨
}

const handleTouchMove = (event: TouchEvent) => {
  console.log('Touch move event triggered!', { isMobile: isMobile.value, isTouching: isTouching.value })
  
  // 터치 이벤트가 활성화되어 있지 않으면 리턴
  if (!isTouching.value || !cardRef.value) {
    console.log('Touch move blocked:', { isTouching: isTouching.value, cardRef: !!cardRef.value })
    return
  }
  
  const touch = event.touches[0]
  const deltaX = Math.abs(touch.clientX - initialTouch.value.x)
  const deltaY = Math.abs(touch.clientY - initialTouch.value.y)
  
  // 더블 탭과 구분하기 위해 최소한의 이동이 있을 때만 드래그로 인식
  if (deltaX > 3 || deltaY > 3) {
    isDragging.value = true
    // 드래그 시작되면 탭 카운트 리셋
    tapCount.value = 0
    lastTapTime.value = 0
    console.log('드래그 감지 - 탭 카운트 리셋')
  }
  
  // Vue의 prevent 모디파이어로 처리됨
  
  // 드래그 중일 때만 3D 애니메이션 적용
  if (isDragging.value) {
    const rect = cardRef.value.getBoundingClientRect()
    const x = touch.clientX - rect.left
    const y = touch.clientY - rect.top
    
    const centerX = rect.width / 2
    const centerY = rect.height / 2
    
    const rotateX = (y - centerY) / centerY * -20 // -20 to 20 degrees
    const rotateY = (x - centerX) / centerX * 20 // -20 to 20 degrees
    
    console.log('Touch drag - 3D Animation ACTIVE:', { 
      touch: { x: touch.clientX, y: touch.clientY },
      rect: { x: rect.left, y: rect.top, width: rect.width, height: rect.height },
      center: { x: centerX, y: centerY },
      rotation: { rotateX, rotateY }, 
      isDragging: isDragging.value,
      delta: { deltaX, deltaY }
    })
    
    // 즉시 3D 회전 적용 (카드 뒤집기 상태 고려)
    if (isCardFlipped.value) {
      cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY + 180}deg)`
    } else {
      cardRef.value.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
    }
    
    cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
    cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
  }
}

const handleTouchEnd = () => {
  console.log('Touch end event triggered!')
  
  const touchDuration = Date.now() - touchStartTime.value
  const currentTime = Date.now()
  
  console.log('Touch end:', { 
    duration: touchDuration, 
    isDragging: isDragging.value,
    isMobile: isMobile.value,
    isTouching: isTouching.value,
    tapCount: tapCount.value
  })
  
  // 드래그하지 않았고 빠른 탭일 때만 탭으로 처리
  if (!isDragging.value && touchDuration < 250) {
    const timeSinceLastTap = currentTime - lastTapTime.value
    
    if (timeSinceLastTap < doubleTapDelay.value) {
      // 더블 탭 감지
      tapCount.value++
      console.log(`탭 카운트: ${tapCount.value}`)
      
      if (tapCount.value >= 2) {
        console.log('더블 탭 감지! 카드 뒤집기')
        
        // 시각적 피드백 추가
        if (cardRef.value) {
          cardRef.value.classList.add('double-tap-feedback')
          setTimeout(() => {
            if (cardRef.value) {
              cardRef.value.classList.remove('double-tap-feedback')
            }
          }, 300)
        }
        
        flipCard()
        tapCount.value = 0 // 카운트 리셋
        lastTapTime.value = 0
      }
    } else {
      // 첫 번째 탭 또는 시간 초과로 새로운 탭 시퀀스 시작
      tapCount.value = 1
      console.log('첫 번째 탭 감지, 더블 탭 대기 중...')
    }
    
    lastTapTime.value = currentTime
    
    // 더블 탭 대기 시간 후 자동으로 카운트 리셋
    setTimeout(() => {
      if (tapCount.value === 1) {
        console.log('더블 탭 시간 초과, 단일 탭으로 처리')
        tapCount.value = 0
        lastTapTime.value = 0
      }
    }, doubleTapDelay.value)
    
  } else if (isDragging.value) {
    console.log('Touch end - drag completed')
    // 드래그 종료 시 탭 카운트 리셋
    tapCount.value = 0
    lastTapTime.value = 0
  }
  
  isTouching.value = false
  isDragging.value = false
  
  // 터치 종료 후 상태에 따른 초기화
  if (!cardRef.value) return
  
  // CSS 클래스로 transition 관리하므로 별도 설정 불필요
  
  if (isCardFlipped.value) {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(180deg)'
  } else {
    cardRef.value.style.transform = 'rotateX(0deg) rotateY(0deg)'
  }
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
}


onMounted(() => {
  isMobile.value = detectMobile()
  console.log('모바일 감지 결과:', isMobile.value)
  
  // 전역 마우스 이벤트 리스너 추가 (카드 영역 밖에서 마우스 업 감지)
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
  
  // 컴포넌트 언마운트 시 이벤트 리스너 정리
  onUnmounted(() => {
    document.removeEventListener('mouseup', handleGlobalMouseUp)
    document.removeEventListener('mousemove', handleGlobalMouseMove)
  })
  
  // 터치 이벤트 리스너 상태 확인
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
  
  // 3초 후 테스트 메시지
  setTimeout(() => {
    console.log('이벤트 테스트: 카드를 터치하거나 마우스로 드래그해보세요!')
    console.log('더블 탭 테스트: 카드를 두 번 연속 빠르게 터치하면 뒷면으로 전환됩니다!')
  }, 3000)
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
  width: var(--card-width);
  aspect-ratio: 5 / 7; /* 운전면허증 비율 */
  position: relative;
  cursor: pointer;
  transform-style: preserve-3d;
  transition: transform 0.9s ease-in-out; /* 50% 느리게 조정 */
  touch-action: none; /* 모바일에서 스크롤 방지 */
  user-select: none; /* 텍스트 선택 방지 */
  
  /* 터치 영역 보장 */
  min-height: 200px;
  min-width: 150px;
}

.profile-card:hover {
  transition: transform 0.1s ease-out;
}

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
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transition: box-shadow 0.3s ease;
  pointer-events: auto; /* 터치 이벤트 활성화 */
}

.profile-card:hover .card-front,
.profile-card:hover .card-back {
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
}

.card-front {
  background: #FFFFFF;
}

.card-back {
  background: #EBE3D5;
  border: 1px solid #B3B3B3;
  transform: rotateY(180deg);
}

/* Front Side Styles */
.profile-header {
  height: 50px;
  background: #776B5D;
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
  background-image: url('@/assets/초보자핸들.png');
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
  background: #776B5D;
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

/* 터치 영역 확장 */
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
  
  /* 터치 시 시각적 피드백 제거 */
  .profile-card:active {
    /* transform 제거하여 JavaScript 제어와 충돌 방지 */
  }
}

@media (min-width: 441px) {
  .main-page-container {
    width: 440px;
    margin: 0 auto;
  }
}
</style>