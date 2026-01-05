"""
測試數據庫連接
"""

import pymysql
from app.config import settings

def test_connection():
    """測試數據庫連接"""
    try:
        connection = pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            print(f"✅ 成功連接到數據庫: {db_name}")
            
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"\n數據表:")
            for table in tables:
                print(f"  - {table[0]}")
                
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 連接失敗: {str(e)}")
        return False

if __name__ == "__main__":
    print("測試數據庫連接...")
    print("=" * 50)
    test_connection()

