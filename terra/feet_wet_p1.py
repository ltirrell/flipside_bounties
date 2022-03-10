import altair as alt
import pandas as pd
import streamlit as st

st.title("Getting Your Feet Wet, Part 1")
st.caption(
    """
Make a table containing wallet addresses whose first transaction was 90 days ago or less. 
Analyze how active they have been since that first transaction, based on either:
1. the number of transactions
2. the number of protocols interacted with, or
3. the number of different types of transactions undertaken. (deposit, delegate, vote)

Note: grand prize-winning submissions will assess at least two of the activity metrics above."""
)


@st.cache(ttl=(3600))
def load_data():
    dfs = []
    # top wallets for different counts
    qs = [
        "142895a1-cdf9-46b8-983c-7431962db152",
        "a2fb9260-97c0-497d-9aa8-ac2f30b2b59b",
        "c0b38d79-109b-4fa9-9047-395577374b2f",
    ]
    for q in qs:
        url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
        df = pd.read_json(url)
        dfs.append(df.copy())

    df = dfs[0].merge(dfs[1], how="outer", on="WALLET")
    df = df.merge(dfs[2], how="outer", on="WALLET")

    # summary info
    q = "c1d82778-7da8-4304-8751-b4b76325c008"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    summary = pd.read_json(url)

    for x in summary.columns:
        summary.rename(columns={x: x.title().replace("_", " ")}, inplace=True)
        summary = summary.sort_index(axis=1, ascending=False)

    # tx_type value counts
    q = "295c07cc-5222-4e6c-bd56-80f8b28725c3"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    tx_type_value_counts = pd.read_json(url)

    q = "1b858e2c-9db0-49bd-9c3e-465c56ccac27"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    all_df = pd.read_json(url)

    return df, summary, tx_type_value_counts, all_df


df, summary, tx_type_value_counts, all_df = load_data()

st.header("Overview")

f"""
Terra is a fast growing blockchain. To assess the user growth, we found all wallets that sent their first transaction in the past 90 days, and assessed their activity during this time.

Overall, there are **{summary['Total Wallets'].values[0]:,} new wallets**, making a total of **{summary['Total Tx'].values[0]:,} transactions** (**{summary['Avg Tx Per Wallet'].values[0]:.1f} on average per wallet**).

Each Terra transaction contains one or more `event_types`, such as `transfer`, `vote`, `swap`, etc. New users, on average, made transactions using **{summary['Avg Tx Type Per Wallet'].values[0]:.1f} different transaction types.**
"""

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

"------"

f"""
Various Terra transactions interact with smart contracts.
Some of these contracts have been labeled to associate them with various protocols (such as Mirror, Ancohor, or Mars Protocols).

We found there were **{summary['Total Protocols'].values[0]:,} unique protocols** that were interacted with by the new users (**{summary['Avg Protocols Per Wallet'].values[0]:.1f} on average per wallet**).

In total, there were **{summary['Total Contracts'].values[0]:,} unique contracts** that were interacted with by the new users (**{summary['Avg Contracts Per Wallet'].values[0]:.1f} on average per wallet**).
"""

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Protocols", value=f"{summary['Total Protocols'].values[0]:,}")
col2.metric(
    "Average Protocols", value=f"{summary['Avg Protocols Per Wallet'].values[0]:.1f}"
)
col3.metric("Total Contracts", value=f"{summary['Total Contracts'].values[0]:,}")
col4.metric(
    "Average Contracts", value=f"{summary['Avg Contracts Per Wallet'].values[0]:.1f}"
)


"""
The table containing the wallet addresses used for this analysis, and the date of their first transaction (`JOIN_DATE`) is below.
See links to this query and others used in this analysis are included in [Queries](#queries).

Note that for this, and all other tables, only the top 100,000 rows are used, as this is a currently the maximum number for queries on Flipside Crypto
"""

st.dataframe(all_df)

