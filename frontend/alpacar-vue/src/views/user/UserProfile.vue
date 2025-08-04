<template>
  <div class="user-profile">
    <!-- Header Component -->
    <Header />

    <!-- Main Content -->
    <div class="user-profile__content">
      <!-- Title and Logout Section -->
      <div class="user-profile__header">
        <h1 class="user-profile__title">내 정보 확인하기</h1>
        <div class="user-profile__logout" @click="handleLogout">로그아웃</div>
      </div>

      <!-- User Info Display -->
      <div class="user-info">
        <div class="user-info__label">이름</div>
        <div class="user-info__value">example@email.com</div>
      </div>

      <!-- Nickname Section -->
      <div class="section-title">닉네임</div>
      <div class="input-field">
        <div class="input-field__value">{{ userInfo.name }}</div>
        <div class="input-field__edit" @click="showNicknameModal = true">수정</div>
      </div>

      <!-- Password Section -->
      <div class="section-title">비밀번호 변경</div>
      <div class="section-subtitle">현재 비밀번호 입력</div>
      <div class="input-field input-field--password">
        <input
          v-model="currentPassword"
          type="password"
          placeholder="현재 비밀번호를 입력하세요"
          class="input-field__input"
        />
      </div>

      <div class="section-subtitle">새 비밀번호 입력</div>
      <div class="input-field input-field--password">
        <input
          v-model="newPassword"
          type="password"
          placeholder="새 비밀번호를 입력하세요"
          class="input-field__input"
        />
      </div>

      <div class="section-subtitle">새 비밀번호 확인</div>
      <div class="input-field input-field--password">
        <input
          v-model="confirmPassword"
          type="password"
          placeholder="새 비밀번호를 다시 입력하세요"
          class="input-field__input"
        />
      </div>

      <!-- Change Password Button -->
      <div class="button-container">
        <div class="button button--primary" @click="showPasswordConfirmModal = true">
          <div class="button__text">변경하기</div>
        </div>
      </div>

      <!-- Vehicle Section -->
      <div class="section-title">내 차량정보</div>
      <div class="button-container">
        <div class="button button--secondary" @click="showVehicleModal = true">
          <div class="button__text">내 차 추가</div>
        </div>
      </div>

      <!-- Vehicle List -->
      <div class="vehicle-list">
        <div
          v-for="(vehicle, index) in displayedVehicles"
          :key="vehicle.id"
          class="vehicle-card"
        >
          <div class="vehicle-card__info">
            {{ vehicle.number }}<br />
            {{ vehicle.name }}
          </div>
          <div class="vehicle-card__actions">
            <div class="vehicle-card__edit" @click="editVehicle(vehicle)">수정</div>
            <div class="vehicle-card__delete" @click="deleteVehicle(vehicle)">삭제</div>
          </div>
        </div>

        <!-- More/Less Button -->
        <div class="button-container">
          <div
            v-if="vehicles.length > 3 && !showAllVehicles"
            class="button button--more"
            @click="showAllVehicles = true"
          >
            <div class="button__text">더보기 ({{ vehicles.length - 3 }})</div>
          </div>
          <div
            v-if="vehicles.length > 3 && showAllVehicles"
            class="button button--more"
            @click="showAllVehicles = false"
          >
            <div class="button__text">접기</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Navigation -->
    <BottomNavigation />

    <!-- Nickname Edit Modal -->
    <div v-if="showNicknameModal" class="modal-overlay" @click="showNicknameModal = false">
      
      <div class="modal modal--nickname" @click.stop>
        <h3 class="modal__title">수정할 닉네임을 입력하세요</h3>
        <div class="modal__input-field">
          <input
            v-model="newNickname"
            type="text"
            placeholder="예: 주차하는 알파카"
            class="modal__input"
          />
        </div>
        <button class="modal__button" @click="updateNickname">설정 완료</button>
      </div>
    </div>

    <!-- Password Change Confirmation Modal -->
    <div
      v-if="showPasswordConfirmModal"
      class="modal-overlay"
      @click="showPasswordConfirmModal = false"
    >
      <div class="modal modal--password-confirm" @click.stop>
        <h3 class="modal__title">비밀번호를 변경하시겠습니까?</h3>
        <div class="modal__buttons">
          <button class="modal__button modal__button--left" @click="confirmPasswordChange">
            예
          </button>
          <button
            class="modal__button modal__button--right"
            @click="showPasswordConfirmModal = false"
          >
            아니오
          </button>
        </div>
      </div>
    </div>

    <!-- Vehicle Add/Edit Modal -->
    <div v-if="showVehicleModal" class="modal-overlay" @click="showVehicleModal = false">
      <div class="modal modal--vehicle" @click.stop>
        <h3 class="modal__title">차량 번호를 입력해주세요</h3>
        <div class="modal__input-field">
          <input
            v-model="vehicleForm.number"
            type="text"
            placeholder="예: 12가3456"
            class="modal__input"
          />
        </div>
        <button class="modal__button" @click="saveVehicle">설정 완료</button>
      </div>
    </div>

    <!-- Delete Vehicle Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="showDeleteModal = false">
      <div class="modal modal--delete" @click.stop>
        <h3 class="modal__title">삭제하시겠습니까?</h3>
        <div class="modal__buttons">
          <button class="modal__button modal__button--left" @click="confirmDeleteVehicle">
            예
          </button>
          <button class="modal__button modal__button--right" @click="showDeleteModal = false">
            아니오
          </button>
        </div>
      </div>
    </div>

    <!-- Single Vehicle Warning Modal -->
    <div
      v-if="showSingleVehicleWarning"
      class="modal-overlay"
      @click="showSingleVehicleWarning = false"
    >
      <div class="modal modal--warning" @click.stop>
        <h3 class="modal__title">차량이 1대밖에 없어 삭제할 수 없습니다.</h3>
        <button class="modal__button" @click="showSingleVehicleWarning = false">확인</button>
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

