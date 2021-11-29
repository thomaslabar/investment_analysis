#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""invest_functions.py: Contains functions for analyzing investment portfolios based on historical data"""

import pandas as pd
import numpy as np

def organize_data(assets, trend = None, trend_period = None):
    """
    This function takes a list of asset names, loads their price and dividend CSV's, and organizes them into a Pandas DataFrame.
    This dataframe should then be used as an input for the function 'historical_return'. I used to do this step within that
    function, but decided to make it its own function for both increased readability of my code and it allows me to use the
    same dataframe for multiple 'historical_return' call. Among other benefits, this makes all these function calls run
    with data that starts on the same date.
    
    Inputs:
        assets (list of strings):  A list of the assets whose price and dividend data will be used to create the dataframe
        trend (boolean): Will this data be used for a trend-following strategy (i.e., should a moving average be calculated)
        trend_period (int): The number of data points to include for the trend's moving average
    
    Outputs:
        all_data (Pandas DataFrame): The dataframe containing every assets' historical prices, dividend payments, and price
        moving average (if specified)
    """
    
    if trend == None:
        trend = False
    if trend_period == None:
        trend_period = 0
        
    assert type(assets) == list, "assets must be a list of strings"
    for i in assets:
        assert type(i) == str, "assets must be a list of strings"
    assert type (trend) == bool, "trend should be either 'True' or 'False'"
    assert type(trend_period) == int and trend_period >= 0, "trend_period must be a nonnegative integer"
    if trend == True:
        assert trend_period != 0, "trend_period must be greater than 0 to calculate price trend"
        
    all_data = pd.DataFrame() #This dataframe will eventually contain all price, trend, and dividend data

    for a in assets:
        
        #Load in price and dividend data. Will only include if both are present
        try:
            price_data = pd.read_csv(a+".csv")
        except FileNotFoundError:
            print(str(a)+" price data not found. Looking for file with name '"+str(a)+".csv'. Unable to include "+str(a))
            continue
        
        dividend_data_found = True
        try:
            dividend_data = pd.read_csv(a+"_dividends.csv")
        except FileNotFoundError:
            print(str(a)+" dividend data not found. Looking for file with name '"+str(a)+"_dividends.csv'. Can only use price data for "+str(a))
            dividend_data_found = False
        
        #Rename dates in dataframes to Year-Month format to handle combining price and dividend data (as dividends
        #have an exact date that may not match the given month date in the price data
        price_data["Date"] = price_data["Date"].map(lambda i: i[:7])
        if dividend_data_found:
            dividend_data["Date"] = dividend_data["Date"].map(lambda i: i[:7])
        
        price_data.rename(columns = {"Close":"Close_"+str(a)}, inplace = True)
        if dividend_data_found:
            dividend_data.rename(columns = {"Dividends":"Dividends_"+str(a)}, inplace = True)
        
        #Add price, then moving average, then dividends to one asset dataframe. Use an outer merge to add dividends in order to keep
        #every date in the price data (which by definition includes all the dividend data)
        asset_data =price_data[["Date","Close_"+str(a)]].copy()
        if trend:
            asset_data["Close_"+str(a)+"_"+str(trend_period)+"-MA"] = asset_data.rolling(trend_period)["Close_"+str(a)].mean()
        if dividend_data_found:
            asset_data = asset_data.merge(dividend_data[["Date","Dividends_"+str(a)]].copy(),
                                          how = "outer", on = ["Date"])

        #If first asset, set all_data to asset_data
        if all_data.empty:
            all_data = asset_data.copy()
        #Otherwise, use an inner join here to only keep dates which all assets have prices
        else:
            all_data = all_data.merge(asset_data.copy(), how = "inner", on = ["Date"])
        #print(all_data[max(trend_period-1,0):])
    
    #This returns the whole dataframe when trend_period = 0 (i.e., no trend following) or
    #removes the first 'trend_period' data points to eliminate the initial 'NaNs' in the moving average
    all_data = all_data[max(trend_period-1,0):]
    
    #This fixes an issue I had with indexes not starting at 0! (drop removes original index as column)
    all_data = all_data.reset_index(drop = True)
    
    return all_data

