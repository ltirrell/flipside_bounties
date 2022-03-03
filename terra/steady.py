from collections import defaultdict
import altair as alt
from arch import arch_model
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import kendalltau, linregress
import streamlit as st


def get_price(symbol, df):
    return df[df["SYMBOL"] == symbol].PRICE


def get_price_df(symbol, df):
    if type(symbol) == list:
        return df[df["SYMBOL"].isin(symbol)]
    else:
        return df[df["SYMBOL"] == symbol]


def get_matching_columns_only(df1, df2, col="DATETIME"):
    overlap = np.intersect1d(df1[col], df2[col])
    return df1[df1[col].isin(overlap)], df2[df2[col].isin(overlap)]


color_map = {
    "FTM": "blue",
    "LUNA": "goldenrod",
    "MATIC": "purple",
    "WBTC": "red",
    "WETH": "#856294",
    "SOL": "lightseagreen",
    "BNB": "black",
}


@st.cache
def load_data():
    q = "acf6805b-94ff-4b8e-bd67-db1fc58b43eb"
    url = f"https://api.flipsidecrypto.com/api/v2/queries/{q}/data/latest"
    df = pd.read_json(url)

    df_daily = (
        df.set_index("DATETIME", drop=True)
        .groupby([pd.Grouper(freq="D"), "SYMBOL"])
        .mean()
        .reset_index()
    )
    df_daily["Return"] = df_daily.groupby("SYMBOL").PRICE.pct_change()
    df_daily = df_daily.dropna()

    for x in df_daily.DATETIME:
        for y in df.SYMBOL.unique():
            l = get_price_df("LUNA", df_daily)
            l_val = l[l.DATETIME == x]["Return"].values[0]
            if l_val > 0:
                l_positive = 1
            else:
                l_positive = 0
            df_daily.loc[df_daily.DATETIME == x, "luna_positive"] = l_positive

            if y == "LUNA":
                pass
            else:
                try:
                    o = get_price_df(y, df_daily)
                    o_val = o[o.DATETIME == x]["Return"].values[0]
                    if o_val > 0:
                        o_positive = 1
                    else:
                        o_positive = 0

                    if l_val > o_val:
                        luna_higher = 1
                    else:
                        luna_higher = 0

                    if l_positive == 1 and o_positive == 1:
                        luna_up_other_down = 0
                        both_up = 1
                        luna_down_other_up = 0
                        both_down = 0
                    elif l_positive == 1 and o_positive == 0:
                        luna_up_other_down = 1
                        both_up = 0
                        luna_down_other_up = 0
                        both_down = 0
                    elif l_positive == 0 and o_positive == 1:
                        luna_up_other_down = 0
                        both_up = 0
                        luna_down_other_up = 1
                        both_down = 0
                    elif l_positive == 0 and o_positive == 0:
                        luna_up_other_down = 0
                        both_up = 0
                        luna_down_other_up = 0
                        both_down = 1
                    else:
                        print(f"idk...{y}, {x}")

                    df_daily.loc[
                        (df_daily.DATETIME == x) & (df_daily.SYMBOL == y), "luna_higher"
                    ] = luna_higher

                    df_daily.loc[
                        (df_daily.DATETIME == x) & (df_daily.SYMBOL == y),
                        "luna_up_other_down",
                    ] = luna_up_other_down
                    df_daily.loc[
                        (df_daily.DATETIME == x) & (df_daily.SYMBOL == y), "both_up"
                    ] = both_up
                    df_daily.loc[
                        (df_daily.DATETIME == x) & (df_daily.SYMBOL == y),
                        "luna_down_other_up",
                    ] = luna_down_other_up
                    df_daily.loc[
                        (df_daily.DATETIME == x) & (df_daily.SYMBOL == y), "both_down"
                    ] = both_down

                except IndexError:
                    pass

    return df_daily


df_daily = load_data()

st.title("Steady As She Goes")
st.caption(
    """
Terra Q155: A common talking point on Twitter is that LUNA is resistant to broader market downturns, when compared to other leading cryptocurrencies.

Assess this claim, using data drawn from a time period of your choosing. In making your argument, acknowledge the unknowns and address potential criticisms of your chosen position. Additionally, clearly define your definition of stability or resistance to broader market pressures, as well as your benchmarks for comparison (i.e. what are you comparing LUNA to, and how does it perform vs. its peers/competitors?)
"""
)

