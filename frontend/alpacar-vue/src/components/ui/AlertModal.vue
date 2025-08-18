<template>
  <Teleport to="body">
    <Transition name="alert-backdrop" appear>
      <div 
        v-if="visible" 
        class="alert-backdrop"
        @click="handleBackdropClick"
      >
        <Transition name="alert-modal" appear>
          <div 
            v-if="visible"
            class="alert-modal"
            :class="typeClass"
            @click.stop
          >
            <!-- Alert Icon -->
            <div class="alert-icon">
              <component :is="iconComponent" />
            </div>
            
            <!-- Alert Content -->
            <div class="alert-content">
              <h3 class="alert-title" v-if="title">{{ title }}</h3>
              <p class="alert-message">{{ message }}</p>
            </div>
            
            <!-- Alert Actions -->
            <div class="alert-actions">
              <button 
                v-if="type === 'confirm'"
                class="alert-button secondary"
                @click="handleCancel"
              >
                {{ cancelText }}
              </button>
              <button 
                class="alert-button primary"
                @click="handleConfirm"
                :class="{ 'full-width': type !== 'confirm' }"
              >
                {{ confirmText }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, defineComponent } from 'vue'

// Icons as inline SVG components
const InfoIcon = defineComponent({
  template: `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.1"/>
      <path d="M12 16V12M12 8H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
})

const SuccessIcon = defineComponent({
  template: `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.1"/>
      <path d="M9 12L11 14L15 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
})

const WarningIcon = defineComponent({
  template: `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M10.29 3.86L1.82 18A2 2 0 0 0 3.64 21H20.36A2 2 0 0 0 22.18 18L13.71 3.86A2 2 0 0 0 10.29 3.86Z" fill="currentColor" fill-opacity="0.1"/>
      <path d="M12 9V13M12 17H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
})

const ErrorIcon = defineComponent({
  template: `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.1"/>
      <path d="M15 9L9 15M9 9L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
})

const QuestionIcon = defineComponent({
  template: `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.1"/>
      <path d="M9.09 9A3 3 0 0 1 12 6C13.66 6 15 7.34 15 9C15 10.64 13.68 11.93 12.06 11.99L12 12V13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M12 17H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `
})

interface Props {
  visible: boolean
  type?: 'info' | 'success' | 'warning' | 'error' | 'confirm'
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  allowBackdropClose?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  type: 'info',
  confirmText: '확인',
  cancelText: '취소',
  allowBackdropClose: true
})

const emit = defineEmits<{
  confirm: []
  cancel: []
  close: []
}>()

const typeClass = computed(() => `alert-${props.type}`)

const iconComponent = computed(() => {
  switch (props.type) {
    case 'success': return SuccessIcon
    case 'warning': return WarningIcon
    case 'error': return ErrorIcon
    case 'confirm': return QuestionIcon
    default: return InfoIcon
  }
})

const handleConfirm = () => {
  emit('confirm')
  emit('close')
}

const handleCancel = () => {
  emit('cancel')
  emit('close')
}

const handleBackdropClick = () => {
  if (props.allowBackdropClose) {
    emit('close')
  }
}
</script>

<style scoped>
/* Backdrop */
.alert-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* Modal */
.alert-modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 32px rgba(0, 0, 0, 0.15);
  max-width: 400px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Icon */
.alert-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 4px;
}

.alert-info .alert-icon {
  color: #4B3D34;
}

.alert-success .alert-icon {
  color: #10b981;
}

.alert-warning .alert-icon {
  color: #f59e0b;
}

.alert-error .alert-icon {
  color: #ef4444;
}

.alert-confirm .alert-icon {
  color: #4B3D34;
}

/* Content */
.alert-content {
  text-align: center;
}

