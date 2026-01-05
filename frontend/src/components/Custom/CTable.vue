<template>
  <div v-if="tableConfig" class="custom-table-wrapper">
    <!-- 配置對象格式（包含 columns 和 data） -->
    <table v-if="tableConfig.columns && tableConfig.data" class="custom-table">
      <thead>
        <tr>
          <th
            v-for="col in tableConfig.columns"
            :key="col.prop"
            class="table-header"
            :style="col.width ? { width: `${col.width}px` } : {}"
          >
            {{ col.label || col.prop }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, rowIndex) in tableConfig.data"
          :key="rowIndex"
          class="table-row"
        >
          <td
            v-for="col in tableConfig.columns"
            :key="col.prop"
            class="table-cell"
            :style="col.width ? { width: `${col.width}px` } : {}"
          >
            {{ row[col.prop] || '' }}
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 簡單數據數組格式（兼容舊格式） -->
    <table
      v-else-if="Array.isArray(tableConfig) && tableConfig.length > 0"
      class="custom-table"
    >
      <thead>
        <tr>
          <th v-for="header in headers" :key="header" class="table-header">
            {{ header }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, rowIndex) in tableConfig"
          :key="rowIndex"
          class="table-row"
        >
          <td v-for="header in headers" :key="header" class="table-cell">
            {{ row[header] || '' }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  code: string
}

const props = defineProps<Props>()

// 檢查 JavaScript 對象字符串是否完整（用於流式傳輸場景）
// 支持單引號和雙引號字符串
function isCompleteJSON(str: string): boolean {
  // 移除前後空白
  const trimmed = str.trim()

  // 檢查是否以 { 開頭
  if (!trimmed.startsWith('{')) {
    return false
  }

  // 計算大括號的匹配情況
  let braceCount = 0
  let inString = false
  let stringChar: string | null = null // 記錄當前字符串的引號類型（' 或 "）
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

    // 檢查單引號或雙引號
    if ((char === '"' || char === "'") && !escapeNext) {
      if (!inString) {
        // 開始字符串
        inString = true
        stringChar = char
      } else if (char === stringChar) {
        // 結束字符串
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
        // 如果大括號匹配完成，且後面沒有更多內容（除了空白和分號），則認為是完整的
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

  // 如果大括號不匹配，說明不完整
  return braceCount === 0
}

// 解析 table 選項格式（用於表格配置）
function parseTableOption(str: string): any {
  try {
    let cleanedStr = str.replace(/^option\s*=\s*/, '').replace(/;\s*$/, '')

    // 在流式傳輸場景中，檢查對象是否完整
    // 如果不完整，返回 null，避免解析錯誤
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
    // 使用更精確的正則：匹配對象 key（在 { 或 , 或 : 之後，且不在字符串中）
    // 匹配模式：{ 或 , 或換行 + 空白 + word + :（但不在字符串中）
    cleanedStr = cleanedStr.replace(
      /([{,]\s*|^\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:/gm,
      '$1"$2":'
    )

    return JSON.parse(cleanedStr)
  } catch (error) {
    // 在流式傳輸中，解析錯誤是正常的（數據可能不完整）
    // 只在開發環境下輸出錯誤，避免控制台噪音
    if (import.meta.env.DEV) {
      console.debug(
        '解析表格選項失敗（可能是流式傳輸中的不完整數據）:',
        error,
        {
          input: str,
        }
      )
    }
    return null
  }
}

// 解析表格數據
const parseTableData = (code: string): any | null => {
  try {
    // 如果是 table 標籤
    // 首先嘗試解析為配置對象格式（包含 columns 和 data）
    // 使用非貪婪匹配，但實際上我們需要匹配完整的對象
    const configMatch = code.match(/option\s*=\s*\{([\s\S]*)\}/)
    if (configMatch) {
      // 提取完整的 option = {...} 字符串
      const fullOptionStr = configMatch[0]
      const config = parseTableOption(fullOptionStr)

      if (config && config.columns && config.data) {
        return config
      } else if (import.meta.env.DEV) {
        // 調試信息：如果匹配到了但解析失敗
        console.debug('表格配置解析失敗:', {
          hasConfig: !!config,
          hasColumns: config?.columns,
          hasData: config?.data,
          fullOptionStr: fullOptionStr.substring(0, 200), // 只顯示前200個字符
        })
      }
    } else if (import.meta.env.DEV && code.includes('option')) {
      // 調試信息：如果包含 option 但沒有匹配到
      console.debug('未匹配到 option 格式:', {
        codePreview: code.substring(0, 200),
      })
    }

    // 嘗試解析為 Markdown 表格格式（兼容舊格式）
    const lines = code
      .trim()
      .split('\n')
      .filter((line) => line.trim())

    if (lines.length < 2) return null

    // 檢查是否是 Markdown 表格格式（包含 | 分隔符）
    if (lines[0].includes('|')) {
      // 第一行是表頭
      const headers = lines[0]
        .split('|')
        .map((h) => h.trim())
        .filter((h) => h && h !== '')

      // 跳過分隔行（第二行通常是 |---|---|）
      const dataLines = lines.slice(2)

      // 解析數據行
      const data = dataLines.map((line) => {
        const values = line
          .split('|')
          .map((v) => v.trim())
          .filter((v) => v !== '')

        const row: any = {}
        headers.forEach((header, index) => {
          row[header] = values[index] || ''
        })
        return row
      })

      return data.length > 0 ? data : null
    }

    return null
  } catch (error) {
    console.error('解析表格數據時出錯:', error)
    return null
  }
}

// 解析後的表格配置
const tableConfig = computed(() => {
  return parseTableData(props.code)
})

// 獲取表頭（用於簡單數組格式）
const headers = computed(() => {
  if (Array.isArray(tableConfig.value) && tableConfig.value.length > 0) {
    return Object.keys(tableConfig.value[0])
  }
  return []
})
</script>

<style scoped lang="scss">
.custom-table-wrapper {
  margin: 12px 0;
  overflow-x: auto;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.custom-table .table-header {
  background: #f5f7fa;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #606266;
  border-bottom: 2px solid #ebeef5;
}

.custom-table .table-row {
  transition: background-color 0.25s;
}

.custom-table .table-row:hover {
  background-color: #f5f7fa;
}

.custom-table .table-row:nth-child(even) {
  background-color: #fafafa;
}

.custom-table .table-row:nth-child(even):hover {
  background-color: #f0f2f5;
}

.custom-table .table-cell {
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  color: #606266;
}
</style>
