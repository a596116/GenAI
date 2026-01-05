<template>
  <Suspense>
    <div class="app-container">
      <!-- 側邊欄 -->
      <Sidebar
        :conversations="conversations"
        :current-conversation-id="currentConversationId"
        :user-name="userName"
        @new-conversation="createNewConversation"
        @select-conversation="selectConversation"
        @delete-conversation="deleteConversation"
      />

      <!-- 主對話區域 -->
      <ConversationArea
        :conversation-id="currentConversationId"
        :conversation-title="currentConversationTitle"
        :messages="currentMessages"
        :is-loading="isLoading"
        :user-name="userName"
        @send-message="sendMessage"
        @clear-conversation="clearConversation"
      />
    </div>
  </Suspense>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import Sidebar from './components/Sidebar.vue'
import ConversationArea from './components/ConversationArea.vue'
import { useXStream } from 'vue-element-plus-x'
import type { ThinkingStatus } from './types/type'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  thinkingStatus?: ThinkingStatus
  isStreaming?: boolean // 標記是否為流式響應中的消息
  statusContent?: string // 單獨存儲 status 的 content，用於 Thinking 組件顯示
  suggestions?: string[] // 推薦問題列表（由後端返回）
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  updated_at: string
  message_count: number
}

// API 端點配置
const apiEndpoint = 'http://localhost:8000/api'

// 用戶配置
const userName = ref('User')

// 對話列表
const conversations = ref<Conversation[]>([])

// 當前對話 ID
const currentConversationId = ref<string | undefined>(undefined)

// 加載狀態
const isLoading = ref(false)

// 計算當前對話
const currentConversation = computed(() => {
  return conversations.value.find((c) => c.id === currentConversationId.value)
})

// 計算當前對話標題
const currentConversationTitle = computed(() => {
  return currentConversation.value?.title || '新對話'
})

// 計算當前消息列表
const currentMessages = computed(() => {
  return currentConversation.value?.messages || []
})

// 創建新對話
const createNewConversation = async () => {
  try {
    const response = await fetch(`${apiEndpoint}/conversations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: '新對話',
      }),
    })

    if (!response.ok) {
      throw new Error('創建對話失敗')
    }

    const data = await response.json()
    const conversationId = data.conversation_id || data.id

    if (!conversationId) {
      throw new Error('後端返回的對話 ID 無效')
    }

    const newConversation: Conversation = {
      id: String(conversationId),
      title: data.title || '新對話',
      messages: [],
      updated_at: new Date().toISOString(),
      message_count: 0,
    }

    conversations.value.unshift(newConversation)
    currentConversationId.value = newConversation.id
  } catch (error) {
    console.error('創建對話失敗:', error)
    // 如果後端不可用，創建本地對話
    const localId = `local-${Date.now()}`
    const localConversation: Conversation = {
      id: localId,
      title: '新對話',
      messages: [],
      updated_at: new Date().toISOString(),
      message_count: 0,
    }
    conversations.value.unshift(localConversation)
    currentConversationId.value = localId
  }
}

// 選擇對話
const selectConversation = async (id: string) => {
  if (!id) {
    console.warn('selectConversation 收到空的 id')
    return
  }

  console.log('選擇對話:', id, '當前對話:', currentConversationId.value)

  // 更新當前對話 ID
  currentConversationId.value = id

  // 如果不是本地對話，從後端加載消息
  if (id && typeof id === 'string' && !id.startsWith('local-')) {
    console.log('準備加載對話消息，conversationId:', id)
    await loadConversationMessages(id)
  } else {
    console.log('本地對話，跳過 API 調用')
    // 本地對話，確保對話對象存在
    const conversation = conversations.value.find((c) => c.id === id)
    if (!conversation) {
      console.warn('找不到對話:', id)
    }
  }
}

// 加載對話消息
const loadConversationMessages = async (conversationId: string) => {
  if (!conversationId) {
    console.warn('loadConversationMessages 收到空的 conversationId')
    return
  }

  const url = `${apiEndpoint}/conversations/${conversationId}/messages`
  console.log('🔵 發送 API 請求:', url)

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    console.log('🔵 API 響應狀態:', response.status, response.statusText)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('🔴 API 請求失敗:', response.status, errorText)
      throw new Error(`加載消息失敗: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    console.log('✅ 收到對話消息數據:', data)

    const conversation = conversations.value.find(
      (c) => c && c.id === conversationId
    )

    if (conversation) {
      // 更新消息列表
      if (data.messages && Array.isArray(data.messages)) {
        conversation.messages = data.messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content || '',
          timestamp: msg.created_at
            ? new Date(msg.created_at).getTime()
            : Date.now(),
          isStreaming: false, // 歷史消息不是流式響應
        }))
        console.log('✅ 已更新對話消息，共', conversation.messages.length, '條')
      } else {
        console.warn('⚠️ 後端返回的消息格式不正確:', data)
        conversation.messages = []
      }
    } else {
      console.warn('⚠️ 找不到對話對象:', conversationId)
    }
  } catch (error: any) {
    console.error('🔴 加載消息失敗:', error)
    console.error('錯誤詳情:', error.message, error.stack)

    // 即使加載失敗，也確保對話對象存在
    const conversation = conversations.value.find(
      (c) => c && c.id === conversationId
    )
    if (conversation && !conversation.messages) {
      conversation.messages = []
    }
  }
}

