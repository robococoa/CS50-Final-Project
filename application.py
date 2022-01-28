from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, escape, session, jsonify
from datetime import datetime
from stockstats import StockDataFrame
import math
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import csv


# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Set session key
app.config.update(SECRET_KEY='temporary_secret_key',ENV='development')
#app.secret_key = "TEMP_SECRET_KEY"


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///symbols.db")


# Create database of Stock Symbols
#with open("nasdaq.csv", "r") as file:
#    reader = csv.reader(file)
#    next(reader)
#    for row in reader:
#        symbol = row[0]
#        name = row[1]
#        db.execute("INSERT OR IGNORE INTO symbols (symbol, name) VALUES (?, ?)", symbol, name)


@app.route("/")
def index():
    """Show portfolio of stocks"""
    return render_template("/index.html")


@app.route("/search")
def search():
    query = "%" + request.args.get("q") + "%"
    symbols = db.execute("SELECT * FROM symbols WHERE symbol LIKE ? OR name LIKE ?", query, query)
    return jsonify(symbols)


@app.route("/stockInfo", methods=["POST"])
def stock_info():
    if request.method == "POST":
        """Show info for selected stock and investment options"""
        years = 3
        search = escape(request.form.get("q")).upper()

        # yahoo finance uses "-" instead of "/", and doesn't use ^XYZ suffixes
        search = search.replace("/", "-")
        i = 0
        for char in search:
            if char == "^":
                # Only use up to where the ^ is
                search = search[:i]
            else:
                i += 1
        symbol_dump = get_symbol_data(search)
        if len(symbol_dump[0]) == 0:
            flash("Could not find and stock data for this symbol on Yahoo Finance, it may no longer exist there. Please try again.")
            return redirect('/')
        symbol_data = symbol_dump[0]
        symbol_info = symbol_dump[1]

        # Separate data for chart.js
        volume = [row["Volume"] for row in symbol_data]
        price = [row["Close"] for row in symbol_data]
        date = [row["Date"] for row in symbol_data]

        # Get 20, 50, 200 SMAs
        sma20 = moving_average(20, price)
        sma50 = moving_average(50, price)
        sma200 = moving_average(200, price)

        # Trim down to 2 years so there are no gaps in the chart
        volume = trim_data(volume)
        price = trim_data(price)
        date = trim_data(date)
        sma20 = trim_data(sma20)
        sma50 = trim_data(sma50)
        sma200 = trim_data(sma200)

        return render_template("/stockInfo.html", symbol_info=symbol_info, date=date, price=price, volume=volume, sma20=sma20, sma50=sma50, sma200=sma200, results=results)


@app.route("/results", methods=["POST"])
def results():
    """Show results for selected stock and investment options"""
    if request.method == "POST":
        symbol = escape(request.form.get("symbol"))
        bank = int(request.form.get("bank"))
        # Check for invalid bank value
        if bank < 100 or bank > 9999999999:
            flash("Invalid action. Please start again.")
            return redirect('/')
        # Check for invalid buy_sell value
        try:
            buy_sell = int(request.form.get("buy-sell"))
        except ValueError as ex:
            flash("Invalid action. Please start again.")
            return redirect('/')
        if buy_sell < 8 or buy_sell > 200:
            flash("Invalid action. Please start again.")
            return redirect('/')
        start_parcel = bank

        symbol_dump = get_symbol_data(symbol)
        symbol_data = symbol_dump[0]

        # Separate data for chart.js
        volume = [row["Volume"] for row in symbol_data]
        price = [row["Close"] for row in symbol_data]
        date = [row["Date"] for row in symbol_data]

        # Calculate trading / account value comparison points
        buy_sell_values = moving_average(buy_sell, price)

        # Calculate buy and hold
        start_price = price[math.floor(len(price) / 3)]
        hodl_end_value = start_parcel * (price[len(price) - 1] / start_price)
        hodl_gains = round(hodl_end_value - start_parcel, 2)

        # Account value data points at each date point
        hodl_yaxis = get_account_values(price, start_parcel)
        hodl_change_percent = round((hodl_gains / start_parcel) * 100, 2)
        avg_return = hodl_change_percent / 2
        final_account_value = hodl_end_value

        # Account value data points for the DCA strategy
        dca_yaxis = get_dca_account_values(price, bank)
        dca_end_value = round(dca_yaxis[len(dca_yaxis) - 1], 2)
        dca_gains = round(dca_end_value - start_parcel, 2)
        dca_change_percent = round((dca_gains / start_parcel) * 100, 2)
        dca_avg_return = round(dca_change_percent / 2, 2)

        # Account value data points for the Trading strategy
        trade_results = get_trading_account_values(price, bank, start_parcel, buy_sell_values)
        trade_yaxis = trade_results[0]
        trade_count = trade_results[1]
        trade_final_account_value = round(trade_yaxis[len(trade_yaxis) - 1], 2)
        trade_gains = round(trade_final_account_value - start_parcel, 2)
        trade_change_percent = round((trade_gains / start_parcel) * 100, 2)
        trade_avg_return = round(trade_change_percent / 2, 2)

        # Trim down to 2 years so there are no gaps in the chart
        volume = trim_data(volume)
        price = trim_data(price)
        date = trim_data(date)
        hodl_yaxis = trim_data(hodl_yaxis)
        trade_yaxis = trim_data(trade_yaxis)
        buy_sell_values = trim_data(buy_sell_values)

        return render_template("/results.html", symbol=symbol, hodl_gains=hodl_gains, hodl_yaxis=hodl_yaxis, hodl_change_percent=hodl_change_percent,
                               price=price, date=date, final_account_value=final_account_value, avg_return=avg_return, trade_yaxis=trade_yaxis,
                               trade_count=trade_count, trade_final_account_value=trade_final_account_value, trade_gains=trade_gains,
                               trade_change_percent=trade_change_percent, trade_avg_return=trade_avg_return, buy_sell_values=buy_sell_values,
                               dca_yaxis=dca_yaxis, dca_end_value=dca_end_value, dca_gains=dca_gains, dca_change_percent=dca_change_percent,
                               dca_avg_return=dca_avg_return)


