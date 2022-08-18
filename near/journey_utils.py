from collections.abc import Mapping

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# from shroomdk import ShroomDK

# fs_key = st.secrets["flipside"]["api_key"]
# fig_key = st.secrets["figment"]["api_key"]
# fig_url = f"https://near--indexer.datahub.figment.io/apikey/{fig_key}"
# sdk = ShroomDK(fs_key)

__all__ = [
    # Variables/info/schema
    "query_information",
    # Utilities
    "gini",
    # Data
    "load_data",
    # Charting
    "alt_user_chart",
    "alt_ordered_bar",
    "alt_date_area",
    "alt_ordered_bar_receiver",
    "alt_ordered_bar_sender",
]


# Variables/info/schema
query_information = {
    "NEAR User Summary": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/ef747a3f-26e0-4d37-a875-103360fa12e1/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/ef747a3f-26e0-4d37-a875-103360fa12e1",
        "short_name": "near_user",
    },
    "NEAR User: First Method": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/172c237c-faec-4aa8-ad93-5a97a2b2b6d0/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/172c237c-faec-4aa8-ad93-5a97a2b2b6d0",
        "short_name": "first_method",
    },
    "Rainbow Bridge": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/439ecbf1-dc9e-4fe7-912a-70695119c7d1/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/439ecbf1-dc9e-4fe7-912a-70695119c7d1",
        "short_name": "rainbow",
    },
}


# Utilities
def gini(array: np.array) -> float:
    """Calculate the Gini coefficient of a numpy array.

    From https://github.com/oliviaguest/gini

    based on bottom eq:
    http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    from:
    http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    """
    # All values are treated equally, arrays must be 1d:
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    # Values cannot be 0:
    array += 0.0000001
    # Values must be sorted:
    array = np.sort(array)
    # Index per array element:
    index = np.arange(1, array.shape[0] + 1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))


# Data
@st.cache(ttl=(3600 * 12), allow_output_mutation=True)
def load_data(
    query_information: Mapping[str, Mapping[str, str]] = query_information
) -> Mapping[str, pd.DataFrame]:
    """Load data from Query information

    Parameters
    ----------
    query_information : Dict, optional
        Information containing URLs to data, see default for how to set this up, by default query_information

    Returns
    -------
    Dict
        Dict of dataframes
    """

    dfs = {}

    for v in query_information.values():
        df = pd.read_json(v["api"], dtype=str)
        dfs[v["short_name"]] = df

    return dfs