// 刪除對話
const deleteConversation = async (id: string) => {
  if (!id) {
    console.warn('deleteConversation 收到空的 id')
    return
  }

  try {
    const wasCurrentConversation = currentConversationId.value === id

    // 先從本地列表移除（樂觀更新）
    conversations.value = conversations.value.filter((c) => c && c.id !== id)

    // 如果刪除的是當前對話，選擇其他對話或清空
    if (wasCurrentConversation) {
      if (conversations.value.length > 0) {
        // 選擇第一個對話
        const firstConversation = conversations.value[0]
        if (firstConversation && firstConversation.id) {
          currentConversationId.value = firstConversation.id
          await loadConversationMessages(firstConversation.id)
        } else {
          currentConversationId.value = undefined
        }
      } else {
        // 沒有其他對話，清空當前對話
        currentConversationId.value = undefined
      }
    }

    // 然後從後端刪除（如果存在）
    if (id && typeof id === 'string' && !id.startsWith('local-')) {
      try {
        const response = await fetch(`${apiEndpoint}/conversations/${id}`, {
          method: 'DELETE',
        })

        if (!response.ok) {
          console.warn('後端刪除對話失敗，但已從本地移除')
        }
      } catch (error) {
        console.warn('刪除對話時後端請求失敗，但已從本地移除:', error)
      }
    }
  } catch (error) {
    console.error('刪除對話失敗:', error)
    // 如果出錯，嘗試重新加載對話列表
    await loadConversations()
  }
}

// 清空對話
const clearConversation = () => {
  const conversation = currentConversation.value
  if (conversation) {
    conversation.messages = []
    conversation.message_count = 0
  }
}

