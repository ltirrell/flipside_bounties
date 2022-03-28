# %%
import datetime

import altair as alt
import networkx as nx
import numpy as np
import pandas as pd
from pyvis.network import Network
from PIL import Image
import requests
from scipy.stats import kendalltau
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="LUNAr Lander", page_icon="🌕")
# %%
# https://github.com/alecande11/terra-discord-webhook/blob/main/realtimeData.js
LCD = "https://lcd.terra.dev"
BLOCKS_PER_YEAR = 4656810

date_values = {
    "24h": 24,
    "7d": 24 * 7,
    "14d": 24 * 14,
    "30d": 24 * 30,
    "60d": 24 * 60,
    "90d": 24 * 90,
    "180d": 24 * 180,
    "1y": 24 * 365,
    "Max": -1,
}


def convert(val: str) -> float:
    return float(val) / 1_000_000


def format_price(val: float, decimals=2) -> str:
    return f"${val:,.{decimals}f}"


def get_date_range(val: str, df: pd.DataFrame) -> pd.DataFrame:
    data_points = date_values[val]
    if data_points == -1:
        return df
    else:
        return df.iloc[:data_points]


def get_time_off_peg(s: pd.Series) -> str:
    total = s.sum()

    if total < 72:
        return f"{total} hr"
    else:
        return f"{total/24:.1f} d"


# %%
@st.cache(ttl=7200, allow_output_mutation=True)
def load_initial_data():
    q = "77bd19d6-0c7c-4ce8-83c2-e7162adf2cb4"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    prices = pd.read_json(url)

    price_dict = {}
    p = prices.copy().sort_values(by="DATETIME", ascending=False).reset_index(drop=True)
    for k in date_values.keys():
        v = get_date_range(k, p)
        price_dict[k] = v

    q = "c3d0aee6-2d96-4aa4-901a-5104d6588eee"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    staking = pd.read_json(url)

    return price_dict, staking


@st.cache(ttl=7200, allow_output_mutation=True)
def load_flipside_data():

    q = "69a171bd-0db3-44e0-9526-93692270d081"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    stables = pd.read_json(url)

    p = prices[["DATETIME", "UST_PRICE"]]
    p["SYMBOL"] = "UST"
    p = p.rename(columns={"UST_PRICE": "PRICE"})
    stables = pd.concat([stables, p], ignore_index=True)

    stable_dict = {}
    s = (
        stables.copy()
        .sort_values(by="DATETIME", ascending=False)
        .reset_index(drop=True)
    )
    for k in date_values.keys():
        v = get_date_range(k, s)
        stable_dict[k] = v

    # feet wet p1
    q = "c1d82778-7da8-4304-8751-b4b76325c008"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    summary = pd.read_json(url)

    q = "c6cb88f8-6d6b-4d52-8f94-5e2b4f523af1"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    join_date = pd.read_json(url)
    join_date = join_date.sort_values(by="JOIN_DATE").reset_index()
    join_date["CUMULATIVE"] = join_date.NEW_USERS.cumsum()
    join_date["JOIN_DATE"] = pd.to_datetime(join_date.JOIN_DATE)

    q = "4f6342fe-87b9-4e4c-a9d3-6ad352d490f4"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    join_date_all = pd.read_json(url)
    join_date_all = join_date_all.sort_values(by="JOIN_DATE").reset_index()
    join_date_all["CUMULATIVE"] = join_date_all.NEW_USERS.cumsum()
    join_date_all["JOIN_DATE"] = pd.to_datetime(join_date_all.JOIN_DATE)

    # feet wet p2
    q = "6ad7225c-594b-4b4e-bc5b-7c25124ffa11"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)

    m = df.melt()
    tx = m[m.variable.str.contains("TX")]
    tx["Protocol"] = tx.variable.str.split("_", expand=True)[0].apply(str.title)
    tx.loc[tx.Protocol == "Random", "Protocol"] = "Random Earth"

    weekly = m[m.variable.str.contains("WEEKLY")]
    weekly["Protocol"] = weekly.variable.str.split("_", expand=True)[1].apply(str.title)
    weekly["type"] = "weekly"
    weekly.loc[weekly.Protocol == "Random", "Protocol"] = "Random Earth"
    users = m[m.variable.str.contains("USERS")][~m.variable.str.contains("WEEKLY")]
    users["Protocol"] = users.variable.str.split("_", expand=True)[0].apply(str.title)
    users["type"] = "any"
    users.loc[users.Protocol == "Random", "Protocol"] = "Random Earth"

    q = "a63088ff-0105-4bbe-bdc7-a9d048f16649"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    ust_supply = pd.read_json(url)

    all_users = pd.concat([users, weekly])

    # contractually
    q = "1c1f031e-7264-4c3e-ad66-c7c7783f05da"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    top20_df = pd.read_json(url)

    q = "e9fbecd3-d5b0-4850-aec1-f62de32a4660"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    by_protocol_df = pd.read_json(url)

    for x in summary.columns:
        summary.rename(columns={x: x.title().replace("_", " ")}, inplace=True)
        summary = summary.sort_index(axis=1, ascending=False)

    # lfg
    q = "514babaa-91a0-400d-b72a-ecbd3b796780"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    net_data_terra = pd.read_json(url)

    q = "0b6a2281-1bed-4de0-b872-1c2fc474fde9"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    net_data_eth = pd.read_json(url)

    net_data = pd.concat([net_data_terra, net_data_eth]).reset_index(drop=True)
    net_data["BLOCK_TIMESTAMP"] = pd.to_datetime(net_data.BLOCK_TIMESTAMP)

    last_ran = (
        datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    )
    return (
        # price_dict,
        stable_dict,
        # staking,
        ust_supply,
        tx,
        all_users,
        summary,
        join_date,
        join_date_all,
        last_ran,
        net_data,
        top20_df,
        by_protocol_df,
    )


