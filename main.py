import argparse
import json
from datetime import datetime
from typing import List, Dict, Any

from database import Database
from realtime_stock_data import RealTimeStockDataFetcher
from llm_service import LLMService
from analysis_framework import MultiRoleAnalyzer


class StockAnalysisSystem:
    def __init__(self, use_multi_role: bool = True):
        self.db = Database()
        self.stock_fetcher = RealTimeStockDataFetcher()
        self.llm_service = LLMService()
        self.multi_analyzer = MultiRoleAnalyzer() if use_multi_role else None
        self.use_multi_role = use_multi_role

    def analyze_single_stock(self, stock_code: str) -> Dict[str, Any]:
        """分析单个股票"""
        print(f"开始分析股票: {stock_code}")

        stock_info = self.db.get_stock_info(stock_code)
        if not stock_info:
            return {
                'code': stock_code,
                'name': '未知',
                'error': '未找到股票基本信息'
            }

        full_code = stock_info.get('full_code')
        history_data = self.db.get_stock_history(stock_code, days=30)
        real_time_data = self.stock_fetcher.get_real_time_data(full_code)

        if not real_time_data:
            return {
                'code': stock_code,
                'name': stock_info.get('name', '未知'),
                'error': '获取实时数据失败'
            }

        if self.use_multi_role and self.multi_analyzer:
            analysis_result = self.multi_analyzer.analyze(
                real_time_data, history_data, stock_info
            )
        else:
            analysis_result = self.llm_service.analyze_stock(
                real_time_data, history_data, stock_info
            )
        print(f"分析结果: {analysis_result}")
        return {
            'code': stock_code,
            'name': stock_info.get('name', '未知'),
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': real_time_data.get('current_price', 0),
            'change_percent': real_time_data.get('change_percent', 0),
            'recommendation': analysis_result.get('recommendation', '保持'),
            'reason': analysis_result.get('reason', ''),
            'action': analysis_result.get('action', '保持'),
            'predicted_price': analysis_result.get('predicted_price', 0),
            'predicted_buy_price': analysis_result.get('predicted_buy_price', 0),
            'predicted_sell_price': analysis_result.get('predicted_sell_price', 0),
            'confidence': analysis_result.get('confidence', 0.5)
        }

    def analyze_multiple_stocks(self, stock_codes: List[str],
                                max_workers: int = 100) -> List[Dict[str, Any]]:
        """分析多个股票"""
        from concurrent.futures import ThreadPoolExecutor
        
        results = []

        def analyze_stock(code):
            try:
                result = self.analyze_single_stock(code)
                print(f"完成分析: {code}")
                return result
            except Exception as e:
                print(f"分析股票 {code} 时出错: {e}")
                return {
                    'code': code,
                    'name': '未知',
                    'error': str(e)
                }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(analyze_stock, stock_codes))

        return results

    def get_all_stocks_analysis(self, sample_size: int = None) -> List[Dict[str, Any]]:
        """分析所有股票"""
        all_codes = self.db.get_all_stock_codes()

        if sample_size and sample_size < len(all_codes):
            import random
            all_codes = random.sample(all_codes, sample_size)

        print(f"开始分析 {len(all_codes)} 只股票...")
        return self.analyze_multiple_stocks(all_codes)

    def save_results(self, results: List[Dict[str, Any]], filename: str):
        """保存分析结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {filename}")

    def print_results(self, results: List[Dict[str, Any]]):
        """打印分析结果"""
        for result in results:
            if 'error' in result:
                print(f"股票 {result['code']} 分析失败: {result['error']}")
            else:
                print(f"\n=== {result['name']} ({result['code']}) ===")
                print(f"当前价格: {result['current_price']}")
                print(f"涨跌幅: {result['change_percent']}%")
                print(f"建议: {result['recommendation']}")
                print(f"动作: {result['action']}")
                print(f"预测价格(T+1): {result['predicted_price']}")
                print(f"预测买入价: {result['predicted_buy_price']}")
                print(f"预测卖出价: {result['predicted_sell_price']}")
                print(f"信心度: {result['confidence']}")
                print(f"推荐原因: {result['reason']}")




def main():
    parser = argparse.ArgumentParser(description='A股T+1选股系统')
    parser.add_argument('--stock', '-s', type=str, help='分析单个股票代码')
    parser.add_argument('--stocks', '-l', type=str, nargs='+', help='分析多个股票代码')
    parser.add_argument('--all', '-a', action='store_true', help='分析所有股票')
    parser.add_argument('--sample', type=int, default=10, help='随机分析样本数量')
    parser.add_argument('--output', '-o', type=str, default='stock_analysis_result.json',
                        help='输出结果文件名')
    parser.add_argument('--simple', action='store_true', help='使用简单分析模式')

    args = parser.parse_args()

    system = StockAnalysisSystem(use_multi_role=not args.simple)

    try:
        if args.stock:
            results = [system.analyze_single_stock(args.stock)]
        elif args.stocks:
            results = system.analyze_multiple_stocks(args.stocks)
        elif args.all:
            results = system.get_all_stocks_analysis()
        else:
            results = system.get_all_stocks_analysis(sample_size=args.sample)

        system.print_results(results)
        system.save_results(results, args.output)

    except KeyboardInterrupt:
        print("\n用户中断分析")
    except Exception as e:
        print(f"分析过程中出现错误: {e}")
    finally:
        print("分析结束")


if __name__ == "__main__":
    main()