""" 
Our analysis will focus on LUNA price compared to a basket of other high market cap coins:
- The OGs (Ethereum: WETH and Bitcoin: WBTC)
- High usage layer-1s, by total value locked (TVL) (Binance Coin: BNB, Solana: SOL, and Fantom: FTM)
- A high usage layer-2, by TVL (Polygon: MATIC)

Our main comparison will focus on the data since the start of 2022, when the market had a large downturn with some recovery in the recent weeks.

We'll also include date starting since the launch of Columbus-5 on Terra (on 30-Sep-2021), as a good starting point for anything related to Terra price action.
"""

st.subheader("Price data overview")
"""
In the first chart below, we show the price of the assets on a log scale (so that all can be seen at once).
This is not very informative, but it does show us the general trends in the market.
Additionally, we can see that LUNA has had a stronger uptrend in recent weeks than other assets.
"""

## log scale price
scale = alt.Scale(domain=list(color_map.keys()), range=list(color_map.values()))
# Create a selection that chooses the nearest point & selects based on x-value
nearest = alt.selection(
    type="single", nearest=True, on="mouseover", fields=["DATETIME"], empty="none"
)
# The basic line
line = (
    alt.Chart(df_daily)
    .mark_line()
    .encode(
        x=alt.X("DATETIME", axis=alt.Axis(title="")),
        y=alt.Y(
            "PRICE:Q",
            axis=alt.Axis(title="Price (USD)"),
            scale=alt.Scale(
                type="log",
            ),
        ),
        color=alt.Color("SYMBOL:N", scale=scale),
    )
)
# Transparent selectors across the chart. This is what tells us
# the x-value of the cursor
selectors = (
    alt.Chart(df_daily)
    .mark_point()
    .encode(
        x="DATETIME",
        opacity=alt.value(0),
    )
    .add_selection(nearest)
)
# Draw points on the line, and highlight based on selection
points = line.mark_point().encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)
# Draw text labels near the points, and highlight based on selection
text = line.mark_text(align="left", dx=5, dy=-5).encode(
    text=alt.condition(nearest, "PRICE:Q", alt.value(" "))
)
# Draw a rule at the location of the selection
rules = (
    alt.Chart(df_daily)
    .mark_rule(color="gray")
    .encode(
        x="DATETIME",
    )
    .transform_filter(nearest)
)
# Put the five layers into a chart and bind the data
log_price_chart = alt.layer(line, selectors, points, rules, text).interactive()
st.altair_chart(log_price_chart, use_container_width=True)


"""
Next, we overlaid all prices on the same axis, making trends more clear.
There are some clear correlations where all assets dipped in price at the same time (early January and around January 20th), but there are some interesting differences.

Ethereum and Bitcoin had a peak in price in November, and then have been steadily going down since (besides for a small recovery in recent weeks.)
BNB has very closely followed Bitcoin in the time period we have data for, and Solana shows similar trends as well.
All these coins are lower in price now than at the start of the time period

FTM and MATIC are more interesting.
FTM has period peaks and dumps in price, showing a strong increase in price while other assets were decreasing in value in December.
MATIC steadily increased after the peak of BTC/ETH before dropping around the new year.
Both these coins have increased in value since the start of this time period, and in general there prices have shot up over the last year.

LUNA's price follows more closely with FTM/MATIC.
It increased rapidly from late November to the end of 2021.
The price dropped with the rest of the crypto currency market in January, however it recovered quicker.
While the rest of the market has seen modest gains in late February, LUNA increased sharply, approaching its all time high.

This recent price action shows a stronger resiliance than other asset, with a strong caveat that past performance doesn't predict the future.
However, there are other reasons to be confident in LUNA going forward.
With the establishment of the Luna Foundation Guard, and a sale to set up a \$1 billion reserve of BTC, there is a notion that the new floor of LUNA is $52, around the low in January but about 50% higher than in October.
See [here](https://app.flipsidecrypto.com/dashboard/52-pickup-zLnqmJ) for further discussion on this topic.
"""
## overlaid prices
dfs = [get_price_df(x, df_daily) for x in df_daily.SYMBOL.unique()]
nearest = alt.selection(
    type="single", nearest=True, on="mouseover", fields=["DATETIME"], empty="none"
)
text_charts = []
other_charts = []
for i, x in enumerate(dfs):
    base = alt.Chart(x).encode(alt.X("DATETIME:T", axis=alt.Axis(title=None)))
    line = base.mark_line().encode(
        alt.Y(
            "PRICE:Q",
            axis=alt.Axis(title=None, tickSize=0, labels=False),
            scale=alt.Scale(type="log"),
        ),
        color=alt.Color("SYMBOL:N", scale=scale),
    )
    point = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))
    )
    text = (
        line.mark_text(align="left")
        .encode(text=alt.condition(nearest, "label:N", alt.value(" ")))
        .transform_calculate(
            label=f'"{x.SYMBOL.unique()[0]} Price: "+ format(datum.PRICE,".1f")'
        )
    )
    other_charts.extend([line, point])
    if i == 0:
        selector = (
            line.mark_point()
            .encode(
                x="DATETIME",
                opacity=alt.value(0),
            )
            .add_selection(nearest)
        )
        other_charts.append(selector)
    text_charts.append(text)
