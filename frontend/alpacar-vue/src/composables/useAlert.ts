import { ref, nextTick } from 'vue'

export type AlertType = 'info' | 'success' | 'warning' | 'error' | 'confirm'

export interface AlertOptions {
  type?: AlertType
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  allowBackdropClose?: boolean
  duration?: number // Auto-close duration in ms (0 = no auto-close)
}

interface AlertState extends AlertOptions {
  id: string
  visible: boolean
  resolve?: (value: boolean) => void
}

const alerts = ref<AlertState[]>([])
let alertIdCounter = 0

export function useAlert() {
  /**
   * Show an alert dialog
   * @param options Alert options
   * @returns Promise<boolean> - resolves to true if confirmed, false if cancelled
   */
  const showAlert = (options: AlertOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      const id = `alert-${++alertIdCounter}`
      
      const alertState: AlertState = {
        id,
        visible: false,
        resolve,
        type: 'info',
        confirmText: '확인',
        cancelText: '취소',
        allowBackdropClose: true,
        duration: 0,
        ...options
      }
      
      alerts.value.push(alertState)
      
      // Show alert with animation
      nextTick(() => {
        const alert = alerts.value.find(a => a.id === id)
        if (alert) {
          alert.visible = true
          
          // Auto-close if duration is set
          if (alert.duration && alert.duration > 0 && alert.type !== 'confirm') {
            setTimeout(() => {
              closeAlert(id, true)
            }, alert.duration)
          }
        }
      })
    })
  }
  
  /**
   * Show a simple info alert
   */
  const alert = (message: string, title?: string): Promise<boolean> => {
    return showAlert({ type: 'info', message, title })
  }
  
  /**
   * Show a success alert
   */
  const alertSuccess = (message: string, title?: string, duration = 3000): Promise<boolean> => {
    return showAlert({ type: 'success', message, title, duration })
  }
  
  /**
   * Show a warning alert
   */
  const alertWarning = (message: string, title?: string): Promise<boolean> => {
    return showAlert({ type: 'warning', message, title })
  }
  
  /**
   * Show an error alert
   */
  const alertError = (message: string, title?: string): Promise<boolean> => {
    return showAlert({ type: 'error', message, title })
  }
  
  /**
   * Show a confirmation dialog
   */
  const confirm = (
    message: string, 
    title?: string, 
    confirmText = '확인', 
    cancelText = '취소'
  ): Promise<boolean> => {
    return showAlert({ 
      type: 'confirm', 
      message, 
      title, 
      confirmText, 
      cancelText,
      allowBackdropClose: false 
    })
  }
  
  /**
   * Close a specific alert
   */
  const closeAlert = (id: string, confirmed = false) => {
    const alertIndex = alerts.value.findIndex(a => a.id === id)
    if (alertIndex >= 0) {
      const alert = alerts.value[alertIndex]
      alert.visible = false
      
      // Resolve promise
      if (alert.resolve) {
        alert.resolve(confirmed)
      }
      
      // Remove from array after transition
      setTimeout(() => {
        const currentIndex = alerts.value.findIndex(a => a.id === id)
        if (currentIndex >= 0) {
          alerts.value.splice(currentIndex, 1)
        }
      }, 300)
    }
  }
  
  /**
   * Close all alerts
   */
  const closeAllAlerts = () => {
    alerts.value.forEach(alert => {
      if (alert.resolve) {
        alert.resolve(false)
      }
    })
    alerts.value.length = 0
  }
  
  /**
   * Handle alert confirmation
   */
  const handleConfirm = (id: string) => {
    closeAlert(id, true)
  }
  
  /**
   * Handle alert cancellation
   */
  const handleCancel = (id: string) => {
    closeAlert(id, false)
  }
  
  /**
   * Handle alert close (backdrop or close button)
   */
  const handleClose = (id: string) => {
    closeAlert(id, false)
  }
  
  return {
    // State
    alerts,
    
    // Methods
    showAlert,
    alert,
    alertSuccess,
    alertWarning,
    alertError,
    confirm,
    closeAlert,
    closeAllAlerts,
    
    // Event handlers
    handleConfirm,
    handleCancel,
    handleClose
  }
}

// Create a global instance for easier access
export const globalAlert = useAlert()

// Global alert methods for easier migration from window.alert
export const {
  alert,
  alertSuccess,
  alertWarning,
  alertError,
  confirm
} = globalAlert