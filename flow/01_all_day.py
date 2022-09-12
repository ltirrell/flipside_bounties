import altair as alt
import pandas as pd
import streamlit as st

from utils_01 import *


st.set_page_config(
    page_title="NFL ALL DAY: Tournament Kickoff", page_icon="🏈", layout="wide"
)

st.title("NFL ALL DAY: Tournament Kickoff")
st.caption(
    """
Kicking off the NFL season with NFL All Day summary metrics.
"""
)

with st.expander("Data Sources and Methods"):
    st.header("Methods")
    f"""
    Data was acquired from Flipside Crypto's Flow Tables.
    
    Queries are hosted on Flipside Crytpo here:
    """
    for k, v in query_information.items():
        x = f"- [{k}]({v['query']})"
        x

dfs = load_data()
date_rules = (
    alt.Chart(
        date_df,
    )
    .mark_rule()
    .encode(
        x="Date:T",
        color=alt.Color("color:N", scale=None),
        tooltip=[
            alt.Tooltip("yearmonthdate(Date)", title="Date"),
            alt.Tooltip("Description"),
        ],
        strokeWidth=alt.value(2),
    )
)

st.header("Wallet Creation")
user_creation = dfs["user_creation"].copy()
user_creation["CREATION_DATE"] = pd.to_datetime(
    user_creation["CREATION_DATE"], utc=True
)
user_creation["CREATION_DATE"] = user_creation["CREATION_DATE"] + pd.Timedelta(days=1)
date_range = st.radio(
    "Date range:", ["All dates", "2022 season"], key="user_creation", horizontal=True
)
if date_range == "2022 season":
    user_creation = user_creation[user_creation.CREATION_DATE >= "2022-08-05T00:00:00Z"]
chart = (
    alt.Chart(user_creation, title="NFL ALL DAY Users: wallet creation date")
    .mark_bar()
    .encode(
        x=alt.X("yearmonthdate(CREATION_DATE)", title=""),
        y=alt.Y("USER_COUNT", title="Users"),
        tooltip=[
            alt.Tooltip("yearmonthdate(CREATION_DATE)", title="Date"),
            alt.Tooltip("USER_COUNT", title="Users"),
        ],
    )
    .interactive()
    .properties(height=500)
)


st.altair_chart(chart + date_rules, use_container_width=True)


st.header("Daily Sales")
daily_sales = dfs["daily_sales"].copy()
daily_sales["DATE"] = pd.to_datetime(daily_sales["DATE"], utc=True)
daily_sales["POSITION"] = daily_sales["POSITION"].apply(
    lambda x: "Team" if x == "" else x
)
daily_sales["DATE"] = daily_sales["DATE"] + pd.Timedelta(days=1)
c1, c2, c3 = st.columns(3)
date_range = c1.radio(
    "Date range:", ["All dates", "2022 season"], key="daily_sales", horizontal=True
)
if date_range == "2022 season":
    daily_sales = daily_sales[daily_sales.DATE >= "2022-08-05T00:00:00Z"]

grouping = c2.selectbox(
    "Grouping:",
    ["Daily total", "By Team", "By Position"],
    key="daily_sales_group",
)
variable = c3.selectbox(
    "Variable:",
    ["TRANSACTIONS", "TOTAL_SALES"],
    format_func=lambda x: x.replace("_", " ").title(),
    key="daily_sales_variable",
)

if variable == "TOTAL_SALES":
    title = "Total Sales (USD)"
else:
    title = "Transactions"

if grouping == "Daily total":
    df = daily_sales.groupby("DATE")[["TRANSACTIONS", "TOTAL_SALES"]].sum()

    df["DATE"] = df.index
    chart = (
        alt.Chart(df, title=f"NFL ALL DAY Sales: Daily Totals ({title})")
        .mark_bar()
        .encode(
            x=alt.X("yearmonthdate(DATE)", title=""),
            y=alt.Y(f"{variable}:Q", title=title),
            tooltip=[
                alt.Tooltip(
                    "yearmonthdate(DATE)",
                    title="Date",
                ),
                alt.Tooltip("TRANSACTIONS", title="Transactions", format=","),
                alt.Tooltip("TOTAL_SALES", title="Total Sales (USD)", format=","),
            ],
        )
        .interactive()
        .properties(height=500)
    )
