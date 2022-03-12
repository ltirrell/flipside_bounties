import datetime
import altair as alt
from matplotlib import interactive
import pandas as pd
from PIL import Image
import streamlit as st



st.title("LFG! Tracking the Luna Foundation Guard reserves and transactions")


image = Image.open('./terra/media/lfg_full.png')
st.image(image,)



st.header("LUNA Foundation Guard Wallet daily balance")
"""
In blue is the balance of the LFG wallet address itself, while other colors represent addresses where LFG transferred funds:
- **Anchor yield reserve funder**: provided $450 million to the Anchor yield reserve
- **Ethereum UST reciever**: (Ethereum address) received UST accross the Wormhole bridge to provide UST to Curve pools
- **Terra -> Ethereum (Wormhole) UST sender**: Sent UST to Ethereum address using Wormhole
- **UST burner**: Wallet burning LUNA for UST

Note: this chart may take up to 1 full day to have up-to-date balances
"""


# Create a dashboard that updates daily to display the Luna Foundation Guard yield reserve. As well, provide at least one visualization and one metric that you think is related to the yield reserve’s growth or depletion. Tweet this out with the hashtag #LFG and #bestanalyticalminds.

# The best 5 dashboards that go above and beyond to provide a) original and insightful analysis and b) visual appeal, great user experience, and flair, will receive a substantial grand prize. Full $150 payout requires a score of 7 or higher

# We will share these directly with Terraform Labs to receive feedback, and potentially, to do a followup project on the financial health and stability of the Luna Foundation Guard.


@st.cache(ttl=4000, allow_output_mutation=True)
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
    return df_daily_balance, df_in_out, vesting, last_ran


df_daily_balance, df_in_out, vesting, last_ran = load_data()

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
df['name'] = df['ADDRESS_LABEL']
df['name'][df['name'].isna()] =df.ADDRESS
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
In its short, LFG has made a large impact:
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
