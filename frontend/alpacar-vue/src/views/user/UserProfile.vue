<template>
  <div class="user-profile-container">
    <!-- Header Component -->
    <Header />

    <!-- Main Content -->
    <div class="main-content">
      <!-- Title and Logout Section -->
      <div class="title-logout-section">
        <h1 class="page-title">내 정보 확인하기</h1>
        <div class="logout-link" @click="handleLogout">로그아웃</div>
      </div>

      <!-- User Info Display -->
      <div class="view">
        <div class="text-wrapper-3">이름</div>
        <div class="text-wrapper-4">example@email.com</div>
      </div>

    <!-- Nickname Section -->
    <div class="text-wrapper-9">닉네임</div>
    <div class="view-5">
      <div class="text-wrapper-7">{{ userInfo.name }}</div>
      <div class="text-wrapper-8" @click="showNicknameModal = true">수정</div>
    </div>

    <!-- Password Section -->
    <div class="text-wrapper-14">비밀번호 변경</div>
    <div class="text-wrapper-15">현재 비밀번호 입력</div>
    <div class="view-6"></div>
    
    <div class="text-wrapper-16">새 비밀번호 입력</div>
    <div class="view-8"></div>
    
    <div class="text-wrapper-17">새 비밀번호 확인</div>
    <div class="view-9"></div>
    
    <!-- Change Password Button -->
    <div class="view-3" @click="showPasswordConfirmModal = true">
      <div class="view-2">변경하기</div>
    </div>

    <!-- Vehicle Section -->
    <div class="text-wrapper-13">내 차량정보</div>
    <div class="component-147-instance" @click="showVehicleModal = true">
      <div class="view-2">내 차 추가</div>
    </div>
    
    <!-- Vehicle List -->
    <div class="vehicle-list-container">
      <div 
        v-for="(vehicle, index) in displayedVehicles" 
        :key="vehicle.id"
        class="vehicle-card"
      >
        <div class="text-wrapper-10">
          {{ vehicle.number }}<br />
          {{ vehicle.name }}
        </div>
        <div class="text-wrapper-11" @click="editVehicle(vehicle)">수정</div>
        <div class="text-wrapper-12" @click="deleteVehicle(vehicle)">삭제</div>
      </div>
      
      <!-- More Button -->
      <div 
        v-if="vehicles.length > 3 && !showAllVehicles" 
        class="more-button"
        @click="showAllVehicles = true"
      >
        <div class="view-2">더보기 ({{ vehicles.length - 3 }})</div>
      </div>
      
      <!-- Show Less Button -->
      <div 
        v-if="vehicles.length > 3 && showAllVehicles" 
        class="more-button"
        @click="showAllVehicles = false"
      >
        <div class="view-2">접기</div>
      </div>
    </div>

    </div>

    <!-- Bottom Navigation -->
    <BottomNavigation />

    <!-- Nickname Edit Modal -->
    <div v-if="showNicknameModal" class="modal-overlay" @click="showNicknameModal = false">
      <div class="figma-modal nickname-modal" @click.stop>
        <h3 class="modal-title">수정할 닉네임을 입력하세요</h3>
        <div class="figma-input-field">
          <input 
            v-model="newNickname" 
            type="text" 
            placeholder="예: 주차하는 알파카"
            class="figma-input"
          />
        </div>
        <button class="figma-btn" @click="updateNickname">설정 완료</button>
      </div>
    </div>

    <!-- Password Change Confirmation Modal -->
    <div v-if="showPasswordConfirmModal" class="modal-overlay" @click="showPasswordConfirmModal = false">
      <div class="figma-modal password-confirm-modal" @click.stop>
        <h3 class="modal-title">비밀번호를 변경하시겠습니까?</h3>
        <div class="modal-buttons">
          <button class="figma-btn-left" @click="confirmPasswordChange">예</button>
          <button class="figma-btn-right" @click="showPasswordConfirmModal = false">아니오</button>
        </div>
      </div>
    </div>

    <!-- Vehicle Add/Edit Modal -->
    <div v-if="showVehicleModal" class="modal-overlay" @click="showVehicleModal = false">
      <div class="figma-modal vehicle-modal" @click.stop>
        <h3 class="modal-title">차량 번호를 입력해주세요</h3>
        <div class="figma-input-field">
          <input 
            v-model="vehicleForm.number" 
            type="text" 
            placeholder="예: 12가 3456"
            class="figma-input"
          />
        </div>
        <button class="figma-btn" @click="saveVehicle">설정 완료</button>
      </div>
    </div>

    <!-- Delete Vehicle Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
      <div class="figma-modal delete-modal" @click.stop>
        <h3 class="modal-title">삭제하시겠습니까?</h3>
        <div class="modal-buttons">
          <button class="figma-btn-left" @click="confirmDeleteVehicle">예</button>
          <button class="figma-btn-right" @click="showDeleteModal = false">아니오</button>
        </div>
      </div>
    </div>

    <!-- Single Vehicle Warning Modal -->
    <div v-if="showSingleVehicleWarning" class="modal-overlay" @click="showSingleVehicleWarning = false">
      <div class="figma-modal warning-modal" @click.stop>
        <h3 class="modal-title">차량이 1대밖에 없어 삭제할 수 없습니다.</h3>
        <button class="figma-btn" @click="showSingleVehicleWarning = false">확인</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Header from '@/components/Header.vue'
