<template>
  <div>
    <!-- Render all active alerts -->
    <AlertModal
      v-for="alert in alerts"
      :key="alert.id"
      :visible="alert.visible"
      :type="alert.type"
      :title="alert.title"
      :message="alert.message"
      :confirm-text="alert.confirmText"
      :cancel-text="alert.cancelText"
      :allow-backdrop-close="alert.allowBackdropClose"
      @confirm="handleConfirm(alert.id)"
      @cancel="handleCancel(alert.id)"
      @close="handleClose(alert.id)"
    />
  </div>
</template>

<script setup lang="ts">
import AlertModal from './AlertModal.vue'
import { globalAlert } from '@/composables/useAlert'

const { alerts, handleConfirm, handleCancel, handleClose } = globalAlert
</script>