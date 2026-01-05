"""
格式化工具函數
"""

from typing import List, Dict, Any, Optional


def convert_result_to_markdown_chart(
    result: List[Dict[str, Any]],
    chart_type: str = 'line',
    x_axis_key: Optional[str] = None,
    y_axis_keys: Optional[List[str]] = None,
    x_axis_type: str = 'category',
    y_axis_type: str = 'value'
) -> str:
    """
    將查詢結果轉換為 markdown chart 格式（使用 echarts 配置）
    
    Args:
        result: 查詢結果列表
        chart_type: 圖表類型，可選值：'line', 'bar', 'pie', 'scatter' 等
        x_axis_key: X 軸對應的數據鍵名（如果為 None，則使用第一列）
        y_axis_keys: Y 軸對應的數據鍵名列表（如果為 None，則使用除 X 軸外的所有列）
        x_axis_type: X 軸類型，可選值：'category', 'value', 'time', 'log'
        y_axis_type: Y 軸類型，可選值：'value', 'category', 'time', 'log'
        
    Returns:
        str: markdown 代碼塊字符串，包含圖表配置
    """
    if not result or len(result) == 0:
        return "查詢結果為空，無法生成圖表"
    
    # 獲取所有列名
    columns_keys = list(result[0].keys())
    
    # 確定 X 軸鍵名
    if x_axis_key is None:
        x_axis_key = columns_keys[0] if columns_keys else None
    
    if x_axis_key is None:
        return "無法確定 X 軸，查詢結果為空"
    
    # 確定 Y 軸鍵名列表
    if y_axis_keys is None:
        y_axis_keys = [key for key in columns_keys if key != x_axis_key]
    
    if not y_axis_keys:
        return "無法確定 Y 軸，請指定至少一個 Y 軸數據列"
    
    # 提取 X 軸數據
    x_axis_data = []
    for row in result:
        value = row.get(x_axis_key, "")
        if value is None:
            value = ""
        x_axis_data.append(str(value))
    
    # 構建 series 數據
    series_data = []
    for y_key in y_axis_keys:
        y_data = []
        for row in result:
            value = row.get(y_key, None)
            # 處理 None 值和非數字值
            if value is None:
                y_data.append(None)
            elif isinstance(value, (int, float)):
                y_data.append(value)
            else:
                # 嘗試轉換為數字
                try:
                    y_data.append(float(value))
                except (ValueError, TypeError):
                    y_data.append(None)
        
        series_data.append({
            'name': y_key,
            'data': y_data
        })
    
    # 輔助函數：轉義字符串中的特殊字符（用於單引號字符串）
    def escape_string_for_single_quote(s: str) -> str:
        """轉義字符串中的特殊字符，用於單引號字符串格式"""
        return str(s).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
    
    # 構建 JavaScript 對象格式的字符串（key 不使用引號，參考 markdown.ts）
    option_str = "option = {\n"
    option_str += f"  type: '{chart_type}',\n"
    option_str += "  data: [\n"
    for series in series_data:
        option_str += f"    {{\n"
        option_str += f"      name: '{escape_string_for_single_quote(series['name'])}',\n"
        option_str += f"      data: {series['data']},\n"
        option_str += f"    }},\n"
    option_str += "  ],\n"
    option_str += "  xAxis: {\n"
    option_str += f"    type: '{x_axis_type}',\n"
    option_str += f"    data: {x_axis_data},\n"
    option_str += "  },\n"
    option_str += "  yAxis: {\n"
    option_str += f"    type: '{y_axis_type}',\n"
    option_str += "  },\n"
    option_str += "}\n"
    
    # 包裝為 markdown 代碼塊
    markdown_chart = f"```chart\n{option_str}```"
    
    return markdown_chart


def convert_result_to_markdown_table(result: List[Dict[str, Any]]) -> str:
    """
    將查詢結果轉換為 markdown 表格格式（新格式：包含 columns 和 data 的配置對象）
    
    Args:
        result: 查詢結果列表
        
    Returns:
        str: markdown 代碼塊字符串，包含表格配置
    """
    if not result or len(result) == 0:
        return "查詢結果為空"
    
    # 獲取所有列名
    columns_keys = list(result[0].keys())
    
    # 構建 columns 配置（包含 label、prop、width）
    columns_config = []
    for col_key in columns_keys:
        # 計算列寬（根據列名長度和數據最大長度）
        max_data_length = max(
            [len(str(row.get(col_key, ""))) for row in result],
            default=len(col_key)
        )
        width = max(len(col_key), max_data_length, 10) * 8  # 字符數轉換為像素寬度（大約）
        width = min(width, 200)  # 限制最大寬度
        
        columns_config.append({
            'label': col_key,
            'prop': col_key,
            'width': width
        })
    
    # 構建 data 配置（處理 None 值）
    data_config = []
    for row in result:
        row_dict = {}
        for col_key in columns_keys:
            value = row.get(col_key, "")
            # 處理 None 值
            if value is None:
                value = ""
            row_dict[col_key] = value
        data_config.append(row_dict)
    
    # 輔助函數：轉義字符串中的特殊字符（用於單引號字符串）
    def escape_string_for_single_quote(s: str) -> str:
        """轉義字符串中的特殊字符，用於單引號字符串格式"""
        return str(s).replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
    
    # 構建 JavaScript 對象格式的字符串（key 不使用引號，參考 markdown.ts）
    option_str = "option = {\n"
    option_str += "  columns: [\n"
    for col in columns_config:
        option_str += f"    {{\n"
        option_str += f"      label: '{escape_string_for_single_quote(col['label'])}',\n"
        option_str += f"      prop: '{escape_string_for_single_quote(col['prop'])}',\n"
        option_str += f"      width: {col['width']},\n"
        option_str += f"    }},\n"
    option_str += "  ],\n"
    option_str += "  data: [\n"
    for row in data_config:
        option_str += f"    {{\n"
        for col_key in columns_keys:
            value = row[col_key]
            # key 不使用引號，直接使用（假設 key 是有效的 JavaScript 標識符）
            # 如果是字符串，用單引號包裹並轉義；否則直接使用
            if isinstance(value, str):
                escaped_value = escape_string_for_single_quote(value)
                option_str += f"      {col_key}: '{escaped_value}',\n"
            elif isinstance(value, (int, float, bool)):
                option_str += f"      {col_key}: {value},\n"
            elif value is None:
                option_str += f"      {col_key}: null,\n"
            else:
                # 其他類型轉為字符串
                escaped_value = escape_string_for_single_quote(str(value))
                option_str += f"      {col_key}: '{escaped_value}',\n"
        option_str += f"    }},\n"
    option_str += "  ],\n"
    option_str += "}\n"
    
    # 包裝為 markdown 代碼塊
    markdown_table = f"```table\n{option_str}```"
    
    return markdown_table