# %%
def load_lcd_data():
    data = {}

    # GET SUPPLY
    r = requests.get(LCD + "/cosmos/bank/v1beta1/supply").json()
    supply = r["supply"]
    for s in supply:
        if s["denom"] == "uusd":
            data["ust"] = convert(s["amount"])
        if s["denom"] == "uluna":
            data["luna"] = convert(s["amount"])

    # GET STAKED LUNA
    r = requests.get(LCD + "/cosmos/staking/v1beta1/pool").json()
    pool = r["pool"]
    data["staked_luna"] = convert(pool["bonded_tokens"])
    data["pool_luna"] = convert(pool["not_bonded_tokens"])  # not sure what this is
    data["staked_percent"] = data["staked_luna"] / data["luna"] * 100

    # GET LUNA PRICE
    r = requests.get(LCD + "/terra/oracle/v1beta1/denoms/uusd/exchange_rate").json()
    data["luna_price"] = float(r["exchange_rate"])

    # GET aUST RATE
    r = requests.get(
        LCD
        + "/wasm/contracts/terra1sepfj7s0aeg5967uxnfk4thzlerrsktkpelm5s/store?query_msg=%7B%20%20%20%22state%22%3A%20%7B%7D%20%7D"
    ).json()
    result = r["result"]
    data["aust_rate"] = float(result["prev_exchange_rate"])
    data["anchor_borrow"] = convert(result["total_liabilities"])

    # GET ANCHOR APY
    r = requests.get(
        LCD
        + "/wasm/contracts/terra1tmnqgvg567ypvsvk6rwsga3srp7e3lg6u0elp8/store?query_msg=%7B%22epoch_state%22%3A%7B%7D%7D"
    ).json()
    block_yield = 1 + float(r["result"]["deposit_rate"])
    data["anchor_apy"] = (np.power(block_yield, BLOCKS_PER_YEAR) - 1) * 100

    # GET ANCHOR YIELD RESERVE
    r = requests.get(
        LCD + "/bank/balances/terra1tmnqgvg567ypvsvk6rwsga3srp7e3lg6u0elp8"
    ).json()
    result = r["result"]
    for x in result:
        if x["denom"] == "uusd":
            data["anchor_reserve"] = convert(x["amount"])

    # HEIGHT
    r = requests.get(LCD + "/blocks/latest").json()

    data["block_height"] = r["block"]["header"]["height"]
    data["block_timestamp"] = r["block"]["header"]["time"]
    data["proposer"] = r["block"]["header"][
        "proposer_address"
    ]  # can get some info from https://terra.stake.id/

    # Governance
    r = requests.get(LCD + "/cosmos/gov/v1beta1/proposals?proposal_status=2")
    proposals = r.json()["proposals"]
    data["open_proposals"] = len(proposals)
    data["proposals"] = proposals

    return data


# %%
_, col, _ = st.columns([1, 3, 1])
image = Image.open(
    "./terra/media/lunar_lander.png",
)
col.image(image, use_column_width="auto")
st.caption("Created by [@ltirrell_](https://twitter.com/ltirrell_)")

data = load_lcd_data()

price_dict, staking = load_initial_data()
prices = price_dict["Max"]

data["ust_price"] = prices.loc[
    prices.DATETIME == prices.DATETIME.max()
].UST_PRICE.values[0]

staking_nona = staking.dropna()
data["staking_yield"] = staking_nona.loc[
    staking_nona.DATE == staking_nona.DATE.max()
].APR.values[0]

with st.expander("Summary", expanded=True):
    st.header("Current blockchain status")
    col1, col2 = st.columns(2)
    # with col1.container():
    col1.metric(
        "Block timestamp (UTC)",
        f"{data['block_timestamp'].split('T')[0]} {data['block_timestamp'].split('T')[1][:8]}",
    )
    image = Image.open("./terra/media/UST.png")
    col1.image(image)
    col1.metric("UST Supply:", f'{data["ust"]:,.0f}')
    col1.metric("UST Price:", format_price(data["ust_price"], 4))
    image = Image.open("./terra/media/ANC_300x300.png")
    col1.image(image, width=60)
    col1.metric("aUST price:", format_price(data["aust_rate"], 3))
    col1.metric("Anchor Reserve:", format_price(data["anchor_reserve"], 0))
    col1.metric("Anchor APY:", f"{data['anchor_apy']:.2f}%")
    # with col2.container():
    col2.metric("Block", data["block_height"])
    image = Image.open("./terra/media/Luna.png")
    col2.image(image)
    col2.metric("Luna Price:", format_price(data["luna_price"]))
    col2.metric("LUNA Supply:", f'{data["luna"]:,.0f}')
    col2.metric("LUNA Staking Yield:", f"{data['staking_yield']:.2f}%")
    col2.metric("LUNA Staking Percentage:", f"{data['staked_percent']:.2f}%")
    image = Image.open("./terra/media/terra_station.png")
    col2.image(image, width=60)
    col2.metric("Open Governance Proposals", data["open_proposals"])
    col2.write("[Vote here](https://station.terra.money/gov#PROPOSAL_STATUS_VOTING_PERIOD)")

#%%
data_load_state = st.text("Loading Flipside data, this will take a few seconds...")
(
    # price_dict,
    stable_dict,
    # staking,
    ust_supply,
    tx,
    all_users,
    summary,
    join_date,
    join_date_all,
    last_ran,
    net_data,
    top20_df,
    by_protocol_df,
) = load_flipside_data()
data_load_state.text("")
stables = stable_dict["Max"]

