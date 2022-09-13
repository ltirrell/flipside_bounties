import altair as alt
import pandas as pd
import streamlit as st

from utils_01 import *

st.set_page_config(
    page_title="NFL ALL DAY: Tournament Kickoff", page_icon="🏈", layout="wide"
)

st.title("🏈 NFL ALL DAY: Tournament Kickoff🏈")
st.caption(
    """
Kicking off the NFL season with NFL All Day summary metrics.
"""
)

st.write(
"""
The NFL 2022 season is finally upon us!
It's a perfect time to analyze metrics related to the [NFL All Day](https://nflallday.com/home) marketplace (hosted on the [Flow blockchain](https://flow.com/)), where users can purchase and sell NFTs of their favorite NFL plays.

Are you ready for some football (and data analysis)?!?!
"""
)
with st.expander("Data Sources and Methods"):
    st.header("Methods")
    f"""
    Data was acquired from Flipside Crypto's Flow Tables.

    - All dates for the 2022 NFL Season were taken from [here](https://operations.nfl.com/gameday/nfl-schedule/2022-23-important-nfl-dates/)
    - The date where NFL All Day users' wallets were created was found by looking at the earliest date a wallet which bought an AllDay NFT (`nft_collection = 'A.e4cf4bdc1751c65d.AllDay'` in the `flow.core.ez_nft_sale` table) was a `proposer` in the `flow.core.fact_transactions` table
    - The Video URL provided by the `flow.core.dim_allday_metadata` is private, so we updated metadata to include the URL for the video hosted on the NFL All Day site when viewing a Moment NFT:
    ```sql
    with updated_metadata as (
        select
            moment_stats_full ['id'] as id,
            lower(replace(set_name, ' ', '_')) as set_name_clean,
            concat(
                'https://assets.nflallday.com/editions/',
                set_name_clean,
                '/',
                id,
                '/play_',
                id,
                '_',
                set_name_clean,
                '_capture_AnimationCapture_Video_Square_Grey_1080_1080_Grey.mp4'
            ) as nflallday_assets_url,
            *
        from
            flow.core.dim_allday_metadata
    ),
    ```
    - Daily sales were calculated by `inner join`ing the above metadata with `low.core.ez_nft_sales` on `nft_id`, and grouping by date, team, player and position.
    - The same was join was done to calculate sales based on the `buyer` and `player`, grouping by `buyer` and `player` instead of the date and other variables.
    - Finally, we looked at popular NFT collections. Due to the size of the dataset, we only looked at the **top 10,000** collections. The top collections based on transaction count, average price, maximum price, and total sale price were queried and combined into a single dataframe, with duplicates dropped (since the same NFT collection may show up in multiple categories, for example a high maximum price and high average price)
    
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
st.write(
"""
First, let's see when NFL All Day users created their Flow wallet.