overlaid_price_chart = (
    alt.layer(*other_charts, alt.layer(*text_charts))
    .resolve_scale(y="independent")
    .interactive(bind_y=False)
)
st.altair_chart(overlaid_price_chart, use_container_width=True)

# ----
st.subheader("Daily Returns")

pos = (
    df_daily[df_daily.DATETIME >= "2022-01-01"]
    .groupby("SYMBOL")
    .apply(lambda x: sum(x.Return > 0))
)
total = df_daily[df_daily.DATETIME >= "2022-01-01"].groupby("SYMBOL").Return.count()
proportion_pos = (pos / total * 100).sort_values()


"""
Daily returns were calculated for the assets, as well as an estimate of volatility over the past 30 days.
"""

# Daily Returns
preds = dict()
models = dict()
fig, axes = plt.subplots(7, 1, figsize=(8, 12), sharex=True, sharey=True)
for i, x in enumerate(color_map.keys()):
    ax = axes.ravel()[i]

    d = get_price_df(x, df_daily).reset_index(drop=True)
    d = d[d.DATETIME >= "2022-01-01"]
    r = d["Return"] * 100
    idx = d["DATETIME"]
    sns.lineplot(
        x=idx,
        y=r,
        color=list(color_map.values())[i],
        ax=ax,
        label=x,
    )

    # see here for reference: https://python.plainenglish.io/how-to-predict-stock-volatility-with-python-46ae341ce804
    garch_model = arch_model(
        r,
        # p=1,
        # q=1,
        # mean="constant",
        # vol="GARCH",
        # dist="normal",
    )
    gm_result = garch_model.fit(disp="off")

    rolling_predictions = []
    test_size = 30
    for i in range(test_size):
        train = r[: -(test_size - i)]
        model = arch_model(train, p=1, q=1)
        model_fit = model.fit(disp="off")
        pred = model_fit.forecast(horizon=1)
        rolling_predictions.append(np.sqrt(pred.variance.values[-1, :][0]))

    rolling_predictions = pd.Series(rolling_predictions, index=idx[-test_size:])
    # ax.plot(
    #     idx[-test_size:],
    #     r[-test_size:],
    # )
    ax.plot(rolling_predictions, color="green", alpha=0.8, linestyle=":")
    # ax.set_title(f"{x}")
    # ax.legend([f"{x} Returns", "Predicted Volatility"], loc="lower left")
    ax.set_xlabel("")
    ax.set_ylabel("")

    ax.hlines(
        5,
        min(ax.get_xticks()),
        max(ax.get_xticks()),
        color="black",
        alpha=0.2,
        linestyle="dashdot",
    )
    ax.hlines(
        -5,
        min(ax.get_xticks()),
        max(ax.get_xticks()),
        color="black",
        alpha=0.2,
        linestyle="dashdot",
    )
    ax.hlines(
        0,
        min(ax.get_xticks()),
        max(ax.get_xticks()),
        color="black",
        alpha=0.4,
        linestyle="-",
    )
    ax.hlines(
        10,
        min(ax.get_xticks()),
        max(ax.get_xticks()),
        color="black",
        alpha=0.3,
        linestyle="dashed",
    )
    ax.hlines(
        -10,
        min(ax.get_xticks()),
        max(ax.get_xticks()),
        color="black",
        alpha=0.3,
        linestyle="dashed",
    )
    ax.tick_params(axis="x", labelrotation=45)
    preds[x] = rolling_predictions
    models[x] = gm_result
    ax.legend(loc="lower left")


