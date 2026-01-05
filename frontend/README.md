# GenAI Chatbot 前端

這是一個基於 Vue 3 + TypeScript + Vite 構建的智能聊天機器人前端應用。

## 功能特點

- 💬 **智能對話**: 與 AI 助手進行自然語言對話
- 📊 **數據查詢**: 自動將自然語言轉換為 SQL 查詢並顯示結果
- 🎨 **現代化 UI**: 漂亮的漸變設計和流暢的動畫效果
- 📱 **響應式設計**: 支援桌面和移動設備
- 🔄 **實時更新**: 即時顯示查詢結果和 SQL 語句

## 技術棧

- **Vue 3**: 漸進式 JavaScript 框架
- **TypeScript**: 類型安全的 JavaScript 超集
- **Vite**: 快速的前端構建工具
- **CSS3**: 現代化樣式和動畫

## 快速開始

### 1. 安裝依賴

```bash
npm install
# 或使用 pnpm
pnpm install
```

### 2. 配置 API 端點

在 `src/App.vue` 中修改 API 端點（如果需要）：

```typescript
const apiEndpoint = ref('http://localhost:8000/api/chat')
```

### 3. 啟動開發服務器

```bash
npm run dev
# 或使用 pnpm
pnpm dev
```

應用將在 `http://localhost:5173` 上運行。

### 4. 構建生產版本

```bash
npm run build
# 或使用 pnpm
pnpm build
```

構建產物將生成在 `dist` 目錄。

## 項目結構

```
frontend/
├── src/
│   ├── components/
│   │   ├── SimpleChatbot.vue    # 簡化的聊天機器人組件
│   │   ├── Chatbot.vue          # 完整的聊天機器人組件（支援 SSE）
│   │   ├── ChatHeader.vue       # 聊天標題欄
│   │   ├── ChatList.vue         # 聊天消息列表
│   │   └── ChatSender.vue       # 消息輸入框
│   ├── types/
│   │   └── type.ts              # TypeScript 類型定義
│   ├── utils/
│   │   └── constants.ts         # 常量定義
│   ├── App.vue                  # 主應用組件
│   ├── main.ts                  # 應用入口
│   └── style.css                # 全局樣式
├── index.html                   # HTML 模板
├── package.json                 # 項目配置
├── tsconfig.json                # TypeScript 配置
└── vite.config.ts               # Vite 配置
```

## 使用說明

### 基本使用

1. 確保後端服務已啟動（默認在 `http://localhost:8000`）
2. 啟動前端開發服務器
3. 在瀏覽器中打開 `http://localhost:5173`
4. 點擊右下角的聊天按鈕開始對話

### 示例查詢

- "顯示所有用戶資料"
- "統計每個部門的員工數量"
- "查詢最近一週的訂單記錄"
- "分析銷售趨勢"

### 組件說明

#### SimpleChatbot

簡化版的聊天機器人組件，適用於標準的 REST API。

**Props:**
- `title`: 聊天窗口標題（默認: "AI 助手"）
- `placeholder`: 輸入框佔位符
- `apiEndpoint`: 後端 API 端點（必填）

**特點:**
- 支援顯示 SQL 查詢語句
- 支援表格形式顯示查詢結果
- 支援錯誤提示
- 支援全屏模式
- 自動滾動到最新消息

#### Chatbot

完整版的聊天機器人組件，支援 SSE（Server-Sent Events）流式響應。

**Props:**
- `title`: 聊天窗口標題
- `placeholder`: 輸入框佔位符
- `apiEndpoint`: 後端 API 端點
- `position`: 浮動按鈕位置
- `width`: 聊天窗口寬度
- `height`: 聊天窗口高度
- `primaryColor`: 主題顏色（支援單色或漸變）
- `avatarUrl`: AI 助手頭像 URL

## 開發指南

### 自定義樣式

修改 `src/style.css` 或組件內的 `<style scoped>` 區塊來自定義樣式。

### 修改主題顏色

在 `App.vue` 中修改漸變顏色：

```vue
<style scoped>
.app-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
```

### 添加新功能

1. 在 `src/components/` 目錄下創建新組件
2. 在 `App.vue` 中引入並使用
3. 更新類型定義（如需要）

## 故障排除

### 無法連接到後端

確保：
1. 後端服務已啟動
2. API 端點配置正確
3. CORS 設置正確（後端已配置允許所有來源）

### 樣式顯示異常

清除瀏覽器緩存並重新加載頁面。

### TypeScript 錯誤

運行以下命令重新安裝依賴：

```bash
rm -rf node_modules package-lock.json
npm install
```

## 瀏覽器支援

- Chrome（推薦）
- Firefox
- Safari
- Edge

建議使用最新版本的現代瀏覽器以獲得最佳體驗。

## 授權

MIT License

## 聯繫方式

如有問題或建議，請聯繫開發團隊。
