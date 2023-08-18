import mysql.connector
import logging  # this should allow all messages to be displayed
import yfinance as yf
import requests

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

        try:
            self.db = mysql.connector.connect(
                host=host, user=user, password=password, database=database
            )
            if self.db.is_connected():
                logging.info(f"Successfully connected to {database} database.")
        except mysql.connector.errors.ProgrammingError:
            logging.error(
                f"Error connecting to the {database} database. Check your credentials."
            )
            exit(1)

        self.cursor = self.db.cursor()

    def close_editor(self):
        """
        close_editor Closes the database editor.
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
        self.cursor.execute("SHOW TABLES;")
        tables = self.cursor.fetchall()
        if len(tables) == 0:
            logging.warning(f"No tables in database {self.db.database}.")
            return None
        else:
            logging.debug(f"Tables in database {self.db.database}: {tables}")
        return tables

    def get_tickers(self):
        # get all tickers from the database
        self.cursor.execute("SELECT ticker_id FROM tickers;")
        tickers = self.cursor.fetchall()
        return [t[0] for t in tickers]

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

    def add_ticker(self, ticker_id: str):
        """
        add_ticker Adds a ticker to the tickers table if it doesn't already exist and is a valid Yahoo! Finance ticker.

        Args:
            ticker_id (str): Ticker to add to the database.
        """
        # check if the ticker is valid
        if self.is_valid_ticker(ticker_id):
            return 1  # fail

        try:
            self.cursor.execute(
                f"INSERT INTO tickers ticker_id VALUES '{ticker_id.upper()}';"
            )
        except mysql.connector.errors.IntegrityError:
            logging.warning(f"{ticker_id} already exists in the database.")
            return 1  # fail

        # commit changes to the database
        self.db.commit()
        logging.info(f"Added {ticker_id} to the database.")
        return 0  # success

    def add_tickers(self, ticker_ids: list):
        """
        add_tickers Method to add multiple tickers to the database at once.

        Args:
            ticker_ids (list): A list of tickers to add to the database.
        """
        for ticker_id in ticker_ids:
            self.add_ticker(ticker_id)
        return 0  # success

    def get_ticker_data(self, ticker_id: str):
        """
        get_ticker_data Returns all data for a given ticker in the tickersData table.

        Args:
            ticker_id (str): Ticker to get data for.
        """
        self.cursor.execute(
            f"SELECT * FROM tickersData WHERE ticker_id='{ticker_id.upper()}';"
        )
        data = self.cursor.fetchall()
        return data

    # todo: is str the right type for timestamp?
    def add_ticker_data(self, ticker_id: str, price: float, timestamp: str):
        # add data where the ticker_id and date don't already exist
        """
        add_ticker_data Add data for a given ticker to the database at the given timestamp.

        Args:
            ticker_id (str): Ticker to add data for.
            price (float): Price of the ticker at the given timestamp.
            timestamp (str): Timestamp of the data.
        """

        try:
            self.cursor.execute(
                f"INSERT INTO tickersData (ticker_id, price, timestamp) VALUES ('{ticker_id.upper()}', {price}, '{timestamp}');"
            )
        except mysql.connector.errors.IntegrityError:
            logging.warning(
                f"{ticker_id} data for {timestamp} already exists in the database."
            )
            return

        # commit changes to the database
        self.db.commit()
        logging.info(f"Added {ticker_id} data for {timestamp} to the database.")


if __name__ == "__main__":
    db_editor = DatabaseEditor(password="guatemala", database="team11")
    db_editor.add_tickers(["AAPL", "TSLA", "MSFT"])
    db_editor.is_valid_ticker("lpol")
    print(db_editor.get_tickers())
    db_editor.add_ticker_data("AAPL", 120.0, "2021-02-02")
    print(db_editor.get_ticker_data("AAPL"))
    db_editor.close_editor()