fig.subplots_adjust(hspace=0.1, wspace=0.05)
fig.text(
    0.05,
    0.5,
    "Daily Return",
    va="center",
    rotation="vertical",
    fontsize=12,
    weight="semibold",
)
st.pyplot(fig)
volatility = pd.DataFrame.from_dict(preds).mean().sort_values()
daily_stdev = (
    df_daily[df_daily.DATETIME >= "2022-01-01"].groupby("SYMBOL").Return.std() * 100
)
f"""
LUNA has a relatively high volatility ({volatility.LUNA:.2f}%), similar to FTM and SOL, and twice as high as BTC.
"""

volatility

f"""
However, volatility isn't always necessary bad.
It is also necessary for large gains, not just losses!
Since the start of the year, LUNA has the highest proportion of days with a positive return ({proportion_pos.LUNA:.2f}%).
This is also true if we look at the past 30 days, or for the full time period
"""
proportion_pos

"""
Besides for just proportion positive, we want to examine if the assests move in the same direction, or are generally correlated.
There are significant but modest positive correlation between LUNA's daily return and each of the other assets.
A fit of the data was also calculated, with slopes around 0.4 to 0.8 for each asset.
This trend is more pronounced on days where LUNA's return is higher than the other assets (data not show.)

Together, this suggests that markets generally move together, in the same direction, though the amount of daily change for non-LUNA assets is lower magnitude.
For example, if LUNA gained 10%, the best guess for BTC's price chage would be a 4% gain.
"""
for l_pos in [-1, 0, 1]:
    fig, axes = plt.subplots(3, 2, figsize=(8, 12), sharex=True, sharey=True)
    alpha = 0.01
    limit = 0.3
    symbols = list(color_map.keys())
    symbols.remove("LUNA")
    for i, x in enumerate(symbols):
        ax = axes.ravel()[i]

        if l_pos == -1:
            ldf, odf = get_matching_columns_only(
                get_price_df("LUNA", df_daily), get_price_df(x, df_daily)
            )
            ldf = ldf[ldf.DATETIME >= "2022-01-01"]
            odf = odf[odf.DATETIME >= "2022-01-01"]
        else:
            ldf, odf = get_matching_columns_only(
                get_price_df("LUNA", df_daily), get_price_df(x, df_daily)
            )
            ldf = ldf[ldf.DATETIME >= "2022-01-01"]
            odf = odf[odf.DATETIME >= "2022-01-01"]
            ldf = ldf[ldf.luna_positive == l_pos]
            odf = odf[odf.luna_positive == l_pos]
        sns.scatterplot(
            x=ldf.Return.values,
            y=odf.Return.values,
            ax=ax,
            color=color_map[x],
            label=x,
        )

        ax.set_xlim(-1 * limit, limit)
        ax.set_ylim(-1 * limit, limit)

        k = kendalltau(ldf.Return.values, odf.Return.values)
        lr = linregress(ldf.Return.values, odf.Return.values)

        if k.pvalue < alpha and lr.pvalue < alpha:
            if lr.intercept < 0:
                intercept = f"- {-1*lr.intercept:.2f}"
            else:
                intercept = f"+ {lr.intercept:.2f}"
            ax.text(
                -0.15,
                0.2,
                fr"$Kendall's ~\tau:{k.correlation:.2f}$",
                ha="center",
                weight="semibold",
            )
            ax.text(
                -0.15,
                0.16,
                fr"$y={lr.slope:.2f}x {intercept}$",
                ha="center",
                weight="semibold",
            )

        pts = np.linspace(-0.3, 3, 25)
        x_pts = pts.copy()
        y_pts = pts * lr.slope + lr.intercept
        sns.lineplot(x=x_pts, y=y_pts, ax=ax, color="gray", linestyle=":")

        if x in ["BNB"]:
            ax.text(
                0.20,
                -0.25,
                f"Data starts on\n{odf.DATETIME.min():%Y-%m-%d}",
                ha="center",
                fontstyle="italic",
            )

    fig.subplots_adjust(hspace=0.05, wspace=0.1)
    fig.text(
        0.05,
        0.5,
        "Daily Return (non-LUNA coin)",
        va="center",
        rotation="vertical",
        fontsize=12,
        weight="semibold",
    )

    fig.text(
        0.5,
        0.08,
        "Daily Return (LUNA)",
        ha="center",
        fontsize=12,
        weight="semibold",
    )
    title = "Correlation between LUNA and other assets, Year to Date 2022"
    if l_pos == 0:
        title += "\n(when LUNA return is negative)"
    if l_pos == 1:
        title += "\n(when LUNA return is positive)"
    fig.text(
        0.5,
        0.9,
        title,
        ha="center",
        fontsize=14,
        weight="semibold",
    )
    if l_pos == -1:
        st.pyplot(fig)

