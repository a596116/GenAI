"""
聊天路由
"""

import logging
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.models import ChatRequest
from app.vanna_client import vanna_client
from app.conversation_manager import conversation_manager
from app.utils.suggestions import generate_suggestions
from app.utils.formatters import convert_result_to_markdown_table, convert_result_to_markdown_chart

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


def extract_result_from_history(conversation_history: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
    """
    從對話歷史中提取最近的查詢結果
    
    Args:
        conversation_history: 對話歷史列表
        
    Returns:
        最近的查詢結果列表，如果沒有則返回 None
    """
    if not conversation_history:
        return None
    
    import re
    import json
    
    # 從最近的助手消息中查找查詢結果
    for msg in reversed(conversation_history):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            # 查找表格代碼塊
            if "```table" in content:
                # 提取 table 代碼塊內容
                table_match = re.search(r"```table\s*(.*?)```", content, re.DOTALL)
                if table_match:
                    table_content = table_match.group(1)
                    # 嘗試解析表格配置
                    try:
                        # 查找 option = { 的位置
                        option_start = re.search(r"option\s*=\s*\{", table_content)
                        if not option_start:
                            continue
                        
                        # 使用算法匹配嵌套的大括號
                        start_pos = option_start.end() - 1  # 大括號的位置
                        brace_count = 0
                        end_pos = start_pos
                        
                        for i in range(start_pos, len(table_content)):
                            if table_content[i] == '{':
                                brace_count += 1
                            elif table_content[i] == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_pos = i + 1
                                    break
                        
                        if brace_count == 0:
                            # 提取 option = {...} 部分
                            option_str = table_content[option_start.start():end_pos]
                            # 清理字符串
                            cleaned_str = re.sub(r'^option\s*=\s*', '', option_str)
                            cleaned_str = re.sub(r';\s*$', '', cleaned_str)
                            cleaned_str = re.sub(r'\bNone\b', 'null', cleaned_str)
                            cleaned_str = re.sub(r'\bTrue\b', 'true', cleaned_str)
                            cleaned_str = re.sub(r'\bFalse\b', 'false', cleaned_str)
                            cleaned_str = re.sub(r',(\s*[}\]])', r'\1', cleaned_str)
                            cleaned_str = cleaned_str.replace("'", '"')
                            # 將沒有引號的鍵名加上雙引號
                            cleaned_str = re.sub(r'([{,]\s*|^\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'\1"\2":', cleaned_str)
                            
                            config = json.loads(cleaned_str)
                            if config.get('data'):
                                logger.info(f"從對話歷史中成功提取 {len(config['data'])} 條記錄")
                                return config['data']
                    except Exception as e:
                        logger.debug(f"從歷史中提取結果失敗: {str(e)}")
                        continue
    
    return None


def enhance_question_with_ai(question: str, conversation_history: List[Dict[str, str]]) -> str:
    """
    使用 AI 理解用戶意圖，將簡短指令轉換成完整的問題
    
    Args:
        question: 用戶的原始問題（可能是簡短指令如"bar圖"）
        conversation_history: 對話歷史
        
    Returns:
        增強後的完整問題
    """
    if not conversation_history or len(question.strip()) > 50:
        # 如果沒有對話歷史或問題已經很完整，直接返回
        return question
    
    try:
        # 構建上下文，包含最近的對話歷史
        context_parts = []
        recent_history = conversation_history[-4:]  # 最近2輪對話
        
        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                context_parts.append(f"用戶: {content}")
            elif role == "assistant":
                # 提取助手回答的摘要（排除表格和圖表代碼塊）
                summary = content.split("**查詢結果：**")[0].strip()
                summary = summary.split("```table")[0].strip()
                summary = summary.split("```chart")[0].strip()
                if summary:
                    context_parts.append(f"助手: {summary[:200]}")
        
        if not context_parts:
            return question
        
        context = "\n".join(context_parts)
        
        # 使用 OpenAI API 來理解用戶意圖
        from app.config import settings
        try:
            from openai import OpenAI
        except ImportError:
            # 如果沒有安裝 openai 包，嘗試使用 vanna 的 AI 能力
            logger.warning("openai 包未安裝，嘗試使用 Vanna AI 能力")
            # 使用簡單的關鍵詞匹配作為後備方案
            return question
        
        try:
            client = OpenAI(api_key=settings.openai_api_key)
            
            prompt = f"""你是一個智能助手，負責理解用戶的簡短指令並轉換成完整的問題。

對話歷史：
{context}

用戶當前問題：{question}

請分析：
1. 如果用戶的問題是簡短指令（如"bar圖"、"柱狀圖"、"pie圖"等），請根據對話歷史理解用戶的意圖
2. 將簡短指令轉換成完整的、清晰的問題
3. 如果問題已經很完整，直接返回原問題
4. 如果用戶想要改變圖表類型，請明確指出圖表類型（line/bar/pie/scatter）
5. 保持問題簡潔，不要添加多餘的解釋

只返回轉換後的問題，不要添加任何其他說明。"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的數據分析助手，擅長理解用戶意圖並轉換成清晰的問題。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            enhanced_question = response.choices[0].message.content.strip()
        except Exception as api_error:
            logger.warning(f"調用 OpenAI API 失敗: {str(api_error)}，使用原問題")
            return question
        
        # 如果 AI 返回的問題太長或包含不必要的內容，使用原問題
        if len(enhanced_question) > 200 or enhanced_question.startswith("根據"):
            logger.debug(f"AI 返回的問題可能不準確，使用原問題")
            return question
        
        logger.info(f"✅ AI 增強問題: '{question}' -> '{enhanced_question}'")
        return enhanced_question
        
    except Exception as e:
        logger.warning(f"使用 AI 增強問題時發生錯誤: {str(e)}，使用原問題")
        return question


@router.post("/api/chat")
async def chat(request: ChatRequest):
    """
    聊天端點 - 處理自然語言查詢（支援 SSE 流式響應）
    
    接收用戶的自然語言問題，使用 Vanna AI 生成 SQL 並執行查詢
    
    Args:
        request: 包含用戶問題和對話 ID 的請求
        
    Returns:
        StreamingResponse: SSE 格式的流式響應
    """
    async def generate():
        try:
            if not vanna_client.is_initialized():
                # 發送錯誤狀態
                error_status_data = {
                    "type": "status",
                    "status": {
                        "type": "error",
                        "content": "Vanna AI 服務尚未初始化，請稍後再試"
                    }
                }
                yield f"data: {json.dumps(error_status_data, ensure_ascii=False)}\n\n"
                # 同時發送 error 類型以保持向後兼容
                error_data = {
                    "error": "Vanna AI 服務尚未初始化，請稍後再試",
                    "type": "error"
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            logger.info(f"收到問題: {request.question}, 對話ID: {request.conversation_id}")
            
            # 如果提供了對話 ID，先獲取對話歷史（在保存新消息之前）
            conversation_history = []
            if request.conversation_id:
                # 先獲取現有的對話歷史
                existing_messages = conversation_manager.get_messages(request.conversation_id)
                logger.info(f"對話ID: {request.conversation_id}, 獲取到 {len(existing_messages)} 條現有消息")
                
                conversation_history = [
                    {
                        "role": msg.get("role", ""),
                        "content": msg.get("content", "")
                    }
                    for msg in existing_messages
                ]
                
                if len(conversation_history) > 0:
                    logger.info(f"獲取到對話歷史，共 {len(conversation_history)} 條消息")
                    # 記錄前幾條消息的摘要用於調試
                    for i, msg in enumerate(conversation_history[:3]):
                        role = msg.get("role", "")
                        content_preview = msg.get("content", "")[:50]
                        logger.debug(f"歷史消息 {i+1} ({role}): {content_preview}...")
                else:
                    logger.info("對話歷史為空，這是第一條消息")
                
                # 然後保存用戶消息
                conversation_manager.add_message(
                    request.conversation_id,
                    "user",
                    request.question
                )
            
            # 發送開始訊息（idle 狀態）
            status_data = {
                "type": "status",
                "status": {
                    "type": "idle",
                    "content": "準備開始處理您的問題..."
                }
            }
            yield f"data: {json.dumps(status_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            
            # 先檢查是否為圖表請求（避免將圖表請求增強成數據庫查詢）
            enhanced_user_question = request.question
            previous_result = None
            
            # 檢查原始問題是否為圖表請求
            original_question_lower = request.question.strip().lower()
            chart_keywords = ['bar', '柱狀', 'pie', '餅', 'line', '折線', 'scatter', '散點', '圖表', '圖']
            is_chart_request = any(keyword in original_question_lower for keyword in chart_keywords)
            
            if is_chart_request and conversation_history:
                # 如果是圖表請求，直接從歷史中提取結果，不要增強問題
                previous_result = extract_result_from_history(conversation_history)
                if previous_result:
                    logger.info(f"檢測到圖表類型變更請求，使用歷史查詢結果，跳過問題增強")
                else:
                    logger.warning(f"檢測到圖表請求但無法從歷史中提取結果")
            elif conversation_history and len(request.question.strip()) <= 30:
                # 如果不是圖表請求，且問題很短，使用 AI 來理解並增強問題
                enhanced_user_question = enhance_question_with_ai(request.question, conversation_history)
            
            # 發送處理中訊息（working 狀態）
            status_data = {
                "type": "status",
                "status": {
                    "type": "working",
                    "content": "正在處理您的問題..."
                }
            }
            yield f"data: {json.dumps(status_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            
            # 如果只是圖表類型變更請求
            if is_chart_request:
                if previous_result:
                    # 找到了歷史結果，直接生成圖表
                    result = {
                        'sql': None,
                        'result': previous_result,
                        'explanation': '已根據您的要求重新生成圖表',
                        'error': None
                    }
                else:
                    # 圖表請求但無法從歷史中提取結果，返回友好錯誤
                    result = {
                        'sql': None,
                        'result': None,
                        'explanation': None,
                        'error': '無法生成圖表，因為沒有找到之前的查詢結果。請先執行一個數據查詢，然後再請求圖表。'
                    }
            else:
                # 不是圖表請求，使用增強後的問題（AI 理解後的完整問題）來處理
                # 但傳遞原始問題給 Vanna，讓它也能理解上下文
                result = vanna_client.ask_question(enhanced_user_question, conversation_history=conversation_history)
            
            if result.get('error'):
                # 發送錯誤狀態
                error_status_data = {
                    "type": "status",
                    "status": {
                        "type": "error",
                        "content": result.get('error', '發生錯誤')
                    }
                }
                yield f"data: {json.dumps(error_status_data, ensure_ascii=False)}\n\n"
                # 同時發送 error 類型以保持向後兼容
                error_data = {
                    "error": result.get('error'),
                    "type": "error"
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                return
            
            # 流式發送解釋（先發送解釋）
            if result.get('explanation'):
                explanation = result.get('explanation')
                # 將解釋分成小塊發送
                chunk_size = 10
                for i in range(0, len(explanation), chunk_size):
                    chunk = explanation[i:i+chunk_size]
                    chunk_data = {
                        "content": chunk,
                        "type": "explanation"
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.03)
            
            # 發送查詢結果（轉換為 markdown 表格和圖表）
            if result.get('result'):
                result_list = result.get('result')
                markdown_table = convert_result_to_markdown_table(result_list)
                
                # 判斷是否需要生成圖表（根據增強後的問題中的關鍵詞）
                question_lower = enhanced_user_question.lower()
                chart_keywords = ['趨勢', '圖表', 'chart', '圖', '可視化', '分析', '統計圖', '折線圖', '柱狀圖', '餅圖', 'bar', 'pie', 'line', 'scatter']
                should_generate_chart = any(keyword in question_lower for keyword in chart_keywords)
                
                # 如果結果數據適合生成圖表（至少有2列數據，且數據量適中）
                can_generate_chart = (
                    len(result_list) > 0 and 
                    len(result_list[0].keys()) >= 2 and 
                    len(result_list) <= 1000  # 限制數據量，避免圖表過於複雜
                )
                
                # 將 markdown 表格作為解釋的一部分發送
                result_header = f"\n\n**查詢結果：** 共 {len(result_list)} 條記錄\n\n"
                result_content = result_header + markdown_table
                
                # 如果需要且可以生成圖表，添加圖表
                if should_generate_chart and can_generate_chart:
                    try:
                        # 自動判斷圖表類型（基於增強後的問題）
                        chart_type = 'line'  # 默認折線圖
                        if '柱狀' in question_lower or 'bar' in question_lower:
                            chart_type = 'bar'
                        elif '餅' in question_lower or 'pie' in question_lower:
                            chart_type = 'pie'
                        elif '散點' in question_lower or 'scatter' in question_lower:
                            chart_type = 'scatter'
                        
                        # 獲取列名
                        columns_keys = list(result_list[0].keys())
                        
                        # 智能選擇 X 軸和 Y 軸
                        # 優先選擇包含日期、時間、名稱等關鍵詞的列作為 X 軸
                        x_axis_key = None
                        x_axis_candidates = ['date', 'time', '日期', '時間', 'name', '名稱', 'id', 'month', '月份', 'year', '年份']
                        for key in columns_keys:
                            key_lower = key.lower()
                            if any(candidate in key_lower for candidate in x_axis_candidates):
                                x_axis_key = key
                                break
                        
                        # 如果沒找到合適的 X 軸，使用第一列
                        if x_axis_key is None:
                            x_axis_key = columns_keys[0] if columns_keys else None
                        
                        # Y 軸選擇除 X 軸外的所有數值列
                        y_axis_keys = [key for key in columns_keys if key != x_axis_key]
                        
                        # 過濾出數值類型的列作為 Y 軸
                        numeric_y_keys = []
                        for key in y_axis_keys:
                            # 檢查該列是否主要為數值類型
                            numeric_count = 0
                            for row in result_list[:10]:  # 檢查前10行
                                value = row.get(key)
                                if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit()):
                                    numeric_count += 1
                            if numeric_count >= 5:  # 如果至少5行是數值，認為是數值列
                                numeric_y_keys.append(key)
                        
                        # 如果沒有找到數值列，使用所有 Y 軸列
                        if not numeric_y_keys:
                            numeric_y_keys = y_axis_keys[:3]  # 最多使用3個 Y 軸
                        
                        if x_axis_key and numeric_y_keys:
                            markdown_chart = convert_result_to_markdown_chart(
                                result=result_list,
                                chart_type=chart_type,
                                x_axis_key=x_axis_key,
                                y_axis_keys=numeric_y_keys
                            )
                            result_content += f"\n\n**數據可視化：**\n\n{markdown_chart}"
                    except Exception as e:
                        logger.warning(f"生成圖表時發生錯誤: {str(e)}")
                        # 如果生成圖表失敗，繼續使用表格
                
                # 將結果以 explanation 類型發送（這樣會被渲染為 markdown）
                chunk_size = 50
                for i in range(0, len(result_content), chunk_size):
                    chunk = result_content[i:i+chunk_size]
                    chunk_data = {
                        "content": chunk,
                        "type": "explanation"
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.02)
                
                await asyncio.sleep(0.1)
            
            # 如果提供了對話 ID，保存助手回覆
            if request.conversation_id:
                # 組合完整的助手回覆（不包含 SQL，與流式響應保持一致）
                full_response = ""
                # 只包含真正的解釋內容，過濾掉簡單的狀態訊息
                explanation = result.get('explanation', '').strip()
                simple_status_messages = ['查詢執行成功', '查詢完成', '思考完成', '正在處理您的問題...']
                if explanation and explanation not in simple_status_messages:
                    full_response += explanation
                if result.get('result'):
                    result_list = result.get('result')
                    markdown_table = convert_result_to_markdown_table(result_list)
                    full_response += f"\n\n**查詢結果：** 共 {len(result_list)} 條記錄\n\n{markdown_table}"
                    
                    # 保存時也包含圖表（如果有的話）
                    question_lower = request.question.lower()
                    chart_keywords = ['趨勢', '圖表', 'chart', '圖', '可視化', '分析', '統計圖', '折線圖', '柱狀圖', '餅圖']
                    should_generate_chart = any(keyword in question_lower for keyword in chart_keywords)
                    
                    if should_generate_chart and len(result_list) > 0 and len(result_list[0].keys()) >= 2 and len(result_list) <= 1000:
                        try:
                            chart_type = 'line'
                            if '柱狀' in question_lower or 'bar' in question_lower:
                                chart_type = 'bar'
                            elif '餅' in question_lower or 'pie' in question_lower:
                                chart_type = 'pie'
                            elif '散點' in question_lower or 'scatter' in question_lower:
                                chart_type = 'scatter'
                            
                            columns_keys = list(result_list[0].keys())
                            x_axis_key = None
                            x_axis_candidates = ['date', 'time', '日期', '時間', 'name', '名稱', 'id', 'month', '月份', 'year', '年份']
                            for key in columns_keys:
                                key_lower = key.lower()
                                if any(candidate in key_lower for candidate in x_axis_candidates):
                                    x_axis_key = key
                                    break
                            
                            if x_axis_key is None:
                                x_axis_key = columns_keys[0] if columns_keys else None
                            
                            y_axis_keys = [key for key in columns_keys if key != x_axis_key]
                            numeric_y_keys = []
                            for key in y_axis_keys:
                                numeric_count = 0
                                for row in result_list[:10]:
                                    value = row.get(key)
                                    if isinstance(value, (int, float)) or (isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit()):
                                        numeric_count += 1
                                if numeric_count >= 5:
                                    numeric_y_keys.append(key)
                            
                            if not numeric_y_keys:
                                numeric_y_keys = y_axis_keys[:3]
                            
                            if x_axis_key and numeric_y_keys:
                                markdown_chart = convert_result_to_markdown_chart(
                                    result=result_list,
                                    chart_type=chart_type,
                                    x_axis_key=x_axis_key,
                                    y_axis_keys=numeric_y_keys
                                )
                                full_response += f"\n\n**數據可視化：**\n\n{markdown_chart}"
                        except Exception as e:
                            logger.warning(f"保存圖表時發生錯誤: {str(e)}")
                
                conversation_manager.add_message(
                    request.conversation_id,
                    "assistant",
                    full_response
                )
            
            # 發送成功狀態
            success_status_data = {
                "type": "status",
                "status": {
                    "type": "success",
                    "content": "處理完成"
                }
            }
            yield f"data: {json.dumps(success_status_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.1)
            
            # 生成並發送推薦問題
            suggestions = generate_suggestions(
                question=request.question,
                sql=result.get('sql'),
                result=result.get('result')
            )
            if suggestions:
                suggestions_data = {
                    "type": "suggestions",
                    "suggestions": suggestions
                }
                yield f"data: {json.dumps(suggestions_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.05)
            
            # 發送完成訊息
            yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            
            logger.info(f"查詢成功，返回 {len(result.get('result', [])) if result.get('result') else 0} 條結果")
            
        except Exception as e:
            logger.error(f"聊天端點錯誤: {str(e)}")
            # 發送錯誤狀態
            error_status_data = {
                "type": "status",
                "status": {
                    "type": "error",
                    "content": f"處理請求時發生錯誤: {str(e)}"
                }
            }
            yield f"data: {json.dumps(error_status_data, ensure_ascii=False)}\n\n"
            # 同時發送 error 類型以保持向後兼容
            error_data = {
                "error": f"處理請求時發生錯誤: {str(e)}",
                "type": "error"
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

