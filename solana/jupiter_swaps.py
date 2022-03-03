from collections import defaultdict
from email.policy import default
import altair as alt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import streamlit as st


st.title("Most Popular Jupiter Swaps")
st.caption(
    """
Jupiter is the best swap aggregator on Solana, meaning that it optimizes the best token swap rate across all decentralized exchanges for users.

- Since February 1st, what have been the 10 most popular tokens to swap away?
- Over that same timeframe, what have been the 10 most popular tokens to swap for?
- What are the 10 most popular swapping pairs (combination of swap away to swap for)?

Define 'popular' as the number of swaps and create a visualization showing total number of swaps over that time fram highlighting these most popular tokens."""
)


def combine_pairs(x):
    sorted_strings = sorted(
        [f"[{x['TO_ADDRESS_LABEL']}]", f"[{x['FROM_ADDRESS_LABEL']}]"]
    )
    return "-".join(sorted_strings)


def get_popular(df, size=20, by_date=False):
    if by_date:
        return (
            df.groupby(["DATETIME"])
            .apply(
                lambda x: (
                    x.groupby("LABEL")
                    .sum()
                    .sort_values("TX_COUNT", ascending=False)
                    .head(size)
                )
            )
            .reset_index()
        )
    else:
        return (
            df.groupby("LABEL")
            .TX_COUNT.sum()
            .sort_values(ascending=False)
            .reset_index()
            .head(size)
        )


def plot_total(source, title, label):
    selection = alt.selection_multi(fields=["LABEL"], bind="legend")
    source["Rank"] = source.index + 1
    chart = (
        alt.Chart(source, title=title)
        .mark_bar()
        .encode(
            alt.X(
                "LABEL:N",
                axis=alt.Axis(domain=False, tickSize=0),
                sort=alt.EncodingSortField(
                    field="TX_COUNT", op="count", order="ascending"
                ),
                title=None,
            ),
            alt.Y("TX_COUNT:Q", title="Transactions"),
            alt.Color(
                "LABEL:N",
                scale=alt.Scale(scheme="category20b"),
                title=label,
                sort=alt.EncodingSortField(
                    field="TX_COUNT", op="sum", order="descending"
                ),
            ),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
            tooltip=["Rank", "LABEL", "TX_COUNT"],
        )
        .add_selection(selection)
        .interactive()
    )
    return chart


def plot_by_date(source, title, label):
    selection = alt.selection_multi(fields=["LABEL"], bind="legend")

    chart = (
        alt.Chart(source, title=title)
        .mark_bar()
        .encode(
            alt.X(
                "DATETIME:T",
                axis=alt.Axis(domain=False, tickSize=0),
                title=None,
            ),
            alt.Y("TX_COUNT:Q", title="Transactions (normalized)", stack="normalize"),
            alt.Color(
                "LABEL:N",
                scale=alt.Scale(scheme="category20b"),
                title=label,
                sort=alt.EncodingSortField(
                    field="TX_COUNT", op="sum", order="descending"
                ),
            ),
            order=alt.Order("TX_COUNT", sort="ascending"),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.2)),
            tooltip=["DATETIME", "LABEL", "TX_COUNT"],
        )
        .add_selection(selection)
        .interactive()
    )
    return chart


@st.cache
def load_data():
    q = "6392e078-4836-4cd8-9551-a3346b2cae06"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)

    # we'll only look at address labels
    df = df[
        [
            "DATETIME",
            "FROM_ADDRESS_LABEL",
            "TO_ADDRESS_LABEL",
            "TOTAL_SWAP_FROM",
            "TOTAL_SWAP_TO",
            "TX_COUNT",
        ]
    ]

    # add pair
    df["PAIR"] = df.apply(combine_pairs, axis=1)
    # daily data for this analysis
    return df


# organize datasets
df = load_data()

to_df = (
    df.groupby(["DATETIME", "TO_ADDRESS_LABEL"])
    .TX_COUNT.sum()
    .reset_index()
    .rename(columns={"TO_ADDRESS_LABEL": "LABEL"})
)
from_df = (
    df.groupby(["DATETIME", "FROM_ADDRESS_LABEL"])
    .TX_COUNT.sum()
    .reset_index()
    .rename(columns={"FROM_ADDRESS_LABEL": "LABEL"})
)
total_df = (
    pd.concat([to_df, from_df]).groupby(["DATETIME", "LABEL"]).sum().reset_index()
)
pair_df = (
    df.groupby(["DATETIME", "PAIR"])
    .TX_COUNT.sum()
    .reset_index()
    .rename(columns={"PAIR": "LABEL"})
)

d = {
    "Most popular asset to swap for": {
        "data": to_df,
        "by_date": pd.DataFrame(),
        "total": pd.DataFrame(),
    },
    "Most popular asset to swap away": {
        "data": from_df,
        "by_date": pd.DataFrame(),
        "total": pd.DataFrame(),
    },
    "Most popular swapped asset": {
        "data": total_df,
        "by_date": pd.DataFrame(),
        "total": pd.DataFrame(),
    },
    "Most popular swapping pairs": {
        "data": pair_df,
        "by_date": pd.DataFrame(),
        "total": pd.DataFrame(),
    },
}

for k, v in d.items():
    v["total"] = get_popular(v["data"])
    v["by_date"] = get_popular(v["data"], by_date=True)


