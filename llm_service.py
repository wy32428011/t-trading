from typing import Dict, Any, List
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from setting import settings


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

        prompt = self._build_analysis_prompt(stock_data, history_data, stock_info)

        try:
            response = self.llm.invoke([
                SystemMessage(content="你是一个专业的股票分析师，需要基于股票历史数据、实时数据和基本面信息进行分析。"),
                HumanMessage(content=prompt)
            ])
            print(f"大模型分析结果: {response.content}")
            return self._parse_response(response.content)

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

        history_summary = "\n".join([
            f"日期: {d['date']}, 开盘: {d['open']}, 最高: {d['high']}, 最低: {d['low']}, 收盘: {d['close']}, "
            f"成交量: {d['volume']}, 涨跌幅: {d['pctChg']}%"
            for d in history_data[:10]  # 只取最近10天的数据
        ])

        prompt = f"""
请基于以下股票数据进行专业的T+1选股分析：

股票基本信息：
- 代码: {stock_data.get('code', '')}
- 名称: {stock_data.get('name', '')}
- 行业: {stock_info.get('sector', '') if stock_info else '未知'}
- 总市值: {stock_data.get('total_market_value', 0)}万元
- 流通市值: {stock_data.get('circulating_market_value', 0)}万元
- 上市日期: {stock_info.get('ipo_date', '') if stock_info else '未知'}

实时数据：
- 当前价格: {stock_data.get('current_price', 0)}
- 涨跌幅: {stock_data.get('change_percent', 0)}%
- 开盘价: {stock_data.get('open', 0)}
- 最高价: {stock_data.get('high', 0)}
- 最低价: {stock_data.get('low', 0)}
- 成交量: {stock_data.get('volume_hand', 0)}手
- 成交额: {stock_data.get('amount_10k', 0)}万元
- 换手率: {stock_data.get('turnover_rate', 0)}%
- 市盈率: {stock_data.get('pe_ratio', 0)}
- 市净率: {stock_data.get('pb_ratio', 0)}

历史数据（最近10天）：
{history_summary}

请进行多角度分析：
1. 基本面分析：评估公司财务状况、行业地位、估值水平
2. 技术面分析：分析价格趋势、成交量变化、技术指标
3. 市场情绪分析：考虑市场整体情绪和资金流向

请给出具体的T+1交易建议，包括：
- 建议（买入/卖出/保持）
- 推荐原因（详细分析）
- 动作（买/卖/保持）
- 预测价格（T+1）
- 预测买入价格（T+1）
- 预测卖出价格（T+1）
- 预测信心（0-1之间的数值）

请以JSON格式返回结果，包含以下字段：
recommendation, reason, action, predicted_price, predicted_buy_price, predicted_sell_price, confidence
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