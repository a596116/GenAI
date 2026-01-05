<template>
  <div class="chat-list">
    <BubbleList
      ref="bubbleListRef"
      :list="bubbleItems"
      :maxHeight="maxHeight"
      :show-back-button="true"
    >
      <!-- 使用 header 插槽顯示 Thinking 組件（僅在流式響應中顯示） -->
      <template #header="{ item }">
        <div
          v-if="
            item.thinkingStatus && item.role === 'assistant' && item.isStreaming
          "
          class="thinking-header"
        >
          <Thinking
            :status="item.thinkingStatus!"
            :content="item.statusContent || ''"
            :auto-collapse="item.thinkingStatus === 'end'"
            button-width="200px"
            max-width="100%"
          />
        </div>
      </template>

      <!-- 內容插槽 -->
      <template #content="{ item }">
        <!-- 其他情況（歷史消息或非 end 狀態）都正常顯示內容 -->
        <XMarkdownAsync
          :markdown="item.content || ''"
          :codeXRender="selfCodeXRender"
          :class="{ 'is-left': item.role === 'assistant' }"
          :allow-html="true"
        />
      </template>
    </BubbleList>
  </div>
</template>

<script setup lang="ts">
import { IMessage, ThinkingStatus } from '@/types/type'
import { ref, computed, h } from 'vue'
import { BubbleList, Thinking, XMarkdownAsync } from 'vue-element-plus-x'
import type { BubbleListItemProps } from 'vue-element-plus-x/types/BubbleList'
import CTable from './Custom/CTable.vue'
import CChart from './Custom/CChart.vue'

type BubbleItem = BubbleListItemProps & {
  key: number
  role: 'user' | 'assistant'
  timestamp: number
  thinkingStatus?: ThinkingStatus
  thinkingContent?: string
  statusContent?: string
  isStreaming?: boolean
}

interface ChatListProps {
  messages: IMessage[]
  isLoading?: boolean
  maxHeight?: string
  avatarUrl?: string
}

const props = withDefaults(defineProps<ChatListProps>(), {
  isLoading: false,
  maxHeight: '400px',
  avatarUrl: '',
})

const bubbleListRef = ref<any>()

// 判斷是否有最終內容需要顯示
const hasFinalContent = (item: BubbleItem): boolean => {
  // 當狀態為 end 時，如果內容不為空且不是簡單的完成訊息，則顯示最終內容
  if (item.thinkingStatus === 'end' && item.content) {
    // 如果內容只是簡單的狀態訊息，不顯示最終內容
    const simpleStatusMessages = ['思考完成', '查詢完成', '正在處理您的問題...']
    return !simpleStatusMessages.includes(item.content.trim())
  }
  return false
}

// 將消息轉換為 BubbleList 所需的格式
const bubbleItems = computed<BubbleItem[]>(() => {
  const items: BubbleItem[] = props.messages.map((msg, index) => ({
    key: index,
    role: msg.role,
    placement: msg.role === 'user' ? 'end' : 'start',
    content: msg.content,
    loading: false,
    shape: 'corner',
    variant: msg.role === 'user' ? 'outlined' : 'filled',
    isMarkdown: false, // 使用 XMarkdown 組件渲染，不再使用內建 Markdown
    typing: false,
    avatar: msg.role === 'user' ? undefined : props.avatarUrl,
    avatarSize: msg.role === 'user' ? '0' : '32px',
    avatarGap: msg.role === 'user' ? '0' : '12px',
    timestamp: msg.timestamp,
    thinkingStatus: msg.thinkingStatus,
    thinkingContent: msg.thinkingStatus ? msg.content : undefined,
    statusContent: msg.statusContent,
    isStreaming: msg.isStreaming, // 標記是否為流式響應中的消息
  }))

  // 如果正在載入，添加一個載入中的消息（使用 loading 插槽顯示）
  if (props.isLoading) {
    items.push({
      key: props.messages.length,
      role: 'assistant',
      placement: 'start',
      content: '正在思考中...',
      loading: true,
      shape: 'corner',
      variant: 'filled',
      isMarkdown: false, // 使用 XMarkdown 組件渲染，不再使用內建 Markdown
      typing: false,
      avatar: props.avatarUrl,
      avatarSize: '32px',
      avatarGap: '12px',
      timestamp: Date.now(),
    })
  }

  return items
})

// 自定義代碼塊渲染對象
const selfCodeXRender = {
  // 渲染表格代碼塊
  table: (props: { raw: any }) => {
    return h(CTable, {
      code: props.raw.content,
    })
  },
  // 渲染圖表代碼塊
  chart: (props: { raw: any }) => {
    return h(CChart, {
      code: props.raw.content,
    })
  },
}

const scrollToBottom = () => {
  bubbleListRef.value?.scrollToBottom()
}

// 暴露方法給父組件
defineExpose({
  scrollToBottom,
})
</script>

<style scoped>
.chat-list {
  flex: 1;
  overflow: hidden;
  background: #f5f7fa;

  :deep(.el-bubble-content) {
    width: 100%;
    flex: 1;
  }
}

/* 自定義 BubbleList 樣式 */
.chat-list :deep(.el-bubble-list) {
  padding: 20px;
}

/* 自定義用戶消息氣泡顏色 */
.chat-list :deep(.el-bubble--outlined) {
  background: var(
    --chatbot-primary-gradient,
    linear-gradient(135deg, #409eff 0%, #337ecc 100%)
  );
  color: white;
  border: none;
}

/* 消息時間樣式 */
.message-time {
  font-size: 12px;
  color: #999;
  padding: 4px 0 0 0;
  margin-left: 44px;
}

/* Thinking 組件容器 */
.thinking-header {
  width: 100%;
  margin-bottom: 8px;
}

.loading-wrapper {
  width: 100%;
}

.final-content {
  margin-top: 12px;
}

.is-left {
  width: 100%;
}
</style>
