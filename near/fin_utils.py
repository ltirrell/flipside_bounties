from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Iterable, Union

import altair as alt
import pandas as pd
import requests
import streamlit as st

# from shroomdk import ShroomDK

# fs_key = st.secrets["flipside"]["api_key"]
# fig_key = st.secrets["figment"]["api_key"]
# fig_url = f"https://near--indexer.datahub.figment.io/apikey/{fig_key}"
# sdk = ShroomDK(fs_key)

__all__ = [
    # Variables/info/schema
    "query_information",
    "get_pair_from_token_id",
    "get_price_df",
    "get_decimals",
    # Data
    "get_ref_data",
    "get_lp",
    "get_price",
    "get_accounts",
    "load_data",
    "get_rewards_by_token",
    "get_pool_deposit_withdraws",
    # Charting
    "alt_date_area",
    "alt_date_line",
    "alt_symbol_bar",
    "alt_lp_bar",
    "alt_farm_claims_bar",
    "alt_farm_bar",
    "alt_farm_reward_claims",
    "alt_farm_date_line",
    "alt_reward_bar",
    "alt_pool_liquidity",
    "alt_stable_user",
]


# Variables/info/schema
query_information = {
    "Ref Reward Claims": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/d2c62cd6-483a-4a8f-8640-609cb06be5f1/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/d2c62cd6-483a-4a8f-8640-609cb06be5f1",
        "short_name": "reward_claims",
    },
    "Ref Reward Claims by Token": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/7f9b4890-5ad2-44c0-b596-e9f60650d927/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/7f9b4890-5ad2-44c0-b596-e9f60650d927",
        "short_name": "reward_claims_by_token",
    },
    "Ref Reward Claims by Top Users": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/7d7ab9bc-66a2-4c9d-ba0a-445d43c7c558/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/7d7ab9bc-66a2-4c9d-ba0a-445d43c7c558",
        "short_name": "reward_claims_by_user",
    },
    # "Ref Farm Deposits and Withdraws": {  # Not using for now
    #     "api": "https://node-api.flipsidecrypto.com/api/v2/queries/dc9e9c76-d999-4fb8-aa90-6f73cc544117/data/latest",
    #     "query": "https://app.flipsidecrypto.com/velocity/queries/dc9e9c76-d999-4fb8-aa90-6f73cc544117",
    #     "short_name": "farm_deposit_withdraws",
    # },
    "Ref Pool Deposits and Withdraws": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/b2c7877e-f140-4085-bb09-4949292843a2/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/b2c7877e-f140-4085-bb09-4949292843a2",
        "short_name": "pool_deposit_withdraws",
    },
    "NEAR Stablecoin Transactions": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/59a1b7b6-84ad-4848-9788-a9a09f745e2c/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/59a1b7b6-84ad-4848-9788-a9a09f745e2c",
        "short_name": "stablecoin_tx",
    },
    "NEAR Stablecoins by Top Users": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/7d475d16-cdbb-4073-aefb-9bc980056677/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/7d475d16-cdbb-4073-aefb-9bc980056677",
        "short_name": "stablecoin_top_users",
    },
}


# Utilities
def convert_to_near(yNEAR: Union[str, Iterable]) -> float:
    if type(yNEAR) == str:
        return int(yNEAR) / 10**24
    else:
        return [int(x) / 10**24 for x in yNEAR]


def get_pair_from_token_id(x, df):
    symbols = []
    for y in x:
        symbol = df[df["token_account_id"] == y].symbol.values[0]
        symbols.append(symbol)
    return "-".join(symbols)


def get_price_df(token_list, df):
    token_ids = df.loc[df.symbol.isin(token_list), "token_id"].values
    price_dfs = []
    for x, y in zip(token_ids, token_list):
        df = get_price(x).copy()
        df["Token ID"] = x
        df["Symbol"] = y
        df["price"] = pd.to_numeric(df.price)
        price_dfs.append(df)
    price_df = pd.concat(price_dfs)
    return price_df


