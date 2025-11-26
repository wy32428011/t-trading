from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from engine import engine,SessionLocal
import pandas as pd

class Database:
    """数据库操作类"""
    def __init__(self):
        self.engine = engine
        self.sessionLocal = SessionLocal

    def get_stock_history(self, stock_code: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取股票历史数据"""
        stock_info = self.get_stock_info(stock_code)
        if not stock_info:
            return []
        full_code = stock_info.get('full_code')
        end = datetime.now()
        start = end - timedelta(days=days)
        sql_str =  f"""
        SELECT date, code, open, high, low, close, preclose, volume, amount,
                   adjustflag, turn, tradestatus, pctChg, peTTM, pbMRQ, psTTM,
                   pcfNcfTTM, isST, update_time
            FROM stock_daily
            WHERE code = '{full_code}' 
            AND date >= '{start.strftime('%Y-%m-%d')}'
            AND date <= '{end.strftime('%Y-%m-%d')}'
            ORDER BY date DESC
        """
        return pd.read_sql(sql_str, self.engine).to_dict(orient="records")

    def get_stock_info(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        sql_str = f"""
        SELECT code, name, total_equity, liquidity, total_value, liquidity_value,
                   sector, ipo_date, update_time, full_code, exchange_code
            FROM stock_info
            WHERE code = '{stock_code}'
        """
        return pd.read_sql(sql_str, self.engine).to_dict(orient="records")[0] if pd.read_sql(sql_str, self.engine).shape[0] > 0 else None

    def get_all_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        sql_str = """
        SELECT code
            FROM stock_info
        """
        return pd.read_sql(sql_str, self.engine)["code"].tolist()
