import altair as alt
import pandas as pd
import streamlit as st

st.title("Getting Your Feet Wet, Part 2")
st.caption(
    """
Assess the extent to which new users interact with each of the following projects.
- Anchor
- Mirror
- Pylon
- Astroport
- Terraswap
- Prism
- Mars

For Definition, clearly define what "interact with" means, e.g. "at least 1 transaction", "at least 5 transactions", etc.

Bonus: to be eligible for the grand prize, complete at least one of the following:
Display at least one visualization to demonstrate project participation, e.g:
- "total # of users who have used each project"
- "total # of transactions by project"
- "TVL by project"
Also include the following projects inyour analysis
- Random Earth
- Knowhere"""
)


# @st.cache(ttl=(3600 * 6))
def load_data():
    q = "6ad7225c-594b-4b4e-bc5b-7c25124ffa11"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)

    return df


df = load_data()

st.header("Overview")

f"""
Following up on our [previous analysis](https://share.streamlit.io/ltirrell/flipside_bounties/main/terra/feet_wet_p1.py), we will assess the usage of popular Terra Protocols by new users (wallet first transacted within the last 90 days).

We looked at the following Protocols/Platforms:
- [Anchor](https://anchorprotocol.com/) (high yield rate savings)
- [Mirror](https://www.mirror.finance/) (synthetic stocks and other assets)
- [Pylon](https://www.pylon.money/): Yield redirection
- [Astroport](https://astroport.fi/): Automated market marker / DEX
- [Terraswap](https://terraswap.io/): Automated market marker / DEX
- [Prism](https://prismprotocol.app/): LUNA refraction
- [Mars](https://marsprotocol.io/): Credit protocol
- [Random Earth](https://randomearth.io/): NFT Marketplace
- [Knowhere](https://knowhere.art/): NFT Marketplace

We will analyze users who had an interaction with the protocol (at least one transaction), as well as "weekly" users (using a proxy of 10 total transactions over the 90 days).
"""

# col1, col2, col3, col4 = st.columns(4)
# col1.metric("Total Wallets", value=f"{summary['Total Wallets'].values[0]:,}")
# col2.metric("Total Transactions", value=f"{summary['Total Tx'].values[0]:,}")
# col3.metric(
#     "Average Transactions", value=f"{summary['Avg Tx Per Wallet'].values[0]:.1f}"
# )
# col4.metric(
#     "Average Transaction Types",
#     value=f"{summary['Avg Tx Type Per Wallet'].values[0]:.1f}",
# )

# "------"

# f"""
# Various Terra transactions interact with smart contracts.
# Some of these contracts have been labeled to associate them with various protocols (such as Mirror, Ancohor, or Mars Protocols).

# We found there were **{summary['Total Protocols'].values[0]:,} unique protocols** that were interacted with by the new users (**{summary['Avg Protocols Per Wallet'].values[0]:.1f} on average per wallet**).

# In total, there were **{summary['Total Contracts'].values[0]:,} unique contracts** that were interacted with by the new users (**{summary['Avg Contracts Per Wallet'].values[0]:.1f} on average per wallet**).
# """

# col1, col2, col3, col4 = st.columns(4)
# col1.metric("Total Protocols", value=f"{summary['Total Protocols'].values[0]:,}")
# col2.metric(
#     "Average Protocols", value=f"{summary['Avg Protocols Per Wallet'].values[0]:.1f}"
# )
# col3.metric("Total Contracts", value=f"{summary['Total Contracts'].values[0]:,}")
# col4.metric(
#     "Average Contracts", value=f"{summary['Avg Contracts Per Wallet'].values[0]:.1f}"
# )


# """
# The table containing the wallet addresses used for this analysis, and the date of their first transaction (`JOIN_DATE`) is below.
# See links to this query and others used in this analysis are included in [Queries](#queries).

