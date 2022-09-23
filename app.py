import pandas as pd
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="🏈 NFL [Big Play] ALL DAY 🏈", page_icon="🏈", layout="wide"
)

st.title("🏈 NFL [Big Play] ALL DAY 🏈")
st.caption(
    """
Celebrating the start of the NFL season by looking at big plays!
"""
)

st.header("Plays or Players?")
st.write(
f"""
Is there a type of play that is more valuable, or do valuable players sell at higher prices regardless of play type?
"""
)

main_df = pd.read_csv("data/current_allday_data.csv.gz")

st.write(main_df.head())

for x in Path('data').glob("*.csv"):
    st.header(x.name)
    df = pd.read_csv(x)
    df
