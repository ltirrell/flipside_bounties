import pandas as pd
import altair as alt
import streamlit as st

st.set_page_config(page_title="Solana Metrics of Success", page_icon="☀️")


def add_rolling_averages_to_melted_df(df):
    df[f"Daily Rolling Average"] = (
        df.groupby("variable")["value"].rolling(24).mean().reset_index(0, drop=True)
    )
    df[f"Weekly Rolling Average"] = (
        df.groupby("variable")["value"].rolling(24 * 7).mean().reset_index(0, drop=True)
    )
    return df


def format_selectbox_value(s):
    if s == "value":
        return "Raw Value"
    else:
        return s


# @st.cache
def load_data():
    df = pd.read_csv(
        "solana/data/tps.csv"
    )  # NOTE: needs to be relative to top-level dir of repo
    tps_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "TOTAL_TPS",
                "SUCCESFUL_TPS",
                "FAILED_TPS",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )
    fee_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "TOTAL_FEE",
                "SUCCESSFUL_FEE",
                "FAILED_FEE",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )
    avg_fee_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "AVG_TOTAL_FEE",
                "AVG_SUCCESSFUL_FEE",
                "AVG_FAILED_FEE",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )
    tx_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "TOTAL_TX",
                "SUCCESSFUL_TX",
                "FAILED_TX",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )
    compute_units_used_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "TOTAL_COMPUTE_UNITS_USED",
                "SUCCESSFUL_COMPUTE_UNITS_USED",
                "FAILED_COMPUTE_UNITS_USED",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )
    avg_compute_units_used_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "TOTAL_AVG_COMPUTE_UNITS_USED",
                "AVG_SUCCESSFUL_COMPUTE_UNITS_USED",
                "AVG_FAILED_COMPUTE_UNITS_USED",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )
    avg_compute_units_requested_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "TOTAL_AVG_COMPUTE_UNITS_REQUESTED",
                "AVG_SUCCESSFUL_COMPUTE_UNITS_REQUESTED",
                "AVG_FAILED_COMPUTE_UNITS_REQUESTED",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )
    avg_compute_units_proportion_df = add_rolling_averages_to_melted_df(
        df[
            [
                "DATETIME",
                "SUCCESS_RATE",
                "TOTAL_AVG_COMPUTE_UNITS_PROPORTION",
                "AVG_SUCCESSFUL_COMPUTE_UNITS_PROPORTION",
                "AVG_FAILED_COMPUTE_UNITS_PROPORTION",
            ]
        ].melt(id_vars=["DATETIME", "SUCCESS_RATE"]),
    )

    return (
        tps_df,
        fee_df,
        avg_fee_df,
        tx_df,
        compute_units_used_df,
        avg_compute_units_used_df,
        avg_compute_units_requested_df,
        avg_compute_units_proportion_df,
    )


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
    columns = sorted(data["variable"].unique())[::-1]
    clean_columns = [c.replace("_", " ").title() for c in columns]

    base = alt.Chart(data, title=clean_columns[0].replace("Total", "")).encode(
        x=alt.X("yearmonthdatehours(DATETIME):T", axis=alt.Axis(title=""))
    )

    data["variable"] = data["variable"].str.title()
    data["variable"] = data["variable"].str.replace("_", " ")

    selection = alt.selection_single(
        fields=["DATETIME"],
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
            "variable:N",
            scale=alt.Scale(
                domain=clean_columns, range=["#0b8fbf", "#14F195", "#9945FF"]
            ),
        ),
    )

    points = lines.mark_point().transform_filter(selection)
    rule = (
        base.transform_pivot("variable", value=colname, groupby=["DATETIME"])
        .mark_rule()
        .encode(
            opacity=alt.condition(selection, alt.value(0.3), alt.value(0)),
            tooltip=[alt.Tooltip("yearmonthdatehours(DATETIME)", title="Date")]
            + [
                alt.Tooltip(
                    c,
                    type="quantitative",
                    format=",",
                )
                for c in clean_columns
            ],
        )
        .add_selection(selection)
    )
    chart = lines + points + rule
    if success_rate:  # NOTE this doesn't work yet so leaving out for now
        pass
        # success = base.mark_line().encode(
        #     y=alt.Y("SUCCESS_RATE"),
        #     color=alt.Color(
        #         "variable:N",
        #         scale=alt.Scale(domain=["SUCCESS_RATE"], range=["#d1cb24"]),
        #     ),
        # )
        # chart = alt.layer(chart, success).resolve_scale(y='independent')

    return chart.interactive().properties(width=800)


st.title("Solana Metrics of Success")
st.caption(
    "Investigating various metrics based on the success or failure of transactions. "
    "All results are based on hourly transaction data."
)

(
    tps_df,
    fee_df,
    avg_fee_df,
    tx_df,
    compute_units_used_df,
    avg_compute_units_used_df,
    avg_compute_units_requested_df,
    avg_compute_units_proportion_df,
) = load_data()

option = st.selectbox(
    "Choose the type of data to plot (raw values, or a rolling average)",
    ("value", "Daily Rolling Average", "Weekly Rolling Average"),
    index=2,
    format_func=format_selectbox_value
)

