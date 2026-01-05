"""
Vanna AI Chatbot API 使用範例
展示如何使用 Python 調用 API
"""

import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:8000"


def check_health():
    """檢查服務健康狀態"""
    print("=" * 50)
    print("1. 檢查服務健康狀態")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def get_tables():
    """獲取資料表列表"""
    print("=" * 50)
    print("2. 獲取資料表列表")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/tables")
    print(f"狀態碼: {response.status_code}")
    data = response.json()
    print(f"找到 {data['count']} 個表:")
    for table in data['tables']:
        print(f"  - {table['table_name']}")
    print()


def train_with_ddl():
    """使用 DDL 訓練模型"""
    print("=" * 50)
    print("3. 使用 DDL 訓練模型")
    print("=" * 50)
    
    ddl = """
    CREATE TABLE customers (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    response = requests.post(
        f"{BASE_URL}/api/train",
        json={"ddl": ddl}
    )
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def train_with_documentation():
    """使用文檔訓練模型"""
    print("=" * 50)
    print("4. 使用文檔訓練模型")
    print("=" * 50)
    
    documentation = "customers 表儲存所有客戶的基本資訊，包括姓名、電子郵件和註冊時間"
    
    response = requests.post(
        f"{BASE_URL}/api/train",
        json={"documentation": documentation}
    )
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def train_with_sql_example():
    """使用 SQL 範例訓練模型"""
    print("=" * 50)
    print("5. 使用 SQL 範例訓練模型")
    print("=" * 50)
    
    response = requests.post(
        f"{BASE_URL}/api/train",
        json={
            "question": "顯示所有客戶",
            "sql": "SELECT * FROM customers"
        }
    )
    print(f"狀態碼: {response.status_code}")
    print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()


def ask_question(question: str):
    """提問並獲取結果"""
    print("=" * 50)
    print(f"6. 提問: {question}")
    print("=" * 50)
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={"question": question}
    )
    print(f"狀態碼: {response.status_code}")
    data = response.json()
    
    print(f"\n問題: {data['question']}")
    print(f"\n生成的 SQL:")
    print(f"  {data.get('sql', 'N/A')}")
    
    if data.get('result'):
        print(f"\n查詢結果 ({len(data['result'])} 條記錄):")
        for i, row in enumerate(data['result'][:5], 1):  # 只顯示前 5 條
            print(f"  {i}. {row}")
        if len(data['result']) > 5:
            print(f"  ... 還有 {len(data['result']) - 5} 條記錄")
    
    if data.get('explanation'):
        print(f"\n解釋: {data['explanation']}")
    
    if data.get('error'):
        print(f"\n❌ 錯誤: {data['error']}")
    
    print()


def get_training_data():
    """獲取訓練資料"""
    print("=" * 50)
    print("7. 獲取訓練資料")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/training-data")
    print(f"狀態碼: {response.status_code}")
    data = response.json()
    print(f"訓練資料數量: {data['count']}")
    print()


def main():
    """主函數 - 執行所有範例"""
    print("\n🤖 Vanna AI Chatbot API 使用範例\n")
    
    try:
        # 1. 檢查健康狀態
        check_health()
        
        # 2. 獲取資料表列表
        get_tables()
        
        # 3. 訓練模型 - DDL
        train_with_ddl()
        
        # 4. 訓練模型 - 文檔
        train_with_documentation()
        
        # 5. 訓練模型 - SQL 範例
        train_with_sql_example()
        
        # 6. 提問範例
        ask_question("顯示所有客戶的電子郵件")
        ask_question("有多少位客戶？")
        ask_question("最近註冊的 5 位客戶是誰？")
        
        # 7. 獲取訓練資料
        get_training_data()
        
        print("✅ 所有範例執行完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到 API 服務")
        print("請確保後端服務正在運行: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")


if __name__ == "__main__":
    main()

