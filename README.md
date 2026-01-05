# GenAI Chatbot - 智能數據查詢助手

一個完整的全棧應用，使用 FastAPI、Vanna AI 和 Vue 3 建立的智能 SQL 查詢助手，能將自然語言轉換為 SQL 查詢並執行。

## 功能特點

### 後端功能
- 🤖 **自然語言轉 SQL**: 使用 Vanna AI 和 OpenAI GPT 將自然語言問題轉換為準確的 SQL 查詢
- ⚡ **高效能 API**: 基於 FastAPI 構建，提供快速的非同步 API
- 🗄️ **MySQL 支援**: 連接 MySQL 數據庫並執行查詢
- 📚 **模型訓練**: 支援添加 DDL、文檔和 SQL 範例來訓練模型
- 📝 **自動文檔**: FastAPI 自動生成 Swagger UI 互動式 API 文檔
- 🔒 **類型安全**: 使用 Pydantic 進行資料驗證
- 💬 **對話管理**: 支援多輪對話和上下文理解
- 🔄 **SSE 流式響應**: 實時流式返回查詢結果和解釋
- 🎯 **智能建議**: 使用 AI 生成相關的後續查詢建議
- 🔍 **智能表匹配**: 自動識別問題中的關鍵詞並匹配相關數據表

### 前端功能
- 💬 **智能對話界面**: 現代化的聊天機器人 UI
- 📊 **數據可視化**: 表格形式展示查詢結果
- 🎨 **漂亮的設計**: 漸變色主題和流暢動畫
- 📱 **響應式布局**: 支援桌面和移動設備
- 🔄 **SSE 流式響應**: 使用 [useXStream](https://element-plus-x.com/zh/components/useXStream/) 實現實時流式數據傳輸
- ⚡ **打字機效果**: SQL 和解釋文字逐步顯示
- 🛑 **可中斷請求**: 支援取消正在進行的查詢

## 系統架構

```
用戶瀏覽器 (Vue 3 前端)
        ↓
    FastAPI 後端
        ↓
    Vanna AI
        ↓
    OpenAI GPT
        ↓
    MySQL 數據庫
```

## 環境需求

### 後端
- Python 3.8+
- MySQL 5.7+ 或 MySQL 8.0+
- OpenAI API Key

### 前端
- Node.js 16+ 
- npm 或 pnpm

## 安裝步驟

### 1. 克隆專案

```bash
git clone <repository-url>
cd GenAI
```

### 2. 創建虛擬環境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 配置環境變數

複製 `.env.example` 為 `.env` 並填入您的配置：

```bash
cp .env.example .env
```

編輯 `.env` 文件：

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database

# Vanna Configuration
VANNA_MODEL=my_vanna_model

# Application Settings
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=False
```

### 5. 準備數據庫

確保您的 MySQL 數據庫已經運行，並且已創建相應的資料庫：

```sql
CREATE DATABASE your_database;
```

## 啟動應用

### 後端啟動

#### 開發模式

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 生產模式

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

或直接運行：

```bash
python -m app.main
```

啟動後，API 將在 `http://localhost:8000` 上運行。

### 前端啟動

#### 1. 進入前端目錄

```bash
cd frontend
```

#### 2. 安裝依賴

```bash
npm install
# 或使用 pnpm
pnpm install
```

#### 3. 啟動開發服務器

```bash
npm run dev
# 或使用 pnpm
pnpm dev
```

前端將在 `http://localhost:5173` 上運行（Vite 默認端口）。

#### 4. 構建生產版本

```bash
npm run build
# 或使用 pnpm
pnpm build
```

### 完整啟動流程

#### 方式一：使用啟動腳本（推薦）

```bash
# 同時啟動前後端
./start-all.sh

# 停止所有服務
./stop-all.sh
```

#### 方式二：分別啟動

1. 先啟動後端服務（確保在 8000 端口）
   ```bash
   # 在項目根目錄
   source venv/bin/activate
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. 再啟動前端服務
   ```bash
   # 在項目根目錄
   ./start-frontend.sh
   # 或手動進入前端目錄
   cd frontend
   npm run dev
   ```

3. 在瀏覽器中訪問 `http://localhost:5173`

## 項目結構

```
GenAI/
├── app/                      # 後端應用
│   ├── __init__.py
│   ├── main.py              # FastAPI 主應用
│   ├── config.py            # 配置管理
│   ├── models.py            # Pydantic 資料模型
│   ├── vanna_client.py      # Vanna AI 客戶端
│   ├── conversation_manager.py  # 對話管理模組
│   ├── routes/              # API 路由模組
│   │   ├── __init__.py
│   │   ├── chat.py          # 聊天路由
│   │   ├── training.py      # 訓練路由
│   │   ├── database.py      # 數據庫路由
│   │   ├── conversations.py # 對話管理路由
│   │   ├── health.py        # 健康檢查路由
│   │   └── root.py          # 根路由
│   ├── utils/               # 工具模組
│   │   ├── __init__.py
│   │   ├── formatters.py    # 格式化工具
│   │   └── suggestions.py   # 建議生成工具
│   └── services/            # 服務層
├── frontend/                 # 前端應用
│   ├── src/
│   │   ├── components/      # Vue 組件
│   │   │   ├── SimpleChatbot.vue
│   │   │   ├── Chatbot.vue
│   │   │   ├── ChatHeader.vue
│   │   │   ├── ChatList.vue
│   │   │   └── ChatSender.vue
│   │   ├── types/           # TypeScript 類型
│   │   ├── utils/           # 工具函數
│   │   ├── App.vue          # 主應用組件
│   │   ├── main.ts          # 應用入口
│   │   └── style.css        # 全局樣式
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md            # 前端文檔
├── conversations_data/       # 對話數據存儲目錄
├── venv/                     # Python 虛擬環境
├── .env                      # 環境變數配置
├── .env.example             # 環境變數範例
├── requirements.txt          # Python 依賴
├── start-all.sh             # 完整啟動腳本
├── start-frontend.sh        # 前端啟動腳本
├── stop-all.sh              # 停止服務腳本
└── README.md                # 項目文檔
```

## API 文檔

啟動應用後，訪問以下 URL 查看互動式 API 文檔：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 前端應用

啟動前端後，訪問：

- **主頁**: http://localhost:5173

## API 端點

### 1. 健康檢查

```bash
GET /api/health
```

檢查服務、數據庫連接和 Vanna AI 的狀態。

**回應範例**:
```json
{
  "status": "healthy",
  "database_connected": true,
  "vanna_initialized": true
}
```

### 2. 聊天查詢

```bash
POST /api/chat
```

發送自然語言問題，使用 SSE（Server-Sent Events）流式響應返回 SQL 查詢和結果。

**請求範例**:
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "顯示所有客戶的訂單總數",
    "conversation_id": "conv_123456"
  }'
