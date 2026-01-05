"""
設置數據庫和測試數據
"""

import pymysql
from app.config import settings

def setup_database():
    """創建數據庫和測試表"""
    
    # 先連接到 MySQL 服務器（不指定數據庫）
    connection = pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
    )
    
    try:
        with connection.cursor() as cursor:
            # 創建數據庫（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database}")
            print(f"✅ 數據庫 '{settings.mysql_database}' 已創建或已存在")
            
            # 切換到該數據庫
            cursor.execute(f"USE {settings.mysql_database}")
            
            # 創建測試表：用戶表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    department VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ 用戶表已創建")
            
            # 創建測試表：訂單表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    product_name VARCHAR(200),
                    quantity INT,
                    price DECIMAL(10, 2),
                    order_date DATE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            print("✅ 訂單表已創建")
            
            # 檢查是否已有數據
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()[0]
            
            if user_count == 0:
                # 插入測試數據
                cursor.execute("""
                    INSERT INTO users (name, email, department) VALUES
                    ('張三', 'zhangsan@example.com', '技術部'),
                    ('李四', 'lisi@example.com', '銷售部'),
                    ('王五', 'wangwu@example.com', '技術部'),
                    ('趙六', 'zhaoliu@example.com', '人事部'),
                    ('錢七', 'qianqi@example.com', '銷售部')
                """)
                print("✅ 已插入用戶測試數據")
                
                cursor.execute("""
                    INSERT INTO orders (user_id, product_name, quantity, price, order_date) VALUES
                    (1, '筆記型電腦', 1, 25000.00, '2024-01-15'),
                    (1, '滑鼠', 2, 500.00, '2024-01-15'),
                    (2, '鍵盤', 1, 1500.00, '2024-01-16'),
                    (3, '顯示器', 2, 8000.00, '2024-01-17'),
                    (2, '耳機', 1, 2000.00, '2024-01-18'),
                    (4, '筆記型電腦', 1, 28000.00, '2024-01-19'),
                    (5, '平板電腦', 1, 15000.00, '2024-01-20')
                """)
                print("✅ 已插入訂單測試數據")
            else:
                print(f"ℹ️  數據庫已有 {user_count} 個用戶，跳過插入測試數據")
            
        connection.commit()
        print("\n🎉 數據庫設置完成！")
        print(f"\n數據庫信息:")
        print(f"  主機: {settings.mysql_host}")
        print(f"  端口: {settings.mysql_port}")
        print(f"  數據庫: {settings.mysql_database}")
        print(f"  用戶: {settings.mysql_user}")
        
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    print("=" * 50)
    print("  數據庫設置腳本")
    print("=" * 50)
    print()
    
    try:
        setup_database()
    except Exception as e:
        print(f"\n❌ 設置失敗: {str(e)}")
        exit(1)

