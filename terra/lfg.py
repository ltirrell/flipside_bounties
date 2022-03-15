import datetime

import networkx as nx
import numpy as np
import pandas as pd
from pyvis.network import Network
from PIL import Image
import streamlit as st
import streamlit.components.v1 as components


@st.cache(ttl=7200, allow_output_mutation=True)
def load_data():
    q = "16137f94-d5de-4ce9-8e8e-6734691fc42b"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    vesting = pd.read_json(url)

    q = "514babaa-91a0-400d-b72a-ecbd3b796780"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    net_data_terra = pd.read_json(url)

    q = "0b6a2281-1bed-4de0-b872-1c2fc474fde9"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    net_data_eth = pd.read_json(url)

    net_data = pd.concat([net_data_terra, net_data_eth]).reset_index(drop=True)
    net_data["BLOCK_TIMESTAMP"] = pd.to_datetime(net_data.BLOCK_TIMESTAMP)

    q = "63749e53-fe73-4608-ab5e-040c8e89a093"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    gnosis = pd.read_json(url)

    last_ran = (
        datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)")
    )
    return (
        vesting,
        net_data,
        gnosis,
        last_ran,
    )


def subset_network(df, date_range):
    net_data = df.copy()[
        (df.BLOCK_TIMESTAMP >= date_range[0]) & (df.BLOCK_TIMESTAMP < date_range[1])
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
    edges_df["title"] = edges_df[["AMOUNT_USD", "TX_ID", "AMOUNT", "CURRENCY"]].apply(
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

    size_map = dict(zip(G.nodes, [45] * len(G.nodes)))
    size_map["Luna Foundation Guard"] = 90
    size_map["Terraform Labs"] = 60
    font_map = dict(zip(G.nodes, ["80px helvetica #bdb897"] * len(G.nodes)))

    address_map = get_address_map(G)
    color_map = get_color_map(G)
    color_map["Luna Foundation Guard"] = "#E4A00C"
    nx.set_node_attributes(G, size_map, "size")
    nx.set_node_attributes(G, font_map, "font")
    nx.set_node_attributes(G, address_map, "title")
    nx.set_node_attributes(G, color_map, "color")

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


# load and process data
(
    vesting,
    net_data,
    gnosis,
    last_ran,
) = load_data()


### Content
st.title("LFG! Tracking the Luna Foundation Guard reserves and transactions")
image = Image.open("./terra/media/lfg_full.png")
st.image(image, caption="A decentralized economy needs a decentralized currency")

f"""
In a short few weeks since it was found, LFG has made a large impact:
- **19 Jan, 2022**: [Formation of the Luna Foundation Guard with a 50 million LUNA from Terraform Labs](https://medium.com/terra-money/formation-of-the-luna-foundation-guard-lfg-6b8dcb5e127b).
- **07 Feb, 2022**: [Proposal to fund the Anchor Yield Reserve with $450 million](https://agora.terra.money/t/capitalising-anchors-reserve-with-450m/4236/).
- **22 Feb, 2022**: [Establishment of a $1 billion Bitcoin reserve](https://twitter.com/terra_money/status/1496162889085902856).
- **09 Mar, 2022**: [Support the expansion of UST by burning over 4 million LUNA and providing it to the Curve pool](https://twitter.com/LFG_org/status/1501563945076862982).
- **11 Mar, 2022**: [Renewal of LFG LUNA reserves, with a second donation of 12 million LUNA from Terraform labs](https://twitter.com/stablekwon/status/1502225674840555523).


Let's F'ing Go investigate how LFG has been using its funding to support its mission of estabilishing a decentralized UST reserve pool.
"""


st.header("LFG Transaction Graph")

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

# latest network, for current values
grouped_net_df = subset_network(
    net_data,
    (
        net_data.BLOCK_TIMESTAMP.min().to_pydatetime(),
        net_data.BLOCK_TIMESTAMP.max().to_pydatetime(),
    ),
)
# grouped_net_df = grouped_nets[max(grouped_nets.keys())]

G = create_network(subset_network(net_data, date_range))
net_viz(G)
html_file = open("lfg.html", "r", encoding="utf-8")
graph = html_file.read()
components.html(graph, height=550, width=1000)

# st.caption(
#     f"LFG-related transactions, from {date_range[0]:%Y-%m-%d} to {date_range[1]:%Y-%m-%d}"
# )


"""
The interactive network of all transactions to and from the [**LFG wallet**](https://finder.extraterrestrial.money/mainnet/account/terra1gr0xesnseevzt3h4nxr64sh5gk4dwrwgszx3nw) are shown above, where nodes are wallet addresses and edges represent transactions between them.
Second order connections (addresses that transacted with addresses funded by LFG) are also shown.
- Edges are weighted by total USD value of transactions between the addresses
- Hovering over the edges shows the total transaction amount in native currencies and the number of total transactions
- Hovering over nodes shows its account address
- Yellow represents transactions coming from the LFG wallet, blue represesents other transactions on the Terra blockchain, and red represensents Ethereum transactions.
"""
st.header("Key Wallets and Metrics")
st.subheader("LFG actions 💰")
"""
LFG's main wallet sends out LUNA to other wallets or smart contracts to complete its goals, including vesting LUNA for a decentralized reserve and funding the Anchor Yield reserve.
- [**Luna Foundation Guard**](https://finder.extraterrestrial.money/mainnet/account/terra1gr0xesnseevzt3h4nxr64sh5gk4dwrwgszx3nw): Funded by Terraform labs, the main wallet of LFG.
"""
col1, col2 = st.columns(2)
col1.metric(
    "LFG Wallet Balance, LUNA",
    f"{grouped_net_df[grouped_net_df.TO_LABEL=='Luna Foundation Guard'].AMOUNT.sum() - grouped_net_df[grouped_net_df.FROM_LABEL=='Luna Foundation Guard'].AMOUNT.sum():,.0f}",
)
col2.metric(
    "LFG Wallet Balance value, USD",
    f"${grouped_net_df[grouped_net_df.TO_LABEL=='Luna Foundation Guard'].AMOUNT_USD.sum() - grouped_net_df[grouped_net_df.FROM_LABEL=='Luna Foundation Guard'].AMOUNT_USD.sum():,.0f}",
)
"""
- [**Vesting Contract**](https://finder.extraterrestrial.money/mainnet/account/terra1xmaaewtj7c2s7fjak8g9eqp8ll68hvvyudrfev): Over \$2 billion worth of LUNA was sent here. Presumably, this will fund the purchase of the BTC Reserve, with approximately \$1 billion left over.
"""
col1, col2 = st.columns(2)
col1.metric("Vested LUNA", f"{vesting.AMOUNT.sum():,.0f}")
col2.metric("Vested LUNA value, USD", f"${vesting.AMOUNT_USD.sum():,.0f}")
"""
- [**Fund Anchor Reserve**](https://finder.extraterrestrial.money/mainnet/account/terra13h0qevzm8r5q0yknaamlq6m3k8kuluce7yf5lj): provided funding to the Anchor Yield Reserce.
"""
st.metric(
    "Anchor Yield Reserve supplement value, UST",
    f"${grouped_net_df[grouped_net_df.TO_LABEL=='anchor: Overseer'].AMOUNT.sum():,.0f}",
)
"-----"
st.subheader("Luna Burn 🌕🔥")
"""
Several wallets were used to burn LUNA for UST, for example this one:
- [**Burn LUNA for UST**](https://finder.extraterrestrial.money/mainnet/account/terra1cymh5ywgn4azak74h4gsrnakqgel4y9ssersvx): Wallet burning LUNA for UST, at a rate of about 1000 / minute between 10-Mar and 13-Mar.
The total LUNA burned by LFG-associated wallets is:
"""
col1, col2 = st.columns(2)
col1.metric(
    "LUNA burned",
    f"{grouped_net_df[grouped_net_df.TO_LABEL=='terra: mints & burns'].AMOUNT.sum():,.0f}",
)
col2.metric(
    "LUNA burned value, USD",
    f"${grouped_net_df[grouped_net_df.TO_LABEL=='terra: mints & burns'].AMOUNT_USD.sum():,.0f}",
)
"-----"
st.subheader("Bridging to Ethereum 🌉")
"""
UST aims to be *the* decentralized currency, so it needs to be readily available across blockchains.
To rebalance supply on Curve, the most popular stablecoin exchange, UST was bridged to Ethereum and sold for USDT, which was stored in Gnosis Safe.
- [**Send UST to Ethereum**](https://finder.extraterrestrial.money/mainnet/account/terra1qy36laaky2ns9n98naha2r0nvt3j7q3fpxfs2e): Sent UST to Ethereum address using Wormhole, for depositing into Curve.
- [**Ethereum UST reciever**](https://etherscan.io/address/0xe3011271416f3a827e25d5251d34a56d83446159): Ethereum address received UST accross the Wormhole bridge to provide UST to Curve pools
- [**Gnosis Safe**](https://etherscan.io/address/0xad41bd1cf3fd753017ef5c0da8df31a3074ea1ea): [Gnosis Safe](https://gnosis-safe.io/) is a multi-signature asset management platform for Ethereum. USDT received from Curve was sent here.
"""


col1, col2, col3 = st.columns(3)
col1.metric(
    "UST bridged to Ethereum",
    f"${grouped_net_df[grouped_net_df.TO_LABEL=='wormhole: wormhole'].AMOUNT_USD.sum():,.0f}",
)
col2.metric(
    "UST swapped on Curve",
    f"${grouped_net_df[grouped_net_df.TO_LABEL=='Curve: UST-3Pool'].AMOUNT_USD.sum():,.0f}",
)
col3.metric(
    "Gnosis Safe balance",
    f"${gnosis.AMOUNT_USD.sum():,.0f}",
    delta=f"${gnosis.AMOUNT_USD.sum()- grouped_net_df[grouped_net_df.TO_LABEL=='Curve: UST-3Pool'].AMOUNT_USD.sum():,.0f}",
)


st.header("Discussion")
f"""
LFG has burned {grouped_net_df[grouped_net_df.TO_LABEL=='terra: mints & burns'].AMOUNT.sum():,.0f} LUNA for UST, and used this to fund Anchor and rebalance the UST-3Pool on Curve.

With ${gnosis.AMOUNT_USD.sum():,.0f} as a reserve on Ethereum, {vesting.AMOUNT.sum():,.0f} LUNA vested for BTC (or other, as-yet-unknown puposes), and a wallet balance of {grouped_net_df[grouped_net_df.TO_LABEL=='Luna Foundation Guard'].AMOUNT.sum() - grouped_net_df[grouped_net_df.FROM_LABEL=='Luna Foundation Guard'].AMOUNT.sum():,.0f}, LFG has a solid and diversifying set of assets to provide stability to the UST peg.
"""

with st.expander("Sources and notes"):
    """
    Data from [Flipside Crypto](https://flipsidecrypto.xyz/)
    - [Terra ransactions used for network creation](https://app.flipsidecrypto.com/velocity/queries/514babaa-91a0-400d-b72a-ecbd3b796780)
    - [Ethereum ransactions used for network creation](https://app.flipsidecrypto.com/velocity/queries/0b6a2281-1bed-4de0-b872-1c2fc474fde9)
    - [Vesting contract transactions](https://app.flipsidecrypto.com/velocity/queries/16137f94-d5de-4ce9-8e8e-6734691fc42b)
    - [Gnosis Safe transactions](https://app.flipsidecrypto.com/velocity/queries/63749e53-fe73-4608-ab5e-040c8e89a093)
    - Inspirations:
        - Discussion on Flipside Crytpo Discord, by users:
            - Pinehearst#1947
            - piper#6707
            - joker#2418
            - lambdadelta#7856
            - forg#9122
            - ahkek76#6812
            - CryptoIcicle#4958
            - GJ | Flipside Crypto#1919

    This data is updated approximately every hour, and the dashboard will be further expanded as more knowledge on LFG addresses and transactions are known.

    Dollar prices may be slightly off due to differences in data sources.
    Transactions with values under $1000 have been removed from these analyses,

    Check out this [dashboard](https://analytics.zoho.com/open-view/2528727000000006323) from [@cryptoicicle](https://twitter.com/cryptoicicle) for additional LFG information!

    **Disclaimer**: This analysis is made using public data only, and not affiliated in any way with LFG, Terraform labs, or members of their teams.
    """
col1, col2, col3 = st.columns([3, 1, 2])
col1.caption(f"Last updated: {last_ran}")
image = Image.open("./terra/media/flipside.png")
col2.image(image, width=50)
col3.caption("Powered by [Flipside Crypto](https://flipsidecrypto.xyz/)")
