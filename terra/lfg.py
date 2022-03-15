import datetime
import altair as alt
import networkx as nx
import pandas as pd
from pyvis.network import Network
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components


st.title("LFG! Tracking the Luna Foundation Guard reserves and transactions")


image = Image.open("./terra/media/lfg_full.png")
st.image(
    image,
)

st.header("Luna Foundation Guard transactions")
f"""
In its short life, LFG has made a large impact:
- [Funded the Anchor Yield Reserve with $450 million](https://agora.terra.money/t/capitalising-anchors-reserve-with-450m/4236)
- [Established a $1 billion Bitcoin reserve](https://twitter.com/terra_money/status/1496162889085902856)
- [Support the expansion of UST by burning over 4 million LUNA and providing it to the Curve pool](https://twitter.com/LFG_org/status/1501563945076862982)

There are some addresses of interest related to LFG:
- [**LFG wallet**](https://finder.extraterrestrial.money/mainnet/account/terra1gr0xesnseevzt3h4nxr64sh5gk4dwrwgszx3nw): Funded by Terraform labs
- [**Anchor yield reserve funder**](https://finder.extraterrestrial.money/mainnet/account/terra13h0qevzm8r5q0yknaamlq6m3k8kuluce7yf5lj): provided $450 million to the Anchor yield reserve
- [**Terra -> Ethereum (Wormhole) UST sender**](https://finder.extraterrestrial.money/mainnet/account/terra1qy36laaky2ns9n98naha2r0nvt3j7q3fpxfs2e): Sent UST to Ethereum address using Wormhole
- [**LUNA burner**](https://finder.extraterrestrial.money/mainnet/account/terra1cymh5ywgn4azak74h4gsrnakqgel4y9ssersvx): Wallet burning LUNA for UST
- [**Ethereum UST reciever**](https://etherscan.io/address/0xe3011271416f3a827e25d5251d34a56d83446159): (Ethereum address) received UST accross the Wormhole bridge to provide UST to Curve pools


"""


st.header("LUNA Foundation Guard Wallet daily balance")
"""
In blue is the balance of the LFG wallet address itself, while other colors represent addresses where LFG transferred funds:
- **Anchor yield reserve funder**: provided $450 million to the Anchor yield reserve
- **Ethereum UST reciever**: (Ethereum address) received UST accross the Wormhole bridge to provide UST to Curve pools
- **Terra -> Ethereum (Wormhole) UST sender**: Sent UST to Ethereum address using Wormhole
- **LUNA burner**: Wallet burning LUNA for UST

Note: this chart may take up to 1 full day to have up-to-date balances
"""


# Create a dashboard that updates daily to display the Luna Foundation Guard yield reserve. As well, provide at least one visualization and one metric that you think is related to the yield reserve’s growth or depletion. Tweet this out with the hashtag #LFG and #bestanalyticalminds.

# The best 5 dashboards that go above and beyond to provide a) original and insightful analysis and b) visual appeal, great user experience, and flair, will receive a substantial grand prize. Full $150 payout requires a score of 7 or higher

# We will share these directly with Terraform Labs to receive feedback, and potentially, to do a followup project on the financial health and stability of the Luna Foundation Guard.


@st.cache(ttl=3600, allow_output_mutation=True)
def load_data():
    q = "33537344-58a7-417c-860f-1835fdc8d0ee"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df_daily_balance = pd.read_json(url)

    q = "47e63b57-41c3-4974-bd09-21d8c4f25aad"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df_in_out = pd.read_json(url)
    df_in_out = df_in_out.sort_values(by="DATETIME")

    df_daily_balance = df_daily_balance[
        ~df_daily_balance.ADDRESS.isin(
            df_in_out[
                df_in_out.AMOUNT_USD.abs() < 1000
            ].ADDRESS.unique()  # get rid of test transactions
        )
    ]

    q = "16137f94-d5de-4ce9-8e8e-6734691fc42b"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    vesting = pd.read_json(url)

    last_ran = (
        datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    )

    q = "514babaa-91a0-400d-b72a-ecbd3b796780"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    net_data = pd.read_json(url)
    return df_daily_balance, df_in_out, vesting, last_ran, net_data


df_daily_balance, df_in_out, vesting, last_ran, net_data = load_data()

grouped_net_df = (
    net_data.groupby(["SENDER", "RECIPIENT", "TO_LABEL", "FROM_LABEL", "CHAIN"])
    .agg({"AMOUNT_USD": "sum", "TX_ID": "count"})
    .reset_index()
)

edges_df = grouped_net_df.copy()
edges_df['title'] = edges_df['AMOUNT_USD'].apply(lambda x: f"{x:,.2f}")
G = nx.from_pandas_edgelist(
    edges_df,
    source="FROM_LABEL",
    target="TO_LABEL",
    edge_attr=['AMOUNT_USD', 'TX_ID', 'title'],
    create_using=nx.DiGraph
)

def net_viz(G):
    nt = Network(directed=True)
    nt.from_nx(G)
    nt.save_graph('./lfg.html')

net_viz(G)
HtmlFile = open("lfg.html", 'r', encoding='utf-8')
source_code = HtmlFile.read() 
components.html(source_code, height = 1200,width=1000)


balance_by_day = (
    df_daily_balance.groupby(["WALLET_LABEL", "ADDRESS", "DATE"])
    .BALANCE_USD.sum()
    .reset_index()
)

