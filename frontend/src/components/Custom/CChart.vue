<template>
  <div v-if="chartConfig" class="custom-chart-wrapper">
    <div ref="chartContainer" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

interface Props {
  code: string
}

const props = defineProps<Props>()
const chartContainer = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 檢查 JavaScript 對象字符串是否完整（用於流式傳輸場景）
function isCompleteJSON(str: string): boolean {
  const trimmed = str.trim()
  if (!trimmed.startsWith('{')) {
    return false
  }

  let braceCount = 0
  let inString = false
  let stringChar: string | null = null
  let escapeNext = false

  for (let i = 0; i < trimmed.length; i++) {
    const char = trimmed[i]

    if (escapeNext) {
      escapeNext = false
      continue
    }

    if (char === '\\') {
      escapeNext = true
      continue
    }

    if ((char === '"' || char === "'") && !escapeNext) {
      if (!inString) {
        inString = true
        stringChar = char
      } else if (char === stringChar) {
        inString = false
        stringChar = null
      }
      continue
    }

    if (!inString) {
      if (char === '{') {
        braceCount++
      } else if (char === '}') {
        braceCount--
        if (braceCount === 0) {
          const remaining = trimmed
            .slice(i + 1)
            .trim()
            .replace(/;?\s*$/, '')
          return remaining === ''
        }
      }
    }
  }

  return braceCount === 0
}

// 解析 chart 選項格式
function parseChartOption(str: string): any {
  try {
    let cleanedStr = str.replace(/^option\s*=\s*/, '').replace(/;\s*$/, '')

    // 在流式傳輸場景中，檢查對象是否完整
    if (!isCompleteJSON(cleanedStr)) {
      return null
    }

    // 處理 Python/JavaScript 特殊值
    cleanedStr = cleanedStr.replace(/\bNone\b/g, 'null')
    cleanedStr = cleanedStr.replace(/\bTrue\b/g, 'true')
    cleanedStr = cleanedStr.replace(/\bFalse\b/g, 'false')

    // 移除尾隨逗號
    cleanedStr = cleanedStr.replace(/,(\s*[}\]])/g, '$1')

    // 將單引號替換為雙引號（先處理字符串值）
    cleanedStr = cleanedStr.replace(/'/g, '"')

    // 將沒有引號的鍵名加上雙引號
    cleanedStr = cleanedStr.replace(
      /([{,]\s*|^\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:/gm,
      '$1"$2":'
    )

    return JSON.parse(cleanedStr)
  } catch (error) {
    if (import.meta.env.DEV) {
      console.debug(
        '解析圖表選項失敗（可能是流式傳輸中的不完整數據）:',
        error,
        {
          input: str,
        }
      )
    }
    return null
  }
}

// 解析圖表配置
const parseChartData = (code: string): any | null => {
  try {
    const configMatch = code.match(/option\s*=\s*\{([\s\S]*)\}/)
    if (configMatch) {
      const fullOptionStr = configMatch[0]
      const config = parseChartOption(fullOptionStr)

      if (config && config.type) {
        return config
      } else if (import.meta.env.DEV) {
        console.debug('圖表配置解析失敗:', {
          hasConfig: !!config,
          hasType: config?.type,
          fullOptionStr: fullOptionStr.substring(0, 200),
        })
      }
    } else if (import.meta.env.DEV && code.includes('option')) {
      console.debug('未匹配到 option 格式:', {
        codePreview: code.substring(0, 200),
      })
    }

    return null
  } catch (error) {
    console.error('解析圖表數據時出錯:', error)
    return null
  }
}

// 解析後的圖表配置
const chartConfig = computed(() => {
  return parseChartData(props.code)
})

// 將自定義配置轉換為 echarts 標準配置
const convertToEChartsOption = (config: any): echarts.EChartsOption => {
  const chartType = config.type || 'line'
  const seriesData = config.data || []
  const xAxisData = config.xAxis?.data || []
  const xAxisType = config.xAxis?.type || 'category'
  const yAxisType = config.yAxis?.type || 'value'

  // 構建 series
  const series: any[] = seriesData.map((item: any) => {
    const baseSeries: any = {
      name: item.name || 'Series',
      data: item.data || [],
    }

    // 根據圖表類型設置不同的配置
    if (chartType === 'line') {
      baseSeries.type = 'line'
      baseSeries.smooth = true
    } else if (chartType === 'bar') {
      baseSeries.type = 'bar'
    } else if (chartType === 'pie') {
      baseSeries.type = 'pie'
      // 餅圖需要特殊處理數據格式
      if (Array.isArray(item.data) && xAxisData.length > 0) {
        baseSeries.data = item.data.map((value: any, index: number) => ({
          value: value,
          name: xAxisData[index] || `Item ${index}`,
        }))
      } else {
        baseSeries.data = item.data || []
      }
    } else if (chartType === 'scatter') {
      baseSeries.type = 'scatter'
    } else {
      baseSeries.type = chartType
    }

    return baseSeries
  })

  // 構建 echarts 標準配置
  const echartsOption: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: seriesData.map((item: any) => item.name || 'Series'),
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: xAxisType,
      data: xAxisData,
      boundaryGap: chartType === 'bar' ? false : true,
    },
    yAxis: {
      type: yAxisType,
    },
    series: series,
  }

  // 如果是餅圖，需要特殊處理
  if (chartType === 'pie') {
    delete echartsOption.xAxis
    delete echartsOption.yAxis
    echartsOption.tooltip = {
      trigger: 'item',
    }
    echartsOption.legend = {
      orient: 'vertical',
      left: 'left',
    }
  }

  return echartsOption
}

// 初始化圖表
const initChart = async () => {
  if (!chartContainer.value || !chartConfig.value) {
    return
  }

  await nextTick()

  // 如果已經有實例，先銷毀
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }

  // 創建新的圖表實例
  chartInstance = echarts.init(chartContainer.value)

  // 轉換配置並設置
  const echartsOption = convertToEChartsOption(chartConfig.value)
  chartInstance.setOption(echartsOption)

  // 響應式調整大小
  const resizeObserver = new ResizeObserver(() => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
  resizeObserver.observe(chartContainer.value)
}

// 監聽配置變化
watch(
  () => chartConfig.value,
  () => {
    if (chartConfig.value) {
      initChart()
    }
  },
  { immediate: true }
)

// 監聽容器變化
watch(
  () => chartContainer.value,
  () => {
    if (chartContainer.value && chartConfig.value) {
      initChart()
    }
  }
)

onMounted(() => {
  if (chartConfig.value) {
    initChart()
  }
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped lang="scss">
.custom-chart-wrapper {
  margin: 12px 0;
  width: 100%;
}

.chart-container {
  width: 100%;
  min-height: 400px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>

