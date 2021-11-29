#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""test_functions.py: Contains test functions"""

import invest_functions as inv

def test_historical_return():
	
	asset_data = inv.organize_data(["VT","VGSH","GLD"], trend = True, trend_period = 10)
	
	vt = inv.historical_return(data = asset_data, output_name = "VT", asset = "VT",initial_cash = 30000.0)
	
	#This won't work until I iimplement the ability to input DataFrames into 'portfolio_statistics'
	if dict(inv.portfolio_statistics(vt,"monthly"))!= {'mean_annual_return': 0.10716119250637639,
													   'standard_deviation_annual_return': 0.07453545946713795,
													   'approx_geomtric_return': 0.1043834251473877,
													   'sharpe_ratio': 1.4377209622437874,
													   'max_drawdown': 0.22177604931461703}:
		print(inv.portfolio_statistics(vt,"monthly"))
		return False
	
	return True

def main():
	
	historical_return_test  =  test_historical_return()
	print("Historical_return test: "+str(historical_return_test))
	