# %%
with st.expander("Square peg, round hole? UST vs. the 💲 Peg", expanded=True):
    st.header("UST Peg Stability")
    # """
    # Choose whether you want to focus analysis on **only when UST is above peg (<= \$1)**, **only** below peg, **only above peg (>= \$1)**, or **both (all UST prices)**.
    # """
    divergence = st.radio(
        "Choose price range for analysis:",
        [
            "All data",
            "UST above peg (price greater than or equal to $1)",
            "UST below peg (price less $1)",
        ],
        0,
    )
    date_range = st.selectbox("Date range", date_values.keys(), len(date_values) - 2)
    p = price_dict[date_range]

    lower_bands = pd.DataFrame(
        {
            "value1": [1, 0.995, 0.99, 0.98, 0.95],
            "value2": [0.995, 0.99, 0.98, 0.95, 0.92],
            "type": [
                "Within $0.005",
                "Within $0.01",
                "Within $0.02",
                "Within $0.05",
                "Greater than $0.05",
            ],
        }
    )
    upper_bands = pd.DataFrame(
        {
            "value1": [1, 1.005, 1.01, 1.02, 1.05],
            "value2": [1.005, 1.01, 1.02, 1.05, 1.08],
            "type": [
                "Within $0.005",
                "Within $0.01",
                "Within $0.02",
                "Within $0.05",
                "Greater than $0.05",
            ],
        }
    )
    lower = (
        alt.Chart(lower_bands)
        .mark_rect()
        .encode(
            y=alt.Y("value1"),
            y2="value2",
            color=alt.Color(
                "type",
                scale=alt.Scale(
                    domain=[
                        "Within $0.005",
                        "Within $0.01",
                        "Within $0.02",
                        "Within $0.05",
                        "Greater than $0.05",
                    ],
                    scheme="turbo",
                ),
                legend=alt.Legend(title="UST Peg Stability"),
            ),
            opacity=alt.Opacity(
                "type",
                scale=alt.Scale(
                    domain=[
                        "Within $0.005",
                        "Within $0.01",
                        "Within $0.02",
                        "Within $0.05",
                        "Greater than $0.05",
                    ],
                    range=[0.3, 0.5, 0.5, 0.6, 0.7],
                ),
            ),
        )
    )
    upper = (
        alt.Chart(upper_bands)
        .mark_rect()
        .encode(
            y=alt.Y("value1"),
            y2="value2",
            color=alt.Color(
                "type",
                scale=alt.Scale(
                    domain=[
                        "Within $0.005",
                        "Within $0.01",
                        "Within $0.02",
                        "Within $0.05",
                        "Greater than $0.05",
                    ],
                    scheme="turbo",
                ),
                legend=alt.Legend(title="UST Peg Stability"),
            ),
            opacity=alt.Opacity(
                "type",
                scale=alt.Scale(
                    domain=[
                        "Within $0.005",
                        "Within $0.01",
                        "Within $0.02",
                        "Within $0.05",
                        "Greater than $0.05",
                    ],
                    range=[0.3, 0.5, 0.5, 0.6, 0.7],
                ),
            ),
        )
    )
    price_chart = (
        alt.Chart(p)
        .mark_line()
        .encode(
            x=alt.X(
                "DATETIME",
                title="Date",
            ),
            y=alt.Y(
                "UST_PRICE",
                title="Hourly UST Price ($)",
                scale=alt.Scale(
                    domain=[p.UST_PRICE.min() * 0.999, p.UST_PRICE.max() * 1.001]
                ),
            ),
            tooltip=[
                alt.Tooltip("utcyearmonthdatehours(DATETIME)", title="Date"),
                alt.Tooltip("UST_PRICE", title="Price (USD)"),
            ],
            color=alt.value("#1030e3"),
            # strokeWidth=alt.value(1)
        )
    )

    if divergence == "UST above peg (price greater than or equal to $1)":
        chart = (price_chart + upper).interactive()
    elif divergence == "UST below peg (price less $1)":
        chart = (price_chart + lower).interactive()
    elif divergence == "All data":
        chart = (price_chart + lower + upper).interactive()
    st.altair_chart(chart, use_container_width=True)

    # %%
    # """
    # Percentage of time in each range of UST Peg Stability for this date range:
    # """
    if divergence == "UST above peg (price greater than or equal to $1)":
        description = "Only data where UST price **greater than or equal to $1** are counted\n\n`Percentage = <number out of range and more than $1> / <total number of data points> * 100`"
    elif divergence == "UST below peg (price less $1)":
        description = "Only data where UST price **less than $1** are counted.\n\n`Percentage = <number out of range and less than $1> / <total number of data points> * 100`"
    elif divergence == "All data":
        description = "All data in date range.\n\n`Percentage = <number out of range> / <total number of data points> * 100`"

    st.subheader("Percentage of time UST has been been in range")
    description

    def get_proportion_in_range(val, df, divergence="All data", col="UST_PRICE"):
        price_diff = df[col] - 1
        all_off_peg = df[np.abs(price_diff) >= val]
        below = all_off_peg[all_off_peg[col] < 1]
        above = all_off_peg[all_off_peg[col] > 1]

        if divergence == "UST above peg (price greater than or equal to $1)":
            return 1 - (len(above) / len(df))
        elif divergence == "UST below peg (price less $1)":
            return 1 - (len(below) / len(df))
        elif divergence == "All data":
            return 1 - (len(all_off_peg) / len(df))

    def get_delta(v: float) -> str:

        if v == 1:
            return "😁"
        if v >= 0.95:
            return "🙂"
        if v >= 0.9:
            return "-😐"
        if v >= 0.85:
            return "-😟"
        else:
            return "-😩"

    good = get_proportion_in_range(0.005, p, divergence)
    lo = get_proportion_in_range(0.01, p, divergence)
    med = get_proportion_in_range(0.02, p, divergence)
    hi = get_proportion_in_range(0.05, p, divergence)
    # vhi =  get_proportion_in_range(0.05, p, opposite=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Within $0.005", f"{good:.2%}", get_delta(good))
    col2.metric("Within $0.01", f"{lo:.2%}", get_delta(lo))
    col3.metric("Within $0.02", f"{med:.2%}", get_delta(med))
    col4.metric("Within $0.05", f"{hi:.2%}", get_delta(hi))
    st.caption("The emoji is happier when more time is spent close to the $1 peg.")

    date_range_texts = {
        "24h": " in the past day",
        "7d": " in the past 7 days",
        "14d": " in the past 14 days",
        "30d": " in the past 30 days",
        "60d": " in the past 60 days",
        "90d": " in the past 90 days",
        "180d": " in the past 180 days",
        "1y": " in the past year",
        "Max": f" since {p.DATETIME.min():%Y-%m-%d}",
    }
    try:
        date_range_string = date_range_texts[date_range]
    except KeyError:
        date_range_string = ""

    chart = (
        alt.Chart(p)
        .transform_joinaggregate(total="count(*)")
        .transform_calculate(pct="1 / datum.total")
        .mark_bar()
        .encode(
            alt.X(
                "UST_PRICE",
                bin=alt.Bin(
                    extent=[p.UST_PRICE.min() * 0.999, p.UST_PRICE.max() * 1.001],
                    step=0.001,
                ),
                title="UST Price (binned)",
            ),
            alt.Y(
                "sum(pct):Q",
                axis=alt.Axis(format="%"),
                title=f"Percentage of time{date_range_string}",
            ),
            tooltip=[
                alt.Tooltip(
                    "UST_PRICE",
                    title="UST Price",
                    bin=alt.Bin(
                        extent=[p.UST_PRICE.min() * 0.999, p.UST_PRICE.max() * 1.001],
                        step=0.001,
                    ),
                ),
                alt.Tooltip("sum(pct):Q", title="Percentage of time"),
            ],
            color=alt.value("#1030e3"),
        )
    ).interactive()
    col1, col2 = st.columns([2, 1])
    col1.altair_chart((chart), use_container_width=True)
    col2.metric("Median Price", f"{p.UST_PRICE.median():.3f}")
    col2.metric("Minimum Price", f"{p.UST_PRICE.min():.3f}")
    col2.metric("Max Price", f"{p.UST_PRICE.max():.3f}")


