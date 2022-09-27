
from urllib.request import urlopen

import altair as alt
import streamlit as st
from PIL import Image
from scipy.stats import ttest_ind

from utils import *

st.set_page_config(page_title="NFL [Big Play] ALL DAY", page_icon="🏈", layout="wide")

st.title("🏈 NFL [Big Play] ALL DAY 🏈")
st.caption(
    """
Celebrating the start of the NFL season by looking at big plays!
"""
)

st.header("Plays or Players?")
st.write(
    f"""
Is there a type of play that is more valuable, or do valuable players sell at higher prices regardless of play type?

We'll break this down based on the date range of sales data, showing the top Players by mean sales price, as well as mean price for each Play Type.
Choose a Date Range:
- All dates
- Since the start of the 2022 preseason (2022-Aug-04)
- Since the start of Week 1 of the 2022 season (2022-Sep-08)
- Since the start of Week 2 of the 2022 season (2022-Sep-15)

as well as a Moment Tier, the rarity level of the Moment NFT (in order of increasing rariry):
- Common
- Rare
- Legendary 
- Ultimate
- All tiers (showing all sales regardless of tier).

**Note** that there have only been 2 sales of Ultimate NFTs, so we will not focus analysis on these.
"""
)


main_data = load_allday_data()
date_range = st.radio(
    "Date range:",
    ["All dates", "Since 2022 preseason", "Since 2022 Week 1", "Since 2022 Week 2"],
    key="radio_summary",
    horizontal=True,
)
if date_range == "Since 2022 preseason":
    df = main_data.copy()[main_data.Date >= "2022-08-04"]
elif date_range == "Since 2022 Week 1":
    df = main_data.copy()[main_data.Date >= "2022-09-08"]
elif date_range == "Since 2022 Week 2":
    df = main_data.copy()[main_data.Date >= "2022-09-15"]
else:
    df = main_data

play_type_price_data = (
    df.groupby(
        [
            "Play_Type",
        ]
    )["Price"]
    .agg(["mean", "count"])
    .reset_index()
)
play_type_price_data["Position"] = "N/A"
play_type_tier_price_data = (
    df.groupby(
        [
            "Play_Type",
            "Moment_Tier",
        ]
    )["Price"]
    .agg(["mean", "count"])
    .reset_index()
)
play_type_tier_price_data["Position"] = "N/A"

player_price_data = (
    df.groupby(["Player", "Position"])["Price"].agg(["mean", "count"]).reset_index()
)
player_tier_price_data = (
    df.groupby(["Player", "Moment_Tier", "Position"])["Price"]
    .agg(["mean", "count"])
    .reset_index()
)
topN_player_data = (
    player_price_data.sort_values("mean", ascending=False)
    .reset_index(drop=True)
    .iloc[:n_players]
)


tier = st.selectbox(
    "Choose the Moment Tier (the rarity level of the Moment NFT)",
    ["All Tiers", "COMMON", "RARE", "LEGENDARY", "ULTIMATE"],
    format_func=lambda x: x.title(),
    key="select_summary",
)

if tier == "All Tiers":
    player_chart = alt_mean_price(topN_player_data, "Player")
    play_type_chart = alt_mean_price(
        play_type_price_data, "Play_Type", y_title=None, y_labels=False
    )
else:
    play_type_tier_subset = get_subset(play_type_tier_price_data, "Moment_Tier", tier)
    player_tier_subset = get_subset(player_tier_price_data, "Moment_Tier", tier)
    player_chart = alt_mean_price(player_tier_subset, "Player")
    play_type_chart = alt_mean_price(
        play_type_tier_subset, "Play_Type", y_title=None, y_labels=False
    )


chart = alt.hconcat(player_chart, play_type_chart, spacing=10).resolve_scale(y="shared")
st.altair_chart(chart, use_container_width=True)

