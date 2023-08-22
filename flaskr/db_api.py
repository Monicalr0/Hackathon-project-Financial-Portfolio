import json
import logging  # this should allow all messages to be displayed
import os
from datetime import datetime

import mysql.connector
import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

# todo remove this line for production code
logging.basicConfig(level=logging.DEBUG)


# class to access and edit the database
class DatabaseEditor:
    def __init__(self, password: str, database: str, host="localhost", user="root"):
        """
        __init__ Initializer for the DatabaseEditor class.

        Args:
            password (str): Database password.
            database (str): Database name.
            host (str, optional): Database host. Defaults to "localhost".
            user (str, optional): Database user. Defaults to "root".
        """
        self.db_name = database
        self.host = host
        self.user = user
        self.password = password
        self.db, self.cursor = self.connect()

    def connect(self):
        """
        connect Connects to the database.

        Returns:
            mysql.connector.connection.MySQLConnection: Database connection.
            mysql.connector.cursor.MySQLCursor: Database cursor.
        """
        try:
            db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name,
            )
            if db.is_connected():
                logging.info(f"Successfully connected to {self.db_name} database.")

            return db, db.cursor()
        except mysql.connector.errors.ProgrammingError:
            logging.error(
                f"Error connecting to the {self.db_name} database. Check your credentials."
            )

    def disconnect(self):
        """
        disconnect Closes the self.cursor and database connection.
        """
        try:
            self.cursor.close()
            self.db.close()
            logging.info(f"Database {self.db_name} editor closed.")
        except mysql.connector.errors.InterfaceError:
            logging.error(f"Error closing database {self.db_name} editor.")

    def get_tables(self):
        """
        get_tables Returns all tables in the database.

        Returns:
            list: List of tables in the database.
        """
        # get all tables in the database
        self.cursor.execute("SHOW TABLES;")
        tables = self.cursor.fetchall()
        # check if there are any tables in the database
        if len(tables) == 0:
            logging.warning(f"No tables in database {self.db_name}.")
            return None
        else:
            logging.debug(f"Tables in database {self.db_name}: {tables}")

        return tables

    def get_ticker(self, ticker_id):
        """
        get_ticker Get a ticker from the database (table: portfolio).

        Args:
            ticker_id (str): Symbol of the ticker to get.

        Returns:
            str: Ticker symbol.
        """
        try:
            self.cursor.execute(
                f"SELECT * FROM portfolio WHERE ticker_id = '{ticker_id}';"
            )
            ticker = self.cursor.fetchone()[0]

            logging.debug(f"Found ticker {ticker} in database {self.db_name}.")
            return json.dumps(ticker, indent=4, sort_keys=True, default=str)
        except mysql.connector.errors.ProgrammingError:
            logging.warning(f"No tickers in database {self.db_name}.")
            return None

    def get_tickers(self):
        """
        get_tickers Get all tickers from the user portfolio.

        Returns:
            list: List of tickers in the database.
        """
        # get all tickers from the database

        try:
            self.cursor.execute("SELECT ticker_id FROM portfolio;")
            tickers = self.cursor.fetchall()

            logging.debug(f"Tickers in database {self.db_name}: {tickers}")
            return [t[0] for t in tickers]
        except mysql.connector.errors.ProgrammingError:
            logging.warning(f"No tickers in database {self.db_name}.")

            return None

    def is_valid_ticker(self, ticker_id: str):
        """
        is_valid_ticker Check if a ticker is a valid Yahoo! Finance ticker.

        Args:
            ticker_id (str): Ticker to check.

        Returns:
            bool: True if the ticker is valid, False otherwise.
        """
        try:
            ticker = yf.Ticker(ticker_id)
            ticker.get_info()
            logging.debug(f"{ticker_id.upper()} is a valid Yahoo! Finance ticker.")
            return True
        except requests.exceptions.HTTPError:
            logging.warning(
                f"{ticker_id.upper()} is not a valid Yahoo! Finance ticker."
            )
            return False

    def get_market_value(self, ticker_id: str, timestamp: datetime = None):
        """
        get_market_value Get the market value of a ticker at a specified timestamp, default to now.

        Args:
            ticker_id (str): Ticker to get the market value of.
            timestamp (datetime, optional): Timestamp to get the market value at. Defaults to None.

        Returns:
            float: Market value of the ticker at the specified timestamp.
        """
        if self.is_valid_ticker(ticker_id):
            ticker = yf.Ticker(ticker_id)

            if timestamp is None:
                timestamp = datetime.now()
            historical_data = ticker.history(start=timestamp, end=timestamp)

            if not historical_data.empty:
                try:
                    market_value = historical_data["Close"][0]
                    return market_value
                except:
                    logging.warning(
                        f"Unable to get market value of {ticker_id.upper()} at {timestamp}."
                    )
                    return None
        return None

    # todo: update_total_return()
    def update_total_return(self, ticker_id: str):
        """
        update_total_return Method to update the total return of a ticker in the portfolio.

        Args:
            ticker_id (str): Ticker to update the total return of.
        """
        # calc the total return of a ticker from start to today
        # Total Return = (Ending Value - Beginning Value) / Beginning Value

        curr_price = self.get_market_value(ticker_id)
        self.cursor.execute(
            f"SELECT num_shares, price, transaction_type FROM transactions WHERE ticker_id = '{ticker_id}'"
        )
        data = self.cursor.fetchall()

        total_return = 0

        # loop through all transactions
        for row in data:
            if row[2] == "buy":  # skip sell transactions
                num_shares = int(row[0])  # number of shares per transaction
                price = float(row[1])  # buy in price at purchase time
                total_return += num_shares * ((curr_price - price) / price)

        self.cursor.execute(
            f"UPDATE portfolio SET total_return = {total_return} WHERE ticker_id = '{ticker_id}'"
        )
        self.db.commit()

    def buy_ticker(self, ticker_id: str, num_shares: int, timestamp: datetime = None):
        """
        buy_ticker Method to buy a ticker and add it to the user portfolio.

        Args:
            ticker_id (str): Ticker symbol to buy.
            num_shares (int): Number of shares to buy.
            timestamp (datetime, optional): Timestamp of the purchase.

        Returns:
            str: Success message if the purchase was successful, error message otherwise.
        """
        num_shares = int(num_shares)

        buy_in_price = self.get_market_value(ticker_id, timestamp)

        if buy_in_price is None:
            msg = f"Unable to determine the market value of {ticker_id.upper()} at {timestamp}."
            logging.warning(msg)
            return msg

        # check if the ticker is valid
        if not self.is_valid_ticker(ticker_id):
            msg = f"{ticker_id.upper()} is not a valid Yahoo! Finance ticker."
            logging.warning(msg)

            return msg  # fail

        elif ticker_id in self.get_tickers():
            logging.info(
                f"{ticker_id.upper()} already exists in the database, updating current portfolio info for purchase."
            )

            # get the current shares for the ticker in the portfolio
            self.cursor.execute(
                f"SELECT total_shares FROM portfolio WHERE ticker_id='{ticker_id}';"
            )
            shares = self.cursor.fetchone()[0]
            # convert from str to float
            shares = float(shares)
            shares += num_shares

            # update the shares in the portfolio
            self.cursor.execute(
                f"UPDATE portfolio SET total_shares={shares + num_shares} WHERE ticker_id='{ticker_id}';"
            )
            self.db.commit()
            logging.info(
                f"Added {num_shares} shares of {ticker_id.upper()} to the database."
            )

        else:
            logging.info(
                f"{ticker_id.upper()} does not exist in the database, adding to portfolio."
            )

            # add to tickers
            self.add_ticker(ticker_id)

            # insert the ticker into the portfolio
            asset_type = self.get_asset_type(ticker_id)
            self.cursor.execute(
                f"INSERT INTO portfolio (ticker_id, total_shares, total_return, asset_type) VALUES ('{ticker_id}', {num_shares}, 0, '{asset_type}');"
            )
            self.db.commit()
            logging.info(f"Added {ticker_id.upper()} to user portfolio.")

        # add purchase to transaction history
        if timestamp is not None:
            query = f"INSERT INTO transactions (ticker_id, num_shares, price, transaction_type, date) VALUES ('{ticker_id}', {num_shares}, {buy_in_price}, 'buy', '{timestamp}');"
            print("QUERY: ", query)
            self.cursor.execute(query)
        else:
            self.cursor.execute(
                f"INSERT INTO transactions (ticker_id, num_shares, price, transaction_type) VALUES ('{ticker_id}', {num_shares}, {buy_in_price}, 'buy');"
            )
            self.db.commit()
            logging.info(f"Added purchase {ticker_id.upper()} to transaction history.")

        return f"Success! Purchased {num_shares} shares of {ticker_id.upper()} for ${buy_in_price:.2f} each."

    def sell_ticker(self, ticker_id: str, num_shares: int, timestamp: datetime = None):
        """
        sell_ticker Method to sell a ticker from the user portfolio.

        Args:
            ticker_id (str): Ticker symbol to sell.
            num_shares (int): Number of shares to sell.

        Returns:
            str: Success message if the sale was successful, error message otherwise.
        """
        sale_price = self.get_market_value(ticker_id, timestamp)
        num_shares = int(num_shares)

        if sale_price is None:
            msg = f"Unable to determine the market value of {ticker_id.upper()} at {timestamp}."
            logging.warning(msg)
            return msg

        if not self.is_valid_ticker(ticker_id):
            msg = f"{ticker_id.upper()} is not a valid Yahoo! Finance ticker."
            logging.warning(msg)

            return msg
        elif ticker_id not in self.get_tickers():
            msg = f"{ticker_id.upper()} is not in the user portfolio, there are no shares to sell."
            logging.warning(msg)
            return msg
        else:
            logging.info(
                f"{ticker_id.upper()} exists in the database, updating current portfolio info for sale."
            )

            # get the current shares for the ticker in the portfolio
            self.cursor.execute(
                f"SELECT total_shares FROM portfolio WHERE ticker_id='{ticker_id}';"
            )
            shares = self.cursor.fetchone()[0]
            # convert shares from str to float
            shares = float(shares)

            # check if the user is trying to sell more shares than they own
            if num_shares > shares:
                logging.warning(
                    f"Cannot sell {num_shares} shares of {ticker_id.upper()}, only {shares} shares are owned. Selling all ({shares}) shares."
                )

            # number of shares to sell
            to_sell = min(num_shares, shares)

            if to_sell == shares:
                self.cursor.execute(
                    f"DELETE FROM portfolio WHERE ticker_id='{ticker_id}';"
                )
            else:
                # update the shares in the portfolio
                self.cursor.execute(
                    f"UPDATE portfolio SET total_shares=total_shares - {to_sell} WHERE ticker_id='{ticker_id}';"
                )

            self.db.commit()
            logging.info(
                f"Sold {to_sell} shares of {ticker_id.upper()} for {sale_price} each."
            )

            if timestamp is not None:
                self.cursor.execute(
                    f"INSERT INTO transactions (ticker_id, num_shares, price, transaction_type, date) VALUES ('{ticker_id}', {to_sell}, {-sale_price}, 'sell', '{timestamp}');"
                )
            else:
                # add sale to transaction history
                self.cursor.execute(
                    f"INSERT INTO transactions (ticker_id, num_shares, price, transaction_type) VALUES ('{ticker_id}', {to_sell}, {-sale_price}, 'sell');"
                )
                self.db.commit()

            return f"Success! Sold {to_sell} shares of {ticker_id.upper()} for ${sale_price:.2f} each."

    def update_ticker_data(self):
        """
        update_ticker_data Method to refresh the database with the latest ticker data.
        """

        # get all tickers from the database (ones in the portfolio)
        tickers = self.get_tickers()

        for ticker in tickers:
            data = yf.download(ticker, period="1d")

            open_price = data["Open"][0]
            close_price = data["Close"][0]
            high_price = data["High"][0]
            low_price = data["Low"][0]
            volume = data["Volume"][0]

            # add to the database
            self.cursor.execute(
                f"INSERT INTO ticker_data (ticker_id, price, open, close, high, low, volume) VALUES ('{ticker}', {self.get_market_value(ticker)}, {open_price}, {close_price}, {high_price}, {low_price}, {volume});"
            )
            self.db.commit()

            # todo update the total return for each ticker in the portfolio
            self.update_total_return(ticker)

    def add_ticker(self, ticker_id: str):
        """
        add_ticker Adds a ticker to the tickers table if it doesn't already exist and is a valid Yahoo! Finance ticker.

        Args:
            ticker_id (str): Ticker to add to the database.
        """

        # check if the ticker is valid
        if not self.is_valid_ticker(ticker_id):
            return  # fail

        try:
            self.cursor.execute(
                f"INSERT INTO tickers (ticker_id) VALUES ('{ticker_id}');"
            )
            print("HERE")
            logging.info(f"Added {ticker_id.upper()} to the tickers table.")
            self.db.commit()

        except mysql.connector.errors.IntegrityError:
            logging.warning(f"{ticker_id.upper()} already exists in the database.")
            return  # fail

        # commit changes to the database
        logging.info(f"Added {ticker_id.upper()} to the database.")

    def add_tickers(self, ticker_ids: list):
        """
        add_tickers Method to add multiple tickers to the database at once.

        Args:
            ticker_ids (list): A list of tickers to add to the database.
        """
        for ticker_id in ticker_ids:
            self.add_ticker(ticker_id)

    def get_ticker_data(self, ticker_id: str):
        """
        get_ticker_data Returns all data for a given ticker in the ticker_data table.

        Args:
            ticker_id (str): Ticker to get data for.
        """

        self.cursor.execute(f"SELECT * FROM ticker_data WHERE ticker_id='{ticker_id}';")
        data = self.cursor.fetchall()

        return data

    def get_transactions(self, ticker_id: str):
        """
        get_transcations Returns all transactions for a given ticker in the transactions table.

        Args:
            ticker_id (str): Ticker to get transactions for.

        Returns:
            dict: A dict of all transactions for the ticker.
        """
        self.cursor.execute(
            f"SELECT * FROM transactions WHERE ticker_id='{ticker_id}';"
        )
        data = self.cursor.fetchall()

        # return jsonify(data)

        # format the data to be returned
        transaction_num = [d[0] for d in data]
        ticker_id = [d[1] for d in data]
        num_shares = [d[2] for d in data]
        price = [d[3] for d in data]
        transaction_type = [d[4] for d in data]
        timestamp = [d[5] for d in data]

        # put into a dict
        data = []
        for i in range(len(transaction_num)):
            data.append(
                {
                    "transaction_num": transaction_num[i],
                    "ticker_id": ticker_id[i].upper(),
                    "num_shares": num_shares[i],
                    "price": f"${price[i]:.2f}",
                    "total": f"${num_shares[i] * price[i]:.2f}",
                    "transaction_type": transaction_type[i].capitalize(),
                    "timestamp": str(timestamp[i]),
                }
            )

        # reverse the list so the most recent transactions are first
        data.reverse()

        return data

    def get_transaction_history(self):
        """
        get_transaction_history Returns all transactions in the transactions table.

        Returns:
            dict: A dict of all transactions in the transactions table.
        """
        self.cursor.execute("SELECT * FROM transactions;")
        data = self.cursor.fetchall()

        # format the data to be returned
        transaction_num = [d[0] for d in data]
        ticker_id = [d[1] for d in data]
        num_shares = [d[2] for d in data]
        price = [d[3] for d in data]
        transaction_type = [d[4] for d in data]
        timestamp = [d[5] for d in data]

        # put into a dict
        data = []
        for i in range(len(transaction_num)):
            data.append(
                {
                    "transaction_num": f"{transaction_num[i]:5d}",
                    "ticker_id": ticker_id[i].upper(),
                    "num_shares": num_shares[i],
                    "price": f"${price[i]:.2f}",
                    "total": f"${num_shares[i] * price[i]:.2f}",
                    "transaction_type": transaction_type[i].capitalize(),
                    "timestamp": str(timestamp[i]),
                }
            )

        # reverse the list so the most recent transactions are first
        data.reverse()

        return data

    def display_portfolio(self):
        """
        display_portfolio Returns all data in the user portfolio.

        Returns:
            dict: A sorted dict of all data for the user portfolio.
        """
        self.cursor.execute("SELECT * FROM portfolio;")
        portfolio = self.cursor.fetchall()

        tickers = [p[0] for p in portfolio]
        shares = [p[1] for p in portfolio]
        returns = [p[2] for p in portfolio]
        asset_types = [p[3] for p in portfolio]

        portfolio_data = []
        for i in range(len(tickers)):
            portfolio_data.append(
                {
                    "ticker_id": tickers[i].upper(),
                    "num_shares": shares[i],
                    "curr_price": f"${self.get_market_value(tickers[i]):.2f}",
                    "total_return": f"{returns[i]:.2f}%",
                    "asset_type": asset_types[i].upper(),
                }
            )

        sorted_portfolio_data = sorted(
            portfolio_data, key=lambda x: x["num_shares"], reverse=True
        )

        return sorted_portfolio_data

    def display_portfolio_yf(self):
        """
        display_portfolio Returns all data for the user portfolio with contextual yfinance data.

        Returns:
            dict: A sorted dict of all data for the user portfolio.
        """
        self.cursor.execute("SELECT * FROM portfolio;")
        portfolio = self.cursor.fetchall()

        tickers = [p[0] for p in portfolio]
        shares = [p[1] for p in portfolio]
        returns = [p[2] for p in portfolio]
        asset_types = [p[3] for p in portfolio]

        portfolio_data = []
        for i in range(len(tickers)):
            ticker = yf.Ticker(tickers[i])
            yr_high = ticker.info["fiftyTwoWeekHigh"]
            yr_low = ticker.info["fiftyTwoWeekLow"]
            name = ticker.info["shortName"]

            portfolio_data.append(
                {
                    "ticker_id": tickers[i].upper(),
                    "name": name,
                    "num_shares": shares[i],
                    "curr_price": f"${self.get_market_value(tickers[i]):.2f}",
                    "total_return": f"{returns[i]:.2f}%",
                    "high_52": f"${yr_high:.2f}",
                    "low_52": f"${yr_low:.2f}",
                    "asset_type": asset_types[i].upper(),
                    "net_gainloss": f"{self.calc_gainloss(tickers[i]):.2f}%",
                }
            )

        sorted_portfolio_data = sorted(
            portfolio_data, key=lambda x: x["num_shares"], reverse=True
        )

        return sorted_portfolio_data

    def ticker_details(self, ticker_id: str):
        """
        ticker_details Returns all data for a given ticker in the portfolio.

        Args:
            ticker_id (str): Ticker to get data for.
        """
        self.cursor.execute(f"SELECT * FROM portfolio WHERE ticker_id='{ticker_id}';")

        ticker = self.cursor.fetchone()

        # get yfinance data about the ticker
        ticker_data = yf.Ticker(ticker_id).info

        # format the data to be returned
        # todo complete this function for stock details button

    def get_asset_type(self, ticker_id: str):
        """
        get_asset_type Return the asset type of a ticker.

        Args:
            ticker_id (str): Ticker to get the asset type of.

        Returns:
            str: Asset type of the ticker.
        """

        ticker = yf.Ticker(ticker_id)
        ticker_info = ticker.info
        asset_type = ticker_info.get("quoteType", "N/A")

        return asset_type

    def asset_type_breakdown(self):
        """
        asset_type_breakdown Returns the asset type breakdown of the user portfolio.

        Returns:
            dict: A dict of the asset type breakdown of the user portfolio.
        """
        # get the asset types in the portfolio
        self.cursor.execute("SELECT total_shares, asset_type FROM portfolio;")
        data = self.cursor.fetchall()

        shares = [d[0] for d in data]
        asset_types = [d[1].upper() for d in data]

        # count of shares for each asset type
        total_shares = sum(shares)
        asset_type_counts = {}
        for i in range(len(asset_types)):
            asset_type_counts[asset_types[i]] = (
                asset_type_counts.get(asset_types[i], 0) + shares[i]
            )

        # dict with asset type and percentage of portfolio
        asset_type_breakdown = {}
        for asset_type in asset_type_counts:
            asset_type_breakdown[asset_type] = (
                asset_type_counts[asset_type] / total_shares
            )

        return asset_type_breakdown

    def calc_gainloss(self, ticker_id):
        """
        calc_gain Calculates the gain from a ticker.

        Args:
            ticker_id (str): Ticker to calculate the gain from.

        Returns:
            float: The gain from the ticker.
        """
        # get the current price of the ticker
        curr_price = self.get_market_value(ticker_id)

        # get the price of the ticker at the time of purchase
        self.cursor.execute(
            f"SELECT num_shares, price FROM transactions WHERE ticker_id='{ticker_id}' AND transaction_type='buy';"
        )
        data = self.cursor.fetchall()

        # loop through all transactions
        gainloss = 0
        for row in data:
            num_shares = int(row[0])
            price = float(row[1])
            gainloss += num_shares * ((curr_price - price) / price)

        return gainloss * 100  # return as a percentage