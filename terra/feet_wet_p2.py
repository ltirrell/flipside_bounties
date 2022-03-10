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


@st.cache(ttl=(3600*6))
def load_data():
    q = "6ad7225c-594b-4b4e-bc5b-7c25124ffa11"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)

    return df


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
"""

df = load_data()

m = df.melt()

# transacations
st.subheader("Transactions")

tx = m[m.variable.str.contains("TX")]
tx["Protocol"] = tx.variable.str.split("_", expand=True)[0].apply(str.title)
tx.loc[tx.Protocol == "Random", "Protocol"] = "Random Earth"

f"""
Below is the number of total transactions for each protocol made by new users.

Anchor has by far the most transactions ({tx[tx.Protocol=='Anchor'].value.values[0]:,} transactions).
This is more than the next 3 protocols combined!
Many new users are drawn to Terra to use Anchor, and this shows in the transaction count.

In second and third place are the two AMMs, Terraswap and Astroport ({tx[tx.Protocol=='Terraswap'].value.values[0]:,} transactions and {tx[tx.Protocol=='Astroport'].value.values[0]:,} transactions, respectively).
Swapping tokens is a key feature of DeFi, and Terraswap is still more widely used by transaction count.

Mirror comes in 4th({tx[tx.Protocol=='Mirror'].value.values[0]:,} transactions).
It is another popular reason for using Terra.

Random Earth and Knowhere are both NFT marketplaces, with Random Earth having a clear lead in transactions (over 20x) ({tx[tx.Protocol=='Random Earth'].value.values[0]:,} transactions and {tx[tx.Protocol=='Knowhere'].value.values[0]:,} transactions, respectively)

Prism and Mars are both new protocols that launched in this time period, and have showns some popularity ({tx[tx.Protocol=='Prism'].value.values[0]:,} transactions and {tx[tx.Protocol=='Mars'].value.values[0]:,} transactions, respectively)

Pylon is an early protocol on Terra, but does not seem to have a lot of popularity with new users ({tx[tx.Protocol=='Pylon'].value.values[0]:,} transactions).

"""

chart = (
    alt.Chart(tx)
    .mark_bar()
    .encode(
        x=alt.X("Protocol", sort="-y", title=""),
        y=alt.Y("value", title="Transactions",),
        tooltip=[
            alt.Tooltip("Protocol", title="Protocol"),
            alt.Tooltip("value", title="Transactions"),
        ],
    )
).interactive()
st.altair_chart(chart, use_container_width=True)

# users
st.subheader("Users")
weekly = m[m.variable.str.contains("WEEKLY")]
weekly["Protocol"] = weekly.variable.str.split("_", expand=True)[1].apply(str.title)
weekly["type"] = "weekly"
weekly.loc[weekly.Protocol == "Random", "Protocol"] = "Random Earth"

users = m[m.variable.str.contains("USERS")][~m.variable.str.contains("WEEKLY")]
users["Protocol"] = users.variable.str.split("_", expand=True)[0].apply(str.title)
users["type"] = "any"
users.loc[users.Protocol == "Random", "Protocol"] = "Random Earth"

all_users = pd.concat([users, weekly])

"""
Next, we will analyze users who had an interaction with the protocols (at least one transaction), as well as "weekly" users (using a proxy of 10 total transactions over the 90 days).

Similar trends emerge as for transactions.
Anchor has the most users, followed by the two AMMs and Mirror though the difference isnt as clear.
This is the same if we look at both users with any interaction, and weekly users.

Mars and Prism are ranked higher in any user count.
They recently had a launch, which attracted the attention of many to participate.

Looking at the weekly trend, these protocols are again behind Random Earth for most popular protocols.

"""



chart = (
    alt.Chart(all_users)
    .mark_bar()
    .encode(
        x=alt.X("Protocol", sort="-y", axis=None, title=None),
        y=alt.Y(
            "value",
            title="Users ",
        ),
        tooltip=[
            alt.Tooltip("Protocol", title="Protocol"),
            alt.Tooltip("value", title="Users"),
            alt.Tooltip("type", title="User type"),
        ],
        color="type",
    )
    .interactive()
)
st.altair_chart(chart, use_container_width=True)


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
