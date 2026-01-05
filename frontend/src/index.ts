import type { App, Plugin } from 'vue'
import { HaoChatbot } from './components'

// 導出組件和類型
export * from './components'
export * from './types/type'

// 為組件添加 install 方法，支持作為插件使用
const HaoChatbotWithInstall = Object.assign(HaoChatbot, {
  install: (app: App) => {
    app.component('HaoChatbot', HaoChatbot)
  },
}) as typeof HaoChatbot & Plugin

// 默認導出（支持 import HaoChatbot from 'hao-chatbot'）
export default HaoChatbotWithInstall

// 支持 UMD 格式的全局註冊
if (typeof window !== 'undefined' && (window as any).Vue) {
  ;(window as any).HaoChatbot = HaoChatbotWithInstall
}
