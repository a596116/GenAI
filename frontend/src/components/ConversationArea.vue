<template>
  <div class="conversation-area">
    <!-- 頂部標題欄 -->
    <div class="conversation-header">
      <h2>{{ conversationTitle }}</h2>
      <div class="header-actions">
        <button class="icon-btn" @click="clearConversation" title="清空對話">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- 消息列表區域 -->
    <div class="messages-container">
      <!-- 歡迎消息 -->
      <div v-if="messages.length === 0" class="welcome-message">
        <div class="welcome-icon">🤖</div>
        <h1>您好！我是 AI 助手</h1>
        <p>有什麼可以幫助您的嗎？</p>
        <div class="example-prompts">
          <button v-if="isLoadingPrompts" class="example-btn loading" disabled>
            正在載入問題建議...
          </button>
          <button
            v-else
            v-for="(example, index) in examplePrompts"
            :key="index"
            class="example-btn"
            @click="sendExample(example)"
          >
            {{ example }}
          </button>
        </div>
      </div>

      <!-- 使用 ChatList 組件 -->
      <ChatList
        v-else
        ref="chatListRef"
        :messages="messages"
        :is-loading="isLoading"
        :max-height="'100%'"
        :avatar-url="avatarUrl"
      />
    </div>

    <!-- 推薦問題（僅在最後一條消息是助手回答且不在加載中時顯示） -->
    <div v-if="shouldShowSuggestions" class="suggestions-area">
      <Prompts :items="suggestions" @item-click="handleSuggestionClick" />
    </div>

    <!-- 使用 ChatSender 組件 -->
    <div class="input-area">
      <ChatSender
        v-model="inputMessage"
        :placeholder="placeholder"
        :loading="isLoading"
        @submit="sendMessage"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed, onMounted } from 'vue'
import ChatList from './ChatList.vue'
import ChatSender from './ChatSender.vue'
import { Prompts } from 'vue-element-plus-x'
import type { IMessage } from '@/types/type'
import type { PromptsItemsProps } from 'vue-element-plus-x/types/Prompts'

interface Props {
  conversationId?: string
  conversationTitle?: string
  messages?: IMessage[]
  isLoading?: boolean
  placeholder?: string
  userName?: string
  avatarUrl?: string
}

const props = withDefaults(defineProps<Props>(), {
  conversationTitle: '新對話',
  messages: () => [],
  isLoading: false,
  placeholder: '輸入您的問題... (Shift+Enter 換行)',
  userName: 'User',
  avatarUrl: '',
})

const emit = defineEmits<{
  (e: 'send-message', message: string): void
  (e: 'clear-conversation'): void
}>()

const inputMessage = ref('')
const chatListRef = ref<InstanceType<typeof ChatList>>()

// API 端點配置（從 App.vue 或環境變數讀取）
const apiEndpoint = 'http://localhost:8000/api'

// 數據庫連接字符串
const databaseConnectionString = 'mysql://user:password@host:3306/database'

// 問題建議列表
const examplePrompts = ref<string[]>([])
const isLoadingPrompts = ref(false)

// 從數據庫獲取問題建議
const fetchDatabaseQuestions = async () => {
  isLoadingPrompts.value = true
  try {
    const response = await fetch(`${apiEndpoint}/database/questions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        connection_string: databaseConnectionString,
      }),
    })

    if (!response.ok) {
      throw new Error('獲取問題建議失敗')
    }

    const data = await response.json()
    if (data.suggestions && Array.isArray(data.suggestions)) {
      // 將問題建議轉換為字符串數組
      examplePrompts.value = data.suggestions.map(
        (s: any) => s.question || s.label || ''
      )
    }
  } catch (error) {
    console.error('獲取數據庫問題建議失敗:', error)
    // 如果獲取失敗，使用默認問題
    examplePrompts.value = [
      '顯示所有用戶資料',
      '統計每個部門的員工數量',
      '查詢最近一週的訂單記錄',
      '分析銷售趨勢',
    ]
  } finally {
    isLoadingPrompts.value = false
  }
}

// 組件掛載時獲取問題建議
onMounted(() => {
  fetchDatabaseQuestions()
})

// 判斷是否應該顯示建議（最後一條消息是助手回答，且不在加載中）
const shouldShowSuggestions = computed(() => {
  if (props.isLoading || props.messages.length === 0) {
    return false
  }
  const lastMessage = props.messages[props.messages.length - 1]
  return (
    lastMessage.role === 'assistant' &&
    !lastMessage.isStreaming &&
    lastMessage.content &&
    lastMessage.content.trim().length > 0
  )
})

// 獲取推薦問題（從最後一條助手消息中獲取後端返回的建議）
const suggestions = computed<PromptsItemsProps[]>(() => {
  // 如果沒有消息，返回空數組（不顯示建議）
  if (props.messages.length === 0) {
    return []
  }

  // 獲取最後一條助手消息
  const lastMessage = props.messages[props.messages.length - 1]

  // 如果最後一條消息有建議，使用後端返回的建議
  if (
    lastMessage.role === 'assistant' &&
    lastMessage.suggestions &&
    lastMessage.suggestions.length > 0
  ) {
    return lastMessage.suggestions.map((suggestion, index) => ({
      key: `suggestion-${index}`,
      label: suggestion,
    }))
  }

  // 如果沒有建議，返回空數組
  return []
})

const sendMessage = () => {
  const message = inputMessage.value.trim()
  if (!message || props.isLoading) return

  emit('send-message', message)
  inputMessage.value = ''

  nextTick(() => {
    scrollToBottom()
  })
}

// 處理建議點擊
const handleSuggestionClick = (item: PromptsItemsProps) => {
  if (item.label) {
    inputMessage.value = item.label
    sendMessage()
  }
}

const sendExample = (example: string) => {
  inputMessage.value = example
  sendMessage()
}

const clearConversation = () => {
  if (confirm('確定要清空此對話嗎？')) {
    emit('clear-conversation')
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    chatListRef.value?.scrollToBottom()
  })
}

// 監聽消息變化，自動滾動到底部
watch(
  () => props.messages,
  () => {
    scrollToBottom()
  },
  { deep: true }
)

// 監聽加載狀態變化，自動滾動
watch(
  () => props.isLoading,
  () => {
    scrollToBottom()
  }
)
</script>

<style scoped>
.conversation-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: white;
}

.conversation-header {
  padding: 20px 32px;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  flex-shrink: 0;
}

.conversation-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
}

.icon-btn:hover {
  background: #f5f5f5;
  border-color: #d5d5d5;
}

.messages-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.welcome-message {
  text-align: center;
  max-width: 600px;
  margin: auto;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 24px;
}

.welcome-message h1 {
  font-size: 32px;
  font-weight: 600;
  color: #333;
  margin: 0 0 12px 0;
}

.welcome-message p {
  font-size: 18px;
  color: #666;
  margin: 0 0 40px 0;
}

.example-prompts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  max-width: 600px;
  margin: 0 auto;
}

.example-btn {
  padding: 16px 20px;
  background: #f7f7f8;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #333;
  text-align: left;
}

.example-btn:hover:not(:disabled) {
  background: #ececed;
  border-color: #667eea;
  transform: translateY(-2px);
}

.example-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.suggestions-area {
  flex-shrink: 0;
  padding: 16px 32px;
  background: white;
  border-top: 1px solid #e5e5e5;
}

.input-area {
  flex-shrink: 0;
  background: white;
  border-top: 1px solid #e5e5e5;
}
</style>
