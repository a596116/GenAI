<template>
  <div class="hao-chatbot-wrapper" :style="themeStyle">
    <!-- 浮動按鈕 -->
    <transition name="fade">
      <div
        v-if="!isOpen"
        class="hao-chatbot-button"
        @click="toggleChat"
        :style="{ ...buttonStyle, ...themeStyle }"
      >
        <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path
            d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"
          />
        </svg>
      </div>
    </transition>

    <!-- 聊天視窗 -->
    <transition name="slide-up">
      <div
        v-if="isOpen"
        class="hao-chatbot-container"
        :class="{ 'is-fullscreen': isFullscreen }"
        :style="{ ...containerStyle, ...themeStyle }"
      >
        <!-- 標題欄 -->
        <ChatHeader
          :title="title"
          @close="toggleChat"
          @toggle-fullscreen="toggleFullscreen"
        />

        <div class="chatbot-content">
          <!-- 聊天內容區域 -->
          <ChatList
            v-if="messages.length > 0"
            ref="chatListRef"
            :messages="messages"
            :is-loading="isLoading"
            :max-height="'100%'"
            :avatar-url="avatarUrl"
          />

          <div v-else class="chatbot-content-welcome">
            <Typewriter
              content="您好！我是 AI 助手，有什麼可以幫助您的嗎？"
              typing
            />
          </div>

          <!-- 輸入區域 -->
          <ChatSender
            ref="chatSenderRef"
            v-model="inputMessage"
            :placeholder="placeholder"
            :loading="isLoading"
            @submit="handleSend"
            @cancel="handleCancel"
            @attachment="handleAttachment"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onUnmounted } from 'vue'
import ChatHeader from './ChatHeader.vue'
import ChatList from './ChatList.vue'
import ChatSender from './ChatSender.vue'
import { IChatbotProps, IMessage, IAttachmentPayload, ThinkingStatus } from '@/types/type'
import { DEFAULT_AVATAR_SVG } from '@/utils/constants'
import { Typewriter, useXStream } from 'vue-element-plus-x'

const props = withDefaults(defineProps<IChatbotProps>(), {
  title: 'AI 助手',
  placeholder: '輸入訊息... (Shift+Enter 換行)',
  position: () => ({ bottom: '20px', right: '20px' }),
  width: '400px',
  height: '600px',
  primaryColor: '#409EFF', // 默認藍色
  tokenHeaderName: 'Authorization', // 默認使用 Authorization header
})

const avatarUrl = computed(() => props.avatarUrl || DEFAULT_AVATAR_SVG)

const emit = defineEmits<{
  (e: 'message-sent', message: string): void
  (e: 'message-received', message: string): void
  (e: 'attachment-selected', payload: IAttachmentPayload): void
}>()

const isOpen = ref(false)
const isFullscreen = ref(false)
const inputMessage = ref('')
const messages = ref<IMessage[]>([
  // {
  //   role: 'assistant',
  //   content: '您好！我是 AI 助手，有什麼可以幫助您的嗎？',
  //   timestamp: Date.now(),
  // },
])
const isLoading = ref(false)
const chatListRef = ref<any>()
const chatSenderRef = ref<any>()
const currentToken = ref<string | undefined>(props.token)

// 使用 useXStream 處理 SSE 流式請求
const {
  startStream,
  cancel: cancelStream,
  data: streamData,
  error: streamError,
  isLoading: isStreaming,
} = useXStream()

const buttonStyle = computed(() => ({
  bottom: props.position.bottom,
  right: props.position.right,
  left: props.position.left,
}))

const containerStyle = computed(() => {
  const baseStyle: any = {
    width: props.width,
    height: props.height,
  }

  if (props.position.right) {
    baseStyle.right = props.position.right
  }
  if (props.position.left) {
    baseStyle.left = props.position.left
  }
  if (props.position.bottom) {
    baseStyle.bottom = props.position.bottom
  }

  if (isFullscreen.value) {
    baseStyle.width = '100vw'
    baseStyle.height = '100vh'
    baseStyle.bottom = '0'
    baseStyle.right = '0'
    baseStyle.borderRadius = '0'
  }

  return baseStyle
})

// 主題顏色樣式
const themeStyle = computed(() => {
  const primary = props.primaryColor

  // 如果是字符串，使用單色（自動生成漸變）
  if (typeof primary === 'string') {
    // 將顏色轉換為漸變（稍微變暗作為結束色）
    const toColor = darkenColor(primary, 15)
    return {
      '--chatbot-primary': primary,
      '--chatbot-primary-from': primary,
      '--chatbot-primary-to': toColor,
      '--chatbot-primary-gradient': `linear-gradient(135deg, ${primary} 0%, ${toColor} 100%)`,
    }
  }

  // 如果是對象，使用自定義漸變
  return {
    '--chatbot-primary': primary.from,
    '--chatbot-primary-from': primary.from,
    '--chatbot-primary-to': primary.to,
    '--chatbot-primary-gradient': `linear-gradient(135deg, ${primary.from} 0%, ${primary.to} 100%)`,
  }
})