.alert-title {
  font-family: "Inter", sans-serif;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.alert-message {
  font-family: "Inter", sans-serif;
  font-size: 16px;
  font-weight: 400;
  color: #374151;
  margin: 0;
  line-height: 1.5;
  word-break: keep-all;
}

/* Actions */
.alert-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.alert-button {
  font-family: "Inter", sans-serif;
  font-size: 16px;
  font-weight: 500;
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 80px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.alert-button.full-width {
  flex: 1;
  min-width: 120px;
}

.alert-button.primary {
  background-color: #4B3D34;
  color: white;
}

.alert-button.primary:hover {
  background-color: #594D44;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(75, 61, 52, 0.3);
}

.alert-button.secondary {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.alert-button.secondary:hover {
  background-color: #e5e7eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.alert-button:active {
  transform: translateY(0);
}

/* Enhanced mobile touch feedback */
@media (hover: none) and (pointer: coarse) {
  .alert-button {
    /* 모바일에서 더 명확한 터치 피드백 */
    transition: all 0.15s ease;
    user-select: none;
    -webkit-user-select: none;
    -webkit-tap-highlight-color: transparent;
  }
  
  .alert-button:active {
    transform: scale(0.98);
    opacity: 0.9;
  }
  
  .alert-button.primary:active {
    background-color: rgba(75, 61, 52, 0.9);
  }
  
  .alert-button.secondary:active {
    background-color: rgba(229, 231, 235, 0.9);
  }
  
  /* 모바일에서 backdrop 터치 개선 */
  .alert-backdrop {
    -webkit-tap-highlight-color: transparent;
  }
}

/* Type-specific button colors for primary button */
.alert-success .alert-button.primary {
  background-color: #10b981;
}

.alert-success .alert-button.primary:hover {
  background-color: #059669;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.alert-warning .alert-button.primary {
  background-color: #f59e0b;
}

.alert-warning .alert-button.primary:hover {
  background-color: #d97706;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.alert-error .alert-button.primary {
  background-color: #ef4444;
}

.alert-error .alert-button.primary:hover {
  background-color: #dc2626;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

/* Transitions */
.alert-backdrop-enter-active,
.alert-backdrop-leave-active {
  transition: opacity 0.3s ease;
}

.alert-backdrop-enter-from,
.alert-backdrop-leave-to {
  opacity: 0;
}

.alert-modal-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.alert-modal-leave-active {
  transition: all 0.2s ease-out;
}

.alert-modal-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(-20px);
}

.alert-modal-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(-10px);
}

/* Enhanced Mobile responsiveness */
/* Large mobile devices (iPhone Pro Max, large Android phones) */
@media (max-width: 768px) {
  .alert-backdrop {
    padding: 20px;
  }
  
  .alert-modal {
    max-width: 90vw;
    min-width: 280px;
    margin: 0 auto;
  }
}

/* Standard mobile devices */
@media (max-width: 480px) {
  .alert-backdrop {
    padding: 16px;
    align-items: flex-start;
    padding-top: 20vh; /* 모달을 화면 상단에서 1/5 지점에 위치 */
  }
  
  .alert-modal {
    padding: 24px;
    gap: 20px;
    max-width: 95vw;
    min-width: 280px;
    max-height: 80vh;
    overflow-y: auto;
    margin: 0;
  }
  
  .alert-icon {
    margin-bottom: 8px;
  }
  
  .alert-title {
    font-size: 18px;
    font-weight: 700;
    line-height: 1.3;
  }
  
  .alert-message {
    font-size: 16px;
    line-height: 1.5;
    text-align: center;
  }
  
  .alert-button {
    font-size: 16px;
    padding: 14px 24px;
    height: 48px;
    min-height: 48px; /* 터치하기 쉬운 크기 */
    border-radius: 8px;
    font-weight: 600;
  }
  
  .alert-actions {
    flex-direction: column;
    gap: 12px;
    margin-top: 8px;
  }
  
  .alert-button.full-width {
    width: 100%;
  }
}

/* Small mobile devices (iPhone SE, small Android phones) */
@media (max-width: 375px) {
  .alert-backdrop {
    padding: 12px;
    padding-top: 15vh;
  }
  
  .alert-modal {
    padding: 20px;
    gap: 16px;
    max-width: 98vw;
  }
  
  .alert-title {
    font-size: 16px;
  }
  
  .alert-message {
    font-size: 15px;
  }
  
  .alert-button {
    font-size: 15px;
    padding: 12px 20px;
    height: 44px;
    min-height: 44px;
  }
}

/* Landscape orientation on mobile */
@media (max-width: 768px) and (orientation: landscape) {
  .alert-backdrop {
    padding: 12px;
    padding-top: 5vh;
    align-items: flex-start;
  }
  
  .alert-modal {
    max-height: 90vh;
    overflow-y: auto;
  }
  
  .alert-actions {
    flex-direction: row;
    gap: 12px;
  }
  
  .alert-button.full-width {
    flex: 1;
    min-width: 100px;
  }
}

/* iOS Safari specific fixes */
@supports (-webkit-touch-callout: none) {
  .alert-modal {
    /* iOS에서 더 부드러운 스크롤 */
    -webkit-overflow-scrolling: touch;
  }
  
  .alert-button {
    /* iOS에서 버튼 스타일 일관성 */
    -webkit-appearance: none;
    appearance: none;
  }
}

/* Android Chrome specific fixes */
@media screen and (-webkit-min-device-pixel-ratio: 2) {
  .alert-modal {
    /* 고해상도 안드로이드에서 선명도 개선 */
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
</style>