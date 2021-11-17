import pandas as pd

def historical_return(output_name, asset, initial_cash = None):
    
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
            
            dividend = round(shares_vt * focused_data["Dividends"][i],2)
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
        current_value = cash + round(shares_vt*focused_data.iloc[i]["Close"],2)
        portfolio_history.loc[len(portfolio_history.index)] = [focused_data["Date"][i], current_value]
    
    #Save results to csv files
    transactions.to_csv(output_name+"_transactions.csv")
    portfolio_history.to_csv(output_name+"_history.csv")
	
	#Return portfolio's value history
    print("Final assets: "+str(cash + round(shares_vt*focused_data.iloc[-1]["Close"],2)))
	return portfolio_history