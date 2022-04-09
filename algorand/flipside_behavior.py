import altair as alt
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr, linregress
import streamlit as st

st.set_page_config(page_title="Flipside Algorand Wallet Behavior", page_icon="🅰️")
st.title("Flipside Algorand Wallet Behavior")
st.caption(
    """
Lets look at wallet behavior associated with wallets that have been paid a Flipside Algorand bounty payout.

The Flipside algorand bounty payout wallet is `TLR47MQCEIC6HSSYLXEI7NJIINWJESIT3XROAYC2DUEFMSRQ6HBVJ3ZWLE` and any sent payment transaction under 10,000 ALGOs can be assumed to be a bounty payout.
"""
)


@st.cache(allow_output_mutation=True, ttl=3600 * 72)
def load_data():
    # summary info
    q = "1b363710-ae95-410e-a2f7-b9d7c980d8d3"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    summary = pd.read_json(url)
    # asa info
    q = "da1bc16f-3d30-4e64-9d59-d9656e9eafc0"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    asa = pd.read_json(url)
    return summary, asa


summary, asa = load_data()

summary["Creation Date"] = pd.to_datetime(summary.CREATION_DATETIME)
summary["First Flipside Payment"] = pd.to_datetime(summary.FIRST_PAYMENT_DATETIME)
summary["PAYMENT_PROPORTION_OF_BALANCE"] = summary.TOTAL_PAID / summary.ACCT_BALANCE
summary["TOTAL_APPS"] = summary["TOTAL_APPS"].fillna(0)
summary["TOTAL_ASAS"] = summary["TOTAL_ASAS"].fillna(0)

# summary["Time Difference"] = (
#     (summary["First Flipside Payment"] - summary["Creation Date"])
#     / pd.Timedelta("1 minute")
#     / (24 * 60)
# )

m = summary.melt(
    value_vars=["Creation Date", "First Flipside Payment"],
    value_name="Date",
    var_name="Date type",
)

top_asas = asa.sort_values(by="WALLETS_WITH_ASSET", ascending=False)[:20]

row = [
    "TIME_DIFF",
    "ACCT_BALANCE",
    "TOTAL_PAID",
    "AVG_PAYMENTS",
    "PAYMENTS",
    "TOTAL_APPS",
    "TOTAL_ASAS",
]
pairplot_df = summary[row]
pairplot_df = pairplot_df.rename(
    columns={
        "TIME_DIFF": "Time between creation and payment",
        "ACCT_BALANCE": "ALGO Balance",
        "TOTAL_PAID": "Flipside payment, total",
        "AVG_PAYMENTS": "Flipside payment, average",
        "PAYMENTS": "Flipside payment, count",
        "TOTAL_APPS": "Total apps used",
        "TOTAL_ASAS": "Total ASAs held",
    }
)
st.header("NOTE:")
"This is currently a work in progress. All info is here but needs to be written up and described..."
st.header("Part 1: Creation date of wallets paid by Flipside")
st.caption(
    """
Chart the creation date of the wallets that have been paid out by the Flipside Algorand Wallet using the created_at block and block_timestamp in the `algorand.account table`. 
- Do we see people creating wallets to answer flipside algorand bounty questions?
"""
)
combined_histogram = (
    alt.Chart(m)
    .mark_bar()
    .encode(
        alt.X("yearmonth(Date):T", title=None),
        alt.Y("count()", title="Count of Wallets"),
        alt.Color("Date type:N"),
        tooltip=[
            alt.Tooltip("Date type"),
            alt.Tooltip("yearmonth(Date)", title="Date"),
            alt.Tooltip("count()", title="Count of Wallets"),
        ],
    )
).interactive()
st.altair_chart(combined_histogram, use_container_width=True)


