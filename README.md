# Backtest, Digest, Invest
#### Video Demo:  https://youtu.be/XksmiBNmukc
#### Description:
With an unprecedented influx of new investors to the stock market, there is a greater need to have more available tools and information to allow them to make more informed investment decisions.
This web application aims to assist new investors to the stock market with information related to different investment strategies.
This website provides comparisons of investment styles and their historical performance to show the advantages and disadvantages of various investment strategies, in this case over a 2 year period.

##### Project Files

###### nasdaq.csv
This file was downloaded from the [Nasdaq](https://www.nasdaq.com/) website so that an up to date list of active stock symbols could be used. This was chosen over the IEX service used during the Week 9 problem set since it can be freely downloaded at no cost.

###### symbols.db
This database contains the stock tickers and stock names provided from nasdaq.csv. This was populated via code in application.py, and has been commented out so that how it was done is still viewable.

###### layout.html
Template file for all the html pages. Includes the navigation bar, and retrieval of Bootstrap and jquery. An improvement could be to separate out the javascript into a separate file.

###### index.html
Landing page for the web app. There is a search bar to input Stock Symbols/Tickers to find out more information. The search bar has an autocomplete feature that uses the symbol data listed in the symbols.db to offer ticker suggestions after each key press. The suggestions are listed below the search bar and can be interacted with to update the search bar with the stock code.
On triggering the search, the submit button will transfer the user to the stockInfo page.

###### stockInfo.html
This page shows details about the stock the user searched for. This includes company fundamental details and the price history for the last 2 years, basic technical indicator data for the price, and investment strategy descriptions. The price is displayed in chart.js over time comparing price/simple moving average line charts on the left axis, and volume of traded stock on the right axis. The user can pick a starting account value and a trading buy/sell trigger option to be compared with a buy & hold strategy, and a dollar-cost-averaging strategy. Using the submit button will transfer the user to the results page. Improvements could include more technical indicator options for the trading strategies, such as exponential moving averages and different cross-over buy/sell conditions, and a more fully fledged and interactive chart; this could be done by embedding a feature complete package such as TradingView.

###### results.html
This page shows a comparison of backtests between the buy & hold, dollar-cost-averaging, and trading strategies over the previous 2 years. This allows the user to see a graphical overview of how the different strategies perform (in terms of overall account value) during different periods of volatility, decline, or growth in the selected stock.

###### application.py
Flask sessions have been implemented to allow the flash message system to operate. This uses a static password; an improvement would use a randomised password for each new session, though there is no sensitive personal information to protect on the site.

The index.html functionality is handled here, having already pre-filled the symbols.db to support the autocomplete feature on the search bar. Each keyup event triggers an AJAX request for a search function to return possible stocks related to the current search letters. The submit form will take the symbol code and pass it through the yfinance API to grab a pandas DataFrame of that stock's information, which is converted into lists that can be used by chart.js for graphing; technical indicator data is also generated from this data to be used in the stockInfo page. There is a dicrepancy between the yfinance symbol tickers and the nasdaq tickers, which required some symbol adjustments before sending to yfinance, for now yfinance's open source nature had it included in the project, but an improvement here would be to have a symbol ticker source that matches the stock information source for smoother requests.

The stockInfo.html functionality is handled here for stock symbol searches from the index.html page, as described above. There is also error checking on the search bar input for if the code is not found via yfinance, triggering a message banner on the index.html page.

The resuts.html functionality is handed here, as described above, and generating the backtest data. Daily account values are calculated for each strategy as list data that can be used by chart.js. Overall data is also calculated, such as profit/loss and % return, and sent to be displayed on the results page. There are some calculations performed in jinja2, based on Australian tax laws, and used in the performance data to outline the effect of selling stock before or after 12 months of holding. There is also error checking on the 2 user input fields that, if triggered, return the user to the index page.

Improvements to this could include separating out generic functions into a utilies file that can be generically imported into any project in future.

###### about.html
Summary of Web Application and tools used to create it.

###### readme.md
Provides project information for viewers and CS50 staff, readable via GitHub or other markdown viewing tools.