# %%
with st.expander("Supply and Demand 📈", expanded=True):
    st.header("UST Supply and LUNA price")
    col1, col2 = st.columns([4, 2])
    col1.write("LUNA is burned to create UST, increasing the scarcity of LUNA.")
    corr = kendalltau(ust_supply.PRICE, ust_supply.TOTAL_BALANCE)
    col2.metric("UST Supply - LUNA price correlation", f"{corr.correlation:.2f}")

    base = alt.Chart(ust_supply).encode(x=alt.X("DATE:T", title=""))
    area = (
        base.mark_area(color="#1030e3")
        .encode(
            y=alt.Y(
                "TOTAL_BALANCE:Q",
                title="UST Supply",
            ),
            tooltip=[
                alt.Tooltip("DATE:T", title="Date"),
                alt.Tooltip("PRICE", title="LUNA price, USD", format=",.2f"),
                alt.Tooltip("TOTAL_BALANCE", title="UST Supply", format=",.2f"),
            ],
        )
        .interactive()
    )
    line = (
        base.mark_line(stroke="goldenrod")
        .encode(
            y=alt.Y(
                "PRICE:Q",
                title="LUNA Price (USD)",
            ),
            tooltip=[
                alt.Tooltip("DATE:T", title="Date"),
                alt.Tooltip("PRICE", title="LUNA price, USD", format=",.2f"),
                alt.Tooltip("TOTAL_BALANCE", title="UST Supply", format=",.2f"),
            ],
        )
        .interactive()
    )
    chart = alt.layer(area, line).resolve_scale(y="independent")
    st.altair_chart(chart, use_container_width=True)