st.header("Transactions")
"""Tranasactions per second and total Transactions"""
for x in (
    tps_df,
    tx_df,
):
    chart = alt_line_chart(x, option)
    st.altair_chart(chart)


st.header("Fees")
"Total Fees and Averge Fee spent per transaction"
for x in (
    fee_df,
    avg_fee_df,
):
    chart = alt_line_chart(x, option)
    st.altair_chart(chart)

st.header("Compute Units")
"""Total Compute Units Used, Average Compute Units Used per Transaction, Average Compute Units Requested, and Proportion of Compute Units Used vs. Requested"""
for x in (
    compute_units_used_df,
    avg_compute_units_used_df,
    avg_compute_units_requested_df,
    avg_compute_units_proportion_df,
):
    chart = alt_line_chart(x, option)
    st.altair_chart(chart)

st.header("Methods")
"""The Flipside Crypto ShroomDK was used to query hourly transaction information, with one query submitted per day.
Some days did not return results (less than 10%), and were excluded.
Future versions of this dashboard will improve the querying method, and also update the information on a regular basis.

The [`flipside_bounties/solana/SDK_query_metrics_of_success.ipynb`](https://github.com/ltirrell/flipside_bounties/blob/main/solana/SDK_query_metrics_of_success.ipynb) contains code used for querying and gathering results.
The query is also copied below, where the `{date}` is replaced with a valid date since the start of 2022.
"""
with st.expander("Query"):
    st.code(
        """--sql @name: all_tps_info@
-- TODO: use Kida's regex?
with consumption_tx as (
    select
        t.block_timestamp,
        t.tx_id,
        t.fee,
        t.succeeded,
        sum(
            split(
                regexp_substr(s.value, '[0-9]* of [0-9]*'),
                ' of '
            ) [0] :: int
        ) as compute_units_used,
        avg(
            split(
                regexp_substr(s.value, '[0-9]* of [0-9]*'),
                ' of '
            ) [1] :: int
        ) as avg_compute_units_requested,
        avg(
            split(
                regexp_substr(s.value, '[0-9]* of [0-9]*'),
                ' of '
            ) [0] :: int / split(
                regexp_substr(s.value, '[0-9]* of [0-9]*'),
                ' of '
            ) [1] :: int
        ) as avg_compute_units_proportion
    from
        solana.core.fact_transactions t,
        lateral flatten(input => t.log_messages) s
    where
        block_timestamp :: date = '{date}'
        and s.value like '% consumed %'
    group by
        t.block_timestamp,
        t.tx_id,
        t.fee,
        t.succeeded
)
select
    date_trunc('hour', block_timestamp) as datetime,
    -- total tx
    count(tx_id) as total_tx,
    sum(fee) as total_fee,
    avg(fee) as avg_total_fee,
    sum(compute_units_used) as total_compute_units_used,
    avg(compute_units_used) as total_avg_compute_units_used,
    avg(avg_compute_units_requested) as total_avg_compute_units_requested,
    avg(avg_compute_units_proportion) as total_avg_compute_units_proportion,
    -- successful tx:
    count(
        case
            when succeeded = 'TRUE' then succeeded
            else NULL
        end
    ) as successful_tx,
    sum(
        case
            when succeeded = 'TRUE' then fee
            else NULL
        end
    ) as successful_fee,
    avg(
        case
            when succeeded = 'TRUE' then fee
            else NULL
        end
    ) as avg_successful_fee,
    sum(
        case
            when succeeded = 'TRUE' then compute_units_used
            else NULL
        end
    ) as successful_compute_units_used,
    avg(
        case
            when succeeded = 'TRUE' then compute_units_used
            else NULL
        end
    ) as avg_successful_compute_units_used,
    avg(
        case
            when succeeded = 'TRUE' then avg_compute_units_requested
            else NULL
        end
    ) as avg_successful_compute_units_requested,
    avg(
        case
            when succeeded = 'TRUE' then avg_compute_units_proportion
            else NULL
        end
    ) as avg_successful_compute_units_proportion,
    -- failed tx:
    count(
        case
            when succeeded = 'FALSE' then succeeded
            else NULL
        end
    ) as failed_tx,
    sum(
        case
            when succeeded = 'FALSE' then fee
            else NULL
        end
    ) as failed_fee,
    avg(
        case
            when succeeded = 'FALSE' then fee
            else NULL
        end
    ) as avg_failed_fee,
    sum(
        case
            when succeeded = 'FALSE' then compute_units_used
            else NULL
        end
    ) as failed_compute_units_used,
    avg(
        case
            when succeeded = 'FALSE' then compute_units_used
            else NULL
        end
    ) as avg_failed_compute_units_used,
    avg(
        case
            when succeeded = 'FALSE' then avg_compute_units_requested
            else NULL
        end
    ) as avg_failed_compute_units_requested,
    avg(
        case
            when succeeded = 'FALSE' then avg_compute_units_proportion
            else NULL
        end
    ) as avg_failed_compute_units_proportion,
    -- rates:
    successful_tx / total_tx as success_rate,
    total_tx / 3600 as total_tps,
    successful_tx / 3600 as succesful_tps,
    failed_tx / 3600 as failed_tps
from
    consumption_tx
group by
    datetime
order by
    datetime 
--end-sql
""",
        language="sql",
    )
