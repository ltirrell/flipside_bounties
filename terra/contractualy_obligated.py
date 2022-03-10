import altair as alt
import pandas as pd
import streamlit as st

st.title("Contractually Obligated")
st.caption(
    """
Based on your analysis for Question 161, 
- provide the top 20 smart contract addresses that users interact with, or
- the top 2 smart contract addresses per each of the protocols that you previously analyzed

Grand prize-winning submissions will assess both!"""
)


# @st.cache(ttl=(3600 * 6))
def load_data():
    q = "6ad7225c-594b-4b4e-bc5b-7c25124ffa11"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)

    return df


df = load_data()

st.header("Overview")