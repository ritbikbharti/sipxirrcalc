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
    
    # Convert Date column to datetime format
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%y", errors='coerce')
    df = df.dropna(subset=["Date"])  # Remove rows with invalid dates
    df = df.sort_values(by="Date")
    
    # Function to calculate XIRR
    def xirr(cashflows, dates, guess=0.1):
        def npv(rate):
            return sum([cf / (1 + rate) ** ((d - dates[0]).days / 365.0) for cf, d in zip(cashflows, dates)])
        return newton(npv, guess) * 100
    
    start_date = pd.to_datetime(st.date_input("Select SIP Start Date", min_value=df["Date"].min(), max_value=df["Date"].max()))
    end_date = pd.to_datetime(st.date_input("Select SIP End Date", min_value=df["Date"].min(), max_value=df["Date"].max()))
    
    if st.button("Calculate SIP XIRR"):
        if start_date >= end_date:
            st.error("End date must be later than start date!")
        else:
            # Filter data
            df_filtered = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
            df_filtered["Year-Month"] = df_filtered["Date"].dt.to_period("M")
            sip_dates = df_filtered.groupby("Year-Month").first().reset_index()
            
            # SIP Calculation
            sip_amount = 10000
            sip_dates["Units Bought"] = sip_amount / sip_dates["Closing Price"]
            total_units = sip_dates["Units Bought"].sum()
            final_nav = df_filtered[df_filtered["Date"] <= end_date].iloc[-1]["Closing Price"]
            final_value = total_units * final_nav
            
            # Prepare cash flows
            cash_flows = [-sip_amount] * len(sip_dates) + [final_value]
            dates = sip_dates["Date"].tolist() + [end_date]
            
            # Calculate XIRR
            sip_xirr = xirr(cash_flows, dates)
            
            # Display result
            st.success(f"SIP XIRR from {start_date.date()} to {end_date.date()}: {sip_xirr:.2f}%")
            
            # Generate Charts
            fig, ax = plt.subplots(1, 2, figsize=(12, 5))
            ax[0].plot(df_filtered["Date"], df_filtered["Closing Price"], label="Index Price", color='b')
            ax[0].scatter(sip_dates["Date"], sip_dates["Closing Price"], color='red', label="SIP Investments")
            ax[0].set_xlabel("Date")
            ax[0].set_ylabel("Index Price")
            ax[0].set_title("Index Performance & SIP Investments")
            ax[0].legend()
            
            investment_values = [sip_amount * (i + 1) for i in range(len(sip_dates))]
            ax[1].bar([str(d.date()) for d in sip_dates["Date"]], investment_values, color='g', label="Invested Amount")
            ax[1].axhline(final_value, color='r', linestyle='--', label="Final Portfolio Value")
            ax[1].set_xticklabels([str(d.date()) for d in sip_dates["Date"]], rotation=90)
            ax[1].set_xlabel("Date")
            ax[1].set_ylabel("Investment Value")
            ax[1].set_title("SIP Investment Growth")
            ax[1].legend()
            
            st.pyplot(fig)