elif grouping == "By Team":
    df = (
        daily_sales.groupby(["DATE", "TEAM"])[["TRANSACTIONS", "TOTAL_SALES"]]
        .sum()
        .reset_index()
    )
    chart = (
        alt.Chart(df, title=f"NFL ALL DAY Sales: Daily Proprtions by Team ({title})")
        .mark_bar()
        .encode(
            x=alt.X("yearmonthdate(DATE)", title=""),
            y=alt.Y(f"{variable}:Q", title=title, stack="normalize"),
            tooltip=[
                alt.Tooltip(
                    "yearmonthdate(DATE)",
                    title="Date",
                ),
                alt.Tooltip(
                    "TEAM",
                    title="Team",
                ),
                alt.Tooltip("TRANSACTIONS", title="Transactions", format=","),
                alt.Tooltip("TOTAL_SALES", title="Total Sales (USD)", format=","),
            ],
            color=alt.Color(
                "TEAM:N",
                title="Team",
                legend=alt.Legend(symbolLimit=0),
                scale=alt.Scale(
                    scheme="tableau20",
                ),
            ),
        )
        .interactive()
        .properties(height=800)
    )
elif grouping == "By Position":
    df = (
        daily_sales.groupby(["DATE", "POSITION"])[["TRANSACTIONS", "TOTAL_SALES"]]
        .sum()
        .reset_index()
    )
    chart = (
        alt.Chart(
            df, title=f"NFL ALL DAY Sales: Daily Proportions by Position ({title})"
        )
        .mark_bar()
        .encode(
            x=alt.X("yearmonthdate(DATE)", title=""),
            y=alt.Y(f"{variable}:Q", title=title, stack="normalize"),
            tooltip=[
                alt.Tooltip(
                    "yearmonthdate(DATE)",
                    title="Date",
                ),
                alt.Tooltip(
                    "POSITION",
                    title="Position",
                ),
                alt.Tooltip("TRANSACTIONS", title="Transactions", format=","),
                alt.Tooltip("TOTAL_SALES", title="Total Sales (USD)", format=","),
            ],
            color=alt.Color(
                "POSITION:N",
                title="Position",
                legend=alt.Legend(symbolLimit=0),
                scale=alt.Scale(
                    scheme="tableau20",
                ),
            ),
        )
        .interactive()
        .properties(height=800)
    )

st.altair_chart(chart + date_rules, use_container_width=True)


st.header("User purchases")
user_tx = dfs["user_tx"].copy()
user_tx = user_tx.rename(
    {
        "TRANSACTIONS": "Transactions",
        "TOTAL_PURCHASE_COST": "Total Purchases (USD)",
        "AVG_PURCHASE_COST": "Average Purchase Price (USD)",
        "MAX_PURCHASE_COST": "Maximum Purchase Price (USD)",
        "NUMBER_OF_PLAYERS": "Number of Players",
        "NUMBER_OF_TEAMS": "Number of Teams",
        "NUMBER_OF_POSITIONS": "Number of Positions",
    },
    axis=1,
)
metrics = [
    "Transactions",
    "Total Purchases (USD)",
    "Average Purchase Price (USD)",
    "Maximum Purchase Price (USD)",
    "Number of Players",
    "Number of Teams",
    "Number of Positions",
]
c1, c2 = st.columns(2)
metric = c1.selectbox(
    "Metric:",
    metrics,
    key="user_tx_metric",
)
sort_order = c2.radio(
    "Sort Order",
    [False, True],
    format_func=lambda x: "Ascending" if x else "Descending",
    key="user_tx_sort",
    horizontal=True,
)

df = (
    user_tx.copy()
    .sort_values(by=metric, ascending=sort_order)
    .iloc[:32]
    .reset_index(drop=True)
)
chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("BUYER", title=None, sort="-y"),
        y=alt.Y(
            f"{metric}:Q",
        ),
        color=alt.Color(
            "BUYER",
            legend=alt.Legend(title="Buyer", symbolLimit=0),
            sort=alt.EncodingSortField(f"{metric}", op="max", order="descending"),
            scale=alt.Scale(
                scheme="tableau20",
            ),
        ),
        tooltip=[alt.Tooltip("BUYER", title="Buyer")]
        + [alt.Tooltip(x, format=",.1f") for x in metrics],
    )
    .properties(height=800)
    .interactive()
)
st.altair_chart(chart, use_container_width=True)


