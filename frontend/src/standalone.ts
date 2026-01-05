/**
 * 獨立版本入口文件
 * 提供簡化的 API，無需手動創建 Vue 應用
 */
import { createApp, h, nextTick } from 'vue'
import Chatbot from './components/Chatbot.vue'

interface MountOptions {
  title?: string
  placeholder?: string
  position?: {
    bottom?: string
    right?: string
    left?: string
  }
  apiEndpoint?: string
  apiKey?: string
  token?: string
  tokenHeaderName?: string
  width?: string
  height?: string
  primaryColor?: string | { from: string; to: string }
  onMessageSent?: (message: string) => void
  onMessageReceived?: (message: string) => void
}

/**
 * 組件實例類型（包含暴露的方法）
 */
interface ChatbotInstance {
  setToken: (token: string | undefined) => void
  destroy: () => void
}

/**
 * 簡化的掛載函數
 * @param options - 配置選項
 * @returns 組件實例，包含 setToken 和 destroy 等方法
 */
function mount(options: MountOptions = {}): ChatbotInstance {
  const { onMessageSent, onMessageReceived, ...props } = options

  // 自動創建一個容器元素
  const container = document.createElement('div')
  container.id = 'chatbot-container'
  // 將容器添加到 body
  document.body.appendChild(container)

  // 使用 ref 來保存組件實例引用（作為函數形式）
  let chatbotInstance: any = null

  const app = createApp({
    render() {
      return h(Chatbot, {
        ref: (el: any) => {
          chatbotInstance = el
        },
        ...props,
        onMessageSent,
        onMessageReceived,
      })
    },
  })

  // 掛載應用
  app.mount(container)

  // 擴展實例，添加 destroy 方法
  const extendedInstance: ChatbotInstance = {
    setToken: (token: string | undefined) => {
      // 確保組件實例已初始化
      if (chatbotInstance && typeof chatbotInstance.setToken === 'function') {
        chatbotInstance.setToken(token)
      } else {
        // 如果實例尚未初始化，等待下一個 tick
        nextTick(() => {
          if (
            chatbotInstance &&
            typeof chatbotInstance.setToken === 'function'
          ) {
            chatbotInstance.setToken(token)
          }
        })
      }
    },
    destroy: () => {
      app.unmount()
      if (container.parentNode) {
        container.parentNode.removeChild(container)
      }
    },
  }

  return extendedInstance
}

export default {
  mount,
}

// 掛載到 window（用於 CDN 引入）
if (typeof window !== 'undefined') {
  ;(window as any).HaoChatbot = { mount }
}
