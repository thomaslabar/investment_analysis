#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""invest_functions.py: Contains functions for analyzing investment portfolios based on historical data"""

import pandas as pd
import numpy as np

def historical_return(output_name, asset, initial_cash = None):
    
    """
    This function calculates the historical return of an investment portfolio. Currently, it is restricted to buying one asset
    and no additional cash inflows. Future additions will include owning multiple assets, implementation of trend-following
    strategies, and the possibility of using leverage.
    
    Inputs:
        output_name (string): Name for the two output csv files of this function. '_tranactions' and '_history' will be appended
        asset (string): Name of the (one) asset for which the returns will be measured. The function looks for data csv's of the
                        form: '${asset}.csv' and '${asset}_dividends.csv'
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
    
    #Make sure inputs are of the correct type
    assert type(output_name) == str, "output_name must be a string"
    assert type(asset) == str, "asset must be a string"
    assert type(initial_cash) == int or type(initial_cash) == float, "initial_cash must be an int for float"
    
    #Load asset prices/dividends from csv's into DataFrames
    try:
        asset_price_data = pd.read_csv(asset+".csv")
    except FileNotFoundError:
        print("Asset price data not found. Looking for file with name '${asset}.csv'. Unable to calculate return")
    
    try:
        asset_dividend_data = pd.read_csv(asset+"_dividends.csv")
    except FileNotFoundError:
        print("Asset dividend data not found. Looking for file with name '${asset}_dividends.csv' Only calculated price returns")
        
    #Rename dates in dataframes to Year-Month format to handle combining price and dividend data (as dividends
    #have an exact date that may not match the given month date in the price data
    asset_price_data["Date"] = asset_price_data["Date"].map(lambda a: a[:7])
    asset_dividend_data["Date"] = asset_dividend_data["Date"].map(lambda a: a[:7])
    
    #Join price and dividend data together
    combined_asset_data = asset_price_data[["Date","Close"]].copy()
    combined_asset_data = combined_asset_data.merge(asset_dividend_data[["Date","Dividends"]].copy(), 
                                                    how = "left", on = ["Date"])
    
    focused_data = combined_asset_data.copy()
    cash = initial_cash
    shares = 0

    for i, row in focused_data.iterrows():
        
        #This IF statement adds the intial portfolio value to the portfolio's history. This means that the 
        #history csv file will have two entries with the first month as the date
        if i == 0:
            portfolio_history.loc[len(portfolio_history.index)] = [focused_data["Date"][i], initial_cash]
        
        
        #If a dividend was paid in a given month, add it to cash value
        if pd.notna(focused_data["Dividends"][i]):
            
            dividend = round(shares * focused_data["Dividends"][i],2)
            cash += dividend

            transactions.loc[len(transactions.index)] = [focused_data["Date"][i],"Dividend","Cash",dividend,
                                                         1,dividend] 
        
        #This if statement currently does nothing, but will be relevant once trend following
        #is implemented. 
        if True:
            #If condition is met, buy shares
            shares_to_buy = cash//focused_data["Close"][i]
            cash -= round(shares_to_buy * focused_data["Close"][i],2)
            shares += int(shares_to_buy)
            
            if shares_to_buy > 0:
                transactions.loc[len(transactions.index)] = [focused_data["Date"][i],"Buy",asset,
                                                             focused_data["Close"][i],int(shares_to_buy),
                                                             round(shares_to_buy * focused_data["Close"][i],2)] 

        else:
            #Otherwise, sell all shares
            cash += round(shares* focused_data["Close"][i],2)
            shares = 0
            
            transactions.loc[len(transactions.index)] = [focused_data["Date"][i],"Sell",asset,
                                                         focused_data["Close"][i],shares,
                                                         round(shares * focused_data["Close"][i],2)] 
        
        #Add final monthly value to historical dataframe
        current_value = cash + round(shares*focused_data.iloc[i]["Close"],2)
        portfolio_history.loc[len(portfolio_history.index)] = [focused_data["Date"][i], current_value]
    
    #Save results to csv files
    transactions.to_csv(output_name+"_transactions.csv")
    portfolio_history.to_csv(output_name+"_history.csv")
    
    #print("Final assets: "+str(cash + round(shares*focused_data.iloc[-1]["Close"],2)))
    #Return portfolio's value history
    return portfolio_history

def portfolio_statistics(historical_data, time_unit):
    """
    This function calculates the following statistics for a portfolio given its historical return data:
        1) mean of annual returns
        2) standard deviation of annual returns
        3) max drawdown
    
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

    statistics["mean_annual_return"] = np.mean(annual_returns)
    statistics["standard_deviation_annual_return"] = np.std(annual_returns)
    
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