st.header("Purchases by Player")
player_tx = dfs["player_tx"].copy()
player_tx = player_tx.rename(
    {
        "TRANSACTIONS": "Transactions",
        "TOTAL_PURCHASE_COST": "Total Purchases (USD)",
        "AVG_PURCHASE_COST": "Average Purchase Price (USD)",
        "MAX_PURCHASE_COST": "Maximum Purchase Price (USD)",
        "NUMBER_OF_BUYERS": "Number of Buyers",
    },
    axis=1,
)
metrics = [
    "Transactions",
    "Total Purchases (USD)",
    "Average Purchase Price (USD)",
    "Maximum Purchase Price (USD)",
    "Number of Buyers",
]
c1, c2 = st.columns(2)
metric = c1.selectbox(
    "Metric:",
    metrics,
    key="player_tx_metric",
)
sort_order = c2.radio(
    "Sort Order",
    [False, True],
    format_func=lambda x: "Ascending" if x else "Descending",
    key="player_tx_sort",
    horizontal=True,
)

df = (
    player_tx.copy()
    .sort_values(by=metric, ascending=sort_order)
    .iloc[:32]
    .reset_index(drop=True)
)
chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("PLAYER_NORMALIZED", title=None, sort="-y"),
        y=alt.Y(
            f"{metric}:Q",
        ),
        color=alt.Color(
            "PLAYER_NORMALIZED",
            legend=alt.Legend(title="Player", symbolLimit=0),
            sort=alt.EncodingSortField(f"{metric}", op="max", order="descending"),
            scale=alt.Scale(
                scheme="tableau20",
            ),
        ),
        tooltip=[alt.Tooltip("PLAYER_NORMALIZED", title="Player")]
        + [alt.Tooltip(x, format=",.1f") for x in metrics],
    )
    .properties(height=800)
    .interactive()
)
st.altair_chart(chart, use_container_width=True)


st.header("Popular NFT Collections")
combined_nft = dfs["combined_nft"].copy()
combined_nft = combined_nft.rename(
    {
        "TRANSACTIONS": "Transactions",
        "TOTAL_PURCHASE_COST": "Total Purchases (USD)",
        "AVG_PURCHASE_COST": "Average Purchase Price (USD)",
        "MAX_PURCHASE_COST": "Maximum Purchase Price (USD)",
        "NUMBER_OF_BUYERS": "Number of Buyers",
    },
    axis=1,
)
metrics = [
    "Transactions",
    "Total Purchases (USD)",
    "Average Purchase Price (USD)",
    "Maximum Purchase Price (USD)",
    "Number of Buyers",
]
c1, c2, c3 = st.columns(3)
metric = c1.selectbox(
    "Metric:",
    metrics,
    key="combined_nft_metric",
)
sort_order = c2.radio(
    "Sort Order",
    [False, True],
    format_func=lambda x: "Ascending" if x else "Descending",
    key="combined_nft_sort",
    horizontal=True,
)
number_of_collections = c3.slider("Number of NFT Collections", 0, 1000, 320)

df = (
    combined_nft.copy()
    .sort_values(by=metric, ascending=sort_order)
    .iloc[: int(number_of_collections)]
    .reset_index(drop=True)
)

chart = (
    alt.Chart(df)
    .mark_circle(size=69)
    .encode(
        x=alt.X("NFT_ID:Q", title="NFT ID"),
        y=alt.Y(
            f"{metric}:Q",
        ),
        color=alt.Color(
            f"{metric}",
            legend=alt.Legend(title=f"{metric}", symbolLimit=0),
            # sort=alt.EncodingSortField(f"{metric}", op="max", order="descending"),
            scale=alt.Scale(
                scheme="plasma",
            ),
        ),
        tooltip=[
            alt.Tooltip("NFT_ID", title="NFT ID"),
            alt.Tooltip("PLAYER", title="Player"),
            alt.Tooltip("TEAM", title="Team"),
            alt.Tooltip("POSITION", title="Position"),
            alt.Tooltip("MOMENT_TIER", title="NFT Rarity"),
            alt.Tooltip("PLAY_TYPE", title="Play Type"),
            alt.Tooltip("TOTAL_CIRCULATION", title="Collection Size"),
            ]
        + [alt.Tooltip(x, format=",.1f") for x in metrics],
        href="NFLALLDAY_ASSETS_URL"
    )
    .properties(height=1000)
    .interactive()
)
