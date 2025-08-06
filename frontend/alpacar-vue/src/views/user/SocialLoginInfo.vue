<template>
  <div class="social-login-info-container">
    <!-- Main Content -->
    <div class="main-content">
      <!-- Page Title -->
      <div class="title-section">
        <h1 class="page-title">차량 등록을 해주세요</h1>
      </div>

      <!-- Vehicle Info Section -->
      <div class="vehicle-info-section">
        <div class="vehicle-info-card">
          <div class="vehicle-info-content">
            <div class="vehicle-info-text">
              <h2 class="vehicle-title">내 차를<br/>추가해주세요</h2>
              <p class="vehicle-description">내 차종에 맞는 주차 위치를 추천해드립니다.</p>
            </div>
            <div class="vehicle-image" @click="showModal = true">
              <img src="@/assets/addcar.png" alt="차량 이미지" class="car-image" />
              <button class="add-vehicle-button" @click.stop="showModal = true" />
            </div>
          </div>
        </div>
      </div>

      <!-- Parking Skill Section -->
      <div class="parking-skill-section">
        <h2 class="skill-title">주차실력을 알려주세요</h2>
        <div class="skill-selection ">
          <button 
            class="skill-button" 
            :class="{ selected: selectedSkill === 'advanced' }"
            @click="selectedSkill = 'advanced'"
          >
            상급자 (좁은 공간도 가능)
          </button>
          <button 
            class="skill-button" 
            :class="{ selected: selectedSkill === 'intermediate' }"
            @click="selectedSkill = 'intermediate'"
          >
            중급자 (보통 크기 공간)
          </button>
          <button 
            class="skill-button" 
            :class="{ selected: selectedSkill === 'beginner' }"
            @click="selectedSkill = 'beginner'"
          >
            초급자 (넓은 공간 필요)
          </button>
        </div>
      </div>

      <!-- Complete Button -->
      <div class="complete-button-container">
        <button class="complete-button" @click="completeSetup">
          <span class="button-text">설정 완료</span>
        </button>
      </div>
    </div>

    <!-- Vehicle Registration Modal -->
    <div v-if="showModal" class="modal-overlay" @click="showModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">차량 번호를 입력해주세요</h3>
        </div>
        <div class="modal-body">
          <input 
            v-model="vehicleNumber" 
            type="text" 
            class="modal-input" 
            placeholder="예: 12가3456"
            @input="handleVehicleNumberInput"
            maxlength="8"
          />
        </div>
        <div class="modal-footer">
          <button class="modal-complete-button" @click="addVehicle">
            <span class="button-text">설정 완료</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { BACKEND_BASE_URL } from '@/utils/api'

const router = useRouter()
const showModal = ref(false)
const selectedSkill = ref('advanced')
const vehicleNumber = ref('')

const formData = reactive({
  vehicleNumber: '',
  parkingSkill: 'advanced'
})

// 차량번호 입력 시 숫자와 한글만 허용
const handleVehicleNumberInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  const value = target.value
  // 숫자와 한글만 허용 (공백, 특수문자 제거)
  const cleanValue = value.replace(/[^0-9ㄱ-ㅎㅏ-ㅣ가-힣]/g, '')
  // 최대 8자로 제한
  if (cleanValue.length > 8) {
    vehicleNumber.value = cleanValue.substring(0, 8)
  } else {
    vehicleNumber.value = cleanValue
  }
}

