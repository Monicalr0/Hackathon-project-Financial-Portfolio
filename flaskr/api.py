import mysql.connector
import logging  # this should allow all messages to be displayed
import yfinance as yf
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

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

    def connect(self):
        try:
            db = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.db_name,
            )
            if db.is_connected():
                logging.info(f"Successfully connected to {self.db_name} database.")
        except mysql.connector.errors.ProgrammingError:
            logging.error(
                f"Error connecting to the {self.db_name} database. Check your credentials."
            )
            exit(1)
        return db, db.cursor()

    def disconnect(self, db, cursor):
        """
        disconnect Closes the cursor and database connection.
        """
        try:
            self.cursor.close()
            self.db.close()
            logging.info(f"Database {self.db_name} editor closed.")
        except mysql.connector.errors.InterfaceError:
            logging.error(f"Error closing database {self.db_name} editor.")
            exit(1)

    def get_tables(self):
        """
        get_tables Returns all tables in the database.
        """
        db, cursor = self.connect()  # connect to the database
        # get all tables in the database
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        # check if there are any tables in the database
        if len(tables) == 0:
            logging.warning(f"No tables in database {self.db_name}.")
            return None
        else:
            logging.debug(f"Tables in database {self.db_name}: {tables}")
        self.disconnect(db, cursor)  # disconnect from the database
        return tables

    def get_tickers(self):
        """
        get_tickers Get all tickers from the user portfolio.

        Returns:
            list: List of tickers in the database.
        """
        # get all tickers from the database
        db, cursor = self.connect()  # connect to the database
        try:
            cursor.execute("SELECT ticker_id FROM portfolio;")
            tickers = cursor.fetchall()
            self.disconnect(db, cursor)  # disconnect from the database
            logging.debug(f"Tickers in database {self.db_name}: {tickers}")
            return [t[0] for t in tickers]
        except mysql.connector.errors.ProgrammingError:
            logging.warning(f"No tickers in database {self.db_name}.")
            self.disconnect(db, cursor)  # disconnect from the database
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
            logging.debug(f"{ticker_id} is a valid Yahoo! Finance ticker.")
            return True
        except requests.exceptions.HTTPError:
            logging.warning(f"{ticker_id} is not a valid Yahoo! Finance ticker.")
            return False

    def get_current_price(self, ticker_id: str):
        """
        get_current_price Get the current price of a ticker.

        Args:
            ticker_id (str): Ticker to get the current price of.

        Returns:
            float: Current price of the ticker.
        """
        if self.is_valid_ticker(ticker_id):
            ticker = yf.Ticker(ticker_id)
            current_price = ticker.history(period="1d")["Close"][0]
            return current_price
        return None

    # todo: calc_total_return()
    def calc_total_return(self, ticker_id: str):
        # calc the total return of a ticker from start to today
        # Total Return = (Ending Value - Beginning Value) / Beginning Value
        db, cursor = self.connect()  # connect to the database
        curr_price = self.get_current_price(ticker_id)
        cursor.excute("SELECT num_shares, price, transaction_type FROM transactions WHERE ticker_id = %s", (ticker_id))
        data = cursor.fetchall()

        total_return = 0

        # loop through all transactions
        for row in data:
            if row[2] == "buy": # skip sell transactions
                num_shares = row[0] # number of shares per transaction
                price = row[1] # buy in price at purchase time 
                total_return += num_shares * ((curr_price - price) / price)

        cursor.execute(f"UPDATE portfolio SET total_return = {total_return} WHERE ticker_id = {ticker_id}")
        db.commit()
        
        self.disconnect(db, cursor)  # disconnect from the database

    def buy_ticker(self, ticker_id: str, num_shares: int):
        """
        buy_ticker Method to buy a ticker and add it to the user portfolio.

        Args:
            ticker_id (str): Ticker symbol to buy.
            num_shares (int): Number of shares to buy.
        """
        db, cursor = self.connect()  # connect to the database

        # get the current price of the ticker
        buy_in_price = self.get_current_price(ticker_id)

        # check if the ticker is valid
        if not self.is_valid_ticker(ticker_id):
            logging.warning(f"{ticker_id} is not a valid Yahoo! Finance ticker.")
            self.disconnect(db, cursor)  # disconnect from the database
            return  # fail

        elif ticker_id in self.get_tickers():
            logging.info(
                f"{ticker_id} already exists in the database, updating current portfolio info for purchase."
            )

            # get the current shares for the ticker in the portfolio
            cursor.execute(
                f"SELECT total_shares FROM portfolio WHERE ticker_id='{ticker_id}';"
            )
            shares = cursor.fetchone()[0]
            shares += num_shares

            # update the shares in the portfolio
            cursor.execute(
                f"UPDATE portfolio SET total_shares={shares + num_shares} WHERE ticker_id='{ticker_id}';"
            )
            db.commit()
            logging.info(f"Added {num_shares} shares of {ticker_id} to the database.")

        else:
            logging.info(
                f"{ticker_id} does not exist in the database, adding to portfolio."
            )

            # insert the ticker into the portfolio
            # ? @kara, is total  when you first buy a stock (assuming you dnot already hold shares of that stock)?
            cursor.execute(
                f"INSERT INTO portfolio (ticker_id, total_shares, total_return) VALUES ('{ticker_id}', {num_shares}, 0);"
            )
            db.commit()
            logging.info(f"Added {ticker_id} to user portfolio.")

        # add purchase to transaction history
        cursor.execute(
            f"INSERT INTO transactions (ticker_id, num_shares, price, transaction_type) VALUES ('{ticker_id}', {num_shares}, {buy_in_price}, 'buy');"
        )
        db.commit()
        logging.info(f"Added purchase {ticker_id} to transaction history.")

        # add to tickers
        self.add_ticker(ticker_id)

        # todo update ticker_data table

        # disconnect from the database
        self.disconnect(db, cursor)

    def sell_ticker(self, ticker_id: str, num_shares: int):
        """
        sell_ticker Method to sell a ticker from the user portfolio.

        Args:
            ticker_id (str): Ticker symbol to sell.
            num_shares (int): Number of shares to sell.
        """
        db, cursor = self.connect()
        sale_price = self.get_current_price(ticker_id)

        if not self.is_valid_ticker(ticker_id):
            logging.warning(f"{ticker_id} is not a valid Yahoo! Finance ticker.")
            self.disconnect(db, cursor)  # disconnect from the database
            return  # fail
        elif ticker_id not in self.get_tickers():
            logging.warning(
                f"{ticker_id} is not in the user portfolio, there are no shares to sell."
            )
            self.disconnect(db, cursor)
            return  # fail
        else:
            logging.info(
                f"{ticker_id} exists in the database, updating current portfolio info for sale."
            )

            # get the current shares for the ticker in the portfolio
            cursor.execute(
                f"SELECT total_shares FROM portfolio WHERE ticker_id='{ticker_id}';"
            )
            shares = cursor.fetchone()[0]

            # check if the user is trying to sell more shares than they own
            if num_shares > shares:
                logging.warning(
                    f"Cannot sell {num_shares} shares of {ticker_id}, only {shares} shares are owned. Selling all ({shares}) shares."
                )
                self.disconnect(db, cursor)

            # calculate the number of shares to sell
            to_sell = (shares - num_shares) if num_shares < shares else shares

            # update the shares in the portfolio
            cursor.execute(
                f"UPDATE portfolio SET total_shares={to_sell} WHERE ticker_id='{ticker_id}';"
            )
            db.commit()
            logging.info(f"Sold {to_sell} shares of {ticker_id} for {sale_price} each.")

            # add sale to transaction history
            cursor.execute(
                f"INSERT INTO transactions (ticker_id, num_shares, price, transaction_type) VALUES ('{ticker_id}', {to_sell}, {-sale_price}, 'sell');"
            )
            db.commit()

            # disconnect from the database
            self.disconnect(db, cursor)

    def refresh_db(self):
        """
        refresh_db Method to refresh the database with the latest ticker data.
        """        
        db, cursor = self.connect()  # connect to the database

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
            cursor.execute(
                f"INSERT INTO ticker_data (ticker_id, open, close, high, low, volume) VALUES ('{ticker}', {open_price}, {close_price}, {high_price}, {low_price}, {volume});"
            )
            db.commit()

        # refresh the portfolio
        # todo: what to do about nexted connections? to fix 
        for ticker in tickers:
            # update the total return for each ticker in the portfolio
            self.calc_total_return(ticker)

        # disconnect from the database
        self.disconnect(db, cursor)

    def add_ticker(self, ticker_id: str):
        """
        add_ticker Adds a ticker to the tickers table if it doesn't already exist and is a valid Yahoo! Finance ticker.

        Args:
            ticker_id (str): Ticker to add to the database.
        """
        db, cursor = self.connect()  # connect to the database
        # check if the ticker is valid
        if self.is_valid_ticker(ticker_id):
            return  # fail

        try:
            cursor.execute(
                f"INSERT INTO tickers ticker_id VALUES '{ticker_id.upper()}';"
            )
            db.commit()
            self.disconnect(db, cursor)  # disconnect from the database
        except mysql.connector.errors.IntegrityError:
            logging.warning(f"{ticker_id} already exists in the database.")
            self.disconnect(db, cursor)  # disconnect from the database
            return  # fail

        # commit changes to the database
        logging.info(f"Added {ticker_id} to the database.")

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
        db, cursor = self.connect()  # connect to the database
        cursor.execute(
            f"SELECT * FROM ticker_data WHERE ticker_id='{ticker_id.upper()}';"
        )
        data = cursor.fetchall()
        self.disconnect(db, cursor)  # disconnect from the database
        return data


# todo: DELETE (TESTING ONLY)
if __name__ == "__main__":
    db_editor = DatabaseEditor(password=DB_PASSWORD, database="team11")
    db_editor.add_tickers(["AAPL", "TSLA", "MSFT"])
    db_editor.is_valid_ticker("lpol")
    print(db_editor.get_tickers())
    db_editor.add_ticker_data("AAPL", 120.0, "2021-02-02")
    print(db_editor.get_ticker_data("AAPL"))
    db_editor.close_editor()
