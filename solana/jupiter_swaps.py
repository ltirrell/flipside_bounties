import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import streamlit as st


@st.cache
def load_data():
    q = "8d4271e8-3ec6-43f2-9235-1b06737c46b8"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)

    # create rolling averages and TPS averages
    for i in ["TX_COUNT", "SUCCESS", "FAILS"]:
        df[f"{i}_per_second"] = df[i] / 60

    for i in [
        "TX_COUNT_per_second",
        "SUCCESS_per_second",
        "SUCCESS_RATE",
        "FAILS_per_second",
    ]:
        df[f"{i}_5_min_avg"] = df[i].rolling(5).mean()
        df[f"{i}_hourly_avg"] = df[i].rolling(60).mean()
        df[f"{i}_6_hr_avg"] = df[i].rolling(60 * 6).mean()
        df[f"{i}_daily_avg"] = df[i].rolling(60 * 24).mean()
        df[f"{i}_weekly_avg"] = df[i].rolling(60 * 24 * 7).mean()
    return df


df = load_data()

st.title("Most Popular Jupiter Swaps")
st.caption(
    """
Solana Q27: Jupiter is the best swap aggregator on Solana, meaning that it optimizes the best token swap rate across all decentralized exchanges for users.
"""
)