import BottomNavigation from '@/components/BottomNavigation.vue'
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// User Info
const userInfo = reactive({
  name: 'User',
  phoneNumber: '111 가 1111'
})

// Vehicles
const vehicles = ref([
  {
    id: 1,
    name: 'K5',
    number: '12가 3456',
    image: '@/assets/k5.avif'
  },
  {
    id: 2,
    name: 'EV6',
    number: '34나 5678',
    image: '@/assets/ev6.avif'
  },
  {
    id: 3,
    name: '스포티지',
    number: '56다 7890',
    image: '@/assets/sportage.avif'
  },
  {
    id: 4,
    name: '카니벌',
    number: '78라 1234',
    image: '@/assets/carnival.avif'
  },
  {
    id: 5,
    name: '모닝',
    number: '90마 5678',
    image: '@/assets/morning.avif'
  }
])

// Computed property for displayed vehicles
const displayedVehicles = computed(() => {
  if (vehicles.value.length <= 3) {
    return vehicles.value
  }
  return showAllVehicles.value ? vehicles.value : vehicles.value.slice(0, 3)
})

// Computed property for content wrapper height
const contentWrapperHeight = computed(() => {
  const baseHeight = 770 // Base content height
  const vehicleHeight = 95 // Height per vehicle card
  const displayCount = displayedVehicles.value.length
  const extraHeight = vehicleHeight * Math.max(0, displayCount - 1)
  const buttonHeight = vehicles.value.length > 3 ? 50 : 0 // More/Less button height
  
  return Math.max(baseHeight + extraHeight + buttonHeight, window.innerHeight - 160)
})

// Modal States
const showNicknameModal = ref(false)
const showPasswordConfirmModal = ref(false)
const showVehicleModal = ref(false)
const showDeleteModal = ref(false)
const showSingleVehicleWarning = ref(false)
const showAllVehicles = ref(false)

// Form Data
const newNickname = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const vehicleForm = reactive({
  name: '',
  number: '',
  image: '@/assets/k5.avif'
})
const editingVehicle = ref(null)
const vehicleToDelete = ref(null)

// Methods
const handleLogout = () => {
  // 세션 만료 처리
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  sessionStorage.clear()
  
  // 로그인 페이지로 이동
  router.push('/login')
}

const updateNickname = () => {
  if (newNickname.value.trim()) {
    userInfo.name = newNickname.value.trim()
    showNicknameModal.value = false
    newNickname.value = ''
    alert('닉네임이 변경되었습니다.')
  } else {
    alert('닉네임을 입력해주세요.')
  }
}