# create plots
for k, v in d.items():
    title = k
    if "pair" in k:
        label = "Pair"
    else:
        label = "Asset"
    v["plot_total"] = plot_total(v["total"], title, label)
    v["plot_by_date"] = plot_by_date(v["by_date"], f"{title}, by date", label)

metrics = [f"- {x}\n" for x in d.keys()]
f"""
This analysis examines the most popular token swaps on the Jupiter Aggregtator in February 2022.

We looked at both total tokens for the month, as well as breaking down popular assets by each day.

The following metrics were compared, with the top 20 shown in charts (though discussion will focus on top 10).
{''.join(metrics)}

**Note**: the asset listed as `wormhole` is [FTT transferred to Solana using the Wormhole bridge](https://solscan.io/token/EzfgjvkSwthhgHaceR3LnKXUoRkP6NUhfghdaHAj1tUv), and `sollet` is [BTC bridged using Sollet](https://solscan.io/token/9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E)
"""
## Total
st.subheader("Most Popular Tokens by Swaps, February 2022")
"""
By far the most popular token to swap for is **USDC**.
It has about as many transactions as the rest of the top 10 combined!

Also included in the top ten is USDT (another stable coin), and 2 forms of SOL (wrapped native SOL and mSOL).
It makes sense users want to swap to stablecoin and SOL-based assets.
"""
st.altair_chart(
    d["Most popular asset to swap for"]["plot_total"], use_container_width=True
)

"""
The exact same trend occurs in assets that are swapped away, with the top 10 following the same order.

The tokens in this group may have the deepest liquidity on Solana, so it is popular to use them in trades for other assets, as well as to acquire them.
"""
st.altair_chart(
    d["Most popular asset to swap away"]["plot_total"], use_container_width=True
)

"""
Since the most popular asset to swap for and away are the same and follow the same order, it makes sense for the total swaps to also match this!

Again, the order and trends of total transactions involving each asset are the same.
"""
st.altair_chart(d["Most popular swapped asset"]["plot_total"], use_container_width=True)

"""
Looking at the most popular swapping pairs, again USDC dominates.
9 of the top 10 most popular swapping pair include USDC!
`USDC - SOL` is by far the most ferequently used, and `USDT - SOL` rounds out the top 10 as another way to buy SOL from stable coins.

The `None - USDC` pair is the 9th most popular swapping pair.
`None` includes all assets that are not currently labeled in Flipside's data.
This shows that USDC is a popular pair for up-and-coming coins which haven't had enough traction to be tracked in more detail.

Interestingly, the `USDC-USDC` and `SOL - SOL` pairs show up among the more popular pairs (3rd and 11th, respectively).
This may be due to a combination of a few things:
- Limitations of data (for example, some swaps like [this one](https://solscan.io/tx/2jAxjCVfrn1gHNFkmSzJo3KAWmjDSfxy54grev9hYaA74bJD8wvbaQwihwnXZfKJ4K14Cs3x731JfHV1s9uUg8Mx) show up as `USDC - USDC` when it is actually a swap for a different asset)
- Arbitrage opportunities, where users (or most likely bots) can take advantage of price differences of USDC on various exchages
"""
st.altair_chart(
    d["Most popular swapping pairs"]["plot_total"], use_container_width=True
)

## By date
st.subheader("Most Popular Tokens Swaps by date, February 2022")
"""
We can look at some trends in token swaps accross February.
Note that data from Feb-21/Feb-22 may be corrupted (only a few total transactions), so we will ignore these dates.

The 3 charts below show the swaps for, away and total by date.
Again, the same top 10 coins are highly relevant each day.

USDC stays at around the same proportion (~60% of the transactions in the top 20),
and SOL makes up ~10% pretty regularly with some minor fluctuations.

The next few most popular assets (RAY, USDT, mSOL, Step, Sollet BTC, Cropper, Wormhole FTT)
change ordering throughout the month to fill out the top 5.

At the start of the month, RAY or USDT were generally the 3rd and 4th most popular assets to swap,
but increasingly mSOL has been taking one of these spaces at the end of February.

"""
st.altair_chart(
    d["Most popular asset to swap for"]["plot_by_date"], use_container_width=True
)
st.altair_chart(
    d["Most popular asset to swap away"]["plot_by_date"], use_container_width=True
)
st.altair_chart(
    d["Most popular swapped asset"]["plot_by_date"], use_container_width=True
)

"""
Pairs involving USDC are dominant throughout the month.

Interestingly, at the end of February, `None - USDC` and `None - SOL` pairs have become more popular.
This may be due to many releases of new coins in recent days.
"""
st.altair_chart(
    d["Most popular swapping pairs"]["plot_by_date"], use_container_width=True
)

st.subheader("Summary")
"""
Overall, USDC dominates as the most popular asset, either swapping to or from, or involved in a trading pair.
USDT, SOL and mSOL are also popular, along with Raydium (one of the leading exchanges on Solana).
"""
st.subheader("Methods")
"""
SQL query [here](https://app.flipsidecrypto.com/velocity/queries/6392e078-4836-4cd8-9551-a3346b2cae06), selecting price data from the `solana.swaps` table, and labeling token names using `solana.labels`.
The total amoun

Code is on GitHub [here](https://github.com/ltirrell/flipside_bounties/blob/main/solana/jupiter_swaps.py)
"""
st.dataframe(df)
