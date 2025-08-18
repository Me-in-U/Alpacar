// 주차 이력 테스트 데이터 - Plain JavaScript for Chart.js compatibility
export const mockParkingRecords = [
  {
    id: 1,
    date: '2025-07-20',
    time: '16:00',
    space: 'A4',
    score: 85
  },
  {
    id: 2,
    date: '2025-07-19',
    time: '09:30',
    space: 'B2',
    score: 72
  },
  {
    id: 3,
    date: '2025-07-18',
    time: '14:15',
    space: 'A1',
    score: 91
  },
  {
    id: 4,
    date: '2025-07-17',
    time: '11:45',
    space: 'C3',
    score: 68
  },
  {
    id: 5,
    date: '2025-07-16',
    time: '14:00',
    space: 'A2',
    score: 79
  },
  {
    id: 6,
    date: '2025-07-15',
    time: '10:20',
    space: 'B1',
    score: 88
  },
  {
    id: 7,
    date: '2025-07-14',
    time: '15:30',
    space: 'A3',
    score: 74
  },
  {
    id: 8,
    date: '2025-07-13',
    time: '13:10',
    space: 'C1',
    score: 82
  },
  {
    id: 9,
    date: '2025-07-12',
    time: '16:45',
    space: 'B3',
    score: 77
  },
  {
    id: 10,
    date: '2025-07-11',
    time: '12:00',
    space: 'A5',
    score: 65
  }
]

// 차트 데이터 생성 - 가장 단순한 형태
export function getChartData() {
  try {
    console.log('getChartData called')
    console.log('mockParkingRecords:', mockParkingRecords)
    
    const recentRecords = mockParkingRecords.slice(0, 9).reverse()
    console.log('recentRecords:', recentRecords)
    
    const labels = recentRecords.map(record => record.date.slice(5))
    const scores = recentRecords.map(record => record.score)
    const fullDateTimes = recentRecords.map(record => `${record.date} ${record.time}`)
    
    const result = {
      labels: labels,
      scores: scores,
      fullDateTimes: fullDateTimes
    }
    
    console.log('Chart data generated successfully:', result)
    return result
  } catch (error) {
    console.error('Error in getChartData:', error)
    // 오류 발생 시 기본 데이터 반환
    return {
      labels: ['07-11', '07-12', '07-13', '07-14', '07-15', '07-16', '07-17', '07-18', '07-19'],
      scores: [65, 77, 82, 74, 88, 79, 68, 91, 72],
      fullDateTimes: ['2025-07-11 12:00', '2025-07-12 16:45', '2025-07-13 13:10', '2025-07-14 15:30', '2025-07-15 10:20', '2025-07-16 14:00', '2025-07-17 11:45', '2025-07-18 14:15', '2025-07-19 09:30']
    }
  }
}

// 최근 주차 이력 가져오기
export function getRecentParkingRecords(count = 5) {
  return mockParkingRecords.slice(0, count)
}