const confirmPasswordChange = () => {
  if (currentPassword.value && newPassword.value && confirmPassword.value) {
    if (newPassword.value === confirmPassword.value) {
      // 비밀번호 변경 로직
      console.log('비밀번호 변경:', { current: currentPassword.value, new: newPassword.value })
      showPasswordConfirmModal.value = false
      currentPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
      alert('비밀번호가 변경되었습니다.')
    } else {
      alert('새 비밀번호가 일치하지 않습니다.')
      showPasswordConfirmModal.value = false
    }
  } else {
    alert('모든 비밀번호 필드를 입력해주세요.')
    showPasswordConfirmModal.value = false
  }
}

const editVehicle = (vehicle) => {
  if (vehicle) {
    editingVehicle.value = vehicle
    vehicleForm.name = vehicle.name
    vehicleForm.number = vehicle.number
    vehicleForm.image = vehicle.image
    showVehicleModal.value = true
  }
}

const saveVehicle = () => {
  if (vehicleForm.number.trim()) {
    if (editingVehicle.value) {
      // 기존 차량 수정
      const index = vehicles.value.findIndex(v => v.id === editingVehicle.value.id)
      if (index !== -1) {
        vehicles.value[index] = {
          ...editingVehicle.value,
          number: vehicleForm.number,
        }
      }
      alert('차량 정보가 수정되었습니다.')
    } else {
      // 새 차량 추가
      const newVehicle = {
        id: Date.now(),
        name: '기아 모닝', // 기본값
        number: vehicleForm.number,
        image: '@/assets/morning.avif' // 기본값
      }
      vehicles.value.push(newVehicle)
      alert('새 차량이 추가되었습니다.')
    }
    
    showVehicleModal.value = false
    editingVehicle.value = null
    vehicleForm.name = ''
    vehicleForm.number = ''
    vehicleForm.image = '@/assets/k5.avif'
  } else {
    alert('차량번호를 입력해주세요.')
  }
}

const deleteVehicle = (vehicle) => {
  if (!vehicle) return
  
  if (vehicles.value.length <= 1) {
    showSingleVehicleWarning.value = true
    return
  }
  
  vehicleToDelete.value = vehicle
  showDeleteModal.value = true
}

const confirmDeleteVehicle = () => {
  if (vehicleToDelete.value) {
    const index = vehicles.value.findIndex(v => v.id === vehicleToDelete.value.id)
    if (index !== -1) {
      vehicles.value.splice(index, 1)
      alert('차량이 삭제되었습니다.')
    }
    showDeleteModal.value = false
    vehicleToDelete.value = null
  }
}
</script>

<style scoped>
.user-profile-container {
  width: 440px;
  height: 956px;
  position: relative;
  background: #F3EDEA;
  overflow: hidden;
  margin: 0 auto;
}

.main-content {
  position: relative;
  padding-top: 80px;
  height: calc(100% - 160px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-left: 20px;
  padding-right: 20px;
  display: flex;
  flex-direction: column;
  width: 100%;
  box-sizing: border-box;
}

/* Title and Logout Section */
.title-logout-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
  margin-top: 20px;
  margin-bottom: 20px;
  position: relative;
  z-index: 10;
}

.page-title {
  color: #000000;
  font-family: "Inter-Bold", Helvetica;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0;
  line-height: 22px;
  margin: 0;
  white-space: nowrap;
}

.logout-link {
  color: #000000;
  font-family: "Inter-Regular", Helvetica;
  font-size: 16px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: 22px;
  cursor: pointer;
  padding: 0;
  white-space: nowrap;
}

.logout-link:hover {
  color: #776b5d;
}


/* Template-based styles */
.view {
  align-items: flex-start;
  background-color: #ebe3d5;
  border: 0px none;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
  padding: 10px;
  position: relative;
  width: 100%;
  margin-bottom: 20px;
}

