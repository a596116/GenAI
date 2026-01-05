<template>
  <div class="chat-header">
    <div class="header-title">
      <span class="title-icon">{{ icon }}</span>
      <span>{{ title }}</span>
    </div>
    <div class="header-actions">
      <button
        class="action-btn"
        @click="$emit('toggle-fullscreen')"
        title="全屏"
      >
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path
            d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"
          />
        </svg>
      </button>
      <button class="action-btn" @click="$emit('close')" title="關閉">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path
            d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface ChatHeaderProps {
  title?: string
  icon?: string
}

withDefaults(defineProps<ChatHeaderProps>(), {
  title: 'AI 助手',
  icon: '🤖',
})

defineEmits<{
  (e: 'close'): void
  (e: 'toggle-fullscreen'): void
}>()
</script>

<style scoped>
.chat-header {
  background: var(
    --chatbot-primary-gradient,
    linear-gradient(135deg, #409eff 0%, #337ecc 100%)
  );
  color: white;
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.title-icon {
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 8px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
