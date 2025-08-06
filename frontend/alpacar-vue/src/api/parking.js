// src/api/parking.js
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL || 'http://localhost:8000/api'

// axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10초 타임아웃
  headers: {
    'Content-Type': 'application/json'
  }
})

// 요청 인터셉터 - 토큰 자동 추가
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    console.log('API Request:', config.method.toUpperCase(), config.url)
    return config
  },
  error => {
    console.error('Request Error:', error)
    return Promise.reject(error)
  }
)

// 응답 인터셉터 - 에러 처리
apiClient.interceptors.response.use(
  response => {
    console.log('API Response:', response.config.url, response.status)
    return response
  },
  error => {
    console.error('Response Error:', error)
    
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout')
      error.message = '요청 시간이 초과되었습니다. 다시 시도해주세요.'
    } else if (error.response) {
      // 서버가 응답했지만 에러 상태 코드
      console.error('Error Status:', error.response.status)
      console.error('Error Data:', error.response.data)
      
      if (error.response.status === 504) {
        error.message = '서버가 응답하지 않습니다. 잠시 후 다시 시도해주세요.'
      }
    } else if (error.request) {
      // 요청은 보냈지만 응답을 받지 못함
      console.error('No response received:', error.request)
      error.message = '서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.'
    }
    
    return Promise.reject(error)
  }
)

// 주차 관련 API
export const parkingAPI = {
  // 주차 이력 조회
  getParkingHistory() {
    return apiClient.get('/parking/history/')
  },

  // 주차 점수 히스토리 조회
  getParkingScoreHistory() {
    return apiClient.get('/parking/score-history/')
  },

  // 차트 데이터 조회
  getChartData() {
    return apiClient.get('/parking/chart-data/')
  },

  // 주차 배정 생성
  createParkingAssignment(data) {
    return apiClient.post('/parking/assign/', data)
  },

  // 주차 완료 처리
  completeParkingAssignment(assignmentId) {
    return apiClient.post(`/parking/complete/${assignmentId}/`)
  }
}

export default parkingAPI