from collections.abc import Mapping
from datetime import datetime
import logging
from typing import Iterable, Union

import altair as alt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from shroomdk import ShroomDK

fs_key = st.secrets["flipside"]["api_key"]
fig_key = st.secrets["figment"]["api_key"]
fig_url = f"https://near--indexer.datahub.figment.io/apikey/{fig_key}"
sdk = ShroomDK(fs_key)

__all__ = [
    "get_blocktimes",
    "get_status",
    "get_blocks",
    "get_epochs",
    "get_validators",
    "get_validator_epochs",
    "get_account_info",
    "query_information",
    "load_data",
    "validator_column_mappings",
    "alt_rank_bar",
    "gini",
    "get_fs_validator_data",
    "alt_lines_bar",
    "fig_key",
]


def convert_to_near(yNEAR: Union[str, Iterable]) -> float:
    if type(yNEAR) == str:
        return int(yNEAR) / 10**24
    else:
        return [int(x) / 10**24 for x in yNEAR]


@st.cache(ttl=60)
def get_blocktimes() -> dict:
    url = f"{fig_url}/block_times"
    r = requests.get(url, params={"limit": 1000})
    data = r.json()
    return data


@st.cache(ttl=60)
def get_status() -> dict:
    url = f"{fig_url}/status"
    r = requests.get(url)
    data = r.json()
    return data


@st.cache(ttl=60)
def get_account_info(address: str) -> dict:
    url = f"{fig_url}/accounts/{address}"
    r = requests.get(url)
    data = r.json()
    data["Staked Amount (NEAR)"] = convert_to_near(data["staked_amount"])
    data["Balance (NEAR)"] = convert_to_near(data["amount"])
    return data


@st.cache(ttl=60)
def get_blocks() -> pd.DataFrame:
    url = f"{fig_url}/blocks"
    r = requests.get(url, params={"limit": 100})
    data = r.json()
    df = pd.DataFrame(data)
    df["Total Supply (NEAR)"] = convert_to_near(df.total_supply)
    return df


@st.cache(ttl=60)
def get_epochs() -> pd.DataFrame:
    url = f"{fig_url}/epochs"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data)
    return df


@st.cache(ttl=60)
def get_validators() -> pd.DataFrame:
    url = f"{fig_url}/validators"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data)
    df["Stake (NEAR)"] = convert_to_near(df.stake)
    df["last_time"] = pd.to_datetime(df["last_time"])
    # NOTE: this is causing issues for some reason, using one of 4 different methods, then returning the full dataset
    new_df = df.copy()[df.active == True].reset_index(drop=True)
    if len(new_df) == 0:
        # looking at today
        new_df = df.copy()[
            df.last_time >= pd.to_datetime(datetime.today(), utc=True)
        ].reset_index(drop=True)
    if len(new_df) == 0:
        # looking at 8 hrs before today
        td = pd.Timedelta(8, "h")
        new_df = df.copy()[
            df.last_time >= pd.to_datetime(datetime.today(), utc=True - td)
        ].reset_index(drop=True)
    if len(new_df) == 0:
        new_df = df.copy()
    return new_df


@st.cache(ttl=60)
def get_validator_epochs(validator: str) -> pd.DataFrame:
    url = f"{fig_url}/validators/{validator}/epochs"
    data = []
    r = requests.get(url)
    p1 = r.json()
    data.extend(p1["records"])
    pages = p1["pages"]
    if pages > 1:
        for i in range(2, pages + 1):
            r = requests.get(url, params={"page": i})
            p1 = r.json()
            data.extend(p1["records"])

    df = pd.DataFrame(data)
    df["Staking Balance (NEAR)"] = convert_to_near(df.staking_balance)
    return df


query_information = {
    "NEAR Number of Stakers": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/24f17c14-f117-4848-b0d4-1365dc8bc347/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/24f17c14-f117-4848-b0d4-1365dc8bc347",
        "short_name": "stakers",
    },
    "NEAR Validator Activity": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/bde5b887-df37-46a8-b21f-2f86fea03c4d/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/bde5b887-df37-46a8-b21f-2f86fea03c4d",
        "short_name": "validator_activity",
    },
}


@st.cache(ttl=(3600 * 6))
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
        df = pd.read_json(v["api"])
        dfs[v["short_name"]] = df

    return dfs


validator_column_mappings = {
    "account_id": {
        "title": "Governor",
    },
    "Stake (NEAR)": {
        "title": "Stake (NEAR)",
        "format": ",.2f",
    },
    "Proportion of Stake": {
        "title": "Proportion of total stake",
        "format": ".1%",
    },
    "start_time": {
        "title": "Start time",
    },
    "produced_blocks": {
        "title": "Blocks produced",
    },
    "efficiency": {
        "title": "Efficiency (%)",
        "format": ".1f",
    },
    "reward_fee": {
        "title": "Reward Fee (%)",
        "format": ".1f",
    },
    "AGE_DAY": {
        "title": "Age of governor (days)",
    },
    "NUMBER_OF_AGES": {
        "title": "Number of active epochs",
    },
    "NUMBER_OF_STAKERS": {"title": "Number of Stakers", "format": ","},
    "NUMBER_OF_UNSTAKERS": {"title": "Number of Unstakers", "format": ","},
    "LEFTOVER_SUPPORTERS": {
        "title": "Current Stakers (stakers - unstakers)",
        "format": ",",
    },
}


