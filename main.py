import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime
from scipy.optimize import newton

# Streamlit UI
st.title("📈 SIP XIRR Calculator for Index Funds")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Convert the second column (Date) to datetime format
    date_column = df.columns[1]  # Assuming the second column is the date column
    
    # Ensure the date column is treated correctly, handling Excel text format issues
    df[date_column] = df[date_column].astype(str).str.strip()  # Convert to string and remove extra spaces
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce', dayfirst=True)  # Convert to datetime
    
    df = df.dropna(subset=[date_column])  # Remove rows with invalid dates
    df = df.sort_values(by=date_column).reset_index(drop=True)  # Reset index after sorting
    
    # Ensure 'Close' column exists
    if "Close" not in df.columns:
        st.error("Uploaded CSV must contain a 'Close' column for closing prices.")
    elif df.empty or df[date_column].isna().all():
        st.error("No valid dates found in the uploaded file.")
    else:
        min_date = df[date_column].min()
        max_date = df[date_column].max()
        
        # Set default dates to prevent NaT errors
        if pd.isna(min_date) or pd.isna(max_date):
            st.error("Error: Date column contains invalid values. Please check the file.")
        else:
            start_date = pd.to_datetime(st.date_input("Select SIP Start Date", min_value=min_date, max_value=max_date, value=min_date))
            end_date = pd.to_datetime(st.date_input("Select SIP End Date", min_value=min_date, max_value=max_date, value=max_date))
            
            # Function to calculate XIRR
            def xirr(cashflows, dates, guess=0.1):
                def npv(rate):
                    return sum([cf / (1 + rate) ** ((d - dates[0]).days / 365.0) for cf, d in zip(cashflows, dates)])
                return newton(npv, guess) * 100
            
            if st.button("Calculate SIP XIRR"):
                if start_date >= end_date:
                    st.error("End date must be later than start date!")
                else:
                    # Filter data
                    df_filtered = df[(df[date_column] >= start_date) & (df[date_column] <= end_date)]
                    df_filtered["Year-Month"] = df_filtered[date_column].dt.to_period("M")
                    sip_dates = df_filtered.groupby("Year-Month").first().reset_index()
                    
                    # SIP Calculation
                    sip_amount = 10000
                    sip_dates["Units Bought"] = sip_amount / sip_dates["Close"]  # Using "Close" column for price
                    total_units = sip_dates["Units Bought"].sum()
                    final_nav = df_filtered[df_filtered[date_column] <= end_date].iloc[-1]["Close"]  # Using "Close" column for price
                    final_value = total_units * final_nav
                    
                    # Prepare cash flows
                    cash_flows = [-sip_amount] * len(sip_dates) + [final_value]
                    dates = sip_dates[date_column].tolist() + [end_date]
                    
                    # Ensure no NaT values in dates
                    dates = [d for d in dates if pd.notna(d)]
                    
                    # Calculate XIRR
                    sip_xirr = xirr(cash_flows, dates)
                    
                    # Display result
                    st.success(f"SIP XIRR from {start_date.date()} to {end_date.date()}: {sip_xirr:.2f}%")
                    
                    # Generate Charts
                    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
                    ax[0].plot(df_filtered[date_column], df_filtered["Close"], label="Index Price", color='b')  # Using "Close" column for price
                    ax[0].scatter(sip_dates[date_column], sip_dates["Close"], color='red', label="SIP Investments")
                    ax[0].set_xlabel("Date")
                    ax[0].set_ylabel("Index Price")
                    ax[0].set_title("Index Performance & SIP Investments")
                    ax[0].legend()
                    
                    investment_values = [sip_amount * (i + 1) for i in range(len(sip_dates))]
                    ax[1].bar([str(d.date()) for d in sip_dates[date_column]], investment_values, color='g', label="Invested Amount")
                    ax[1].axhline(final_value, color='r', linestyle='--', label="Final Portfolio Value")
                    ax[1].set_xticklabels([str(d.date()) for d in sip_dates[date_column]], rotation=90)
                    ax[1].set_xlabel("Date")
                    ax[1].set_ylabel("Investment Value")
                    ax[1].set_title("SIP Investment Growth")
                    ax[1].legend()
                    
                    st.pyplot(fig)
