import mysql.connector
import logging  # this should allow all messages to be displayed
import yfinance as yf

# todo remove this line for production code
logging.basicConfig(level=logging.DEBUG)


# class to access and edit the database
class DatabaseEditor:
    def __init__(self, password: str, database: str, host="localhost", user="root"):
        """
        __init__ Initializer for the DatabaseEditor class.

        Args:
        ----
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
        else:
            logging.debug(f"Tables in database {self.db.database}: {tables}")
        return tables

    def add_ticker(self, ticker_id: str):
        """
        add_ticker Adds a ticker to the database if it doesn't already exist and is a valid Yahoo! Finance ticker.

        Args:
            ticker_id (str): Ticker to add to the database.
        """
        # check if the ticker is valid
        if yf.Ticker(ticker_id).info == {}:
            logging.warning(f"{ticker_id} is not a valid Yahoo! Finance ticker.")
            return

        try:
            self.cursor.execute(
                f"INSERT INTO tickers (ticker_id) VALUES ('{ticker_id.upper()}');"
            )
        except mysql.connector.errors.IntegrityError:
            logging.warning(f"{ticker_id} already exists in the database.")
            return

        # commit changes to the database
        self.db.commit()
        logging.info(f"Added {ticker_id} to the database.")

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
    # use input to get host, user, password, and database
    # password = input("Enter database password: ")
    password = "guatemala"

    db_editor = DatabaseEditor(
        host="localhost", user="root", password=password, database="team11"
    )

    db_editor.show_tables()

    db_editor.add_ticker("AAPL")
    db_editor.add_ticker_data("AAPL", 100, "2021-04-01 00:00:00")
    db_editor.close_editor()