st.write(
    f"""
For `All Tiers`:
- Pressure is the most valuable play type, regardless of Date range
- Team-based moments have high mean sales price for before the start of Week 1, but after that it is generally mixed by position. 
For `Common` moments:
- QBs are generally the most popular position group for all Dates, with WR and RB also fairly popular (few in the top 40 for other position groups). Tom Brady has a particularly high mean price.
- With the high number of QBs, it makes sense that Pass is the highest mean price for play types.
For `Rare` and `Legendary` moments:
- Similar trends are noted for Player positions and Play Type, though other QBs surpass Tom Brady at the top.
- A Legendary 2-pt Attempt Play Type moment was sold for $5000, surpassing the average price of Pass and other play types.
"""
)
st.subheader("Don't hate the player")
st.write(
    f"""
To analyze whether Players themselves or the Play Type captured in the Moment lead to more value, we used XGBoost to determine feature importance of our data.
See [Methods](#methods) below for more details. Our model included 
- `Player` name for the top 35 Players, with the remaining Players grouped into a `Player_Other` category
- `Team` name for the top 6 Teams, with the remaining Teams grouped into a `Team_Other` category
- `Position` name for the top 3 Postions, with the remaining Positions grouped into a `Postions_Other` category
- `Play_Type` name for the top 4 Play_Types, with the remaining Play_Types grouped into a `Play_Type_Other` category
- `Rarity`, coding the Moment Tier as an integer in increasing order of rarity
- `Sales_Count`: the number of times a specific NFT is sold (e.g. if an NFT was sold 3 times, this number would be 3 for all rows of data)
- `Resell Number`: for a specific transaction, the number of times that each specific NFT was resold (e.g. for the first ransaction of an NFT, this would be 0; if the same NFT was then purchased again, the second sale would have a value of 1)
We used these features to determine the price of the NFT, determining which factors are best indicators of predicting the sale price of an NFT.
"""
)

st.metric(
    "",
    "Players are generally among the most important features in determining Moment price",
    "",
)
st.write(
    f"""
We used 2 measures to assess feature importance: [gain](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.Booster.get_score) (how much a feature contributed to the model), and [SHAP](https://github.com/slundberg/shap) (an approach for explaining output of machine learning models) (see [here](https://stackoverflow.com/a/59007136) for a discussion of determining feature importance).

Note: A feature is just a [measurable property of our data](https://en.wikipedia.org/wiki/Feature_(machine_learning)), such as whether the NFT is from a specific player. 
"""
)
c1, c2, c3 = st.columns(3)

image = Image.open("images/gain_importance.png")
baseheight = 700
hpercent = baseheight / float(image.size[1])
wsize = int((float(image.size[0]) * float(hpercent)))
image = image.resize((wsize, baseheight), Image.Resampling.LANCZOS)

c1.image(
    image,
    use_column_width="auto",
    caption="Figure 1: Gain for determination of Feature Importance",
)
image = Image.open("images/mean_shap.png")
baseheight = 700
hpercent = baseheight / float(image.size[1])
wsize = int((float(image.size[0]) * float(hpercent)))
image = image.resize((wsize, baseheight), Image.Resampling.LANCZOS)