# Note that for this, and all other tables, only the top 100,000 rows are used, as this is a currently the maximum number for queries on Flipside Crypto
# """

# st.dataframe(all_df)

# st.header("Wallet behavior")
# """
# We'll investigate some of the behavior of the new users.
# """
# st.subheader("Transactions")
# """
# Below are the top 50 wallets by transaction count.

# Noticably, the top 3 addresses account for ~10% of the total transactions!
# These may be related to price oracle/validator activtity, where every few blocks a transaction  is sent with exchange rate information(see [here](https://finder.extraterrestrial.money/mainnet/address/terra1gtszdkzdz5rggssxyayumgehw5ae2p6wedrljf) for an example).

# Future analysis will remove these transactions to look at real user activitiy.
# """
# chart = (
#     alt.Chart(df.sort_values("TX_COUNT", ascending=False)[:50])
#     .mark_bar()
#     .encode(
#         x=alt.X(
#             "WALLET",
#             sort="-y",
#         ),
#         y=alt.Y("TX_COUNT", title="Transactions"),
#         tooltip=[
#             alt.Tooltip("WALLET", title="Wallet"),
#             alt.Tooltip("TX_COUNT", title="Transactions"),
#         ],
#     )
# )
# st.altair_chart(chart, use_container_width=True)

# st.subheader("Protocols")
# """
# Below are the top 50 wallets by the number of unique protocols they interacted with.

# The number of protocols used per address shows less of a steep dropoff after the first few wallets.

# About 1/3 of the 100,000 wallets examined used 3 or more protocols in the last 90 days and 75% used 2 or more. All used at least one protocol.

# This facet will be examined in more detail in a future dashboard...
# """
# chart = (
#     alt.Chart(df.sort_values("PROTOCOL_COUNT", ascending=False)[:50])
#     .mark_bar()
#     .encode(
#         x=alt.X("WALLET", sort="-y", title=""),
#         y=alt.Y("PROTOCOL_COUNT", title="Protocols"),
#         tooltip=[
#             alt.Tooltip("WALLET", title="Wallet"),
#             alt.Tooltip("PROTOCOL_COUNT", title="Number of Transaction Types"),
#         ],
#     )
# )
# st.altair_chart(chart, use_container_width=True)

# st.subheader("Transaction types")
# """
# Below are the top 50 wallets by number of Transaction Types they used.

# This shows similar behaviour as number of Protocols, with a much larger spread of values.
# """
# chart = (
#     alt.Chart(df.sort_values("TX_TYPE_COUNT", ascending=False)[:50])
#     .mark_bar()
#     .encode(
#         x=alt.X("WALLET", sort="-y", title=""),
#         y=alt.Y("TX_TYPE_COUNT", title="Transaction Types"),
#         tooltip=[
#             alt.Tooltip("WALLET", title="Wallet"),
#             alt.Tooltip("TX_TYPE_COUNT", title="Number of Protocols"),
#         ],
#     )
# )
# st.altair_chart(chart, use_container_width=True)

# """
# The number of wallets using each Transaction Type is shown below (there is a slight difference in wallets selected for this query, so the numbers don't exactly line up with the totals listed above).

# `message`, `coin_spent`, `coin_recieved` and `transfer` transaction types were done by almost all wallets.
# """
# st.dataframe(tx_type_value_counts)


st.header("Methods")
"""
The wallets that made their first transactions were selected for using a query based on [this one](https://discord.com/channels/784442203187314689/856566159692136468/950485826842820618).

Any address in the `tx_from` column of the `terra.transactions` table that had a minimum transaction date less than  90 days ago was included.
"""

st.subheader("Queries:")
"""
Queries were done on using Flipside crypto, and are linked here:
- [Breakdown of Transactions and users by protocol](https://app.flipsidecrypto.com/velocity/queries/6ad7225c-594b-4b4e-bc5b-7c25124ffa11)

"""
# st.subheader("Summary Table")
# st.table(summary.T)
