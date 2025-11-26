from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from functools import lru_cache

from engine import engine,SessionLocal
import pandas as pd

class Database:
    """数据库操作类"""
    def __init__(self):
        self.engine = engine
        self.sessionLocal = SessionLocal

    @lru_cache(maxsize=1000)
    def _get_stock_history_cache(self, full_code: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取股票历史数据（带缓存）"""
        sql_str =  f"""
        SELECT date, code, open, high, low, close, preclose, volume, amount,
                   adjustflag, turn, tradestatus, pctChg, peTTM, pbMRQ, psTTM,
                   pcfNcfTTM, isST, update_time
            FROM stock_daily
            WHERE code = '{full_code}' 
            AND date >= '{start_date}'
            AND date <= '{end_date}'
            ORDER BY date DESC
        """
        return pd.read_sql(sql_str, self.engine).to_dict(orient="records")
    
    def get_stock_history(self, stock_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取股票历史数据"""
        stock_info = self.get_stock_info(stock_code)
        if not stock_info:
            return []
        full_code = stock_info.get('full_code')
        end = datetime.now()
        start = end - timedelta(days=days)
        start_date = start.strftime('%Y-%m-%d')
        end_date = end.strftime('%Y-%m-%d')
        return self._get_stock_history_cache(full_code, start_date, end_date)

    @lru_cache(maxsize=1000)
    def _get_stock_info_cache(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息（带缓存）"""
        sql_str = f"""
        SELECT code, name, total_equity, liquidity, total_value, liquidity_value,
                   sector, ipo_date, update_time, full_code, exchange_code
            FROM stock_info
            WHERE code = '{stock_code}'
            ORDER BY code
        """
        result = pd.read_sql(sql_str, self.engine).to_dict(orient="records")
        return result[0] if result else None
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        return self._get_stock_info_cache(stock_code)

    def get_batch_stock_info(self, stock_codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量获取股票基本信息"""
        if not stock_codes:
            return {}
        
        # 使用IN子句批量查询
        codes_str = "'" + "','".join(stock_codes) + "'"
        sql_str = f"""
        SELECT code, name, total_equity, liquidity, total_value, liquidity_value,
                   sector, ipo_date, update_time, full_code, exchange_code
            FROM stock_info
            WHERE code IN ({codes_str})
            ORDER BY code
        """
        
        results = pd.read_sql(sql_str, self.engine).to_dict(orient="records")
        return {result['code']: result for result in results}

    def get_batch_stock_history(self, full_codes: List[str], days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """批量获取股票历史数据"""
        if not full_codes:
            return {}
        
        # 使用IN子句批量查询
        codes_str = "'" + "','".join(full_codes) + "'"
        end = datetime.now()
        start = end - timedelta(days=days)
        
        sql_str =  f"""
        SELECT date, code, open, high, low, close, preclose, volume, amount,
                   adjustflag, turn, tradestatus, pctChg, peTTM, pbMRQ, psTTM,
                   pcfNcfTTM, isST, update_time
            FROM stock_daily
            WHERE code IN ({codes_str})
            AND date >= '{start.strftime('%Y-%m-%d')}'
            AND date <= '{end.strftime('%Y-%m-%d')}'
            ORDER BY code, date DESC
        """
        
        results = pd.read_sql(sql_str, self.engine).to_dict(orient="records")
        
        # 按股票代码分组
        grouped_results = {}
        for result in results:
            code = result['code']
            if code not in grouped_results:
                grouped_results[code] = []
            grouped_results[code].append(result)
        
        return grouped_results

    def get_all_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        sql_str = """
        SELECT code
            FROM stock_info
        """
        return pd.read_sql(sql_str, self.engine)["code"].tolist()