c2.image(image, use_column_width="auto", caption="Figure 2: Mean absolute SHAP values")
c3.write(
    f"""
While the methods have some differences, both generally agree that **Player**, **Position** and **Rarity** are most importantant, while **Play_Type** is lower down on ranking.

This makes sense, as average prices jump drastically as rarity increases, and as we saw above, certain specific players or position groups were among the highest average price.

Figure 1:
- Tom Brady, Patrick Mahomes, and several other QBs (as well as the position of QB itself) are highest on the list. That is, whether you are one of these players or not contributes the predicting the price of an NFT.
- Rarity is the 4th ranked feature
- The first `Play_type` is ranked around 25, showing that this has little relative effect in determining NFT price compared to Players

Figure 2:
- `Rarity`, followed by being a Player outside the top 35 or position outside the top 3 (not a QB, RB or Team-based Moment) explain the NFT the most
- The number sales, and the resell number for NFTs also show value in determining price. Generally, people would like to resell at a profit (maybe investigated in a future analysis?) so more sales of a specific NFT may lead to a higher price overall.
- Whether the Moment is of Tom Brady still has an important effect on explaining price.
- `Play_Type_Interception` has the 8th highest mean SHAP value. Play Type appears higher in this method of explaining importance, but still below many Player-related categories
"""
)
st.write(
    f"""
Some examples of interactions between features are shown below, described in clockwise from the top left:
1. If an NFT has the feature `Player_Other` (red), our model would predict its price is lower for higher Rarity levels.
2. The opposite effect is seen for `Position_QB`: for higher rarities, a QB NFT would be predicted to be hgiher.
3. While more mixed, the the previous 2 charts, NFTs for `Position_Other` have higher prices at Rarity 1 (Rare), but lower prices at Rarity 2 (Legendary)
4. `Play_Type_Interception` is similar to `Player_Other`: NFTs of this type are lower than those not of inteceptions at igher Rarity values.
5. If an NFT is `Player_Other` (not a top-35 player by importance) and is a QB, its price is predicted to be lower.
6. For `Play_Type Rush`, if a player is not `Position_Other` (so either QB, RB or Team), an NFT would be predicted to have lower value if the NFT shows a Rushing play.
"""
)
image = Image.open("images/interactions.png")
st.image(
    image,
    use_column_width="auto",
    caption="Figure 3: Selection of interactions between features",
)

st.header("Purchasing based on recent performance")
st.write(
    f"""
Last we'll look at whether recent higher performing players have increased number of sales, or higher median or mean price.
We'll use NFL stats for the players from a specific date range (the entire 2022 season, or from a specific week), and sort players by a given metric.
Fantasy Points is used by default; while this isn't the best metric of a player, those who score high generally had big games.
Players of all positions can be used, or you can select one of the available positions.
Use the slider to select how many players to view.

Top Players will show up in large circles in the chart below, and their NFT sales are compared with other players in the same timeframe.
Explore all the different possible combinations!
**Generally, the top players have increased sales and average price compared to the rest of the league**.

`Ctrl-Click`ing a circle will open the video of the first Moment sold for that player on that day.
"""
)
c1, c2, c3, c4, c5 = st.columns(5)
date_range = c1.radio(
    "Date range:",
    ["2022 Full Season", "2022 Week 1", "2022 Week 2", "2022 Week 3"],
    key="radio_stats",
)
position = c2.selectbox("Player Position", ["All", "QB", "RB", "WR", "TE"])
metric = c3.selectbox(
    "Metric for top players:",
    [
        "fantasy_points_ppr",
        "passing_tds",
        "passing_yards",
        "receiving_tds",
        "receiving_yards",
        "rushing_tds",
        "rushing_yards",
    ],
    format_func=lambda x: x.replace("_", " ").title(),
    key="select_stats",
)
num_players = c4.slider("Number of top players:", 1, 32, 7, key="slider_stats")
agg_metric = c5.radio(
    "Aggregation metric",
    ["median", "mean", "count"],
    format_func=lambda x: f"{x.title()} Price" if x != "count" else "Sales Count",
    key="radio_stats2",
)

weekly_df_2022, season_df_2022, roster_df_2022, team_df = load_stats_data(years=2022)
if date_range == "2022 Full Season":
    stats_df = season_df_2022
elif date_range == "2022 Week 1":
    stats_df = weekly_df_2022[weekly_df_2022.week == 1]
elif date_range == "2022 Week 2":
    stats_df = weekly_df_2022[weekly_df_2022.week == 2]
elif date_range == "2022 Week 3":
    stats_df = weekly_df_2022[weekly_df_2022.week == 3]

if position == "All":
    stats_df = stats_df.sort_values(by=metric, ascending=False).reset_index(drop=True)
else:
    stats_df = (
        stats_df[stats_df["position"] == position]
        .sort_values(by=metric, ascending=False)
        .reset_index(drop=True)
    )
if date_range == "2022 Full Season":
    df = main_data.copy()[main_data.Date >= "2022-09-08"]
elif date_range == "2022 Week 1":
    df = main_data.copy()[
        (main_data.Date >= "2022-09-08") & (main_data.Date < "2022-09-15")
    ]
