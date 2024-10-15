# This Python script simulates a simple trading strategy on the stock ticker TQQQ over a specific time period (from 2023-09-19 to 2024-10-15) using historical data from Yahoo Finance (yfinance). 
# It incorporates technical indicators such as moving averages and the Relative Strength Index (RSI) to make decisions about when to enter and exit trades. 
# Here's a breakdown of what the code does:
# 
# 1. Imports and Setup
# 
# Imports libraries: 
# yfinance: For downloading stock data.
# pandas: To work with data in tabular format.
# pandas_ta: For technical analysis (TA) indicators like moving averages and RSI.
# random: To simulate randomness for slippage in trade prices.
# datetime: To work with dates and times.
# dataclasses: For a simple way to define constants using the Dow class (days of the week).
# Dataclass Dow: This class assigns numerical values to days of the week (e.g., Monday = 0, Tuesday = 1).
# 
# 2. Download Historical Data
# The script downloads historical stock data for TQQQ from Yahoo Finance between the start and end dates.
# 
# 3. Define Trading Parameters
# open_limit_offset: Offset applied to the open price when simulating trades.
# take_profit_percentage: Initial take profit percentage for a trade (e.g., 7% above the entry price).
# take_profit_increase: An additional percentage to increase the take profit when a condition is met (e.g., 1% increase after hitting 3.5% profit).
# Slippage: Simulates price slippage during trade entry/exit.
# 
# 4. RSI and Moving Averages
# use_rsi_low, use_rsi_hi: Flags to enable or disable RSI-based conditions.
# slope_lookback: Number of days used to determine if the RSI slope is positive or negative.
# RSI, SMA, HMA Periods: The periods used for calculating the RSI (13), Simple Moving Average (SMA, 200), and Hull Moving Average (HMA, 19).
# 
# 5. Allowed Trading Days
# Trades are only allowed on specified days of the week: Monday, Wednesday, Thursday, and Friday (as defined by allowed_days).
# 
# 6. Calculate Indicators
# Calculates technical indicators:
# SMA: Simple Moving Average.
# HMA: Hull Moving Average.
# RSI: Relative Strength Index.
# UpSlope: A flag indicating whether the RSI is increasing compared to its previous value.
# 
# 7. Trade Simulation
# The script groups the historical data by weeks and simulates trades week by week.
# 
# Entry conditions: A trade is initiated when several conditions are met:
# Price condition (e.g., price hitting a specific limit based on the open_limit_offset).
# Technical indicators (RSI, SMA, HMA) must align with the specified conditions.
# Trade must occur on an allowed day (Monday, Wednesday, Thursday, or Friday).
# 
# Exit conditions:
# If the price reaches a profit target (initially set at 7%, or later increased if certain conditions are met).
# If the trade is still active at the end of the week (Friday), it closes at the weekly close price.
# 
# 8. Trade Logging
# trades list: Stores details about each trade made during the simulation, such as entry/exit date, prices, RSI values, and profit percentages.
# 
# 9. Post-Simulation Analysis
# After the simulation, the trades are saved to a CSV file (trades.log).
# The script computes:
# Maximum and minimum trade profits.
# Total trades made.
# Win rate (percentage of profitable trades).
# Average profit per trade.
# Average number of days a trade was active.
# Profit per week based on the total profit over the number of weeks in the dataset.
# 
# 10. Output
# Displays a summary of the trade results, including:
# Total number of trades.
# Number of winning and losing trades.
# Win rate and average profit per trade.
# Maximum and minimum profit, along with the dates these occurred.
# Number of days each trade was active and the total number of weeks analyzed.
# 
# Summary
# This code simulates a technical trading strategy using historical data. 
# It tests trade entry and exit conditions based on price, technical indicators (RSI, SMA, HMA), and the day of the week. 
# After simulating the trades, it analyzes the results, calculating the win rate, average profit, and overall performance.

# RSI length = 13
# Use rsi_low 51.0, use rsi_high 73.0
# Use rsi slope, with lookback = 1

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import random
import datetime as dt
from dataclasses import dataclass

@dataclass
class Dow():
    MON: int=0
    TUE: int=1
    WED: int=2
    THU: int=3
    FRI: int=4
    SAT: int=5
    SUN: int=6

# Define the ticker and download historical data
ticker = 'TQQQ'
data = yf.download(ticker, start='2024-01-01', end='2024-10-15')

open_limit_offset = 0.01
take_profit_percentage = 0.07
take_profit_increase = 0.01

open_max_slippage = 0.01
close_max_slippage = 0.01  

rsi_low = 51.0
rsi_high = 73.0

use_sma = False
use_hma = False
use_rsi_low = True
use_rsi_hi = True
use_rsi_slope = True

slope_lookback = 1

rsi_period = 13
sma_period = 200
hma_period = 19

allowed_days = [Dow.MON, Dow.WED, Dow.THU, Dow.FRI] # 0-Monday, 1-Tuesday, 2-Wednesday, 3-Thursday, 4-Friday 

# Calculate moving averages and rsi 
data['SMA'] = ta.sma(data['Close'], length=sma_period)
data['HMA'] = ta.hma(data['Close'], length=hma_period)
data['RSI'] = ta.rsi(data['Close'], length=rsi_period)
data['Previous_RSI'] = data['RSI'].shift(slope_lookback)
data['UpSlope'] = data['RSI'] > data['Previous_RSI']

# Ensure the data is sorted by date
data.sort_index(inplace=True)

# Initialize a list to store trades
trades = []

# Initialize variables to track the dates of max and min exit profits
max_exit_profit_date = None
min_exit_profit_date = None

# Group data by weeks and iterate over each week
data['Week Start'] = data.index.to_period('W').start_time
grouped = data.groupby('Week Start')