def get_decimals(token_ids: pd.Series, ft: pd.DataFrame, precorrection=18):
    df = ft[ft.token_account_id.isin(token_ids)][
        ["name", "symbol", "token_account_id", "decimals"]
    ]
    df["decimals_raw"] = pd.to_numeric(df["decimals"])
    if precorrection:
        df["decimals"] = df["decimals_raw"] - precorrection
    else:
        df["decimals"] = df["decimals_raw"]
    df["conversion_factor"] = 10 ** (df.decimals.apply(float))
    return df


# Data
@st.cache(ttl=3600)
def get_ref_data() -> Mapping[
    str, Mapping[str, Union[pd.DataFrame, str, int, dict, list]]
]:
    ref_data = {
        "volume_variation_24h": {
            "url": "https://api.stats.ref.finance/api/24h-volume-variation",
        },
        "ft": {
            "url": "https://api.stats.ref.finance/api/ft",
        },
        "historical_tvl_all": {
            "url": "https://api.stats.ref.finance/api/historical-tvl?period=730",
        },
        "last_tvl": {
            "url": "https://api.stats.ref.finance/api/last-tvl",
        },
        "top_pools": {
            "url": "https://api.stats.ref.finance/api/top-pools",
        },
        "top_tokens": {
            "url": "https://api.stats.ref.finance/api/top-tokens",
        },
        "volume_24h_all": {
            "url": "https://api.stats.ref.finance/api/volume24h?period=730",
        },
        "pool_number": {
            "url": "https://api.stats.ref.finance/api/pool-number",
        },
        "active_pool_number": {
            "url": "https://api.stats.ref.finance/api/active-pool-number",
        },
        "all_pairs": {
            "url": "https://api.stats.ref.finance/api/all-pairs",
        },
        "all_farms": {
            "url": "https://api.stats.ref.finance/api/all-farms",
        },
        "average_farming_rate": {
            "url": "https://api.stats.ref.finance/api/average-farming-rate",
        },
        "last_farming_stats": {
            "url": "https://api.stats.ref.finance/api/last-farming-stats",
        },
        "pools": {
            "url": "https://api.stats.ref.finance/api/pools",
        },
        "mcap": {
            "url": "https://api.stats.ref.finance/api/marketcap",
        },
        "seeds": {
            "url": "https://api.stats.ref.finance/api/seeds",
        },
        "ref_holders": {
            "url": "https://api.stats.ref.finance/api/ref-holders",
        },
    }

    for k, v in ref_data.items():
        r = requests.get(v["url"])
        ref_data[k]["data"] = r.json()
    for k, v in ref_data.items():
        try:
            ref_data[k]["df"] = pd.DataFrame(v["data"])
        except ValueError:
            pass
    return ref_data


@st.cache(ttl=3600 * 12)
def get_lp(pool_id: int) -> dict:
    url = f"https://api.stats.ref.finance/api/pool/{pool_id}/lp"
    r = requests.get(url)
    data = r.json()
    return data


@st.cache(ttl=3600 * 12, allow_output_mutation=True)
def get_price(token_id: str) -> pd.DataFrame:
    url = f"https://api.stats.ref.finance/api/price-data?tokenId={token_id}"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data)
    return df


@st.cache(ttl=3600 * 12)
def get_accounts(seed: str) -> dict:
    url = f"https://api.stats.ref.finance/api/seed/{seed}/accounts"
    r = requests.get(url)
    data = r.json()
    return data


@st.cache(ttl=(3600 * 12), allow_output_mutation=True)
def load_data(
    query_information: Mapping[str, Mapping[str, str]] = query_information
) -> Mapping[str, pd.DataFrame]:
    """Load data from Query information

    Parameters
    ----------
    query_information : Dict, optional
        Information containing URLs to data, see default for how to set this up, by default query_information

    Returns
    -------
    Dict
        Dict of dataframes
    """

    dfs = {}

    for v in query_information.values():
        df = pd.read_json(v["api"], dtype=str)
        dfs[v["short_name"]] = df

    return dfs


