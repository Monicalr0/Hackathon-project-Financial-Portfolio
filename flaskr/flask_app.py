from flask import Flask, jsonify, request, render_template
from flask_restful import Api, Resource, reqparse
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD")

app = Flask(__name__)
# TODO: update DB info
db = mysql.connector.connect(
    host="localhost", user="root", password=DB_PASSWORD, database="team11"
)

cursor = db.cursor()
api = Api(app)


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
    return render_template("home.html")


@app.route("/page1")
def page1():
    return render_template("page1.html")


if __name__ == "__main__":
    app.run(debug=True)