# print(data)

# Calculate total number of weeks in the dataset
total_weeks = len(grouped)

for week_start, weekly_data in grouped:
        
    # Initialize variables to store trade information
    trade_entry_date = None
    trade_exit_date = None
    trade_entry_price = None
    trade_exit_price = None
    trade_entry_rsi = None
    increased_take_profit = False  # Flag to track if the take profit limit was increased
    trade_made = False  # Flag to track if a trade was made this week
        
    # Simulate the trading week
    for j, row in weekly_data.iterrows():

        open_price = row["Open"]
        slippage = random.uniform(-open_max_slippage, open_max_slippage)
        limit_price = open_price + open_limit_offset + slippage
        take_profit_price = limit_price * (1 + take_profit_percentage)

        if trade_entry_date is None:
            # Conditions to check for trade entry
            price_condition_met = (
                (open_limit_offset > 0 and row['High'] >= limit_price) or
                (open_limit_offset <= 0 and row['Low'] <= limit_price)
            )            
            indicators_condition_met = (
                (not use_sma or row['Open'] > row['SMA']) and
                (not use_hma or row['Open'] > row['HMA']) and                                
                (not use_rsi_slope or (row['UpSlope'])) and
                (not use_rsi_low or (row['RSI'] >= rsi_low)) and
                (not use_rsi_hi or (row['RSI'] <= rsi_high))
            )
            days_condition_met = (
                dt.datetime.weekday(j) in allowed_days
            )
            
            # Check all conditions
            if price_condition_met and indicators_condition_met and days_condition_met:
                trade_entry_date = j
                trade_entry_price = limit_price
                trade_entry_rsi = row['RSI']
                trade_made = True  # Mark that a trade was made
                        
        # If in a trade, check if the price hits 3.5% above the entry price
        if trade_entry_date is not None and not increased_take_profit:
            if row['High'] >= trade_entry_price * (1 + (take_profit_percentage / 2.0)):
                # Increase take profit target to 8% if 3.5% threshold is hit
                take_profit_price = trade_entry_price * (1 + take_profit_percentage + take_profit_increase)
                increased_take_profit = True
                
        # If in a trade, check if take profit is hit
        if trade_entry_date is not None:
            if row['High'] >= take_profit_price:
                trade_exit_date = j
                trade_exit_price = take_profit_price
                break
    
    # If still in a trade by Friday, exit at the close price with simulated slippage
    if trade_entry_date is not None and trade_exit_date is None:
        trade_exit_date = weekly_data.index[-1]
        # Simulate slippage by adding a random value between -5 cents and +5 cents
        slippage = random.uniform(-close_max_slippage, close_max_slippage)
        trade_exit_price = weekly_data.iloc[-1]['Close'] + slippage
    
    # If a trade was made, increment the weeks_with_trade counter
    if trade_made:
        days_in_trade = (trade_exit_date - trade_entry_date).days
        trade_profit = (trade_exit_price / trade_entry_price - 1) * 100
        trades.append({
            'Entry Date': trade_entry_date,
            'Exit Date': trade_exit_date,
            'Entry Price': trade_entry_price,
            'Exit Price': trade_exit_price,
            'Profit (%)': trade_profit,
            'Days in Trade': days_in_trade,
            'Entry Day': trade_entry_date.strftime('%A'),  
            'Exit Day': trade_exit_date.strftime('%A'),
            'Entry RSI': trade_entry_rsi,
            'TP Boost': increased_take_profit
        })
    
# Convert trades to a DataFrame for analysis
trades_df = pd.DataFrame(trades)
trades_df.to_csv('./trades.log')

# Calculate maximum and minimum profits at the exit of trades
max_exit_profit = trades_df['Profit (%)'].max() if not trades_df.empty else None
min_exit_profit = trades_df['Profit (%)'].min() if not trades_df.empty else None

# Find the dates when the maximum and minimum exit profits occurred
if not trades_df.empty:
    max_exit_profit_date = trades_df.loc[trades_df['Profit (%)'].idxmax(), 'Exit Date']
    min_exit_profit_date = trades_df.loc[trades_df['Profit (%)'].idxmin(), 'Exit Date']

# Display the trades
print(trades_df)

# Calculate overall metrics
total_trades = len(trades_df)
winning_trades = len(trades_df[trades_df['Profit (%)'] > 0])
losing_trades = total_trades - winning_trades
win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
average_profit = trades_df['Profit (%)'].mean() if total_trades > 0 else 0
profit_per_week = trades_df['Profit (%)'].sum()/total_weeks if total_trades > 0 else 0
average_days_in_trade = trades_df['Days in Trade'].mean() if total_trades > 0 else 0

print(f'Using SMA: {use_sma}')
print(f'Using HMA: {use_hma}')
print(f'Using RSI Low: {use_rsi_low}, {rsi_low:1.1f}')
print(f'Using RSI High: {use_rsi_hi}, {rsi_high:1.1f}')
print(f'Total Trades: {total_trades}')
print(f'Winning Trades: {winning_trades}')
print(f'Losing Trades: {losing_trades}')
print(f'Win Rate: {win_rate:.2f}%')
print(f'Average Profit per Trade: {average_profit:.2f}%')
print(f'Profit Per Week: {profit_per_week:.2f}%')
print(f'Maximum Exit Profit: {max_exit_profit:.2f}% on {max_exit_profit_date}')
print(f'Minimum Exit Profit: {min_exit_profit:.2f}% on {min_exit_profit_date}')
print(f'Average Number of Days in Trade: {average_days_in_trade:.2f} days')
print(f'Total Number of Weeks in the Time Period: {total_weeks}')