@st.cache(ttl=(3600 * 12))
def get_rewards_by_token(dfs, ft):
    rewards_by_token = dfs["reward_claims_by_token"]
    token_conversions = get_decimals(rewards_by_token.TOKEN_ID, ft)
    rewards_by_token = rewards_by_token.merge(
        token_conversions,
        left_on="TOKEN_ID",
        right_on="token_account_id",
    )
    rewards_by_token["token_id"] = rewards_by_token.TOKEN_ID
    rewards_by_token["Date"] = pd.to_datetime(rewards_by_token.Date)
    rewards_by_token["Raw Total Amount"] = pd.to_numeric(
        rewards_by_token["Total Amount"]
    )
    rewards_by_token["Total Amount"] = (
        rewards_by_token["Raw Total Amount"] / rewards_by_token["conversion_factor"]
    )
    price_df = get_price_df(rewards_by_token.symbol.unique(), rewards_by_token)
    price_df["Date"] = pd.to_datetime(
        pd.to_datetime(price_df.date).dt.strftime("%Y-%m-%d")
    )
    rewards_by_token = rewards_by_token.merge(
        price_df[["price", "Symbol", "Date"]],
        left_on=["symbol", "Date"],
        right_on=["Symbol", "Date"],
        how="left",
    )
    rewards_by_token["Amount (USD)"] = (
        rewards_by_token["Total Amount"] * rewards_by_token["price"]
    )
    return rewards_by_token


@st.cache(ttl=(3600 * 12))
def get_pool_deposit_withdraws(dfs, ft):
    pool_deposit_withdraws = dfs["pool_deposit_withdraws"]

    token_conversions = get_decimals(pool_deposit_withdraws.TOKEN, ft)
    pool_deposit_withdraws = pool_deposit_withdraws.merge(
        token_conversions,
        left_on="TOKEN",
        right_on="token_account_id",
    )
    pool_deposit_withdraws["token_id"] = pool_deposit_withdraws.TOKEN
    pool_deposit_withdraws["Date"] = pd.to_datetime(pool_deposit_withdraws.Date)
    pool_deposit_withdraws["Raw Total Amount"] = pd.to_numeric(
        pool_deposit_withdraws["Total Token Amount"]
    )
    pool_deposit_withdraws["Total Amount"] = (
        pool_deposit_withdraws["Raw Total Amount"]
        / pool_deposit_withdraws["conversion_factor"]
    )
    pool_deposit_withdraws["Raw Average Amount"] = pd.to_numeric(
        pool_deposit_withdraws["Average Average Token Amount"]
    )
    pool_deposit_withdraws["Average Amount"] = (
        pool_deposit_withdraws["Raw Average Amount"]
        / pool_deposit_withdraws["conversion_factor"]
    )

    price_df = get_price_df(
        pool_deposit_withdraws.symbol.unique(), pool_deposit_withdraws
    )
    price_df["Date"] = pd.to_datetime(
        pd.to_datetime(price_df.date).dt.strftime("%Y-%m-%d")
    )
    pool_deposit_withdraws = pool_deposit_withdraws.merge(
        price_df[["price", "Symbol", "Date"]],
        left_on=["symbol", "Date"],
        right_on=["Symbol", "Date"],
        how="left",
    )
    pool_deposit_withdraws["Amount (USD)"] = (
        pool_deposit_withdraws["Total Amount"] * pool_deposit_withdraws["price"]
    )
    pool_deposit_withdraws["Average Amount (USD)"] = (
        pool_deposit_withdraws["Average Amount"] * pool_deposit_withdraws["price"]
    )
    return pool_deposit_withdraws


# Charting
def alt_date_area(df, value, title, date_range, val_format="", color="black"):
    if type(date_range) == int:
        df = df.iloc[-date_range:]
    chart = (
        alt.Chart(df)
        .mark_area(color=color)
        .encode(
            x=alt.X("yearmonthdate(date)", title="Date"),
            y=alt.Y(f"{value}:Q", title=title),
            tooltip=[
                alt.Tooltip("yearmonthdate(date)", title="Date"),
                alt.Tooltip(value, title=title, format=val_format),
            ],
        )
    ).interactive()
    return chart