time_diff = (
    alt.Chart(summary)
    .transform_joinaggregate(total="count(*)")
    .transform_calculate(pct="1 / datum.total")
    .mark_bar()
    .encode(
        alt.X(
            "TIME_DIFF:Q",
            bin=alt.Bin(
                extent=[0, 80],
                step=2,
            ),
            title="Time between wallet creation and first Flipside payment (days)",
        ),
        alt.Y("sum(pct):Q", axis=alt.Axis(format="%"), title="Percentage"),
        tooltip=[
            alt.Tooltip("sum(pct):Q", title="Percent of wallets in bin", format=".2%"),
            alt.Tooltip("count():Q", title="Count of wallets in bin"),
        ],
    )
).interactive()
st.altair_chart(time_diff, use_container_width=True)
percentiles = summary.TIME_DIFF.describe(
    percentiles=[0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999]
)
"Time differences:"
percentiles


# ---#
st.header("Part 2: Balances and payment summaries")
st.caption(
    """
Using `algorand.account`:
- show the distribution of current balances using the balance field for wallets that have been paid out by Flipside.
- We want to see what percent of each wallet's ALGO holdings are from bounty payouts. Show the distribution of what percent of each wallets current ALGO holdings come from bounty payouts.
- What is the total amount Flipside has paid out to wallets and what is the total amount of ALGOs these wallets are currently holding (use balance in the algroand.account table for balance).
    """
)
balances = (
    alt.Chart(summary)
    .transform_joinaggregate(total="count(*)")
    .transform_calculate(pct="1 / datum.total")
    .mark_bar()
    .encode(
        alt.X(
            "ACCT_BALANCE:Q",
            bin=alt.Bin(
                extent=[0, 200],
                step=5,
            ),
            title="Current account balance (ALGO)",
        ),
        alt.Y("sum(pct):Q", axis=alt.Axis(format="%"), title="Percentage"),
        tooltip=[
            alt.Tooltip("sum(pct):Q", title="Percent of wallets in bin", format=".2%"),
            alt.Tooltip("count():Q", title="Count of wallets in bin"),
        ],
    )
).interactive()
st.altair_chart(balances, use_container_width=True)

"""Acount balances:"""
percentiles = summary.ACCT_BALANCE.describe(
    percentiles=[0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999]
)
percentiles
# percentiles.loc["mean"]

paid_by_flipside = (
    alt.Chart(summary)
    .transform_joinaggregate(total="count(*)")
    .transform_calculate(pct="1 / datum.total")
    .mark_bar()
    .encode(
        alt.X(
            "TOTAL_PAID:Q",
            bin=alt.Bin(
                extent=[0, 200],
                step=5,
            ),
            title="Amount Paid by Flipside (ALGO)",
        ),
        alt.Y("sum(pct):Q", axis=alt.Axis(format="%"), title="Percentage"),
        tooltip=[
            alt.Tooltip("sum(pct):Q", title="Percent of wallets in bin", format=".2%"),
            alt.Tooltip("count():Q", title="Count of wallets in bin"),
        ],
    )
).interactive()


balances_percentage = (
    alt.Chart(summary)
    .transform_joinaggregate(total="count(*)")
    .transform_calculate(pct="1 / datum.total")
    .mark_bar(color="orange")
    .encode(
        alt.X(
            "PAYMENT_PROPORTION_OF_BALANCE:Q",
            bin=alt.Bin(
                extent=[0, 10],
                step=0.25,
            ),
            axis=alt.Axis(format="%"),
            title="Percentage of current balance paid by Flipside",
        ),
        alt.Y("sum(pct):Q", axis=alt.Axis(format="%"), title="Percentage"),
        tooltip=[
            alt.Tooltip("sum(pct):Q", title="Percent of wallets in bin", format=".2%"),
            alt.Tooltip("count():Q", title="Count of wallets in bin"),
        ],
    )
).interactive()
st.altair_chart(paid_by_flipside | balances_percentage, use_container_width=True)

