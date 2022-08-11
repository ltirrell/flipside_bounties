from functools import partial

import pandas as pd
import streamlit as st

from fin_utils import *

st.set_page_config(
    page_title="Citizens of NEAR: Financial District", page_icon="🌆", layout="wide"
)

st.title("Citizens of NEAR: Financial District")
st.caption(
    """
Investigating the *de facto* Central Bank within the NEAR ecosystem. 
"""
)
with st.expander("Data Sources and Methods"):
    st.header("Methods")
    f"""
    Data was acquired from Flipside Crypto's NEAR tables, as well as using [Ref Finance's Analytics Page](https://stats.ref.finance/) for more real time information.

    Ref Analytics polls an internal API, which can be accessed publicly. The [`get_ref_data`](https://github.com/ltirrell/flipside_bounties/blob/main/near/fin_utils.py#L129) (around line 93 of the linked file on GitHub) function lists the URLs that were pulled, and the resulting data was converter to a DataFrame in Python. This is the source of all pricing information, as well as other metrics associated with the protocol (such as TVL).

    Data related to claiming Farm Rewards and depositing/withdrawing into Farms as acquired using Flipside Crypto. Successful transactions with `receiver_id = 'v2.ref-farming.near'` were used as the basis for these queries.

    Daily reward claims per farm were counted by counting the transactions with `method_name = 'claim_reward_by_farm`, while rewards per user/token looked at `method_name = 'withdraw_reward` transactions.
    Deposits into Farms were transactions with `method_name = 'mft_transfer_call`, while withdrawing from farms were transactions with `method_name = 'withdraw_seed`.

    Note: due to large size of integrers used in NEAR, values were divided by `pow(10, 18)` in the SQL queries before processing in python

    Queries are hosted on Flipside Crytpo here:
    """
    for k, v in query_information.items():
        x = f"- [{k}]({v['query']})"
        x


st.header("Central Bank of NEAR")
"""As the saying goes, "cash rules everything around me", and NEAR is no different. The place where this happens the most is at the *de facto* central bank of NEAR, Ref Finance. [Ref](https://www.ref.finance/) is by [far the most popular](https://awesomenear.com/ranking) DeFi platform on NEAR, allowing users to trade, pool their tokens in liquidity pools (LP), and farm their LP tokens to earn rewards. Additionally, the protocol has a token, $REF, which can be staked to earn fees generated by the protocol.

Let's take a look at some of its metrics:
"""
ref_data = get_ref_data()
date_range = st.radio(
    "Date range for charts:",
    ["All", 7, 30, 60, 90],
    format_func=lambda x: x if type(x) == str else f"{x}d",
    horizontal=True,
)
tvl = ref_data["historical_tvl_all"]["df"].copy()
tvl["date"] = tvl["historicalTVL"].map(lambda x: pd.to_datetime(x["date"]))
tvl["totalUsdTvl"] = tvl["historicalTVL"].map(lambda x: x["totalUsdTvl"])
tvl["usdNear"] = tvl["historicalTVL"].map(lambda x: x["usdNear"])
latest_tvl = tvl.iloc[-1]
tvl = tvl.drop(index=len(tvl) - 1)
tvl_chart = alt_date_area(
    tvl,
    "totalUsdTvl",
    title="TVL (USD)",
    date_range=date_range,
    color="#08754a",
    val_format=",",
)

vol = ref_data["volume_24h_all"]["df"].copy()
vol["date"] = pd.to_datetime(vol["date"])
latest_vol = ref_data["volume_variation_24h"]["data"]
vol_chart = alt_date_area(
    vol,
    "volume",
    title="Trade Volume (USD)",
    date_range=date_range,
    color="#3d403e",
    val_format=",.0f",
)

c1, c2 = st.columns(2)
c1.metric(
    "Curent Total Value Locked (TVL)",
    f"${latest_tvl.tvlAmount24h:,}",
    f"{latest_tvl.tvlVariation24h:.2%}",
)
c2.metric(
    "Trade Volume, past 24 hours",
    f"${float(latest_vol['lastVolumeUSD']):,.0f}",
    f"{float(latest_vol['variation']):.2%}",
)
c1.altair_chart(tvl_chart, use_container_width=True)
c2.altair_chart(vol_chart, use_container_width=True)


