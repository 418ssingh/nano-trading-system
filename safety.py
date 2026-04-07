"""
Retail safety mechanisms
Meets: Native strategy builders for retail (safety features)
"""

import time
from collections import defaultdict
from typing import Tuple

class RetailGuard:
    def __init__(self):
        self.order_count = defaultdict(int)
        self.last_time = {}
    
    def check_rate_limit(self, user_id: str, max_per_sec: int = 10) -> Tuple[bool, str]:
        """Prevent order spam - critical for retail"""
        now = time.time()
        
        if user_id in self.last_time:
            if now - self.last_time[user_id] < 1.0:
                self.order_count[user_id] += 1
                if self.order_count[user_id] > max_per_sec:
                    return False, f"Rate limit: {self.order_count[user_id]}/sec"
            else:
                self.order_count[user_id] = 1
        else:
            self.order_count[user_id] = 1
        
        self.last_time[user_id] = now
        return True, "OK"
    
    def check_order_size(self, qty: int, max_qty: int = 100) -> Tuple[bool, str]:
        """Prevent fat-finger errors"""
        if qty > max_qty:
            return False, f"Max size {max_qty}, got {qty}"
        if qty <= 0:
            return False, "Invalid quantity"
        return True, "OK"
    
    def get_stats(self):
        return {
            'active_users': len(self.order_count),
            'total_orders': sum(self.order_count.values())
        }