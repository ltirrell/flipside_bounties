from audioop import avg
import datetime
from gc import collect
import io
import random

import altair as alt
import pandas as pd
import requests
from shroomdk import ShroomDK, errors
import streamlit as st
from PIL import Image

# import near_info

st.set_page_config(page_title="Citizens of NEAR: Arts District", page_icon="🌆")
st.title("Citizens of NEAR: Arts District")
st.caption(
    """
What is a city without a thriving center for arts and culture?!

Exploring the NEAR NFT scene.
"""
)

API_KEY = st.secrets["flipside"]["api_key"]

@st.cache(ttl=24 * 60)
def get_flipside_data(query, cached=True):
    query_result_set = sdk.query(query, cached=cached)
    df = pd.DataFrame(query_result_set.rows, columns=query_result_set.columns)
    return df


def get_random_collections(n=10, max_num=34270) -> list:
    limit = n
    skip = random.randint(0, max_num)

    r = requests.get(
        "https://api-v2-mainnet.paras.id/collections",
        params={"__limit": limit, "__skip": skip},
    )

    return r.json()["data"]["results"]


def add_collection_stats(collection_data: list) -> list:
    data = []
    for x in collection_data:
        r = requests.get(
            "https://api-v2-mainnet.paras.id/collection-stats",
            params={"collection_id": x["collection_id"]},
        )
        data.append({**x, **r.json()["data"]["results"]})
    return data


def print_stats(x):
    s = ""
    try:
        total_card_sale = x["total_card_sale"]
        total_cards = x["total_cards"]
        s += f"- Total NFTs Minted: {total_cards} ({total_card_sale} listed)\n"
    except:
        pass
    try:
        total_owners = x["total_owners"]
        s += f"- Total Unique Owners: {total_owners}\n"
    except:
        pass
    try:
        volume = x["volume"]
        s += f"- Volume: {int(volume)/10**24:.2f} NEAR\n"
    except:
        pass
    try:
        floor_price = x["floor_price"]
        s += f"- Floor Price: {int(floor_price)/10**24:.2f} NEAR\n"
    except:
        pass
    return s


