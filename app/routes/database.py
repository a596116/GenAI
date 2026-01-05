"""
數據庫相關路由
"""

import logging
import re
import json
from urllib.parse import urlparse, unquote
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
import pymysql
from openai import OpenAI
from app.models import TablesResponse, TableInfo, DatabaseConnectionRequest, DatabaseQuestionsResponse, QuestionSuggestion
from app.vanna_client import vanna_client
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Database"])


def parse_mysql_connection_string(connection_string: str) -> Dict[str, Any]:
    """
    解析MySQL連接字符串
    格式：mysql://user:password@host:port/database
    
    Args:
        connection_string: MySQL連接字符串
        
    Returns:
        Dict: 包含host, port, user, password, database的字典
        
    Raises:
        ValueError: 如果連接字符串格式不正確
    """
    try:
        # 使用正則表達式解析連接字符串
        # 格式：mysql://user:password@host:port/database
        pattern = r"mysql://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)"
        match = re.match(pattern, connection_string)
        
        if match:
            username, password, host, port, database = match.groups()
            return {
                "host": host,
                "port": int(port),
                "user": username,
                "password": unquote(password),
                "database": database
            }
        
        # 嘗試不帶端口的格式：mysql://user:password@host/database
        pattern2 = r"mysql://([^:]+):([^@]+)@([^/]+)/(.+)"
        match2 = re.match(pattern2, connection_string)
        
        if match2:
            username, password, host, database = match2.groups()
            return {
                "host": host,
                "port": 3306,
                "user": username,
                "password": unquote(password),
                "database": database
            }
        
        # 嘗試使用urlparse作為備選方案
        parsed = urlparse(connection_string)
        
        if parsed.hostname:
            username = unquote(parsed.username) if parsed.username else ""
            password = unquote(parsed.password) if parsed.password else ""
            database = parsed.path.lstrip('/') if parsed.path else ""
            
            return {
                "host": parsed.hostname,
                "port": parsed.port if parsed.port else 3306,
                "user": username,
                "password": password,
                "database": database
            }
        
        raise ValueError(f"無法解析連接字符串格式: {connection_string}")
        
    except Exception as e:
        logger.error(f"解析連接字符串失敗: {str(e)}")
        raise ValueError(f"無法解析連接字符串: {connection_string}, 錯誤: {str(e)}")


