CREATE DATABASE team11;

USE team11;

CREATE TABLE tickers (
    ticker_id varchar(10) PRIMARY KEY
);

CREATE TABLE tickersData (
    ticker_id varchar(10),
    price decimal,
    date timestamp,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

CREATE TABLE portfolio (
    ticker_id varchar(10),
    num_share int,
    buy_in_price decimal,
    totalReturn decimal
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

CREATE TABLE tickersReturn (
    ticker_id varchar(10),
    meanReturn decimal,
    date timestamp
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);