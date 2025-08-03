<template>
  <div class="chart-container">
    <canvas ref="chartCanvas" id="parkingChart"></canvas>
    <div v-if="!chartCreated" class="chart-loading">차트를 로드하는 중...</div>
    <div v-if="error" class="chart-error">{{ error }}</div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'

// Chart.js의 모든 요소 등록
Chart.register(...registerables)

export default {
  name: 'ParkingScoreChart',
  props: {
    data: {
      type: Object,
      default: () => null
    }
  },
  data() {
    return {
      chart: null,
      chartCreated: false,
      error: null
    }
  },
  async mounted() {
    console.log('ParkingScoreChart mounted')
    console.log('Props data:', this.data)
    
    // DOM이 완전히 로드된 후 차트 생성
    await this.$nextTick()
    setTimeout(() => {
      this.createChart()
    }, 100)
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy()
      this.chart = null
    }
  },
  methods: {
    createChart() {
      try {
        console.log('Creating chart...')
        
        const canvas = this.$refs.chartCanvas
        if (!canvas) {
          this.error = 'Canvas 요소를 찾을 수 없습니다'
          console.error('Canvas not found')
          return
        }

        console.log('Canvas found:', canvas)

        // 기존 차트가 있다면 제거
        if (this.chart) {
          this.chart.destroy()
          this.chart = null
        }

        // 차트 데이터 준비
        const chartData = this.prepareChartData()
        console.log('Chart data prepared:', chartData)

        // 차트 생성
        this.chart = new Chart(canvas, {
          type: 'bar',
          data: {
            labels: chartData.labels,
            datasets: [{
              label: '주차점수',
              data: chartData.scores,
              backgroundColor: '#F3EEEA',
              borderColor: '#776B5D',
              borderWidth: 2,
              borderRadius: 10,
              borderSkipped: false,
              barThickness: 18,
              categoryPercentage: 0.8,
              barPercentage: 0.7
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
              duration: 1000
            },
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                enabled: true,
                backgroundColor: '#776B5D',
                titleColor: '#FFFFFF',
                bodyColor: '#FFFFFF',
                cornerRadius: 6,
                displayColors: false,
                callbacks: {
                  title: (context) => {
                    const index = context[0].dataIndex
                    return chartData.fullDateTimes[index] || context[0].label
                  },
                  label: (context) => {
                    return `주차점수: ${context.parsed.y}점`
                  }
                }
              }
            },
            scales: {
              x: {
                display: false,
                grid: {
                  display: false
                }
              },
              y: {
                display: true,
                position: 'left',
                min: 0,
                max: 100,
                beginAtZero: true,
                ticks: {
                  stepSize: 50,
                  callback: function(value) {
                    return value + '점'
                  },
                  color: '#000000',
                  font: {
                    size: 12,
                    family: 'Inter'
                  },
                  padding: 5
                },
                grid: {
                  display: true,
                  color: '#CCCCCC',
                  lineWidth: 1,
                  drawBorder: false,
                  drawTicks: false
                },
                border: {
                  display: false
                }
              }
            },
            layout: {
              padding: {
                left: 5,
                right: 5,
                top: 10,
                bottom: 10
              }
            }
          }
        })

        console.log('Chart created successfully:', this.chart)
        this.chartCreated = true
        this.error = null

      } catch (error) {
        console.error('Error creating chart:', error)
        this.error = `차트 생성 오류: ${error.message}`
        this.chartCreated = false
      }
    },

    prepareChartData() {
      // props에서 데이터가 넘어왔는지 확인
      if (this.data && this.data.labels && this.data.scores) {
        console.log('Using props data')
        return {
          labels: this.data.labels,
          scores: this.data.scores,
          fullDateTimes: this.data.fullDateTimes || this.data.labels
        }
      }

      // 기본 테스트 데이터 사용
      console.log('Using fallback data')
      return {
        labels: ['07-11', '07-12', '07-13', '07-14', '07-15', '07-16', '07-17', '07-18', '07-19'],
        scores: [65, 77, 82, 74, 88, 79, 68, 91, 72],
        fullDateTimes: ['2025-07-11 12:00', '2025-07-12 16:45', '2025-07-13 13:10', '2025-07-14 15:30', '2025-07-15 10:20', '2025-07-16 14:00', '2025-07-17 11:45', '2025-07-18 14:15', '2025-07-19 09:30']
      }
    }
  },
  watch: {
    data: {
      handler(newData) {
        console.log('Data prop changed:', newData)
        if (this.chart && newData) {
          // 차트 데이터 업데이트
          const chartData = this.prepareChartData()
          this.chart.data.labels = chartData.labels
          this.chart.data.datasets[0].data = chartData.scores
          this.chart.update('active')
        }
      },
      deep: true,
      immediate: false
    }
  }
}
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  height: 200px;
  background: #EBE3D5;
  border: 1px solid #CCCCCC;
  border-radius: 10px;
  padding: 20px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

canvas {
  width: 100% !important;
  height: 100% !important;
  max-width: 100%;
  max-height: 100%;
}

.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #776B5D;
  font-size: 14px;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  z-index: 10;
}

.chart-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #d32f2f;
  font-size: 12px;
  font-family: 'Inter', sans-serif;
  text-align: center;
  z-index: 10;
  padding: 10px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 5px;
}
</style>