```

**請求參數**:
- `question` (必填): 用戶的自然語言問題
- `conversation_id` (可選): 對話 ID，用於連續對話和上下文理解

**響應格式**:
使用 SSE 流式響應，包含以下事件類型：
- `status`: 狀態更新（idle、working、success、error）
- `explanation`: 查詢解釋文字（流式輸出）
- `suggestions`: 推薦的後續問題
- `error`: 錯誤訊息
- `done`: 查詢完成標記

**注意**: 此端點返回的是 SSE 流式響應，需要使用支持 SSE 的客戶端來處理。

### 3. 訓練模型

```bash
POST /api/train
```

添加訓練資料來改善 Vanna AI 的查詢生成能力。

**使用 DDL 訓練**:
```bash
curl -X POST "http://localhost:8000/api/train" \
  -H "Content-Type: application/json" \
  -d '{
    "ddl": "CREATE TABLE customers (id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100))"
  }'
```

**使用文檔訓練**:
```bash
curl -X POST "http://localhost:8000/api/train" \
  -H "Content-Type: application/json" \
  -d '{
    "documentation": "customers 表儲存所有客戶的基本資訊，包括姓名和電子郵件"
  }'
```

**使用 SQL 範例訓練**:
```bash
curl -X POST "http://localhost:8000/api/train" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "顯示所有客戶",
    "sql": "SELECT * FROM customers"
  }'
```

### 4. 獲取資料表列表

```bash
GET /api/tables
```

獲取數據庫中所有表的名稱和結構。

**回應範例**:
```json
{
  "tables": [
    {
      "table_name": "customers",
      "table_schema": "CREATE TABLE `customers` (...)"
    },
    {
      "table_name": "orders",
      "table_schema": "CREATE TABLE `orders` (...)"
    }
  ],
  "count": 2
}
```

### 5. 獲取訓練資料

```bash
GET /api/training-data
```

查看已添加到模型中的所有訓練資料。

### 6. 外部數據庫問題建議

```bash
POST /api/database/questions
```

連接外部數據庫並獲取可詢問的問題建議。系統會自動分析數據庫結構，過濾出用戶關心的表，並生成相關的查詢建議。

**請求範例**:
```bash
curl -X POST "http://localhost:8000/api/database/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_string": "mysql://user:password@host:3306/database"
  }'
```

**請求參數**:
- `connection_string` (必填): MySQL 連接字符串，格式：`mysql://user:password@host:port/database`

**回應範例**:
```json
{
  "suggestions": [
    {
      "question": "顯示所有用戶資料",
      "description": "查詢users表中的所有記錄"
    }
  ],
  "count": 10,
  "database_name": "my_database",
  "table_count": 5
}
```

**注意**: 
- 只會為有數據（行數 > 0）的表生成建議
- 系統會自動過濾掉系統表、配置表等用戶不關心的表
- 使用 AI 分析表結構並生成中文表名

### 7. 對話管理

#### 7.1 創建對話

```bash
POST /api/conversations
```

創建一個新的對話。

**請求範例**:
```bash
curl -X POST "http://localhost:8000/api/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "數據查詢對話"
  }'
```

