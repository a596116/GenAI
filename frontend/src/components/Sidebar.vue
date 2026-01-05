<template>
  <div class="sidebar" :class="{ collapsed: isCollapsed }">
    <!-- 側邊欄頭部 -->
    <div class="sidebar-header">
      <button v-if="!isCollapsed" class="new-chat-btn" @click="createNewConversation">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path d="M12 5v14m7-7H5" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <span>新對話</span>
      </button>
      <button class="collapse-btn" @click="toggleCollapse">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path :d="isCollapsed ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
    </div>

    <!-- 搜索框 -->
    <div v-if="!isCollapsed" class="search-box">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="11" cy="11" r="8" stroke-width="2"/>
        <path d="m21 21-4.35-4.35" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="搜索對話..." 
        @input="handleSearch"
      />
    </div>

    <!-- 對話列表 -->
    <div v-if="!isCollapsed" class="conversations-list">
      <div 
        v-for="conversation in filteredConversations" 
        :key="conversation.id"
        class="conversation-item"
        :class="{ active: conversation.id && conversation.id === currentConversationId }"
        @click="handleItemClick(conversation.id, $event)"
      >
        <div class="conversation-content">
          <div class="conversation-title">{{ conversation.title }}</div>
          <div class="conversation-time">{{ formatTime(conversation.updated_at) }}</div>
        </div>
        <button 
          class="delete-btn" 
          @click.stop.prevent="deleteConversation(conversation.id)"
          :aria-label="`刪除對話：${conversation.title}`"
          type="button"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div v-if="filteredConversations.length === 0" class="empty-state">
        <p v-if="searchQuery">找不到匹配的對話</p>
        <p v-else>還沒有對話記錄</p>
      </div>
    </div>

    <!-- 底部用戶信息 -->
    <div v-if="!isCollapsed" class="sidebar-footer">
      <div class="user-info">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-details">
          <div class="user-name">{{ userName }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Conversation {
  id: string
  title: string
  updated_at: string
  message_count: number
}

interface Props {
  conversations?: Conversation[]
  currentConversationId?: string
  userName?: string
}

const props = withDefaults(defineProps<Props>(), {
  conversations: () => [],
  currentConversationId: undefined,
  userName: 'User'
})

const emit = defineEmits<{
  (e: 'new-conversation'): void
  (e: 'select-conversation', id: string): void
  (e: 'delete-conversation', id: string): void
}>()

const isCollapsed = ref(false)
const searchQuery = ref('')

const userInitial = computed(() => {
  return props.userName.charAt(0).toUpperCase()
})

const filteredConversations = computed(() => {
  if (!props.conversations || props.conversations.length === 0) {
    return []
  }
  
  if (!searchQuery.value) {
    return props.conversations
  }
  
  return props.conversations.filter(conv => {
    if (!conv || !conv.title) return false
    return conv.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  })
})

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

const createNewConversation = () => {
  emit('new-conversation')
}

const selectConversation = (id: string | undefined) => {
  if (!id) {
    console.warn('嘗試選擇對話時 id 為空')
    return
  }
  emit('select-conversation', id)
}

const handleItemClick = (id: string | undefined, event: MouseEvent) => {
  if (!id) {
    console.warn('handleItemClick 收到空的 id')
    return
  }
  
  // 如果點擊的是刪除按鈕或其子元素，不觸發選擇
  const target = event.target as HTMLElement
  if (target.closest('.delete-btn')) {
    return
  }
  
  // 觸發選擇對話
  console.log('選擇對話:', id)
  selectConversation(id)
}

const deleteConversation = (id: string | undefined) => {
  if (!id) {
    console.warn('嘗試刪除對話時 id 為空')
    return
  }
  
  // 添加確認對話框
  if (confirm('確定要刪除此對話嗎？此操作無法復原。')) {
    emit('delete-conversation', id)
  }
}

const handleSearch = () => {
  // 搜索邏輯已通過 computed 實現
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '剛剛'
  if (diffMins < 60) return `${diffMins} 分鐘前`
  if (diffHours < 24) return `${diffHours} 小時前`
  if (diffDays < 7) return `${diffDays} 天前`
  
  return date.toLocaleDateString('zh-TW', { month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.sidebar {
  width: 280px;
  height: 100vh;
  background: #f7f7f8;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  gap: 8px;
  border-bottom: 1px solid #e5e5e5;
}

.new-chat-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  background: #5568d3;
  transform: translateY(-1px);
}

.collapse-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.collapse-btn:hover {
  background: #e5e5e5;
}

.search-box {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #e5e5e5;
}

.search-box svg {
  color: #999;
}

.search-box input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 14px;
  color: #333;
}

.search-box input::placeholder {
  color: #999;
}

.conversations-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: #e5e5e5;
}

.conversation-item.active {
  background: #667eea;
  color: white;
}

.conversation-item.active .conversation-time {
  color: rgba(255, 255, 255, 0.8);
}

.conversation-content {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.conversation-time {
  font-size: 12px;
  color: #999;
}

.delete-btn {
  display: flex;
  width: 28px;
  height: 28px;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.05);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  opacity: 0;
  flex-shrink: 0;
  z-index: 10;
}

.conversation-item:hover .delete-btn,
.conversation-item.active .delete-btn,
.conversation-item:focus-within .delete-btn {
  opacity: 1;
}

/* 移動設備上，點擊時顯示刪除按鈕 */
@media (hover: none) and (pointer: coarse) {
  .delete-btn {
    opacity: 0.5;
  }
  
  .conversation-item.active .delete-btn {
    opacity: 1;
  }
}

.conversation-item.active .delete-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.delete-btn:hover {
  background: rgba(255, 0, 0, 0.1);
  color: #ff4444;
}

.conversation-item.active .delete-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  color: white;
}

.empty-state {
  padding: 32px 16px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e5e5e5;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
}

.user-details {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 滾動條樣式 */
.conversations-list::-webkit-scrollbar {
  width: 6px;
}

.conversations-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversations-list::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.conversations-list::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>