View the entire date range, or just the 2022 season, starting from the Hall of Fame game weekend (see [here](https://operations.nfl.com/gameday/nfl-schedule/2022-23-important-nfl-dates/) for a listing of all dates relevant to this season).
The start of the season (Hall of Fame Game weekend) is marked with a red line, the 3 preseason games are marked with gray lines, and the Week 1 game is marked with a blue line.

The vast majority were created in April 2022, when the [Historical Drop](https://mobile.twitter.com/NFLALLDAY/status/1517562004579536904) collection was launched.
Recent spikes occurred at the end of July and early August, as preseason activities were ramping up.
Additionally, an influx of new users occurred at the [announcement of the first NFAL ALL DAY Pack Drop for the 2022 season on 18-Aug-2022](https://www.prnewswire.com/news-releases/nfl-nflpa-and-dapper-labs-launch-nfl-all-day-worldwide-revolutionizing-the-way-fans-engage-with-their-favorite-teams-and-players-301608499.html)

There appears to be a general uptick in wallet creation since the start of the preseason, though this is neglible compared to the number of wallets created in April (before general market downturns).
So far during the season, wallets generally show an increase in creation on Wednesday through Friday.
"""
)
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
st.write(
"""
We can see Daily Sales of NFL All Day Moment NFTs, either for the entire date range or just the 2022 season, with important 2022 dates marked (see [the Wallet Creation](#wallet-creation) section for a description).

Sales volume can be viewed as one of 2 Variables in the dropdown:
- Transactions: the count of NFT sales transactions
- Total Sales: the total USD value of sales

Three possible groupings are possible:
- Daily total
- By Team: proportion of daily NFT sales by NFL Team
- By Position: proportion of daily NFT sales by postion of the player

For Daily total, there has been an increase in sales around the start of the preason.
Starting from 28-Jul-2022 (the week before the Hall of Fame Game), volume is generally higher than in the offeason (besides April-May, at the launch of the NFT platform).

There are cyclical trends, with highest volume on Fridays.
This could be due to [pack drops](https://nflallday.com/packs) generally occurring on Thursdays.

For data By Team, the defending Super Bowl Champion Los Angeles Rams generally seem to have a high proportion of daily sales.
Interestingly, after their Week 1 victory, the Buffalo Bills show a large proportion of Daily Sales volume increase.

Generally, wide receivers (WR) have the highest proportion of Daily Sales, followed by running backs (RB) and quarterbacks (QB).
"""
)
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


st.header("User Purchases")
st.write(
"""
The top (sort order: Descending) or bottom (sort order: Ascending) 32 wallets by various metrics can be seen below.

Use the dropdown menu to select which metric to view:
- Transactions: number of purchase transactions
- Total Purchases (USD): Total amount spent (in USD) purchasing Moment NFT
- Average Purchase Price (USD): Average purchase price paid by a wallet
- Maximum Purchase Price (USD): Most expensive NFT price per wallet
- Number of Players: The number of different players a user bought
- Number of Teams: The number of different teams a user bought
- Number of Positions: The number of different positions a user bought
"""
)
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
st.write(
"""
The top (sort order: Descending) or bottom (sort order: Ascending) 32 Players by various metrics can be seen below.

Use the dropdown menu to select which metric to view:
- Transactions: number of purchases of NFTs for that player
- Total Purchases (USD): Total amount spent (in USD) purchasing Moment NFTs for that player
- Average Purchase Price (USD): Average purchase price paid for NFTs for that player
- Maximum Purchase Price (USD): Most expensive price paid for NFTs for that player
- Number of Buyers: the number of unique wallets purchasing NFTs for that player
"""
)
#TODO change title, do by position/team as well?
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
st.write(
"""e
The top (sort order: Descending) or bottom (sort order: Ascending) NFT Collections by various metrics can be seen below.
- `Ctrl-click` (or `Cmd-click` on Mac) a point to view the video captured in the Moment NFT in a new tab.
- Use the slider to view more or less collections.
- Use the dropdown menu to select which metric to view:
    - Transactions: number of purchases of NFTs for that Collection
    - Total Purchases (USD): Total amount spent (in USD) purchasing Moment NFTs for that Collection
    - Average Purchase Price (USD): Average purchase price paid for NFTs for that Collection
    - Maximum Purchase Price (USD): Most expensive price paid for NFTs for that Collection
    - Number of Buyers: the number of unique wallets purchasing NFTs for that Collection
"""
)
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
combined_nft = combined_nft.drop_duplicates(subset="NFT_ID")
combined_nft = combined_nft.apply(update_player_name, axis=1)
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
df = df.drop_duplicates(subset="NFT_ID")
chart = (
    alt.Chart(df)
    .mark_circle(size=69)
    .encode(
        x=alt.X("NFT_ID:Q", title="NFT ID"),
        y=alt.Y(
            f"{metric}:Q",
            scale=alt.Scale(
                zero=False,
            ),
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
        href="NFLALLDAY_ASSETS_URL",
    )
    .properties(height=1000)
    .interactive()
)
st.altair_chart(chart, use_container_width=True)