st.subheader("Tokens and Pools")
st.write(
    """
Let's take a look inside the vaults, and see the most popular Tokens and Pools used on Ref.

Pools are a group of 2 or 3 tokens that allow users to trade one token in group for another. A Pool has a set fee for trades.
Any user can create a Pool of 2 tokens (a trading Pair), while a Tri-Pool is permissioned so only Ref can create them. For more information, see the [Ref Finance documentation](https://guide.ref.finance/products/pooling).
Users can also deposit to Pools to get liquidity tokens, giving them access to a portion of trading fees.

Choose the metric (TVL or 24 hour Volume) you would like to see, and how many items you would like to see ranked.
"""
)
ft = ref_data["ft"]["df"].copy()
dfs = load_data()

tokens = ref_data["top_tokens"]["df"].copy()
tokens["Current TVL"] = pd.to_numeric(tokens.tvl)
tokens["24h Volume"] = pd.to_numeric(tokens.volume24h)
tokens["price"] = pd.to_numeric(tokens.price)
tokens["is_stablecoin"] = tokens.symbol.isin(["USDC", "USDT", "USN", "cUSD", "DAI"])
tokens["is_btc"] = tokens.symbol.isin(["WBTC", "HBTC"])
tokens["is_near"] = tokens.symbol.isin(["wNEAR", "STNEAR", "NearX", "LINEAR"])


pools = ref_data["top_pools"]["df"].copy()
pools["Current TVL"] = pd.to_numeric(pools.tvl)
pools["24h Volume"] = pd.to_numeric(pools.volume24hinUSD)
get_pair = partial(get_pair_from_token_id, df=ft)
pools["Pair"] = pools.token_account_ids.apply(get_pair)
pools = pools[
    [
        "Pair",
        "pool_id",
        "token_account_ids",
        "total_fee",
        "Current TVL",
        "24h Volume",
    ]
]

c1, c2 = st.columns([1, 3])

analysis_type = c1.radio(
    "Which do you want to see?", ["Tokens", "Pools"], horizontal=True
)
metric = c1.radio("Metric", ["Current TVL", "24h Volume"], horizontal=True)
num = c1.slider("Number of Tokens / Pools:", 1, 100, 20)

if analysis_type == "Tokens":
    df = tokens
    var = "symbol"
if analysis_type == "Pools":
    df = pools
    var = "Pair"

c1.metric(
    "Total Pools",
    f"{ref_data['pool_number']['data']} ({ref_data['active_pool_number']['data']} active)",
)
c1.metric(
    "Total Pairs",
    f"{len(ref_data['all_pairs']['df']):,}",
)
c2.altair_chart(
    alt_symbol_bar(df, metric, num, analysis_type, var), use_container_width=True
)

st.write(
    """We can now take a look at individual pools, and get some further information on the NEAR citizens using them."""
)
c1, c2 = st.columns([1, 3])
pool_id = c1.selectbox(
    "Choose a pool",
    pools["pool_id"],
    format_func=lambda x: f"{x}: {pools[pools.pool_id == x]['Pair'].values[0]}",
)
pool_df = pools[pools.pool_id == pool_id]
pool_name = f"{pool_id}: {pool_df.iloc[0]['Pair']}"
lp_info = get_lp(pool_id)
lp_created_at = lp_info["pool"]["createdAt"]
lp_shares = pd.DataFrame(lp_info["pool"]["shares"])
lp_shares["Value (USD)"] = pool_df.iloc[0]["Current TVL"] * pd.to_numeric(
    lp_shares.prct
)

c1.metric(
    "Curent Total Value Locked (TVL)",
    f"${pool_df.iloc[0]['Current TVL']:,.0f}",
)
c1.metric(
    "Trade Volume, past 24 hours",
    f"${pool_df.iloc[0]['24h Volume']:,.0f}",
)
c2.altair_chart(alt_lp_bar(lp_shares, pool_name), use_container_width=True)

st.write(
    """We can explore how users deposit and withdraw into pools here.

Choose whether you want to look at:
- Liquidity action by Pool or Token
- How this changes over time (By Date) for a selected Pool or Token, or look at the overal Daily Metric for the top Pool/Token
- A specific metric: Total Actions (withdraw/deposit transactions), average amount per Tx per day, or total amount per day
"""
)
c1, c2 = st.columns([1, 3])
pool_deposit_withdraws = get_pool_deposit_withdraws(dfs, ft)
deposit_withdraws_subset = pool_deposit_withdraws.copy()[
    [
        "Date",
        "POOL_ID",
        "Symbol",
        "name",
        "ACTION_TYPE",
        "price",
        "Total Actions",
        "Total Amount",
        "Average Amount",
        "Amount (USD)",
        "Average Amount (USD)",
    ]
]
deposit_withdraws_subset["Total Actions"] = pd.to_numeric(
    deposit_withdraws_subset["Total Actions"]
)
deposit_withdraws_subset["POOL_ID"] = pd.to_numeric(deposit_withdraws_subset["POOL_ID"])