"""
Our last analysis will compare proportions where LUNA performed better or worse than other assets.

For each day in this year, we compared the following. 
- **luna_higher**: Days where LUNA had a higher overall return than the other asset
- **both_up**: Days where LUNA and the other asset both had a positive return
- **luna_up_other_down**: Days where LUNA had a had a positive return return and the other asset had a negative return
- **luna_down_other_up**: Days where LUNA had a had a negative return return and the other asset had a positive return
- **both_down**: Days where LUNA and the other asset both had a negative return

The cumulative proportion of these metrics are plotted below (the number of days it happened divided by total days that passed so far).
Note that **luna_higher** is not mutually exclusive with the other 4 categories, but the other 4 categories are exclusive (and combed are equal to one)

LUNA performed better than the other assets over 50% of the time.
This has occurred steadily iver the time period, and not just recently when there were large gains in LUNA price.

It was generally pretty rare that assets moved in opposite directions.
LUNA price decreased when the other asset increased only around 10% of the time.
However, LUNA increased when the other decreased at a slight higher rate, aroynd 10-20%.
Both assets moved in the same direction around 40% of the time.
"""
fig, axes = plt.subplots(3,2, figsize=(8, 16), sharex=True, sharey=True)
alpha = 0.001  #  conservative Bonferroni correction for significance
limit = 0.3
symbols = list(color_map.keys())
symbols.remove("LUNA")
for i, x in enumerate(symbols):
    ax = axes.ravel()[i]
    _, odf = get_matching_columns_only(get_price_df("LUNA", df_daily), get_price_df(x, df_daily))
    odf = odf[odf.DATETIME >= "2022-01-01"]
    sns.lineplot(
        x=odf['DATETIME'],
        y=odf['luna_higher'].cumsum() / len(odf),
        ax=ax,
        label='luna_higher'
    )
    sns.lineplot(
        x=odf['DATETIME'],
        y=odf['both_up'].cumsum() / len(odf),
        ax=ax,
        label='both_up'
    )
    sns.lineplot(
        x=odf['DATETIME'],
        y=odf['luna_up_other_down'].cumsum() / len(odf),
        ax=ax,
        label='luna_up_other_down'
    )
    sns.lineplot(
        x=odf['DATETIME'],
        y=odf['luna_down_other_up'].cumsum() / len(odf),
        ax=ax,
        label='luna_down_other_up'
    )
    sns.lineplot(
        x=odf['DATETIME'],
        y=odf['both_down'].cumsum() / len(odf),
        ax=ax,
        label='both_down'
    )
    ax.tick_params(axis='x', labelrotation=45)
    ax.set_xlabel('')
    ax.set_ylabel('')
    handles, labels = ax.get_legend_handles_labels()
    ax.get_legend().remove()
    ax.set_title(x)
fig.legend(handles, labels, loc='upper center')

fig.subplots_adjust(hspace=0.1, wspace=0.1)
fig.text(
    0.05,
    0.5,
    "Proportion",
    va="center",
    rotation="vertical",
    fontsize=12,
    weight="semibold",
)
st.pyplot(fig)
st.subheader("Summary")
"""
Overall, recent trends suggest that LUNA is correlated with the basket of other similiar crypto assets we chose.
However the price has generally moved in a farvorable direction more often.
"""
st.subheader("Methods")
"""
SQL query [here](https://app.flipsidecrypto.com/velocity/queries/acf6805b-94ff-4b8e-bd67-db1fc58b43eb), selecting price data from Ethereum tables when available.
Luna oracle prices were used for LUNA prices, and SOL swaps against stablecoins were used to determine its price.
Code is on GitHub [here](https://github.com/ltirrell/flipside_bounties/blob/main/terra/steady.py)
"""
st.dataframe(df_daily)
