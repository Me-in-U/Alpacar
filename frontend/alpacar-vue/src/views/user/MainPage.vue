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
          :class="{ 'is-flipped': isCardFlipped }" 
          @click="flipCard"
          @mousemove="handleMouseMove"
          @mouseleave="handleMouseLeave"
          @touchstart="handleTouchStart"
          @touchmove="handleTouchMove"
          @touchend="handleTouchEnd"
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
                        <img src="@/assets/초급자알파카_아바타.png" alt="Grade Icon" />
                      </div>
                    </div>
                  </div>
                  <div class="grade-labels">
                    <span class="grade-label">0</span>
                    <span class="grade-label">50</span>
                    <span class="grade-label">85</span>
                    <span class="grade-label">100</span>
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
import { ref, onMounted } from 'vue'

const isCardFlipped = ref(false)
const cardRef = ref<HTMLElement>()
const isTouching = ref(false)

const flipCard = () => {
  isCardFlipped.value = !isCardFlipped.value
}

const handleMouseMove = (event: MouseEvent) => {
  if (!cardRef.value) return
  
  const rect = cardRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  
  const rotateX = (y - centerY) / centerY * -10 // -10 to 10 degrees
  const rotateY = (x - centerX) / centerX * 10 // -10 to 10 degrees
  
  cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
  cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
}

const handleMouseLeave = () => {
  if (!cardRef.value) return
  
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
}

const handleTouchStart = (event: TouchEvent) => {
  isTouching.value = true
  event.preventDefault()
}

const handleTouchMove = (event: TouchEvent) => {
  if (!isTouching.value || !cardRef.value) return
  
  event.preventDefault()
  const touch = event.touches[0]
  const rect = cardRef.value.getBoundingClientRect()
  const x = touch.clientX - rect.left
  const y = touch.clientY - rect.top
  
  const centerX = rect.width / 2
  const centerY = rect.height / 2
  
  const rotateX = (y - centerY) / centerY * -10 // -10 to 10 degrees
  const rotateY = (x - centerX) / centerX * 10 // -10 to 10 degrees
  
  cardRef.value.style.setProperty('--rotate-x', `${rotateX}deg`)
  cardRef.value.style.setProperty('--rotate-y', `${rotateY}deg`)
}

const handleTouchEnd = () => {
  isTouching.value = false
  if (!cardRef.value) return
  
  cardRef.value.style.setProperty('--rotate-x', '0deg')
  cardRef.value.style.setProperty('--rotate-y', '0deg')
}
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
  transform: rotateX(var(--rotate-x)) rotateY(var(--rotate-y));
}

.profile-card:hover {
  transition: transform 0.1s ease-out;
}

.profile-card.is-flipped {
  transform: rotateX(var(--rotate-x)) rotateY(calc(var(--rotate-y) + 180deg));
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
  gap: 20px;
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
  gap: 10px;
}

.grade-bar {
  position: relative;
  width: 100%;
  height: 40px;
  background: #666666;
  border-radius: 8px;
  overflow: hidden;
}

.grade-fill {
  height: 100%;
  background: #4CAF50;
  transition: width 0.3s ease;
}

.grade-marker {
  position: absolute;
  top: -5px;
  width: 30px;
  height: 30px;
  transition: left 0.3s ease;
}

.marker-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.marker-icon img {
  width: 25px;
  height: 25px;
  object-fit: contain;
}

.grade-labels {
  display: flex;
  justify-content: space-between;
  padding: 0 5px;
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

@media (min-width: 441px) {
  .main-page-container {
    width: 440px;
    margin: 0 auto;
  }
}
</style>