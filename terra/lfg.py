import datetime
import altair as alt
import pandas as pd
import streamlit as st

st.title("LFG!")
st.caption(
    """
LUNA Foundation Guard yield reserve
"""
)

st.header("LUNA Foundation Guard Wallet daily balance")
"""
In blue is the balance of the LFG wallet address itself, while other colors represent addresses where LFG transferred funds:
- **Anchor yield reserve funder**: provided $450 million to the Anchor yield reserve
- **Ethereum UST reciever**: (Ethereum address) received UST accross the Wormhole bridge to provide UST to Curve pools
- **Terra -> Ethereum (Wormhole) UST sender**: Sent UST to Ethereum address using Wormhole
- **UST burner**: Wallet burning LUNA for UST
"""


# Create a dashboard that updates daily to display the Luna Foundation Guard yield reserve. As well, provide at least one visualization and one metric that you think is related to the yield reserve’s growth or depletion. Tweet this out with the hashtag #LFG and #bestanalyticalminds.

# The best 5 dashboards that go above and beyond to provide a) original and insightful analysis and b) visual appeal, great user experience, and flair, will receive a substantial grand prize. Full $150 payout requires a score of 7 or higher

# We will share these directly with Terraform Labs to receive feedback, and potentially, to do a followup project on the financial health and stability of the Luna Foundation Guard.


@st.cache(ttl=7200)
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
            df_in_out[df_in_out.AMOUNT_USD.abs() < 1000].ADDRESS.unique() # get rid of test transactions
        )
    ]
    last_ran = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    return df_daily_balance, df_in_out, last_ran


df_daily_balance, df_in_out, last_ran = load_data()

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

st.header('Inflows and outflows')
"""
The amount (USD) moving into and out of the LFG Wallet is shown below
"""

chart = (
    alt.Chart(df_in_out)
    .mark_bar()
    .encode(
        x=alt.X("DATETIME", title=""),
        y=alt.Y(
            "AMOUNT_USD",
            title="Amount (USD)",
        ),
        color="DIRECTION",
        tooltip=[
            alt.Tooltip("DATETIME", title="Date"),
            alt.Tooltip("AMOUNT", title="Amount (USD)", format=",.2f"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)



st.subheader("Sources and notes")
"""
Data from [Flipside Crypto](https://flipsidecrypto.xyz/)
- [Daily Balances](https://app.flipsidecrypto.com/velocity/queries/33537344-58a7-417c-860f-1835fdc8d0ee)
- [LFG inflows and outflows](https://app.flipsidecrypto.com/velocity/queries/47e63b57-41c3-4974-bd09-21d8c4f25aad)
- Inspirations:
    - [LFG inflows and outflows](https://app.flipsidecrypto.com/velocity/queries/89c83ffc-7999-4c86-9c80-d8e68befa438)
    - Discussion on Flipside Crytpo Discord, by users:
        - Pinehearst#1947
        - piper#6707
        - joker#2418
        - lambdadelta#7856
        - forg#9122
        - ahkek76#6812

This data is updated hourly, and the dashboard will be further expanded as more knowledge on LFG addresses and transactions are known.
"""

st.caption(f"Last updated: {last_ran:%Y-%m-%d %H:%M}")


# Create a dashboard that updates daily to display the Luna Foundation Guard yield reserve. As well, provide at least one visualization and one metric that you think is related to the yield reserve’s growth or depletion. Tweet this out with the hashtag #LFG and #bestanalyticalminds.

# The best 5 dashboards that go above and beyond to provide a) original and insightful analysis and b) visual appeal, great user experience, and flair, will receive a substantial grand prize. Full $150 payout requires a score of 7 or higher

# We will share these directly with Terraform Labs to receive feedback, and potentially, to do a followup project on the financial health and stability of the Luna Foundation Guard.