def alt_rank_bar(df: pd.DataFrame, value: str, ranks: tuple, mapping: dict):
    for k, v in mapping.items():
        if v["title"] == "Governor":
            x_val = k
    min_val, max_val = ranks
    title = mapping[value]["title"]
    if value == "start_time":
        v = f"yearmonthdate({value}):T"
        order = "ascending"
    else:
        v = value
        order = "descending"
    chart = (
        alt.Chart(df)
        .transform_window(
            rank=f"rank({value})", sort=[alt.SortField(value, order=order)]
        )
        .transform_filter(alt.datum.rank >= min_val and alt.datum.rank < max_val)
        .mark_bar()
        .encode(
            x=alt.X(x_val, title="Governor", sort="-y"),
            y=alt.Y(v, title=title),
            color=alt.Color(
                x_val,
                sort=alt.EncodingSortField(value, op="max", order=order),
                scale=alt.Scale(
                    scheme="tableau20",
                ),
                title="Governor",
            ),
            tooltip=[alt.Tooltip(k, **v) for k, v in mapping.items()],
        )
    ).interactive()
    return chart


def gini(array: np.array) -> float:
    """Calculate the Gini coefficient of a numpy array.

    From https://github.com/oliviaguest/gini

    based on bottom eq:
    http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    from:
    http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    """
    # All values are treated equally, arrays must be 1d:
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    # Values cannot be 0:
    array += 0.0000001
    # Values must be sorted:
    array = np.sort(array)
    # Index per array element:
    index = np.arange(1, array.shape[0] + 1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))


val_daily_info_query = """
--sql
select
  date_trunc('day', r.block_timestamp) as datetime,
  avg(split(
    regexp_substr(
      l.value, 'Contract total staked balance is [0-9]*'
    ),
    ' '
  ) [5] :: int / pow(10,24)) as "Stake (NEAR)",
  count(distinct b.block_hash) as "Blocks produced",
  sum(tx_count) as "Transactions Processed"
from 
  near.core.fact_receipts r
  full outer join near.core.fact_blocks b on r.block_timestamp::date = b.block_timestamp::date,
  lateral flatten(input => r.logs) l
where 
  r.receiver_id = '{validator}'
  and r.receipt_index=0
  and l.value::string ilike '%Contract total staked balance is%'
  and r.block_timestamp::date >= '2022-01-01'
  and b.block_author = '{validator}'
group by
  datetime
order by
  datetime
;
"""


@st.cache(ttl=12 * 60)
def get_fs_validator_data(
    validator,
    base_query=val_daily_info_query,
    cached=True,
):
    q = base_query.format(validator=validator)
    query_result_set = sdk.query(q, cached=cached)
    df = pd.DataFrame(query_result_set.rows, columns=query_result_set.columns)
    return df


def alt_lines_bar(
    df: pd.DataFrame,
    validator: str,
    date_col="DATETIME",
    date_type="yearmonthdate",
    variable_col="Stake (NEAR)",
    value_vars=["Blocks produced", "Transactions Processed"],
) -> alt.LayerChart:
    melt_df = df.melt(id_vars=[date_col, variable_col], value_vars=value_vars)
    base = alt.Chart(melt_df, title=f"Governance Track Record: {validator}").encode(
        x=alt.X(f"{date_type}({date_col}):T", axis=alt.Axis(title=""))
    )

    columns = sorted(melt_df["variable"].unique())
    selection = alt.selection_single(
        fields=[date_col],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout",
    )
    lines = base.mark_line(color="#004D40", interpolate="monotone").encode(
        y=alt.Y(variable_col),
    )
    bars = base.mark_bar(width=10).encode(
        y=alt.Y(
            "value",
            title="Voting Record",
        ),
        color=alt.Color(
            "variable",
            title="Voting Record",
            scale=alt.Scale(domain=columns, range=["#1E88E5", "#FFC107"]),
        ),
    )

    points = lines.mark_point().transform_filter(selection)
    rule = (
        base.transform_pivot(
            "variable", value="value", groupby=[date_col, variable_col]
        )
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip(f"{date_type}({date_col})", title="Date"),
                alt.Tooltip(variable_col, type="quantitative", format=",.2f"),
            ]
            + [
                alt.Tooltip(
                    c,
                    type="quantitative",
                    format=",",
                )
                for c in columns
            ],
        )
        .add_selection(selection)
    )
    chart = alt.layer((lines + points + rule), bars).resolve_scale(y="independent")
    return chart.interactive()
