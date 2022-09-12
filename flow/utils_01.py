import altair as alt
from collections.abc import Mapping
import datetime
import pandas as pd
import streamlit as st


__all__ = ["query_information", "load_data", "date_df", "update_player_name"]


query_information = {
    "NFL All Day: Wallet Creation": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/666a2a57-105a-4a6e-a54d-8a7087f56411/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/666a2a57-105a-4a6e-a54d-8a7087f56411",
        "short_name": "user_creation",
    },
    "NFL All Day: Daily Sales": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/2265fd42-bcd2-49e3-b464-81258cc3ef96/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/2265fd42-bcd2-49e3-b464-81258cc3ef96",
        "short_name": "daily_sales",
    },
    "NFL All Day: User Purchases": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/cf0f3961-51dc-4eaa-97ea-08882eb762ee/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/cf0f3961-51dc-4eaa-97ea-08882eb762ee",
        "short_name": "user_tx",
    },
    "NFL All Day: Purchases by Player": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/7c40aa00-8870-485c-86f9-06adc6552b3a/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/7c40aa00-8870-485c-86f9-06adc6552b3a",
        "short_name": "player_tx",
    },
    "NFL All Day: Popular NFT Collections, by Transaction Count": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/1162b91a-4a0f-4dde-93eb-0b5f53ec3c22/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/1162b91a-4a0f-4dde-93eb-0b5f53ec3c22",
        "short_name": "nft_tx",
    },
    "NFL All Day: Popular NFT Collections, by Average Price": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/a56db5ee-276b-4f71-9ca9-3528a0d9c5c5/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/a56db5ee-276b-4f71-9ca9-3528a0d9c5c5",
        "short_name": "nft_avg",
    },
    "NFL All Day: Popular NFT Collections, by Maximum Sale Price": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/61de8c77-8d02-4a12-8b48-e7af79c4ac6b/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/61de8c77-8d02-4a12-8b48-e7af79c4ac6b",
        "short_name": "nft_max",
    },
    "NFL All Day: Popular NFT Collections, by Total Sale Price": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/badf76b4-8ff8-46dc-8ead-93a3fc5d809b/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/badf76b4-8ff8-46dc-8ead-93a3fc5d809b",
        "short_name": "nft_total",
    },
}

date_df = pd.DataFrame(
    {
        "Date": [
            "2022-08-05T00:00:00Z",
            "2022-08-12T00:00:00Z",
            "2022-08-19T00:00:00Z",
            "2022-08-26T00:00:00Z",
            "2022-09-09T00:00:00Z",
        ],
        "color": ["red", "gray", "gray", "gray", "blue"],
        "Description": [
            "Start of 2022 Season: Hall of Fame Weekend",
            "First Preseason Weekend",
            "Second Preseason Weekend",
            "Third Preseason Weekend",
            "Week 1",
        ],
    }
)

date_df["DATE"] = pd.to_datetime(date_df.Date)


@st.cache(ttl=(3600 * 12), allow_output_mutation=True)
def load_data(
    query_information: Mapping[str, Mapping[str, str]] = query_information
) -> pd.DataFrame:
    """Load data from Query information

    Parameters
    ----------
    query_information : Dict, optional
        Information containing URLs to data, see default for how to set this up, by default query_information

    Returns
    -------
    pd.DataFrame
        Dataframe of multi-blockchain data
    """

    dfs = {}
    combined = []

    for v in query_information.values():
        df = pd.read_json(v["api"])
        if v["short_name"].startswith("nft"):
            name = v["short_name"].split("_")[-1]
            df["type"] = name
            combined.append(df)
        else:
            dfs[v["short_name"]] = df
    dfs["combined_nft"] = pd.concat(combined).reset_index()

    return dfs


def update_player_name(row):
    if row.PLAYER == "N/A":
        row.PLAYER = row.TEAM
    return row
