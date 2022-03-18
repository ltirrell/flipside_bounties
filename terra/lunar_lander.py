# %%
import datetime

import altair as alt
import networkx as nx
import numpy as np
import pandas as pd
from pyvis.network import Network
from PIL import Image
import requests
import streamlit as st
import streamlit.components.v1 as components

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
@st.cache(ttl=3600, allow_output_mutation=True)
def load_flipside_data():
    """
    # Not using for now
    # prices["UST_DAILY"] = prices.UST_PRICE.rolling(24).mean()
    # prices["UST_WEEKLY"] = prices.UST_PRICE.rolling(24 * 7).mean()
    # prices['UST_MONTHLY'] = prices.UST_PRICE.rolling(24*7*30).mean()

    # # prices["LUNA_DAILY"] = prices.LUNA_PRICE.rolling(24).mean()
    # prices["LUNA_WEEKLY"] = prices.LUNA_PRICE.rolling(24 * 7).mean()
    # prices['LUNA_MONTHLY'] = prices.LUNA_PRICE.rolling(24*7*30).mean()
    """
    q = "77bd19d6-0c7c-4ce8-83c2-e7162adf2cb4"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    prices = pd.read_json(url)

    q = "69a171bd-0db3-44e0-9526-93692270d081"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    stables = pd.read_json(url)

    prices["$0.005"] = (prices.UST_PRICE <= 0.995) | (prices.UST_PRICE >= 1.005)
    prices["$0.01"] = (prices.UST_PRICE <= 0.99) | (prices.UST_PRICE >= 1.01)
    prices["$0.02"] = (prices.UST_PRICE <= 0.98) | (prices.UST_PRICE >= 1.02)
    prices["$0.05 or more"] = (prices.UST_PRICE <= 0.95) | (prices.UST_PRICE >= 1.05)
    # prices["More than $0.05"] = (prices.UST_PRICE < 0.98) | (prices.UST_PRICE > 1.08)

    price_dict = {}
    p = prices.copy().sort_values(by="DATETIME", ascending=False).reset_index(drop=True)
    for k in date_values.keys():
        v = get_date_range(k, p)
        price_dict[k] = v
    return prices, price_dict


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
prices, price_dict = load_flipside_data()
data = load_lcd_data()
data["ust_price"] = prices.loc[
    prices.DATETIME == prices.DATETIME.max()
].UST_PRICE.values[0]
# %%

# %%
# st.title('LUNAR Lander')
_, col, _ = st.columns([1, 3, 1])
image = Image.open(
    "./terra/media/lunar_lander.png",
)
col.image(image, use_column_width="auto")

with st.expander("Summary", expanded=True):
    col1, col2 = st.columns(2)
    with col1.container():
        st.metric(
            "Block timestamp (UTC)",
            f"{data['block_timestamp'].split('T')[0]} {data['block_timestamp'].split('T')[1][:8]}",
        )
        image = Image.open("./terra/media/UST.png")
        st.image(image)
        st.metric("UST Supply:", f'{data["ust"]:,.0f}')
        st.metric("UST Price:", format_price(data["ust_price"], 4))
        image = Image.open("./terra/media/ANC_300x300.png")
        st.image(image, width=60)
        st.metric("aUST price:", format_price(data["aust_rate"], 3))
        st.metric("Anchor Reserve:", format_price(data["anchor_reserve"], 0))
        st.metric("Anchor APY:", f"{data['anchor_apy']:.2f}%")
    with col2.container():
        st.metric("Block", data["block_height"])
        image = Image.open("./terra/media/Luna.png")
        st.image(image)
        st.metric("Luna Price:", format_price(data["luna_price"]))
        st.metric("LUNA Supply:", f'{data["luna"]:,.0f}')
        st.metric("LUNA Staking Percentage:", f"{data['staked_percent']:.2f}%")
        image = Image.open("./terra/media/terra_station.png")
        st.image(image, width=60)
        st.metric("Open Governance Proposals", data["open_proposals"])
        "[Vote here](https://station.terra.money/gov#PROPOSAL_STATUS_VOTING_PERIOD)"

