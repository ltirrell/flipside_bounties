from urllib.request import urlopen
from io import BytesIO
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from scipy.stats import ttest_ind
from PIL import Image

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

We'll break this down based on the date range of sales data. Choose a Date Range:
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


st.header("Purchasing based on recent performance")
c1, c2, c3, c4, c5 = st.columns(5)
date_range = c1.radio(
    "Date range:",
    ["2022 Full Season", "2022 Week 1", "2022 Week 2"],
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
num_players = c4.slider("Number of top players:", 1, 32, 5, key="slider_stats")
agg_metric = c5.radio(
    "Aggregation metric",
    ["median", "mean", "count"],
    format_func=lambda x: f"{x.title()} Price" if x != "count" else "Sales Count",
    key="radio_stats2",
)

weekly_df, season_df, roster_df, team_df = load_stats_data()
if date_range == "2022 Full Season":
    stats_df = season_df
elif date_range == "2022 Week 1":
    stats_df = weekly_df[weekly_df.week == 1]
elif date_range == "2022 Week 2":
    stats_df = weekly_df[weekly_df.week == 2]

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
    df = main_data.copy()[main_data.Date >= "2022-09-15"]

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
grouped["Date"] = grouped.Date.dt.tz_localize("US/Pacific")
# st.write(grouped.dtypes)
players = top_players["player_display_name"].values
grouped["Top_Player"] = grouped.Player.apply(lambda x: True if x in players else False)

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

c1, c2 = st.columns([1, 2])
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

pval = ttest_ind(top_price.Price.values, others.Price.values, equal_var=False).pvalue
c1.write(player_display)
c1.metric(
    f"{ytitle}, Top Players (for selected positions)",
    f"{top_price.Price.agg(agg_metric):,.2f}",
)
c1.metric(
    f"{ytitle}, Other Players (for selected positions)",
    f"{others.Price.agg(agg_metric):,.2f}",
)
c1.metric("Significant Difference?", f"{pval:.3f}", "+ Yes" if pval < 0.05 else "- No")
c2.altair_chart(chart)

cols = st.columns(5)
for i in list(range(num_players))[:5]:
    image = Image.open(urlopen(stats_df.iloc[i]["headshot_url"]))
    basewidth = 200
    wpercent = basewidth / float(image.size[0])
    hsize = int((float(image.size[1]) * float(wpercent)))
    image = image.resize((basewidth, hsize), Image.ANTIALIAS)
    # image.thumbnail((200,200), Image.ANTIALIAS)
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
st.write(df.sort_values(by="Date").head())
