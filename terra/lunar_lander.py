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
    q = "77bd19d6-0c7c-4ce8-83c2-e7162adf2cb4"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    prices = pd.read_json(url)

    q = "69a171bd-0db3-44e0-9526-93692270d081"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    stables = pd.read_json(url)

    p = prices[["DATETIME", "UST_PRICE"]]
    p["SYMBOL"] = "UST"
    p = p.rename(columns={"UST_PRICE": "PRICE"})
    stables = pd.concat([stables, p], ignore_index=True)

    price_dict = {}
    p = prices.copy().sort_values(by="DATETIME", ascending=False).reset_index(drop=True)
    for k in date_values.keys():
        v = get_date_range(k, p)
        price_dict[k] = v

    stable_dict = {}
    s = (
        stables.copy()
        .sort_values(by="DATETIME", ascending=False)
        .reset_index(drop=True)
    )
    for k in date_values.keys():
        v = get_date_range(k, s)
        stable_dict[k] = v

    return price_dict, stable_dict


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
price_dict, stable_dict = load_flipside_data()
prices = price_dict["Max"]
stables = stable_dict["Max"]
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
        [
            "All data",
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
                "utcyearmonthdatehours(DATETIME)",
                title="Date",
            ),
            y=alt.Y(
                "UST_PRICE",
                title="Hourly UST Price ($)",
                scale=alt.Scale(domain=[p.UST_PRICE.min()*.999, p.UST_PRICE.max()*1.001]),
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

    def get_proportion_in_range(val, df, divergence='All data', col='UST_PRICE'):
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

    chart = (
        alt.Chart(p)
        .transform_joinaggregate(total="count(*)")
        .transform_calculate(pct="1 / datum.total")
        .mark_bar()
        .encode(
            alt.X(
                "UST_PRICE",
                bin=alt.Bin(extent=[0.95, 1.05], step=0.005),
                title="UST Price (binned)",
            ),
            alt.Y("sum(pct):Q", axis=alt.Axis(format="%"), title="Percentage"),
            tooltip=[
                # alt.Tooltip("utcyearmonthdatehours(DATETIME)", title="Date"),
                alt.Tooltip(
                    "UST_PRICE",
                    title="UST Price",
                    bin=alt.Bin(extent=[0.95, 1.05], step=0.005),
                ),
                alt.Tooltip("sum(pct):Q", title="Percentage"),
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

    st.subheader("UST compared to other stablecoins")

    "Pricing information for other top stablecoins is below, for the same date range. Percentage of time within $0.005 of the peg is also shown."
    s = stable_dict[date_range]

    base = alt.Chart(s).encode(x=alt.X("utcyearmonthdatehours(DATETIME):T", title='Date'))
    columns = sorted(s.SYMBOL.unique())
    selection = alt.selection_single(
        fields=["utcyearmonthdatehours(DATETIME)"], nearest=True, on="mouseover", empty="none", clear="mouseout"
    )

    lines = base.mark_line().encode(
        y=alt.Y(
            "PRICE",
            title="Hourly Price ($)",
            scale=alt.Scale(domain=[s.PRICE.min()*.999, s.PRICE.max()*1.001]),
        ),
        color="SYMBOL:N",
    )
    points = lines.mark_point().transform_filter(selection)

    rule = (
        base.transform_pivot("SYMBOL", value="PRICE", groupby=["DATETIME"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip(c, type="quantitative") for c in columns],
        )
        .add_selection(selection)
    )
    chart = (lines + points + rule ).interactive()
    col1,col2 = st.columns([3,1])
    col1.altair_chart(chart, use_container_width=True)
    col1.caption("Stablecoin prices")

    
    for i,c in enumerate(columns):
        if i > 3:
            i -= 3
        d = s[s.SYMBOL==c]
        result = get_proportion_in_range(0.005, d, col='PRICE')
        col2.metric(f"{c}: within $0.005", f"{result:.2%}", get_delta(result))

    s['DAILY_MOVING'] = s.groupby('SYMBOL')['PRICE'].transform(lambda x: x.rolling(24*7,1 ).mean())


    base = alt.Chart(s).encode(x=alt.X("utcyearmonthdatehours(DATETIME):T", title='Date'))
    columns = sorted(s.SYMBOL.unique())
    selection = alt.selection_single(
        fields=["utcyearmonthdatehours(DATETIME)"], nearest=True, on="mouseover", empty="none", clear="mouseout"
    )

    lines = base.mark_line().encode(
        y=alt.Y(
            "DAILY_MOVING",
            title="Hourly Price ($)",
            scale=alt.Scale(domain=[s.DAILY_MOVING.min()*.999, s.DAILY_MOVING.max()*1.001]),
        ),
        color="SYMBOL:N",
    )
    points = lines.mark_point().transform_filter(selection)

    rule = (
        base.transform_pivot("SYMBOL", value="DAILY_MOVING", groupby=["DATETIME"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip(c, type="quantitative") for c in columns],
        )
        .add_selection(selection)
    )
    chart = (lines + points + rule ).interactive()
    col1.altair_chart(chart, use_container_width=True)
    col1.caption("Weekly rolling average")
    # s2 = s[s.SYMBOL!='UST']
    # s2.index=s2.DATETIME
    # ust = s[s.SYMBOL=='UST']
    # ust.index=ust.DATETIME
    # ust=ust.dropna()
    # diff = ust.PRICE - s2.PRICE
    # s2 = s2.merge(diff, left_index=True, right_index=True)

    #     good = get_proportion_in_range(0.005, p, divergence)
    # lo = get_proportion_in_range(0.01, p, divergence)
    # med = get_proportion_in_range(0.02, p, divergence)
    # hi = get_proportion_in_range(0.05, p, divergence)
    # # vhi =  get_proportion_in_range(0.05, p, opposite=True)

    # col1, col2, col3, col4 = st.columns(4)
    # col1.metric("Within $0.005", f"{good:.2%}", get_delta(good))
    # col2.metric("Within $0.01", f"{lo:.2%}", get_delta(lo))
    # col3.metric("Within $0.02", f"{med:.2%}", get_delta(med))
    # col4.metric("Within $0.05", f"{hi:.2%}", get_delta(hi))
# nearest = alt.selection(type='single', nearest=True, on='mouseover',
#                         fields=["DATETIME"], empty='none')
# line = (
#     alt.Chart(s)
#     .mark_line()
#     .encode(
#         x=alt.X(
#             "DATETIME",
#             title="Date",
#         ),
#         y=alt.Y(
#             "PRICE",
#             title="Hourly Price ($)",
#             scale=alt.Scale(domain=[0.92, 1.08]),
#         ),
#         # tooltip=[
#         #     alt.Tooltip("utcyearmonthdatehours(DATETIME)", title="Date"),
#         #     alt.Tooltip("SYMBOL", title="Symbol"),
#         #     alt.Tooltip("PRICE", title="Price"),

#         # ],
#         color="SYMBOL",
#         # strokeWidth=alt.value(1)
#     )
# )
# # Transparent selectors across the chart. This is what tells us
# # the x-value of the cursor
# selectors = alt.Chart(s).mark_point().encode(
#     x= "DATETIME",
#     opacity=alt.value(0),
# ).add_selection(
#     nearest
# )

# # Draw points on the line, and highlight based on selection
# points = line.mark_point().encode(
#     opacity=alt.condition(nearest, alt.value(1), alt.value(0))
# )

# # Draw text labels near the points, and highlight based on selection
# text = line.mark_text(align='left', dx=5, dy=-5).encode(
#     text=alt.condition(nearest, 'PRICE', alt.value(' '))
# )

# # Draw a rule at the location of the selection
# rules = alt.Chart(s).mark_rule(color='gray').encode(
#     x= "DATETIME",
# ).transform_filter(
#     nearest
# )

# # Put the five layers into a chart and bind the data
# chart = alt.layer(
#     line, selectors, points, rules, text
# ).interactive()




# %%

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
