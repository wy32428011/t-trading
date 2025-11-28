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
                                max_workers: int = 20, save_batch_size: int = None,
                                output_file: str = None) -> List[Dict[str, Any]]:
        """分析多个股票，支持分批保存结果
        
        Args:
            stock_codes: 股票代码列表
            max_workers: 并发工作线程数
            save_batch_size: 每批保存的股票数量，None表示不分批保存
            output_file: 输出文件名，None表示不保存
        
        Returns:
            分析结果列表
        """
        from concurrent.futures import ThreadPoolExecutor
        from tqdm import tqdm
        
        results = []
        temp_results = []
        
        # 1. 批量获取股票基本信息
        print(f"批量获取 {len(stock_codes)} 只股票的基本信息...")
        stock_infos = self.db.get_batch_stock_info(stock_codes)
        
        # 2. 准备完整代码列表，过滤掉 full_code 为 None 的情况
        full_codes = [info['full_code'] for code, info in stock_infos.items() if info and info.get('full_code')]
        
        # 3. 批量获取实时数据
        print(f"批量获取 {len(full_codes)} 只股票的实时数据...")
        real_time_data_dict = self.stock_fetcher.get_multiple_stocks_data(full_codes)
        
        # 4. 批量获取历史数据
        print(f"批量获取 {len(full_codes)} 只股票的历史数据...")
        history_data_dict = self.db.get_batch_stock_history(full_codes, days=30)
        
        # 5. 分析股票
        def analyze_stock(code):
            try:
                stock_info = stock_infos.get(code)
                if not stock_info:
                    return {
                        'code': code,
                        'name': '未知',
                        'error': '未找到股票基本信息'
                    }
                
                full_code = stock_info.get('full_code')
                real_time_data = real_time_data_dict.get(full_code)
                history_data = history_data_dict.get(full_code, [])
                
                if not real_time_data:
                    return {
                        'code': code,
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
                
                return {
                    'code': code,
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
            except Exception as e:
                print(f"分析股票 {code} 时出错: {e}")
                return {
                    'code': code,
                    'name': '未知',
                    'error': str(e)
                }
        
        print(f"开始分析 {len(stock_codes)} 只股票...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 使用tqdm包装executor.map的结果，显示分析进度
            with tqdm(total=len(stock_codes), desc="股票分析进度", unit="只", ncols=100) as pbar:
                # 使用列表推导式和回调函数更新进度
                for result in executor.map(analyze_stock, stock_codes):
                    results.append(result)
                    temp_results.append(result)
                    pbar.update(1)  # 更新进度条
                    
                    # 当临时结果达到批次大小时，保存结果
                    if save_batch_size and output_file and len(temp_results) >= save_batch_size:
                        self.save_results(temp_results, output_file, batch_size=save_batch_size, append=True)
                        temp_results.clear()
        
        # 保存剩余的结果
        if temp_results and save_batch_size and output_file:
            self.save_results(temp_results, output_file, batch_size=save_batch_size, append=True)
            temp_results.clear()
        
        # 如果使用了分批保存，需要在文件末尾添加]
        if save_batch_size and output_file:
            import os
            if os.path.exists(output_file):
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write('\n]')
                print(f"结果已全部保存到: {output_file}")

        return results

    def get_all_stocks_analysis(self, sample_size: int = None, save_batch_size: int = None, output_file: str = None) -> List[Dict[str, Any]]:
        """分析所有股票，支持分批保存结果
        
        Args:
            sample_size: 随机分析样本数量
            save_batch_size: 每批保存的股票数量，None表示不分批保存
            output_file: 输出文件名，None表示不保存
        
        Returns:
            分析结果列表
        """
        all_codes = self.db.get_all_stock_codes()

        if sample_size and sample_size < len(all_codes):
            import random
            all_codes = random.sample(all_codes, sample_size)

        print(f"开始分析 {len(all_codes)} 只股票...")
        return self.analyze_multiple_stocks(all_codes, save_batch_size=save_batch_size, output_file=output_file)

    def save_results(self, results: List[Dict[str, Any]], filename: str, batch_size: int = None, append: bool = False):
        """保存分析结果，支持分批写入
        
        Args:
            results: 分析结果列表
            filename: 输出文件名
            batch_size: 每批写入的股票数量，None表示一次写入所有结果
            append: 是否追加到现有文件
        """
        if not results:
            return
        
        # 如果不使用分批写入，直接保存所有结果
        if batch_size is None:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {filename}")
            return
        
        # 使用分批写入
        import os
        file_exists = os.path.exists(filename)
        
        # 首次写入或覆盖写入时，创建新文件并写入[
        if not file_exists or not append:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('[\n')
            append = True
        else:
            # 如果是追加写入，检查文件是否为空
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            # 如果文件内容为空，写入[
            if not content:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('[\n')
            # 如果文件内容不为空且不是以[结尾，说明之前有写入，需要添加逗号
            elif not content.endswith('['):
                with open(filename, 'a', encoding='utf-8') as f:
                    f.write(',\n')
        
        # 分批写入结果
        for i, result in enumerate(results):
            with open(filename, 'a', encoding='utf-8') as f:
                # 写入结果，最后一个结果不需要逗号
                if i == len(results) - 1:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                    f.write(',\n')
        
        print(f"已保存 {len(results)} 条结果到: {filename}")

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
    parser.add_argument('--output', '-o', type=str, default=f'stock_analysis_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                        help='输出结果文件名')
    parser.add_argument('--simple', action='store_true', help='使用简单分析模式')
    parser.add_argument('--save-batch-size', type=int, default=None, help='分批保存的批次大小，None表示一次写入所有结果')

    args = parser.parse_args()

    system = StockAnalysisSystem(use_multi_role=not args.simple)

    try:
        if args.stock:
            results = [system.analyze_single_stock(args.stock)]
            system.print_results(results)
            system.save_results(results, args.output)
        elif args.stocks:
            if args.save_batch_size:
                # 使用分批保存
                results = system.analyze_multiple_stocks(args.stocks, save_batch_size=args.save_batch_size, output_file=args.output)
                system.print_results(results)
            else:
                # 不使用分批保存
                results = system.analyze_multiple_stocks(args.stocks)
                system.print_results(results)
                system.save_results(results, args.output)
        elif args.all:
            if args.save_batch_size:
                # 使用分批保存
                results = system.get_all_stocks_analysis(save_batch_size=args.save_batch_size, output_file=args.output)
                system.print_results(results)
            else:
                # 不使用分批保存
                results = system.get_all_stocks_analysis()
                system.print_results(results)
                system.save_results(results, args.output)
        else:
            if args.save_batch_size:
                # 使用分批保存
                results = system.get_all_stocks_analysis(sample_size=args.sample, save_batch_size=args.save_batch_size, output_file=args.output)
                system.print_results(results)
            else:
                # 不使用分批保存
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