analysis_type = c1.radio(
    "How do you want to view the data?", ["By Pool", "By Token"], horizontal=True
)
grouping = c1.radio("Grouping", ["By Date", "Daily Average", "Daily Total"])
metric = c1.radio(
    "Metric",
    [
        "Total Actions",
        "Average Amount",
        "Total Amount",
        "Amount (USD)",
        "Average Amount (USD)",
    ],
)


if grouping == "By Date":
    date_range = c1.radio(
        "Date range:",
        [
            "All dates",
            7,
            30,
            60,
            90,
        ],
        format_func=lambda x: x if type(x) == str else f"{x}d",
        key="pool_deposits",
    )
    if analysis_type == "By Pool":
        selection = c1.selectbox(
            "Choose a pool",
            sorted(pd.to_numeric(deposit_withdraws_subset["POOL_ID"]).unique()),
            key="pool_deposits",
        )
    if analysis_type == "By Token":
        selection = c1.selectbox(
            "Choose a token",
            deposit_withdraws_subset["Symbol"].unique(),
            format_func=lambda x: f"{deposit_withdraws_subset[deposit_withdraws_subset['Symbol'] == x]['name'].values[0]} ({x})",
            key="pool_deposits",
        )
else:
    date_range = None
    selection = c1.slider(
        "Number of Tokens / Pools:",
        1,
        100,
        20,
        key="pool_deposits",
    )


c2.altair_chart(
    alt_pool_liquidity(
        deposit_withdraws_subset, analysis_type, metric, grouping, date_range, selection
    ),
    use_container_width=True,
)


st.subheader("Token prices")
"""The people of NEAR are like the rest of us, and are concerned about the price of the tokens.

Let's look at the price of our favorite tokens.
"""

tab1, tab2, tab3, tab4 = st.tabs(
    ["All tokens", "NEAR tokens", "Stablecoins", "Bitcoin tokens"]
)

date_range_1 = tab1.radio(
    "Date range for charts:",
    ["All", 7, 30, 60, 90],
    format_func=lambda x: x if type(x) == str else f"{x}d",
    horizontal=True,
    key="price_date_range_1",
)
date_range_2 = tab2.radio(
    "Date range for charts:",
    ["All", 7, 30, 60, 90],
    format_func=lambda x: x if type(x) == str else f"{x}d",
    horizontal=True,
    key="price_date_range_2",
)
date_range_3 = tab3.radio(
    "Date range for charts:",
    ["All", 7, 30, 60, 90],
    format_func=lambda x: x if type(x) == str else f"{x}d",
    horizontal=True,
    key="price_date_range_3",
)
date_range_4 = tab4.radio(
    "Date range for charts:",
    ["All", 7, 30, 60, 90],
    format_func=lambda x: x if type(x) == str else f"{x}d",
    horizontal=True,
    key="price_date_range_4",
)

token_list = tab1.selectbox("Choose which token to chart", tokens.symbol.values, 2)
near_list = tokens[tokens.is_near].symbol.to_list()
stable_list = tokens[tokens.is_stablecoin].symbol.to_list()
btc_list = tokens[tokens.is_btc].symbol.to_list()

price_chart = alt_date_line(
    [token_list],
    tokens,
    "price",
    title="Price (USD)",
    date_range=date_range_1,
    color_col="Symbol",
    val_format=",.2f",
)
near_chart = alt_date_line(
    near_list,
    tokens,
    "price",
    title="Price (USD)",
    date_range=date_range_2,
    color_col="Symbol",
    val_format=",.2f",
)
stable_chart = alt_date_line(
    stable_list,
    tokens,
    "price",
    title="Price (USD)",
    date_range=date_range_3,
    color_col="Symbol",
    val_format=",.2f",
    is_stable=True,
)
btc_chart = alt_date_line(
    btc_list,
    tokens,
    "price",
    title="Price (USD)",
    date_range=date_range_4,
    color_col="Symbol",
    val_format=",.2f",
)

tab1.altair_chart(price_chart, use_container_width=True)
tab2.altair_chart(near_chart, use_container_width=True)
tab3.altair_chart(stable_chart, use_container_width=True)
tab4.altair_chart(btc_chart, use_container_width=True)


