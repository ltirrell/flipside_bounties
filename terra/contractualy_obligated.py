import altair as alt
import pandas as pd
import streamlit as st

st.title("Contractually Obligated")
st.caption(
    """
Based on your analysis for Question 161, 
- provide the top 20 smart contract addresses that users interact with, or
- the top 2 smart contract addresses per each of the protocols that you previously analyzed

Grand prize-winning submissions will assess both!"""
)


@st.cache(ttl=(3600 * 6))
def load_data():
    q = "1c1f031e-7264-4c3e-ad66-c7c7783f05da"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    top20_df = pd.read_json(url)

    q = "e9fbecd3-d5b0-4850-aec1-f62de32a4660"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    by_protocol_df = pd.read_json(url)

    return top20_df, by_protocol_df


top20_df, by_protocol_df = load_data()

st.header("Overview")
f"""
Following up on our [previous analysis](https://share.streamlit.io/ltirrell/flipside_bounties/main/terra/feet_wet_p2.py), we are now going to investigate some of the top smart contracts.

We'll look at:
- Top 20 contracts interacted with by new users
- Top 2 contracts for protocols in our previous analysis (note: Knowhere only has 1 contract address so it is excluded from this analysis)
- Anchor
- Mirror
- Pylon
- Astroport
- Terraswap
- Prism
- Mars
"""

st.header("Top 20 Contract Addresses")


def replace_name(x):
    if x.ADDRESS_NAME is None:
        return x.rank
    else:
        return x.ADDRESS_NAME


t20_tx = top20_df.sort_values("TX_COUNT", ascending=False)[:20].reset_index(drop=True)
t20_tx["rank"] = t20_tx.index + 1
t20_tx["ADDRESS_NAME_NORMALIZED"] = t20_tx.ADDRESS_NAME.fillna(
    t20_tx["CONTRACT"].str[:12]
)
t20_users = top20_df.sort_values("USERS", ascending=False)[:20].reset_index(drop=True)
t20_users["rank"] = t20_users.index + 1
t20_users["ADDRESS_NAME_NORMALIZED"] = t20_users.ADDRESS_NAME.fillna(
    t20_users["CONTRACT"].str[:12]
)

st.subheader("By Transactions")

f"""
The top 20 contract addresses by Transactions is shown below.

Anchor dominates this group, with 5 spots, and the Anchor Market contract is about double the next highest in the group (the Terraswap LUNA-UST LP Pair).

Several of the contracts are unlabled.
As all labels have to be manually entered, it will take time and effort to get all contracts fully labled.
Different sources may have different label sets. 
For example, [terra1zgrz...zupp9](https://finder.extraterrestrial.money/mainnet/address/terra1zgrx9jjqrfye8swykfgmd6hpde60j0nszzupp9) has been labeled on Extraterrestrial Finder as an Astroport-related contract.
"""

chart = (
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
            alt.Tooltip("TX_COUNT", title="Transaction Count"),
            alt.Tooltip("USERS", title="Users"),
            alt.Tooltip("CONTRACT", title="Contract address"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)

st.subheader("By Users")

f"""
The top 20 contract addresses by Users (where users made at least one interaction with the contract) is shown below.

Again, there are many Anchor contracts.
Additionally there are more Terraswap and Astroport related contracts.

Interestingly, the Random Earth contract shows up as one of the most Transacted contracts, but not in the top 20 by number of users.
This suggests a smaller set of users make larger number of transactions on this NFT Marketplace.
"""


chart = (
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
            alt.Tooltip("TX_COUNT", title="Transaction Count"),
            alt.Tooltip("USERS", title="Users"),
            alt.Tooltip("CONTRACT", title="Contract address"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)


st.header("Top 2 contracts per protocol")
st.subheader("By Transactions")

f"""
The top 2 contract addresses per selected protocol, by Transactions is shown below.

Anchor takes 2 of the top 3 spots, with its aUST token as well as its general contract.

The ANC-UST pair is also the 2nd highest transacted contract on Astroport
"""

t2_df = by_protocol_df[
    (by_protocol_df.TX_COUNT_RANK < 3) & (by_protocol_df.USERS_RANK < 3)
]
t2_df = t2_df[t2_df.LABEL != "astroport finance"]

chart = (
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
            alt.Tooltip("TX_COUNT_RANK", title="Rank"),
            alt.Tooltip("ADDRESS_NAME", title="Contract name"),
            alt.Tooltip("LABEL", title="Label"),
            alt.Tooltip("LABEL_TYPE", title="Contract type"),
            alt.Tooltip("LABEL_SUBTYPE", title="Contract subtype"),
            alt.Tooltip("TX_COUNT", title="Transaction Count"),
            alt.Tooltip("USERS", title="Users"),
            alt.Tooltip("USERS_RANK", title="Rank (by users)"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)

st.subheader("By Users")

f"""
The top 2 contract addresses per selected protocol, by Users (where users made at least one interaction with the contract) is shown below.

Similar trends occur as with the Transactions ranking.
The same contracts appear, just in differing order by protocol.
"""
chart = (
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
            alt.Tooltip("USERS_RANK", title="Rank"),
            alt.Tooltip("ADDRESS_NAME", title="Contract name"),
            alt.Tooltip("LABEL", title="Label"),
            alt.Tooltip("LABEL_TYPE", title="Contract type"),
            alt.Tooltip("LABEL_SUBTYPE", title="Contract subtype"),
            alt.Tooltip("TX_COUNT", title="Transaction Count"),
            alt.Tooltip("USERS", title="Users"),
            alt.Tooltip("TX_COUNT_RANK", title="Rank (by transactions)"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)

# chart = (
#     alt.Chart(t20_users)
#     .mark_bar()
#     .encode(
#         x=alt.X("ADDRESS_NAME", sort="-y", title=""),
#         y=alt.Y(
#             "USERS",
#             title="Users",
#         ),
#         tooltip=[
#             alt.Tooltip("rank", title="Rank"),
#             alt.Tooltip("ADDRESS_NAME", title="Contract name"),
#             alt.Tooltip("LABEL", title="Label"),
#             alt.Tooltip("LABEL_TYPE", title="Contract type"),
#             alt.Tooltip("LABEL_SUBTYPE", title="Contract subtype"),
#             alt.Tooltip("TX_COUNT", title="Transaction Count"),
#             alt.Tooltip("USERS", title="Users"),
#         ],
#     )
# ).interactive()
# st.altair_chart(chart, use_container_width=True)


st.header("Methods")
"""
The wallets that made their first transactions were selected for using a query based on [this one](https://discord.com/channels/784442203187314689/856566159692136468/950485826842820618).

Any address in the `tx_from` column of the `terra.transactions` table that had a minimum transaction date less than  90 days ago was included.
"""

st.subheader("Queries:")
"""
Queries were done on using Flipside crypto, and are linked here:
- [Top 20 contracts](https://app.flipsidecrypto.com/velocity/queries/1c1f031e-7264-4c3e-ad66-c7c7783f05da)
- [Top 2 by protocol](https://app.flipsidecrypto.com/velocity/queries/e9fbecd3-d5b0-4850-aec1-f62de32a4660)
"""