elif date_range == "2022 Week 2":
    df = main_data.copy()[
        (main_data.Date >= "2022-09-15") & (main_data.Date < "2022-09-22")
    ]
elif date_range == "2022 Week 3":
    df = main_data.copy()[
        (main_data.Date >= "2022-09-22") & (main_data.Date < "2022-09-29")
    ]

top_players = stats_df.iloc[:num_players]
player_display = top_players[
    ["player_display_name", "position", "team", metric]
].rename(
    columns={
        "player_display_name": "Player",
        "position": "Position",
        "team": "Team",
        metric: metric.replace("_", " ").title(),
    }
)


grouped = (
    df.groupby(["Date", "Player", "Position", "Team"])
    .Price.agg(agg_metric)
    .reset_index()
)
video_url = (
    df.groupby(["Date", "Player", "Position", "Team"])
    .NFLALLDAY_ASSETS_URL.first()
    .reset_index()
)
grouped = grouped.merge(video_url, on=["Date", "Player", "Position", "Team"])
grouped["Date"] = grouped.Date.dt.tz_localize("US/Pacific")
players = top_players[["player_display_name", "position"]]
grouped["Top_Player"] = grouped.apply(
    lambda x: True
    if x.Player in top_players.player_display_name.values
    and x.Position
    in top_players.position.values  # HACK gets rid of the LB named Josh Allen
    else False,
    axis=1,
)

if position == "All":
    top_price = grouped[grouped.Top_Player]
    others = grouped[~grouped.Top_Player]
else:
    top_price = grouped[(grouped["Position"] == position) & (grouped.Top_Player)]
    others = grouped[(grouped["Position"] == position) & (~grouped.Top_Player)]

if agg_metric == "count":
    ytitle = "Sales Count"
elif agg_metric == "mean":
    ytitle = "Mean Sale Price ($)"
elif agg_metric == "median":
    ytitle = "Median Sale Price ($)"

c1, c2 = st.columns([2, 5])
chart = (
    alt.Chart(grouped)
    .mark_circle()
    .encode(
        x=alt.X(
            "jitter:Q",
            title=None,
            axis=alt.Axis(values=[0], ticks=True, grid=False, labels=False),
            scale=alt.Scale(),
        ),
        y=alt.Y(
            "Price", title=ytitle, scale=alt.Scale(type="log", zero=False, nice=False)
        ),
        color=alt.Color("Position"),
        column=alt.Column(
            "yearmonthdate(Date)",
            title=None,
            header=alt.Header(
                labelAngle=-90,
                titleOrient="top",
                labelOrient="bottom",
                labelAlign="right",
                labelPadding=3,
            ),
        ),
        size=alt.Size("Top_Player", title="Top Player"),
        tooltip=[
            alt.Tooltip("yearmonthdate(Date)", title="Date"),
            alt.Tooltip(
                "Player",
            ),
            alt.Tooltip(
                "Position",
            ),
            alt.Tooltip(
                "Team",
            ),
            alt.Tooltip(
                "Price", title=ytitle, format=",.2f" if ytitle != "Sales Count" else ","
            ),
        ],
        href="NFLALLDAY_ASSETS_URL",
    )
    .transform_calculate(
        # Generate Gaussian jitter with a Box-Muller transform
        jitter="sqrt(-2*log(random()))*cos(2*PI*random())"
    )
    .configure_facet(spacing=0)
    .configure_view(stroke=None)
    .interactive()
    .properties(height=600, width=100)
)

c1.write(player_display)
if agg_metric != "count":
    pval = ttest_ind(
        top_price.Price.values, others.Price.values, equal_var=False
    ).pvalue
    c1.metric(
        f"{ytitle}, Top Players (for selected positions)",
        f"{top_price.Price.agg(agg_metric):,.2f}",
    )
    c1.metric(
        f"{ytitle}, Other Players (for selected positions)",
        f"{others.Price.agg(agg_metric):,.2f}",
    )
else:
    top_count = top_price.groupby("Player").Price.count()
    others_count = others.groupby("Player").Price.count()
    c1.metric(
        f"Average Sales Count, Top Players (for selected positions)",
        f"{top_count.mean():,.2f}",
    )
    c1.metric(
        f"Average Sales Count, Other Players (for selected positions)",
        f"{others_count.mean():,.2f}",
    )
    pval = ttest_ind(top_count.values, others_count.values, equal_var=False).pvalue