# %%
with st.expander("To the moon 🚀🌕! User metrics", expanded=True):
    st.header("User Metrics")
    base = alt.Chart(join_date_all).encode(x=alt.X("JOIN_DATE:T", title=""))
    area = (
        base.mark_area(color="#1030e3")
        .encode(
            y=alt.Y(
                "NEW_USERS:Q",
                title="New Users",
            ),
            tooltip=[
                alt.Tooltip("JOIN_DATE:T", title="Date"),
                alt.Tooltip("NEW_USERS", title="Users", format=",.2f"),
                alt.Tooltip("CUMULATIVE", title="Cumulative New Users", format=",.2f"),
            ],
        )
        .interactive()
    )
    line = (
        base.mark_line(color="goldenrod")
        .encode(
            y=alt.Y(
                "CUMULATIVE:Q",
                title="Cumulative New Users",
            ),
            tooltip=[
                alt.Tooltip("JOIN_DATE:T", title="Date"),
                alt.Tooltip("NEW_USERS", title="Users", format=",.2f"),
                alt.Tooltip("CUMULATIVE", title="Cumulative New Users", format=",.2f"),
            ],
        )
        .interactive()
    )
    chart = (area + line).resolve_scale(y="independent")

    last_full_day = join_date_all.iloc[-2]
    weekly = join_date_all.resample("7d", on="JOIN_DATE").NEW_USERS.sum()
    monthly = join_date_all.resample("30d", on="JOIN_DATE").NEW_USERS.sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Average daily new users", f"{join_date_all.NEW_USERS.mean():,.0f}")
    col2.metric("Average weekly new users", f"{weekly.mean():,.0f}")
    col3.metric("Average monthly new users", f"{monthly.mean():,.0f}")


    st.altair_chart(chart, use_container_width=True)

    st.subheader("New Users: Summary information")
    "New users are defined as creating their first transaction within the last 90 days."
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Wallets", value=f"{summary['Total Wallets'].values[0]:,}")
    col2.metric("Total Transactions", value=f"{summary['Total Tx'].values[0]:,}")
    col3.metric(
        "Average Transactions", value=f"{summary['Avg Tx Per Wallet'].values[0]:.1f}"
    )
    col4.metric(
        "Average Transaction Types",
        value=f"{summary['Avg Tx Type Per Wallet'].values[0]:.1f}",
    )
    col1.metric("Total Protocols", value=f"{summary['Total Protocols'].values[0]:,}")
    col2.metric(
        "Average Protocols",
        value=f"{summary['Avg Protocols Per Wallet'].values[0]:.1f}",
    )
    col3.metric("Total Contracts", value=f"{summary['Total Contracts'].values[0]:,}")
    col4.metric(
        "Average Contracts",
        value=f"{summary['Avg Contracts Per Wallet'].values[0]:.1f}",
    )

    st.subheader("New users growth")
    base = alt.Chart(join_date).encode(x=alt.X("JOIN_DATE:T", title=""))
    area = (
        base.mark_area(color="#1030e3")
        .encode(
            y=alt.Y(
                "NEW_USERS:Q",
                title="New Users",
            ),
            tooltip=[
                alt.Tooltip("JOIN_DATE:T", title="Date"),
                alt.Tooltip("NEW_USERS", title="Users", format=",.2f"),
                alt.Tooltip("CUMULATIVE", title="Cumulative New Users", format=",.2f"),
            ],
        )
        .interactive()
    )
    line = (
        base.mark_line(color="goldenrod")
        .encode(
            y=alt.Y(
                "CUMULATIVE:Q",
                title="Cumulative New Users",
            ),
            tooltip=[
                alt.Tooltip("JOIN_DATE:T", title="Date"),
                alt.Tooltip("NEW_USERS", title="Users", format=",.2f"),
                alt.Tooltip("CUMULATIVE", title="Cumulative New Users", format=",.2f"),
            ],
        )
        .interactive()
    )
    chart = (area + line).resolve_scale(y="independent")

    last_full_day = join_date.iloc[-2]
    weekly = join_date.resample("7d", on="JOIN_DATE").NEW_USERS.sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Average daily new users", f"{join_date.NEW_USERS.mean():,.0f}")
    col2.metric(
        f"New users, {last_full_day.JOIN_DATE:%Y-%m-%d}",
        f"{last_full_day.NEW_USERS:,}",
        f"{last_full_day.NEW_USERS-join_date.NEW_USERS.mean():,.0f}",
    )
    col3.metric("Average weekly new users", f"{weekly.mean():,.0f}")
    col4.metric(
        f"New users, last full week",
        f"{join_date.iloc[-8:-1].NEW_USERS.sum():,.0f}",
        f"{join_date.iloc[-8:-1].NEW_USERS.sum() - weekly.mean() :,.0f}",
    )

    st.altair_chart(chart, use_container_width=True)

    st.subheader("New users and transactions by protocol")

    """
    Usage of some of the most popular platforms and protocols on the Terra blockchain by new users
    - [Anchor](https://anchorprotocol.com/): high yield rate savings
    - [Mirror](https://www.mirror.finance/): synthetic stocks and other assets
    - [Pylon](https://www.pylon.money/): Yield redirection
    - [Astroport](https://astroport.fi/): Automated market marker / DEX
    - [Terraswap](https://terraswap.io/): Automated market marker / DEX
    - [Prism](https://prismprotocol.app/): LUNA refraction
    - [Mars](https://marsprotocol.io/): Credit protocol
    - [Random Earth](https://randomearth.io/): NFT Marketplace
    - [Knowhere](https://knowhere.art/): NFT Marketplace
    """
    st.write("")
    chart1 = (
        alt.Chart(tx)
        .mark_bar(color="#1030e3")
        .encode(
            x=alt.X("Protocol", sort="-y", title=""),
            y=alt.Y(
                "value",
                title="Transactions",
            ),
            tooltip=[
                alt.Tooltip("Protocol", title="Protocol"),
                alt.Tooltip("value", title="Transactions", format=","),
            ],
        )
    ).interactive()
    chart2 = (
        alt.Chart(all_users)
        .mark_bar(color="#1030e3")
        .encode(
            x=alt.X("Protocol", sort="-y", title=""),
            y=alt.Y(
                "value",
                title="Users",
            ),
            tooltip=[
                alt.Tooltip("Protocol", title="Protocol"),
                alt.Tooltip("value", title="Users", format=","),
                alt.Tooltip("type", title="User type"),
            ],
            color=alt.Color(
                "type",
                scale=alt.Scale(
                    domain=["any", "weekly"],
                    range=["#1030e3", "goldenrod"],
                ),
                legend=alt.Legend(title="Transactions"),
            ),
        )
        .interactive()
    )
    st.altair_chart(alt.hconcat(chart1, chart2), use_container_width=True)
    st.caption(
        "Transaction Count and New users per protocol.\n- **any** = at least one transaction\n- **weekly** = approximately 1 transaction per week"
    )
    "------"
    # from contractually_obligated:

    st.subheader("Top 20 contract addresses")
    st.write("The most used contracts interacted with by new users.")

    def replace_name(x):
        if x.ADDRESS_NAME is None:
            return x.rank
        else:
            return x.ADDRESS_NAME

    t20_tx = top20_df.sort_values("TX_COUNT", ascending=False)[:20].reset_index(
        drop=True
    )
    t20_tx["rank"] = t20_tx.index + 1
    t20_tx["ADDRESS_NAME_NORMALIZED"] = t20_tx.ADDRESS_NAME.fillna(
        t20_tx["CONTRACT"].str[:12]
    )
    t20_users = top20_df.sort_values("USERS", ascending=False)[:20].reset_index(
        drop=True
    )
    t20_users["rank"] = t20_users.index + 1
    t20_users["ADDRESS_NAME_NORMALIZED"] = t20_users.ADDRESS_NAME.fillna(
        t20_users["CONTRACT"].str[:12]
    )

    chart1 = (
        (
            alt.Chart(t20_tx)
            .mark_bar()
            .encode(
                x=alt.X("ADDRESS_NAME_NORMALIZED", sort="-y", title=""),
                y=alt.Y(
                    "TX_COUNT",
                    title="Transactions",
                ),
                color="LABEL",
                tooltip=[
                    alt.Tooltip("rank", title="Rank"),
                    alt.Tooltip("ADDRESS_NAME", title="Contract name"),
                    alt.Tooltip("LABEL", title="Label"),
                    alt.Tooltip("LABEL_TYPE", title="Contract type"),
                    alt.Tooltip("LABEL_SUBTYPE", title="Contract subtype"),
                    alt.Tooltip("TX_COUNT", title="Transaction Count", format=","),
                    alt.Tooltip("USERS", title="Users", format=".2f"),
                    alt.Tooltip("CONTRACT", title="Contract address"),
                ],
            )
        )
        .interactive()
        .properties(width=200)
    )

    chart2 = (
        (
            alt.Chart(t20_users)
            .mark_bar()
            .encode(
                x=alt.X("ADDRESS_NAME_NORMALIZED", sort="-y", title=""),
                y=alt.Y(
                    "USERS",
                    title="Users",
                ),
                color="LABEL",
                tooltip=[
                    alt.Tooltip("rank", title="Rank"),
                    alt.Tooltip("ADDRESS_NAME", title="Contract name"),
                    alt.Tooltip("LABEL", title="Label"),
                    alt.Tooltip("LABEL_TYPE", title="Contract type"),
                    alt.Tooltip("LABEL_SUBTYPE", title="Contract subtype"),
                    alt.Tooltip("TX_COUNT", title="Transaction Count", format=","),
                    alt.Tooltip("USERS", title="Users", format=","),
                    alt.Tooltip("CONTRACT", title="Contract address"),
                ],
            )
        )
        .interactive()
        .properties(width=200)
    )
    st.altair_chart(alt.hconcat(chart1, chart2), use_container_width=True)
    "------"
    st.subheader("Top Contract addresses by popular protocols")
    st.write(
        "For the popular protocols listed above, the most used contracts by new users."
    )
    t2_df = by_protocol_df[
        (by_protocol_df.TX_COUNT_RANK < 3) & (by_protocol_df.USERS_RANK < 3)
    ]
    t2_df = t2_df[t2_df.LABEL != "astroport finance"]

    chart1 = (
        (
            alt.Chart(t2_df)
            .mark_bar()
            .encode(
                x=alt.X("ADDRESS_NAME", sort="-y", title=""),
                y=alt.Y(
                    "TX_COUNT",
                    title="Transactions",
                ),
                color="LABEL",
                tooltip=[
                    alt.Tooltip("ADDRESS_NAME", title="Contract name"),
                    alt.Tooltip("LABEL", title="Label"),
                    alt.Tooltip("LABEL_TYPE", title="Contract type"),
                    alt.Tooltip("LABEL_SUBTYPE", title="Contract subtype"),
                    alt.Tooltip("TX_COUNT", title="Transaction Count", format=","),
                    alt.Tooltip("USERS", title="Users", format=","),
                    alt.Tooltip("USERS_RANK", title="Rank on protocol (by users)"),
                    alt.Tooltip(
                        "TX_COUNT_RANK", title="Rank on protocol (by transactions)"
                    ),
                ],
            )
        )
        .interactive()
        .properties(width=200)
    )
    chart2 = (
        (
            alt.Chart(t2_df)
            .mark_bar()
            .encode(
                x=alt.X("ADDRESS_NAME", sort="-y", title=""),
                y=alt.Y(
                    "USERS",
                    title="Users",
                ),
                color="LABEL",
                tooltip=[
                    alt.Tooltip("ADDRESS_NAME", title="Contract name"),
                    alt.Tooltip("LABEL", title="Label"),
                    alt.Tooltip("LABEL_TYPE", title="Contract type"),
                    alt.Tooltip("LABEL_SUBTYPE", title="Contract subtype"),
                    alt.Tooltip("TX_COUNT", title="Transaction Count", format=","),
                    alt.Tooltip("USERS", title="Users", format=","),
                    alt.Tooltip("USERS_RANK", title="Rank on protocol (by users)"),
                    alt.Tooltip(
                        "TX_COUNT_RANK", title="Rank on protocol (by transactions)"
                    ),
                ],
            )
        )
        .interactive()
        .properties(width=200)
    )

    st.altair_chart(alt.hconcat(chart1, chart2), use_container_width=True)