#### 7.2 獲取對話列表

```bash
GET /api/conversations?limit=100&offset=0
```

獲取所有對話列表。

#### 7.3 獲取對話詳情

```bash
GET /api/conversations/{conversation_id}
```

獲取特定對話的詳情。

#### 7.4 刪除對話

```bash
DELETE /api/conversations/{conversation_id}
```

刪除指定的對話。

#### 7.5 獲取對話消息

```bash
GET /api/conversations/{conversation_id}/messages
```

獲取指定對話中的所有消息。

## 使用流程

### 初次使用建議

1. **啟動應用** - 確保應用成功連接到數據庫
2. **訓練模型** - 添加資料庫結構和範例查詢
3. **測試查詢** - 使用自然語言提問

### 訓練模型最佳實踐

為了獲得最佳的查詢結果，建議：

1. **添加所有表的 DDL**:
   ```python
   # 可以使用 /api/tables 端點獲取所有表結構
   # 然後使用 /api/train 端點添加每個表的 DDL
   ```

2. **添加文檔說明**:
   - 解釋表之間的關係
   - 說明重要欄位的含義
   - 提供業務邏輯說明

3. **添加常見查詢範例**:
   - 提供典型問題和對應的 SQL
   - 包含複雜查詢的範例（JOIN、GROUP BY、子查詢等）

## 範例使用情境

### 情境 1: 查詢客戶訂單

```bash
# 自然語言問題
POST /api/chat
{
  "question": "過去 30 天內下了超過 3 筆訂單的客戶有哪些？"
}

# Vanna AI 會自動生成並執行類似的 SQL：
# SELECT customer_id, COUNT(*) as order_count 
# FROM orders 
# WHERE order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
# GROUP BY customer_id
# HAVING COUNT(*) > 3
```

### 情境 2: 數據分析

```bash
# 自然語言問題
POST /api/chat
{
  "question": "每個月的銷售總額是多少？"
}

# 自動生成 SQL 並返回結果
```


## 故障排除

### 問題 1: 無法連接到數據庫

**錯誤訊息**: `database_connected: false`

**解決方法**:
- 檢查 MySQL 服務是否正在運行
- 確認 `.env` 文件中的數據庫配置正確
- 檢查數據庫用戶是否有足夠的權限

### 問題 2: Vanna AI 初始化失敗

**錯誤訊息**: `vanna_initialized: false`

**解決方法**:
- 檢查 OpenAI API Key 是否有效
- 確認網絡連接正常
- 查看應用日誌獲取詳細錯誤訊息

### 問題 3: 生成的 SQL 不準確

**解決方法**:
- 添加更多訓練資料（DDL、文檔、SQL 範例）
- 確保問題表述清晰明確
- 查看訓練資料是否完整覆蓋數據庫結構
- 使用 `conversation_id` 進行連續對話，提供更多上下文

### 問題 4: AI 返回解釋而不是 SQL

**錯誤訊息**: "生成的內容不是有效的 SQL"

**解決方法**:
- 檢查問題中提到的表名是否在資料庫中存在
- 系統會自動列出可用的表名，請使用實際存在的表名
- 確保相關表的 DDL 已經添加到訓練資料中

## 開發指南

### 添加新的 API 端點

1. 在 `app/models.py` 中定義請求和回應模型
2. 在 `app/main.py` 中添加新的路由函數
3. 更新本 README 文件

### 自定義 Vanna AI 行為

修改 `app/vanna_client.py` 中的 `VannaClient` 類別來自定義行為。

## 安全注意事項

⚠️ **重要**: 本專案為開發範例，生產環境使用前請注意：

1. **API 認證**: 添加身份驗證機制（JWT、OAuth2 等）
2. **CORS 限制**: 在 `main.py` 中限制允許的來源
3. **SQL 注入防護**: Vanna AI 會自動處理，但建議額外驗證
4. **敏感資訊保護**: 不要將 `.env` 文件提交到版本控制
5. **速率限制**: 添加 API 速率限制防止濫用
6. **日誌安全**: 避免在日誌中記錄敏感資訊

## 後續擴展建議

- [x] 實作對話歷史記錄功能
- [x] 支援生成圖表和視覺化
- [x] AI 生成相關查詢建議
- [x] 智能表名匹配和關鍵詞識別
- [ ] 添加用戶認證和授權
- [ ] 添加查詢結果緩存
- [ ] 實作 WebSocket 支援實時對話
- [ ] 添加多語言支援
- [ ] 整合更多數據庫類型（PostgreSQL、SQLite 等）

## 技術棧

- **Web 框架**: FastAPI 0.109.0
- **AI 引擎**: Vanna AI 0.5.5
- **LLM**: OpenAI GPT
- **數據庫**: MySQL with PyMySQL
- **配置管理**: Pydantic Settings
- **ASGI 伺服器**: Uvicorn

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 授權

MIT License

## 聯繫方式

如有問題或建議，請開 Issue 討論。

---

**享受使用 Vanna AI Chatbot！** 🚀