"""Payout proportion of balance:"""
percentiles = summary.PAYMENT_PROPORTION_OF_BALANCE.describe(
    percentiles=[
        0.05,
        0.1,
        0.25,
        0.5,
        0.6,
        0.65,
        0.75,
        0.8,
        0.85,
        0.9,
    ]
)
percentiles

"""Total Paid:"""
percentiles = summary.TOTAL_PAID.describe(
    percentiles=[
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        0.75,
        0.9,
        0.95,
        0.99,
    ]
)
percentiles


f"""
Total number of wallets paid: {len(summary):,} ALGO

Total paid out: {summary.TOTAL_PAID.sum():,.2f} ALGO

Total balance, paid wallet: {summary.ACCT_BALANCE.sum():,.2f} ALGO

Average balance, paid wallet: {summary.ACCT_BALANCE.mean():,.2f} ± {summary.ACCT_BALANCE.std()/np.sqrt(len(summary)):,.2f} ALGO

Median balance, paid wallet: {summary.ACCT_BALANCE.median():,.2f} ± {summary.ACCT_BALANCE.std()/np.sqrt(len(summary)):,.2f} ALGO


Average paid out, per wallet: {summary.TOTAL_PAID.mean():,.2f} ± {summary.TOTAL_PAID.std()/np.sqrt(len(summary)):,.2f} ALGO


Average per payout: {summary.AVG_PAYMENTS.mean():,.2f} ± {summary.AVG_PAYMENTS.std()/np.sqrt(len(summary)):,.2f} ALGO

Average number of payments per wallet: {summary.PAYMENTS.mean():,.2f} ± {summary.PAYMENTS.std()/np.sqrt(len(summary)):,.2f}

"""


st.header("Part 3: ASA Breakdown")
st.caption(
    """
Using `algorand.account_asset` table, let's look at what other ASAs wallets (that have been paid by flipside crypto) are holding. 
- Create a chart of the top 10 assets the wallets are holding(make sure the amount field, balance, is greater than 0).
- Display a count of the number of wallets that are holding this asset and display the percent of flipside bounty wallets that hold this asset.
    """
)

top_asa_chart = (
    alt.Chart(top_asas)
    .mark_bar()
    .encode(
        alt.X("ASSET_NAME:N", title="", sort="-y"),
        alt.Y(
            "WALLETS_WITH_ASSET",
            title="Wallets holding ASA",
        ),
        tooltip=[
            alt.Tooltip("ASSET_NAME", title="ASA"),
            alt.Tooltip("WALLETS_WITH_ASSET", title="Wallets holding ASA"),
            alt.Tooltip(
                "PROPORTION_WITH_ASA", title="Proportion holding ASA", format=".2%"
            ),
        ],
        color=alt.Color(
            "ASSET_NAME:N",
            title="ASA Name",
            sort="-y",
            scale=alt.Scale(scheme="category20"),
        ),
    )
)
st.altair_chart(top_asa_chart, use_container_width=True)

f"""
Total number of ASAs held: {len(asa)}

ASAs held by more than 1 wallet: {len(asa[asa.WALLETS_WITH_ASSET > 1])}
"""

app_users = summary[summary.TOTAL_ASAS > 0]
f"""
Percentage of users holding at least one ASA: {len(app_users) / len(summary):.2%}
"""

asas = (
    alt.Chart(summary)
    .transform_joinaggregate(total="count(*)")
    .transform_calculate(pct="1 / datum.total")
    .mark_bar()
    .encode(
        alt.X(
            "TOTAL_ASAS:Q",
            bin=alt.Bin(
                extent=[0, 20],
                step=1,
            ),
            title="Number of ASAS (with non-zero balance)",
        ),
        alt.Y("sum(pct):Q", axis=alt.Axis(format="%"), title="Percentage"),
        tooltip=[
            alt.Tooltip("sum(pct):Q", title="Percent of wallets in bin", format=".2%"),
            alt.Tooltip("count():Q", title="Count of wallets in bin"),
        ],
    )
).interactive()
st.altair_chart(asas, use_container_width=True)