st.subheader("Farms")
st.write(
    """
Farms allow users to make their money earn additonal rewards by staking their liquidity tokens.

Here is a high level overview of how users claim rewards, and what tokens are given out as rewards. Let's look at:
- Number of Farms and Farmers actively using Ref
- The number of reward claims per day, broken down by pool
- The amount of reward claims per day (in USD), broken down by token
- The top 20 wallets claiming rewards, broken down by token
"""
)
latest_farm = ref_data["last_farming_stats"]["df"].iloc[0]
all_farms = ref_data["all_farms"]["df"].copy()

reward_claims = dfs["reward_claims"].copy()
reward_claims["Reward Claims"] = pd.to_numeric(reward_claims["Reward Claims"])
reward_claims["Farm ID"] = reward_claims.FARM_ID.str.split("#", expand=True)[0]
reward_claims = (
    reward_claims.groupby(["Farm ID", "Date"])["Reward Claims"].sum().reset_index()
)
total_claims = (
    reward_claims.groupby("Date")["Reward Claims"]
    .sum()
    .reset_index()
    .rename(columns={"Reward Claims": "Total Claims"})
)
reward_claims = reward_claims.merge(total_claims, on="Date")

rewards_by_token = get_rewards_by_token(dfs, ft)


reward_claims_by_user = dfs["reward_claims_by_user"]
token_conversions = get_decimals(reward_claims_by_user.TOKEN_ID, ft)
reward_claims_by_user = reward_claims_by_user.merge(
    token_conversions,
    left_on="TOKEN_ID",
    right_on="token_account_id",
)
reward_claims_by_user["Raw Total Amount"] = pd.to_numeric(
    reward_claims_by_user["Total Amount"]
)
reward_claims_by_user["Total Amount"] = (
    reward_claims_by_user["Raw Total Amount"]
    / reward_claims_by_user["conversion_factor"]
)


c1, c2 = st.columns([1, 3])
c1.metric("Total Farms", latest_farm.farm_count)
c1.metric("Total Farmers", f"{int(latest_farm.farmer_count):,}")
c1.metric("Overall Farming Reward Rate", f"{int(latest_farm.reward_count)}%")

c2.altair_chart(alt_farm_reward_claims(reward_claims), use_container_width=True)

c1, c2 = st.columns([1, 3])
date_range = c1.radio(
    "Date range:",
    ["All", 7, 30, 60, 90],
    format_func=lambda x: x if type(x) == str else f"{x}d",
    horizontal=True,
    key="reward_claims",
)

c2.altair_chart(
    alt_farm_date_line(rewards_by_token, "Amount (USD)", date_range, val_format=".2f"),
    use_container_width=True,
)

c1, c2 = st.columns([1, 3])
token_name = c1.selectbox(
    "Choose a Token",
    sorted(reward_claims_by_user.name.unique()),
    format_func=lambda x: f"{x} ({reward_claims_by_user[reward_claims_by_user.name == x]['symbol'].values[0]})",
)
token_df = reward_claims_by_user[reward_claims_by_user.name == token_name]
c2.altair_chart(
    alt_reward_bar(token_df, token_name),
    use_container_width=True,
)

st.write(
    """
Let's look at some stats for specific farms:
- The percent ownership of the liquidity in the farm (top 20 wallet addresses)
"""
)
c1, c2 = st.columns([1, 3])
farm_id = c1.selectbox(
    "Choose a Farm",
    pd.unique(sorted(all_farms["seed_id"])),
    # format_func=lambda x: f"{x}: {pools[pools.pool_id == x]['Pair'].values[0]}",
    key="farm",
)
c1.write(
    f"[Click here to view the farm](https://app.ref.finance/v2farms/{farm_id.split('@')[-1]}-r)"
)

farm_df = all_farms[all_farms.farm_id == farm_id]
# farm_name = f"{pool_id}: {farm_df.iloc[0]['Pair']}"
farm_info = get_accounts(farm_id)
farm_accounts = pd.DataFrame(farm_info["accounts"])
farm_accounts = pd.concat(
    [farm_accounts, pd.json_normalize(farm_accounts["accounts"])], axis=1
)
c2.altair_chart(alt_farm_bar(farm_accounts, farm_id), use_container_width=True)

for k, v in ref_data.items():
    st.subheader(k)
    try:
        v["df"]
    except:
        v["data"]

dfs
