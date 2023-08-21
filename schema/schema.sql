CREATE DATABASE team11;

USE team11;

-- tickers (not necessarily ones the user has) 
CREATE TABLE tickers (
    ticker_id varchar(10) PRIMARY KEY
);

CREATE TABLE ticker_data (
    ticker_id varchar(10),
    price decimal,
    date timestamp,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

-- tickers the user has
CREATE TABLE portfolio (
    ticker_id varchar(10),
    num_share int,
    buy_in_price decimal,
    total_return decimal,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

CREATE TABLE ticker_returns (
    ticker_id varchar(10),
    mean_return decimal,
    date timestamp,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);