c1.metric("Significant Difference?", f"{pval:.3f}", "+ Yes" if pval < 0.05 else "- No")
c2.altair_chart(chart)

cols = st.columns(5)
for i in list(range(num_players))[:5]:
    image = Image.open(urlopen(stats_df.iloc[i]["headshot_url"]))
    basewidth = 200
    wpercent = basewidth / float(image.size[0])
    hsize = int((float(image.size[1]) * float(wpercent)))
    image = image.resize((basewidth, hsize), Image.Resampling.LANCZOS)
    cols[i].image(
        image,
        use_column_width="auto",
    )
    cols[i].metric(
        f"{player_display.iloc[i]['Player']} ({player_display.iloc[i]['Position']}) - {player_display.iloc[i]['Team']}",
        player_display.iloc[i][metric.replace("_", " ").title()],
        metric.replace("_", " ").title(),
    )


with st.expander("Full Stats Infomation"):
    st.write(
        "All stats information, obtained from [`nfl_data_py`](https://github.com/cooperdff/nfl_data_py). Uses the Date Range and Player Position from above. See [here](https://github.com/nflverse/nflreadr/blob/bf1dc066c18b67823b9293d8edf252e3a58c3208/data-raw/dictionary_playerstats.csv) for a description of most metrics."
    )
    st.write(stats_df)
    csv = convert_df(stats_df)

    st.download_button(
        "Press to Download",
        csv,
        f"nfl_stats_{date_range.replace(' ', '')}_Position-{position}.csv",
        "text/csv",
        key="download-csv",
    )


st.header("Score for more?")
score_data = main_data[
    main_data.Play_Type.isin(
        [
            "Pass",
            "Reception",
            "Rush",
            "Strip Sack",
            "Interception",
            "Fumble Recovery", # ~50% TD
            "Blocked Kick", # 1/4 not td
            "Punt Return", # all TD
            "Kick Return", # 1/6 not td
        ]
    )
].reset_index(drop=True)

# score_data = combine_td_columns(score_data)

score_data['Week']=score_data.Week.astype(str)
score_data['NFL_ID']=score_data.NFL_ID.astype(str)

# weekly_df, season_df, roster_df, team_df = load_stats_data()
st.write(score_data.sample(50))
st.write(len(score_data), len(main_data))
st.write('----')

no_pbp = score_data[score_data.pbp_td.isna()]
st.write(len(no_pbp), len(no_pbp[no_pbp.Season >=1999]))

st.write(score_data.Season.unique())

st.header("Methods")
with st.expander("Method details and data sources"):
    st.write(
        f"""
Data was queried using the [Flipside ShroomDK](https://sdk.flipsidecrypto.xyz/shroomdk) using [this query template](https://github.com/ltirrell/allday/blob/main/sql/sdk_allday.sql), acquiring all the sales data and metadata from the Flow tables.
Data is saved to a [GitHub repo](https://github.com/ltirrell/allday) ([data collection script](https://github.com/ltirrell/allday/blob/main/gather_data.py), [data directory](https://github.com/ltirrell/allday/blob/main/data)).
The script is currently manually ran at least once per week (to get new data for each NFL week).

The [XGBoost Python Package](https://xgboost.readthedocs.io/en/stable/python/index.html) was used to determine feature importance using [this notebook](https://github.com/ltirrell/allday/blob/main/xgboost.ipynb).
Overall, the model explains about 69.2 percent of variance in the data (based on r^2 score); this isn't very accurate for prediction but is sufficient for determining which features most effect NFT Price.

As mentioned above, stats information were obtained from [`nfl_data_py`](https://github.com/cooperdff/nfl_data_py).
See [here](https://github.com/nflverse/nflreadr/blob/bf1dc066c18b67823b9293d8edf252e3a58c3208/data-raw/dictionary_playerstats.csv) for a description of most metrics.
"""
    )
