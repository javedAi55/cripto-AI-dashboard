# Crypto Market Analysis & Risk Dashboard

A Streamlit dashboard for conservative, rule-based cryptocurrency analysis using public Binance spot klines. It does not place trades, request private exchange keys, promise outcomes, or provide investment advice.

## Features

- Completed 15m and 1h candle analysis; optional 4h trend confirmation.
- EMA 20/50/200, Wilder RSI(14), MACD, ATR(14), volume confirmation, and recent high/low structure.
- BUY / LONG, SELL / SHORT, or WAIT / NO TRADE based on multi-timeframe agreement, score separation, and multiple confirmations. Extreme RSI and weak/sideways setups are rejected.
- Scores from 0 to 100 are rule-based setup-quality scores, not probabilities of winning or profit. No profitability claim is made; historical backtesting has not been performed.
- Hypothetical ATR-based stops/targets, quantity, position notional, estimated margin, leverage, and maximum planned loss.
- Coin scanner continues when a symbol fails and reports per-symbol errors.
- Deduplicated CoinDesk, Cointelegraph, and Decrypt RSS/Atom headlines with publication time and original article link. No sentiment classifier is used.

## Risk and data limitations

Position quantity is capital multiplied by risk percent divided by stop distance. Estimated margin is position notional divided by user-entered leverage; leverage is not characterized as safe. Planned loss excludes fees, slippage, funding, liquidation, gaps, and exchange-specific rules. Actual outcomes may differ. Binance spot availability changes, and public endpoints may rate-limit or be unavailable; errors appear in the app.

## Run locally

Python 3.11 is the checked-in devcontainer baseline; the source avoids syntax newer than Python 3.9.

~~~~bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
~~~~

## Tests

~~~~bash
python -m unittest discover -s tests -v
python -m py_compile app.py analysis_engine.py tests/test_analysis_engine.py
~~~~

Tests use deterministic local candle data and do not call Binance or RSS. They do not verify live endpoint or Streamlit Community Cloud availability.

## Streamlit Community Cloud

Deploy app.py from the repository root with requirements.txt. The app uses Python standard-library RSS parsing and public HTTP endpoints, with no secret configuration or trading credentials. The devcontainer baseline is Python 3.11; Community Cloud defaults to Python 3.12. Dependency ranges allow compatible Streamlit, pandas, and requests releases.

## Supported symbols

TAO, NEAR, RENDER, FET, WLD, SOL, BTC, ETH, BNB, DOGE, XRP, and PEPE quoted in USDT. Unavailable spot pairs appear as scan errors instead of stopping the scan.
