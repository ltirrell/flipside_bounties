import altair as alt
from collections.abc import Mapping
import datetime
import pandas as pd
import streamlit as st


query_information = {
    "NEAR User Data": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/a20cb189-e613-4b4a-afb7-2d461243d6fc/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/a20cb189-e613-4b4a-afb7-2d461243d6fc",
        "short_name": "near_users",
        "blockchain": "NEAR",
    },
    "Ethereum User Data": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/45c7182e-83cd-4725-8d4f-f3c6228ef39d/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/45c7182e-83cd-4725-8d4f-f3c6228ef39d",
        "short_name": "eth_users",
        "blockchain": "Ethereum",
    },
    "Solana User Data": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/a6e1f91d-6ddb-4a1e-a4a3-cf5cbc8131c6/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/a6e1f91d-6ddb-4a1e-a4a3-cf5cbc8131c6",
        "short_name": "sol_users",
        "blockchain": "Solana",
    },
    "Polygon User Data": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/935f4942-6b68-42b0-b8f4-13abc00a0cc4/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/935f4942-6b68-42b0-b8f4-13abc00a0cc4",
        "short_name": "matic_users",
        "blockchain": "Polygon",
    },
    "Algorand User Data": {
        "api": "https://node-api.flipsidecrypto.com/api/v2/queries/90d54dd7-0488-4b14-89dc-47c756657d62/data/latest",
        "query": "https://app.flipsidecrypto.com/velocity/queries/90d54dd7-0488-4b14-89dc-47c756657d62",
        "short_name": "algo_users",
        "blockchain": "Algorand",
    },
}


@st.cache(ttl=(60 * 30))
def load_data(
    query_information: Mapping[str, Mapping[str, str]] = query_information
) -> pd.DataFrame:
    """Load data from Query information

    Parameters
    ----------
    query_information : Dict, optional
        Information containing URLs to data, see default for how to set this up, by default query_information

    Returns
    -------
    pd.DataFrame
        Dataframe of multi-blockchain data
    """

    dfs = []

    for v in query_information.values():
        df = pd.read_json(v["api"])
        df["blockchain"] = v["blockchain"]
        dfs.append(df)

    user_data = pd.concat(dfs).sort_values(by="datetime").reset_index(drop=True)
    user_data = user_data[user_data.datetime.dt.date < datetime.date.today()]
    return user_data


def alt_line_chart(data: pd.DataFrame, colname: str, log_scale=True) -> alt.Chart:
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
    base = alt.Chart(data).encode(
        x=alt.X("yearmonthdate(datetime):T", axis=alt.Axis(title=""))
    )
    columns = sorted(data.blockchain.unique())
    selection = alt.selection_single(
        fields=["datetime"],
        nearest=True,
        on="mouseover",
        empty="none",
        clear="mouseout",
    )
    lines = base.mark_line().encode(
        y=alt.Y(
            colname,
            axis=alt.Axis(title=colname.replace("_", " ").title()),
            scale=alt.Scale(type=scale),
        ),
        color=alt.Color(
            "blockchain:N",
        ),
    )
    points = lines.mark_point().transform_filter(selection)
    rule = (
        base.transform_pivot("blockchain", value=colname, groupby=["datetime"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip("datetime", title="Date")]
            + [alt.Tooltip(c, type="quantitative", format=",") for c in columns],
        )
        .add_selection(selection)
    )

    chart = lines + points + rule
    return chart.interactive()
