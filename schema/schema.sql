CREATE DATABASE team11;

USE team11;

-- Tickers (not necessarily ones the user has)
CREATE TABLE tickers (
    ticker_id VARCHAR(10) PRIMARY KEY
);

-- data for the portfolio tickers 
CREATE TABLE ticker_data (
    ticker_id VARCHAR(10),
    price DECIMAL,
    open DECIMAL,
    low DECIMAL,
    close DECIMAL,
    high DECIMAL,
    volume INT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

-- Tickers the user has
CREATE TABLE portfolio (
    ticker_id VARCHAR(10),
    total_shares INT,
    total_return DECIMAL,
    asset_type VARCHAR(10),
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

CREATE TABLE transactions (
    transaction_num INT AUTO_INCREMENT PRIMARY KEY,
    ticker_id VARCHAR(10),
    num_shares INT,
    price DECIMAL, -- price per share (negative for sell)
    transaction_type VARCHAR(10), -- buy or sell
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

CREATE TABLE ticker_returns (
    ticker_id VARCHAR(10),
    mean_return DECIMAL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker_id) REFERENCES tickers(ticker_id)
);

CREATE TABLE accounts (
    account_num INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(20),
    password VARCHAR(20),
    email VARCHAR(50),
    first_name VARCHAR(20),
    last_name VARCHAR(20),
    balance DECIMAL
);