def alt_date_line(
    token_list,
    base_df,
    value,
    title,
    date_range,
    val_format="",
    color_col="token",
    is_stable=False,
):
    df = get_price_df(token_list, base_df)
    df = df.sort_values(by="date")
    if type(date_range) == int:
        df = df.iloc[-date_range:]
    if is_stable:
        scale = alt.Scale(zero=False, domain=[0.8, 1.2], nice=False)
    else:
        scale = alt.Scale(zero=False, nice=False)

    base = alt.Chart(df).encode(
        x=alt.X("yearmonthdate(date):T", axis=alt.Axis(title=""))
    )
    columns = sorted(df[color_col].unique())
    selection = alt.selection_single(
        fields=["date"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout",
    )
    lines = base.mark_line().encode(
        y=alt.Y(
            f"{value}:Q",
            title=title,
            scale=scale,
        ),
        color=alt.Color(color_col, title=color_col.title()),
    )
    points = lines.mark_point().transform_filter(selection)
    rule = (
        base.transform_pivot(color_col, value=value, groupby=["date"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip("yearmonthdate(date):T", title="Date")]
            + [
                alt.Tooltip(
                    c,
                    type="quantitative",
                    format=val_format,
                )
                for c in columns
            ],
        )
        .add_selection(selection)
    )

    chart = lines + points + rule
    return chart.properties(height=500).interactive()


def alt_symbol_bar(df, metric, num, analysis_type, var):
    df = df.sort_values(by=metric, ascending=False).iloc[:num].reset_index(drop=True)

    tooltips = [
        alt.Tooltip(var, title=var.title()),
        alt.Tooltip("24h Volume", title="24h Volume ($)", format=",.0f"),
        alt.Tooltip("Current TVL", title="Current TVL ($)", format=",.0f"),
    ]
    if var == "Pair":
        tooltips.append(alt.Tooltip("pool_id", title="Pool ID"))
    chart = (
        alt.Chart(df, title=f"Top {analysis_type} by {metric}")
        .mark_bar()
        .encode(
            x=alt.X(var, title=None, sort="-y"),
            y=alt.Y(
                metric,
                title=f"{metric} ($)",
            ),
            color=alt.Color(
                var,
                sort=alt.EncodingSortField(metric, op="max", order="descending"),
                scale=alt.Scale(
                    scheme="sinebow",
                ),
            ),
            tooltip=tooltips,
        )
        .interactive()
        .properties(height=500)
    )

    return chart


def alt_lp_bar(df, pool_name):
    chart = (
        alt.Chart(df, title=pool_name)
        .mark_bar()
        .encode(
            x=alt.X("account", title=None, sort="-y"),
            y=alt.Y(
                "prct:Q", title=f"Percent of total liquidity", axis=alt.Axis(format="%")
            ),
            color=alt.Color(
                "account",
                legend=alt.Legend(title="Account"),
                sort=alt.EncodingSortField("prct", op="max", order="descending"),
                scale=alt.Scale(
                    scheme="tableau20",
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "account",
                    title="Account",
                ),
                alt.Tooltip("prct", title="Percent of liquidity", format=".3%"),
                alt.Tooltip("Value (USD)", format=",.0f"),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_farm_claims_bar(df):
    chart = (
        alt.Chart(df, title=f"Reward Claims per Day")
        .mark_bar()
        .encode(
            x=alt.X("Date:T", title=None, sort="-y"),
            y=alt.Y(
                "Reward Claims",
            ),
            color=alt.Color(
                "Farm ID",
                scale=alt.Scale(
                    scheme="sinebow",
                ),
            ),
            tooltip=[
                alt.Tooltip("Date:T"),
                alt.Tooltip("Farm ID"),
                alt.Tooltip("Reward Claims"),
                alt.Tooltip("Total Claims"),
            ],
        )
        .interactive()
        .properties(height=500, width=1000)
    )
    return chart


def alt_farm_bar(df, pool_name):
    chart = (
        alt.Chart(df, title=pool_name)
        .mark_bar()
        .encode(
            x=alt.X("account", title=None, sort="-y"),
            y=alt.Y("prct:Q", title=f"Percent of farm", axis=alt.Axis(format="%")),
            color=alt.Color(
                "account",
                legend=alt.Legend(title="Account"),
                sort=alt.EncodingSortField("prct", op="max", order="descending"),
                scale=alt.Scale(
                    scheme="tableau20",
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "account",
                    title="Account",
                ),
                alt.Tooltip("prct", title="Percent of farm", format=".3%"),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_farm_reward_claims(df):
    chart = (
        alt.Chart(df, title=f"Reward Claims per Day")
        .mark_bar()
        .encode(
            x=alt.X("Date:T", title=None, sort="-y"),
            y=alt.Y(
                "Reward Claims",
            ),
            color=alt.Color(
                "Farm ID",
                scale=alt.Scale(
                    scheme="sinebow",
                ),
            ),
            tooltip=[
                alt.Tooltip("Date:T"),
                alt.Tooltip("Farm ID"),
                alt.Tooltip("Reward Claims"),
                alt.Tooltip("Total Claims"),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_farm_date_line(
    df,
    value,
    date_range,
    val_format="",
    color_col="name",
):
    df = df.sort_values(by="Date")
    if type(date_range) == int:
        today = datetime.today()
        date_diff = pd.to_datetime(today - timedelta(days=date_range))
        df = df[df.Date >= date_diff]

    base = alt.Chart(df, title="Reward Amount Claimed per Day (in USD)").encode(
        x=alt.X("yearmonthdate(Date):T", axis=alt.Axis(title=""))
    )
    columns = (
        df.groupby(color_col)[value].mean().sort_values(ascending=False).index.to_list()
    )
    selection = alt.selection_single(
        fields=["Date"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout",
    )
    lines = base.mark_line().encode(
        y=alt.Y(
            f"{value}:Q",
        ),
        color=alt.Color(
            color_col,
            title=color_col.title(),
            sort=alt.EncodingSortField("Amount (USD)", op="max", order="descending"),
        ),
    )
    points = lines.mark_point().transform_filter(selection)
    rule = (
        base.transform_pivot(color_col, value=value, groupby=["Date"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip("yearmonthdate(Date):T", title="Date")]
            + [
                alt.Tooltip(
                    c,
                    type="quantitative",
                    format=val_format,
                )
                for c in columns
            ],
        )
        .add_selection(selection)
    )

    chart = lines + points + rule
    return chart.properties(height=500).interactive()


def alt_reward_bar(df, token_name):
    chart = (
        alt.Chart(df, title=f"Top 20 claimers: {token_name}")
        .mark_bar()
        .encode(
            x=alt.X("Wallet Address", title=None, sort="-y"),
            y=alt.Y(
                "Total Amount",
                title=f"Total Amount Claimed (tokens)",
            ),
            color=alt.Color(
                "Wallet Address",
                legend=alt.Legend(title="Account"),
                sort=alt.EncodingSortField(
                    "Total Amount", op="max", order="descending"
                ),
                scale=alt.Scale(
                    scheme="tableau20",
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "Wallet Address",
                    title="Account",
                ),
                alt.Tooltip(
                    "name",
                    title="Token Name",
                ),
                alt.Tooltip(
                    "symbol",
                    title="Symbol",
                ),
                alt.Tooltip("Total Amount", title="Total Amount Claimed", format=".2f"),
            ],
        )
        .interactive()
        .properties(height=500)
    )
    return chart


def alt_pool_liquidity(df, analysis_type, metric, grouping, date_range, s):
    if analysis_type == "By Pool":
        col = "POOL_ID"
    if analysis_type == "By Token":
        col = "Symbol"
    if grouping == "By Date":
        df = df.sort_values(by="Date")
        if type(date_range) == int:
            today = datetime.today()
            date_diff = pd.to_datetime(today - timedelta(days=date_range))
            df = df[df.Date >= date_diff]
        df = df[df[col] == s]
        if analysis_type == "By Pool":
            grouped_df = (
                df.groupby(["Date", "ACTION_TYPE"])[metric].mean().reset_index()
            )
            grouped_df["Symbol"] = "-".join(df.Symbol.unique())
            grouped_df["name"] = f"{'/ '.join(df.Symbol.unique())} LP"
        else:
            grouped_df = df
        grouped_df[metric] = grouped_df.apply(
            lambda x: x[metric] * -1 if x.ACTION_TYPE == "remove" else x[metric], axis=1
        )
        base = alt.Chart(
            grouped_df, title=f"{metric}, {grouping}, {analysis_type}: {s}"
        ).encode(x=alt.X("yearmonthdate(Date):T", axis=alt.Axis(title="")))
        columns = (
            df.groupby("ACTION_TYPE")[metric]
            .mean()
            .sort_values(ascending=False)
            .index.to_list()
        )
        selection = alt.selection_single(
            fields=["Date"],
            nearest=True,
            on="mouseover",
            empty="none",
            clear="mouseout",
        )
        lines = base.mark_line(interpolate="monotone").encode(
            y=alt.Y(
                f"{metric}:Q",
            ),
            color=alt.Color(
                "ACTION_TYPE",
                title="Action Type",
                # sort=alt.EncodingSortField("Amount (USD)", op="max", order="descending"),
            ),
        )
        points = lines.mark_point().transform_filter(selection)
        rule = (
            base.transform_pivot(
                "ACTION_TYPE", value=metric, groupby=["Date", "Symbol", "name"]
            )
            .mark_rule()
            .encode(
                opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
                tooltip=[
                    alt.Tooltip("yearmonthdate(Date):T", title="Date"),
                    alt.Tooltip("Symbol"),
                    alt.Tooltip("name"),
                ]
                + [
                    alt.Tooltip(
                        c,
                        type="quantitative",
                    )
                    for c in columns
                ],
            )
            .add_selection(selection)
        )

        chart = lines + points + rule
    else:
        if grouping == "Daily Average":
            agg = "mean"
        if grouping == "Daily Total":
            agg = "sum"
        items = df.groupby(col)[metric].agg(agg).sort_values(ascending=False)[:s].index
        grouped_df = (
            df[df[col].isin(items)]
            .groupby([col, "ACTION_TYPE", "Symbol", "name"])[metric]
            .agg(agg)
            .reset_index()
        )
        grouped_df[metric] = grouped_df.apply(
            lambda x: x[metric] * -1 if x.ACTION_TYPE == "remove" else x[metric], axis=1
        )
        chart = (
            alt.Chart(grouped_df, title=f"{metric}, {grouping}, {analysis_type}")
            .mark_bar()
            .encode(
                x=alt.X(
                    f"{col}:N",
                    title=None,
                ),
                y=alt.Y(
                    metric,
                ),
                color=alt.Color(
                    "ACTION_TYPE",
                    legend=alt.Legend(title="Liquidity action type"),
                    scale=alt.Scale(
                        scheme="tableau20",
                    ),
                ),
                tooltip=[
                    alt.Tooltip(col),
                    alt.Tooltip(metric),
                    alt.Tooltip("Symbol"),
                    alt.Tooltip("name"),
                    alt.Tooltip("ACTION_TYPE", title="Liquidity Action"),
                ],
            )
        )
    return chart.interactive().properties(height=800)


def alt_stable_user(df):
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Address", sort="-y"),
            y="Total Amount",
            color=alt.Color(
                "Address",
                sort=alt.EncodingSortField(
                    "Total Amount", op="max", order="descending"
                ),
            ),
            tooltip=[
                alt.Tooltip("Symbol"),
                alt.Tooltip("Address"),
                alt.Tooltip("Total Amount"),
            ],
        )
        .interactive()
        .properties(height=500)
    )

    return chart
