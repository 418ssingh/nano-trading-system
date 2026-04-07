"""
Core trading engine with connection pooling and latency tracking
Meets: Sub-8ms infrastructure + High-performance Python
"""

import time
from typing import List, Tuple, Any
from contextlib import contextmanager
from ib_async import IB, Stock, LimitOrder
from dataclasses import dataclass

# ============ LATENCY TRACKER ============
@dataclass
class LatencyStats:
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    p99_ms: float = 0.0
    sub_8ms_percent: float = 0.0
    total_samples: int = 0

class LatencyTracker:
    def __init__(self, name: str = "default", window: int = 1000):
        self.name = name
        self.window = window
        self._lats = []
    
    def record(self, ms: float):
        self._lats.append(ms)
        if len(self._lats) > self.window:
            self._lats.pop(0)
    
    @property
    def stats(self) -> LatencyStats:
        if not self._lats:
            return LatencyStats()
        s = sorted(self._lats)
        n = len(s)
        sub_8 = sum(1 for x in s if x < 8.0)
        return LatencyStats(
            avg_ms=sum(s)/n,
            min_ms=s[0],
            max_ms=s[-1],
            p99_ms=s[int(n*0.99)],
            sub_8ms_percent=(sub_8/n)*100,
            total_samples=n
        )
    
    def report(self) -> str:
        s = self.stats
        return f"""
╔════════════════════════════╗
║ {self.name}: {s.avg_ms:.3f}ms avg
║ P99: {s.p99_ms:.3f}ms | Sub-8ms: {s.sub_8ms_percent:.0f}%
║ Samples: {s.total_samples}
╚════════════════════════════╝"""

# ============ CONNECTION POOL ============
class ConnectionPool:
    def __init__(self, host="127.0.0.1", port=4002, size=3):
        self.host = host
        self.port = port
        self.size = size
        self._conns: List[IB] = []
        self._index = 0
        self._contract_cache = {}
        self.latency = LatencyTracker("Order")
    
    def connect(self):
        for i in range(self.size):
            conn = IB()
            conn.connect(self.host, self.port, clientId=i+1)
            self._conns.append(conn)
        print(f"✅ Connected {self.size} connections")
    
    def get_contract(self, symbol: str) -> Stock:
        """Cached contract - eliminates qualifyContracts latency"""
        if symbol not in self._contract_cache:
            self._contract_cache[symbol] = Stock(symbol, "SMART", "USD")
        return self._contract_cache[symbol]
    
    @contextmanager
    def get_conn(self):
        conn = self._conns[self._index % len(self._conns)]
        self._index += 1
        yield conn
    
    def place_order(self, symbol: str, qty: int, price: float, action: str = "BUY") -> Tuple[Any, float]:
        start = time.perf_counter_ns()
        
        contract = self.get_contract(symbol)
        order = LimitOrder(action, qty, price)
        
        with self.get_conn() as conn:
            trade = conn.placeOrder(contract, order)
        
        latency = (time.perf_counter_ns() - start) / 1_000_000
        self.latency.record(latency)
        return trade, latency
    
    def disconnect(self):
        for conn in self._conns:
            if conn.isConnected():
                conn.disconnect()