// Types
interface Vehicle {
  id: number
  name: string
  number: string
  image: string
}

// User Info
const userInfo = reactive({
  name: 'User',
  phoneNumber: '010-1234-5678'
})

// Vehicles
const vehicles = ref<Vehicle[]>([
  { id: 1, name: 'K5', number: '12가3456', image: '@/assets/k5.avif' },
  { id: 2, name: 'EV6', number: '34나5678', image: '@/assets/ev6.avif' },
  { id: 3, name: '스포티지', number: '56다7890', image: '@/assets/sportage.avif' },
  { id: 4, name: '카니발', number: '78라1234', image: '@/assets/carnival.avif' },
  { id: 5, name: '모닝', number: '90마5678', image: '@/assets/morning.avif' }
])

const showAllVehicles = ref(false)
const displayedVehicles = computed(() =>
  vehicles.value.length <= 3 ? vehicles.value : showAllVehicles.value ? vehicles.value : vehicles.value.slice(0, 3)
)

// Modal States & Form Data
const showNicknameModal = ref(false)
const showPasswordConfirmModal = ref(false)
const showVehicleModal = ref(false)
const showDeleteModal = ref(false)
const showSingleVehicleWarning = ref(false)

const newNickname = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const vehicleForm = reactive({ name: '', number: '', image: '@/assets/k5.avif' })
const editingVehicle = ref<Vehicle | null>(null)
const vehicleToDelete = ref<Vehicle | null>(null)

// Methods
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  sessionStorage.clear()
  router.push('/login')
}

const updateNickname = () => {
  if (newNickname.value.trim()) {
    userInfo.name = newNickname.value.trim()
    showNicknameModal.value = false
    newNickname.value = ''
    alert('닉네임이 변경되었습니다.')
  } else alert('닉네임을 입력해주세요.')
}

const confirmPasswordChange = () => {
  if (currentPassword.value && newPassword.value && confirmPassword.value) {
    if (newPassword.value === confirmPassword.value) {
      console.log('비밀번호 변경:', { current: currentPassword.value, new: newPassword.value })
      alert('비밀번호가 변경되었습니다.')
    } else alert('새 비밀번호가 일치하지 않습니다.')
  } else alert('모든 비밀번호 필드를 입력해주세요.')
  showPasswordConfirmModal.value = false
  currentPassword.value = ''
  newPassword.value = ''
  confirmPassword.value = ''
}

const editVehicle = (vehicle: Vehicle) => {
  editingVehicle.value = vehicle
  vehicleForm.name = vehicle.name
  vehicleForm.number = vehicle.number
  vehicleForm.image = vehicle.image
  showVehicleModal.value = true
}

