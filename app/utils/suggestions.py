"""
推薦問題生成工具
"""

import logging
import json
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_suggestions(question: str, sql: Optional[str] = None, result: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """
    根據用戶問題、SQL 和查詢結果使用 AI 生成推薦問題
    
    Args:
        question: 用戶的問題
        sql: 生成的 SQL 查詢（可選）
        result: 查詢結果（可選）
        
    Returns:
        List[str]: 推薦問題列表
    """
    try:
        from app.config import settings
        from openai import OpenAI
        
        client = OpenAI(api_key=settings.openai_api_key)
        
        # 構建上下文信息
        context_parts = []
        
        # 添加用戶問題
        context_parts.append(f"用戶剛才查詢的問題：{question}")
        
        # 如果有 SQL，添加 SQL 信息
        if sql:
            context_parts.append(f"執行的 SQL 查詢：{sql}")
        
        # 如果有查詢結果，添加結果摘要
        if result and len(result) > 0:
            columns = list(result[0].keys())
            row_count = len(result)
            
            # 提取結果的樣本數據（前3行）
            sample_data = result[:3]
            
            context_parts.append(f"查詢結果：共 {row_count} 條記錄")
            context_parts.append(f"結果欄位：{', '.join(columns)}")
            context_parts.append(f"結果樣本：{json.dumps(sample_data, ensure_ascii=False, default=str)}")
        
        context = "\n".join(context_parts)
        
        prompt = f"""你是一個智能數據查詢助手。請根據用戶剛才的查詢，生成4個相關的、有價值的後續查詢建議。

{context}

要求：
1. 建議必須與用戶剛才的查詢高度相關
2. 建議應該基於查詢結果的欄位和數據內容
3. 建議應該是有意義的、可以執行的查詢問題
4. 建議應該幫助用戶深入探索數據或從不同角度分析
5. 使用繁體中文，問題要簡潔清晰
6. 避免重複用戶已經查詢過的內容

請返回 JSON 格式的建議列表：
{{
  "suggestions": [
    "建議問題1",
    "建議問題2",
    "建議問題3",
    "建議問題4"
  ]
}}

只返回 JSON，不要其他說明文字。"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一個專業的數據分析助手，擅長根據用戶的查詢生成相關且有價值的後續問題建議。只返回有效的 JSON 格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
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
        
        # 解析 JSON
        try:
            parsed = json.loads(result_text)
            suggestions = parsed.get("suggestions", [])
            
            # 確保返回的是列表且最多4個
            if isinstance(suggestions, list):
                suggestions = [s for s in suggestions if s and isinstance(s, str)][:4]
                if suggestions:
                    logger.info(f"✅ AI 生成了 {len(suggestions)} 個相關建議")
                    return suggestions
        except json.JSONDecodeError as e:
            logger.warning(f"AI 返回的 JSON 格式錯誤: {str(e)}, 原始內容: {result_text[:200]}")
        
    except ImportError:
        logger.warning("openai 包未安裝，無法使用 AI 生成建議")
    except Exception as e:
        logger.warning(f"使用 AI 生成建議時發生錯誤: {str(e)}")
    
    # 如果 AI 生成失敗，返回空列表（不顯示不相關的建議）
    logger.info("AI 生成建議失敗，返回空列表")
    return []

