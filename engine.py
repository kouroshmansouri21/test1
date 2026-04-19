import time
import math
import pandas as pd


def calculate_metrics(equity_curve):
    if len(equity_curve) < 2:
        return {
            "Sharpe_Ratio": 0.0,
            "Max_Drawdown": 0.0,
            "Total_Return_Pct": 0.0,
        }

    returns = []
    for i in range(1, len(equity_curve)):
        prev_value = equity_curve[i - 1]
        curr_value = equity_curve[i]

        if prev_value != 0:
            returns.append((curr_value - prev_value) / prev_value)

    if len(returns) == 0:
        sharpe_ratio = 0.0
    else:
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        std_return = math.sqrt(variance)

        if std_return == 0:
            sharpe_ratio = 0.0
        else:
            sharpe_ratio = (mean_return / std_return) * math.sqrt(len(returns))

    peak = equity_curve[0]
    max_drawdown = 0.0

    for value in equity_curve:
        if value > peak:
            peak = value

        drawdown = (peak - value) / peak if peak != 0 else 0.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    total_return_pct = ((equity_curve[-1] - equity_curve[0]) / equity_curve[0]) * 100

    return {
        "Sharpe_Ratio": round(sharpe_ratio, 4),
        "Max_Drawdown": round(max_drawdown, 4),
        "Total_Return_Pct": round(total_return_pct, 2),
    }


def run_local_engine(team_bot, test_data):
    cash = 100000.0
    inventory = 0
    fee = 0.001
    executed = 0
    rejected = 0
    timeouts = 0
    equity_curve = []

    for tick in test_data:
        price = tick["close"]
        current_buying_power = cash + (inventory * price)

        equity_curve.append(current_buying_power)

        if current_buying_power <= 0:
            print("MARGIN CALL: You went bankrupt!")
            metrics = calculate_metrics(equity_curve)
            return {
                "Final_Value": 0,
                "Executed": executed,
                "Rejected": rejected,
                "Timeouts": timeouts,
                "Status": "BANKRUPT",
                "Sharpe_Ratio": metrics["Sharpe_Ratio"],
                "Max_Drawdown": metrics["Max_Drawdown"],
                "Total_Return_Pct": metrics["Total_Return_Pct"],
            }

        try:
            start = time.time()
            entscheidung = team_bot.get_action(tick, cash, inventory)
            duration = time.time() - start
        except Exception:
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

    final_value = cash + (inventory * test_data[-1]["close"])
    equity_curve.append(final_value)

    metrics = calculate_metrics(equity_curve)

    return {
        "Final_Value": round(final_value, 2),
        "Executed": executed,
        "Rejected": rejected,
        "Timeouts": timeouts,
        "Status": "COMPLETED",
        "Sharpe_Ratio": metrics["Sharpe_Ratio"],
        "Max_Drawdown": metrics["Max_Drawdown"],
        "Total_Return_Pct": metrics["Total_Return_Pct"],
    }


if __name__ == "__main__":
    print("Loading training data...")
    # Load data directly from the URL
    try:
        df = pd.read_csv(url, sep=";")
        market_data = df.to_dict("records")
    except Exception as e:
        print(f"ERROR: Could not load data from URL: {e}")
        # If data cannot be loaded, prevent further execution to avoid NameError
        market_data = [] # Assign an empty list to prevent NameError, though backtest will fail gracefully
        exit() # This exit() is more likely to work here in Colab.

    print("Initializing your Bot...")
    my_bot = Bot()

    print("Starting backtest (this might take a few seconds)...")
    result = run_local_engine(my_bot, market_data)

    print("\n" + "=" * 30)
    print("BACKTEST RESULTS")
    print("=" * 30)
    for key, value in result.items():
        print(f"{key}: {value}")
    print("=" * 30)