const saveVehicle = () => {
  if (!vehicleForm.number.trim()) return alert('차량번호를 입력해주세요.')
  if (editingVehicle.value) {
    const idx = vehicles.value.findIndex(v => v.id === editingVehicle.value!.id)
    if (idx !== -1) vehicles.value[idx].number = vehicleForm.number
    alert('차량 정보가 수정되었습니다.')
  } else {
    vehicles.value.push({
      id: Date.now(),
      name: '기아 모닝',
      number: vehicleForm.number,
      image: '@/assets/morning.avif'
    })
    alert('새 차량이 추가되었습니다.')
  }
  showVehicleModal.value = false
  editingVehicle.value = null
  vehicleForm.number = ''
}

const deleteVehicle = (vehicle: Vehicle) => {
  if (vehicles.value.length <= 1) return (showSingleVehicleWarning.value = true)
  vehicleToDelete.value = vehicle
  showDeleteModal.value = true
}

const confirmDeleteVehicle = () => {
  if (!vehicleToDelete.value) return
  const idx = vehicles.value.findIndex(v => v.id === vehicleToDelete.value!.id)
  if (idx !== -1) vehicles.value.splice(idx, 1)
  alert('차량이 삭제되었습니다.')
  showDeleteModal.value = false
  vehicleToDelete.value = null
}
</script>

<style scoped>
/* ── 전체 레이아웃 ── */
.user-profile {
  width: 440px;
  height: 956px;
  position: relative;
  background: #F3EDEA;
  overflow: hidden;
  margin: 0 auto;
}
.user-profile__content {
  position: relative;
  padding-top: 80px;
  height: calc(100% - 160px);
  overflow-y: auto;
  padding-left: 20px;
  padding-right: 20px;
}

/* Header */
.user-profile__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.user-profile__title {
  font-size: 24px; font-weight: 700;
}
.user-profile__logout {
  font-size: 16px; cursor: pointer;
}

/* User Info */
.user-info {
  background: #ebe3d5;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 20px;
}
.user-info__label { font-size: 16px; margin-bottom: 4px; }
.user-info__value { font-size: 16px; }

/* Section Titles */
.section-title { font-size: 20px; font-weight: 600; margin-bottom: 10px; }
.section-subtitle { font-size: 16px; font-weight: 600; margin: 0 0 10px; }

/* ── Input Field ── */
.input-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 0 14px;
  margin-bottom: 20px;
}
.input-field__value {
  font-size: 16px;
  white-space: normal;
}
.input-field__edit {
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}
.input-field__input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 16px;
}

/* ── Buttons ── */
.button {
  background: #776b5d;
  border-radius: 5px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  align-self: flex-end;
}
.button--primary,
.button--secondary { width: auto; height: 31px; padding: 0 12px; }
.button--more { padding: 8px 12px; align-self: flex-end; }
.button__text { color: #fff; font-weight: 700; font-size: 13px; }
.button-container {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

/* ── Vehicle Card ── */
.vehicle-list { margin-top: 10px; }
.vehicle-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 75px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 0 14px;
  margin-bottom: 15px;
}
.vehicle-card__info {
  font-size: 14px;
  white-space: normal;
}
.vehicle-card__actions {
  display: flex;
  gap: 12px;
}
.vehicle-card__edit,
.vehicle-card__delete {
  font-size: 11px;
  cursor: pointer;
}

/* ── Modal 공통 ── */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  background: #f3eeea;
  width: 90%;
  max-width: 320px;
  padding: 27px 24px 50px;
  border-radius: 0;
}
.modal__title { font-size: 18px; font-weight: 600; text-align: center; margin-bottom: 30px; }
.modal__input-field { 
  width: 100%; 
  background: #fff; 
  border: 1px solid #ccc; 
  margin-bottom: 30px; 
  padding: 10px 15px; 
  box-sizing: border-box;
}
.modal__input { width: 100%; border: none; outline: none; font-size: 16px; padding: 0; box-sizing: border-box; }
.modal__button {
  width: 100%; height: 50px; background: #776b5d; color: #fff;
  border: none; font-size: 16px; font-weight: 600; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.modal__buttons { display: flex; justify-content: space-between; gap: 20px; }
.modal__button--left,
.modal__button--right { width: 48%; }

/* ── Responsive (데스크톱 vs 모바일) ── */
@media (max-width: 440px) {
  .user-profile {
    width: 100vw;
    height: 100vh;
  }
  
  .user-profile__content {
    padding-left: 15px;
    padding-right: 15px;
  }
}

@media (min-width: 441px) {
  .user-profile {
    width: 440px;
    height: auto;
    min-height: 100vh;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
  }
  
  .user-profile__content {
    flex: 1;
    height: auto;
    min-height: calc(100vh - 160px);
    padding-bottom: 20px;
  }
}
</style>