def analyze_tables_with_ai(tables_info: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    使用 AI 分析表列表，過濾出用戶真正關心的表並生成中文名稱
    
    Args:
        tables_info: 表信息列表，每個元素包含 table_name 和 columns
        
    Returns:
        Dict: 包含 filtered_tables (過濾後的表) 和 table_names_cn (中文名稱映射) 的字典
    """
    try:
        client = OpenAI(api_key=settings.openai_api_key)
        
        # 構建表信息摘要
        table_summaries = []
        for table_info in tables_info:
            table_name = table_info.get("table_name", "")
            columns = table_info.get("columns", [])
            column_names = [col.get("name", "") for col in columns if col.get("name")]
            table_summaries.append({
                "table_name": table_name,
                "column_count": len(column_names),
                "sample_columns": column_names[:5]  # 只取前5個列作為樣本
            })
        
        prompt = f"""你是一個數據庫分析專家。請分析以下數據庫表列表，判斷哪些表是終端用戶真正想查詢和查看的數據，並為每個表生成對應的中文名稱。

表列表：
{json.dumps(table_summaries, ensure_ascii=False, indent=2)}

判斷標準：
1. 過濾掉系統表、配置表、中間表（如以 App、Config、Setting 開頭的表通常是配置表，不適合終端用戶查詢）
2. 過濾掉關聯映射表（如 XxxTagMap、XxxPermission 等中間表）
3. 保留業務數據表（如用戶數據、內容數據、統計數據等）
4. 保留用戶真正關心的核心業務表

請返回 JSON 格式：
{{
  "filtered_tables": ["table1", "table2", ...],  // 過濾後應該保留的表名列表
  "table_names_cn": {{
    "table1": "中文名稱1",
    "table2": "中文名稱2",
    ...
  }}  // 所有表的中文名稱映射（包括被過濾的表也給出中文名，以備參考）
}}

只返回 JSON，不要其他說明文字。"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個專業的數據庫分析專家，擅長識別用戶關心的數據表和生成合適的中文名稱。只返回有效的 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # 清理可能的代碼塊標記
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        result = json.loads(result_text)
        
        logger.info(f"AI 分析結果: 過濾後保留 {len(result.get('filtered_tables', []))} 個表")
        return result
        
    except json.JSONDecodeError as e:
        result_text_snippet = result_text[:200] if 'result_text' in locals() else "無法獲取"
        logger.error(f"AI 返回的 JSON 格式錯誤: {str(e)}, 原始內容: {result_text_snippet}")
        # 如果解析失敗，返回所有表
        return {
            "filtered_tables": [t.get("table_name", "") for t in tables_info],
            "table_names_cn": {t.get("table_name", ""): t.get("table_name", "") for t in tables_info}
        }
    except Exception as e:
        logger.error(f"AI 分析表失敗: {str(e)}")
        # 如果 AI 調用失敗，返回所有表
        return {
            "filtered_tables": [t.get("table_name", "") for t in tables_info],
            "table_names_cn": {t.get("table_name", ""): t.get("table_name", "") for t in tables_info}
        }


def generate_question_suggestions(tables_info: List[Dict[str, Any]], table_names_cn: Optional[Dict[str, str]] = None, table_row_counts: Optional[Dict[str, int]] = None) -> List[QuestionSuggestion]:
    """
    根據數據庫表結構生成問題建議（使用中文表名）
    
    Args:
        tables_info: 表信息列表，每個元素包含 table_name 和 columns
        table_names_cn: 表名中文字典映射，可選
        table_row_counts: 表名對應的行數字典，可選。如果提供的話，只會為行數大於0的表生成建議
        
    Returns:
        List[QuestionSuggestion]: 問題建議列表
    """
    suggestions = []
    
    if not table_names_cn:
        table_names_cn = {}
    
    if not table_row_counts:
        table_row_counts = {}
    
    for table_info in tables_info:
        table_name = table_info.get("table_name", "")
        
        # 如果提供了行數資訊，且該表的行數為0，則跳過該表
        if table_row_counts and table_name in table_row_counts:
            row_count = table_row_counts[table_name]
            if row_count == 0:
                logger.debug(f"跳過空表 {table_name}（行數: {row_count}）")
                continue
        
        table_name_cn = table_names_cn.get(table_name, table_name)  # 使用中文名稱，如果沒有則使用原名
        columns = table_info.get("columns", [])
        column_names = [col.get("name", "") for col in columns if col.get("name")]
        
        if not column_names:
            continue
        
        # 分析列名，生成問題建議
        # 查找常見的列名模式
        id_columns = [col for col in column_names if 'id' in col.lower()]
        name_columns = [col for col in column_names if any(keyword in col.lower() for keyword in ['name', 'title', '名稱', '標題'])]
        date_columns = [col for col in column_names if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated', '日期', '時間'])]
        count_columns = [col for col in column_names if any(keyword in col.lower() for keyword in ['count', 'quantity', 'amount', '數量', '金額'])]
        
        # 使用中文表名生成問題
        suggestions.append(QuestionSuggestion(
            question=f"顯示所有{table_name_cn}的資料",
            description=f"查詢{table_name}表中的所有記錄"
        ))
        
        # 如果有名稱列，生成相關問題
        if name_columns:
            suggestions.append(QuestionSuggestion(
                question=f"顯示所有{table_name_cn}的{name_columns[0]}",
                description=f"查詢{table_name}表中的{name_columns[0]}字段"
            ))
        
        # 如果有日期列，生成時間相關問題
        if date_columns:
            suggestions.append(QuestionSuggestion(
                question=f"查詢最近一週的{table_name_cn}記錄",
                description=f"根據{date_columns[0]}查詢最近一週的{table_name}記錄"
            ))
        
        # 如果有數量/金額列，生成統計問題
        if count_columns:
            suggestions.append(QuestionSuggestion(
                question=f"統計{table_name_cn}的{count_columns[0]}總和",
                description=f"計算{table_name}表中{count_columns[0]}的總和"
            ))
            if name_columns:
                suggestions.append(QuestionSuggestion(
                    question=f"按{name_columns[0]}分組統計{table_name_cn}",
                    description=f"按{name_columns[0]}分組統計{table_name}表"
                ))
    
    # 如果有多個有資料的表，生成關聯查詢建議
    # 先過濾出有資料的表（如果有提供行數資訊的話）
    tables_with_data = tables_info
    if table_row_counts:
        tables_with_data = [
            t for t in tables_info 
            if table_row_counts.get(t.get("table_name", ""), 1) > 0
        ]
    
    if len(tables_with_data) > 1:
        table_names_cn_list = [table_names_cn.get(t.get("table_name", ""), t.get("table_name", "")) for t in tables_with_data]
        if len(table_names_cn_list) >= 2:
            suggestions.append(QuestionSuggestion(
                question=f"查詢{table_names_cn_list[0]}和{table_names_cn_list[1]}的關聯資料",
                description=f"關聯查詢兩個表的數據"
            ))
    
    # 限制建議數量，返回最多10個
    return suggestions[:10]


@router.get("/api/tables", response_model=TablesResponse)
async def get_tables():
    """
    獲取資料庫表列表
    
    返回數據庫中所有表的名稱和結構
    
    Returns:
        TablesResponse: 包含所有表的列表
    """
    try:
        if not vanna_client.is_initialized():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vanna AI 服務尚未初始化，請稍後再試"
            )
        
        # 獲取所有表名
        table_names = vanna_client.get_all_tables()
        
        # 獲取每個表的 DDL
        tables_info: list[TableInfo] = []
        for table_name in table_names:
            ddl = vanna_client.get_table_ddl(table_name)
            tables_info.append(TableInfo(
                table_name=table_name,
                table_schema=ddl
            ))
        
        return TablesResponse(
            tables=tables_info,
            count=len(tables_info)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取表列表錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取表列表時發生錯誤: {str(e)}"
        )


@router.post("/api/database/questions", response_model=DatabaseQuestionsResponse)
async def get_database_questions(request: DatabaseConnectionRequest):
    """
    連接外部數據庫並獲取可詢問的問題建議
    
    根據數據庫的表結構生成問題建議
    
    Args:
        request: 包含數據庫連接字符串的請求
        
    Returns:
        DatabaseQuestionsResponse: 包含問題建議列表的回應
    """
    connection = None
    try:
        # 解析連接字符串
        db_config = parse_mysql_connection_string(request.connection_string)
        logger.info(f"解析連接配置: host={db_config['host']}, port={db_config['port']}, database={db_config['database']}")
        
        # 連接到數據庫
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        logger.info(f"成功連接到數據庫: {db_config['database']}")
        
        # 獲取所有表名
        tables_info = []
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_names = [list(table.values())[0] for table in tables]
            
            # 獲取每個表的列信息
            for table_name in table_names:
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                
                # 轉換列信息為字典列表
                column_list = []
                for col in columns:
                    column_list.append({
                        "name": col.get("Field", ""),
                        "type": col.get("Type", ""),
                        "null": col.get("Null", ""),
                        "key": col.get("Key", ""),
                        "default": col.get("Default"),
                        "extra": col.get("Extra", "")
                    })
                
                tables_info.append({
                    "table_name": table_name,
                    "columns": column_list
                })
        
        # 使用 AI 分析表，過濾並生成中文名稱
        logger.info("開始使用 AI 分析表結構...")
        ai_analysis = analyze_tables_with_ai(tables_info)
        filtered_table_names = set(ai_analysis.get("filtered_tables", []))
        table_names_cn = ai_analysis.get("table_names_cn", {})
        
        # 過濾表，只保留用戶關心的表
        filtered_tables_info = [
            t for t in tables_info 
            if t.get("table_name", "") in filtered_table_names
        ]
        
        logger.info(f"AI 過濾結果: 從 {len(tables_info)} 個表中過濾出 {len(filtered_tables_info)} 個用戶關心的表")
        
        # 查詢每個表的行數
        table_row_counts = {}
        with connection.cursor() as cursor:
            for table_info in filtered_tables_info:
                table_name = table_info.get("table_name", "")
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
                    result = cursor.fetchone()
                    row_count = result.get("count", 0) if isinstance(result, dict) else (result[0] if result else 0)
                    table_row_counts[table_name] = row_count
                    logger.debug(f"表 {table_name} 的行數: {row_count}")
                except Exception as e:
                    logger.warning(f"查詢表 {table_name} 的行數失敗: {str(e)}")
                    table_row_counts[table_name] = 0
        
        # 使用過濾後的表、中文名稱和行數資訊生成問題建議（空表會被自動跳過）
        suggestions = generate_question_suggestions(filtered_tables_info, table_names_cn, table_row_counts)
        
        logger.info(f"為數據庫 {db_config['database']} 生成了 {len(suggestions)} 個問題建議")
        
        return DatabaseQuestionsResponse(
            suggestions=suggestions,
            count=len(suggestions),
            database_name=db_config['database'],
            table_count=len(table_names)
        )
        
    except ValueError as e:
        logger.error(f"連接字符串解析錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"連接字符串格式錯誤: {str(e)}"
        )
    except pymysql.Error as e:
        logger.error(f"數據庫連接錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"無法連接到數據庫: {str(e)}"
        )
    except Exception as e:
        logger.error(f"獲取問題建議錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取問題建議時發生錯誤: {str(e)}"
        )
    finally:
        if connection:
            connection.close()
            logger.info("數據庫連接已關閉")

