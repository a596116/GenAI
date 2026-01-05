"""
訓練 Vanna AI 模型
讓模型了解數據庫結構和常見查詢
"""

from app.vanna_client import vanna_client

def train_model():
    """訓練 Vanna AI 模型"""
    
    print("=" * 60)
    print("  訓練 Vanna AI 模型")
    print("=" * 60)
    print()
    
    # 初始化
    if not vanna_client.initialize():
        print("❌ Vanna AI 初始化失敗")
        return False
    
    print("✅ Vanna AI 初始化成功")
    print()
    
    # 訓練 DDL（表結構）
    print("📚 訓練表結構...")
    
    # 用戶表
    users_ddl = """
    CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用戶ID',
        name VARCHAR(100) NOT NULL COMMENT '用戶名稱',
        email VARCHAR(100) UNIQUE NOT NULL COMMENT '電子郵件',
        department VARCHAR(50) COMMENT '部門',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '創建時間'
    ) COMMENT='用戶資料表';
    """
    
    if vanna_client.train_on_ddl(users_ddl):
        print("  ✅ 用戶表結構已訓練")
    
    # 訂單表
    orders_ddl = """
    CREATE TABLE orders (
        id INT AUTO_INCREMENT PRIMARY KEY COMMENT '訂單ID',
        user_id INT COMMENT '用戶ID',
        product_name VARCHAR(200) COMMENT '產品名稱',
        quantity INT COMMENT '數量',
        price DECIMAL(10, 2) COMMENT '價格',
        order_date DATE COMMENT '訂單日期',
        FOREIGN KEY (user_id) REFERENCES users(id)
    ) COMMENT='訂單資料表';
    """
    
    if vanna_client.train_on_ddl(orders_ddl):
        print("  ✅ 訂單表結構已訓練")
    
    print()
    
    # 訓練文檔（業務說明）
    print("📖 訓練業務文檔...")
    
    documentations = [
        "users 表存儲所有用戶的基本信息，包括姓名、郵件和所屬部門",
        "orders 表存儲所有訂單記錄，每個訂單關聯一個用戶",
        "department 欄位包含：技術部、銷售部、人事部等部門名稱",
        "可以通過 user_id 將 orders 表和 users 表關聯起來查詢用戶的訂單信息",
    ]
    
    for doc in documentations:
        if vanna_client.train_on_documentation(doc):
            print(f"  ✅ 已訓練: {doc[:50]}...")
    
    print()
    
    # 訓練 SQL 範例
    print("💡 訓練查詢範例...")
    
    sql_examples = [
        ("顯示所有用戶", "SELECT * FROM users;"),
        ("顯示所有用戶的名稱和郵件", "SELECT name, email FROM users;"),
        ("統計每個部門的員工數量", "SELECT department, COUNT(*) as count FROM users GROUP BY department;"),
        ("查詢技術部的所有員工", "SELECT * FROM users WHERE department = '技術部';"),
        ("顯示所有訂單", "SELECT * FROM orders;"),
        ("查詢所有訂單及對應用戶信息", 
         "SELECT o.*, u.name, u.email FROM orders o JOIN users u ON o.user_id = u.id;"),
        ("統計每個用戶的訂單數量", 
         "SELECT u.name, COUNT(o.id) as order_count FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name;"),
        ("查詢訂單總金額最高的前3位用戶", 
         "SELECT u.name, SUM(o.price * o.quantity) as total FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name ORDER BY total DESC LIMIT 3;"),
        ("查詢最近一週的訂單", 
         "SELECT * FROM orders WHERE order_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY);"),
        ("統計各部門的訂單總金額", 
         "SELECT u.department, SUM(o.price * o.quantity) as total FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.department;"),
    ]
    
    for question, sql in sql_examples:
        if vanna_client.train_on_sql(question, sql):
            print(f"  ✅ 已訓練: {question}")
    
    print()
    print("=" * 60)
    print("  🎉 訓練完成！")
    print("=" * 60)
    print()
    print("現在可以嘗試以下問題：")
    print("  - 顯示所有用戶")
    print("  - 統計每個部門的員工數量")
    print("  - 查詢所有訂單")
    print("  - 哪些用戶的訂單金額最高？")
    print()
    
    return True

if __name__ == "__main__":
    try:
        train_model()
    except Exception as e:
        print(f"\n❌ 訓練失敗: {str(e)}")
        exit(1)

