from flask import Flask, jsonify, request
from flask_restful import Api, Resource, reqparse
import mysql.connector

app = Flask(__name__)
# TODO: update DB info
db = mysql.connector.connect(
    host="localhost", user="root", password="c0nygre", database="conygre"
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


# class TickerDataResource(Resource):

if __name__ == "__main__":
    app.run()