# Charting
def alt_user_chart(df):
    base = alt.Chart(df, title="NEAR New Users").encode(
        x=alt.X("CREATION_DATE:T", axis=alt.Axis(title=""))
    )

    area = base.mark_area(color="#403b3b").encode(
        y=alt.Y(
            "NEW_USERS:Q",
            title="New Users",
        ),
        tooltip=[
            alt.Tooltip("yearmonthdate(CREATION_DATE):T", title="Creation Date"),
            alt.Tooltip("NEW_USERS:Q", title="New Users", format=","),
            alt.Tooltip("CUMULATIVE_USERS:Q", title="Cumulative New Users", format=","),
            alt.Tooltip(
                "CUMULATIVE_AVERAGE_DAILY_NEW_USERS:Q",
                title="Cumulative Average Daily New Users",
                format=",.1f",
            ),
        ],
    )

    cumavg = base.mark_line(color="#e33048", interpolate="monotone").encode(
        y=alt.Y(
            "CUMULATIVE_AVERAGE_DAILY_NEW_USERS:Q",
            title="Cumulative Average Daily New Users",
        ),
        tooltip=[
            alt.Tooltip("yearmonthdate(CREATION_DATE):T", title="Creation Date"),
            alt.Tooltip("NEW_USERS:Q", title="New Users", format=","),
            alt.Tooltip("CUMULATIVE_USERS:Q", title="Cumulative New Users", format=","),
            alt.Tooltip(
                "CUMULATIVE_AVERAGE_DAILY_NEW_USERS:Q",
                title="Cumulative Average Daily New Users",
                format=",.1f",
            ),
        ],
    )

    cumsum = base.mark_line(color="#0b1da1", strokeDash=[12, 3]).encode(
        y=alt.Y(
            "CUMULATIVE_USERS:Q",
            title="Cumulative New Users",
            axis=alt.Axis(titleColor="#0b1da1"),
        ),
        tooltip=[
            alt.Tooltip("yearmonthdate(CREATION_DATE):T", title="Creation Date"),
            alt.Tooltip("NEW_USERS:Q", title="New Users", format=","),
            alt.Tooltip("CUMULATIVE_USERS:Q", title="Cumulative New Users", format=","),
            alt.Tooltip(
                "CUMULATIVE_AVERAGE_DAILY_NEW_USERS:Q",
                title="Cumulative Average Daily New Users",
                format=",.1f",
            ),
        ],
    )

    users = alt.layer(area, cumavg)
    chart = (
        alt.layer(users, cumsum)
        .resolve_scale(y="independent")
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_ordered_bar(df, tx_type):
    df = df[df.TX_TYPE == tx_type]
    df = df.sort_values(by="USER_COUNT", ascending=False).reset_index(drop=True)
    df = df.iloc[:30]

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("FIRST_METHOD_NAME", sort="-y", title=None),
            y=alt.Y("USER_COUNT:Q", title="Users"),
            color=alt.Color(
                "FIRST_METHOD_NAME",
                title="Method Name",
                sort=alt.EncodingSortField(
                    "USER_COUNT:Q", op="max", order="descending"
                ),
            ),
            tooltip=[
                alt.Tooltip("FIRST_METHOD_NAME", title="Method name"),
                alt.Tooltip("USER_COUNT:Q", title="Users", format=","),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_date_area(df, metric):
    chart = (
        alt.Chart(df)
        .mark_area(color="#054480")
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y(f"{metric}:Q", title=f"{metric.replace('_', ' ').title()}"),
            tooltip=[
                alt.Tooltip(
                    "Date:T",
                ),
                alt.Tooltip(f"{metric}:Q", title=f"{metric.replace('_', ' ').title()}"),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_ordered_bar_receiver(df, metric, ordering):
    df = df.dropna()
    df = df.sort_values(by=metric, ascending=ordering).reset_index(drop=True)
    df = df.iloc[:30]

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("GROUPER", sort="-y", title=None),
            y=alt.Y(metric, title=f"{metric.replace('_', ' ').title()}"),
            color=alt.Color(
                "GROUPER",
                title="Near Address",
                sort=alt.EncodingSortField("f{metric}:Q", op="max", order="descending"),
            ),
            tooltip=[
                alt.Tooltip("GROUPER", title="Near Address"),
                alt.Tooltip(
                    f"NUMBER_OF_BRIDGE_TX:Q",
                    title="Number of bridge transactions",
                    format=",",
                ),
                alt.Tooltip(
                    f"TOTAL_AMOUNT_BRIDGED:Q",
                    title="Total amount received (USD)",
                    format=",.2f",
                ),
                alt.Tooltip(
                    f"AVERAGE_AMOUNT_BRIDGED:Q",
                    title="Average amount received (USD)",
                    format=",.2f",
                ),
                alt.Tooltip(
                    f"NUMBER_OF_TOKENS_BRIDGED:Q",
                    title="Number of different tokens received",
                    format=",",
                ),
                alt.Tooltip(
                    f"TOTAL_SENDERS:Q",
                    title="Number of unique senders to this address",
                    format=",",
                ),
                alt.Tooltip(
                    f"LATEST_BALANCE_ETHEREUM:Q",
                    title="Average Ethereum balance of senders to this address (USD)",
                    format=",.2f",
                ),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_ordered_bar_sender(df, metric, ordering):
    df = df.dropna()
    df = df.sort_values(by=metric, ascending=ordering).reset_index(drop=True)
    df = df.iloc[:30]

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("GROUPER", sort="-y", title=None),
            y=alt.Y(metric, title=f"{metric.replace('_', ' ').title()}"),
            color=alt.Color(
                "GROUPER",
                title="Ethereum Address",
                sort=alt.EncodingSortField("f{metric}:Q", op="max", order="descending"),
            ),
            tooltip=[
                alt.Tooltip("GROUPER", title="Ethereum Address"),
                alt.Tooltip(
                    f"NUMBER_OF_BRIDGE_TX:Q",
                    title="Number of bridge transactions",
                    format=",",
                ),
                alt.Tooltip(
                    f"TOTAL_AMOUNT_BRIDGED:Q",
                    title="Total amount sent (USD)",
                    format=",.2f",
                ),
                alt.Tooltip(
                    f"AVERAGE_AMOUNT_BRIDGED:Q",
                    title="Average amount sent (USD)",
                    format=",.2f",
                ),
                alt.Tooltip(
                    f"NUMBER_OF_TOKENS_BRIDGED:Q",
                    title="Number of different tokens sent",
                    format=",",
                ),
                alt.Tooltip(
                    f"TOTAL_RECEIVERS:Q",
                    title="Number of unique receivers from this address",
                    format=",",
                ),
                alt.Tooltip(
                    f"LATEST_BALANCE_ETHEREUM:Q",
                    title="Latest Account Balance (USD)",
                    format=",.2f",
                ),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart
