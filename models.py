from sqlalchemy import Column, String, Float, BigInteger, SmallInteger, Date, DateTime, Boolean
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class StockDaily(Base):
    __tablename__ = "stock_daily"

    date = Column(Date, primary_key=True, nullable=False)
    code = Column(String(20), primary_key=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    preclose = Column(Float)
    volume = Column(BigInteger)
    amount = Column(Float)
    adjustflag = Column(SmallInteger)
    turn = Column(Float)
    tradestatus = Column(SmallInteger)
    pctChg = Column(Float)
    peTTM = Column(Float)
    pbMRQ = Column(Float)
    psTTM = Column(Float)
    pcfNcfTTM = Column(Float)
    isST = Column(Boolean)
    update_time = Column(DateTime)


class StockInfo(Base):
    __tablename__ = "stock_info"

    code = Column(String(50), primary_key=True, nullable=False)
    name = Column(String(300), nullable=False)
    total_equity = Column(Float)
    liquidity = Column(Float)
    total_value = Column(Float)
    liquidity_value = Column(Float)
    sector = Column(String(300))
    ipo_date = Column(String(20), nullable=False)
    update_time = Column(DateTime)
    full_code = Column(String(20))
    exchange_code = Column(String(20))

