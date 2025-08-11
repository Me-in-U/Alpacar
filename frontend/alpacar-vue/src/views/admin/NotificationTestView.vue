<template>
  <div class="notification-test-view">
    <div class="container">
      <UnifiedNotificationTester />
    </div>
  </div>
</template>

<script setup lang="ts">
import UnifiedNotificationTester from '@/components/UnifiedNotificationTester.vue'
</script>

<style scoped>
.notification-test-view {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 20px;
}

.container {
  max-width: 1000px;
  margin: 0 auto;
}
</style>