def alt_line_chart(
    data: pd.DataFrame, colname: str = "value", log_scale=False, success_rate=False
) -> alt.Chart:
    """Create a multiline Altair chart with tooltip

    Parameters
    ----------
    data : pd.DataFrame
        Data source to use
    colname : str
        Column name for values
    log_scale : str
        Use log scale for Y axis

    Returns
    -------
    alt.Chart
        Chart showing columnname values, and a multiline tooltip on mouseover
    """
    scale = "log" if log_scale else "linear"
    columns = [
        "Most Expensive NFT",
        "Average Sale",
        "Cheapest NFT",
    ]  # hard coding for now...

    base = alt.Chart(
        data,
        title=f"Sale information for NFT collection: {collection_data['collection']} ({col_id})",
    ).encode(
        x=alt.X(
            "yearmonthdate(DATETIME):T",
            axis=alt.Axis(title=""),
        )
    )

    # data["variable"] = data["variable"].str.title()
    # data["variable"] = data["variable"].str.replace("_", " ")

    selection = alt.selection_single(
        fields=["DATETIME"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout",
    )
    lines = base.mark_area().encode(
        y=alt.Y(
            colname,
            axis=alt.Axis(title="Price (NEAR)"),
            scale=alt.Scale(type=scale),
            stack=None,
        ),
        color=alt.Color(
            "variable:N",
            sort=columns,
            scale=alt.Scale(domain=columns, range=["black", "#2eab9c", "magenta"]),
        ),
        # order=alt.Order(columns)
        opacity=alt.value(0.6),
    )

    rule = (
        base.transform_pivot("variable", value=colname, groupby=["DATETIME"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip("yearmonthdate(DATETIME)", title="Date")]
            + [
                alt.Tooltip(
                    c,
                    type="quantitative",
                    format=".1f",
                )
                for c in columns
            ],
        )
        .add_selection(selection)
    )
    chart = lines + rule

    return chart.interactive().properties(width=1000)


st.header("The hottest place for art: Paras")
f"""
[Paras](https://paras.id/) is the most popular NFT marketplace on NEAR. Let's take a look at what it has to offer.

**NSFW warning: data is loaded at random, and may contain inappropriate images!**
Random images are hidden by default because of this.
"""
st.header("Gallery")
st.write(
    "Walking through Paras, we see a wide variety of collections. We stop at some to take a look:"
)
n_random = st.slider("Number of random collections", 1, 10, 4)
data_load_state = st.text(
    "Loading collection data... if this is taking too long, try refreshing the page."
)
collection_data = get_random_collections(n=n_random)
collection_data = add_collection_stats(collection_data)


with st.expander("Random Collections, expand to view!"):
    cols = st.columns(2)
    for i, collection_data in enumerate(collection_data):
        c_num = i % 2
        if collection_data["creator_id"].endswith(".near"):
            creator = collection_data["creator_id"]
        else:
            creator = f"{collection_data['creator_id'][:8]}...{collection_data['creator_id'][-8:]}"

        try:
            r = requests.get(f"https://ipfs.fleek.co/ipfs/{collection_data['media']}")
            image = Image.open(io.BytesIO(r.content))
            cols[c_num].image(image)
        except:
            pass
        cols[c_num].subheader(f"{collection_data['collection']}")
        try:
            cols[c_num].caption(collection_data["description"])
        except:
            pass
        cols[c_num].write(
            f"""
- **Creator:** {creator}
- [**View on Paras**](https://paras.id/collection/{collection_data['collection_id']})
{print_stats(collection_data)}
-----
    """
        )
data_load_state.text("")


st.header("Tour")
st.write(
    """
Now let's look at a collections in more detail! Take a look at a popular collection, or enter your own below!

We can see the average, most expensive, and cheapest NFT sales each day, as well as the sales volume for the collection (in NEAR and number of transactions).

Try some popular NFT collections such as:
- asac.near (Antisocial Ape Club)
- secretskelliessociety.near (Secret Skellies Society)
- nearnautnft.near (NEARNauts)
"""
)

col_id = st.text_input("Collection ID", "asac.near")
try:
    r = requests.get(
        "https://api-v2-mainnet.paras.id/collections",
        params={"collection_id": col_id},
    )
    collection_data = r.json()["data"]["results"]
    collection_data = add_collection_stats(collection_data)[0]

    if collection_data["creator_id"].endswith(".near"):
        creator = collection_data["creator_id"]
    else:
        creator = f"{collection_data['creator_id'][:8]}...{collection_data['creator_id'][-8:]}"

    try:
        r = requests.get(f"https://ipfs.fleek.co/ipfs/{collection_data['media']}")
        image = Image.open(io.BytesIO(r.content))
        st.image(image)
    except:
        pass
    st.subheader(f"{collection_data['collection']}")
    try:
        st.caption(collection_data["description"])
    except:
        pass
    st.write(
        f"""
    - **Creator:** {creator}
    - [**View on Paras**](https://paras.id/collection/{collection_data['collection_id']})
    {print_stats(collection_data)}
    -----
    """
    )
except:
    st.text(f"Error processing '{col_id}', try again with a different collection!")

query = f"""
with TX AS (
    SELECT
        blocK_timestamp,
        txn_hash,
        tx :receipt as receipt,
        tx :public_key as public_key,
        tx :signer_id as signer_id,
        tx :receiver_id as receiver_id --,action_data:deposit/pow(10,24) as deposit, action_data:gas/pow(10,24) as gas*/
    FROM
        flipside_prod_db.mdao_near.transactions -- WHERE txn_hash = 'AS5QLqtdQKz4fGZeqtBgXHhLbkA1HpVCM4fRaSoBqK5y' -- sale https://paras.id/token/x.paras.near::426086
),
JSON_PARSING AS (
    SELECT
        block_timestamp,
        txn_hash,
        public_key,
        signer_id,
        receiver_id,
        seq,
        key,
        path,
        index,
        replace(value :outcome :logs [0], '\\\\') as logs,
        -- remove // | convert variant | parse json
        check_json(logs) as checks
    FROM
        tx,
        table(flatten(input => receipt))
),
nft_tx_log AS (
    SELECT
        --PARSE_JSON(LOGS):PARAMS
        block_timestamp,
        txn_hash,
        public_key,
        signer_id,
        receiver_id,
        try_parse_json(logs) as parse_logs,
        parse_logs :type as type,
        parse_logs :params :buyer_id as buyer_id,
        parse_logs :params :owner_id as owner_id,
        parse_logs :params :is_offer as is_offer,
        parse_logs :params :is_auction as is_auction,
        parse_logs :params :nft_contract_id as nft_contract_id,
        parse_logs :params :token_id as token_id,
        parse_logs :params :ft_token_id as ft_token_id,
        parse_logs :params :price / pow(10, 24) as near
    FROM
        JSON_PARSING
    WHERE
        checks is null
        and logs is not null -- filter out json_parse 
        AND type is not null
)
SELECT
    date_trunc('day', block_timestamp :: date) as datetime,
    avg(NEAR) as average_sale_NEAR,
    sum(NEAR) as total_sale_NEAR,
    count(txn_hash) as total_tx,
    min(NEAR) as cheapest_NFT,
    max(NEAR) as most_expensive_NFT
FROM
    nft_tx_log
where
    type = 'resolve_purchase'
    and nft_contract_id = '{col_id}'
    and is_offer is NULL
    and is_auction is NULL
group by
    datetime
"""
data_load_state = st.text(
    "Loading data from Flipside... this will take several minutes unless the collection is cached"
)
sdk = ShroomDK(API_KEY)
try:
    df = get_flipside_data(query, cached=True)
except errors.UserError:
    df = get_flipside_data(query, cached=False)
data_load_state.text("")


df = df.rename(
    columns={
        "AVERAGE_SALE_NEAR": "Average Sale",
        "CHEAPEST_NFT": "Cheapest NFT",
        "MOST_EXPENSIVE_NFT": "Most Expensive NFT",
        "TOTAL_SALE_NEAR": "Total Sale Volume",
        "TOTAL_TX": "Number of Sales",
    }
)
sale_df = df[
    [
        "DATETIME",
        "Average Sale",
        "Cheapest NFT",
        "Most Expensive NFT",
    ]
].melt(id_vars=["DATETIME"])


chart = alt_line_chart(sale_df)
st.altair_chart(chart)

chart1 = (
    alt.Chart(
        df,
        title=f"Sale Volume: {collection_data['collection']} ({col_id})",
    )
    .mark_bar()
    .encode(
        x=alt.X(
            "yearmonthdate(DATETIME):T",
            axis=alt.Axis(title=""),
        ),
        y=alt.Y("Number of Sales"),
        tooltip=[
            alt.Tooltip("yearmonthdate(DATETIME)", title="Date"),
            alt.Tooltip("Number of Sales", type="quantitative", format=","),
            alt.Tooltip("Total Sale Volume", type="quantitative", format=",.2f"),
        ],
    )
    .interactive()
    .properties(width=1000)
)

chart2 = (
    alt.Chart(
        df,
    )
    .mark_line(color="red")
    .encode(
        x=alt.X(
            "yearmonthdate(DATETIME):T",
            axis=alt.Axis(title=""),
        ),
        y=alt.Y("Total Sale Volume", title="Sale Volume (NEAR)"),
        tooltip=[
            alt.Tooltip("yearmonthdate(DATETIME)", title="Date"),
            alt.Tooltip("Number of Sales", type="quantitative", format=","),
            alt.Tooltip("Total Sale Volume", type="quantitative", format=",.2f"),
        ],
    )
    .interactive()
    .properties(width=1000)
)
st.altair_chart(alt.layer(chart1, chart2).resolve_scale(y="independent"))

st.header("Methods")
"""Data was gathered using the [Paras API](https://parashq.github.io/) and Flipside Crypto, using this [query](https://app.flipsidecrypto.com/velocity/queries/b4781971-7539-41ef-9c1e-4af08afb79de) from [@pinehearst_](https://twitter.com/pinehearst_)"""
