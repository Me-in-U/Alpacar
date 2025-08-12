<template>
  <div class="unified-notification-tester">
    <!-- 헤더 -->
    <div class="header">
      <h2>🔔 푸시 알림 테스트</h2>
      <p class="subtitle">푸시 알림이 정상적으로 작동하는지 테스트하고 상태를 확인하세요</p>
    </div>

    <!-- 현재 상태 표시 -->
    <div class="status-section">
      <div class="status-cards">
        <div class="status-card" :class="pushStatus.enabled ? 'enabled' : 'disabled'">
          <div class="status-icon">
            {{ pushStatus.enabled ? '✅' : '❌' }}
          </div>
          <div class="status-content">
            <h3>푸시 알림</h3>
            <p>{{ pushStatus.enabled ? '활성화됨' : '비활성화됨' }}</p>
          </div>
        </div>

        <div class="status-card">
          <div class="status-icon">📱</div>
          <div class="status-content">
            <h3>구독 상태</h3>
            <p>{{ pushStatus.subscriptions }}개 디바이스</p>
          </div>
        </div>

        <div class="status-card">
          <div class="status-icon">📬</div>
          <div class="status-content">
            <h3>읽지 않은 알림</h3>
            <p>{{ pushStatus.unreadCount }}개</p>
          </div>
        </div>

        <div class="status-card" :class="apiStatus.connected ? 'enabled' : 'disabled'">
          <div class="status-icon">
            {{ apiStatus.connected ? '🟢' : '🔴' }}
          </div>
          <div class="status-content">
            <h3>API 상태</h3>
            <p>{{ apiStatus.connected ? '연결됨' : '연결 끊김' }}</p>
          </div>
        </div>
      </div>
      
      <button class="refresh-btn" @click="refreshStatus" :disabled="loading">
        🔄 상태 새로고침
      </button>
    </div>

    <!-- 빠른 테스트 섹션 -->
    <div class="quick-test-section" v-if="pushStatus.enabled">
      <h3>⚡ 빠른 테스트</h3>
      <div class="test-buttons">
        <button 
          class="test-btn primary" 
          @click="runBasicTest" 
          :disabled="loading"
        >
          <span class="btn-icon">🔔</span>
          <span class="btn-text">기본 알림</span>
        </button>
        
        <button 
          class="test-btn" 
          @click="runParkingFlowTest" 
          :disabled="loading"
        >
          <span class="btn-icon">🚗</span>
          <span class="btn-text">주차 플로우</span>
        </button>
        
        <button 
          class="test-btn" 
          @click="runSystemTest" 
          :disabled="loading"
        >
          <span class="btn-icon">⚙️</span>
          <span class="btn-text">시스템 테스트</span>
        </button>
      </div>
    </div>

    <!-- 고급 테스트 섹션 (관리자용) -->
    <div class="advanced-test-section" v-if="isAdmin && pushStatus.enabled">
      <details>
        <summary>🔧 고급 테스트 옵션</summary>
        
        <!-- 사용자 정의 알림 -->
        <div class="custom-test">
          <h4>✨ 사용자 정의 알림</h4>
          <form @submit.prevent="sendCustomNotification" class="custom-form">
            <div class="form-row">
              <input 
                v-model="customNotification.title" 
                type="text" 
                placeholder="알림 제목"
                required
              />
              <select v-model="customNotification.type">
                <option value="system">시스템</option>
                <option value="vehicle_entry">입차</option>
                <option value="parking_complete">주차완료</option>
                <option value="grade_upgrade">등급승급</option>
              </select>
            </div>
            <textarea 
              v-model="customNotification.message" 
              placeholder="알림 메시지를 입력하세요"
              required
            ></textarea>
            <button type="submit" class="test-btn" :disabled="loading">
              📤 사용자 정의 알림 전송
            </button>
          </form>
        </div>

        <!-- 배치 테스트 -->
        <div class="batch-test">
          <h4>📦 배치 테스트</h4>
          <div class="batch-controls">
            <div class="form-group">
              <label>알림 개수:</label>
              <input v-model.number="batchSettings.count" type="number" min="1" max="5" />
            </div>
            <div class="form-group">
              <label>간격(초):</label>
              <input v-model.number="batchSettings.delay" type="number" min="1" max="10" />
            </div>
            <button class="test-btn" @click="runBatchTest" :disabled="loading">
              🚀 배치 실행
            </button>
          </div>
        </div>

        <!-- 관리 기능 -->
        <div class="management">
          <h4>🛠️ 관리</h4>
          <div class="management-buttons">
            <button class="test-btn danger" @click="clearTestNotifications" :disabled="loading">
              🧹 테스트 알림 삭제
            </button>
            <button class="test-btn" @click="exportResults" :disabled="loading">
              📊 결과 내보내기
            </button>
          </div>
        </div>
      </details>
    </div>

    <!-- 테스트 결과 -->
    <div class="results-section" v-if="testResults.length > 0">
      <div class="results-header">
        <h3>📝 테스트 결과</h3>
        <button class="clear-btn" @click="clearResults">🗑️ 지우기</button>
      </div>
      <div class="results-list">
        <div 
          v-for="(result, index) in testResults" 
          :key="index"
          class="result-item"
          :class="result.success ? 'success' : 'error'"
        >
          <span class="result-icon">
            {{ result.success ? '✅' : '❌' }}
          </span>
          <div class="result-content">
            <div class="result-message">{{ result.message }}</div>
            <div class="result-time">{{ formatTime(result.timestamp) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 도움말 -->
    <div class="help-section">
      <details>
        <summary>💡 도움말 및 문제 해결</summary>
        <div class="help-content">
          <div class="help-item">
            <h4>🚫 알림이 표시되지 않는 경우:</h4>
            <ul>
              <li>브라우저 알림 권한이 허용되어 있는지 확인하세요</li>
              <li>푸시 알림 설정이 활성화되어 있는지 확인하세요</li>
              <li>HTTPS 환경에서 사용하고 있는지 확인하세요</li>
              <li>페이지가 활성 상태인지 확인하세요</li>
            </ul>
          </div>
          <div class="help-item">
            <h4>🔧 API 연결 문제:</h4>
            <ul>
              <li>로그인 상태를 확인하세요</li>
              <li>인터넷 연결을 확인하세요</li>
              <li>서버 상태를 확인하세요</li>
            </ul>
          </div>
          <div class="help-item">
            <h4>📱 모바일에서 사용시:</h4>
            <ul>
              <li>브라우저 설정에서 알림을 허용해야 합니다</li>
              <li>홈화면에 추가한 경우 PWA로 실행하세요</li>
            </ul>
          </div>
        </div>
      </details>
    </div>

    <!-- 로딩 오버레이 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>{{ loadingMessage }}</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { BACKEND_BASE_URL } from '@/utils/api'

interface TestResult {
  success: boolean
  message: string
  timestamp: Date
  apiUsed?: string
}

interface PushStatus {
  enabled: boolean
  subscriptions: number
  unreadCount: number
}

interface ApiStatus {
  connected: boolean
  endpoints: string[]
}

interface CustomNotification {
  title: string
  message: string
  type: string
}

interface BatchSettings {
  count: number
  delay: number
}

export default defineComponent({
  name: 'UnifiedNotificationTester',
  setup() {
    const userStore = useUserStore()
    const loading = ref(false)
    const loadingMessage = ref('처리 중...')
    const testResults = ref<TestResult[]>([])

    const pushStatus = ref<PushStatus>({
      enabled: false,
      subscriptions: 0,
      unreadCount: 0
    })

    const apiStatus = ref<ApiStatus>({
      connected: false,
      endpoints: []
    })

    const customNotification = reactive<CustomNotification>({
      title: '',
      message: '',
      type: 'system'
    })

    const batchSettings = reactive<BatchSettings>({
      count: 3,
      delay: 2
    })

    const isAdmin = computed(() => {
      return userStore.me?.is_staff || false
    })

    // API 호출 유틸리티
    const apiCall = async (url: string, method: string = 'POST', body?: any): Promise<any> => {
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('로그인이 필요합니다.')
      }

      const response = await fetch(`${BACKEND_BASE_URL}${url}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: body ? JSON.stringify(body) : undefined
      })

      if (!response.ok) {
        const errorText = await response.text()
        // 더 상세한 에러 정보 제공
        let errorDetail = `API 호출 실패 (${response.status})`
        
        try {
          const errorJson = JSON.parse(errorText)
          if (errorJson.error) {
            errorDetail += `: ${errorJson.error}`
          } else if (errorJson.detail) {
            errorDetail += `: ${errorJson.detail}`
          }
        } catch {
          // JSON 파싱 실패 시 원본 텍스트 사용
          if (errorText) {
            errorDetail += `: ${errorText}`
          }
        }
        
        throw new Error(errorDetail)
      }

      return await response.json()
    }

    // 결과 추가
    const addResult = (success: boolean, message: string, apiUsed?: string) => {
      testResults.value.unshift({
        success,
        message,
        timestamp: new Date(),
        apiUsed
      })

      // 최대 10개 결과만 유지
      if (testResults.value.length > 10) {
        testResults.value = testResults.value.slice(0, 10)
      }
    }

    // API 연결 상태 확인 (실제 작동하는 엔드포인트 위주)
    const checkApiStatus = async () => {
      const testEndpoints = [
        '/vehicles/send-push/',  // AdminParkingLogs.vue에서 사용하는 실제 작동 엔드포인트
        '/vehicles/',            // 차량 정보 조회
        '/vehicle-events/active/', // AdminMain.vue에서 사용
        '/parking/assign/',      // AdminMain.vue에서 사용
        '/notifications/test-push/', // 테스트용 (있을 수도 있음)
      ]

      const workingEndpoints: string[] = []
      
      for (const endpoint of testEndpoints) {
        try {
          // HEAD 요청으로 엔드포인트 존재 확인 (더 가벼움)
          const response = await fetch(`${BACKEND_BASE_URL}${endpoint}`, {
            method: 'HEAD',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          })
          if (response.ok || response.status === 405 || response.status === 401) { // 401도 엔드포인트 존재를 의미
            workingEndpoints.push(endpoint)
          }
        } catch (error) {
          // 엔드포인트 없음 또는 네트워크 오류
        }
      }

      // 핵심 엔드포인트 /vehicles/send-push/ 가 작동하면 연결된 것으로 간주
      const isConnected = workingEndpoints.includes('/vehicles/send-push/')
      
      apiStatus.value = {
        connected: isConnected,
        endpoints: workingEndpoints
      }

      return isConnected
    }

    // 푸시 설정 자동 활성화
    const enablePushNotifications = async (): Promise<boolean> => {
      try {
        // 현재 푸시 설정 확인
        const currentSetting = await apiCall('/push/setting/', 'GET')
        if (currentSetting.push_on) {
          return true // 이미 활성화됨
        }

        // 푸시 설정 활성화
        await apiCall('/push/setting/', 'POST', { push_on: true })
        addResult(true, '푸시 알림이 자동으로 활성화되었습니다.', '푸시 설정 API')
        return true
      } catch (error) {
        addResult(false, `푸시 설정 활성화 실패: ${error}`)
        return false
      }
    }

    // 상태 새로고침
    const refreshStatus = async () => {
      try {
        loading.value = true
        loadingMessage.value = '상태 확인 중...'

        // 사용자 정보 새로고침
        const token = localStorage.getItem('access_token')
        if (token) {
          await userStore.fetchMe(token)
        }

        // API 상태 확인
        await checkApiStatus()

        // 푸시 상태 업데이트
        pushStatus.value = {
          enabled: Boolean(userStore.me?.push_on),
          subscriptions: 1, // 임시값
          unreadCount: 0    // 임시값
        }

        // 푸시가 비활성화된 경우 자동 활성화 시도
        if (!pushStatus.value.enabled) {
          loadingMessage.value = '푸시 알림 설정 확인 중...'
          const enableSuccess = await enablePushNotifications()
          if (enableSuccess && token) {
            // 사용자 정보 다시 불러오기
            await userStore.fetchMe(token)
            pushStatus.value.enabled = Boolean(userStore.me?.push_on)
          }
        }

        // 알림 개수 조회 (가능한 경우)
        try {
          const unreadResponse = await apiCall('/notifications/unread-count/', 'GET')
          pushStatus.value.unreadCount = unreadResponse.count || 0
        } catch (error) {
          console.log('읽지 않은 알림 개수 조회 실패:', error)
        }

        addResult(true, '상태가 성공적으로 새로고침되었습니다.')
      } catch (error) {
        addResult(false, `상태 새로고침 실패: ${error}`)
        console.error('Status refresh error:', error)
      } finally {
        loading.value = false
      }
    }

    // 기본 테스트
    const runBasicTest = async () => {
      try {
        loading.value = true
        loadingMessage.value = '기본 알림 테스트 준비 중...'

        // 푸시 설정 확인 및 활성화
        if (!pushStatus.value.enabled) {
          loadingMessage.value = '푸시 알림 설정 활성화 중...'
          const enableSuccess = await enablePushNotifications()
          if (!enableSuccess) {
            addResult(false, '푸시 알림이 비활성화되어 있습니다. 설정에서 활성화해주세요.')
            return
          }
        }

        loadingMessage.value = '기본 알림 테스트 중...'

        // 사용자 차량번호 가져오기 (있는 경우)
        const getUserLicensePlate = async () => {
          try {
            const vehicleResponse = await apiCall('/vehicles/', 'GET')
            if (vehicleResponse?.results?.length > 0) {
              return vehicleResponse.results[0].license_plate
            }
          } catch (error) {
            console.log('사용자 차량 정보 조회 실패:', error)
          }
          return 'TEST123' // 기본값
        }

        const licensePlate = await getUserLicensePlate()

        // AdminParkingLogs.vue에서 사용하는 동일한 방식으로 푸시 발송
        try {
          await apiCall('/vehicles/send-push/', 'POST', { 
            license_plate: licensePlate,
            message: '🔔 푸시 알림 테스트입니다!' 
          })
          addResult(true, `기본 푸시 알림 테스트가 성공했습니다! (차량번호: ${licensePlate})`, '차량 API')
        } catch (error) {
          console.error('기본 테스트 실패:', error)
          addResult(false, `기본 테스트 실패: ${error}`)
        }

      } catch (error) {
        addResult(false, `기본 테스트 실패: ${error}`)
      } finally {
        loading.value = false
      }
    }

    // 주차 플로우 테스트 (AdminMain.vue와 AdminParkingLogs.vue 패턴 기반)
    const runParkingFlowTest = async () => {
      try {
        loading.value = true
        loadingMessage.value = '주차 플로우 테스트 준비 중...'

        // 푸시 설정 확인 및 활성화
        if (!pushStatus.value.enabled) {
          loadingMessage.value = '푸시 알림 설정 활성화 중...'
          const enableSuccess = await enablePushNotifications()
          if (!enableSuccess) {
            addResult(false, '푸시 알림이 비활성화되어 있습니다. 설정에서 활성화해주세요.')
            return
          }
        }

        loadingMessage.value = '주차 플로우 테스트 중...'

        // 사용자 차량번호 가져오기 (있는 경우)
        const getUserLicensePlate = async () => {
          try {
            const vehicleResponse = await apiCall('/vehicles/', 'GET')
            if (vehicleResponse?.results?.length > 0) {
              return vehicleResponse.results[0].license_plate
            }
          } catch (error) {
            console.log('사용자 차량 정보 조회 실패:', error)
          }
          return 'TEST123' // 기본값
        }

        const licensePlate = await getUserLicensePlate()

        // 1단계: 입차 알림 (AdminMain.vue의 입차 이벤트 시뮬레이션)
        try {
          await apiCall('/vehicles/send-push/', 'POST', {
            license_plate: licensePlate,
            message: `🚗 [${licensePlate}] 차량 입차가 감지되었습니다.`
          })
          addResult(true, `입차 알림 전송 완료 (차량번호: ${licensePlate})`, '차량 API')
        } catch (error) {
          addResult(false, `입차 알림 실패: ${error}`)
          return
        }

        // 2초 대기 (실제 주차 과정 시뮬레이션)
        await new Promise(resolve => setTimeout(resolve, 2000))
        loadingMessage.value = '주차 배정 시뮬레이션 중...'

        // 2단계: 주차 배정 알림 (AdminMain.vue의 배정 로직 시뮬레이션)
        try {
          await apiCall('/vehicles/send-push/', 'POST', {
            license_plate: licensePlate,
            message: `🅿️ [${licensePlate}] A3 구역에 주차 배정되었습니다.`
          })
          addResult(true, '주차 배정 알림 전송 완료', '차량 API')
        } catch (error) {
          addResult(false, `주차 배정 알림 실패: ${error}`)
        }

        // 3초 대기 (주차 완료까지의 시간)
        await new Promise(resolve => setTimeout(resolve, 3000))
        loadingMessage.value = '주차 완료 처리 중...'

        // 3단계: 주차 완료 알림 (AdminParkingLogs.vue의 주차완료 로직)
        try {
          await apiCall('/vehicles/send-push/', 'POST', {
            license_plate: licensePlate,
            message: `✅ [${licensePlate}] 주차가 완료되었습니다. 점수: ${Math.floor(Math.random() * 20) + 80}점`
          })
          addResult(true, '주차 완료 알림 전송 완료', '차량 API')
        } catch (error) {
          addResult(false, `주차 완료 알림 실패: ${error}`)
        }

        // 2초 대기 후 출차 시뮬레이션
        await new Promise(resolve => setTimeout(resolve, 2000))
        loadingMessage.value = '출차 처리 중...'

        // 4단계: 출차 알림 (AdminParkingLogs.vue의 출차 로직)
        try {
          await apiCall('/vehicles/send-push/', 'POST', {
            license_plate: licensePlate,
            message: `🚪 [${licensePlate}] 출차가 완료되었습니다. 이용해주셔서 감사합니다!`
          })
          addResult(true, '출차 알림 전송 완료', '차량 API')
        } catch (error) {
          addResult(false, `출차 알림 실패: ${error}`)
        }

        addResult(true, '🎉 주차 플로우 테스트가 모두 완료되었습니다! (입차 → 배정 → 주차완료 → 출차)')

      } catch (error) {
        addResult(false, `주차 플로우 테스트 실패: ${error}`)
      } finally {
        loading.value = false
      }
    }

    // 시스템 테스트 (관리자 페이지의 실제 작동 방식 기반)
    const runSystemTest = async () => {
      try {
        loading.value = true
        loadingMessage.value = '시스템 테스트 준비 중...'

        // 푸시 설정 확인 및 활성화
        if (!pushStatus.value.enabled) {
          loadingMessage.value = '푸시 알림 설정 활성화 중...'
          const enableSuccess = await enablePushNotifications()
          if (!enableSuccess) {
            addResult(false, '푸시 알림이 비활성화되어 있습니다. 설정에서 활성화해주세요.')
            return
          }
        }

        loadingMessage.value = '시스템 테스트 중...'

        // 사용자 차량번호 가져오기
        const getUserLicensePlate = async () => {
          try {
            const vehicleResponse = await apiCall('/vehicles/', 'GET')
            if (vehicleResponse?.results?.length > 0) {
              return vehicleResponse.results[0].license_plate
            }
          } catch (error) {
            console.log('사용자 차량 정보 조회 실패:', error)
          }
          return 'TEST123' // 기본값
        }

        const licensePlate = await getUserLicensePlate()

        // AdminMain.vue와 AdminParkingLogs.vue에서 실제 사용되는 알림 패턴들
        const tests = [
          {
            name: '기본 푸시 알림',
            message: '🔔 시스템 테스트: 기본 푸시 알림'
          },
          {
            name: '입차 감지 알림',
            message: '🚗 시스템 테스트: 차량 입차 감지'
          },
          {
            name: '주차 배정 알림', 
            message: '🅿️ 시스템 테스트: A1 구역 주차 배정'
          },
          {
            name: '주차 완료 알림',
            message: '✅ 시스템 테스트: 주차 완료 (점수: 95점)'
          },
          {
            name: '출차 완료 알림',
            message: '🚪 시스템 테스트: 출차 완료'
          },
          {
            name: '등급 승급 알림',
            message: '🎉 시스템 테스트: 골드 등급으로 승급'
          }
        ]

        let successCount = 0
        for (let i = 0; i < tests.length; i++) {
          const test = tests[i]
          loadingMessage.value = `${test.name} 테스트 중... (${i + 1}/${tests.length})`
          
          try {
            // AdminParkingLogs.vue의 sendPush 함수와 동일한 방식 사용
            await apiCall('/vehicles/send-push/', 'POST', {
              license_plate: licensePlate,
              message: test.message
            })
            addResult(true, `${test.name} 성공 (차량번호: ${licensePlate})`, '차량 API')
            successCount++
          } catch (error) {
            addResult(false, `${test.name} 실패: ${error}`)
          }
          
          // 각 테스트 간 1초 간격
          if (i < tests.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }

        const resultMessage = successCount === tests.length 
          ? '🎉 모든 시스템 테스트가 성공했습니다!'
          : `⚠️ 시스템 테스트 완료: ${successCount}/${tests.length} 성공`
        
        addResult(
          successCount === tests.length, 
          resultMessage + ` (차량번호: ${licensePlate})`
        )

      } catch (error) {
        addResult(false, `시스템 테스트 실패: ${error}`)
      } finally {
        loading.value = false
      }
    }

    // 사용자 정의 알림 (AdminParkingLogs.vue 패턴 사용)
    const sendCustomNotification = async () => {
      try {
        loading.value = true
        loadingMessage.value = '사용자 정의 알림 전송 중...'

        // 푸시 설정 확인 및 활성화
        if (!pushStatus.value.enabled) {
          loadingMessage.value = '푸시 알림 설정 활성화 중...'
          const enableSuccess = await enablePushNotifications()
          if (!enableSuccess) {
            addResult(false, '푸시 알림이 비활성화되어 있습니다. 설정에서 활성화해주세요.')
            return
          }
        }

        // 사용자 차량번호 가져오기
        const getUserLicensePlate = async () => {
          try {
            const vehicleResponse = await apiCall('/vehicles/', 'GET')
            if (vehicleResponse?.results?.length > 0) {
              return vehicleResponse.results[0].license_plate
            }
          } catch (error) {
            console.log('사용자 차량 정보 조회 실패:', error)
          }
          return 'TEST123' // 기본값
        }

        const licensePlate = await getUserLicensePlate()
        
        // 타입별 이모지 추가
        const typeEmojis: Record<string, string> = {
          system: '🔔',
          vehicle_entry: '🚗',
          parking_complete: '🅿️',
          grade_upgrade: '🎉'
        }
        
        const emoji = typeEmojis[customNotification.type] || '📢'
        const fullMessage = `${emoji} [${customNotification.title}] ${customNotification.message}`

        // AdminParkingLogs.vue의 sendPush와 동일한 방식 사용
        await apiCall('/vehicles/send-push/', 'POST', {
          license_plate: licensePlate,
          message: fullMessage
        })

        addResult(true, `사용자 정의 알림 전송 성공: ${customNotification.title} (차량번호: ${licensePlate})`, '차량 API')
        
        // 폼 초기화
        customNotification.title = ''
        customNotification.message = ''
        customNotification.type = 'system'

      } catch (error) {
        addResult(false, `사용자 정의 알림 전송 실패: ${error}`)
      } finally {
        loading.value = false
      }
    }

    // 배치 테스트 (AdminParkingLogs.vue 패턴 기반)
    const runBatchTest = async () => {
      try {
        loading.value = true
        loadingMessage.value = `배치 알림 ${batchSettings.count}개 전송 중...`

        // 푸시 설정 확인 및 활성화
        if (!pushStatus.value.enabled) {
          loadingMessage.value = '푸시 알림 설정 활성화 중...'
          const enableSuccess = await enablePushNotifications()
          if (!enableSuccess) {
            addResult(false, '푸시 알림이 비활성화되어 있습니다. 설정에서 활성화해주세요.')
            return
          }
        }

        // 사용자 차량번호 가져오기 (있는 경우)
        const getUserLicensePlate = async () => {
          try {
            const vehicleResponse = await apiCall('/vehicles/', 'GET')
            if (vehicleResponse?.results?.length > 0) {
              return vehicleResponse.results[0].license_plate
            }
          } catch (error) {
            console.log('사용자 차량 정보 조회 실패:', error)
          }
          return 'TEST123' // 기본값
        }

        const licensePlate = await getUserLicensePlate()

        let successCount = 0
        const batchMessages = [
          '🔔 배치 테스트 알림',
          '📱 모바일 알림 테스트',
          '⚡ 실시간 알림 테스트',
          '🎯 타겟 알림 테스트', 
          '✨ 최종 알림 테스트'
        ]

        for (let i = 0; i < batchSettings.count; i++) {
          const messageTemplate = batchMessages[i % batchMessages.length]
          loadingMessage.value = `${messageTemplate} #${i + 1} 전송 중...`
          
          try {
            // AdminParkingLogs.vue의 sendPush와 동일한 방식
            await apiCall('/vehicles/send-push/', 'POST', {
              license_plate: licensePlate,
              message: `${messageTemplate} #${i + 1} (차량번호: ${licensePlate})`
            })
            addResult(true, `배치 알림 #${i + 1} 전송 성공`, '차량 API')
            successCount++
          } catch (error) {
            addResult(false, `배치 알림 #${i + 1} 전송 실패: ${error}`)
          }
          
          // 마지막이 아니면 대기
          if (i < batchSettings.count - 1) {
            await new Promise(resolve => setTimeout(resolve, batchSettings.delay * 1000))
          }
        }

        const finalMessage = successCount === batchSettings.count
          ? `🎉 배치 테스트 완료: ${batchSettings.count}개 알림 모두 전송 성공!`
          : `⚠️ 배치 테스트 완료: ${successCount}/${batchSettings.count} 성공`

        addResult(successCount === batchSettings.count, finalMessage + ` (차량번호: ${licensePlate})`)

      } catch (error) {
        addResult(false, `배치 테스트 실패: ${error}`)
      } finally {
        loading.value = false
      }
    }

    // 테스트 알림 삭제 (실제 API 엔드포인트가 없으므로 로컬 결과만 삭제)
    const clearTestNotifications = async () => {
      if (!confirm('테스트 결과를 모두 삭제하시겠습니까?')) {
        return
      }

      try {
        loading.value = true
        loadingMessage.value = '테스트 결과 정리 중...'
        
        // 실제 서버 알림 삭제 API가 없으므로 로컬 결과만 삭제
        testResults.value = []
        await refreshStatus() // 상태 새로고침
        
        addResult(true, '테스트 결과가 삭제되었습니다. 실제 푸시 알림은 디바이스에서 직접 삭제하세요.')
      } catch (error) {
        addResult(false, `테스트 결과 삭제 실패: ${error}`)
      } finally {
        loading.value = false
      }
    }

    // 결과 내보내기
    const exportResults = () => {
      const data = {
        timestamp: new Date().toISOString(),
        pushStatus: pushStatus.value,
        apiStatus: apiStatus.value,
        results: testResults.value
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `notification-test-results-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
      
      addResult(true, '테스트 결과를 내보냈습니다.')
    }

    // 결과 지우기
    const clearResults = () => {
      testResults.value = []
    }

    // 시간 포맷
    const formatTime = (timestamp: Date) => {
      return timestamp.toLocaleTimeString()
    }

    onMounted(() => {
      refreshStatus()
    })

    return {
      loading,
      loadingMessage,
      testResults,
      pushStatus,
      apiStatus,
      customNotification,
      batchSettings,
      isAdmin,
      refreshStatus,
      runBasicTest,
      runParkingFlowTest,
      runSystemTest,
      sendCustomNotification,
      runBatchTest,
      clearTestNotifications,
      exportResults,
      clearResults,
      formatTime,
      enablePushNotifications
    }
  }
})
</script>

<style scoped>
.unified-notification-tester {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
  position: relative;
}

.header {
  text-align: center;
  margin-bottom: 30px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header h2 {
  color: #2c3e50;
  margin: 0 0 8px 0;
  font-size: 24px;
}

.subtitle {
  color: #6c757d;
  margin: 0;
  font-size: 14px;
}

.status-section, .quick-test-section, .advanced-test-section, 
.results-section, .help-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border-radius: 8px;
  background: #f8f9fa;
  border: 2px solid #e9ecef;
}

.status-card.enabled {
  background: #d4edda;
  border-color: #c3e6cb;
}

.status-card.disabled {
  background: #f8d7da;
  border-color: #f1aeb5;
}

.status-icon {
  font-size: 24px;
}

.status-content h3 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #495057;
}

.status-content p {
  margin: 0;
  font-size: 12px;
  color: #6c757d;
}

.refresh-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #0056b3;
}

.test-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.test-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  text-align: center;
  justify-content: center;
}

.test-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.test-btn.primary {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.test-btn.danger {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
}

.btn-icon {
  font-size: 16px;
}

.custom-form {
  display: grid;
  gap: 15px;
}

.form-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 10px;
}

.form-row input, .form-row select, textarea {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

textarea {
  min-height: 60px;
  resize: vertical;
}

.batch-controls {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 15px;
  align-items: end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-size: 12px;
  color: #495057;
  font-weight: 500;
}

.form-group input {
  padding: 6px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
}

.management-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.results-header h3 {
  margin: 0;
  color: #2c3e50;
}

.clear-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 6px;
  font-size: 14px;
}

.result-item.success {
  background: #d4edda;
  border: 1px solid #c3e6cb;
}

.result-item.error {
  background: #f8d7da;
  border: 1px solid #f1aeb5;
}

.result-icon {
  font-size: 16px;
}

.result-content {
  flex: 1;
}

.result-message {
  color: #2c3e50;
  font-weight: 500;
}

.result-time {
  color: #6c757d;
  font-size: 12px;
  margin-top: 2px;
}

.help-content {
  padding: 15px 0;
}

.help-item {
  margin-bottom: 20px;
}

.help-item h4 {
  color: #495057;
  margin: 0 0 8px 0;
  font-size: 14px;
}

.help-item ul {
  margin: 0;
  padding-left: 20px;
  color: #6c757d;
  font-size: 13px;
}

.help-item li {
  margin-bottom: 4px;
}

details summary {
  cursor: pointer;
  color: #007bff;
  font-weight: 500;
  padding: 10px 0;
}

details[open] summary {
  margin-bottom: 15px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  z-index: 1000;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 15px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-overlay p {
  color: #495057;
  font-weight: 500;
  margin: 0;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

@media (max-width: 768px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
  
  .test-buttons {
    grid-template-columns: 1fr;
  }
  
  .batch-controls, .form-row {
    grid-template-columns: 1fr;
  }
}
</style>