import importlib
import os
import pandas as pd
from engine import run_local_engine

BOTS = [
    ("baseline", "template bot", "bot_template"),
    ("v1", "momentum", "bot_momentum"),
    ("v2", "mean reversion", "bot_meanrev"),
    ("v3", "ema", "bot_ema"),
]


def make_note(version, idea, result):
    executed = result["Executed"]
    final_value = result["Final_Value"]
    sharpe = result.get("Sharpe_Ratio", 0)
    max_drawdown = result.get("Max_Drawdown", 0)

    notes = []

    if version == "baseline":
        notes.append("Baseline template bot")

    if executed > 100000:
        notes.append("Extremely high turnover")
    elif executed > 1000:
        notes.append("Very active trading")
    elif executed > 100:
        notes.append("Moderate trading")
    else:
        notes.append("Selective trading")

    if final_value > 100000:
        notes.append("Profitable")
    elif final_value < 100000:
        notes.append("Loss-making")
    else:
        notes.append("Flat result")

    if sharpe > 1:
        notes.append("Good risk-adjusted returns")
    elif sharpe < 0:
        notes.append("Negative risk-adjusted returns")

    if max_drawdown > 0.2:
        notes.append("Large drawdown")

    return "; ".join(notes)


def load_market_data(path="train_data.csv"):
    df = pd.read_csv(path, sep=";")
    return df.to_dict("records")


def run_one_bot(module_name, market_data):
    module = importlib.import_module(module_name)
    bot = module.Bot()
    return run_local_engine(bot, market_data)


def main():
    if not os.path.exists("train_data.csv"):
        raise FileNotFoundError("train_data.csv not found.")

    market_data = load_market_data("train_data.csv")
    rows = []

    for version, idea, module_name in BOTS:
        try:
            result = run_one_bot(module_name, market_data)

            rows.append({
                "Version": version,
                "Idea": idea,
                "Final Value": result["Final_Value"],
                "Total Return %": result.get("Total_Return_Pct", None),
                "Sharpe Ratio": result.get("Sharpe_Ratio", None),
                "Max Drawdown": result.get("Max_Drawdown", None),
                "Executed": result["Executed"],
                "Rejected": result["Rejected"],
                "Timeouts": result["Timeouts"],
                "Status": result["Status"],
                "Notes": make_note(version, idea, result),
            })

            print(f"{version} done: {result}")

        except Exception as e:
            rows.append({
                "Version": version,
                "Idea": idea,
                "Final Value": "ERROR",
                "Total Return %": "ERROR",
                "Sharpe Ratio": "ERROR",
                "Max Drawdown": "ERROR",
                "Executed": "ERROR",
                "Rejected": "ERROR",
                "Timeouts": "ERROR",
                "Status": "ERROR",
                "Notes": str(e),
            })
            print(f"{version} failed: {e}")

    df = pd.DataFrame(rows)
    df.to_csv("backtest_results.csv", index=False)

    print("\nShared table:")
    print(df.to_string(index=False))
    print("\nSaved as backtest_results.csv")


if __name__ == "__main__":
    main()
