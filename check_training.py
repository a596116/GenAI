"""
檢查 Vanna AI 訓練狀態
"""

import requests

API_BASE = "http://localhost:8000"

def check_training():
    """檢查訓練數據"""
    
    print("=" * 60)
    print("  檢查 Vanna AI 訓練狀態")
    print("=" * 60)
    print()
    
    try:
        response = requests.get(f"{API_BASE}/api/training-data")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            
            if count == 0:
                print("❌ 模型尚未訓練！")
                print()
                print("請先運行訓練腳本：")
                print("  python train_via_api.py")
                print()
                return False
            else:
                print(f"✅ 模型已訓練，共有 {count} 條訓練數據")
                print()
                print("訓練數據預覽：")
                
                training_data = data.get('training_data', [])
                for i, item in enumerate(training_data[:5], 1):
                    item_type = item.get('training_data_type', 'unknown')
                    if item_type == 'sql':
                        question = item.get('question', 'N/A')
                        print(f"  {i}. [SQL] {question}")
                    elif item_type == 'ddl':
                        content = item.get('content', '')[:50]
                        print(f"  {i}. [DDL] {content}...")
                    elif item_type == 'documentation':
                        content = item.get('documentation', '')[:50]
                        print(f"  {i}. [文檔] {content}...")
                
                if len(training_data) > 5:
                    print(f"  ... 還有 {len(training_data) - 5} 條數據")
                
                print()
                print("建議的查詢問題：")
                print("  - 顯示所有用戶")
                print("  - 統計每個部門的員工數量")
                print("  - 查詢所有訂單")
                print("  - 查詢訂單金額最高的用戶")
                print()
                return True
        else:
            print(f"❌ 無法獲取訓練數據: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        print()
        print("請確保後端服務正在運行：")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return False

if __name__ == "__main__":
    check_training()

