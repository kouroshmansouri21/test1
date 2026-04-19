import time
import pandas as pd

url = "https://raw.githubusercontent.com/kouroshmansouri21/test1/main/train_data.csv"

# --- Start of Bot class from 9FC_BCLYy1yd, adapted for Colab ---
from pathlib import Path

class Bot:
    def __init__(self):
        self.ai_model = "EMA_TrailingStop_Reentry"

        # EMA periods (optimized via grid search on train_data)
        self.FAST_PERIOD = 10
        self.SLOW_PERIOD = 100
        self.af = 2 / (self.FAST_PERIOD + 1)
        self.as_ = 2 / (self.SLOW_PERIOD + 1)

        # Trailing stop: sell if portfolio drops >55% from its all-time peak
        self.TRAILING_STOP = 0.55

        # Don't allow an exit before this many ticks (avoids immediate whipsaw on open)
        self.MIN_HOLD_TICKS = 2000

        # --- Internal state ---
        self.ema_fast = None
        self.ema_slow = None
        self.tick = 0
        self.peak_portfolio = 0.0

        # Entry flags
        self.initial_buy_done = False  # have we placed our first buy?
        self.in_cash = False  # are we currently flat (waiting to re-enter)?
        self.was_bearish = False  # did EMA cross bearish while in cash?

    # ------------------------------------------------------------------
    def get_action(self, tick, cash, inventory):
        price = tick["close"]
        self.tick += 1

        # ── 1. Initialise EMAs on very first tick ──────────────────────
        if self.ema_fast is None:
            self.ema_fast = price
            self.ema_slow = price
            return {"action": "HOLD", "quantity": 0}

        # ── 2. Update EMAs incrementally (O(1), always within time limit) ──
        self.ema_fast = self.af * price + (1 - self.af) * self.ema_fast
        self.ema_slow = self.as_ * price + (1 - self.as_) * self.ema_slow

        portfolio = cash + inventory * price

        # Track all-time peak portfolio value
        if portfolio > self.peak_portfolio:
            self.peak_portfolio = portfolio

        # ── 3. Initial full-size buy at tick 2 ────────────────────────
        if not self.initial_buy_done and inventory == 0:
            qty = max(1, int(cash * 0.99 / (price * 1.001)))
            if cash >= qty * price * 1.001:
                self.initial_buy_done = True
                self.peak_portfolio = portfolio
                return {"action": "BUY", "quantity": qty}

        # ── 4. Trailing stop: protect against catastrophic drawdown ───
        if (
            inventory > 0
            and self.peak_portfolio > 0
            and self.tick > self.MIN_HOLD_TICKS
        ):
            drawdown = (self.peak_portfolio - portfolio) / self.peak_portfolio
            if drawdown > self.TRAILING_STOP:
                # Exit entire position; reset peak; wait for bearish → bullish cycle
                self.in_cash = True
                self.was_bearish = False
                self.peak_portfolio = portfolio
                return {"action": "SELL", "quantity": inventory}

        # ── 5. Re-entry logic (only active while flat after a stop-out) ─
        if self.in_cash and inventory == 0:
            # Step A: wait until EMA crosses bearish (confirms the downtrend)
            if self.ema_fast < self.ema_slow:
                self.was_bearish = True

            # Step B: re-enter only once EMA turns bullish AFTER the bearish dip
            if self.was_bearish and self.ema_fast > self.ema_slow:
                qty = max(1, int(cash * 0.99 / (price * 1.001)))
                if cash >= qty * price * 1.001:
                    self.in_cash = False
                    self.was_bearish = False
                    self.peak_portfolio = portfolio
                    return {"action": "BUY", "quantity": qty}

        return {"action": "HOLD", "quantity": 0}
# --- End of Bot class ---


def run_local_engine(team_bot, test_data):
    cash = 100000.0
    inventory = 0
    fee = 0.001
    executed = 0
    rejected = 0
    timeouts = 0


    for tick in test_data:
        price = tick['close']
        current_buying_power = cash + (inventory * price)


        if current_buying_power <= 0:
            print("MARGIN CALL: You went bankrupt!")
            return {
                "Final_Value": 0,
                "Executed": executed,
                "Rejected": rejected,
                "Timeouts": timeouts,
                "Status": "BANKRUPT"
            }


        try:
            start = time.time()
            entscheidung = team_bot.get_action(tick, cash, inventory)
            duration = time.time() - start
        except Exception as e:
            timeouts += 1
            continue


        if duration > 0.03:
            timeouts += 1
            continue


        act = entscheidung.get("action")
        qty = entscheidung.get("quantity", 0)
        cost = qty * price


        if act == "BUY" and qty > 0:
            new_inv = inventory + qty
            if cash >= (cost * (1 + fee)) and abs(new_inv * price) <= current_buying_power:
                cash -= cost * (1 + fee)
                inventory = new_inv
                executed += 1
            else:
                rejected += 1


        elif act == "SELL" and qty > 0:
            new_inv = inventory - qty
            if abs(new_inv * price) <= current_buying_power:
                cash += cost * (1 - fee)
                inventory = new_inv
                executed += 1
            else:
                rejected += 1


    final_value = cash + (inventory * test_data[-1]['close'])

    return {
        "Final_Value": round(final_value, 2),
        "Executed": executed,
        "Rejected": rejected,
        "Timeouts": timeouts,
        "Status": "COMPLETED"
    }


if __name__ == "__main__":
    print("Loading training data...")
    df = pd.read_csv(url, sep=";")
    market_data = df.to_dict('records')


    print("Initializing your Bot...")
    my_bot = Bot()


    print("Starting backtest (this might take a few seconds)...")
    result = run_local_engine(my_bot, market_data)


    print("\n" + "="*30)
    print("BACKTEST RESULTS")
    print("="*30)
    for key, value in result.items():
        print(f"{key}: {value}")
    print("="*30)
