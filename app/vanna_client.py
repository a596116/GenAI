"""
Vanna AI 客戶端封裝
提供與 Vanna AI 交互的高級介面
"""

import logging
import re
from typing import Optional, Dict, List, Any
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
import pymysql
import os
from .config import settings

logger = logging.getLogger(__name__)


class VannaClient:
    """Vanna AI 客戶端類別"""
    
    def __init__(self):
        """初始化 Vanna 客戶端"""
        self.vn = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """
        初始化 Vanna AI 實例並連接到數據庫
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 創建 Vanna 實例使用 OpenAI + ChromaDB（本地向量存儲）
            class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                def __init__(self, config=None):
                    # ChromaDB_VectorStore 使用本地存儲，不需要 email
                    ChromaDB_VectorStore.__init__(self, config=config)
                    # OpenAI_Chat 從 config 中讀取 api_key
                    OpenAI_Chat.__init__(self, config=config)
            
            # 初始化 Vanna，config 中包含 OpenAI api_key 和 ChromaDB 配置
            config = {
                'api_key': settings.openai_api_key,  # OpenAI API key
                'model': 'gpt-3.5-turbo',  # 使用 gpt-3.5-turbo（更快更便宜）或 gpt-4
                'path': './chromadb_data'  # ChromaDB 本地存儲路徑
            }
            self.vn = MyVanna(config=config)
            
            # 連接到 MySQL 數據庫
            # connect_to_mysql 使用 dbname 而不是 database
            connection_params = {
                'host': settings.mysql_host,
                'port': settings.mysql_port,
                'user': settings.mysql_user,
                'password': settings.mysql_password,
                'dbname': settings.mysql_database,  # 使用 dbname 而不是 database
            }
            
            self.vn.connect_to_mysql(**connection_params)
            
            self._initialized = True
            logger.info("Vanna AI 客戶端初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"Vanna AI 初始化失敗: {str(e)}")
            self._initialized = False
            return False
    
    def is_initialized(self) -> bool:
        """檢查是否已初始化"""
        return self._initialized
    
    def train_on_ddl(self, ddl: str) -> bool:
        """
        使用 DDL 語句訓練模型
        
        Args:
            ddl: 資料定義語言語句
            
        Returns:
            bool: 訓練是否成功
        """
        try:
            if not self._initialized:
                raise Exception("Vanna 客戶端尚未初始化")
            
            self.vn.train(ddl=ddl)
            logger.info(f"成功添加 DDL 訓練資料")
            return True
            
        except Exception as e:
            logger.error(f"DDL 訓練失敗: {str(e)}")
            return False
    
    def train_on_documentation(self, documentation: str) -> bool:
        """
        使用文檔訓練模型
        
        Args:
            documentation: 資料庫文檔或描述
            
        Returns:
            bool: 訓練是否成功
        """
        try:
            if not self._initialized:
                raise Exception("Vanna 客戶端尚未初始化")
            
            self.vn.train(documentation=documentation)
            logger.info(f"成功添加文檔訓練資料")
            return True
            
        except Exception as e:
            logger.error(f"文檔訓練失敗: {str(e)}")
            return False
    
    def train_on_sql(self, question: str, sql: str) -> bool:
        """
        使用問題-SQL 對訓練模型
        
        Args:
            question: 自然語言問題
            sql: 對應的 SQL 查詢
            
        Returns:
            bool: 訓練是否成功
        """
        try:
            if not self._initialized:
                raise Exception("Vanna 客戶端尚未初始化")
            
            self.vn.train(question=question, sql=sql)
            logger.info(f"成功添加 SQL 訓練資料: {question}")
            return True
            
        except Exception as e:
            logger.error(f"SQL 訓練失敗: {str(e)}")
            return False
    
    def ask_question(self, question: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        提問並獲取 SQL 查詢結果
        
        Args:
            question: 用戶的自然語言問題
            conversation_history: 可選的對話歷史，格式為 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
        Returns:
            Dict: 包含 SQL、結果和解釋的字典
        """
        try:
            if not self._initialized:
                raise Exception("Vanna 客戶端尚未初始化")
            
            # 如果有對話歷史，將歷史上下文添加到問題中
            enhanced_question = question
            if conversation_history and len(conversation_history) > 0:
                logger.info(f"開始處理對話歷史，原始歷史消息數: {len(conversation_history)}")
                
                # 構建上下文提示
                context_parts = []
                # 只取最近的幾輪對話（避免上下文過長）
                recent_history = conversation_history[-6:]  # 最近3輪對話（6條消息）
                logger.info(f"使用最近 {len(recent_history)} 條消息作為上下文")
                
                for i, msg in enumerate(recent_history):
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    
                    if role == "user":
                        context_parts.append(f"用戶: {content}")
                        logger.debug(f"添加上下文 - 用戶消息 {i+1}: {content[:50]}...")
                    elif role == "assistant":
                        # 提取主要解釋部分（排除表格和SQL）
                        # 先嘗試提取 SQL（如果有的話）
                        sql_match = None
                        if "```sql" in content:
                            sql_pattern = r"```sql\s*(.*?)\s*```"
                            sql_match = re.search(sql_pattern, content, re.DOTALL)
                        
                        # 提取解釋部分（在查詢結果之前）
                        explanation_part = content.split("**查詢結果：**")[0].strip()
                        explanation_part = explanation_part.split("```sql")[0].strip()
                        
                        # 構建助手回答摘要
                        assistant_summary = []
                        if explanation_part and len(explanation_part) > 0:
                            # 只取前150字符作為摘要
                            assistant_summary.append(f"回答: {explanation_part[:150]}")
                        
                        if sql_match:
                            sql_content = sql_match.group(1).strip()
                            # 提取 SQL 的關鍵部分（表名、列名等）
                            assistant_summary.append(f"執行的SQL: {sql_content[:100]}")
                        
                        if assistant_summary:
                            context_parts.append("助手: " + " | ".join(assistant_summary))
                            logger.debug(f"添加上下文 - 助手消息 {i+1}: {assistant_summary[0][:50]}...")
                
                if context_parts:
                    context = "\n".join(context_parts)
                    # 使用更簡潔和直接的提示
                    enhanced_question = f"""對話歷史：
{context}

當前問題：{question}

請根據對話歷史理解用戶意圖。如果當前問題是對之前查詢的進一步操作（如「給我技術部的」、「只顯示前5個」等），請基於之前的查詢來生成新的SQL。"""
                    logger.info(f"✅ 已增強問題，增強後的問題長度: {len(enhanced_question)} 字符")
                    logger.info(f"📝 增強後的問題預覽: {enhanced_question[:300]}...")
                else:
                    logger.warning("⚠️ 對話歷史為空，無法構建上下文，使用原始問題")
            
            # 在生成 SQL 前，獲取實際的表名列表和 DDL 並添加到提示中
            actual_tables = self.get_all_tables()
            if actual_tables:
                # 構建表信息（包括表名和 DDL）
                tables_info_parts = [f"\n\n資料庫中實際存在的表名列表：{', '.join(actual_tables)}"]
                
                # 智能選擇相關表的 DDL（基於問題中的關鍵詞）
                question_lower = enhanced_question.lower()
                relevant_tables = []
                
                # 提取問題中的關鍵詞（中文和英文）
                # 提取中文詞彙（至少2個字符）
                chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', question_lower)
                # 提取英文單詞（至少3個字符）
                english_words = re.findall(r'[a-z]{3,}', question_lower)
                
                # 處理中文中的常見翻譯對應（如「數據庫」->「database」，「標籤」->「tag」等）
                translation_map = {
                    '數據庫': 'database',
                    '資料庫': 'database',
                    '標籤': 'tag',
                    '頁面': 'page',
                    '視圖': 'view',
                    '設置': 'setting',
                    '配置': 'config',
                    '用戶': 'user',
                    '角色': 'role'
                }
                
                # 添加翻譯後的關鍵詞
                translated_keywords = []
                for word in chinese_words:
                    if word in translation_map:
                        translated_keywords.append(translation_map[word])
                
                keywords = chinese_words + english_words + translated_keywords
                
                logger.debug(f"從問題中提取的關鍵詞: {keywords}")
                
                # 從問題中提取可能的表名關鍵詞
                for table_name in actual_tables:
                    table_name_lower = table_name.lower()
                    is_relevant = False
                    
                    # 方法1: 完整表名匹配
                    if table_name_lower in question_lower:
                        is_relevant = True
                        logger.debug(f"完整匹配: {table_name} 在問題中")
                    
                    # 方法2: 表名包含問題中的關鍵詞（支持部分匹配）
                    if not is_relevant:
                        for keyword in keywords:
                            # 直接匹配
                            if keyword in table_name_lower:
                                is_relevant = True
                                logger.debug(f"關鍵詞匹配: {keyword} 在 {table_name} 中")
                                break
                            # 反向匹配（表名在關鍵詞中，用於處理復合關鍵詞如「Notion數據庫」）
                            if table_name_lower.replace('_', '').replace(' ', '') in keyword.replace(' ', ''):
                                is_relevant = True
                                logger.debug(f"反向匹配: {table_name} 在關鍵詞 {keyword} 中")
                                break
                            # 檢查關鍵詞是否為表名的前綴或核心部分
                            if len(keyword) >= 3 and table_name_lower.startswith(keyword):
                                is_relevant = True
                                logger.debug(f"前綴匹配: {keyword} 是 {table_name} 的前綴")
                                break
                    
                    # 方法3: 檢查表名的核心部分（去掉前綴如 App、Blog 等）
                    if not is_relevant:
                        # 提取表名的核心部分（通常是去掉前綴）
                        core_parts = re.split(r'(app|blog|notion|portfolio|user|role|database|page|tag)', table_name_lower)
                        for part in core_parts:
                            if len(part) > 2:
                                # 檢查核心部分是否在問題中
                                if part in question_lower:
                                    is_relevant = True
                                    logger.debug(f"核心部分匹配: {part} <-> {table_name}")
                                    break
                                # 檢查核心部分是否在關鍵詞中
                                for keyword in keywords:
                                    if part in keyword or keyword in part:
                                        is_relevant = True
                                        logger.debug(f"核心部分-關鍵詞匹配: {part} <-> {keyword} <-> {table_name}")
                                        break
                                if is_relevant:
                                    break
                    
                    if is_relevant:
                        relevant_tables.append(table_name)
                
                logger.info(f"找到 {len(relevant_tables)} 個相關表: {relevant_tables}")
                
                # 如果沒有找到相關表，使用前5個表
                if not relevant_tables:
                    relevant_tables = actual_tables[:5]
                    logger.warning(f"沒有找到相關表，使用前5個表: {relevant_tables}")
                else:
                    # 限制相關表數量，避免提示過長，但至少要包含前15個匹配的表
                    relevant_tables = relevant_tables[:15]
                
                # 獲取相關表的 DDL，讓 AI 知道表結構
                ddl_info_parts = []
                for table_name in relevant_tables:
                    try:
                        ddl = self.get_table_ddl(table_name)
                        if ddl:
                            # 簡化 DDL，只保留關鍵信息（表名和列定義）
                            ddl_lines = [line.strip() for line in ddl.split('\n') if line.strip()]
                            # 提取 CREATE TABLE 行和列定義行
                            simplified_lines = []
                            for i, line in enumerate(ddl_lines):
                                if 'CREATE TABLE' in line.upper() or line.startswith('`') or line.startswith('PRIMARY KEY'):
                                    simplified_lines.append(line)
                                    if len(simplified_lines) >= 15:  # 限制行數
                                        break
                            
                            if simplified_lines:
                                simplified_ddl = '\n'.join(simplified_lines[:15])
                                if len(ddl_lines) > 15:
                                    simplified_ddl += '\n...'
                                ddl_info_parts.append(f"\n表 {table_name} 的結構：\n{simplified_ddl}")
                    except Exception as e:
                        logger.warning(f"獲取表 {table_name} 的 DDL 失敗: {str(e)}")
                        # 即使獲取 DDL 失敗，至少提供表名
                        ddl_info_parts.append(f"\n表 {table_name} 存在於資料庫中")
                
                # 組合表名和 DDL 信息
                if ddl_info_parts:
                    tables_info = ''.join(tables_info_parts) + '\n' + ''.join(ddl_info_parts)
                else:
                    tables_info = ''.join(tables_info_parts)
                
                # 強化的指令，確保 AI 使用我們提供的表信息
                tables_info += "\n\n重要提示：\n"
                tables_info += "1. 上述表名列表是資料庫中實際存在的所有表\n"
                tables_info += "2. 如果問題中提到的表名在上述列表中，必須使用列表中的確切表名\n"
                tables_info += "3. 請根據提供的表結構信息（DDL）生成 SQL 查詢\n"
                tables_info += "4. 如果問題中提到「Notion數據庫」或「Notion」，請查找列表中以 Notion 開頭的表（如 NotionDatabase, NotionPage 等）\n"
                tables_info += "5. 忽略任何訓練數據中的舊表信息，只使用上述提供的表信息\n"
                
                # 將表信息放在問題前面，確保 AI 優先看到
                enhanced_question_with_tables = tables_info + "\n\n" + enhanced_question
                logger.info(f"已添加實際表名和 DDL 信息到提示中，表名列表: {actual_tables[:5]}... (共{len(actual_tables)}個表)")
            else:
                enhanced_question_with_tables = enhanced_question
                logger.warning("無法獲取表名列表，將使用原始提示")
            
            # 生成 SQL
            try:
                logger.info(f"開始生成 SQL，問題: {enhanced_question_with_tables[:200]}")
                sql_raw = self.vn.generate_sql(question=enhanced_question_with_tables)
                logger.info(f"generate_sql 返回的原始內容類型: {type(sql_raw)}, 長度: {len(str(sql_raw)) if sql_raw else 0}")
                logger.info(f"generate_sql 返回的原始內容: {repr(sql_raw)[:500]}")
                
                # 將 SQL 轉換為字符串
                sql = str(sql_raw).strip() if sql_raw else None
                
                # 如果 SQL 包含 markdown 代碼塊，嘗試提取
                if sql and "```sql" in sql:
                    logger.info("檢測到 SQL 包含 markdown 代碼塊，嘗試提取...")
                    sql_match = re.search(r"```sql\s*(.*?)\s*```", sql, re.DOTALL)
                    if sql_match:
                        sql = sql_match.group(1).strip()
                        logger.info(f"從 markdown 代碼塊提取 SQL: {sql[:200]}")
                    else:
                        # 嘗試其他格式
                        sql_match = re.search(r"```\s*(.*?)\s*```", sql, re.DOTALL)
                        if sql_match:
                            sql = sql_match.group(1).strip()
                            logger.info(f"從代碼塊提取 SQL: {sql[:200]}")
            except Exception as gen_error:
                # 如果 SQL 生成失敗，記錄詳細錯誤
                logger.error(f"SQL 生成失敗: {str(gen_error)}", exc_info=True)
                error_msg = f"無法生成 SQL 查詢。錯誤: {str(gen_error)[:200]}"
                # 如果是 OpenAI API 錯誤，提供更友好的提示
                if "api" in str(gen_error).lower() or "openai" in str(gen_error).lower():
                    error_msg = "無法生成 SQL 查詢。請檢查 OpenAI API 配置和網絡連接。"
                return {
                    'sql': None,
                    'result': None,
                    'explanation': None,
                    'error': error_msg
                }
            
            # 檢查 SQL 是否成功生成
            if sql is None or sql.strip() == '':
                error_msg = "無法生成 SQL 查詢。可能原因：1) 模型尚未訓練 2) 問題不清楚 3) 沒有相關的表結構信息"
                logger.warning(f"{error_msg} (generate_sql 返回 None 或空字符串)")
                return {
                    'sql': None,
                    'result': None,
                    'explanation': None,
                    'error': error_msg
                }
            
            # 清理 SQL：移除可能的註釋和前導空白
            sql_cleaned = sql.strip()
            logger.debug(f"SQL 清理前: {sql_cleaned[:200]}")
            # 移除 SQL 註釋（-- 和 /* */ 格式）
            sql_cleaned = re.sub(r'--.*?$', '', sql_cleaned, flags=re.MULTILINE)
            sql_cleaned = re.sub(r'/\*.*?\*/', '', sql_cleaned, flags=re.DOTALL)
            sql_cleaned = sql_cleaned.strip()
            logger.debug(f"SQL 清理後: {sql_cleaned[:200]}")
            
            # 檢查生成的是否真的是 SQL（改進的驗證）
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'SHOW', 'DESCRIBE', 'WITH']
            sql_upper = sql_cleaned.upper()
            # 檢查是否包含 SQL 關鍵字（不一定要在開頭，因為可能有註釋）
            is_sql = any(keyword in sql_upper for keyword in sql_keywords)
            logger.debug(f"清理後的 SQL 包含關鍵字: {is_sql}")
            
            # 如果清理後的 SQL 不包含關鍵字，嘗試檢查原始 SQL
            if not is_sql:
                sql_upper_original = sql.upper()
                is_sql = any(keyword in sql_upper_original for keyword in sql_keywords)
                logger.debug(f"原始 SQL 包含關鍵字: {is_sql}")
            
            if not is_sql:
                # 可能是普通對話，而不是 SQL 查詢
                logger.error(f"生成的內容不是有效的 SQL，原始內容: {repr(sql)}")
                logger.error(f"生成的內容不是有效的 SQL，前200字符: {str(sql)[:200]}")
                
                # 嘗試從 AI 返回的內容中提取有用的信息
                sql_lower = sql.lower()
                error_msg_parts = []
                
                # 檢查是否提到找不到表
                if '沒有' in sql or '不存在' in sql or '找不到' in sql or 'not found' in sql_lower or 'does not exist' in sql_lower:
                    error_msg_parts.append('無法找到您提到的資料表。')
                    
                    # 嘗試獲取實際可用的表名列表
                    try:
                        actual_tables = self.get_all_tables()
                        if actual_tables:
                            # 只顯示前10個表名，避免訊息太長
                            tables_display = ', '.join(actual_tables[:10])
                            if len(actual_tables) > 10:
                                tables_display += f' 等共 {len(actual_tables)} 個表'
                            error_msg_parts.append(f'\n\n可用的資料表包括：{tables_display}')
                            error_msg_parts.append('\n請使用上述實際存在的表名重新提問。')
                    except Exception as e:
                        logger.debug(f"獲取表名列表失敗: {str(e)}")
                
                # 如果沒有提取到特定信息，使用通用錯誤訊息
                if not error_msg_parts:
                    error_msg_parts.append('無法生成有效的 SQL 查詢。')
                    
                    # 檢查是否有訓練數據
                    try:
                        training_data = self.vn.get_training_data()
                        # 安全地檢查訓練數據
                        if training_data is not None:
                            try:
                                # 嘗試獲取長度
                                if hasattr(training_data, '__len__'):
                                    training_count = len(training_data)
                                elif hasattr(training_data, 'empty'):
                                    # 如果是 DataFrame，使用 empty 屬性
                                    training_count = 0 if training_data.empty else 1
                                else:
                                    training_count = 1 if training_data else 0
                            except Exception:
                                training_count = 0
                        else:
                            training_count = 0
                        
                        logger.warning(f"訓練數據數量: {training_count}")
                        if training_count == 0:
                            error_msg_parts.append('\n可能的原因：模型尚未訓練，請先訓練模型。')
                        else:
                            error_msg_parts.append('\n請嘗試更清楚地描述您的問題，或使用資料庫中實際存在的表名。')
                    except Exception as e:
                        logger.error(f"檢查訓練數據失敗: {str(e)}")
                        error_msg_parts.append('\n請嘗試更清楚地描述您的問題，或使用資料庫中實際存在的表名。')
                
                error_msg = ''.join(error_msg_parts)
                
                return {
                    'sql': None,
                    'result': None,
                    'explanation': None,
                    'error': error_msg
                }
            
            logger.info(f"生成 SQL: {sql}")
            
            # 修正 SQL 中的表名，確保使用資料庫中實際存在的表名
            sql = self._correct_sql_table_names(sql)
            logger.info(f"修正後的 SQL: {sql}")
            
            # 執行 SQL（使用修正後的 SQL）
            try:
                df = self.vn.run_sql(sql=sql)
            except Exception as sql_error:
                # 如果執行失敗，記錄錯誤並返回友好的錯誤訊息
                error_str = str(sql_error)
                error_lower = error_str.lower()
                logger.error(f"SQL 執行失敗: {error_str}", exc_info=True)
                logger.error(f"失敗的 SQL: {sql}")
                
                # 根據錯誤類型提供更準確的錯誤訊息
                if "sql syntax" in error_lower or "1064" in error_lower:
                    # SQL 語法錯誤 - 提供更詳細的信息
                    error_detail = error_str.split(":")[-1].strip() if ":" in error_str else error_str[:100]
                    error_msg = f"生成的 SQL 語句有語法錯誤。\n\n生成的 SQL:\n{sql}\n\n錯誤詳情: {error_detail}"
                    logger.warning(f"SQL 語法錯誤，生成的 SQL: {sql}, 錯誤: {error_str}")
                elif "table" in error_lower and ("doesn't exist" in error_lower or "not exist" in error_lower or "不存在" in error_lower):
                    error_msg = f"查詢的表不存在。\n\n生成的 SQL:\n{sql}\n\n請檢查表名或數據庫配置。"
                    logger.warning(f"表不存在錯誤，SQL: {sql}, 錯誤: {error_str}")
                elif "column" in error_lower and ("unknown" in error_lower or "not exist" in error_lower or "不存在" in error_lower):
                    error_msg = f"查詢的列不存在。\n\n生成的 SQL:\n{sql}\n\n請檢查列名或表結構。"
                    logger.warning(f"列不存在錯誤，SQL: {sql}, 錯誤: {error_str}")
                elif "access denied" in error_lower or "permission" in error_lower or "denied" in error_lower:
                    error_msg = "數據庫訪問權限不足。請檢查數據庫用戶權限。"
                    logger.warning(f"權限錯誤，錯誤: {error_str}")
                elif "connection" in error_lower or "connect" in error_lower:
                    error_msg = "無法連接到數據庫。請檢查數據庫配置和連接狀態。"
                    logger.warning(f"連接錯誤，錯誤: {error_str}")
                else:
                    # 其他錯誤，保留詳細錯誤信息（限制長度）
                    error_detail = error_str[:300]
                    error_msg = f"SQL 執行失敗。\n\n生成的 SQL:\n{sql}\n\n錯誤詳情: {error_detail}"
                    logger.warning(f"SQL 執行失敗，SQL: {sql}, 錯誤: {error_str}")
                
                return {
                    'sql': sql,
                    'result': None,
                    'explanation': None,
                    'error': error_msg
                }
            
            # 將 DataFrame 轉換為字典列表
            if df is not None and not df.empty:
                # 轉換日期時間類型為字符串，確保 JSON 可序列化
                import pandas as pd
                import numpy as np
                from datetime import datetime, date
                
                # 複製 DataFrame 以避免修改原始數據
                df_copy = df.copy()
                
                # 轉換所有日期時間類型為字符串
                for col in df_copy.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                        df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
                    elif df_copy[col].dtype == 'object':
                        # 檢查是否包含 datetime 或 date 對象
                        df_copy[col] = df_copy[col].apply(
                            lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, datetime) 
                            else x.strftime('%Y-%m-%d') if isinstance(x, date)
                            else x
                        )
                
                result = df_copy.to_dict('records')
            else:
                result = []
            
            # 生成解釋（可選）
            try:
                explanation = self.vn.generate_explanation(question=question, sql=sql)
            except:
                explanation = "查詢執行成功"
            
            return {
                'sql': sql,
                'result': result,
                'explanation': explanation,
                'error': None
            }
            
        except Exception as e:
            error_msg = f"查詢處理失敗: {str(e)}"
            logger.error(f"ask_question 異常: {error_msg}", exc_info=True)
            
            # 根據錯誤類型提供更準確的錯誤訊息
            error_str = str(e).lower()
            if "sql syntax" in error_str or "1064" in error_str:
                error_msg = "生成的 SQL 語句有誤。請嘗試更清楚地描述您的問題，例如：\n- 顯示所有用戶\n- 統計每個部門的員工數量"
            elif "api" in error_str or "openai" in error_str or "rate limit" in error_str:
                error_msg = "OpenAI API 調用失敗。請檢查 API 配置、額度或網絡連接。"
            elif "connection" in error_str or "timeout" in error_str:
                error_msg = "無法連接到服務。請檢查網絡連接或稍後再試。"
            elif "database" in error_str or "mysql" in error_str:
                error_msg = f"數據庫錯誤: {str(e)[:200]}"
            else:
                # 對於其他錯誤，保留詳細錯誤信息（限制長度）
                error_msg = f"查詢處理失敗: {str(e)[:300]}"
            
            return {
                'sql': None,
                'result': None,
                'explanation': None,
                'error': error_msg
            }
    
    def get_training_data(self) -> Optional[List[Dict]]:
        """
        獲取當前的訓練資料
        
        Returns:
            List[Dict]: 訓練資料列表
        """
        try:
            if not self._initialized:
                raise Exception("Vanna 客戶端尚未初始化")
            
            training_data = self.vn.get_training_data()
            
            # 確保數據是可序列化的
            if training_data is not None:
                # 轉換為簡單的字典列表
                serializable_data = []
                for item in training_data:
                    if isinstance(item, dict):
                        # 只保留基本的字符串和數字類型
                        simple_item = {}
                        for key, value in item.items():
                            if isinstance(value, (str, int, float, bool, type(None))):
                                simple_item[key] = value
                            elif isinstance(value, (list, dict)):
                                # 跳過複雜的嵌套結構
                                simple_item[key] = str(value)[:100]
                        serializable_data.append(simple_item)
                return serializable_data
            
            return []
            
        except Exception as e:
            logger.error(f"獲取訓練資料失敗: {str(e)}")
            return []
    
    def get_all_tables(self) -> List[str]:
        """
        獲取數據庫中所有表的列表
        
        Returns:
            List[str]: 表名列表
        """
        try:
            if not self._initialized:
                raise Exception("Vanna 客戶端尚未初始化")
            
            # 直接查詢數據庫獲取表列表
            connection = pymysql.connect(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password,
                database=settings.mysql_database
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
            
            connection.close()
            return tables
            
        except Exception as e:
            logger.error(f"獲取表列表失敗: {str(e)}")
            return []
    
    def get_table_ddl(self, table_name: str) -> Optional[str]:
        """
        獲取指定表的 DDL
        
        Args:
            table_name: 表名
            
        Returns:
            str: DDL 語句
        """
        try:
            if not self._initialized:
                raise Exception("Vanna 客戶端尚未初始化")
            
            connection = pymysql.connect(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password,
                database=settings.mysql_database
            )
            
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                result = cursor.fetchone()
                ddl = result[1] if result else None
            
            connection.close()
            return ddl
            
        except Exception as e:
            logger.error(f"獲取表 DDL 失敗: {str(e)}")
            return None
    
    def _find_matching_table_name(self, table_name: str, actual_tables: List[str]) -> Optional[str]:
        """
        在實際表名列表中查找匹配的表名（支持模糊匹配）
        
        Args:
            table_name: 要查找的表名
            actual_tables: 實際存在的表名列表
            
        Returns:
            Optional[str]: 匹配的表名，如果找不到則返回 None
        """
        table_name_lower = table_name.lower()
        
        # 首先嘗試精確匹配（不區分大小寫）
        for actual_table in actual_tables:
            if actual_table.lower() == table_name_lower:
                logger.info(f"找到精確匹配的表名: {table_name} -> {actual_table}")
                return actual_table
        
        # 如果精確匹配失敗，嘗試單複數形式匹配
        # 例如：users -> User, user -> User
        for actual_table in actual_tables:
            actual_table_lower = actual_table.lower()
            
            # 檢查單複數形式（例如 user 和 users）
            if table_name_lower.endswith('s') and actual_table_lower == table_name_lower[:-1]:
                logger.info(f"找到單複數匹配的表名（複數->單數）: {table_name} -> {actual_table}")
                return actual_table
            elif actual_table_lower.endswith('s') and table_name_lower == actual_table_lower[:-1]:
                logger.info(f"找到單複數匹配的表名（單數->複數）: {table_name} -> {actual_table}")
                return actual_table
            elif table_name_lower + 's' == actual_table_lower:
                logger.info(f"找到單複數匹配的表名（添加s）: {table_name} -> {actual_table}")
                return actual_table
            elif actual_table_lower + 's' == table_name_lower:
                logger.info(f"找到單複數匹配的表名（移除s）: {table_name} -> {actual_table}")
                return actual_table
        
        return None
    
    def _correct_sql_table_names(self, sql: str) -> str:
        """
        修正 SQL 中的表名，確保使用資料庫中實際存在的表名
        
        Args:
            sql: 原始 SQL 語句
            
        Returns:
            str: 修正後的 SQL 語句
        """
        try:
            # 獲取實際的表名列表
            actual_tables = self.get_all_tables()
            if not actual_tables:
                logger.warning("無法獲取表名列表，跳過表名修正")
                return sql
            
            logger.info(f"資料庫中實際存在的表: {actual_tables}")
            
            # 使用正則表達式提取 SQL 中的表名
            # 匹配 FROM, JOIN, UPDATE, INSERT INTO, DELETE FROM 後面的表名
            # 支持反引號、引號或不帶引號的表名，以及表別名
            table_patterns = [
                r'(?i)\bFROM\s+[`"]?(\w+)[`"]?(?:\s+\w+)?',  # FROM table_name [alias]
                r'(?i)\bJOIN\s+[`"]?(\w+)[`"]?(?:\s+\w+)?',  # JOIN table_name [alias]
                r'(?i)\bUPDATE\s+[`"]?(\w+)[`"]?',  # UPDATE table_name
                r'(?i)\bINTO\s+[`"]?(\w+)[`"]?',  # INSERT INTO table_name
                r'(?i)\bDELETE\s+FROM\s+[`"]?(\w+)[`"]?',  # DELETE FROM table_name
            ]
            
            corrected_sql = sql
            found_tables = set()
            sql_keywords = {'select', 'where', 'group', 'order', 'having', 'limit', 'as', 'on', 'by', 'set', 'values', 'inner', 'left', 'right', 'outer', 'cross'}
            
            for pattern in table_patterns:
                matches = re.finditer(pattern, sql, re.IGNORECASE)
                for match in matches:
                    table_name = match.group(1)
                    # 跳過 SQL 關鍵字
                    if table_name.lower() not in sql_keywords:
                        found_tables.add(table_name)
            
            # 修正找到的表名
            for table_name in found_tables:
                matched_table = self._find_matching_table_name(table_name, actual_tables)
                if matched_table and matched_table != table_name:
                    # 替換表名（保持原始的大小寫和引號格式）
                    # 使用正則表達式替換，保持上下文
                    corrected_sql = re.sub(
                        r'\b' + re.escape(table_name) + r'\b',
                        matched_table,
                        corrected_sql,
                        flags=re.IGNORECASE
                    )
                    logger.info(f"修正表名: {table_name} -> {matched_table}")
                elif not matched_table:
                    logger.warning(f"無法找到匹配的表名: {table_name}，實際表名列表: {actual_tables}")
            
            return corrected_sql
            
        except Exception as e:
            logger.error(f"修正 SQL 表名時發生錯誤: {str(e)}")
            return sql  # 如果修正失敗，返回原始 SQL
    
    def test_connection(self) -> bool:
        """
        測試數據庫連接
        
        Returns:
            bool: 連接是否成功
        """
        try:
            connection = pymysql.connect(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password,
                database=settings.mysql_database
            )
            connection.close()
            return True
        except Exception as e:
            logger.error(f"數據庫連接測試失敗: {str(e)}")
            return False


# 全局 Vanna 客戶端實例
vanna_client = VannaClient()