chart = (
    alt.Chart(balance_by_day)
    .mark_bar()
    .encode(
        x=alt.X("DATE", title=""),
        y=alt.Y(
            "BALANCE_USD",
            title="Total balance (USD)",
        ),
        color=alt.Color("WALLET_LABEL", sort=["LFG Wallet"]),
        tooltip=[
            alt.Tooltip("DATE", title="Date"),
            alt.Tooltip("WALLET_LABEL", title="Wallet label"),
            alt.Tooltip("BALANCE_USD", title="Total balance (USD)", format=",.2f"),
            alt.Tooltip("ADDRESS", title="Address"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)

st.header("Inflows and outflows")
"""
The amount (USD) moving into and out of the LFG Wallet is shown here:
"""
df = df_in_out.copy()
df["name"] = df["ADDRESS_LABEL"]
df["name"][df["name"].isna()] = df.ADDRESS
chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("DATETIME", title=""),
        y=alt.Y(
            "AMOUNT",
            title="Amount (LUNA)",
        ),
        color="DIRECTION",
        tooltip=[
            alt.Tooltip("DATETIME", title="Date"),
            alt.Tooltip("AMOUNT", title="Amount (LUNA)", format=",.2f"),
            alt.Tooltip("name", title="Address label"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)

st.subheader("Discussion")
f"""
In its short life, LFG has made a large impact:
- [Funded the Anchor Yield Reserve with $450 million](https://agora.terra.money/t/capitalising-anchors-reserve-with-450m/4236)
- [Established a $1 billion Bitcoin reserve](https://twitter.com/terra_money/status/1496162889085902856)
- [Support the expansion of UST by burning over 4 million LUNA and providing it to the Curve pool](https://twitter.com/LFG_org/status/1501563945076862982)

These drawdowns are reflected in the shrinking balance of the LFG wallet.

The actual LFG yield reserve balance has funding in other wallets which may not yet be reflected in this dashboard.
This may include addresses on the Ethereum blockchain (related to the Curve pool).


Additionally, there were {vesting.TX_COUNT.sum()} transactions on {vesting.DATETIME.count()} days, sent to [this vesting contract](https://finder.extraterrestrial.money/mainnet/address/terra1xmaaewtj7c2s7fjak8g9eqp8ll68hvvyudrfev), for {vesting.AMOUNT.sum():,} LUNA (about ${vesting.AMOUNT_USD.sum():,.2f}).

The first transaction corresponds with the setup of the Bitcoin reserve (about $1 billion)
The others are sent for an as-yet-unknown reason.

Future updates to this dashboard may investigate this further!
"""
vesting = vesting.sort_values(
    by="DATETIME",
)
vesting["cumulative"] = vesting.AMOUNT_USD.cumsum()
chart = (
    alt.Chart(vesting)
    .mark_bar()
    .encode(
        x=alt.X("DATETIME", title=""),
        y=alt.Y(
            "AMOUNT_USD",
            title="Amount (USD)",
        ),
        tooltip=[
            alt.Tooltip("DATETIME", title="Date"),
            alt.Tooltip("AMOUNT_USD", title="Amount (USD)", format=",.2f"),
            alt.Tooltip("AMOUNT", title="Amount (LUNA)", format=",.2f"),
            alt.Tooltip("cumulative", title="Cumulative total (USD)", format=",.2f"),
        ],
    )
)
line = (
    alt.Chart(vesting)
    .mark_line(color="red")
    .encode(
        x=alt.X("DATETIME", title=""),
        y=alt.Y(
            "cumulative",
            title="Amount (USD)",
        ),
        tooltip=[
            alt.Tooltip("DATETIME", title="Date"),
            alt.Tooltip("AMOUNT_USD", title="Amount (USD)", format=",.2f"),
            alt.Tooltip("AMOUNT", title="Amount (LUNA)", format=",.2f"),
            alt.Tooltip("cumulative", title="Cumulative total (USD)", format=",.2f"),
        ],
    )
)

fig = (chart + line).interactive()
st.altair_chart(fig, use_container_width=True)

st.subheader("Sources and notes")
"""
Data from [Flipside Crypto](https://flipsidecrypto.xyz/)
- [Daily Balances](https://app.flipsidecrypto.com/velocity/queries/33537344-58a7-417c-860f-1835fdc8d0ee)
- [LFG inflows and outflows](https://app.flipsidecrypto.com/velocity/queries/47e63b57-41c3-4974-bd09-21d8c4f25aad)
- [Vesting contract](https://app.flipsidecrypto.com/velocity/queries/16137f94-d5de-4ce9-8e8e-6734691fc42b)
- Inspirations:
    - [LFG inflows and outflows](https://app.flipsidecrypto.com/velocity/queries/89c83ffc-7999-4c86-9c80-d8e68befa438)
    - Discussion on Flipside Crytpo Discord, by users:
        - Pinehearst#1947
        - piper#6707
        - joker#2418
        - lambdadelta#7856
        - forg#9122
        - ahkek76#6812

This data is updated approximately every hour, and the dashboard will be further expanded as more knowledge on LFG addresses and transactions are known.

**Disclaimer**: This analysis is made using public data only, and not affiliated in any way with LFG, Terraform labs, or members of their teams.
"""

st.caption(f"Last updated: {last_ran}")
