CREATE DATABASE team11;

USE team11;

CREATE TABLE portfolio (
    ticker_id varchar(10) PRIMARY KEY,
    num_shares int,
    buy_in_price decimal,
    total_return decimal
);

CREATE TABLE ticker_data (
    ticker_id varchar(10),
    price decimal,
    date timestamp,
    FOREIGN KEY(ticker_id) REFERENCES portfolio(ticker_id)
);

CREATE TABLE ticker_return (
    ticker_id varchar(10),
    mean_return decimal,
    date timestamp,
    FOREIGN KEY(ticker_id) REFERENCES portfolio(ticker_id)
);
