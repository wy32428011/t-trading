import requests
from typing import Dict, Any, Optional
import time


class RealTimeStockDataFetcher:
    def __init__(self):
        self.base_url = "https://qt.gtimg.cn/q={}"

    def get_real_time_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票实时数据"""
        url = self.base_url.format(stock_code)

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.text.strip()
            if not data:
                return None

            data_parts = data.split('=')
            if len(data_parts) < 2:
                return None

            values = data_parts[1].strip('"').split('~')

            if len(values) < 49:
                return None

            return {
                'unknown': values[0],
                'name': values[1],
                'code': values[2],
                'current_price': float(values[3]) if values[3] else 0.0,
                'prev_close': float(values[4]) if values[4] else 0.0,
                'open': float(values[5]) if values[5] else 0.0,
                'volume': int(values[6]) if values[6] else 0,
                'outer_disc': int(values[7]) if values[7] else 0,
                'inner_disc': int(values[8]) if values[8] else 0,
                'bid_price_1': float(values[9]) if values[9] else 0.0,
                'bid_volume_1': int(values[10]) if values[10] else 0,
                'bid_price_2': float(values[11]) if values[11] else 0.0,
                'bid_volume_2': int(values[12]) if values[12] else 0,
                'bid_price_3': float(values[13]) if values[13] else 0.0,
                'bid_volume_3': int(values[14]) if values[14] else 0,
                'bid_price_4': float(values[15]) if values[15] else 0.0,
                'bid_volume_4': int(values[16]) if values[16] else 0,
                'bid_price_5': float(values[17]) if values[17] else 0.0,
                'bid_volume_5': int(values[18]) if values[18] else 0,
                'ask_price_1': float(values[19]) if values[19] else 0.0,
                'ask_volume_1': int(values[20]) if values[20] else 0,
                'ask_price_2': float(values[21]) if values[21] else 0.0,
                'ask_volume_2': int(values[22]) if values[22] else 0,
                'ask_price_3': float(values[23]) if values[23] else 0.0,
                'ask_volume_3': int(values[24]) if values[24] else 0,
                'ask_price_4': float(values[25]) if values[25] else 0.0,
                'ask_volume_4': int(values[26]) if values[26] else 0,
                'ask_price_5': float(values[27]) if values[27] else 0.0,
                'ask_volume_5': int(values[28]) if values[28] else 0,
                'recent_trades': values[29],
                'time': values[30],
                'change': float(values[31]) if values[31] else 0.0,
                'change_percent': float(values[32]) if values[32] else 0.0,
                'high': float(values[33]) if values[33] else 0.0,
                'low': float(values[34]) if values[34] else 0.0,
                'price_volume_amount': values[35],
                'volume_hand': int(values[36]) if values[36] else 0,
                'amount_10k': float(values[37]) if values[37] else 0.0,
                'turnover_rate': float(values[38]) if values[38] else 0.0,
                'pe_ratio': float(values[39]) if values[39] else 0.0,
                'unknown_40': values[40],
                'high_2': float(values[41]) if values[41] else 0.0,
                'low_2': float(values[42]) if values[42] else 0.0,
                'amplitude': float(values[43]) if values[43] else 0.0,
                'circulating_market_value': float(values[44]) if values[44] else 0.0,
                'total_market_value': float(values[45]) if values[45] else 0.0,
                'pb_ratio': float(values[46]) if values[46] else 0.0,
                'limit_up': float(values[47]) if values[47] else 0.0,
                'limit_down': float(values[48]) if values[48] else 0.0
            }

        except requests.RequestException as e:
            print(f"请求股票实时数据错误: {e}")
            return None
        except (ValueError, IndexError) as e:
            print(f"解析股票数据错误: {e}")
            return None

    def get_multiple_stocks_data(self, stock_codes: list, delay: float = 0.1) -> Dict[str, Dict[str, Any]]:
        """批量获取多个股票实时数据"""
        results = {}

        for code in stock_codes:
            data = self.get_real_time_data(code)
            if data:
                results[code] = data
            time.sleep(delay)

        return results