# %%
with st.expander("The Stablest?", expanded=True):
    st.subheader("UST compared to other stablecoins")

    "UST can be compared to other stablecoins below"

    date_range = st.selectbox("Date range", date_values.keys(), len(date_values) - 4)
    price_range = st.selectbox(
        "Price range", [0.005, 0.01, 0.02, 0.05], 0, format_func=lambda x: f"${x}"
    )
    s = stable_dict[date_range]

    base = alt.Chart(s).encode(
        x=alt.X("utcyearmonthdatehours(DATETIME):T", title="Date")
    )
    columns = sorted(s.SYMBOL.unique())
    selection = alt.selection_single(
        fields=["utcyearmonthdatehours(DATETIME)"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout",
    )

    lines = base.mark_line().encode(
        y=alt.Y(
            "PRICE",
            title="Hourly Price ($)",
            scale=alt.Scale(domain=[s.PRICE.min() * 0.999, s.PRICE.max() * 1.001]),
        ),
        color=alt.Color("SYMBOL:N", scale=alt.Scale(scheme="tableau10")),
    )
    points = lines.mark_point().transform_filter(selection)

    rule = (
        base.transform_pivot("SYMBOL", value="PRICE", groupby=["DATETIME"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip("utcyearmonthdatehours(DATETIME)", title="Date")]
            + [alt.Tooltip(c, type="quantitative") for c in columns],
        )
        .add_selection(selection)
    )
    chart = (lines + points + rule).interactive()
    col1, col2 = st.columns([3, 1])
    col1.altair_chart(chart, use_container_width=True)
    col1.caption("Stablecoin prices")

    for c in columns:
        d = s[s.SYMBOL == c]
        result = get_proportion_in_range(price_range, d, col="PRICE")
        col2.metric(f"{c}: within ${price_range}", f"{result:.2%}", get_delta(result))

    s["WEEKLY_MOVING"] = s.groupby("SYMBOL")["PRICE"].transform(
        lambda x: x.rolling(24 * 7, 1).mean()
    )

    base = alt.Chart(s).encode(
        x=alt.X("utcyearmonthdatehours(DATETIME):T", title="Date")
    )
    columns = sorted(s.SYMBOL.unique())
    selection = alt.selection_single(
        fields=["utcyearmonthdatehours(DATETIME)"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout",
    )

    lines = base.mark_line().encode(
        y=alt.Y(
            "WEEKLY_MOVING",
            title="Hourly Price ($)",
            scale=alt.Scale(
                domain=[s.WEEKLY_MOVING.min() * 0.999, s.WEEKLY_MOVING.max() * 1.001]
            ),
        ),
        color=alt.Color("SYMBOL:N", scale=alt.Scale(scheme="tableau10")),
    )
    points = lines.mark_point().transform_filter(selection)

    rule = (
        base.transform_pivot("SYMBOL", value="WEEKLY_MOVING", groupby=["DATETIME"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip(c, type="quantitative") for c in columns],
        )
        .add_selection(selection)
    )
    chart = (lines + points + rule).interactive()
    col1.altair_chart(chart, use_container_width=True)
    col1.caption("Weekly rolling average")

# %%
with st.expander("LFG! 🌝", expanded=True):
    st.header("LUNA Foundation Guard")
    f"""
    The Luna Foundation Guard (LFG) was established in January 2022 to build a decentralized reserve to back UST.
    Terraform Labs donated over 60 million LUNA to fund this mission.

    LFG's transactions are tracked below. See [here](https://share.streamlit.io/ltirrell/flipside_bounties/main/terra/lfg.py) for more detailed information:
    """

    def subset_network(df, date_range):
        net_data = df.copy()[
            (df.BLOCK_TIMESTAMP >= date_range[0])
            & (df.BLOCK_TIMESTAMP <= date_range[1])
        ]
        grouped_net_df = (
            net_data.groupby(
                ["SENDER", "RECIPIENT", "TO_LABEL", "FROM_LABEL", "CHAIN", "CURRENCY"]
            )
            .agg({"AMOUNT_USD": "sum", "AMOUNT": "sum", "TX_ID": "count"})
            .reset_index()
        )
        return grouped_net_df

    def create_network(df):

        edges_df = df.copy()
        edges_df["title"] = edges_df[
            ["AMOUNT_USD", "TX_ID", "AMOUNT", "CURRENCY"]
        ].apply(
            lambda x: f"<center><strong>{x.AMOUNT:,.2f} {x.CURRENCY}</strong><br>${x.AMOUNT_USD:,.2f} value<br>{int(x.TX_ID)} transaction(s)</center>",
            axis=1,
        )
        edges_df["value"] = np.log(edges_df.AMOUNT_USD)
        G = nx.from_pandas_edgelist(
            edges_df,
            source="FROM_LABEL",
            target="TO_LABEL",
            edge_attr=["AMOUNT_USD", "TX_ID", "title", "value"],
            # node_attr=['CHAIN', 'SENDER', 'RECIPIENT'],
            create_using=nx.DiGraph,
        )

        def get_address_map(G):
            address_map = {}
            for n in G.nodes:
                try:
                    address_map[
                        n
                    ] = f"Address: {net_data[net_data.TO_LABEL==n].RECIPIENT.values[0]}"
                except IndexError:
                    address_map[
                        n
                    ] = f"Address: {net_data[net_data.FROM_LABEL==n].SENDER.values[0]}"
            return address_map

        def get_color_map(G):
            color_map = {}
            for n in G.nodes:
                try:
                    if net_data[net_data.TO_LABEL == n].CHAIN.values[0] == "terra":
                        color_map[n] = "#1888ce"
                    else:
                        color_map[n] = "#9e4364"
                except IndexError:
                    if net_data[net_data.FROM_LABEL == n].CHAIN.values[0] == "terra":
                        color_map[n] = "#1888ce"
                    else:
                        color_map[n] = "#9e4364"
            return color_map

        font_map = dict(zip(G.nodes, ["80px helvetica #bdb897"] * len(G.nodes)))

        address_map = get_address_map(G)
        color_map = get_color_map(G)
        color_map["Luna Foundation Guard"] = "#E4A00C"
        size_map = dict(zip(G.nodes, [45] * len(G.nodes)))
        size_map["Luna Foundation Guard"] = 90
        size_map["Terraform Labs"] = 60

        nx.set_node_attributes(G, font_map, "font")
        nx.set_node_attributes(G, address_map, "title")
        nx.set_node_attributes(G, color_map, "color")
        nx.set_node_attributes(G, size_map, "size")

        return G

    def net_viz(G):
        nt = Network(
            directed=True,
            bgcolor="#051212",
        )
        nt.from_nx(G)
        # nt.show_buttons(filter_=["physics"])
        nt.barnes_hut(spring_length=400, overlap=0)
        nt.save_graph("./lfg.html")

    st.subheader("LFG Transaction Graph")

    date_range = st.slider(
        "Choose the date range for LFG-related transactions to include:",
        net_data.BLOCK_TIMESTAMP.min().to_pydatetime(),
        net_data.BLOCK_TIMESTAMP.max().to_pydatetime(),
        value=(
            net_data.BLOCK_TIMESTAMP.min().to_pydatetime(),
            net_data.BLOCK_TIMESTAMP.max().to_pydatetime(),
        ),
        format="YYYY-MM-DD",
    )

    G = create_network(subset_network(net_data, date_range))
    net_viz(G)
    html_file = open("lfg.html", "r", encoding="utf-8")
    graph = html_file.read()
    components.html(graph, height=550, width=1000)


# %%
with st.expander("Sources and References 📜"):
    st.header("Data Sources")
    f"""
    All data besides the Summary section comes from queries made on [Flipside Crypto](app.flipsidecrypto.com).
    The Summary section uses realtime data for all its metrics *except* for UST price and LUNA staking yield.

    Results may be slightly different if they are reported from multiple different data sources.

    Flipside data is updated is queried hourly (for more real time metrics) or daily (for daily metrics).
    There is some delay between events occurring on chain and ingestion into their database, so their might be some lag in results.

    Luna - UST Supply correlation was calulated using Kendall's Tau (correlation: {corr.correlation:.2f}, pvalue={corr.pvalue:.3f})
    """
    st.subheader("Realtime data")
    f"""
    - Pulled from the [Terra LCD]({LCD})
        - Inspired by the Terra Discord, translated parts of the code from [this repo](https://github.com/alecande11/terra-discord-webhook) into Python
    """
    st.subheader("Flipside Crypto")
    """
    - [LUNA staking information](https://app.flipsidecrypto.com/velocity/queries/c3d0aee6-2d96-4aa4-901a-5104d6588eee)
    - [UST pricing information](https://app.flipsidecrypto.com/velocity/queries/77bd19d6-0c7c-4ce8-83c2-e7162adf2cb4)
    - [Pricing information for other stablecoins](https://app.flipsidecrypto.com/velocity/queries/69a171bd-0db3-44e0-9526-93692270d081)
    - [All Users: Join date](https://app.flipsidecrypto.com/velocity/queries/4f6342fe-87b9-4e4c-a9d3-6ad352d490f4)
    - [New Users: Summary information](https://app.flipsidecrypto.com/velocity/queries/c1d82778-7da8-4304-8751-b4b76325c008)
    - [New Users: Join date](https://app.flipsidecrypto.com/velocity/queries/c6cb88f8-6d6b-4d52-8f94-5e2b4f523af1)
    - [New Users: Breakdown of Transactions and users by protocol](https://app.flipsidecrypto.com/velocity/queries/6ad7225c-594b-4b4e-bc5b-7c25124ffa11)
    - [New Users: Top 20 contracts](https://app.flipsidecrypto.com/velocity/queries/1c1f031e-7264-4c3e-ad66-c7c7783f05da)
    - [New Users: Top 2 by protocol](https://app.flipsidecrypto.com/velocity/queries/e9fbecd3-d5b0-4850-aec1-f62de32a4660)
    - [UST Supply and LUNA Price](https://app.flipsidecrypto.com/velocity/queries/a63088ff-0105-4bbe-bdc7-a9d048f16649)
    - [Terra ransactions used for network creation](https://app.flipsidecrypto.com/velocity/queries/514babaa-91a0-400d-b72a-ecbd3b796780)
    - [Ethereum ransactions used for network creation](https://app.flipsidecrypto.com/velocity/queries/0b6a2281-1bed-4de0-b872-1c2fc474fde9)
    """


col1, col2, col3 = st.columns([4, 1, 2])
col1.caption(f"Flipside data last updated: {last_ran}")
image = Image.open("./terra/media/flipside.png")
col2.image(image, width=50)
col3.caption("Powered by [Flipside Crypto](https://flipsidecrypto.xyz/)")

# %%

# %%
# Question 159: Make your own business intelligence dashboard for the Terra community. Build something that you think your fellow LUNAtics would use. Note: this is not a research or analysis - it is meant to be a functional dashboard. (Examples of past submissions will be provided in the show-and-tell channel.)

# Display at least five key metrics of choice in a visual format. The ability to adjust parameters is welcome, though not required. For Definition, make sure to provide minimal context for your metrics (a sentence or two is fine) to help novice users understand what they are looking at and why it’s important.

# In addition to the grand prize, the best examples will be shared with Do Kwon and the Terraform Labs team. As well, they may receive additional funding for further development in subsequent bounty rounds.

# Notes:

# We will be giving the reward to the Top 5 Submissions we recieve.

# Priority in grading will be given to simple and clean visualizations that display high-impact data metrics to keep the Terra community up-to-date on the health and growth of the network. Additionally, collaboration with other users is welcomed and encouraged. Lastly: we encourage you to rely on existing queries from past submissions rather than reinventing the wheel.

# %%
# chart2 = (
#     alt.Chart(p_off)
#     .mark_line(point=True)
#     .encode(
#         x=alt.X(
#             "utcyearmonthdatehours(DATETIME)",
#             title="",
#         ),
#         y=alt.Y(
#             "UST_PRICE",
#             title="Hourly UST Price ($)",
#             scale=alt.Scale(domain=[0.92, 1.08]),
#         ),
#         tooltip=[
#             alt.Tooltip("utcyearmonthdatehours(DATETIME)", title="Date"),
#             alt.Tooltip("UST_PRICE", title="UST Price"),
#         ],
#         color=alt.value("#1030e3"),
#         # strokeWidth=alt.value(1)
#     )
# )


# col5.metric("More than $0.05", f"{vhi:.2%}", get_delta(vhi))

# col1, col2, col3, col4 = st.columns(4)
# col1.metric("$0.005 off peg", f"{lo:.2%}", get_delta(lo))
# col2.metric("$0.01 off peg", f"{med:.2%}", get_delta(med))
# col3.metric("$0.02 off peg", f"{hi:.2%}", get_delta(hi))
# col4.metric("$0.05 or more off peg", f"{vhi:.2%}", get_delta(vhi))

# col1.metric("", get_time_off_peg(p["off_peg"]))
# col2.metric("", get_time_off_peg(p["off_peg_high"]))
# col3.metric("", get_time_off_peg(p["off_peg_vhigh"]))

# Not using for now
# prices["UST_DAILY"] = prices.UST_PRICE.rolling(24).mean()
# prices["UST_WEEKLY"] = prices.UST_PRICE.rolling(24 * 7).mean()
# prices['UST_MONTHLY'] = prices.UST_PRICE.rolling(24*7*30).mean()

# # prices["LUNA_DAILY"] = prices.LUNA_PRICE.rolling(24).mean()
# prices["LUNA_WEEKLY"] = prices.LUNA_PRICE.rolling(24 * 7).mean()
# prices['LUNA_MONTHLY'] = prices.LUNA_PRICE.rolling(24*7*30).mean()