// 發送消息
const sendMessage = async (message: string) => {
  if (!message || !message.trim()) {
    return
  }

  if (!currentConversationId.value) {
    await createNewConversation()
    // 確保創建後有有效的對話 ID
    if (!currentConversationId.value) {
      console.error('創建對話後仍然沒有有效的對話 ID')
      return
    }
  }

  const conversation = currentConversation.value
  if (!conversation || !conversation.id) {
    console.error('當前對話無效')
    return
  }

  // 添加用戶消息
  const userMessage: Message = {
    role: 'user',
    content: message,
    timestamp: Date.now(),
  }
  conversation.messages.push(userMessage)

  // 更新對話標題（如果是第一條消息）
  if (conversation.messages.length === 1) {
    conversation.title =
      message.slice(0, 30) + (message.length > 30 ? '...' : '')
  }

  // 更新時間
  conversation.updated_at = new Date().toISOString()
  conversation.message_count++

  // 發送到後端
  isLoading.value = true

  try {
    const response = await fetch(`${apiEndpoint}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        question: message,
        conversation_id: currentConversationId.value,
      }),
    })

    if (!response.ok) {
      throw new Error('發送消息失敗')
    }

    const readableStream = response.body
    if (!readableStream) {
      throw new Error('無法讀取響應流')
    }

    // 在函數內部創建新的 useXStream 實例，確保每次調用都是全新的
    const { startStream, data: streamData, error: streamError } = useXStream()

    // 添加助手消息佔位符
    const assistantMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      thinkingStatus: 'start',
      isStreaming: true, // 標記為流式響應中的消息
    }
    conversation.messages.push(assistantMessage)

    // 重置處理計數
    let processedCount = 0
    let contentBuffer = ''

    // 監聽 streamData 的變化來逐步更新內容
    // 注意：watch 必須在 startStream 之前設置
    const stopWatch = watch(
      () => streamData.value, // 明確訪問 .value
      (newData) => {
        // 確保 newData 是數組
        const dataArray = Array.isArray(newData) ? newData : []
        if (!dataArray || !dataArray.length) return

        // 只處理新增的數據
        for (let index = processedCount; index < dataArray.length; index++) {
          const item = dataArray[index]
          // streamData 的數據格式是 { data: '...' }
          const chunk = item?.data || item

          // 先檢查是否是結束標記，避免不必要的 JSON 解析錯誤
          const trimmedChunk = chunk?.trim()
          if (trimmedChunk === '[DONE]') {
            // 數據接收完畢 - 設置為 end 狀態，並標記流式響應結束
            const messageIndex = conversation.messages.length - 1
            if (conversation.messages[messageIndex]) {
              conversation.messages[messageIndex].content =
                contentBuffer || '查詢完成'
              conversation.messages[messageIndex].thinkingStatus = 'end'
              conversation.messages[messageIndex].isStreaming = false // 流式響應結束
            }
            continue
          }

          try {
            const json = JSON.parse(chunk)

            // 處理不同類型的數據
            if (json.type === 'explanation' && json.content) {
              // 解釋內容（包括 SQL 和查詢結果的 markdown 表格）
              contentBuffer += json.content
              // 更新消息內容 - 使用數組索引確保響應式更新
              const messageIndex = conversation.messages.length - 1
              if (conversation.messages[messageIndex]) {
                conversation.messages[messageIndex].content = contentBuffer
                // 當開始收到解釋內容時，將狀態改為 thinking
                if (
                  conversation.messages[messageIndex].thinkingStatus === 'start'
                ) {
                  conversation.messages[messageIndex].thinkingStatus =
                    'thinking'
                }
              }
            } else if (json.type === 'status') {
              // 狀態訊息 - 根據 status.type 映射到 Thinking 狀態
              const messageIndex = conversation.messages.length - 1
              if (conversation.messages[messageIndex]) {
                const statusType = json.status?.type || 'working'
                const statusContent =
                  json.status?.content || json.content || '正在處理中...'

                // 映射 status.type 到 Thinking 狀態
                let thinkingStatus: ThinkingStatus = 'thinking'
                if (statusType === 'idle') {
                  thinkingStatus = 'start'
                } else if (statusType === 'working') {
                  thinkingStatus = 'thinking'
                } else if (statusType === 'error') {
                  thinkingStatus = 'error'
                } else if (statusType === 'success') {
                  thinkingStatus = 'end'
                }

                conversation.messages[messageIndex].content = statusContent
                conversation.messages[messageIndex].statusContent =
                  statusContent
                conversation.messages[messageIndex].thinkingStatus =
                  thinkingStatus
              }
            } else if (json.type === 'error') {
              // 錯誤訊息 - 設置為 error 狀態
              const messageIndex = conversation.messages.length - 1
              if (conversation.messages[messageIndex]) {
                const errorContent = json.error || '發生錯誤'
                conversation.messages[messageIndex].content = errorContent
                conversation.messages[messageIndex].statusContent = errorContent
                conversation.messages[messageIndex].thinkingStatus = 'error'
              }
            } else if (json.type === 'suggestions') {
              // 接收推薦問題
              const messageIndex = conversation.messages.length - 1
              if (conversation.messages[messageIndex] && json.suggestions) {
                conversation.messages[messageIndex].suggestions =
                  json.suggestions
              }
            } else if (json.type === 'done') {
              // 處理完成 - 設置為 end 狀態，並標記流式響應結束
              const messageIndex = conversation.messages.length - 1
              if (conversation.messages[messageIndex]) {
                conversation.messages[messageIndex].thinkingStatus = 'end'
                conversation.messages[messageIndex].isStreaming = false // 流式響應結束
              }
            }
          } catch (e) {
            console.warn('解析 JSON 失敗:', e, 'chunk:', chunk)
            // 直接當作文本處理
            if (chunk) {
              contentBuffer += chunk
              const messageIndex = conversation.messages.length - 1
              if (conversation.messages[messageIndex]) {
                conversation.messages[messageIndex].content = contentBuffer
                // 當開始收到內容時，將狀態改為 thinking
                if (
                  conversation.messages[messageIndex].thinkingStatus === 'start'
                ) {
                  conversation.messages[messageIndex].thinkingStatus =
                    'thinking'
                }
              }
            }
          }
        }

        processedCount = dataArray.length
      },
      { immediate: false, deep: true }
    )

    // 使用 useXStream 處理流式數據
    // 注意：startStream 是異步的，watch 已經在之前設置好
    try {
      await startStream({ readableStream })

      // 等待流完成後再停止監聽
      // 注意：startStream 完成後，streamData 可能還有最後的數據需要處理
      await new Promise((resolve) => setTimeout(resolve, 200))
    } finally {
      // 停止監聽
      stopWatch()

      // 如果有流錯誤，拋出
      if (streamError.value) {
        throw streamError.value
      }
    }

    // 更新對話信息
    conversation.updated_at = new Date().toISOString()
    conversation.message_count++

    // 注意：消息已經由後端在 SSE 流式響應中自動保存，無需額外調用 API

    // 如果有流錯誤，拋出
    if (streamError.value) {
      throw streamError.value
    }
  } catch (error) {
    console.error('發送消息失敗:', error)

    // 添加錯誤消息
    conversation.messages.push({
      role: 'assistant',
      content: '抱歉，發生了錯誤，請稍後再試。',
      timestamp: Date.now(),
    })
  } finally {
    isLoading.value = false
  }
}

// 加載對話列表
const loadConversations = async () => {
  try {
    // 創建超時控制器
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000) // 5 秒超時

    const response = await fetch(`${apiEndpoint}/conversations`, {
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error(`加載對話列表失敗: ${response.status}`)
    }

    const data = await response.json()
    console.log('📋 收到對話列表數據:', data)
    conversations.value = (data.conversations || [])
      .map((conv: any) => {
        const conversationId = conv.conversation_id || conv.id
        return {
          id: String(conversationId || `local-${Date.now()}-${Math.random()}`),
          title: conv.title || '新對話',
          messages: [],
          updated_at: conv.updated_at || new Date().toISOString(),
          message_count: conv.message_count || 0,
        }
      })
      .filter((conv: Conversation) => conv.id) // 過濾掉無效的對話

    console.log(
      '📋 處理後的對話列表:',
      conversations.value.map((c) => ({ id: c.id, title: c.title }))
    )

    // 如果沒有對話，創建一個新對話
    if (conversations.value.length === 0) {
      await createNewConversation()
    } else {
      // 選擇第一個對話
      currentConversationId.value = conversations.value[0].id
      await loadConversationMessages(conversations.value[0].id)
    }
  } catch (error: any) {
    // 靜默處理錯誤，不顯示錯誤訊息
    if (error.name !== 'AbortError') {
      console.warn('無法從後端加載對話列表，使用本地模式:', error.message)
    }
    // 創建一個本地對話
    await createNewConversation()
  }
}

// 初始化
// 註解掉這行可以避免初始化時發送請求
loadConversations()
</script>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: white;
}
</style>
