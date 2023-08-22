from flask import Flask, jsonify, request, render_template
from flask_restful import Api, Resource, reqparse
import mysql.connector
import os
from dotenv import load_dotenv
from db_api import DatabaseEditor

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

app = Flask(__name__)

# cursor = db.cursor()
api = Api(app)

db = mysql.connector.connect(
    host="localhost", user="root", password=DB_PASSWORD, database="team11"
)


class TickersResource(Resource):
    # GET /tickers
    def get(self):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tickers;")
        tickers = cursor.fetchall()
        cursor.close()
        return jsonify(tickers)


class TickerDataResource(Resource):
    # GET /tickers/<ID>
    def get(self, t_id):
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tickersData WHERE ID = %s", (t_id))
        ticker = cursor.fetchone()
        cursor.close()
        if ticker:
            return jsonify(ticker)
        else:
            return {"error": "ticker not found"}, 404

    # DELETE /tickers/<ID>
    def delete(self, t_id):
        cursor = db.cursor()
        cursor.execute("DELETE FROM tickers WHERE id = %s", (t_id,))
        db.commit()
        cursor.close()
        return {"message": "Ticker deleted successfully"}, 200

    # PUT /tickers/<ID>
    def put(self, t_id):
        parser = reqparse.RequestParser()
        parser.add_argument("price", required=True, type=float)
        parser.add_argument("timestamp", required=True)

        args = parser.parse_args()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE tickersData SET price = %s, timestamp = %s WHERE id = %s",
            (args["price"], args["timestamp"], t_id),
        )
        db.commit()
        cursor.close()
        good_response = ({"message": "ticker data updated scucessfully"}, 200)
        not_found = ({"error": "Ticker not found"}, 404)
        return good_response if cursor.rowcount else not_found


# add resource to api
api.add_resource(TickersResource, "/tickers")
api.add_resource(TickerDataResource, "/tickers/<int:t_id>")

@app.route("/")
def home():
    db_editor = DatabaseEditor(
        host="localhost", user="root", password=DB_PASSWORD, database="team11"
    )

    portfolio_data = db_editor.display_portfolio()
    asset_type_data = db_editor.asset_type_breakdown()

    # refresh db with yfinance data
    db_editor.refresh_db()
         
    return render_template("home.html", portfolio_data=portfolio_data, asset_type_data=asset_type_data)

@app.route("/transactions")
def transactions():
    # get transcation history 
    db_editor = DatabaseEditor(
        host="localhost", user="root", password=DB_PASSWORD, database="team11"
    )

    transaction_history = db_editor.get_transaction_history()
    return render_template("transactions.html", transaction_history=transaction_history)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/buy_sell", methods=["POST"])
def execute_buysell():
    # get form data
    ticker_id = request.form["ticker_id"]
    num_shares = request.form["num_shares"]
    transaction_type = request.form["transaction_type"]

    db_editor = DatabaseEditor(
        host="localhost", user="root", password=DB_PASSWORD, database="team11"
    )

    if transaction_type == "buy":
        status = db_editor.buy_ticker(ticker_id, num_shares)
    else: # sell
        status = db_editor.sell_ticker(ticker_id, num_shares)

    db_editor.disconnect()
    return render_template("transaction_status.html", status=status)


if __name__ == "__main__":
    app.run(debug=True)