// 將顏色變暗的工具函數
const darkenColor = (color: string, percent: number): string => {
  // 如果是十六進制顏色
  if (color.startsWith('#')) {
    const num = parseInt(color.replace('#', ''), 16)
    const r = Math.max(0, ((num >> 16) & 0xff) - percent)
    const g = Math.max(0, ((num >> 8) & 0xff) - percent)
    const b = Math.max(0, (num & 0xff) - percent)
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`
  }
  // 如果是其他格式，返回原色
  return color
}

const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (!isOpen.value) {
    isFullscreen.value = false
  }
  if (isOpen.value) {
    nextTick(() => {
      scrollToBottom()
      chatSenderRef.value?.focus('end')
    })
  }
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  // 等待過渡動畫完成後重新計算並滾動
  nextTick(() => {
    setTimeout(() => {
      scrollToBottom()
    }, 500) // 配合 CSS 過渡時間
  })
}

const handleCancel = () => {
  // 中止正在進行的流式請求
  if (isStreaming.value) {
    cancelStream()
  }
  isLoading.value = false
}

const handleAttachment = (payload: IAttachmentPayload) => {
  emit('attachment-selected', payload)
}

const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || isLoading.value) return

  // 添加用戶消息
  messages.value.push({
    role: 'user',
    content: message,
    timestamp: Date.now(),
  })

  inputMessage.value = ''
  emit('message-sent', message)

  nextTick(() => {
    scrollToBottom()
  })

  // 發送 API 請求
  isLoading.value = true

  try {
    await callApiSSE(message)
  } catch (error: any) {
    console.error('發送消息失敗:', error)
    messages.value.push({
      role: 'assistant',
      content: '抱歉，發生了錯誤，請稍後再試。',
      timestamp: Date.now(),
    })
  } finally {
    isLoading.value = false
  }
}

// SSE 模式 API 調用（使用 useXStream）
const callApiSSE = async (message: string): Promise<void> => {
  if (!props.apiEndpoint) {
    throw new Error('API endpoint 未設置')
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }

  // 添加 token（優先使用 currentToken，如果沒有則使用 props.token）
  const token = currentToken.value || props.token
  if (token) {
    // 如果 tokenHeaderName 是 'Authorization'，自動添加 'Bearer ' 前綴
    if (
      props.tokenHeaderName === 'Authorization' &&
      !token.startsWith('Bearer ')
    ) {
      headers[props.tokenHeaderName] = `Bearer ${token}`
    } else {
      headers[props.tokenHeaderName] = token
    }
  }

  // 如果有 apiKey，也添加到 headers（用於向後兼容）
  if (props.apiKey) {
    headers['Authorization'] = `Bearer ${props.apiKey}`
  }

  const response = await fetch(props.apiEndpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      question: message, // 後端期望的欄位名稱是 question
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(
      `API 請求失敗: ${response.status} ${response.statusText} - ${errorText}`
    )
  }

  const readableStream = response.body
  if (!readableStream) {
    throw new Error('無法讀取響應流')
  }

  // 添加空的助手消息，用於流式更新
  const assistantMessageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    timestamp: Date.now(),
    thinkingStatus: 'start',
    isStreaming: true, // 標記為流式響應中的消息
  })

  // 記錄已處理的數據量，避免重複處理
  let processedCount = 0
  let contentBuffer = ''

  // 監聽 streamData 的變化來逐步更新內容
  const stopWatch = watch(
    streamData,
    (newData) => {
      if (!newData.length) return

      // 只處理新增的數據
      for (let index = processedCount; index < newData.length; index++) {
        const chunk = newData[index].data

        // 先檢查是否是結束標記，避免不必要的 JSON 解析錯誤
        const trimmedChunk = chunk?.trim()
        if (trimmedChunk === '[DONE]') {
          // 數據接收完畢 - 設置為 end 狀態，並標記流式響應結束
          messages.value[assistantMessageIndex].content =
            contentBuffer || '查詢完成'
          messages.value[assistantMessageIndex].thinkingStatus = 'end'
          messages.value[assistantMessageIndex].isStreaming = false // 流式響應結束
          continue
        }

        try {
          const json = JSON.parse(chunk)

          // 處理不同類型的數據
          if (json.type === 'explanation' && json.content) {
            // 解釋內容（包括 SQL 和查詢結果的 markdown 表格）
            contentBuffer += json.content
            // 更新消息內容
            messages.value[assistantMessageIndex].content = contentBuffer
            // 當開始收到解釋內容時，將狀態改為 thinking
            if (messages.value[assistantMessageIndex].thinkingStatus === 'start') {
              messages.value[assistantMessageIndex].thinkingStatus = 'thinking'
            }
            nextTick(() => {
              scrollToBottom()
            })
          } else if (json.type === 'status') {
            // 狀態訊息 - 根據 status.type 映射到 Thinking 狀態
            const statusType = json.status?.type || 'working'
            const statusContent = json.status?.content || json.content || '正在處理中...'
            
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
            
            messages.value[assistantMessageIndex].content = statusContent
            messages.value[assistantMessageIndex].thinkingStatus = thinkingStatus
            nextTick(() => {
              scrollToBottom()
            })
          } else if (json.type === 'error') {
            // 錯誤訊息 - 設置為 error 狀態
            messages.value[
              assistantMessageIndex
            ].content = json.error || '發生錯誤'
            messages.value[assistantMessageIndex].thinkingStatus = 'error'
            nextTick(() => {
              scrollToBottom()
            })
          } else if (json.type === 'done') {
            // 處理完成 - 設置為 end 狀態，並標記流式響應結束
            messages.value[assistantMessageIndex].thinkingStatus = 'end'
            messages.value[assistantMessageIndex].isStreaming = false // 流式響應結束
          } else {
            // 支持傳統格式作為後備
            let content = ''

            // 1. OpenAI 格式
            if (json.choices && json.choices[0]?.delta?.content) {
              content = json.choices[0].delta.content
            }
            // 2. content 欄位
            else if (json.content && !json.type) {
              content = json.content
            }
            // 3. delta.content 格式
            else if (json.delta?.content) {
              content = json.delta.content
            }
            // 4. text 欄位
            else if (json.text) {
              content = json.text
            }
            // 5. message 欄位
            else if (json.message) {
              content = json.message
            }
            // 6. reply 欄位
            else if (json.reply) {
              content = json.reply
            }

            if (content) {
              contentBuffer += content
              messages.value[assistantMessageIndex].content = contentBuffer
              // 當開始收到內容時，將狀態改為 thinking
              if (messages.value[assistantMessageIndex].thinkingStatus === 'start') {
                messages.value[assistantMessageIndex].thinkingStatus = 'thinking'
              }
              nextTick(() => {
                scrollToBottom()
              })
            }
          }
        } catch (e) {
          // 直接當作文本處理
          if (chunk) {
            contentBuffer += chunk
            messages.value[assistantMessageIndex].content = contentBuffer
            nextTick(() => {
              scrollToBottom()
            })
          }
        }
      }

      processedCount = newData.length
    },
    { immediate: false }
  )

  // 使用 useXStream 處理流式數據
  await startStream({ readableStream })

  // 停止監聽
  stopWatch()

  // 發送最終消息事件
  const finalResponse = messages.value[assistantMessageIndex].content
  emit('message-received', finalResponse)

  // 如果有流錯誤，拋出
  if (streamError.value) {
    throw streamError.value
  }
}

// 暴露方法供外部調用，用於動態設置 token
const setToken = (token: string | undefined) => {
  currentToken.value = token
}

// 暴露方法
defineExpose({
  setToken,
})

const scrollToBottom = () => {
  nextTick(() => {
    chatListRef.value?.scrollToBottom()
  })
}

// 監聽全屏狀態，控制 body 滾動和重新計算高度
watch(isFullscreen, (newValue) => {
  if (newValue) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }

  // 等待過渡動畫完成後重新計算聊天列表高度
  nextTick(() => {
    setTimeout(() => {
      if (chatListRef.value) {
        chatListRef.value.scrollToBottom?.()
      }
    }, 500)
  })
})

// 組件卸載時恢復 body 滾動
onUnmounted(() => {
  document.body.style.overflow = ''
})
</script>

<style scoped>
.hao-chatbot-wrapper {
  position: fixed;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, sans-serif;
}

/* 浮動按鈕 */
.hao-chatbot-button {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(
    --chatbot-primary-gradient,
    linear-gradient(135deg, #409eff 0%, #337ecc 100%)
  );
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
  position: fixed;
}

.hao-chatbot-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

/* 聊天容器 */
.hao-chatbot-container {
  position: fixed;
  background: #f5f7fa;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.hao-chatbot-container.is-fullscreen {
  border-radius: 0;
  box-shadow: none;
}

/* 動畫 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.8);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 響應式設計 */
@media (max-width: 768px) {
  .hao-chatbot-container {
    width: calc(100vw - 32px) !important;
    height: calc(100vh - 100px) !important;
    left: 16px !important;
    right: 16px !important;
    bottom: 16px !important;
  }
}

.chatbot-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  flex-direction: column;
  /* height: 100%; */
  justify-content: center;
}

.chatbot-content-welcome {
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px;
  font-size: 16px;
}
</style>