.text-wrapper-3 {
  color: #000000;
  font-family: "Inter-Regular", Helvetica;
  font-size: 16px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  white-space: nowrap;
  width: fit-content;
}

.text-wrapper-4 {
  color: #776b5d;
  font-family: "Inter-Regular", Helvetica;
  font-size: 16px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  white-space: nowrap;
  width: fit-content;
}

.component-147-instance {
  position: relative;
  background: #776b5d;
  border-radius: 5px;
  padding: 8px 16px;
  cursor: pointer;
  align-self: flex-end;
  margin-bottom: 20px;
}

.view-2 {
  color: #ffffff;
  font-family: "Inter-SemiBold", Helvetica;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.view-3 {
  position: relative;
  background: #776b5d;
  border-radius: 5px;
  padding: 8px 16px;
  cursor: pointer;
  align-self: flex-end;
  margin-bottom: 20px;
}

.overlap-group {
  height: 84px;
  left: 0;
  position: absolute;
  top: 872px;
  width: 440px;
}

.view-4 {
  background-color: #f0f0f0;
  height: 84px;
  left: 0;
  position: absolute;
  top: 0;
  width: 440px;
}

/* Remove old title and logout styles as they're now handled by new classes */

.view-5 {
  background-color: #ffffff;
  border: 1px solid;
  border-color: #cccccc;
  border-radius: 10px;
  height: 50px;
  overflow: hidden;
  position: relative;
  width: 100%;
  margin-bottom: 20px;
}

.text-wrapper-7 {
  color: #000000;
  font-family: "Inter-Regular", Helvetica;
  font-size: 16px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: normal;
  position: absolute;
  left: 14px;
  top: 15px;
  white-space: nowrap;
}

.text-wrapper-8 {
  color: #000000;
  font-family: "Inter-Regular", Helvetica;
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0;
  line-height: normal;
  position: absolute;
  right: 14px;
  top: 16px;
  cursor: pointer;
}

.view-6 {
  background-color: #ffffff;
  border: 1px solid;
  border-color: #cccccc;
  border-radius: 10px;
  height: 50px;
  position: relative;
  width: 100%;
  margin-bottom: 20px;
}

.text-wrapper-9 {
  color: #333333;
  font-family: "Inter-SemiBold", Helvetica;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  margin-bottom: 10px;
  white-space: nowrap;
}

/* Vehicle List Styles */
.vehicle-list-container {
  position: relative;
  width: 100%;
}

.vehicle-card {
  background-color: #ffffff;
  border: 1px solid;
  border-color: #cccccc;
  border-radius: 10px;
  height: 85px;
  overflow: hidden;
  position: relative;
  width: 100%;
  margin-bottom: 15px;
  transition: all 0.3s ease;
}

.more-button {
  background: #776b5d;
  border-radius: 5px;
  padding: 8px 16px;
  cursor: pointer;
  position: relative;
  align-self: flex-end;
  margin-bottom: 15px;
  transition: background 0.3s;
}

.more-button:hover {
  background: #6a5d50;
}

.text-wrapper-10 {
  color: #000000;
  font-family: "Inter-Regular", Helvetica;
  font-size: 16px;
  font-weight: 400;
  left: 14px;
  letter-spacing: 0;
  line-height: normal;
  position: absolute;
  top: 23px;
}

.text-wrapper-11 {
  color: #000000;
  font-family: "Inter-Regular", Helvetica;
  font-size: 12px;
  font-weight: 400;
  right: 70px;
  letter-spacing: 0;
  line-height: normal;
  position: absolute;
  top: 34px;
  cursor: pointer;
}

.text-wrapper-12 {
  color: #000000;
  font-family: "Inter-Regular", Helvetica;
  font-size: 12px;
  font-weight: 400;
  right: 32px;
  letter-spacing: 0;
  line-height: normal;
  position: absolute;
  top: 34px;
  cursor: pointer;
}

.text-wrapper-13 {
  color: #333333;
  font-family: "Inter-SemiBold", Helvetica;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  margin-bottom: 10px;
  white-space: nowrap;
}

.text-wrapper-14 {
  color: #333333;
  font-family: "Inter-SemiBold", Helvetica;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  margin-bottom: 10px;
  white-space: nowrap;
}

.text-wrapper-15 {
  color: #333333;
  font-family: "Inter-SemiBold", Helvetica;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  margin-bottom: 10px;
  white-space: nowrap;
}

.view-8 {
  background-color: #ffffff;
  border: 1px solid;
  border-color: #cccccc;
  border-radius: 10px;
  height: 50px;
  position: relative;
  width: 100%;
  margin-bottom: 20px;
}

.text-wrapper-16 {
  color: #333333;
  font-family: "Inter-SemiBold", Helvetica;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  margin-bottom: 10px;
  white-space: nowrap;
}

.view-9 {
  background-color: #ffffff;
  border: 1px solid;
  border-color: #cccccc;
  border-radius: 10px;
  height: 50px;
  position: relative;
  width: 100%;
  margin-bottom: 20px;
}

.text-wrapper-17 {
  color: #333333;
  font-family: "Inter-SemiBold", Helvetica;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: normal;
  position: relative;
  margin-bottom: 10px;
  white-space: nowrap;
}

.profile-section {
  margin-bottom: 30px;
}

.profile-header {
  text-align: center;
  margin-bottom: 20px;
}

.profile-title {
  color: white;
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  font-family: 'Inter', sans-serif;
}

.profile-card {
  background: white;
  border-radius: 20px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-container {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-details {
  flex: 1;
}

.user-name, .user-number {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 16px;
  font-family: 'Inter', sans-serif;
}

.label {
  color: #666;
  font-weight: 500;
  min-width: 40px;
}

.separator {
  color: #ccc;
}

.value {
  color: #333;
  font-weight: 600;
  flex: 1;
}

.edit-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.3s;
}

.edit-btn:hover {
  background: #5a6fd8;
}

.menu-items {
  margin-bottom: 30px;
}

.menu-item {
  background: white;
  border-radius: 15px;
  padding: 20px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.menu-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.menu-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.password-icon {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
}

.vehicle-icon {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
}

.menu-content {
  flex: 1;
}

.menu-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0 0 5px 0;
  font-family: 'Inter', sans-serif;
}

.menu-description {
  font-size: 14px;
  color: #666;
  margin: 0;
  font-family: 'Inter', sans-serif;
}

.vehicle-section {
  margin-bottom: 30px;
}

.section-title {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 15px;
  font-family: 'Inter', sans-serif;
}

.vehicle-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.vehicle-item {
  background: white;
  border-radius: 15px;
  padding: 15px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.vehicle-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.vehicle-image {
  width: 60px;
  height: 60px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
}

.vehicle-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.vehicle-details {
  flex: 1;
}

.vehicle-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 5px 0;
  font-family: 'Inter', sans-serif;
}

.vehicle-number {
  font-size: 14px;
  color: #666;
  margin: 0;
  font-family: 'Inter', sans-serif;
}

.vehicle-actions {
  display: flex;
  gap: 10px;
}

.edit-vehicle-btn, .delete-vehicle-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Inter', sans-serif;
}

.edit-vehicle-btn {
  background: #667eea;
  color: white;
}

.edit-vehicle-btn:hover {
  background: #5a6fd8;
}

.delete-vehicle-btn {
  background: #ff6b6b;
  color: white;
}

.delete-vehicle-btn:hover:not(:disabled) {
  background: #ee5a24;
}

.delete-vehicle-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.logout-section {
  margin-top: 30px;
}

.logout-btn {
  width: 100%;
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 15px;
  border-radius: 15px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
  font-family: 'Inter', sans-serif;
}

.logout-btn:hover {
  background: #ee5a24;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 20px;
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
  font-family: 'Inter', sans-serif;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  font-family: 'Inter', sans-serif;
}

.input-group input,
.input-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Inter', sans-serif;
  box-sizing: border-box;
}