st.header("Wallet behavior")
"""
We'll investigate some of the behavior of the new users.
"""
st.subheader("Transactions")
"""
Below are the top 50 wallets by transaction count.

Noticably, the top 3 addresses account for ~10% of the total transactions!
These may be related to price oracle/validator activtity, where every few blocks a transaction  is sent with exchange rate information(see [here](https://finder.extraterrestrial.money/mainnet/address/terra1gtszdkzdz5rggssxyayumgehw5ae2p6wedrljf) for an example).

Future analysis will remove these transactions to look at real user activitiy.
"""
chart = (
    alt.Chart(df.sort_values("TX_COUNT", ascending=False)[:50])
    .mark_bar()
    .encode(
        x=alt.X(
            "WALLET",
            sort="-y",
        ),
        y=alt.Y("TX_COUNT", title="Transactions"),
        tooltip=[
            alt.Tooltip("WALLET", title="Wallet"),
            alt.Tooltip("TX_COUNT", title="Transactions"),
        ],
    )
)
st.altair_chart(chart, use_container_width=True)

st.subheader("Protocols")
"""
Below are the top 50 wallets by the number of unique protocols they interacted with.

The number of protocols used per address shows less of a steep dropoff after the first few wallets.

About 1/3 of the 100,000 wallets examined used 3 or more protocols in the last 90 days and 75% used 2 or more. All used at least one protocol.

This facet will be examined in more detail in a future dashboard (see [here](https://share.streamlit.io/ltirrell/flipside_bounties/main/terra/feet_wet_p2.py))
"""
chart = (
    alt.Chart(df.sort_values("PROTOCOL_COUNT", ascending=False)[:50])
    .mark_bar()
    .encode(
        x=alt.X("WALLET", sort="-y", title=""),
        y=alt.Y("PROTOCOL_COUNT", title="Protocols"),
        tooltip=[
            alt.Tooltip("WALLET", title="Wallet"),
            alt.Tooltip("PROTOCOL_COUNT", title="Number of Transaction Types"),
        ],
    )
)
st.altair_chart(chart, use_container_width=True)

st.subheader("Transaction types")
"""
Below are the top 50 wallets by number of Transaction Types they used.

This shows similar behaviour as number of Protocols, with a much larger spread of values.
"""
chart = (
    alt.Chart(df.sort_values("TX_TYPE_COUNT", ascending=False)[:50])
    .mark_bar()
    .encode(
        x=alt.X("WALLET", sort="-y", title=""),
        y=alt.Y("TX_TYPE_COUNT", title="Transaction Types"),
        tooltip=[
            alt.Tooltip("WALLET", title="Wallet"),
            alt.Tooltip("TX_TYPE_COUNT", title="Number of Protocols"),
        ],
    )
)
st.altair_chart(chart, use_container_width=True)

"""
The number of wallets using each Transaction Type is shown below (there is a slight difference in wallets selected for this query, so the numbers don't exactly line up with the totals listed above).

`message`, `coin_spent`, `coin_recieved` and `transfer` transaction types were done by almost all wallets.
"""
st.dataframe(tx_type_value_counts)


st.header("Methods")
"""
The wallets that made their first transactions were selected for using a query based on [this one](https://discord.com/channels/784442203187314689/856566159692136468/950485826842820618).

Any address in the `tx_from` column of the `terra.transactions` table that had a minimum transaction date less than  90 days ago was included.
"""

st.subheader("Queries:")
"""
Queries were done on using Flipside crypto, and are linked here:
- [All addresses](https://app.flipsidecrypto.com/velocity/queries/1b858e2c-9db0-49bd-9c3e-465c56ccac27): limited to 100,000 by Flipside, but can be used as the basis for other queries that aggregate this data
- [Summary information](https://app.flipsidecrypto.com/velocity/queries/c1d82778-7da8-4304-8751-b4b76325c008)
- [Top addresses by Number of Transactions](https://app.flipsidecrypto.com/velocity/queries/142895a1-cdf9-46b8-983c-7431962db152)
- [Top addresses by Number of Protocols](https://app.flipsidecrypto.com/velocity/queries/a2fb9260-97c0-497d-9aa8-ac2f30b2b59b)
- [Top addresses by Number of Transaction Types](https://app.flipsidecrypto.com/velocity/queries/c0b38d79-109b-4fa9-9047-395577374b2f)
- [Value counts Number of Transaction Types](https://app.flipsidecrypto.com/velocity/queries/295c07cc-5222-4e6c-bd56-80f8b28725c3)

"""
st.subheader("Summary Table")
st.table(summary.T)
