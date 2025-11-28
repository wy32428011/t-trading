from typing import Dict, Any, List
import os
import time
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from setting import settings

# 缓存字典，键为股票代码+日期+模式，值为(结果, 时间戳)
llm_cache = {}
# 缓存有效期（秒），设置为1天
CACHE_EXPIRY = 24 * 60 * 60


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            temperature=0.1
        )

    def analyze_stock(self, stock_data: Dict[str, Any],
                      history_data: List[Dict[str, Any]],
                      stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """使用大模型分析股票数据"""
        
        # 获取当前日期，作为缓存键的一部分
        current_date = time.strftime("%Y-%m-%d")
        # 构建缓存键：股票代码+日期+模式
        cache_key = f"{stock_data.get('code', '')}_{current_date}_single"
        
        # 检查缓存中是否存在有效的分析结果
        if cache_key in llm_cache:
            cached_result, timestamp = llm_cache[cache_key]
            # 检查缓存是否过期
            if time.time() - timestamp < CACHE_EXPIRY:
                return cached_result
        
        prompt = self._build_analysis_prompt(stock_data, history_data, stock_info)

        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个专业的股票分析师，需要基于股票历史数据、实时数据和基本面信息进行分析。"),
                HumanMessage(content=prompt)
            ])
            # 只打印关键信息，减少输出开销
            # print(f"大模型分析结果: {response.content}")
            result = self._parse_response(response.content)
            
            # 将结果存入缓存
            llm_cache[cache_key] = (result, time.time())
            return result

        except Exception as e:
            print(f"大模型分析错误: {e}")
            return {
                'recommendation': '保持',
                'reason': '分析过程中出现错误',
                'action': '保持',
                'predicted_price': stock_data.get('current_price', 0),
                'predicted_buy_price': stock_data.get('current_price', 0),
                'predicted_sell_price': stock_data.get('current_price', 0),
                'confidence': 0.5
            }

    def _build_analysis_prompt(self, stock_data: Dict[str, Any],
                               history_data: List[Dict[str, Any]],
                               stock_info: Dict[str, Any]) -> str:
        """构建分析提示词"""

        # 只取最近3天的历史数据，进一步减少上下文长度
        history_summary = "\n".join([
            f"{d['date']}: {round(d['close'], 2)}({d['pctChg']}%)"
            for d in history_data[:3]  # 只取最近3天的数据
        ])

        prompt = f"""
请基于以下股票数据进行T+1选股分析：

基本信息：
- 代码: {stock_data.get('code', '')}
- 名称: {stock_data.get('name', '')}
- 行业: {stock_info.get('sector', '') if stock_info else '未知'}
- PE: {stock_data.get('pe_ratio', 0)}
- PB: {stock_data.get('pb_ratio', 0)}

实时数据：
- 现价: {stock_data.get('current_price', 0)}
- 涨跌幅: {stock_data.get('change_percent', 0)}%
- 成交量: {stock_data.get('volume_hand', 0)}手

近3天走势：
{history_summary}

请给出T+1交易建议，包括：
- recommendation: 买入/卖出/保持
- reason: 推荐原因
- action: 买/卖/保持
- predicted_price: T+1预测价格
- predicted_buy_price: T+1预测买入价
- predicted_sell_price: T+1预测卖出价
- confidence: 0-1的信心值

请严格以JSON格式返回，不要添加其他内容。
"""
        return prompt

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析大模型响应"""
        import json
        import re

        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'recommendation': result.get('建议', '保持'),
                    'reason': result.get('推荐原因', '分析完成'),
                    'action': result.get('动作', '保持'),
                    'predicted_price': float(result.get('预测价格',result.get('预测价格_T+1', 0))),
                    'predicted_buy_price': float(result.get('预测买入价格', result.get('预测买入价格_T+1', 0))),
                    'predicted_sell_price': float(result.get('预测卖出价格', result.get('预测卖出价格_T+1', 0))),
                    'confidence': float(result.get('预测信心', -0.5))
                }
        except (json.JSONDecodeError, ValueError):
            pass

        return {
            'recommendation': '保持',
            'reason': '分析完成',
            'action': '保持',
            'predicted_price': 0,
            'predicted_buy_price': 0,
            'predicted_sell_price': 0,
            'confidence': 0.5
        }