.input-group input:focus,
.input-group select:focus {
  outline: none;
  border-color: #667eea;
}

.modal-footer {
  display: flex;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.cancel-btn, .confirm-btn, .delete-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  font-family: 'Inter', sans-serif;
}

.cancel-btn {
  background: #f5f5f5;
  color: #666;
}

.cancel-btn:hover {
  background: #e5e5e5;
}

.confirm-btn {
  background: #667eea;
  color: white;
}

.confirm-btn:hover {
  background: #5a6fd8;
}

.delete-btn {
  background: #ff6b6b;
  color: white;
}

.delete-btn:hover {
  background: #ee5a24;
}

/* Delete Modal Specific */
.delete-warning {
  text-align: center;
  padding: 20px 0;
}

.delete-warning svg {
  margin-bottom: 15px;
}

.delete-warning p {
  margin: 10px 0;
  font-size: 16px;
  color: #333;
  font-family: 'Inter', sans-serif;
}

.vehicle-info {
  font-weight: 600;
  color: #667eea;
}

/* Warning Modal Specific */
.warning-content {
  text-align: center;
  padding: 20px 0;
  animation: warningShake 0.5s ease-in-out;
}

@keyframes warningShake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.warning-content svg {
  margin-bottom: 15px;
}

.warning-content p {
  margin: 10px 0;
  font-size: 16px;
  color: #333;
  font-family: 'Inter', sans-serif;
}

