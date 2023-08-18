CREATE DATABASE team11;

USE team11;

CREATE TABLE tickers (
    ticker_id varchar(10) PRIMARY KEY
);

-- CREATE TABLE transactions (
--     tran_type varchar(4),
--     amount decimal,
--     tran_time timestamp,
--     ticker_id varchar(10),
--     FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
-- );

CREATE TABLE tickersData (
    ticker_id varchar(10),
    price decimal,
    timestamp timestamp,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);