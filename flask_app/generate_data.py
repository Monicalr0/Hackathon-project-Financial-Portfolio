import os
import random
from datetime import datetime, time, timedelta

from db_api import DatabaseEditor
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")


def random_stock_market_datetime(start_date=datetime(2023, 1, 1), end_date=None):
    if end_date is None:
        end_date = datetime.today() - timedelta(days=1)  # yesterday

    # define stock market opening and closing times
    market_open_time = time(9, 30)
    market_close_time = time(16, 0)

    # calculate the time difference in seconds between the two dates
    time_diff = (end_date - start_date).total_seconds()

    # generate a random number of seconds within the time range
    random_seconds = random.randint(0, int(time_diff))

    # create the random datetime by adding the random number of seconds to the start date
    random_dt = start_date + timedelta(seconds=random_seconds)

    # adjust the time to match market opening time if before, and to the market closing time if after
    if random_dt.time() < market_open_time:
        random_dt = random_dt.replace(
            hour=market_open_time.hour, minute=market_open_time.minute
        )
    elif random_dt.time() > market_close_time:
        random_dt = random_dt.replace(
            hour=market_close_time.hour, minute=market_close_time.minute
        )

    return random_dt


# !! GENERATES A VALID PORTFOLIO HISTORY
if __name__ == "__main__":
    db_editor = DatabaseEditor(password=DB_PASSWORD, database="team11")

    # random datetimes to backfill the database
    datetimes = [random_stock_market_datetime() for _ in range(100)]
    # sort the dates
    datetimes.sort()

    tickers = [
        "AAPL",  # Apple Inc. - Stock
        "GOOGL",  # Alphabet Inc. - Stock
        "TSLA",  # Tesla, Inc. - Stock
        "MSFT",  # Microsoft Corporation - Stock
        "AMZN",  # Amazon.com, Inc. - Stock
        "AAP",  # Advance Auto Parts, Inc. - Stock
        "VWO",  # Vanguard FTSE Emerging Markets ETF - ETF
        "JNJ",  # Johnson & Johnson - Stock
        "V",  # Visa Inc. - Stock
        "FB",  # Meta Platforms, Inc. - Stock
        "NVDA",  # NVIDIA Corporation - Stock
        "GLD",  # SPDR Gold Trust - Gold ETF
        "XOM",  # Exxon Mobil Corporation - Stock
        "XLF",  # Financial Select Sector SPDR Fund - Financial ETF
    ]

    for dt in datetimes:
        ticker = random.choice(tickers)  # random ticker to buy/sell
        num_shares = random.randint(1, 13)  # random number of shares to buy/sell
        # 50% chance to buy, 50% chance to sell
        if random.random() < 0.5:
            db_editor.sell_ticker(ticker, num_shares, dt)
        else:
            db_editor.buy_ticker(ticker, num_shares, dt)
