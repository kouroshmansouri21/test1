class Bot:
    def __init__(self):
        self.ai_model = "Weekly_Trend_Follower_Optimized"
        # Parameters updated to 'Absolute Best' configuration from grid search
        self.FAST_PERIOD = 100
        self.SLOW_PERIOD = 2000
        self.af = 2 / (self.FAST_PERIOD + 1)
        self.as_ = 2 / (self.SLOW_PERIOD + 1)
        self.TRAILING_STOP = 0.15

        self.ema_fast = None
        self.ema_slow = None
        self.peak_portfolio = 0.0
        self.last_trade_tick = -20000
        self.current_tick = 0
        # Optimized cooling period
        self.MIN_WAIT = 5000

    def get_action(self, tick, cash, inventory):
        self.current_tick += 1
        price = tick["close"]

        if self.ema_fast is None:
            self.ema_fast = price
            self.ema_slow = price
            return {"action": "HOLD", "quantity": 0}

        prev_fast, prev_slow = self.ema_fast, self.ema_slow
        self.ema_fast = self.af * price + (1 - self.af) * self.ema_fast
        self.ema_slow = self.as_ * price + (1 - self.as_) * self.ema_slow

        portfolio = cash + inventory * price
        if portfolio > self.peak_portfolio: self.peak_portfolio = portfolio

        # SELL logic
        if inventory > 0:
            drawdown = (self.peak_portfolio - portfolio) / self.peak_portfolio if self.peak_portfolio > 0 else 0
            bearish_cross = (prev_fast >= prev_slow) and (self.ema_fast < self.ema_slow)
            if bearish_cross or drawdown > self.TRAILING_STOP:
                self.peak_portfolio = 0
                self.last_trade_tick = self.current_tick
                return {"action": "SELL", "quantity": inventory}

        # BUY logic (with cooling period)
        if inventory == 0 and (self.current_tick - self.last_trade_tick) > self.MIN_WAIT:
            bullish_cross = (prev_fast <= prev_slow) and (self.ema_fast > self.ema_slow)
            if bullish_cross:
                qty = int(cash * 0.95 / (price * 1.001))
                if qty > 0:
                    self.last_trade_tick = self.current_tick
                    return {"action": "BUY", "quantity": qty}

        return {"action": "HOLD", "quantity": 0}
