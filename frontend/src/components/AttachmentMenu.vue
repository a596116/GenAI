<template>
  <div class="attachment-menu">
    <button
      ref="triggerRef"
      class="attachment-trigger"
      type="button"
      :aria-expanded="isOpen"
      aria-haspopup="true"
      @click.stop="togglePanel"
    >
      <slot name="icon">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
        </svg>
      </slot>
    </button>

    <Teleport to="body">
      <Transition name="menu-fade">
        <div
          v-if="isOpen"
          ref="panelRef"
          class="attachment-panel"
          :style="panelStyle"
          role="menu"
          @click.stop
        >
          <button
            type="button"
            class="attachment-item"
            @click="handleMediaClick"
          >
            <svg
              class="attachment-item__icon"
              viewBox="0 0 24 24"
              width="18"
              height="18"
            >
              <path
                fill="currentColor"
                d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"
              />
            </svg>
            <span class="attachment-item__text">新增照片和檔案</span>
          </button>

          <button
            type="button"
            class="attachment-item"
            @click="handleCodeFileClick"
          >
            <svg
              class="attachment-item__icon"
              viewBox="0 0 24 24"
              width="18"
              height="18"
            >
              <path
                fill="currentColor"
                d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"
              />
            </svg>
            <span class="attachment-item__text">代碼文件</span>
          </button>

          <button
            type="button"
            class="attachment-item"
            @click="handleCodeFolderClick"
          >
            <svg
              class="attachment-item__icon"
              viewBox="0 0 24 24"
              width="18"
              height="18"
            >
              <path
                fill="currentColor"
                d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"
              />
            </svg>
            <span class="attachment-item__text">代碼文件夾</span>
          </button>
        </div>
      </Transition>
    </Teleport>

    <input
      ref="mediaInputRef"
      class="attachment-input"
      type="file"
      :accept="mediaAccept"
      :multiple="allowMultiple"
      @change="onFilesChange('media', $event)"
    />
    <input
      ref="codeInputRef"
      class="attachment-input"
      type="file"
      :accept="codeAccept"
      :multiple="allowMultiple"
      @change="onFilesChange('code-file', $event)"
    />
    <input
      ref="folderInputRef"
      class="attachment-input"
      type="file"
      webkitdirectory
      directory
      @change="onFilesChange('code-folder', $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, toRefs, nextTick } from 'vue'
import type { AttachmentType, IAttachmentPayload } from '@/types/type'

interface AttachmentMenuProps {
  mediaAccept?: string
  codeAccept?: string
  allowMultiple?: boolean
}

const props = withDefaults(defineProps<AttachmentMenuProps>(), {
  mediaAccept: 'image/*,.pdf,.doc,.docx,.txt',
  codeAccept:
    '.js,.ts,.tsx,.jsx,.py,.java,.go,.cpp,.c,.cs,.rb,.php,.rs,.swift,.kt,.scala,.sh,.json,.yaml,.yml,.md',
  allowMultiple: true,
})
const { mediaAccept, codeAccept, allowMultiple } = toRefs(props)

const emit = defineEmits<{
  (e: 'select', payload: IAttachmentPayload): void
}>()

const isOpen = ref(false)
const panelRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLButtonElement | null>(null)
const mediaInputRef = ref<HTMLInputElement | null>(null)
const codeInputRef = ref<HTMLInputElement | null>(null)
const folderInputRef = ref<HTMLInputElement | null>(null)

const panelStyle = ref({
  top: '0px',
  left: '0px',
})

const togglePanel = async () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    await nextTick()
    updatePanelPosition()
  }
}

const closePanel = () => {
  isOpen.value = false
}

const updatePanelPosition = () => {
  if (!triggerRef.value || !panelRef.value) return

  const triggerRect = triggerRef.value.getBoundingClientRect()
  const panelRect = panelRef.value.getBoundingClientRect()
  const panelWidth = panelRect.width || 200
  const panelHeight = panelRect.height || 160
  const spacing = 10

  // 面板顯示在按鈕上方，間距 2px
  let top = triggerRect.top - panelHeight - spacing
  let left = triggerRect.left

  // 如果上方空間不夠，顯示在下方，間距 2px
  if (top < 16) {
    top = triggerRect.bottom + spacing
  }

  if (left + panelWidth > window.innerWidth) {
    left = window.innerWidth - panelWidth - 16
  }

  if (left < 16) {
    left = 16
  }

  panelStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
  }
}

const handleOutsideClick = (event: MouseEvent) => {
  if (!isOpen.value) return
  const target = event.target as Node
  const clickedInsidePanel = panelRef.value?.contains(target)
  const clickedTrigger = triggerRef.value?.contains(target)

  if (!clickedInsidePanel && !clickedTrigger) {
    closePanel()
  }
}

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && isOpen.value) {
    closePanel()
  }
}

onMounted(() => {
  document.addEventListener('click', handleOutsideClick)
  document.addEventListener('keydown', handleEscape)
  window.addEventListener('resize', updatePanelPosition)
  window.addEventListener('scroll', updatePanelPosition, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
  document.removeEventListener('keydown', handleEscape)
  window.removeEventListener('resize', updatePanelPosition)
  window.removeEventListener('scroll', updatePanelPosition, true)
})

const emitSelection = (type: AttachmentType, files: File[]) => {
  emit('select', { type, files })
  closePanel()
}

const handleMediaClick = () => {
  mediaInputRef.value?.click()
}

const handleCodeFileClick = () => {
  codeInputRef.value?.click()
}

const handleCodeFolderClick = () => {
  folderInputRef.value?.click()
}

const onFilesChange = (type: AttachmentType, event: Event) => {
  const input = event.target as HTMLInputElement
  const files = input.files ? Array.from(input.files) : []
  if (files.length > 0) {
    emitSelection(type, files)
  }
  input.value = ''
}
</script>

<style scoped>
.attachment-menu {
  position: relative;
  display: inline-block;
}

/* 觸發按鈕 */
.attachment-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #666;
  cursor: pointer;
  transition: all 0.2s ease;
}

.attachment-trigger:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

/* 面板 */
.attachment-panel {
  position: fixed;
  min-width: 200px;
  background: #ffffff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  z-index: 9999;
  padding: 6px;
}

/* 選項按鈕 */
.attachment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #333;
  cursor: pointer;
  transition: background 0.15s ease;
  text-align: left;
  font-size: 14px;
}

.attachment-item:hover {
  background: rgba(0, 0, 0, 0.05);
}

.attachment-item:active {
  background: rgba(0, 0, 0, 0.08);
}

.attachment-item__icon {
  flex-shrink: 0;
  color: #666;
}

.attachment-item__text {
  flex: 1;
  white-space: nowrap;
}

/* 隱藏的文件輸入 */
.attachment-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* 動畫 */
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
}

.menu-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 響應式 */
@media (max-width: 640px) {
  .attachment-panel {
    position: fixed !important;
    top: auto !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    width: 100% !important;
    min-width: 100% !important;
    border-radius: 16px 16px 0 0;
  }

  .menu-fade-enter-from {
    transform: translateY(100%);
  }

  .menu-fade-leave-to {
    transform: translateY(100%);
  }
}
</style>
