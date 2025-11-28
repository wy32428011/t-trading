from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.constants import END
from langgraph.graph import StateGraph
import time

from llm_service import LLMService, llm_cache, CACHE_EXPIRY
from typing import Dict, Any, List, TypedDict


class MessageState(TypedDict):
    """状态对象"""
    stock_data: Dict[str, Any]
    history_data: List[Dict[str, Any]]
    stock_info: Dict[str, Any]
    fundamental_analyst: str
    technical_analysis: str
    trader_analysis: str
    final_recommendation: str



class MultiRoleAnalyzer:
    def __init__(self):
        self.llm_service = LLMService()
        self.graph = self._build_graph()
    def _build_graph(self):

        workflow = StateGraph(MessageState)

        workflow.add_node("fundamental_analyst", self.fundamental_analysis_node)
        workflow.add_node("technical_analyst", self.technical_analysis_node)
        workflow.add_node("trader_analyst", self.trader_analysis_node)
        workflow.add_node("final_decision", self.final_decision_node)

        workflow.set_entry_point("fundamental_analyst")
        workflow.add_edge("fundamental_analyst", "technical_analyst")
        workflow.add_edge("technical_analyst", "trader_analyst")
        workflow.add_edge("trader_analyst", "final_decision")
        workflow.add_edge("final_decision", END)

        return workflow.compile()

    def fundamental_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """基本面分析师节点"""
        prompt = f"""
作为基本面分析师，请对以下股票进行深入的基本面分析：

股票基本信息：
- 代码: {state['stock_data'].get('code', '')}
- 名称: {state['stock_data'].get('name', '')}
- 行业: {state['stock_info'].get('sector', '') if state['stock_info'] else '未知'}
- 总市值: {state['stock_data'].get('total_market_value', 0)}万元
- 流通市值: {state['stock_data'].get('circulating_market_value', 0)}万元
- 市盈率: {state['stock_data'].get('pe_ratio', 0)}
- 市净率: {state['stock_data'].get('pb_ratio', 0)}

请分析：
1. 公司财务状况和盈利能力
2. 行业地位和竞争优势
3. 估值水平是否合理
4. 长期投资价值

请给出详细的基本面分析报告。
"""

        response = self.llm_service.llm.invoke([
            SystemMessage(content="你是一个专业的股票基本面分析师，擅长财务分析和估值评估。"),
            HumanMessage(content=prompt)
        ])
        state['fundamental_analyst'] = response.content
        # 只打印关键信息，减少输出开销
        # print(f"基本面分析师: {response.content}")
        return state

    def technical_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """技术指标分析师节点"""

        history_summary = "\n".join([
            f"日期: {d['date']}, 开盘: {d['open']}, 最高: {d['high']}, 最低: {d['low']}, 收盘: {d['close']}, "
            f"成交量: {d['volume']}, 涨跌幅: {d['pctChg']}%"
            for d in state['history_data'][:15]
        ])

        prompt = f"""
作为技术指标分析师，请对以下股票进行技术分析：

实时数据：
- 当前价格: {state['stock_data'].get('current_price', 0)}
- 涨跌幅: {state['stock_data'].get('change_percent', 0)}%
- 开盘价: {state['stock_data'].get('open', 0)}
- 最高价: {state['stock_data'].get('high', 0)}
- 最低价: {state['stock_data'].get('low', 0)}
- 成交量: {state['stock_data'].get('volume_hand', 0)}手

历史数据（最近15天）：
{history_summary}

请分析：
1. 价格趋势和支撑阻力位
2. 成交量变化和资金流向
3. 技术指标信号（如MACD、RSI、均线等）
4. 短期交易机会

请给出详细的技术分析报告。
"""

        response = self.llm_service.llm.invoke([
            SystemMessage(content="你是一个专业的股票技术分析师，擅长技术指标分析和趋势判断。"),
            HumanMessage(content=prompt)
        ])
        state['technical_analysis'] = response.content
        # 只打印关键信息，减少输出开销
        # print(f"技术分析师: {response.content}")
        return state

    def trader_analysis_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """交易员分析节点"""

        prompt = f"""
作为股市交易员，请基于基本面分析和技术分析，给出具体的交易建议：

基本面分析：
{state['fundamental_analyst']}

技术分析：
{state['technical_analysis']}

请综合考虑：
1. 风险收益比
2. 市场情绪和资金面
3. 交易时机和仓位管理
4. 止损止盈策略

请给出具体的交易建议。
"""

        response = self.llm_service.llm.invoke([
            SystemMessage(content="你是一个经验丰富的股市交易员，擅长风险管理和交易策略制定。"),
            HumanMessage(content=prompt)
        ])
        state['trader_analysis'] = response.content
        # 只打印关键信息，减少输出开销
        # print(f"交易员分析师: {response.content}")
        return state

    def final_decision_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """最终决策节点"""

        prompt = f"""
请基于三位专家的分析，给出最终的T+1选股建议：

基本面分析：
{state['fundamental_analyst']}

技术分析：
{state['technical_analysis']}

交易员分析：
{state['trader_analysis']}

请给出具体的投资建议，包括：
- 建议（买入/卖出/保持）
- 推荐原因
- 动作（买/卖/保持）
- 预测价格（T+1）
- 预测买入价格（T+1）
- 预测卖出价格（T+1）
- 预测信心（0-1）

请以JSON格式返回结果。
"""

        response = self.llm_service.llm.invoke([
            SystemMessage(content="你是首席投资官，需要综合各方分析做出最终投资决策。"),
            HumanMessage(content=prompt)
        ])
        # 只打印关键信息，减少输出开销
        # print(f"大模型最终决策结果: {response.content}")
        final_result = self.llm_service._parse_response(response.content)
        state['final_recommendation'] = final_result
        return state

    def analyze(self, stock_data: Dict[str, Any],
                history_data: List[Dict[str, Any]],
                stock_info: Dict[str, Any]) -> Dict[str, Any]:
        """执行多角色分析"""

        # 获取当前日期，作为缓存键的一部分
        current_date = time.strftime("%Y-%m-%d")
        # 构建缓存键：股票代码+日期+模式
        cache_key = f"{stock_data.get('code', '')}_{current_date}_multi"
        
        # 检查缓存中是否存在有效的分析结果
        if cache_key in llm_cache:
            cached_result, timestamp = llm_cache[cache_key]
            # 检查缓存是否过期
            if time.time() - timestamp < CACHE_EXPIRY:
                return cached_result

        try:
            result = self.graph.invoke(MessageState(
                stock_data=stock_data,
                history_data=history_data,
                stock_info=stock_info,
                fundamental_analyst="",
                technical_analysis_node="",
            ))
            # 直接从结果字典中获取final_recommendation
            # print(f"最终推荐结果: {result['final_recommendation']}")
            final_result = result["final_recommendation"]
            
            # 将结果存入缓存
            llm_cache[cache_key] = (final_result, time.time())
            return final_result
        except Exception as e:
            print(f"多角色分析错误: {e}")
            return self.llm_service.analyze_stock(stock_data, history_data, stock_info)