@app.route("/about")
def about():
    """ Display information for the web app """
    return render_template("/about.html")

def get_symbol_data(symbol):
    # Call yfinance API for symbol data
    symbol = yf.Ticker(symbol)
    symbol_info = symbol.info
    symbol_history = symbol.history(period='3y', actions=False)
    symbol_data = symbol_history.reset_index()
    symbol_data = symbol_data.to_dict(orient='records')

    # Format timestamps into date format
    for i in symbol_data:
        i['Date'] = i['Date'].strftime("%Y-%m-%d")

    return [symbol_data, symbol_info]


# Calculate averages for input time period
def moving_average(timePeriod, price_data):
    moving_averages = []
    period = timePeriod + 1
    for n in range(period):
        moving_averages.append(0)
    i = 0
    while i < (len(price_data) - period):
        period_subset = price_data[i : i + period]
        subset_average = sum(period_subset) / period
        moving_averages.append(subset_average)
        i += 1

    return moving_averages


# Trim to 2 years of data
def trim_data(data_to_trim):
    data = []
    length = len(data_to_trim)
    start = math.floor(length / 3)
    for i in range(start, length):
        data.append(data_to_trim[i])
    return data


# Calculate buy and hold account data points list
def get_account_values(price, start_parcel):
    account_values = []

    # Only generate values for the most recent 2 years
    length = len(price)
    start = math.floor(length / 3)
    for n in range(start + 1):
        account_values.append(start_parcel)

    # Generate account value data points
    for i in range(start, len(price)):
        account_point = start_parcel * (price[i] / price[start])
        account_values.append(account_point)
        i += 1
    return account_values


# Calculate dollar cost averaging data point list
def get_dca_account_values(price, bank):
    account_values = []
    account_point = 0
    buy_amount = bank / 12
    cash = bank - buy_amount

    # Dollar-cost buying will occur on the 1st 12 months, out of 24 months
    length = len(price)
    month = math.floor(length / 36) # 3 years of price results
    i = math.floor(length / 3) # start account values after 1 year
    months = [n for n in range(i, i * 2, month)]    # contains the first 12 months
    positions = 0

    # Purchase the stock with buy_amount at the start of every month for 12 months
    position_prices = [price[n] for n in months]
    position_point = 0

    # Generate account value data points, same as buy and hold but with 12 staggered starting values
    for n in range(i, length):      # list of days, going up in 1 day steps
        for x in range(0, 12):      # id of purchase months
            if n >= months[x]:      # if month[x] is in the past, then a position is open for that month; calculate the current value of that parcel
                position_point += buy_amount * (price[n] / position_prices[x])
                positions = x + 1

        cash = bank - buy_amount * positions
        account_point = position_point + cash
        account_values.append(account_point)
        position_point = 0
    return account_values


# Calculate trading account data point list
def get_trading_account_values(price, bank, start_value, buy_sell_values): #, allocation
    account_values = []
    cash = bank - start_value
    position_size = None
    position_price = None
    trade_count = 0

    # Only generate values for the most recent 2 years
    length = len(price)
    start = math.floor(length / 3)

    # Set first year values = bank
    for n in range(start):
        account_values.append(bank)

    i = start
    # Check if a buy needs to occur for 1st data point
    if i == start and price[i] > buy_sell_values[i]:
        position_size = bank # * (allocation / 100)
        position_price = price[i]
        cash = bank - position_size
        account_values.append(position_size + cash)
        trade_count += 1
        i += 1
    else:
        account_values.append(bank)
        i += 1

    # Search through looking for buy and sell triggers
    for i in range(i, length):

        # If the closing price is above the selected moving average price, buy
        if price[i] > buy_sell_values[i]:

            # Open a new position if there isn't already an open position
            if i > start and position_size == None:
                position_size = account_values[i - 1] #* (allocation / 100)
                position_price = price[i]
                cash = account_values[i - 1] - position_size
                account_values.append(position_size + cash)
                trade_count += 1
                i += 1

            # There is an active position, record the current value
            elif i >= start and position_size is not None:
                account_point = position_size * (price[i] / position_price)
                account_values.append(account_point + cash)
                i += 1

        # If the closing price is below the selected moving average price, sell if there is an open position
        elif price[i] < buy_sell_values[i]:

            # Check if there is an open position before selling
            if position_size is not None:
                account_point = position_size * (price[i] / position_price)
                account_values.append(account_point + cash)
                position_size = None
                position_price = None
                trade_count += 1
                i += 1

            # There is no active position, record the previous value as the current value
            else:
                account_values.append(account_values[i - 1])
                i += 1
                #print(f"i: {i}, SELL ELSE position_size: {position_size}, position_price: {position_price}, cash: {cash}, account_point: {account_point}, account_value: {account_values[i]}")
        # If neither of the above, account value remains the same
        else:
            account_values.append(account_values[i - 1])
            i += 1

    return [account_values, trade_count]