/* Figma Modal Styles */
.figma-modal {
  background: #f3eeea;
  width: 320px;
  padding: 27px 48px 124px 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  border-radius: 0;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.modal-title {
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
  font-size: 18px;
  font-weight: 600;
  color: #4d4d4d;
  text-align: center;
  margin: 0 0 47px 0;
  line-height: normal;
  white-space: nowrap;
  width: auto;
  max-width: 100%;
}

.figma-input-field {
  width: 280px;
  background: #ffffff;
  border: 1px solid #cccccc;
  margin-bottom: 50px;
  display: flex;
  align-items: center;
  padding: 10px 15px;
}

.figma-input {
  width: 100%;
  border: none;
  outline: none;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
  font-size: 16px;
  color: #999999;
  background: transparent;
  padding: 0;
}

.figma-input::placeholder {
  color: #999999;
}

.figma-btn {
  width: 280px;
  height: 50px;
  background: #776b5d;
  color: #ffffff;
  border: none;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  margin: 0;
}

.figma-btn:hover {
  background: #6a5d50;
}

.modal-buttons {
  display: flex;
  gap: 56px;
  margin-top: 62px;
}

.figma-btn-left, .figma-btn-right {
  width: 100px;
  height: 50px;
  background: #776b5d;
  color: #ffffff;
  border: none;
  font-family: 'Inter', 'Noto Sans KR', sans-serif;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
}

.figma-btn-left:hover, .figma-btn-right:hover {
  background: #6a5d50;
}

/* Modal specific adjustments */
.nickname-modal .modal-title {
  width: auto;
}

.password-confirm-modal .modal-title {
  width: auto;
}

.vehicle-modal .modal-title {
  width: auto;
}

.delete-modal .modal-title {
  width: auto;
}

.warning-modal {
  padding: 27px 48px 50px 48px;
}

.warning-modal .modal-title {
  width: auto;
  margin-bottom: 24px;
  white-space: nowrap;
}

.warning-modal .figma-btn {
  margin-top: 0;
}

/* Responsive Design */
@media (max-width: 440px) {
  .user-profile-container {
    width: 100vw;
    height: 100vh;
  }
  
  .main-content {
    padding-left: 15px;
    padding-right: 15px;
  }

  .figma-modal {
    width: 90%;
    max-width: 320px;
    padding: 27px 24px 50px 24px;
  }

  .figma-input-field, .figma-btn {
    width: 100%;
  }

  .modal-buttons {
    gap: 20px;
  }
}

@media (min-width: 441px) {
  .user-profile-container {
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