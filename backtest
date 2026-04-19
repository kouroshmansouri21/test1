import time
import pandas as pd
import bot_template

url = "https://raw.githubusercontent.com/kouroshmansouri21/test1/main/train_data.csv"


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
    my_bot = bot_template.Bot()


    print("Starting backtest (this might take a few seconds)...")
    result = run_local_engine(my_bot, market_data)


    print("\n" + "="*30)
    print("BACKTEST RESULTS")
    print("="*30)
    for key, value in result.items():
        print(f"{key}: {value}")
    print("="*30)