# %%
with st.expander("Square peg, round hole? UST vs. the 💲 Peg", expanded=True):
    st.header("UST Peg Stability")
    # """
    # Choose whether you want to focus analysis on **only when UST is above peg (<= \$1)**, **only** below peg, **only above peg (>= \$1)**, or **both (all UST prices)**.
    # """
    divergence = st.radio(
        "Choose price range for analysis:",
        [   "All data",
            "UST above peg (price greater than or equal to $1)",
            "UST below peg (price less $1)",
            
        ],
        0,
    )
    date_range = st.selectbox("Date range", date_values.keys(), len(date_values) - 1)
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

    price_chart = (
        alt.Chart(p)
        .mark_line()
        .encode(
            x=alt.X(
                "utcyearmonthdatehours(DATETIME)",
                title="",
            ),
            y=alt.Y(
                "UST_PRICE",
                title="Hourly UST Price ($)",
                scale=alt.Scale(domain=[0.92, 1.08]),
            ),
            tooltip=[
                alt.Tooltip("utcyearmonthdatehours(DATETIME)", title="Date"),
                alt.Tooltip("UST_PRICE", title="UST Price"),
            ],
            color=alt.value("#1030e3"),
            # strokeWidth=alt.value(1)
        )
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
        description = "Only when UST price **greater than or equal to $1**."
    elif divergence == "UST below peg (price less $1)":
        description = "Only when UST price **less than $1**."
    elif divergence == "All data":
        description = "All data in date range. The emoji is happier wehn more time is spend close to the peg."
    st.subheader("Percentage of time UST has been been in range")
    description

    def get_proportion_in_range(val, df, divergence):
        price_diff = df.UST_PRICE - 1

        if divergence == "UST above peg (price greater than or equal to $1)":
            return len(df[(price_diff >= 0) & (np.abs(price_diff) <= val)]) / len(df)
        elif divergence == "UST below peg (price less $1)":
            return len(df[(price_diff < 0) & (np.abs(price_diff) <= val)]) / len(df)
        elif divergence == "All data":
            return len(df[np.abs(price_diff) <= val]) / len(df)

    def get_delta(v: float, divergence: str) -> str:
        if divergence == "All data":
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
        else:
            return ""

    good = get_proportion_in_range(0.005, p, divergence)
    lo = get_proportion_in_range(0.01, p, divergence)
    med = get_proportion_in_range(0.02, p, divergence)
    hi = get_proportion_in_range(0.05, p, divergence)
    # vhi =  get_proportion_in_range(0.05, p, opposite=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Within $0.005", f"{good:.2%}", get_delta(good, divergence))
    col2.metric("Within $0.01", f"{lo:.2%}", get_delta(lo, divergence))
    col3.metric("Within $0.02", f"{med:.2%}", get_delta(med, divergence))
    col4.metric("Within $0.05", f"{hi:.2%}", get_delta(hi, divergence))
    # col5.metric("More than $0.05", f"{vhi:.2%}", get_delta(vhi))

    # col1, col2, col3, col4 = st.columns(4)
    # col1.metric("$0.005 off peg", f"{lo:.2%}", get_delta(lo))
    # col2.metric("$0.01 off peg", f"{med:.2%}", get_delta(med))
    # col3.metric("$0.02 off peg", f"{hi:.2%}", get_delta(hi))
    # col4.metric("$0.05 or more off peg", f"{vhi:.2%}", get_delta(vhi))

    # col1.metric("", get_time_off_peg(p["off_peg"]))
    # col2.metric("", get_time_off_peg(p["off_peg_high"]))
    # col3.metric("", get_time_off_peg(p["off_peg_vhigh"]))

# %%
with st.expander("To the moon 🚀🌕! User metrics", expanded=True):
    """New user growth, for new wallets and anchor"""

# %%
with st.expander("Up 📈 or down 📉: Price and supply", expanded=True):
    """LUNA price, UST supply, ..."""

# %%
with st.expander("Sources and References 📜"):
    ...

# %%


#  %%
# p_off = p.copy()
# p_off.loc[p.off_peg == False, "UST_PRICE"] = np.nan

# p = prices[['DATETIME', 'UST_PRICE', 'UST_DAILY', 'UST_WEEKLY']]
# m = prices.melt(id_vars='DATETIME')

# chart = (
#     alt.Chart(prices)
#     .mark_line()
#     .encode(
#         x=alt.X("DATETIME", title=""),
#         y=alt.Y("UST_PRICE", title="Hourly UST Price ($)", scale=alt.Scale(domain=[.92, 1.08])),
#         tooltip=[
#             alt.Tooltip("DATETIME", title="Date"),
#             alt.Tooltip("UST_PRICE", title="UST Price"),
#         ],
#         color='variable'
#     )
# ).interactive()

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
