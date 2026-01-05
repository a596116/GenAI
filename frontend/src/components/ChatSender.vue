<template>
  <div class="chat-sender" :class="{ 'is-loading': loading }">
    <Sender
      ref="senderRef"
      v-model="messageText"
      :placeholder="placeholder"
      :loading="loading"
      :submit-btn-disabled="!messageText.trim()"
      clearable
      allow-speech
      variant="updown"
      @submit="handleSubmit"
      @cancel="handleCancel"
      @recordingChange="handleRecordingChange"
    >
      <template #prefix>
        <AttachmentMenu @select="handleAttachmentSelect" />
      </template>
    </Sender>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { Sender } from 'vue-element-plus-x'
import AttachmentMenu from './AttachmentMenu.vue'
import type { IAttachmentPayload } from '@/types/type'

interface ChatSenderProps {
  modelValue: string
  placeholder?: string
  loading?: boolean
}

const props = withDefaults(defineProps<ChatSenderProps>(), {
  placeholder: '輸入訊息... (Shift+Enter 換行)',
  loading: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'submit'): void
  (e: 'cancel'): void
  (e: 'attachment', payload: IAttachmentPayload): void
}>()

const senderRef = ref<any>()
const messageText = ref(props.modelValue)

// 同步 v-model
watch(
  () => props.modelValue,
  (newValue) => {
    messageText.value = newValue
  }
)

watch(messageText, (newValue) => {
  emit('update:modelValue', newValue)
})

// 語音識別相關
let recognition: any = null
const isRecognizing = ref(false)
let baseText = '' // 開始識別時的基礎文本
let finalText = '' // 已確認的最終文本
let interimText = '' // 當前的臨時識別文本

// 初始化語音識別
const initSpeechRecognition = () => {
  const SpeechRecognition =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition

  if (!SpeechRecognition) {
    console.warn('⚠️ 您的瀏覽器不支援語音識別功能')
    return
  }

  recognition = new SpeechRecognition()

  // 連續識別模式
  recognition.continuous = true

  // 返回即時結果
  recognition.interimResults = true

  // 最大候選結果數
  recognition.maxAlternatives = 1

  // 開始識別事件
  recognition.onstart = () => {
    console.log('🎤 語音識別已開始')
    isRecognizing.value = true
    baseText = messageText.value
    finalText = ''
    interimText = ''
  }

  // 識別結果事件
  recognition.onresult = (event: any) => {
    let newInterimTranscript = ''
    let newFinalTranscript = ''

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript
      if (event.results[i].isFinal) {
        newFinalTranscript += transcript
      } else {
        newInterimTranscript += transcript
      }
    }

    if (newFinalTranscript) {
      finalText += (finalText ? ' ' : '') + newFinalTranscript
      interimText = ''
      console.log('✅ 識別完成：', newFinalTranscript)
    }

    if (newInterimTranscript) {
      interimText = newInterimTranscript
      console.log('🔄 即時識別：', newInterimTranscript)
    } else {
      interimText = ''
    }

    const parts = [baseText, finalText, interimText].filter(Boolean)
    messageText.value = parts.join(' ').trim()
  }

  // 識別結束事件
  recognition.onend = () => {
    console.log('⏹️ 語音識別已結束')
    isRecognizing.value = false

    if (interimText) {
      finalText += (finalText ? ' ' : '') + interimText
      interimText = ''
    }

    const parts = [baseText, finalText].filter(Boolean)
    messageText.value = parts.join(' ').trim()

    baseText = ''
    finalText = ''
    interimText = ''
  }

  // 錯誤處理
  recognition.onerror = (event: any) => {
    console.error('❌ 語音識別錯誤：', event.error)
    isRecognizing.value = false

    switch (event.error) {
      case 'no-speech':
        console.warn('未檢測到語音輸入')
        break
      case 'audio-capture':
        console.warn('無法捕獲音頻，請檢查麥克風')
        break
      case 'not-allowed':
        console.warn('麥克風權限被拒絕')
        break
      default:
        console.warn('語音識別發生錯誤')
    }
  }

  console.log('✅ 語音識別初始化完成')
}

// 處理語音識別狀態變化
const handleRecordingChange = (recording: boolean) => {
  console.log('🎙️ 錄音狀態變化：', recording ? '開始' : '結束')

  if (!recognition) {
    console.warn('⚠️ 語音識別未初始化')
    return
  }

  if (recording) {
    try {
      recognition.start()
    } catch (error) {
      console.error('啟動語音識別失敗：', error)
    }
  } else {
    try {
      if (isRecognizing.value) {
        recognition.stop()
      }
    } catch (error) {
      console.error('停止語音識別失敗：', error)
    }
  }
}

const handleSubmit = () => {
  emit('submit')
}

const handleCancel = () => {
  emit('cancel')
}

const handleAttachmentSelect = (payload: IAttachmentPayload) => {
  emit('attachment', payload)
}

const focus = (position: 'start' | 'end' | 'all' = 'end') => {
  senderRef.value?.focus(position)
}

// 初始化
onMounted(() => {
  initSpeechRecognition()
})

// 暴露方法給父組件
defineExpose({
  focus,
})
</script>

<style scoped>
.chat-sender {
  padding: 8px;
  background: #f5f7fa;
  /* border-top: 1px solid #e8e8e8; */
}

/* 自定義 Sender 組件樣式 */
.chat-sender :deep(.el-sender) {
  width: 100%;
  /* background-color: #fff; */
}

.chat-sender :deep(.el-sender__inner) {
  border-radius: 12px;
  border-color: #e8e8e8;
}

.chat-sender :deep(.el-sender__inner:focus-within) {
  border-color: var(--chatbot-primary, #409eff);
}

.chat-sender :deep(.el-sender__submit-btn) {
  width: 32px;
  height: 32px;
  min-width: 32px;
  padding: 0;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #666;
  transition: all 0.2s ease;
}

.chat-sender :deep(.el-sender__submit-btn:hover:not(:disabled)) {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
  transform: none;
  box-shadow: none;
}

.chat-sender :deep(.el-sender__submit-btn:active:not(:disabled)) {
  transform: scale(0.96);
}

.chat-sender :deep(.el-sender__submit-btn:disabled) {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 統一按鈕風格 - 改成和 attachment 按鈕一樣的樣式 */
.chat-sender :deep(.el-send-button .el-button) {
  width: 32px;
  height: 32px;
  min-width: 32px;
  padding: 0;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #666;
  transition: all 0.2s ease;
}
.chat-sender:not(.is-loading) :deep(.el-send-button:first-child .el-button) {
  background: var(
    --chatbot-primary-gradient,
    linear-gradient(135deg, #409eff 0%, #337ecc 100%)
  );
  color: #fff;
}

.chat-sender
  :deep(.el-send-button:not(:first-child) .el-button:hover:not(:disabled)) {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
  /* transform: none; */
  box-shadow: none;
}

.chat-sender
  :deep(.el-send-button:first-child .el-button:hover:not(:disabled)) {
  /* background: var(
    --chatbot-primary-gradient,
    linear-gradient(135deg, #409eff 0%, #337ecc 100%)
  ); */
  opacity: 0.9;
  color: #fff;
}

.chat-sender :deep(.el-button.is-circle:active:not(:disabled)) {
  transform: scale(0.96);
}

.chat-sender :deep(.el-button.is-circle:disabled) {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