"""Total ASAS:"""
percentiles = summary.TOTAL_ASAS.describe(
    percentiles=[0.1, 0.5, 0.75, 0.9, 0.95, 0.99, 0.999, 0.9999]
)
percentiles


st.header("Part 4: Application usage")
st.caption(
    """
Using `algorand.application_call_transaction`,
- What percent of wallets(that have been paid by flipside crypto) have interacted with an application on algorand?
- Show the distribution of number of applications users have interacted with(plot the number of app_ids each wallet has interacted with).
    """
)
app_users = summary[summary.TOTAL_APPS > 0]
f"""
Percentage of users inerteracting with an Algorand application: {len(app_users) / len(summary):.2%}
"""

apps = (
    alt.Chart(summary)
    .transform_joinaggregate(total="count(*)")
    .transform_calculate(pct="1 / datum.total")
    .mark_bar()
    .encode(
        alt.X(
            "TOTAL_APPS:Q",
            bin=alt.Bin(
                extent=[0, 20],
                step=1,
            ),
            title="Number of Applications Used",
        ),
        alt.Y("sum(pct):Q", axis=alt.Axis(format="%"), title="Percentage"),
        tooltip=[
            alt.Tooltip("sum(pct):Q", title="Percent of wallets in bin", format=".2%"),
            alt.Tooltip("count():Q", title="Count of wallets in bin"),
        ],
    )
).interactive()
st.altair_chart(apps, use_container_width=True)


"""Total Apss:"""
percentiles = summary.TOTAL_APPS.describe(
    percentiles=[
        0.01,
        0.05,
        0.1,
        0.25,
        0.5,
        0.75,
        0.9,
        0.95,
        0.99,
    ]
)
percentiles

st.header("Part 5: Bonus")
"""

Note, pairplot takes a bit of time to load...
"""
def corrfunc(x, y, ax=None, **kws):
    """Plot the correlation coefficient in the top left hand corner of a plot.
    https://stackoverflow.com/questions/50832204/show-correlation-values-in-pairplot-using-seaborn-in-python
    """
    r, p = spearmanr(x, y)
    lr = linregress(x, y)
    if lr.intercept < 0:
        intercept = f"- {-1*lr.intercept:.2f}"
    else:
        intercept = f"+ {lr.intercept:.2f}"

    if p < 0.0025 and abs(r) > 0.35:
        ax = ax or plt.gca()
        ax.annotate(
            f"r = {r:.2f}\ny={lr.slope:.2f}x {intercept}",
            xy=(0.1, 0.9),
            xycoords=ax.transAxes,
        )


# column = list(reversed(row))
# chart = (
#     alt.Chart(summary)
#     .mark_circle()
#     .encode(
#         alt.X(alt.repeat("column"), type="quantitative"),
#         alt.Y(alt.repeat("row"), type="quantitative"),
#         # color='Origin:N'
#     )
#     .properties(width=50, height=50)
#     .repeat(row=row, column=column)
#     .interactive()
# )
# st.altair_chart(chart, use_container_width=True)
@st.cache(allow_output_mutation=True, ttl=3600 * 72)
def pairwise_plot():
    fig, ax = plt.subplots()
    g = sns.pairplot(pairplot_df)
    g.map_lower(corrfunc)
    return g


g = pairwise_plot()
st.pyplot(g)


with st.expander("Data Sources"):
    """
    Data was queried from Flipside Crypto following suggestions from the bounties. They are available here:
    - [Summary information on users receiving payment from Flipsie](https://app.flipsidecrypto.com/velocity/queries/1b363710-ae95-410e-a2f7-b9d7c980d8d3)
    - [ASA counts](https://app.flipsidecrypto.com/velocity/queries/da1bc16f-3d30-4e64-9d59-d9656e9eafc0)
    """