def historical_return(data, output_name, asset, riskless_asset = None, trend = None, trend_period = None, initial_cash = None):
    
    """
    This function calculates the historical return of an investment portfolio. Currently, it is restricted to buying one asset
    and no additional cash inflows. Implementing a trend-following strategy is possible. Future additions will include owning multiple assets
    and the possibility of using leverage.
    
    Inputs:
        output_name (string): Name for the two output csv files of this function. '_tranactions' and '_history' will be appended
        asset (string): Name of the (one) asset for which the returns will be measured. The function looks for data csv's of the
                        form: '${asset}.csv' and '${asset}_dividends.csv'
        riskless_asset (string): Name of the 'riskless' asset to trade into when usiing a trend-following strategy (usually short-term
                                 treasuries). The function looks for data csv's of the
                                 form: '${asset}.csv' and '${asset}_dividends.csv'
        trend (boolean): Will this data be used for a trend-following strategy (i.e., should a moving average be calculated)
        trend_period (int): The number of data points to include for the trend's moving average
        initial_cash (int or float; optional): The starting value of the portfolio in USD
        
    Outputs:
       returns portfolio_history (Pandas DataFrame): A dataframe with two columns: the date the portfolio's value was calculated and the
                                                     and the portfolio's value
       saves '${output_name}_history.csv': A csv containg the portfolio history data
       sages '${output_name}_transactions.csv': A csv containing a record of every transaction made during the portfolio simulation (right
                                                now restricted to asset purchase). This is for sanity-checks of the simulation.
    """
    
    #These two data frames will store data to be saved
    transactions = pd.DataFrame(columns = ["Date","Transaction","Asset","Price","Units","Value"])
    portfolio_history = pd.DataFrame(columns = ["Date","PortfolioValue"])
    
    #Handle non-required inputs
    if initial_cash == None:
        initial_cash = 10000.0
    if riskless_asset == None:
        riskless_asset = ""
    if trend == None:
        trend = False
    if trend_period == None:
        trend_period = 0
    
    #Make sure inputs are valid
    assert type(data) == pd.DataFrame, "data must be a Pandas DataFrame"
    assert type(output_name) == str, "output_name must be a string"
    assert type(asset) == str, "asset must be a string"
    assert type(riskless_asset) == str, "riskless_asset must be a string"
    assert type(initial_cash) == int or type(initial_cash) == float, "initial_cash must be an int for float"
    assert type (trend) == bool, "trend should be either 'True' or 'False'"
    assert type (trend_period) == int and trend_period >= 0, "trend must be an nonnegative integer"
    if trend == True:
        assert riskless_asset != "", "Riskless asset must be specified if trend is True"
        assert trend_period > 0, "If trend = True, trend_period must be greater than 0"
    assert "Close_"+str(asset) in data.columns, "Price data not available for asset "+str(asset)
    if riskless_asset != "":
        assert "Close_"+str(riskless_asset) in data.columns, "Price data not available for riskless_asset "+str(riskless_asset)

    cash = initial_cash

    shares = {asset:0}
    if trend:
        shares[riskless_asset] = 0

    #Adds the intial portfolio value to the portfolio's history. This means that the 
    #history csv file will have two entries with the first month as the date
    portfolio_history.loc[len(portfolio_history.index)] = [data["Date"][0], initial_cash]
    
    for i, row in data.iterrows():
        
        #If a dividend was paid in a given month, add it to cash value
        for a in shares.keys():
            if "Dividends_"+str(a) in data.columns and pd.notna(row["Dividends_"+str(a)]):
                
                dividend = round(shares[a] * row["Dividends_"+str(a)],2)
                cash += dividend
                
                if dividend > 0:
                    transactions.loc[len(transactions.index)] = [row["Date"],"Dividend",a,row["Dividends_"+str(a)],
                                                                 shares[a],dividend] 
                
        #If trend == False (denoting no trend-following strategy) or the current price is greater than the trend, move portfolio to risk asset
        if trend == False or (trend == True and row["Close_"+str(asset)] > row["Close_"+str(asset)+"_"+str(trend_period)+"-MA"]):
        #if trend == False or (trend == True and row["Close_"+str(asset)] > row["Close_"+str(asset)+"_"+str(trend_period)+"-MA"]):
            #Sell riskless asset
            if trend == True and shares[riskless_asset] > 0:
                shares_to_sell = int(shares[riskless_asset])
                cash += round(shares_to_sell * row["Close_"+str(riskless_asset)],2)
                shares[riskless_asset] = 0
                
                transactions.loc[len(transactions.index)] = [row["Date"],"Sell",riskless_asset,
                                                             row["Close_"+str(riskless_asset)],shares_to_sell,
                                                             round(shares_to_sell * row["Close_"+str(riskless_asset)],2)]
            
            #Buy risk asset
            shares_to_buy = cash//row["Close_"+str(asset)]
            cash -= round(shares_to_buy * row["Close_"+str(asset)],2)
            shares[asset] += int(shares_to_buy)
            
            if shares_to_buy > 0:
                transactions.loc[len(transactions.index)] = [row["Date"],"Buy",asset,
                                                             row["Close_"+str(asset)],int(shares_to_buy),
                                                             round(shares_to_buy * row["Close_"+str(asset)],2)]
                
        #Otherwise, sell all shares and move into riskless asset
        else:
            
            #Sell risk asset
            if trend == True and shares[asset] > 0:
                #Sell risk asset
                shares_to_sell = int(shares[asset])
                cash += round(shares_to_sell * row["Close_"+str(asset)],2)
                shares[asset] = 0
                
                transactions.loc[len(transactions.index)] = [row["Date"],"Sell",asset,
                                                             row["Close_"+str(asset)],shares_to_sell,
                                                             round(shares_to_sell * row["Close_"+str(asset)],2)]

            
            #Buy riskless asset
            shares_to_buy = cash//row["Close_"+str(riskless_asset)]
            cash -= round(shares_to_buy * row["Close_"+str(riskless_asset)],2)
            shares[riskless_asset] += int(shares_to_buy)
            
            if shares_to_buy > 0:
                transactions.loc[len(transactions.index)] = [row["Date"],"Buy",riskless_asset,
                                                             row["Close_"+str(riskless_asset)],int(shares_to_buy),
                                                             round(shares_to_buy * row["Close_"+str(riskless_asset)],2)]
        
        #Add final monthly value to historical dataframe
        current_value = cash
        for a in shares.keys():
            current_value += round(shares[a] * row["Close_"+str(a)],2)
        portfolio_history.loc[len(portfolio_history.index)] = [row["Date"], current_value]
    
    #Save results to csv files
    transactions.to_csv(output_name+"_transactions.csv")
    portfolio_history.to_csv(output_name+"_history.csv")
    
    #Return portfolio's value history
    return portfolio_history

