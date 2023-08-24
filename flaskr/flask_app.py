import logging
import os

import mysql.connector
import yfinance as yf
from db_api import DatabaseEditor
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_restful import Api, Resource, reqparse

# load the database password from the .env file
load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

app = Flask(__name__)
api = Api(app)


class CreatePortfolioTableItem(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /create_portfolio_table
    def get(self):
        table = {}
        for t_id in self.db_editor.get_tickers():
            try:
                market_value = self.db_editor.get_market_value(t_id)
                num_shares = self.db_editor.get_num_shares(t_id)
                asset_type = self.db_editor.get_asset_type(t_id)
                # net_gainloss = self.db_editor.calc_gainloss(t_id)
                # fetch yfinance data for a given ticker
                ticker = yf.Ticker(t_id)
                high_52 = ticker.info["fiftyTwoWeekHigh"]
                low_52 = ticker.info["fiftyTwoWeekLow"]
                name = ticker.info["shortName"]

                high_52 = f"{high_52:.2f}"
                low_52 = f"{low_52:.2f}"

                table[t_id] = {
                    "market_value": f"{market_value:.2f}",
                    "num_shares": num_shares,
                    # "net_gainloss": net_gainloss,
                    "high_52": high_52,
                    "low_52": low_52,
                    "name": name,
                    "asset_type": asset_type,
                }
            except:
                return {"error": f"Data for ticker {t_id} not found"}, 404

        # sort table by num_shares
        table = dict(
            sorted(table.items(), key=lambda item: item[1]["num_shares"], reverse=True)
        )
        return table, 200


class PortfolioResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /portfolio
    def get(self):
        """
        get Get the portfolio from the database (table: portfolio)

        Returns:
            dict: A dictionary containing the portfolio data.
        """
        portfolio = self.db_editor.display_portfolio()
        return portfolio, 200


class TransactionHistoryResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /transaction_history/<t_id>
    def get(self, t_id):
        """
        get Get all transactions for a given ticker from the database.

        Args:
            t_id (int): ID of the transaction to get.
        """
        transaction = self.db_editor.get_transactions(t_id)
        if transaction:
            return transaction, 200
        else:
            return {"error": f"Transaction {t_id} not found"}, 404


class TranscationsHistoryResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /transaction_history
    def get(self):
        """
        get Get the complete transaction history from the database.

        Returns:
            dict: A dictionary containing the transaction history data.
        """
        transaction_history = self.db_editor.get_transaction_history()
        return transaction_history, 200


class BuyResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # POST /buy/<t_id>/<num_shares>
    def post(self, t_id, num_shares):
        """
        post Buy a given ticker.

        Args:
            t_id (int): ID of the ticker to buy.
            num_shares (int): Number of shares to purchase.
        """
        status = self.db_editor.buy_ticker(t_id, num_shares)
        return status, 200


class SellResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # POST /sell/<t_id>/<num_shares>
    def post(self, t_id, num_shares):
        """
        post Sell a given ticker.

        Args:
            t_id (int): ID of the ticker to sell.
            num_shares (int): Number of shares to sell.
        """
        status = self.db_editor.sell_ticker(t_id, num_shares)
        return status, 200


class TickersResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /tickers
    def get(self):
        """
        get Get all tickers in the user's portfolio.

        Returns:
            list: A list of tickers.
        """
        tickers = self.db_editor.get_tickers()
        return tickers, 200


class TickerDataResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /tickers/<t_id>
    def get(self, t_id):
        """
        get Get a ticker from the database (table: portfolio)

        Args:
            t_id (str): Symbol of the ticker to get.
        """
        ticker = self.db_editor.get_ticker(t_id)
        if ticker:
            return ticker
        else:
            return {"error": f"Ticker {t_id} not found"}, 404


class TickerDataTableResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /ticker_data/<t_id>
    def get(self, t_id):
        return self.db_editor.get_ticker_data(t_id)


class AssetsBreakdownResource(Resource):
    def __init__(self):
        self.db_editor = DatabaseEditor(
            host="localhost", user="root", password=DB_PASSWORD, database="team11"
        )

    def __del__(self):
        self.db_editor.disconnect()

    # GET /assets_breakdown
    def get(self):
        """
        get Get the asset breakdown from the database (table: portfolio)

        Returns:
            dict: A dictionary containing the asset breakdown data.
        """
        asset_breakdown = self.db_editor.asset_type_breakdown()
        return asset_breakdown, 200


# add resources to api
api.add_resource(CreatePortfolioTableItem, "/create_portfolio_table")
api.add_resource(PortfolioResource, "/portfolio")
api.add_resource(TransactionHistoryResource, "/transaction_history/<string:t_id>")
api.add_resource(TranscationsHistoryResource, "/transaction_history")
api.add_resource(BuyResource, "/buy/<string:t_id>/<int:num_shares>")
api.add_resource(SellResource, "/sell/<string:t_id>/<int:num_shares>")
api.add_resource(TickersResource, "/tickers")
api.add_resource(TickerDataResource, "/tickers/<string:t_id>")
api.add_resource(AssetsBreakdownResource, "/assets_breakdown")
api.add_resource(TickerDataTableResource, "/ticker_data/<string:t_id>")


@app.route("/")
def home():
    db_editor = DatabaseEditor(
        host="localhost", user="root", password=DB_PASSWORD, database="team11"
    )

    portfolio_data = db_editor.display_portfolio_yf()
    # asset_type_data = db_editor.asset_type_breakdown()

    # refresh db with yfinance data
    # db_editor.update_ticker_data()
    db_editor.disconnect()

    return render_template("home.html", portfolio_data=portfolio_data)


@app.route("/transactions")
def transactions():
    # get transcation history
    db_editor = DatabaseEditor(
        host="localhost", user="root", password=DB_PASSWORD, database="team11"
    )

    transaction_history = db_editor.get_transaction_history()
    db_editor.disconnect()
    return render_template("transactions.html", transaction_history=transaction_history)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/buy_sell", methods=["POST"])
def buy_sell():
    # get form data
    ticker_id = request.form["ticker_id"]
    num_shares = request.form["num_shares"]
    transaction_type = request.form["transaction_type"]

    db_editor = DatabaseEditor(
        host="localhost", user="root", password=DB_PASSWORD, database="team11"
    )

    if transaction_type == "buy":
        status = db_editor.buy_ticker(ticker_id, num_shares)
    else:  # sell
        status = db_editor.sell_ticker(ticker_id, num_shares)

    db_editor.disconnect()
    return render_template("transaction_status.html", status=status)


@app.route("/docs")
def docs():
    return render_template("docs.html")


if __name__ == "__main__":
    app.run(debug=True)
