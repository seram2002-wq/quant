CREATE TABLE IF NOT EXISTS company_info (
    code VARCHAR(20),
    company VARCHAR(40),
    last_update DATE,
    PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS daily_price (
    code VARCHAR(20),
    date DATE,
    open BIGINT(20),
    high BIGINT(20),
    low BIGINT(20),
    close BIGINT(20),
    diff BIGINT(20),
    volume BIGINT(20),
    PRIMARY KEY (code, date)
);

SELECT * FROM company_info;
SELECT * FROM daily_price;
SHOW VARIABLES LIKE 'wait_timeout';
SELECT MIN(date), MAX(date) FROM daily_price;