def portfolio_statistics(historical_data, time_unit):
    """
    This function calculates the following statistics for a portfolio given its historical return data:
        1) mean of annual returns
        2) standard deviation of annual returns
        3) max drawdown
        4) sharpe ratio (assuming zero riskfree return)
        5) approximate geometric return (estimated as mean - 0.5 * std.dev^2)
    
    Inputs:
        historical_data (string or Pandas dataframe): the historical returns of a portfolio calculated using
                                                      the 'historical_return' function above. If a string is
                                                      the input, load the saved csv into a Pandas Dataframe.
                                                      If a dataframe is provided, load the output of the function
                                                      directly. (NOTE: only works for string currently)
        time_unit (string): What is the unit of time for each entry in the historical data provided (i.e., daily,
                            monthly, or annual returns). For use in determining how to calculate annual returns
    
    Outputs:
        statistics (dictionary): A dictionary containing all the calculated statistics with strings as keys (the name
                                 of each statistic) and the values as the calculated stat.
    """
    
    #Check inputs
    assert type(historical_data) == str, "historical_data must be a string"
    assert type(time_unit) == str, "time_unit must be a string"
    assert time_unit in ["daily","monthly","annual"], "time_unit must be either 'daily', 'monthly', or 'annual'"
    
    try:
        returns = pd.read_csv(historical_data)
    except FileNotFoundError:
        print("Historical return data not found")
        
    #Confirm that first two historical_data entries share a date (as designed)
    assert returns.loc[0]["Date"] == returns.loc[1]["Date"], "Dates for first two entries not equal"
    
    #store all statistics in dictionary
    statistics = {}
    
    #Calculate annual returns
    annual_returns = []
    
    time_unit_dict = {"daily":365,"monthly":12,"annual":1}
    
    prev_value = returns.loc[0]["PortfolioValue"]
    for i in range(time_unit_dict[time_unit],len(returns.index),time_unit_dict[time_unit]):
        r = (returns.loc[i]["PortfolioValue"] - prev_value) / prev_value
        annual_returns.append(r)
        prev_value = returns.loc[i]["PortfolioValue"]
    #print(annual_returns)
    statistics["mean_annual_return"] = np.mean(annual_returns)
    statistics["standard_deviation_annual_return"] = np.std(annual_returns)
    statistics["approx_geomtric_return"] = np.mean(annual_returns) - 0.5 * np.std(annual_returns) * np.std(annual_returns)
    
    #Note: This is the sharpe ratio with the risk-free return set to 0
    statistics["sharpe_ratio"] = np.mean(annual_returns) / np.std(annual_returns) 
    
    #Calculate max drawdown (i.e., lowest percentage decrease from an all-time high)
    max_value = returns.loc[0]["PortfolioValue"]
    max_drawdown = 0.0
    
    for i in range(1,len(returns.index),1):
        current_value = returns.loc[i]["PortfolioValue"]
        if current_value >= max_value:
            max_value = current_value
        else:
            current_drawdown = (max_value - current_value) / max_value
            max_drawdown = max(max_drawdown,current_drawdown)
    
    statistics["max_drawdown"] = max_drawdown
        
    return statistics