const addVehicle = async () => {
  if (vehicleNumber.value.trim()) {
    try {
      // 토큰 가져오기 (localStorage 또는 sessionStorage에서)
      const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
      
      if (!token) {
        alert('로그인이 필요합니다.')
        router.push('/login')
        return
      }

      const response = await fetch(`${BACKEND_BASE_URL}/user/vehicle/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          license_plate: vehicleNumber.value.trim()
        })
      })

      if (response.ok) {
        formData.vehicleNumber = vehicleNumber.value.trim()
        console.log('차량 번호 저장 성공:', vehicleNumber.value)
        alert('차량 번호가 성공적으로 등록되었습니다!')
        showModal.value = false
        vehicleNumber.value = ''
      } else {
        // 응답이 JSON인지 확인
        const contentType = response.headers.get('content-type')
        if (contentType && contentType.includes('application/json')) {
          const errorData = await response.json()
          alert('차량 번호 저장 실패: ' + (errorData.detail || errorData.message || '서버 오류'))
        } else {
          // HTML 응답인 경우 (보통 404, 401 등의 에러)
          console.error('API 응답이 HTML입니다. 상태 코드:', response.status)
          if (response.status === 404) {
            alert('API 엔드포인트를 찾을 수 없습니다. 서버 설정을 확인해주세요.')
          } else if (response.status === 401) {
            alert('인증이 만료되었습니다. 다시 로그인해주세요.')
            router.push('/login')
          } else {
            alert('차량 번호 저장에 실패했습니다. (오류 코드: ' + response.status + ')')
          }
        }
      }
    } catch (error) {
      console.error('차량 번호 저장 중 오류:', error)
      alert('차량 번호 저장 중 오류가 발생했습니다.')
    }
  }
}

const completeSetup = async () => {
  formData.parkingSkill = selectedSkill.value
  
  // 차량이 등록되지 않은 경우 경고
  if (!formData.vehicleNumber) {
    alert('차량 번호를 먼저 등록해주세요.')
    return
  }
  
  try {
    // 토큰 가져오기
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
    
    if (!token) {
      alert('로그인이 필요합니다.')
      router.push('/login')
      return
    }

    // 주차 실력별 점수 매핑
    const scoreMap: Record<string, number> = {
      'beginner': 30,    // 초급자
      'intermediate': 65, // 중급자
      'advanced': 86      // 상급자
    }

    const userScore = scoreMap[selectedSkill.value] || 30

    // 주차실력과 점수 업데이트 API 호출
    const response = await fetch(`${BACKEND_BASE_URL}/user/parking-skill/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        parking_skill: selectedSkill.value,
        score: userScore
      })
    })

    if (response.ok) {
      console.log('주차실력 저장 성공:', selectedSkill.value, '점수:', userScore)
      alert(`차량 정보 설정이 완료되었습니다! (주차 점수: ${userScore}점)`)
      router.push('/main')
    } else {
      // 응답이 JSON인지 확인
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        const errorData = await response.json()
        alert('주차실력 저장 실패: ' + (errorData.detail || errorData.message || '서버 오류'))
      } else {
        // HTML 응답인 경우 (보통 404, 401 등의 에러)
        console.error('API 응답이 HTML입니다. 상태 코드:', response.status)
        if (response.status === 404) {
          alert('API 엔드포인트를 찾을 수 없습니다. 서버 설정을 확인해주세요.')
        } else if (response.status === 401) {
          alert('인증이 만료되었습니다. 다시 로그인해주세요.')
          router.push('/login')
        } else {
          alert('주차실력 저장에 실패했습니다. (오류 코드: ' + response.status + ')')
        }
      }
    }
  } catch (error) {
    console.error('주차실력 저장 중 오류:', error)
    alert('주차실력 저장 중 오류가 발생했습니다.')
  }
}

// 컴포넌트 마운트 시 로그인 상태 확인
onMounted(async () => {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
  if (!token) {
    alert('로그인이 필요합니다.')
    router.push('/login')
    return
  }
  
  // 이미 차량 정보가 등록되어 있는 유저는 메인 페이지로 리다이렉트
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/user/me/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (response.ok) {
      const userData = await response.json()
      // 차량 정보가 이미 있으면 메인으로 리다이렉트
      if (userData.vehicles && userData.vehicles.length > 0) {
        router.push('/main')
      }
    }
  } catch (error) {
    console.error('유저 정보 확인 중 오류:', error)
  }
})
</script>

<style scoped>
.social-login-info-container {
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
  height: 100%;
  padding-top: 60px;
}

/* Title Section */
.title-section {
  position: absolute;
  left: 26px;
  top: 32px;
  margin-top: 60px;
}

.page-title {
  color: black;
  font-size: 24px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  line-height: 22px;
  margin: 0;
}

/* Vehicle Info Section */
.vehicle-info-section {
  position: absolute;
  width: 440px;
  height: 171px;
  left: 1px;
  top: 136px;
  background: white;
  overflow: hidden;
}

.vehicle-info-card {
  width: 100%;
  height: 100%;
  position: relative;
}

.vehicle-info-content {
  position: relative;
  width: 100%;
  height: 100%;
}

.vehicle-info-text {
  position: absolute;
  left: 42px;
  top: 43px;
  width: 157px;
  height: 71px;
}

.vehicle-title {
  color: #464038;
  font-size: 24px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  line-height: 32px;
  margin: 0;
}

.vehicle-description {
  width: 100%;
  color: #A0907F;
  font-size: 14px;
  font-family: 'Inter', sans-serif;
  font-weight: 100;
  line-height: 18px;
  margin: 8px 0 0 0;
  white-space: nowrap;
}

.vehicle-image {
  position: absolute;
  width: 184px;
  height: 68px;
  left: 232px;
  top: 37px;
  cursor: pointer;
}

.car-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.add-vehicle-button {
  position: absolute;
  width: 38px;
  height: 38px;
  left: 305px;
  top: 56px;
  background: rgba(255, 255, 255, 0);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plus-button-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Parking Skill Section */
.parking-skill-section {
  position: absolute;
  left: 26px;
  right: 26px;
  top: 349px;
  width: calc(100% - 52px);
}

.skill-title {
  color: #333333;
  font-size: 24px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  line-height: 29px;
  margin-bottom: 20px;
}

.skill-selection {
  width: 100%;
  height: 150px;
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 1px solid #f3eeea;
  border-radius: 8px;
  overflow: hidden;
}

.skill-button {
  width: 100%;
  height: 50px;
  border: none;
  background-color: #ebe3d5;
  color: #4d4d4d;
  font-size: 16px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  padding: 0 15px;
}

.skill-button.selected {
  background-color: #776b5d;
  color: #f5f5f5;
}

.skill-button:hover {
  background-color: #d4c8b8;
}

.skill-button.selected:hover {
  background-color: #665a4d;
}

/* Complete Button */
.complete-button-container {
  position: absolute;
  width: 344px;
  height: 50px;
  left: 48px;
  top: 625px;
}

.complete-button {
  width: 100%;
  height: 100%;
  background: #776B5D;
  border: none;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.complete-button:hover {
  background: #665a4d;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}

.button-text {
  color: white;
  font-size: 16px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  line-height: 19px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 375px;
  height: 200px;
  background-color: #f3eeea;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-header {
  text-align: center;
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: #4d4d4d;
  margin: 0;
  line-height: 22px;
}

.modal-body {
  flex: 1;
  display: flex;
  align-items: center;
}

.modal-input {
  width: 100%;
  height: 50px;
  background-color: #ffffff;
  border: 1px solid #cccccc;
  border-radius: 8px;
  padding: 0 15px;
  font-size: 16px;
  font-weight: 400;
  color: #333333;
  outline: none;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}

.modal-input::placeholder {
  color: #999999;
}

.modal-input:focus {
  border-color: #776b5d;
}

.modal-footer {
  display: flex;
  justify-content: center;
}

.modal-complete-button {
  width: 280px;
  height: 50px;
  background-color: #776b5d;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-complete-button:hover {
  background-color: #665a4d;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(119, 107, 93, 0.3);
}


/* Responsive Design */
@media (max-width: 440px) {
  .social-login-info-container {
    width: 100vw;
    height: 100vh;
  }
  
  .vehicle-info-section {
    width: 100%;
  }
  
  .parking-skill-section {
    left: 26px;
    right: 26px;
    width: calc(100% - 52px);
  }
  
  .skill-selection {
    width: 100%;
  }
  
  .complete-button-container {
    width: calc(100% - 96px);
    left: 48px;
  }
}

@media (min-width: 441px) {
  .social-login-info-container {
    width: 440px;
    margin: 0 auto;
  }
}
</style> 